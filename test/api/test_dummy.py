import asyncio

from aiohttp import ClientSession as Session
import pytest
import pytest_asyncio

from aioqzone.api import DummyQapi
from aioqzone.api.loginman import MixedLoginMan
from aioqzone.exception import LoginError
from aioqzone.exception import QzoneError
from aioqzone.type import FeedRep
from aioqzone.utils.html import HtmlContent

first = lambda it, pred: next(filter(pred, it), None)


@pytest.fixture(scope="module")
def storage():
    return []


@pytest_asyncio.fixture(scope="module")
async def api(sess: Session, man: MixedLoginMan):
    yield DummyQapi(sess, man)


class TestDummy:
    pytestmark = pytest.mark.asyncio

    async def test_more(self, api: DummyQapi, storage: list):
        future = asyncio.gather(*(api.feeds3_html_more(i) for i in range(3)))
        try:
            r = await future
        except LoginError:
            pytest.xfail("Login failed")
        for ls, aux in r:  # type: ignore
            assert isinstance(ls, list)
            assert aux.dayspac >= 0
            storage.extend(ls)
        assert storage

    @pytest.mark.upstream
    async def test_complete(self, api: DummyQapi, storage: list[FeedRep]):
        if not storage:
            pytest.xfail("storage is empty")
        f: FeedRep | None = first(storage, None)
        assert f
        from aioqzone.utils.html import HtmlInfo

        _, info = HtmlInfo.from_html(f.html)
        assert await api.emotion_getcomments(f.uin, f.fid, info.feedstype)

    async def test_detail(self, api: DummyQapi, storage: list[FeedRep]):
        if not storage:
            pytest.xfail("storage is empty")
        for f in storage:
            try:
                assert await api.emotion_msgdetail(f.uin, f.fid)
            except QzoneError as e:
                continue

    async def test_heartbeat(self, api: DummyQapi):
        try:
            assert await api.get_feeds_count()
        except LoginError:
            pytest.xfail("Login failed")

    async def test_photo_list(self, api: DummyQapi, storage: list[FeedRep]):
        if not storage:
            pytest.xfail("storage is empty")
        f: HtmlContent | None = first(
            (HtmlContent.from_html(i.html, i.uin) for i in storage), lambda t: t.pic
        )
        if f is None:
            pytest.skip("No feed with pic in storage")
        assert f
        assert f.album
        await api.floatview_photo_list(f.album, 10)
