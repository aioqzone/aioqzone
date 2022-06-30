import sys
from dataclasses import dataclass

if sys.version_info >= (3, 9):
    frozen = dataclass(frozen=True, slots=True)
else:
    frozen = dataclass(frozen=True)


@frozen
class PT_QR_APP:
    app: str = ""
    link: str = ""
    register: str = ""
    help: str = ""


@frozen
class Proxy:
    proxy_url: str
    s_url: str


@frozen
class APPID:
    appid: int
    daid: int
