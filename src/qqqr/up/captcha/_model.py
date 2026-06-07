"""Captcha API response models.

TypedDicts and BaseModels for the tcaptcha prehandle response, including
PoW config, render info, and sprite definitions.
"""

import typing as t

from pydantic import AliasPath, BaseModel, Field, TypeAdapter
from typing_extensions import TypedDict


class PowCfg(TypedDict):
    """PoW (Proof of Work) configuration for tcaptcha."""

    prefix: str
    md5: str


class CommonCaptchaConf(TypedDict):
    """Common captcha configuration from the server."""

    pow_cfg: PowCfg
    """Ians, duration = match_md5(pow_cfg)"""
    tdc_path: str
    """relative path to get tdc.js"""


class CommonClickConf(TypedDict):
    """Click configuration for captcha render."""

    data_type: t.Annotated[str, Field(validation_alias=AliasPath("data_type", 0))]
    mark_style: str


class CommonBgElmConf(BaseModel):
    """Background element configuration model."""

    cfg: CommonClickConf = Field(validation_alias="click_cfg")


class CommonRender(BaseModel):
    """Common render configuration from captcha response."""

    bg: CommonBgElmConf = Field(validation_alias="bg_elem_cfg")


class Sprite(BaseModel):
    """Represents a sprite from a source material."""

    size_2d: t.List[int]
    """sprite size (w, h)"""
    sprite_pos: t.List[int]
    """sprite position on material (x, y)"""

    @property
    def height(self):
        return self.size_2d[1]

    @property
    def width(self):
        return self.size_2d[0]

    @property
    def box(self):
        """Bounding box as (left, top, right, bottom) tuple."""
        l, t = self.sprite_pos
        return (l, t, l + self.width, l + self.height)


class CaptchaData(TypedDict):
    """Full captcha data from prehandle response."""

    common: t.Annotated[CommonCaptchaConf, Field(alias="comm_captcha_cfg")]
    render: t.Annotated[dict[str, t.Any], Field(alias="dyn_show_info")]


class PrehandleResp(TypedDict):
    """Prehandle API response type containing captcha data."""

    captcha: t.Annotated[t.Optional[CaptchaData], Field(alias="data", default=None)]
    sess: str

    capclass: t.Annotated[int, Field(default=0)]
    log_js: t.Annotated[str, Field(default="")]
    randstr: t.Annotated[str, Field(default="")]
    sid: t.Annotated[str, Field(default="")]
    src_1: t.Annotated[str, Field(default="")]
    src_2: t.Annotated[str, Field(default="")]
    src_3: t.Annotated[str, Field(default="")]
    state: t.Annotated[int, Field(default=0)]
    subcapclass: t.Annotated[int, Field(default=0)]
    ticket: t.Annotated[str, Field(default="")]
    uip: t.Annotated[str, Field(default="")]
    """ipv4 / ipv6"""


PrehandleRespValidator = TypeAdapter(PrehandleResp)
