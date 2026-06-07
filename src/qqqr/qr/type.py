"""QR login API response models.

TypedDicts for poll, fetch_device_uin, and push_qr API responses.
"""

import typing as t

from pydantic import BaseModel, Field
from pydantic.networks import HttpUrl

from qqqr.type import RedirectCookies


class PollResp(BaseModel):
    """Response from the QR poll API."""

    code: int  #: status code (see :class:`~qqqr.constant.StatusCode`)
    url: t.Union[HttpUrl, str]  #: callback URL after authentication
    msg: str  #: result message
    nickname: str  #: user nickname
    cookies: t.Optional[RedirectCookies] = None  #: redirect cookies


class FetchDevUinResp(BaseModel):
    """Response from the fetch_device_uin API."""

    code: int = Field(validation_alias="errcode")  #: result code
    uin_list: t.List[int] = Field(
        default_factory=list, validation_alias="data"
    )  #: device QQ number list


class PushQrResp(BaseModel):
    """Response from the push_qr API."""

    code: int = Field(validation_alias="ec")  #: result code
    message: str = Field(default="", validation_alias="em")  #: result message
