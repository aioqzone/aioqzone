import asyncio
from typing import List, Optional

import pytest
import pytest_asyncio
from httpx import HTTPStatusError

from aioqzone.api import DummyQapi
from aioqzone.api.loginman import MixedLoginMan
from aioqzone.exception import LoginError, QzoneError
from aioqzone.type.resp import FeedRep
from aioqzone.utils import first
from aioqzone.utils.html import HtmlContent
from qqqr.utils.net import ClientAdapter


@pytest.fixture(scope="module")
def storage():
    return []


@pytest_asyncio.fixture(scope="module")
async def api(client: ClientAdapter, man: MixedLoginMan):
    yield DummyQapi(client, man)


class TestDummy:
    pytestmark = pytest.mark.asyncio

    async def test_heartbeat(self, api: DummyQapi):
        try:
            assert await api.get_feeds_count()
        except LoginError:
            pytest.xfail("Login failed")

    async def test_more(self, api: DummyQapi, storage: list):
        future = asyncio.gather(*(api.feeds3_html_more(i) for i in range(3)))
        try:
            r = await future
        except LoginError:
            pytest.xfail("Login failed")
        for i in r:
            assert isinstance(i.feeds, list)
            assert i.aux.dayspac >= 0
            storage.extend(i.feeds)
        assert storage

    @pytest.mark.upstream
    async def test_complete(self, api: DummyQapi, storage: List[FeedRep]):
        if not storage:
            pytest.xfail("storage is empty")
        f: Optional[FeedRep] = first(storage, None)
        assert f
        from aioqzone.utils.html import HtmlInfo

        _, info = HtmlInfo.from_html(f.html)
        assert await api.emotion_getcomments(f.uin, f.fid, info.feedstype)

    async def test_detail(self, api: DummyQapi, storage: List[FeedRep]):
        if not storage:
            pytest.xfail("storage is empty")
        for f in storage:
            try:
                assert await api.emotion_msgdetail(f.uin, f.fid)
            except (QzoneError, HTTPStatusError) as e:
                continue

    async def test_photo_list(self, api: DummyQapi, storage: List[FeedRep]):
        if not storage:
            pytest.xfail("storage is empty")
        f: Optional[HtmlContent] = first(
            (HtmlContent.from_html(i.html, i.uin) for i in storage), lambda t: bool(t.pic)
        )
        if f is None:
            pytest.skip("No feed with pic in storage")
        assert f
        assert f.album
        await api.floatview_photo_list(f.album, 10)
