from dataclasses import dataclass


@dataclass(frozen=True)
class PT_QR_APP:
    app: str = ""
    link: str = ""
    register: str = ""
    help: str = ""


@dataclass(frozen=True)
class Proxy:
    proxy_url: str
    s_url: str


@dataclass(frozen=True)
class APPID:
    appid: int
    daid: int
