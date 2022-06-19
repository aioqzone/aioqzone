from abc import ABC, abstractmethod
from time import time
from typing import Dict, Generic, Optional, TypeVar, Union

import httpx
from httpx import AsyncClient

from .type import APPID, PT_QR_APP, Proxy
from .utils.net import get_all_cookie, raise_for_status

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.46"


class LoginSession(ABC):
    login_url: Optional[str] = None
    logined: bool = False

    def __init__(self, create_time: float = ...) -> None:
        super().__init__()
        self.create_time = time() if create_time == ... else create_time


_S = TypeVar("_S", bound=LoginSession)


class LoginBase(ABC, Generic[_S]):
    login_sig: str = ""

    def __init__(
        self, client: AsyncClient, app: APPID, proxy: Proxy, info: Optional[PT_QR_APP] = None
    ):
        self.app = app
        self.proxy = proxy
        self.info = info if info else PT_QR_APP()

        self.client = client
        self.referer = "https://i.qq.com/"
        self.ua = UA
        self.client.headers["DNT"] = "1"

    @property
    def referer(self):
        return self.client.headers["Referer"]

    @referer.setter
    def referer(self, value: str):
        self.client.headers["Referer"] = value

    @property
    def ua(self):
        return self.client.headers["User-Agent"]

    @ua.setter
    def ua(self, value: str):
        self.client.headers["User-Agent"] = value

    @property
    def xlogin_url(self):
        return httpx.URL("https://xui.ptlogin2.qq.com/cgi-bin/xlogin").copy_with(
            params={
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
                "pt_qr_app": self.info.app,
                "pt_qr_link": self.info.link,
                "self_regurl": self.info.register,
                "pt_qr_help_link": self.info.help,
                "pt_no_auth": 1,
            }
        )

    async def request(self):
        r = await self.client.get(self.xlogin_url)
        r.raise_for_status()
        self.local_token = int(r.cookies["pt_local_token"])
        self.login_sig = r.cookies["pt_login_sig"]
        return self

    @abstractmethod
    async def login(self) -> Dict[str, str]:
        """Block until cookie is received."""
        raise NotImplementedError

    async def _get_login_url(self, login_url: Union[str, httpx.URL]):
        r = await self.client.get(login_url, follow_redirects=False)
        raise_for_status(r, 302)
        return get_all_cookie(r)

    @abstractmethod
    async def new(self) -> _S:
        raise NotImplementedError
