import typing as t
from abc import ABC, abstractmethod
from time import time

from yarl import URL

from .constant import QzoneAppid, QzoneH5Appid, QzoneH5Proxy, QzoneProxy
from .type import APPID, PT_QR_APP, Proxy
from .utils.net import ClientAdapter, get_all_cookie, raise_for_status, use_mobile_ua

XLOGIN_URL = "https://xui.ptlogin2.qq.com/cgi-bin/xlogin"


class LoginSession(ABC):
    """A LoginSession collects all data generated or received during login."""

    login_url: t.Optional[str] = None
    """GET this login url to get cookies."""
    logined: bool = False
    """whether this session is logined."""

    def __init__(self, login_sig: str, *, create_time: t.Optional[float] = None) -> None:
        """
        :param create_time: Set the default value of create_time to the current time when an instance is created
        """
        super().__init__()
        self.create_time = time() if create_time is None else create_time
        self.login_sig = login_sig


_S = t.TypeVar("_S", bound=LoginSession)


class LoginBase(ABC, t.Generic[_S]):
    def __init__(
        self,
        client: ClientAdapter,
        uin: int,
        h5=True,
        app: t.Optional[APPID] = None,
        proxy: t.Optional[Proxy] = None,
        info: t.Optional[PT_QR_APP] = None,
        *args,
        **kwds,
    ):
        """
        :param client: network client
        :param h5: simulate h5 access
        :param app: contains appid and daid. This specify which app you are logining.
        :param proxy: specify where to redirect after login. This can be got from login HTTP request workload.
        :param info: t.Optional, app help link, download link, etc.
        """
        super().__init__(*args, **kwds)
        self.uin = uin
        self.app = app or (QzoneH5Appid if h5 else QzoneAppid)
        self.proxy = proxy or (QzoneH5Proxy if h5 else QzoneProxy)
        self.info = info

        self.client = client
        self.referer = "https://i.qq.com/"

        self.client.headers["DNT"] = "1"
        if h5 or self.app.appid == QzoneH5Appid.appid:
            use_mobile_ua(self.client)
        else:
            from .constant import UA

            if "User-Agent" not in self.client.headers:
                ua = None
            else:
                ua = self.client.headers["User-Agent"].lower()
            if ua is None or any(i in ua for i in ["python", "httpx", "aiohttp"]):
                client.headers["User-Agent"] = UA

    async def deviceId(self) -> str:
        """a js fingerprint.

        .. seealso:: https://github.com/fingerprintjs/fingerprintjs
        """
        return ""  # TODO

    @property
    def login_page_url(self):
        params = {
            "hide_title_bar": 1,
            "style": 22,
            "daid": self.app.daid,
            "low_login": 0,
            "qlogin_auto_login": 1,
            "no_verifyimg": 1,
            "link_target": "blank",
            "appid": self.app.appid,
            "target": "self",
            "s_url": self.proxy.s_url,
            "proxy_url": self.proxy.proxy_url,
            "pt_no_auth": 1,
        }
        if self.info:
            if self.info.app:
                params["pt_qr_app"] = self.info.app
            if self.info.link:
                params["pt_qr_link"] = self.info.link
            if self.info.register:
                params["self_regurl"] = self.info.register
            if self.info.help:
                params["pt_qr_help_link"] = self.info.help

        return URL(XLOGIN_URL).with_query(params)

    @abstractmethod
    async def login(self) -> t.Dict[str, str]:
        """Block until cookie is received."""
        raise NotImplementedError

    async def _pt_login_sig(self) -> str:
        async with self.client.get(self.login_page_url) as response:
            response.raise_for_status()
            return response.cookies["pt_login_sig"].value

    async def _get_login_url(
        self, sess: _S, cur_cookies: t.Optional[t.Mapping[str, t.Any]] = None
    ) -> t.Dict[str, str]:
        assert sess.login_url
        assert not sess.logined, "This session is logined."

        r = {}
        if cur_cookies is not None:
            r.update(cur_cookies)
        async with self.client.get(sess.login_url, allow_redirects=False) as response:
            raise_for_status(response, 302)
            r.update(get_all_cookie(response))
            sess.logined = True

        return r

    @abstractmethod
    async def new(self) -> _S:
        """Create a new :class:`LoginSession`."""
        raise NotImplementedError
