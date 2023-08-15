from typing import Literal, Union

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

LoginMethod = Union[Literal["qr"], Literal["up"]]


class LoginConfig(BaseSettings):
    uin: int = 0
    """Login uin (qq)."""
    min_login_interval: float = 1800
    """Minimum login interval, in second."""


class UpLoginConfig(LoginConfig):
    pwd: SecretStr = Field(default="")
    """User password."""


class QrLoginConfig(LoginConfig):
    max_refresh_times: int = 6
    """Maximum QR code refresh times."""
    poll_freq: float = 3
    """QR status polling interval."""
