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
        if api.attach_token:
            params = dict(qzonetoken=self.qzonetoken, g_tk=str(self.login.gtk))
        else:
            params = dict()

        data = api.params.build_params(self.login.uin)
        if api.http_method == "GET":
            params.update(data)
            data = None

        self.client.referer = "https://h5.qzone.qq.com/"
        async for attempt in self._relogin_retry:
            with attempt:
                if params.get("g_tk") == 0:
                    raise TryAgain
                async with self.client.request(
                    api.http_method, api.url, params=params, data=data, cookies=self.login.cookie
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

        r = await self.call(FeedPageApi(response=IndexPageResp, attach_token=False))
        assert isinstance(r, IndexPageResp)
        self.qzonetoken = r.qzonetoken
        log.debug(f"got qzonetoken = {self.qzonetoken}")
        return r

    async def get_active_feeds(self, attach_info: str) -> FeedPageResp:
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
    ) -> GetMoreResp:
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
                response=GetMoreResp,
            )
        )

    async def mfeeds_get_count(self) -> FeedCount:
        return await self.call(
            GetCountApi(params=GetCountParams(), response=FeedCount),
        )

    async def internal_dolike_app(
        self, appid: int, unikey: str, curkey: str, like=True
    ) -> SingleReturnResp:
        if like:
            path = "/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_dolike_app"
        else:
            path = "/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_unlike_app"

        return await self.call(
            QzoneApi(
                http_method="GET",
                path=path,
                params=DolikeParam(appid=appid, unikey=unikey, curkey=curkey),
                response=SingleReturnResp,
            )
        )

    async def add_comment(self, ownuin: int, srcId: str, appid: int, content: str, private=False):
        return await self.call(
            AddCommentApi(
                params=AddCommentParams(
                    ownuin=ownuin,
                    srcId=srcId,
                    isPrivateComment=private,
                    content=content,
                    appid=appid,
                ),
                response=SingleReturnResp,
            )
        )
