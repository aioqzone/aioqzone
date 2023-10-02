import typing as t

from tylisten import hookdef

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
def login_success(uin: int):
    ...


@hookdef
def login_failed(uin: int, exc: t.Union[BaseException, str]):
    ...
