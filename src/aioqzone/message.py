from typing import Literal, Union

from pydantic import BaseModel
from tylisten import BaseMessage

from qqqr.message import *

LoginMethod = Union[Literal["qr"], Literal["up"]]


class login_success(BaseModel, BaseMessage):
    uin: int
    method: LoginMethod


class login_failed(BaseModel, BaseMessage):
    uin: int
    method: LoginMethod
    exc: str
