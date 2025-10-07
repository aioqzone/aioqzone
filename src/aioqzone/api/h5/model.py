import logging
import typing as t
from os import PathLike

from pydantic import HttpUrl, ValidationError
from tenacity import AsyncRetrying, TryAgain, after_log, stop_after_attempt

from aioqzone.api.login import Loginable
from aioqzone.model.api import *
from aioqzone.utils.retry import retry_if_qzone_code, retry_if_status
from qqqr.utils.net import ClientAdapter

log = logging.getLogger(__name__)


class QzoneH5API:
    qzone_tokens: t.Dict[int, str]

    def __init__(
        self, client: ClientAdapter, loginman: Loginable, *, retry_if_login_expire: bool = True
    ) -> None:
        """
        :param retry_if_login_expire: if we should retry if login expired.
        """
        super().__init__()
        self.client = client
        self.login = loginman
        self._relogin_retry = AsyncRetrying(
            stop=stop_after_attempt(2 if retry_if_login_expire else 1),
            retry=retry_if_status(302, 403) | retry_if_qzone_code(-3000, -10000),
            after=after_log(log, logging.INFO),
            sleep=self._retry_sleep,
        )
        """A decorator which will relogin and retry given func if cookie expired.

        'cookie expired' is indicated by:

        - `aioqzone.exception.QzoneError` code -3000/-10000
        - HTTP response code 302/403

        .. note:: Decorate code as less as possible
        .. warning::

                You *SHOULD* **NOT** wrap a function with mutable input. If you change the mutable
                var in the first attempt, in the second attempt the var saves the changed value.
        """
        self.qzone_tokens = {}

    async def call(self, api: QzoneApi[TyRequest, TyResponse]) -> TyResponse:
        params: t.Dict[str, t.Any] = api.params.build_params(self.login.uin)
        if api.http_method == "GET":
            data = {}
        else:
            data = dict(json=params) if api.is_json else dict(data=params)
            params = {}

        headers = dict(Referer=api.referer)
        if api.keep_alive:
            headers["Connection"] = "keep-alive"
        # if api.is_json:
        #     headers["Content-Type"] = "application/json"
        #     headers["Accept"] = "application/json"

        async for attempt in self._relogin_retry:
            with attempt:
                if api.login_required:
                    if (gtk := self.login.gtk) == 0:
                        raise TryAgain("no login state")

                    if api.attach_token:
                        params["g_tk"] = gtk
                        hostuin: int = getattr(api.params, "hostuin", self.login.uin)
                        if qzonetoken := self.qzone_tokens.get(hostuin):
                            params["qzonetoken"] = qzonetoken

                async with self.client.request(
                    api.http_method,
                    api.url,
                    params=params,
                    headers=headers,
                    cookies=self.login.cookie,
                    **data,
                ) as r:
                    r.raise_for_status()
                    obj = await api.response.response_to_object(r)
                    try:
                        return api.response.from_response_object(obj)
                    except ValidationError:
                        log.debug(f"Error when validating {obj}", api)
                        raise
        else:
            raise AssertionError

    async def _retry_sleep(self, *_) -> None:
        await self.login.new_cookie()

    async def index(self) -> IndexPageResp:
        """This api is the redirect page after h5 login, which is also the landing (main) page of h5 qzone.

        :raise `RuntimeError`: if any failure occurs in data parsing.
        """

        r = await self.call(IndexPageApi())
        self.qzone_tokens[self.login.uin] = r.qzonetoken
        log.debug(f"qzonetoken[{self.login.uin}] = {r.qzonetoken}")
        return r

    async def profile(self, hostuin: int, start_time: float = 0) -> ProfilePagePesp:
        """Get the profile page of a user.

        :param hostuin: uin of the user
        :param start_time: timestamp in seconds, default as current time.
        """
        r = await self.call(UserProfileApi(params=ProfileParams.model_validate(locals())))
        self.qzone_tokens[hostuin] = r.qzonetoken
        log.debug(f"qzonetoken[{hostuin}] = {r.qzonetoken}")
        return r

    async def get_active_feeds(self, attach_info: t.Optional[str] = None) -> FeedPageResp:
        """Get next page. If :obj:`.qzone_tokens` has not cached a qzonetoken of the login uin
        or :obj:`attach_info` is empty, this method will call :meth:`.index` and return its response.

        :param attach_info: The ``attach_info`` field from last call.
            Pass an empty string equals to call :meth:`.index`.
        :return: If success, the ``data`` field of the response.
        """
        if not self.qzone_tokens.get(self.login.uin) or not attach_info:
            return await self.index()

        return await self.call(FeedPageApi(params=ActiveFeedsParams.model_validate(locals())))

    async def get_feeds(self, hostuin: int, attach_info: t.Optional[str] = None) -> ProfileResp:
        """Get next page of the given :obj:`uin`.
        If :obj:`.qzone_tokens` has not cached qzonetoken of given :obj:`uin` or :obj:`attach_info` is empty,
        it will call :meth:`.profile` and return its :obj:`~ProfileResp.feedpage` field.

        :param hostuin: uin of the user
        :param attach_info: The ``attach_info`` field from last call.
            Pass an empty string equals to call :meth:`.index`.
        :return: If success, the ``data`` field of the response.
        """
        if not self.qzone_tokens.get(hostuin) or not attach_info:
            return (await self.profile(hostuin)).feedpage

        return await self.call(GetFeedsApi(params=GetFeedsParams.model_validate(locals())))

    async def shuoshuo(self, fid: str, uin: int, appid=311, busi_param: str = "") -> DetailResp:
        """This can be used to get the detailed summary of a feed.

        :param fid: :term:`fid`
        :param uin: uin of the owner of the given feed
        :param appid: :term:`appid`
        :param busi_param: optional encoded params
        """
        return await self.call(ShuoshuoApi(params=ShuoshuoParams.model_validate(locals())))

    async def mfeeds_get_count(self) -> FeedCount:
        """Get new feeds count. This is also the "keep-alive" signal of the cookie."""
        return await self.call(GetCountApi())

    async def internal_dolike_app(
        self, appid: int, unikey: str, curkey: str, like=True
    ) -> SingleReturnResp:
        """Like or unlike."""
        cls = LikeApi if like else UnlikeApi

        return await self.call(cls(params=DolikeParam.model_validate(locals())))

    @t.overload
    async def add_comment(
        self,
        hostuin: int,
        fid: str,
        appid: int,
        content: str,
        *,
        busi_param: t.Optional[dict] = None,
        private: bool = False,
    ) -> AddCommentResp: ...

    @t.overload
    async def add_comment(
        self,
        hostuin: int,
        fid: str,
        appid: int,
        content: str,
        photos: t.Sequence[HttpUrl],
        *,
        feedsType: int = 100,
        private: bool = False,
        abstime: t.Optional[int] = None,
    ) -> AddCommentLegacyResp: ...

    async def add_comment(
        self,
        hostuin: int,
        fid: str,
        appid: int,
        content: str,
        photos: t.Optional[t.Sequence[HttpUrl]] = None,
        busi_param: t.Optional[dict] = None,
        *,
        feedsType: int = 100,
        private=False,
        abstime: t.Optional[int] = None,
    ) -> t.Union[AddCommentResp, AddCommentLegacyResp]:
        """Comment a feed. If :obj:`photos` is given, the legacy comment api will be used.

        :param hostuin: Feed owner uin
        :param fid: :term:`fid`
        :param appid: :term:`appid`
        :param content: comment content
        :param photos: photos to be attached, usually returned by :meth:`.preupload_photos`
        :param busi_param: optional encoded params from :obj:`FeedOperation.operation.busi_param`
        :param abstime: required if `appid != 311`
        :param private: is private comment

        .. seealso:: :meth:`.preupload_photos`, :meth:`.upload_pic`

        .. versionchanged:: 1.9.5.dev1

            added support for legacy comment api (with photos).
        """
        if photos:
            if appid == 311:
                topicId = f"{hostuin}_{fid}__1"
            else:
                assert abstime, "abstime is required if appid != 311"
                topicId = f"{hostuin}_{abstime}"
            return await self.call(
                AddCommentApiLegacy(
                    params=AddCommentParamsLegacy.model_validate(locals(), from_attributes=True)
                )
            )

        busi_param = busi_param or {}
        return await self.call(AddCommentApi(params=AddCommentParams.model_validate(locals())))

    async def delete_comment(
        self,
        hostUin: int,
        topicId: str,
        commentId: int,
        feedsType: int = 100,
        commentUin: t.Optional[int] = None,
    ) -> DeleteCommentResp:
        """Delete a comment.

        :param hostUin: Feed owner uin
        :param topicId:
        :param feedsType:
        :param commentId: id of the comment to be deleted
        :param commentUin: uin of the comment owner, default as None, means the login uin
        """
        if commentUin is None:
            commentUin = self.login.uin
        return await self.call(
            DeleteCommentApi(params=DeleteCommentParams.model_validate(locals()))
        )

    async def publish_mood(
        self,
        content: str,
        photos: t.Optional[t.Sequence[t.Union[PhotoData, PicInfo]]] = None,
        sync_weibo=False,
        ugc_right: UgcRight = UgcRight.all,
    ) -> PublishMoodResp:
        """Publish a feed.

        :param content: feed content
        :param photos: photos to be attached, usually returned by :meth:`.preupload_photos`
        :param sync_weibo: sync to weibo, default to false
        :param ugc_right: access right, default to "Available to Everyone".

        .. seealso:: :meth:`.preupload_photos`, :meth:`.upload_pic`
        """
        photos = photos or []
        return await self.call(
            PublishMoodApi(params=PublishMoodParams.model_validate(locals(), from_attributes=True))
        )

    async def upload_pic(
        self,
        picture: t.Union[bytes, str, PathLike, t.IO[bytes]],
        width: t.Optional[int] = None,
        height: t.Optional[int] = None,
        quality: t.Union[int, float] = 70,
    ) -> UploadPicResponse:
        """
        .. versionchanged:: 1.8.5

            In version <= 1.8.4, user is responsible for compressing a image and this api
            encode the :obj:`picture` with Base64 and send it to Qzone *ASIS* .

            Since version 1.8.5, we recognize a compressed image by :obj:`width` and :obj:`height`
            parameters. If :obj:`width` and :obj:`height` is provided, this API will keep the former
            behavior. If not provided, the image will be compressed with the given quality.
        """
        if isinstance(quality, float):
            if quality < 1:
                quality *= 100
            quality = int(quality)

        assert 0 < quality <= 100

        if isinstance(picture, (str, PathLike, t.IO)):
            params = UploadPicParams.from_image(picture, quality)
        elif (width is None) or (height is None):
            params = UploadPicParams.from_bytes(picture, quality)
        else:
            params = UploadPicParams(
                picture=picture,
                hd_width=width,
                hd_height=height,
                hd_quality=quality,
            )

        return await self.call(UploadPicApi(params=params))

    async def preupload_photos(
        self, upload_pics: t.List[UploadPicResponse], cur_num=0, upload_hd=False
    ) -> PhotosPreuploadResponse:
        """Preupload photos before publishing a feed.

        :param upload_pics: List of :obj:`.UploadPicResponse`, usually returned by :meth:`.upload_pic`

        .. seealso:: :meth:`.upload_pic`
        """
        assert upload_pics
        return await self.call(
            PhotosPreuploadApi(params=PhotosPreuploadParams.model_validate(locals()))
        )

    async def delete_ugc(self, fid: str, appid: int) -> DeleteUgcResp:
        """Delete a feed.

        :param fid: :term:`fid`
        :param appid: :term:`appid`
        """
        return await self.call(
            AddOperationApi(
                params=DeleteUgcParams.model_validate(locals()),
                response=DeleteUgcResp,
            )
        )

    async def avatar(self, hostuin: int, size: t.Literal[100, 640]) -> AvatarResponse:
        """Get avatar from uin. Do not require login.

        :param hostuin: the uin whose avatar to be get
        :param size: availible sizes: `100`|`640`
        """
        return await self.call(
            AvatarApi(
                params=AvatarParams.model_validate(locals()),
            ),
        )
