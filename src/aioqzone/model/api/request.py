import typing as t

from pydantic import BaseModel, Field

from aioqzone.utils.time import time_ms

__all__ = [
    "QzoneRequestParams",
    "ActiveFeedsParams",
    "ShuoshuoParams",
    "GetCountParams",
    "DolikeParam",
    "AddCommentParams",
    "PublishMoodParams",
    "DeleteUgcParams",
]


class QzoneRequestParams(BaseModel):
    uin_fields: t.ClassVar[t.Tuple[str, ...]] = ()
    ts_fields: t.ClassVar[t.Tuple[str, ...]] = ()

    def build_params(self, uin: int, timestamp: t.Optional[float] = None):
        d = self.model_dump(mode="json", by_alias=True)
        d.update({i: uin for i in self.uin_fields})
        if self.ts_fields:
            timestamp = time_ms(timestamp)
            d.update({i: timestamp for i in self.ts_fields})
        return d


class ActiveFeedsParams(QzoneRequestParams):
    attach_info: str


class ShuoshuoParams(QzoneRequestParams):
    fid: str = Field(serialization_alias="cellid")
    hostuin: int = Field(serialization_alias="uin")
    appid: int = Field(default=311)
    busi_param: str = Field(default="", max_length=100)

    format: str = "json"
    count: int = 20
    refresh_type: int = 31
    subid: str = ""


class GetCountParams(QzoneRequestParams):
    format: str = "json"


class DolikeParam(QzoneRequestParams):
    uin_fields = ("opuin",)
    unikey: str
    curkey: str
    appid: int
    opr_type: str = "like"
    format: str = "purejson"


class AddCommentParams(QzoneRequestParams):
    uin_fields = ("uin",)
    ownuin: int
    fid: str = Field(serialization_alias="srcId")
    private: int = Field(serialization_alias="isPrivateComment")
    content: str = Field(min_length=1, max_length=2000)
    appid: int = Field(default=311)

    bypass_param: dict = Field(default_factory=dict)
    busi_param: dict = Field(default_factory=dict)


class PublishMoodParams(QzoneRequestParams):
    uin_fields = ("res_uin",)
    content: str = Field(min_length=1, max_length=2000)
    richval: str = ""
    issyncweibo: int = Field(default=False, validate_default=True)

    opr_type: str = "publish_shuoshuo"
    format: str = "json"
    # lat: int
    # lon: int
    # lbsid: str = "poiinfo_district"


class DeleteUgcParams(QzoneRequestParams):
    uin_fields = ("res_uin",)
    appid: int = Field(serialization_alias="res_type")
    fid: str = Field(serialization_alias="res_id")

    opr_type: str = "delugc"
    real_del: int = 0
    format: str = "json"
