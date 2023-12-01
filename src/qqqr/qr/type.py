import typing as t

from pydantic import BaseModel, Field
from pydantic.networks import HttpUrl

from qqqr.type import RedirectCookies


class PollResp(BaseModel):
    code: int
    url: t.Union[HttpUrl, str]
    msg: str
    nickname: str
    cookies: t.Optional[RedirectCookies] = None


class FetchDevUinResp(BaseModel):
    code: int = Field(validation_alias="errcode")
    uin_list: t.List[int] = Field(default_factory=list, validation_alias="data")


class PushQrResp(BaseModel):
    code: int = Field(validation_alias="ec")
    message: str = Field(default="", validation_alias="em")
