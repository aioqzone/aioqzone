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


@dataclass
class CheckResult:
    code: int
    """code = 0/2/3 hideVC; code = 1 showVC
    """
    verifycode: str
    salt: str
    verifysession: str
    isRandSalt: int
    ptdrvs: str
    session: str

    def __post_init__(self):
        self.code = int(self.code)
        self.isRandSalt = int(self.isRandSalt)
        salt = self.salt.split(r"\x")[1:]
        salt = [chr(int(i, 16)) for i in salt]
        self.salt = "".join(salt)
