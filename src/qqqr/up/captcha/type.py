"""Response validation in `qqqr.up.captcha`"""

from typing import Optional, Union

from pydantic import BaseModel, HttpUrl


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
    errorCode: int
    randstr: str
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
