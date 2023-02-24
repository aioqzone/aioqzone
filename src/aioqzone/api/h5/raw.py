from aioqzone.api.loginman import Loginable
from qqqr.utils.net import ClientAdapter


class QzoneH5RawAPI:
    host = "https://user.qzone.qq.com"

    def __init__(self, client: ClientAdapter, loginman: Loginable) -> None:
        super().__init__()
        self.client = client
        self.login = loginman
