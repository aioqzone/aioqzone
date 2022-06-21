"""Response validation in `qqqr.up.captcha`"""

from typing import Optional, Union

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


class PrehandleResp(BaseModel):
    state: int
    ticket: str
    capclass: int
    subcapclass: int
    src_1: str
    src_2: str
    src_3: str
    sess: str
    randstr: str
    sid: int


class VerifyResp(BaseModel):
    code: int = Field(alias="errorCode")
    verifycode: str = Field(alias="randstr")
    ticket: str
    errMessage: str
    sess: str


class PowCfg(BaseModel):
    md5: str
    prefix: str


class CaptchaConfig(BaseModel):
    htdocsPath: Optional[HttpUrl] = None
    lang: Optional[int] = 1
    color: str = ""
    tdcHtdocsPath: str = ""
    dcFileName: str
    vmFileName: str = ""
    noheader: int = 1
    showtype: str = ""
    theme: str = ""
    uid: str = ""
    subcapclass: str = ""
    aid: str = ""
    uip: str
    clientype: str = ""
    websig: str = ""
    collectdata: str = "collect"
    asig: str = ""
    buid: str = ""
    vmData: str = ""
    vsig: str = ""
    dst: str = ""
    nonce: str
    capSrc: str = ""
    spt: int
    curenv: str = ""
    fwidth: Union[int, str] = ""
    slink: str = ""
    sess: str
    cdnPic1: str
    cdnPic2: str
    iscdn: int = 1
    vmByteCode: str
    vmAvailable: str
    TuCao: Optional[HttpUrl] = None
    ticket: str
    randstr: str
    powCfg: PowCfg
