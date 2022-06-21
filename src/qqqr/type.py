from dataclasses import dataclass
from platform import python_version_tuple

if int(python_version_tuple()[1]) >= 10:
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
