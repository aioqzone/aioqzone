import logging
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from aioqzone.type.resp.h5 import FeedCount, FeedPageResp

from .raw import QzoneH5RawAPI

_model = TypeVar("_model", bound=BaseModel)

log = logging.getLogger(__name__)


def _parse_obj(model: Type[_model], o: object) -> _model:
    try:
        return model.parse_obj(o)
    except ValidationError:
        log.debug(o)
        raise


class QzoneH5API(QzoneH5RawAPI):
    async def index(self) -> FeedPageResp:
        return _parse_obj(FeedPageResp, await super().index())

    async def get_active_feeds(self, attach_info: str) -> FeedPageResp:
        return _parse_obj(FeedPageResp, await super().get_active_feeds(attach_info))

    async def shuoshuo(
        self, fid: str, hostuin: int, appid=311, busi_param: str = ""
    ) -> FeedPageResp:
        return _parse_obj(FeedPageResp, await super().shuoshuo(fid, hostuin, appid, busi_param))

    async def mfeeds_get_count(self) -> FeedCount:
        return _parse_obj(FeedCount, await super().mfeeds_get_count())
