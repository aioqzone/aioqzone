from typing import Literal, Union

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


class LoginConfig(BaseSettings):
    uin: int = 0
    """Login uin (qq)."""


class UpLoginConfig(LoginConfig):
    pwd: SecretStr = Field(default="")
    """User password."""


class QrLoginConfig(LoginConfig):
    max_refresh_times: int = 6
    """Maximum QR code refresh times."""
    poll_freq: float = 3
    """QR status polling interval."""
