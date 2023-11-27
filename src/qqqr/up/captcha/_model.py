from typing import List, Optional

from pydantic import BaseModel, Field


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

    @property
    def box(self):
        l, t = self.sprite_pos
        return (l, t, l + self.width, l + self.height)


class ClickCfg(BaseModel):
    mark_style: str
    data_type: List[str]


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


class CaptchaData(BaseModel):
    common: CommonCaptchaConf = Field(alias="comm_captcha_cfg")
    render: dict = Field(alias="dyn_show_info")


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
    """ipv4 / ipv6"""
