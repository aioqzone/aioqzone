from dataclasses import dataclass

@dataclass
class PT_QR_APP:
    app: str
    link: str
    register: str
    help: str

@dataclass
class Proxy:
    proxy_url: str
    s_url: str

@dataclass
class APPID:
    appid: int
    daid: int
