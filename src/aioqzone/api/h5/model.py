import logging

from pydantic import ValidationError
from tenacity import AsyncRetrying, TryAgain, after_log, stop_after_attempt

from aioqzone.api.login import Loginable
from aioqzone.model.api import *
from aioqzone.utils.retry import retry_if_qzone_code, retry_if_status
from qqqr.utils.net import ClientAdapter

log = logging.getLogger(__name__)


class QzoneH5API:
    qzonetoken: str = ""

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

    async def call(self, api: QzoneApi[TyRequest, TyResponse]) -> TyResponse:
        params = api.params.build_params(self.login.uin)
        if api.http_method == "GET":
            data = None
        else:
            data = params
            params = {}

        headers = dict(Referer=api.referer)
        if api.keep_alive:
            headers["Connection"] = "keep-alive"
        if api.accept:
            headers["Accept"] = api.accept

        async for attempt in self._relogin_retry:
            with attempt:
                if (gtk := self.login.gtk) == 0:
                    raise TryAgain
                if api.attach_token:
                    params.update(qzonetoken=self.qzonetoken, g_tk=str(gtk))

                async with self.client.request(
                    api.http_method,
                    api.url,
                    params=params,
                    data=data,
                    headers=headers,
                    cookies=self.login.cookie,
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

        r = await self.call(IndexPageApi(response=IndexPageResp, attach_token=False))
        self.qzonetoken = r.qzonetoken
        log.debug(f"got qzonetoken = {self.qzonetoken}")
        return r

    async def profile(self, hostuin: int, start_time: float = 0) -> ProfilePagePesp:
        """Get profile page of a user.

        :param hostuin: uin of the user
        :param start_time: timestamp in seconds, default as current time.
        """
        return await self.call(
            UserProfileApi(
                params=ProfileParams(hostuin=hostuin, starttime=int(1e3 * start_time)),
                response=ProfilePagePesp,
            )
        )

    async def get_active_feeds(self, attach_info: t.Optional[str] = None) -> FeedPageResp:
        """Get next page. If :obj:`.qzonetoken` is not parsed or :obj:`attach_info` is empty,
        it will call :meth:`.index` and return its response.

        :param attach_info: The ``attach_info`` field from last call.
            Pass an empty string equals to call :meth:`.index`.
        :return: If success, the ``data`` field of the response.
        """
        if not self.qzonetoken or not attach_info:
            return await self.index()

        return await self.call(
            FeedPageApi(
                params=ActiveFeedsParams(attach_info=attach_info),
                response=FeedPageResp,
            )
        )

    async def shuoshuo(
        self, fid: str, hostuin: int, appid=311, busi_param: str = ""
    ) -> DetailResp:
        """This can be used to get the detailed summary of a feed.

        :param fid: aka. ``cellid``
        :param hostuin: uin of the owner of the given feed
        :param appid: appid of the given feed, default as 311
        :param busi_param: optional encoded params
        """
        return await self.call(
            ShuoshuoApi(
                params=ShuoshuoParams(
                    fid=fid, hostuin=hostuin, appid=appid, busi_param=busi_param
                ),
                response=DetailResp,
            )
        )

    async def mfeeds_get_count(self) -> FeedCount:
        """Get new feeds count. This is also the "keep-alive" signal of the cookie."""
        return await self.call(
            GetCountApi(params=GetCountParams(), response=FeedCount),
        )

    async def internal_dolike_app(
        self, appid: int, unikey: str, curkey: str, like=True
    ) -> SingleReturnResp:
        """Like or unlike."""
        if like:
            path = "/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_dolike_app"
        else:
            path = "/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_unlike_app"

        return await self.call(
            DoLikeApi(
                path=path,
                params=DolikeParam(appid=appid, unikey=unikey, curkey=curkey),
                response=SingleReturnResp,
            )
        )

    async def add_comment(
        self, owner_uin: int, fid: str, appid: int, content: str, private=False
    ) -> AddCommentResp:
        """Comment a feed."""
        return await self.call(
            AddCommentApi(
                params=AddCommentParams(
                    ownuin=owner_uin,
                    fid=fid,
                    private=private,
                    content=content,
                    appid=appid,
                ),
                response=AddCommentResp,
            )
        )

    async def publish_mood(
        self,
        content: str,
        photos: t.Optional[t.List[PhotoData]] = None,
        sync_weibo=False,
        ugc_right: UgcRight = UgcRight.all,
    ) -> PublishMoodResp:
        return await self.call(
            PublishMoodApi(
                params=PublishMoodParams(
                    content=content,
                    photos=photos or [],
                    issyncweibo=sync_weibo,
                    ugc_right=ugc_right,
                ),
                response=PublishMoodResp,
            )
        )

    async def upload_pic(
        self, picture: bytes, width: int, height: int, quality: int
    ) -> UploadPicResponse:
        return await self.call(
            UploadPicApi(
                params=UploadPicParams(
                    picture=picture,
                    hd_width=width,
                    hd_height=height,
                    hd_quality=quality,
                ),
                response=UploadPicResponse,
            )
        )

    async def preupload_photos(
        self, photos: t.List[UploadPicResponse], cur_num=0, hd=False
    ) -> PhotosPreuploadResponse:
        assert photos
        return await self.call(
            PhotosPreuploadApi(
                params=PhotosPreuploadParams(
                    upload_pics=photos,
                    currnum=cur_num,
                    upload_hd=int(hd),
                ),
                response=PhotosPreuploadResponse,
            )
        )

    async def delete_ugc(self, fid: str, appid: int) -> DeleteUgcResp:
        return await self.call(
            AddOperationApi(
                params=DeleteUgcParams(fid=fid, appid=appid),
                response=DeleteUgcResp,
            )
        )
