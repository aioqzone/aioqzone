from tylisten import hookdef

from aioqzone.model import LoginMethod
from qqqr.message import *

__all__ = [
    "qr_cancelled",
    "qr_fetched",
    "qr_refresh",
    "sms_code_input",
    "login_success",
    "login_failed",
]


@hookdef
def login_success(uin: int, method: LoginMethod):
    ...


@hookdef
def login_failed(uin: int, method: LoginMethod, exc: str):
    ...
