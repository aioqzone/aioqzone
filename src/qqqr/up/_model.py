"""Response validation in `qqqr.up.captcha`"""

from typing import Union

from pydantic import BaseModel, Field, HttpUrl


class CheckResp(BaseModel):
    code: int
    """code = 0/2/3 hideVC; code = 1 showVC
    """
    verifycode: str
    salt_repr: str = Field(alias="salt")
    verifysession: str
    isRandSalt: int
    ptdrvs: str
    session: str

    @property
    def salt(self):
        salt = self.salt_repr.split(r"\x")[1:]
        salt = [chr(int(i, 16)) for i in salt]
        return "".join(salt)


class LoginResp(BaseModel):
    code: int
    url: Union[HttpUrl, str]
    msg: str
    nickname: str


class VerifyResp(BaseModel):
    code: int = Field(alias="errorCode")
    verifycode: str = Field(alias="randstr")
    ticket: str
    errMessage: str
    sess: str
