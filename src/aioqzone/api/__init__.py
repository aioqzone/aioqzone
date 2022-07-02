"""
Create an easy-to-use api from :mod:`.raw`.
"""
import logging
from typing import List, Optional

from pydantic import ValidationError

from ..type.internal import AlbumData
from ..type.resp import *
from .raw import QzoneApi

log = logging.getLogger(__name__)


class DummyQapi(QzoneApi):
    """A wrapper of :class:`.QzoneApi`. It will validate the returns from :class:`.QzoneApi`,
    and return a typed response. The value returned is usually a :class:`BaseModel`, sometimes
    just a basic type if not needed."""

    async def feeds3_html_more(
        self, pagenum: int, count: int = 10, *, aux: Optional[FeedMoreAux] = None
    ) -> FeedMoreResp:
        """This will call :meth:`.QzoneApi.feeds3_html_more`.

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
        return FeedMoreResp.parse_obj(r)

    async def emotion_getcomments(self, uin: int, tid: str, feedstype: int) -> str:
        r = await super().emotion_getcomments(uin, tid, feedstype)
        xml = r.get("newFeedXML", "")
        assert isinstance(xml, str)
        return xml.strip()

    async def emotion_msgdetail(self, owner: int, fid: str) -> FeedDetailRep:
        r = await super().emotion_msgdetail(owner, fid)
        return FeedDetailRep.parse_obj(r)

    async def get_feeds_count(self) -> FeedsCount:
        r = await super().get_feeds_count()
        return FeedsCount.parse_obj(r)

    async def floatview_photo_list(self, album: AlbumData, num: int) -> List[FloatViewPhoto]:
        r = await super().floatview_photo_list(album, num)
        photos = r.get("photos", [])
        assert isinstance(photos, list)

        ret = []
        for i in photos:
            try:
                ret.append(FloatViewPhoto.parse_obj(i))
            except ValidationError:
                log.error(f"ValidationError parsing FloatViewPhoto: {i}")
                continue
        return ret

    async def emotion_msglist(self, uin: int, num: int = 20, pos: int = 0) -> List[MsgListElm]:
        r = await super().emotion_msglist(uin, num, pos)
        return [MsgListElm.parse_obj(i) for i in r]

    async def emotion_publish(self, content: str, right: int = 0) -> PublishResp:
        r = await super().emotion_publish(content, right)
        return PublishResp.parse_obj(r)
