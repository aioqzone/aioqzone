import typing as t

from pydantic import BaseModel, HttpUrl
from yarl import URL

from .request import *
from .response import *

TyRequest = t.TypeVar("TyRequest", bound=QzoneRequestParams)
TyResponse = t.TypeVar("TyResponse", bound=QzoneResponse)


class QzoneApi(BaseModel, t.Generic[TyRequest, TyResponse]):
    host: HttpUrl = Field(default="https://h5.qzone.qq.com", validate_default=True)
    http_method: t.Union[t.Literal["GET"], t.Literal["POST"]]
    attach_token: bool = True
    path: str

    params: TyRequest = Field(default_factory=QzoneRequestParams)
    response: t.Type[TyResponse]

    @property
    def url(self) -> URL:
        return URL(str(self.host)).with_path(self.path)


class FeedPageApi(QzoneApi):
    http_method: t.Literal["GET"] = Field(default="GET")
    path: str = Field(default="/mqzone/index")


class ShuoshuoApi(QzoneApi):
    http_method: t.Literal["GET"] = Field(default="GET")
    path: str = Field(default="/webapp/json/mqzone_detail/shuoshuo")


class GetCountApi(QzoneApi):
    http_method: t.Literal["GET"] = Field(default="GET")
    path: str = Field(default="/feeds/mfeeds_get_count")


class AddCommentApi(QzoneApi):
    http_method: t.Literal["POST"] = Field(default="POST")
    path: str = Field(default="/webapp/json/qzoneOperation/addComment")
