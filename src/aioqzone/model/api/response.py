import re
from typing import TYPE_CHECKING, ClassVar, Dict, List, Optional, Tuple

from aiohttp import ClientResponse
from lxml.html import HtmlElement, document_fromstring
from pydantic import AliasChoices, BaseModel, Field, model_validator
from typing_extensions import Self

from aioqzone.exception import QzoneError
from aioqzone.utils.regex import entire_closing
from qqqr.utils.iter import firstn
from qqqr.utils.jsjson import json_loads

from .feed import FeedData

__all__ = [
    "QzoneResponse",
    "FeedPageResp",
    "IndexPageResp",
    "GetMoreResp",
    "FeedCount",
    "SingleReturnResp",
    "FeedData",
]

if TYPE_CHECKING:
    from qqqr.utils.jsjson import JsonValue

    StrDict = Dict[str, JsonValue]


class QzoneResponse(BaseModel):
    class _parse_conf:
        cb: ClassVar[bool] = False
        errno_key: ClassVar[Tuple[str, ...]] = "code", "err"
        msg_key: ClassVar[Tuple[str, ...]] = "message", "msg"
        data_key: ClassVar[Optional[str]] = "data"

    def __init_subclass__(
        cls,
        *,
        cb: bool = False,
        errno_key: Tuple[str, ...] = ("code", "err"),
        msg_key: Tuple[str, ...] = ("message", "msg"),
        data_key: Optional[str] = "data",
        **kwargs,
    ):
        cls._parse_conf.cb = cb
        cls._parse_conf.errno_key = errno_key
        cls._parse_conf.msg_key = msg_key
        cls._parse_conf.data_key = data_key
        return super().__init_subclass__(**kwargs)

    @classmethod
    def from_response_object(cls, obj: "StrDict") -> Self:
        """Parses the response text or object recieved from Qzone API.

        :param obj: the parsed response object. see `.response_to_object`
        :raise `aioqzone.exception.QzoneError`: if returned result code != 0

        :return: Self
        """
        pc = cls._parse_conf

        class response_header(BaseModel):
            status: int = Field(validation_alias=AliasChoices(*pc.errno_key))
            message: str = Field(default="", validation_alias=AliasChoices(*pc.msg_key))

        header = response_header.model_validate(obj)
        if header.status != 0:
            if header.message:
                raise QzoneError(header.status, header.message, rdict=header)
            else:
                raise QzoneError(header.status, rdict=header)

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


class GetMoreResp(FeedData, QzoneResponse):
    hasmore: bool = False
    attach_info: str = ""

    @model_validator(mode="before")
    def remove_prefix(cls, v: dict):
        return {k[5:] if str.startswith(k, "cell_") else k: i for k, i in v.items()}


class FeedPageResp(QzoneResponse, errno_key=("code", "ret")):
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
            raise QzoneError(-3000, "script tag not found")

        texts: List[str] = [s.text for s in scripts]
        script = firstn(texts, lambda s: "shine0callback" in s)
        if not script:
            raise QzoneError(-3000, "data script not found")

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

        data["qzonetoken"] = qzonetoken
        return data


class SingleReturnResp(QzoneResponse, errno_key=("ret",)):
    pass
