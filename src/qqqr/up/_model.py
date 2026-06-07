"""Response models for UP login APIs.

Defines :class:`CheckResp`, :class:`LoginResp`, and :class:`VerifyResp`
used by the UP login flow.
"""

import typing as t

from pydantic import BaseModel, Field, HttpUrl, TypeAdapter

from qqqr.type import RedirectCookies


class CheckResp(t.NamedTuple):
    """Response from the ``check`` API.

    Fields: code, uin, session, isRandSalt, salt, ptdrvs, verifycode, verifysession.
    """

    code: int
    """code = 0/2/3 hideVC; code = 1 showVC
    """
    verifycode: str
    salt_repr: t.Annotated[str, Field(alias="salt")]
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
    """Response from the ``login`` API."""

    code: int  #: Status code (see :class:`~qqqr.constant.StatusCode`)
    url: t.Union[HttpUrl, str]
    msg: str
    nickname: str
    pt_ev_token: str = ""
    cookies: t.Optional[RedirectCookies] = None  #: Login cookies on success


class VerifyResp(BaseModel):
    """Response from the captcha verify API."""

    code: int = Field(alias="errorCode")  #: Verification result code
    verifycode: str = Field(alias="randstr")
    ticket: str  #: Verification ticket
    errMessage: str
    sess: str


CheckRespValidator = TypeAdapter(CheckResp)
