import logging
import re
from functools import wraps
from typing import Callable, Dict, List, Optional, Tuple, Union

from lxml.html import fromstring

from aioqzone.api.loginman import Loginable
from aioqzone.exception import QzoneError
from aioqzone.utils.catch import HTTPStatusErrorDispatch, QzoneErrorDispatch
from aioqzone.utils.regex import entire_closing, response_callback
from jssupport.jsjson import JsonValue, json_loads
from qqqr.utils.net import ClientAdapter

StrDict = Dict[str, JsonValue]


log = logging.getLogger(__name__)


class QzoneH5RawAPI:
    host = "https://h5.qzone.qq.com"
    qzonetoken: str = ""

    def __init__(self, client: ClientAdapter, loginman: Loginable) -> None:
        """
        .. warning:: If `loginman` uses an `AsyncClient`, the `client` param MUST use this client as well.
        """
        super().__init__()
        self.client = client
        self.login = loginman

    def host_get(
        self,
        path: str,
        params: Optional[dict] = None,
        *,
        attach_token=True,
        host: Optional[str] = None,
        **kw,
    ):
        if params is None:
            params = {}
        if "p_skey" not in self.login.cookie:
            raise QzoneError(-3000, "未登录")
        if attach_token:
            params["qzonetoken"] = self.qzonetoken
            params["g_tk"] = str(self.login.gtk)
            self.client.referer = "https://h5.qzone.qq.com/"
        host = host or self.host
        return self.client.get(host + path, params=params, **kw)

    def host_post(
        self,
        path: str,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        *,
        attach_token=True,
        host: Optional[str] = None,
        **kw,
    ):
        if params is None:
            params = {}
        if "p_skey" not in self.login.cookie:
            raise QzoneError(-3000, "未登录")
        if attach_token:
            params["qzonetoken"] = self.qzonetoken
            params["g_tk"] = str(self.login.gtk)
        self.client.referer = "https://h5.qzone.qq.com/"
        host = host or self.host
        return self.client.post(self.host + path, params=params, data=data, **kw)

    def _relogin_retry(self, func: Callable):
        """A decorator which will relogin and retry given func if cookie expired.

        'cookie expired' is indicated by:

        - `aioqzone.exception.QzoneError` code -3000 or -4002
        - HTTP response code 403

        :meta public:
        :param func: a callable, which should be rerun after login expired and relogin.

        .. note:: Decorate code as less as possible
        .. warning::

                You *SHOULD* **NOT** wrap a function with mutable input. If you change the mutable
                var in the first attempt, in the second attempt the var saves the changed value.
        """

        @wraps(func)
        async def relogin_wrapper(*args, **kwds):
            """
            This wrapper will call :meth:`aioqzone.event.login.Loginable.new_cookie` if the wrapped
            function raises an error indicating that a new login is required.

            The exceptions this wrapper may raise depends on the login manager you passed in.
            Any exceptions irrelevent to "login needed" will be passed through w/o any change.

            :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.
            """

            with QzoneErrorDispatch() as qze, HTTPStatusErrorDispatch() as hse:
                qze.dispatch(-3000, suppress=lambda e: "登录" in e.msg)  # -3000: 请先登录
                qze.dispatch(-10000)
                hse.dispatch(302, 403)
                return await func(*args, **kwds)

            log.info(f"Cookie expire in {func.__qualname__}. Relogin...")
            cookie = await self.login.new_cookie()
            try:
                self.client.cookies.update(cookie)
            except:
                log.error("Error when updating client cookies", exc_info=True)
                # since actually we often use the same client in loginman and QzoneAPI,
                # it is not essential to update cookies.
            return await func(*args, **kwds)

        return relogin_wrapper

    def _rtext_handler(
        self,
        robj: Union[str, StrDict],
        cb: bool = True,
        errno_key: Tuple[str, ...] = ("code", "err"),
        msg_key: Tuple[str, ...] = ("message", "msg"),
        data_key: Optional[str] = None,
    ) -> StrDict:
        """Handles the response text recieved from Qzone API, returns the parsed json dict.

        :meta public:
        :param rtext: response text
        :param cb: The text is to be parsed by callback_regex, defaults to True.
        :param errno_key: Error # key, defaults to ('code', 'err').
        :param msg_key: Error message key, defaults to ('msg', 'message').

        :raise `aioqzone.exception.QzoneError`: if errno != 0

        :return: json response
        """
        if isinstance(robj, str):
            if cb:
                match = response_callback.search(robj)
                assert match
                robj = match.group(1)
            r = json_loads(robj)
        else:
            r = robj

        assert isinstance(r, dict)

        err = next(filter(lambda i: i is not None, (r.get(i) for i in errno_key)), None)
        assert err is not None, f"no {errno_key} in {r.keys()}"
        assert isinstance(err, (int, str))
        err = int(err)

        if err != 0:
            msg = next(filter(None, (r.get(i) for i in msg_key)), None)
            if msg:
                raise QzoneError(err, msg, rdict=r)
            else:
                raise QzoneError(err, rdict=r)

        return r[data_key] if data_key is not None else r  # type: ignore

    async def index(self) -> StrDict:
        """This api is the redirect page after h5 login, which is also the landing (main) page of h5 qzone.

        :raise RuntimeError: if any failure occurs in data parsing.
        """

        @self._relogin_retry
        async def retry_closure():
            async with self.host_get("/mqzone/index", attach_token=False) as r:
                r.raise_for_status()
                return r.text

        html = await retry_closure()
        scripts: List = fromstring(html).xpath('body/script[@type="application/javascript"]')
        if not scripts:
            log.debug(html)
            raise RuntimeError("script tag not found")

        texts: List[str] = [s.text for s in scripts]
        script = next(filter(lambda s: "shine0callback" in s, texts), None)
        if not script:
            raise RuntimeError("data script not found")

        m = re.search(r'window\.shine0callback.*return "([0-9a-f]+?)";', script)
        if m is None:
            raise RuntimeError("data script not found")

        self.qzonetoken = m.group(1)
        log.debug(f"got qzonetoken = {self.qzonetoken}")

        m = re.search(r"var FrontPage =.*?data\s*:\s*\{", script)
        if m is None:
            raise RuntimeError("page data not found")
        data = script[m.end() - 1 : m.end() + entire_closing(script[m.end() - 1 :])]
        return self._rtext_handler(data, cb=False, errno_key=("code", "ret"), data_key="data")

    async def get_active_feeds(self, attach_info: str) -> StrDict:
        """Get next page. If :obj:`.qzonetoken` is not parsed or `attach_info` is empty,
        it will call :meth:`index` and return its response.

        :param attach_info: The ``attach_info`` field from last call.
            Pass an empty string equals to call :meth:`.index`.
        :return: If success, the ``data`` field of the response.
        """
        if not self.qzonetoken or not attach_info:
            return await self.index()

        data = dict(
            res_type=0,
            res_attach=attach_info,
            refresh_type=2,
            format="json",
            attach_info=attach_info,
        )
        log.debug("get_active_feeds post data:", data)

        @self._relogin_retry
        async def retry_closure() -> StrDict:
            async with self.host_post("/webapp/json/mqzone_feeds/getActiveFeeds", data=data) as r:
                r.raise_for_status()
                return r.json()

        return self._rtext_handler(
            await retry_closure(), cb=False, errno_key=("code", "ret"), data_key="data"
        )

    async def shuoshuo(self, fid: str, hostuin: int, appid=311, busi_param: str = ""):
        """This can be used to get the detailed summary of a feed.

        :param fid: aka. cellid
        :param hostuin: uin of the owner of the given feed
        :param appid: appid of the given feed, default as 311
        :param busi_param: optional encoded params
        """
        data = dict(
            format="json",
            appid=appid,
            uin=hostuin,
            count=20,
            refresh_type=31,
            cellid=fid,
            subid="",
        )
        if busi_param and len(busi_param) < 100:
            data["busi_param"] = busi_param

        @self._relogin_retry
        async def retry_closure() -> StrDict:
            async with self.host_get("/webapp/json/mqzone_detail/shuoshuo", data) as r:
                r.raise_for_status()
                return r.json()

        return self._rtext_handler(await retry_closure(), cb=False, data_key="data")

    async def mfeeds_get_count(self) -> StrDict:
        @self._relogin_retry
        async def retry_closure() -> StrDict:
            async with self.host_get(
                "/feeds/mfeeds_get_count", dict(format="json"), host="https://mobile.qzone.qq.com"
            ) as r:
                r.raise_for_status()
                return r.json()

        return self._rtext_handler(await retry_closure(), cb=False, data_key="data")

    async def internal_dolike_app(self, appid: int, unikey: str, curkey: str, like=True):
        data = dict(
            opuin=self.login.uin,
            unikey=unikey,
            curkey=curkey,
            appid=appid,
            opr_type="like",
            format="purejson",
        )
        if like:
            path = "/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_dolike_app"
        else:
            path = "/proxy/domain/w.qzone.qq.com/cgi-bin/likes/internal_unlike_app"

        @self._relogin_retry
        async def retry_closure() -> StrDict:
            async with self.host_get(path, data) as r:
                r.raise_for_status()
                return r.json()

        self._rtext_handler(await retry_closure(), errno_key=("ret",), cb=False)
        return True

    async def add_comment(self, ownuin: int, srcId: str, appid: int, content: str, private=False):
        assert content, "comment should not be empty"
        assert len(content) <= 2000, "comment maxlen=2000"

        data = dict(
            ownuin=str(ownuin),
            srcId=srcId,
            uin=self.login.uin,
            isPrivateComment=int(private),
            content=content,
            appid=appid,
            bypass_param={},
            busi_param={},
        )
        log.debug("add_comment post data:", data)

        @self._relogin_retry
        async def retry_closure() -> StrDict:
            async with self.host_post("/webapp/json/qzoneOperation/addComment", data=data) as r:
                r.raise_for_status()
                return r.json()

        return self._rtext_handler(
            await retry_closure(), cb=False, errno_key=("ret",), data_key="data"
        )
