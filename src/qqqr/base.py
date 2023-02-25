from abc import ABC, abstractmethod
from time import time
from typing import Dict, Generic, Optional, TypeVar

from .constant import UA, QzoneH5Proxy
from .type import APPID, PT_QR_APP, Proxy
from .utils.net import ClientAdapter, get_all_cookie, raise_for_status


class LoginSession(ABC):
    """A LoginSession collects all data generated or received during login."""

    login_url: Optional[str] = None
    """GET this login url to get cookies."""
    logined: bool = False
    """whether this session is logined."""

    def __init__(self, *, create_time: float = ...) -> None:
        """
        :param create_time: Set the default value of create_time to the current time when an instance is created
        """
        super().__init__()
        self.create_time = time() if create_time == ... else create_time


_S = TypeVar("_S", bound=LoginSession)


class LoginBase(ABC, Generic[_S]):
    def __init__(
        self, client: ClientAdapter, app: APPID, proxy: Proxy, info: Optional[PT_QR_APP] = None
    ):
        """
        :param client: network client
        :param app: contains appid and daid. This specify which app you are logining.
        :param proxy: specify where to redirect after login. This can be got from login HTTP request workload.
        :param info: Optional, app help link, download link, etc.
        """
        super().__init__()
        self.app = app
        self.proxy = proxy
        self.info = info

        self.client = client
        self.referer = "https://i.qq.com/"

        self.client.headers["DNT"] = "1"
        for blackword in ["python", "httpx", "aiohttp"]:
            if blackword in self.client.ua.lower():
                self.ua = UA
                break

    @abstractmethod
    async def login(self) -> Dict[str, str]:
        """Block until cookie is received."""
        raise NotImplementedError

    async def _get_login_url(self, sess: _S):
        assert sess.login_url
        assert not sess.logined, "This session is logined."
        async with self.client.get(sess.login_url, follow_redirects=False) as r:
            raise_for_status(r, 302)
            r = get_all_cookie(r)
            sess.logined = True
            return r

    @abstractmethod
    async def new(self) -> _S:
        """Create a new :class:`LoginSession`."""
        raise NotImplementedError
