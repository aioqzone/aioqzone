from typing import List, Optional

from aioqzone.api.raw import QzoneApi
from aioqzone.type import AlbumData
from aioqzone.type import FeedDetailRep
from aioqzone.type import FeedMoreAux
from aioqzone.type import FeedRep
from aioqzone.type import FeedsCount
from aioqzone.type import FloatViewPhoto
from aioqzone.type import MsgListElm

class DummyQapi(QzoneApi):
    async def feeds3_html_more(
        self, pagenum: int, trans: Optional[QzoneApi.FeedsMoreTransaction] = None, count: int = 10
    ) -> tuple[List[FeedRep], FeedMoreAux]: ...
    async def emotion_getcomments(self, uin: int, tid: str, feedstype: int) -> str: ...
    async def emotion_msgdetail(self, owner: int, fid: str) -> FeedDetailRep: ...
    async def get_feeds_count(self) -> FeedsCount: ...
    async def floatview_photo_list(self, album: AlbumData, num: int) -> List[FloatViewPhoto]: ...
    async def emotion_msglist(self, uin: int, num: int = 20, pos: int = 0) -> List[MsgListElm]: ...
