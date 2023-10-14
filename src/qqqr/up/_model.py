"""Response validation in `qqqr.up.captcha`"""

from typing import List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, model_validator

from qqqr.utils.jsjson import json_loads


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

    @property
    def height(self):
        return self.size_2d[1]

    @property
    def width(self):
        return self.size_2d[0]


class SlideBgElemCfg(Sprite):
    img_url: str
    """relative url to get jigsaw puzzle image (background with dimmed piece shape)."""
    init_pos: List[int] = Field(default=[0, 0])
    """sprite init position on captcha (x, y)"""


class ClickCfg(BaseModel):
    mark_style: str
    data_type: List[str]


class SelectBgElemCfg(Sprite):
    click_cfg: ClickCfg
    img_url: str


class MoveCfg(BaseModel):
    track_limit: str
    move_factor: List[int]
    data_type: Optional[List[str]] = None


class FgElemCfg(Sprite):
    id: int
    init_pos: List[int]
    move_cfg: Optional[MoveCfg] = None


class FgBindingCfg(BaseModel):
    master: int
    slave: int
    bind_type: str
    bind_factor: int


class SlideCaptchaDisplay(BaseModel):
    bg: SlideBgElemCfg = Field(alias="bg_elem_cfg")
    """Background (puzzle)"""
    fg_binding_list: List[FgBindingCfg] = Field(default=[])
    sprites: List[FgElemCfg] = Field(alias="fg_elem_list")
    """Foreground sprites"""
    sprite_url: str
    """relative url to get jigsaw piece (and handle) image."""


class SelectRegion(BaseModel):
    id: int
    range: List[int]


class SelectJsonPayload(BaseModel):
    select_region_list: List[SelectRegion]
    prompt_id: int
    picture_ids: List[int]


class SelectCaptchaDisplay(BaseModel):
    instruction: str
    bg: SelectBgElemCfg = Field(alias="bg_elem_cfg")
    verify_trigger_cfg: dict
    color_scheme: str  # pydantic_extra_types.color
    json_payload: SelectJsonPayload

    @model_validator(mode="before")
    def parse_json(cls, v: dict):
        v["json_payload"] = json_loads(v["json_payload"])
        return v


class CaptchaData(BaseModel):
    common: CommonCaptchaConf = Field(alias="comm_captcha_cfg")
    render: Union[SlideCaptchaDisplay, SelectCaptchaDisplay] = Field(alias="dyn_show_info")


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
