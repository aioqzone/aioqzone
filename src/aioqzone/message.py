from pydantic import BaseModel
from tylisten import BaseMessage

from aioqzone.model import LoginMethod
from qqqr.message import *

__all__ = [
    "qr_cancelled",
    "qr_fetched",
    "qr_refresh",
    "sms_code_input",
    "sms_code_required",
    "login_success",
    "login_failed",
]


class login_success(BaseModel, BaseMessage):
    uin: int
    method: LoginMethod


class login_failed(BaseModel, BaseMessage):
    uin: int
    method: LoginMethod
    exc: str
