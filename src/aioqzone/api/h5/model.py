from aioqzone.type.resp.h5 import FeedCount, FeedPageResp

from .raw import QzoneH5RawAPI


class QzoneH5API(QzoneH5RawAPI):
    async def index(self) -> FeedPageResp:
        return FeedPageResp.parse_obj(await super().index())

    async def get_active_feeds(self, attach_info: str) -> FeedPageResp:
        return FeedPageResp.parse_obj(await super().get_active_feeds(attach_info))

    async def mfeeds_get_count(self) -> FeedCount:
        return FeedCount.parse_obj(await super().mfeeds_get_count())
