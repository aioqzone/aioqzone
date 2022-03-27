"""
Make some easy-to-use api from basic wrappers.
"""
from typing import List, Optional, Tuple

from pydantic import ValidationError

from ..type.internal import AlbumData
from ..type.resp import *
from .raw import QzoneApi


class DummyQapi(QzoneApi):
    """A wrapper of :class:`.QzoneApi`. Validate the responses, returns pydantic `BaseModel`."""

    async def feeds3_html_more(
        self, pagenum: int, trans: Optional[QzoneApi.FeedsMoreTransaction] = None, count: int = 10
    ) -> Tuple[List[FeedRep], FeedMoreAux]:
        r = await super().feeds3_html_more(pagenum, trans=trans, count=count)
        data = r["data"]
        main = r["main"]
        assert isinstance(data, list)
        return [FeedRep.parse_obj(i) for i in data if i], FeedMoreAux.parse_obj(main)

    async def emotion_getcomments(self, uin: int, tid: str, feedstype: int) -> str:
        r = await super().emotion_getcomments(uin, tid, feedstype)
        return str.strip(r["newFeedXML"])  # type: ignore

    async def emotion_msgdetail(self, owner: int, fid: str) -> FeedDetailRep:
        r = await super().emotion_msgdetail(owner, fid)
        return FeedDetailRep.parse_obj(r)

    async def get_feeds_count(self) -> FeedsCount:
        r = await super().get_feeds_count()
        return FeedsCount.parse_obj(r)

    async def floatview_photo_list(self, album: AlbumData, num: int) -> List[FloatViewPhoto]:
        r = await super().floatview_photo_list(album, num)
        try:
            return [FloatViewPhoto.parse_obj(i) for i in r["photos"]]  # type: ignore
        except ValidationError as e:
            # for DEBUG only
            raise e

    async def emotion_msglist(self, uin: int, num: int = 20, pos: int = 0) -> List[MsgListElm]:
        r = await super().emotion_msglist(uin, num, pos)
        return [MsgListElm.parse_obj(i) for i in r]
