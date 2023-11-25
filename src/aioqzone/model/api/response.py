import re
from typing import TYPE_CHECKING, Any, ClassVar, Coroutine, Dict, List, Optional, Tuple

from aiohttp import ClientResponse
from lxml.html import HtmlElement, document_fromstring
from pydantic import AliasChoices, BaseModel, Field, HttpUrl, model_validator
from tenacity import TryAgain
from typing_extensions import Self

from aioqzone.exception import QzoneError
from aioqzone.utils.regex import entire_closing, response_callback
from qqqr.utils.iter import firstn
from qqqr.utils.jsjson import json_loads

from .feed import FeedData

__all__ = [
    "QzoneResponse",
    "FeedPageResp",
    "IndexPageResp",
    "DetailResp",
    "FeedCount",
    "SingleReturnResp",
    "AddCommentResp",
    "PublishMoodResp",
    "DeleteUgcResp",
    "UploadPicResponse",
    "PhotosPreuploadResponse",
    "FeedData",
]

if TYPE_CHECKING:
    from qqqr.utils.jsjson import JsonValue

    StrDict = Dict[str, JsonValue]


class _ResponseParseConfig(BaseModel):
    errno_key: Tuple[str, ...] = "code", "ret", "err"
    msg_key: Tuple[str, ...] = "message", "msg"
    data_key: Optional[str] = "data"


class QzoneResponse(BaseModel):
    _parse_conf: ClassVar[_ResponseParseConfig]

    def __init_subclass__(cls, **kwargs):
        cls._parse_conf = _ResponseParseConfig.model_validate(kwargs)
        for k in cls._parse_conf.model_fields_set:
            kwargs.pop(k)  # type: ignore
        return super().__init_subclass__(**kwargs)

    @classmethod
    def from_response_object(cls, obj: "StrDict") -> Self:
        """Parses the response text or object recieved from Qzone API.

        :param obj: the parsed response object. see `.response_to_object`
        :raise `aioqzone.exception.QzoneError`: if returned result code != 0

        :return: Self
        """
        pc = cls._parse_conf

        if pc.errno_key and pc.msg_key:

            class response_header(BaseModel):
                status: int = Field(validation_alias=AliasChoices(*pc.errno_key))
                message: str = Field(default="", validation_alias=AliasChoices(*pc.msg_key))

            header = response_header.model_validate(obj)
            if header.status != 0:
                if header.message:
                    raise QzoneError(header.status, header.message, robj=header)
                else:
                    raise QzoneError(header.status, robj=header)

        if pc.data_key is None:
            return cls.model_validate(obj)
        return cls.model_validate(obj[pc.data_key])

    @classmethod
    async def response_to_object(cls, response: ClientResponse) -> "StrDict":
        return await response.json(content_type=None)


class FeedCount(QzoneResponse):
    active_cnt: int = 0
    passive_cnt: int = 0
    gamebar_cnt: int = 0
    gift_cnt: int = 0
    visitor_cnt: int = 0


class DetailResp(FeedData, QzoneResponse):
    hasmore: bool = False
    attach_info: str = ""

    @model_validator(mode="before")
    def remove_prefix(cls, v: dict):
        return {k[5:] if str.startswith(k, "cell_") else k: i for k, i in v.items()}


class FeedPageResp(QzoneResponse):
    """Represents RESPonse from get feed page operation.
    Used to validate response data in :meth:`aioqzone.api.h5.QzoneH5API.index`
    and :meth:`aioqzone.api.h5.QzoneH5API.getActivateFeeds`
    """

    hasmore: bool = False
    attachinfo: str = ""
    newcnt: int

    undeal_info: FeedCount
    vFeeds: List[FeedData]


class IndexPageResp(FeedPageResp):
    qzonetoken: str = ""

    @classmethod
    async def response_to_object(cls, response: ClientResponse):
        html = await response.text()
        scripts: List[HtmlElement] = document_fromstring(html).xpath(
            'body/script[@type="application/javascript"]'
        )
        if not scripts:
            raise TryAgain("script tag not found")

        texts: List[str] = [s.text for s in scripts]
        script = firstn(texts, lambda s: "shine0callback" in s)
        if not script:
            raise TryAgain("data script not found")

        m = re.search(r'window\.shine0callback.*return "([0-9a-f]+?)";', script)
        if m is None:
            raise RuntimeError("data script not found")
        qzonetoken = m.group(1)

        m = re.search(r"var FrontPage =.*?data\s*:\s*\{", script)
        if m is None:
            raise RuntimeError("page data not found")
        data = script[m.end() - 1 : m.end() + entire_closing(script[m.end() - 1 :])]
        data = json_loads(data)
        assert isinstance(data, dict)

        if cls._parse_conf.data_key:
            if d := data[cls._parse_conf.data_key]:
                assert isinstance(d, dict)
                d["qzonetoken"] = qzonetoken
            else:
                data[cls._parse_conf.data_key] = dict(qzonetoken=qzonetoken)
        else:
            data["qzonetoken"] = qzonetoken
        return data


class SingleReturnResp(QzoneResponse, data_key=None):  # type: ignore
    pass


class AddCommentResp(QzoneResponse):
    ret: int = 0
    msg: str = ""
    verifyurl: str = ""
    commentid: int = 0
    commentLikekey: HttpUrl


class PublishMoodResp(QzoneResponse):
    ret: int = 0
    msg: str = ""
    fid: str = Field(validation_alias="tid")
    undeal_info: FeedCount = Field(default_factory=FeedCount)


class DeleteUgcResp(QzoneResponse):
    ret: int = 0
    msg: str = ""
    undeal_info: FeedCount = Field(default_factory=FeedCount)


class UploadPicResponse(QzoneResponse, errno_key=()):  # type: ignore
    filelen: int
    filemd5: str

    @classmethod
    async def response_to_object(cls, response: ClientResponse):
        m = response_callback.search(await response.text())
        assert m
        return json_loads(m.group(1))


class PicInfo(BaseModel):
    pre: HttpUrl
    url: HttpUrl
    sloc: str
    lloc: str
    width: int
    height: int
    albumid: str


class PhotosPreuploadResponse(QzoneResponse, errno_key=()):  # type: ignore
    photos: List[PicInfo] = Field(default_factory=list)

    @classmethod
    async def response_to_object(cls, response: ClientResponse):
        m = response_callback.search(await response.text())
        assert m
        return dict(photos=json_loads(m.group(1)))
