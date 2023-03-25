"""
Create an easy-to-use api from :mod:`.raw`.
"""
import logging
from contextlib import suppress
from typing import List, Optional, Type, TypeVar

from pydantic import ValidationError

from aioqzone.type.internal import AlbumData
from aioqzone.type.resp import *

from .raw import QzoneWebRawAPI

_model = TypeVar("_model", bound=BaseModel)

log = logging.getLogger(__name__)


def _parse_obj(model: Type[_model], o: object) -> _model:
    try:
        return model.parse_obj(o)
    except ValidationError:
        log.debug(o)
        raise


class QzoneWebAPI(QzoneWebRawAPI):
    """A wrapper of :class:`.QzoneWebRawAPI`. It will validate the returns from :class:`.QzoneWebRawAPI`,
    and return a typed response. The value returned is usually one or more :class:`BaseModel`, sometimes
    just a basic type if not needed.

    .. versionchanged:: 0.12.1
        rename to ``QzoneWebAPI``
    """

    async def feeds3_html_more(
        self, pagenum: int, count: int = 10, *, aux: Optional[FeedMoreAux] = None
    ) -> FeedMoreResp:
        """This will call :meth:`.QzoneWebRawAPI.feeds3_html_more`.

        :param aux: :obj:`~.FeedMoreResp.aux` field of last return (pagenum - 1).
        :return: a validated and typed response with a list of :obj:`~.FeedMoreResp.feeds` and :obj:`~.FeedMoreResp.aux` info.

        .. versionchanged:: 0.9.4a1

            use `aux` instead of previous `trans` keyword.
        """
        r = await super().feeds3_html_more(
            pagenum,
            count=count,
            external=aux and aux.externparam,
            daylist=aux and aux.daylist or "",
            uinlist=aux and aux.uinlist or "",
        )
        return _parse_obj(FeedMoreResp, r)

    async def emotion_getcomments(self, uin: int, tid: str, feedstype: int) -> str:
        r = await super().emotion_getcomments(uin, tid, feedstype)
        xml = r.get("newFeedXML", "")
        assert isinstance(xml, str)
        return xml.strip()

    async def emotion_msgdetail(self, owner: int, fid: str) -> FeedDetailRep:
        r = await super().emotion_msgdetail(owner, fid)
        return _parse_obj(FeedDetailRep, r)

    async def get_feeds_count(self) -> FeedsCount:
        r = await super().get_feeds_count()
        return _parse_obj(FeedsCount, r)

    async def floatview_photo_list(self, album: AlbumData, num: int) -> List[FloatViewPhoto]:
        r = await super().floatview_photo_list(album, num)
        photos = r.get("photos", [])
        assert isinstance(photos, list)

        ret = []
        for photo in photos:
            with suppress(ValidationError):
                ret.append(_parse_obj(FloatViewPhoto, photo))
        return ret

    async def emotion_msglist(self, uin: int, num: int = 20, pos: int = 0) -> List[MsgListElm]:
        r = await super().emotion_msglist(uin, num, pos)
        return [_parse_obj(MsgListElm, i) for i in r]

    async def emotion_publish(self, content: str, right: int = 0) -> PublishResp:
        r = await super().emotion_publish(content, right)
        return _parse_obj(PublishResp, r)
