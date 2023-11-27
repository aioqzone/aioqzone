from abc import ABC, abstractmethod
from time import time
from typing import Dict, Generic, Optional, TypeVar

from .constant import QzoneAppid, QzoneH5Appid, QzoneH5Proxy, QzoneProxy
from .type import APPID, PT_QR_APP, Proxy
from .utils.net import ClientAdapter, get_all_cookie, raise_for_status, use_mobile_ua

XLOGIN_URL = "https://xui.ptlogin2.qq.com/cgi-bin/xlogin"


class LoginSession(ABC):
    """A LoginSession collects all data generated or received during login."""

    login_url: Optional[str] = None
    """GET this login url to get cookies."""
    logined: bool = False
    """whether this session is logined."""

    def __init__(self, login_sig: str, *, create_time: Optional[float] = None) -> None:
        """
        :param create_time: Set the default value of create_time to the current time when an instance is created
        """
        super().__init__()
        self.create_time = time() if create_time is None else create_time
        self.login_sig = login_sig


_S = TypeVar("_S", bound=LoginSession)


class LoginBase(ABC, Generic[_S]):
    def __init__(
        self,
        client: ClientAdapter,
        uin: int,
        h5=True,
        app: Optional[APPID] = None,
        proxy: Optional[Proxy] = None,
        info: Optional[PT_QR_APP] = None,
        *args,
        **kwds,
    ):
        """
        :param client: network client
        :param h5: simulate h5 access
        :param app: contains appid and daid. This specify which app you are logining.
        :param proxy: specify where to redirect after login. This can be got from login HTTP request workload.
        :param info: Optional, app help link, download link, etc.
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

    @abstractmethod
    async def login(self) -> Dict[str, str]:
        """Block until cookie is received."""
        raise NotImplementedError

    async def _get_login_url(self, sess: _S):
        assert sess.login_url
        assert not sess.logined, "This session is logined."
        async with self.client.get(sess.login_url, allow_redirects=False) as r:
            raise_for_status(r, 302)
            r = get_all_cookie(r)
            sess.logined = True
            return r

    @abstractmethod
    async def new(self) -> _S:
        """Create a new :class:`LoginSession`."""
        raise NotImplementedError
