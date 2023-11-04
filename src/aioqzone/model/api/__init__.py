import typing as t

from pydantic import BaseModel, HttpUrl
from yarl import URL

from .request import *
from .response import *

TyRequest = t.TypeVar("TyRequest", bound=QzoneRequestParams)
TyResponse = t.TypeVar("TyResponse", bound=QzoneResponse)
TyMethod = t.Union[t.Literal["GET"], t.Literal["POST"]]


class QzoneApi(BaseModel, t.Generic[TyRequest, TyResponse]):
    host: t.ClassVar[str] = "https://h5.qzone.qq.com"
    http_method: t.ClassVar[TyMethod]
    attach_token: bool = True
    path: str

    params: TyRequest = Field(default_factory=QzoneRequestParams)
    response: t.Type[TyResponse]

    @property
    def url(self) -> URL:
        return URL(str(self.host)).with_path(self.path)


class IndexPageApi(QzoneApi[QzoneRequestParams, IndexPageResp]):
    http_method: t.ClassVar[TyMethod] = "GET"
    path: t.ClassVar[str] = "/mqzone/index"


class FeedPageApi(QzoneApi[ActiveFeedsParams, FeedPageResp]):
    http_method: t.ClassVar[TyMethod] = "GET"
    path: t.ClassVar[str] = "/webapp/json/mqzone_feeds/getActiveFeeds"


class ShuoshuoApi(QzoneApi[ShuoshuoParams, DetailResp]):
    http_method: t.ClassVar[TyMethod] = "GET"
    path: t.ClassVar[str] = "/webapp/json/mqzone_detail/shuoshuo"


class GetCountApi(QzoneApi[GetCountParams, FeedCount]):
    http_method: t.ClassVar[TyMethod] = "GET"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "/feeds/mfeeds_get_count"


class DoLikeApi(QzoneApi[DolikeParam, SingleReturnResp]):
    http_method: t.ClassVar[TyMethod] = "POST"


class AddCommentApi(QzoneApi[AddCommentParams, AddCommentResp]):
    http_method: t.ClassVar[TyMethod] = "POST"
    path: t.ClassVar[str] = "/webapp/json/qzoneOperation/addComment"


class ListFriendApi(QzoneApi):
    http_method: t.ClassVar[TyMethod] = "GET"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "/friend/mfriend_list"


class PublishMoodApi(QzoneApi[PublishMoodParams, PublishMoodResp]):
    http_method: t.ClassVar[TyMethod] = "POST"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "/mood/publish_mood"


class AddOperationApi(QzoneApi):
    http_method: t.ClassVar[TyMethod] = "POST"
    host: t.ClassVar[str] = "https://mobile.qzone.qq.com"
    path: t.ClassVar[str] = "operation/operation_add"