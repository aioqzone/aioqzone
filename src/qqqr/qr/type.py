import typing as t

from pydantic import BaseModel
from pydantic.networks import HttpUrl


class PollCookie(BaseModel):
    supertoken: str
    superkey: str
    pt_guid_sig: str
    pt_recent_uins: str
    ptcz: str


class PollResp(BaseModel):
    code: int
    url: t.Union[HttpUrl, str]
    msg: str
    nickname: str
    cookies: t.Optional[PollCookie] = None
