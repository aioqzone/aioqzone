from pydantic import BaseModel
from pydantic.networks import HttpUrl


class PollResp(BaseModel):
    code: int
    url: HttpUrl
    msg: str
    my_name: str
