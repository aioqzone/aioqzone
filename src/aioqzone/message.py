import typing as t

from tylisten import hookdef

from qqqr.message import *

__all__ = [
    "qr_cancelled",
    "qr_fetched",
    "sms_code_input",
    "solve_select_captcha",
    "solve_slide_captcha",
    "login_success",
    "login_failed",
]


@hookdef
def login_success(uin: int):
    """Login success.

    :param uin: login uin
    """
    ...


@hookdef
def login_failed(uin: int, exc: t.Union[BaseException, str]):
    """Login failed.

    :param uin: login uin
    :param exc: exception or error message
    """
    ...
