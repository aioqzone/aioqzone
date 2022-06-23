from typing import Union

from pydantic import BaseModel
from pydantic.networks import HttpUrl


class PollResp(BaseModel):
    code: int
    url: Union[HttpUrl, str]
    msg: str
    nickname: str
