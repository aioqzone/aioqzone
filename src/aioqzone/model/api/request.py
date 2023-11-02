import typing as t

from pydantic import BaseModel, Field


class QzoneRequestParams(BaseModel):
    uin_fields: t.ClassVar[t.Tuple[str]] = Field(default_factory=tuple, repr=False, exclude=True)

    def build_params(self, uin: int):
        d = self.model_dump(mode="json")
        d.update({i: uin for i in self.uin_fields})
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
    _uin_fields = ("opuin",)
    unikey: str
    curkey: str
    appid: int
    opr_type: str = "like"
    format: str = "purejson"


class AddCommentParams(QzoneRequestParams):
    _uin_fields = ("uin",)
    ownuin: int
    srcId: str
    isPrivateComment: int
    content: str = Field(min_length=1, max_length=2000)
    appid: int = Field(default=311)

    bypass_param: dict = Field(default_factory=dict)
    busi_param: dict = Field(default_factory=dict)
