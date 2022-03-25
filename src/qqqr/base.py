import ssl
from abc import ABC, abstractmethod
from typing import Dict, Optional
from urllib.parse import urlencode

from aiohttp import ClientSession as Session
from multidict import istr

from .type import APPID, PT_QR_APP, Proxy

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.46"
CIPHERS = [
    "ECDHE+AESGCM",
    "ECDHE+CHACHA20",
    "DHE+AESGCM",
    "DHE+CHACHA20",
    "ECDH+AESGCM",
    "DH+AESGCM",
    "RSA+AESGCM",
    "!aNULL",
    "!eNULL",
    "!MD5",
    "!DSS",
]
XLOGIN_URL = "https://xui.ptlogin2.qq.com/cgi-bin/xlogin"


def ssl_context():
    c = ssl.create_default_context()
    c.set_ciphers(":".join(CIPHERS))
    return c


class LoginBase(ABC):
    login_sig: str = ""

    def __init__(self, sess: Session, app: APPID, proxy: Proxy, info: Optional[PT_QR_APP] = None):
        self.app = app
        self.proxy = proxy
        self.info = info if info else PT_QR_APP()
        sess.headers.update(
            {istr("DNT"): "1", istr("Referer"): "https://i.qq.com/", istr("User-Agent"): UA}
        )
        self.session = sess
        self.ssl = ssl_context()

    @property
    def xlogin_url(self):
        return (
            XLOGIN_URL
            + "?"
            + urlencode(
                {
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
        )

    async def request(self):
        async with self.session.get(self.xlogin_url, ssl=self.ssl) as r:
            r.raise_for_status()
            self.local_token = int(r.cookies["pt_local_token"].value)
            self.login_sig = r.cookies["pt_login_sig"].value
        return self

    @abstractmethod
    async def login(self, *args, **kwds) -> Dict[str, str]:
        pass

    async def ja3Detect(self) -> dict:
        # for debuging
        async with self.session.get("https://ja3er.com/json", ssl=self.ssl) as r:
            return await r.json()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.session.close()
