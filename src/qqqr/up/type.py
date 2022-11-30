"""Response validation in `qqqr.up.captcha`"""

from typing import List, Optional, Union

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


class PowCfg(BaseModel):
    prefix: str
    md5: str


class CommonCaptchaConf(BaseModel):
    pow_cfg: PowCfg
    """Ians, duration = match_md5(pow_cfg)"""
    tdc_path: str
    """relative path to get tdc.js"""


class Sprite(BaseModel):
    """Represents a sprite from a source material."""

    size_2d: List[int]
    """sprite size (w, h)"""
    sprite_pos: List[int]
    """sprite position on material (x, y)"""
    init_pos: List[int]
    """sprite init position on captcha (x, y)"""

    @property
    def height(self):
        return self.size_2d[1]

    @property
    def width(self):
        return self.size_2d[0]


class BgElemCfg(Sprite):
    img_url: str
    """relative url to get jigsaw puzzle image (background with dimmed piece shape)."""
    init_pos: List[int] = Field(default=[0, 0])


class MoveCfg(BaseModel):
    track_limit: str
    move_factor: List[int]
    data_type: Optional[List[str]]


class FgElemCfg(Sprite):
    id: int
    move_cfg: Optional[MoveCfg] = None


class FgBindingCfg(BaseModel):
    master: int
    slave: int
    bind_type: str
    bind_factor: int


class CaptchaDisplay(BaseModel):
    bg: BgElemCfg = Field(alias="bg_elem_cfg")
    """Background (puzzle)"""
    fg_binding_list: List[FgBindingCfg]
    sprites: List[FgElemCfg] = Field(alias="fg_elem_list")
    """Foreground sprites"""
    sprite_url: str
    """relative url to get jigsaw piece (and handle) image."""


class CaptchaData(BaseModel):
    common: CommonCaptchaConf = Field(alias="comm_captcha_cfg")
    render: CaptchaDisplay = Field(alias="dyn_show_info")


class PrehandleResp(BaseModel):
    captcha: CaptchaData = Field(alias="data", default=None)
    sess: str

    capclass: int = 0
    log_js: str = ""
    randstr: str = ""
    sid: str = ""
    src_1: str = ""
    src_2: str = ""
    src_3: str = ""
    state: int = 0
    subcapclass: int = 0
    ticket: str = ""
    uip: str = ""
    """ipv6"""
