"""
Make some easy-to-use api from basic wrappers.
"""
import logging
from typing import List, Optional

from pydantic import ValidationError

from ..type.internal import AlbumData
from ..type.resp import *
from .raw import QzoneApi

log = logging.getLogger(__name__)


class DummyQapi(QzoneApi):
    """A wrapper of :class:`.QzoneApi`. Validate the responses, returns pydantic `BaseModel`."""

    async def feeds3_html_more(
        self, pagenum: int, trans: Optional[QzoneApi.FeedsMoreTransaction] = None, count: int = 10
    ) -> FeedMoreResp:
        r = await super().feeds3_html_more(pagenum, trans=trans, count=count)
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
