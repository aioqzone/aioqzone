from pydantic import BaseModel


class PollResp(BaseModel):
    code: int
    url: str
    msg: str
    my_name: str
