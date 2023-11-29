import typing as t

from pydantic import BaseModel
from pydantic.networks import HttpUrl

from qqqr.type import RedirectCookies


class PollResp(BaseModel):
    code: int
    url: t.Union[HttpUrl, str]
    msg: str
    nickname: str
    cookies: t.Optional[RedirectCookies] = None
