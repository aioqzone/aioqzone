import asyncio

from aiohttp import ClientSession as Session
import pytest
import pytest_asyncio

from aioqzone.api import DummyQapi
from aioqzone.api.loginman import MixedLoginMan
from aioqzone.exception import LoginError
from aioqzone.interface.hook import QREvent
from aioqzone.type import FeedRep
from aioqzone.utils.html import HtmlContent

first = lambda it, pred: next(filter(pred, it), None)


@pytest.fixture(scope="module")
def storage():
    return []


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def sess():
    async with Session() as sess:
        yield sess


@pytest_asyncio.fixture(scope="module")
async def man(sess: Session):
    from os import environ as env

    man = MixedLoginMan(
        sess,
        int(env["TEST_UIN"]),
        env.get("TEST_QRSTRATEGY", "forbid"),  # forbid QR by default.
        pwd=env.get("TEST_PASSWORD", None),
    )

    class inner_qrevent(QREvent):
        async def QrFetched(self, png: bytes):
            showqr(png)

    man.register_hook(inner_qrevent())
    yield man


@pytest_asyncio.fixture(scope="module")
async def api(sess: Session, man: MixedLoginMan):
    yield DummyQapi(sess, man)


def showqr(png: bytes):
    import cv2 as cv
    import numpy as np

    def frombytes(b: bytes, dtype="uint8", flags=cv.IMREAD_COLOR) -> np.ndarray:
        return cv.imdecode(np.frombuffer(b, dtype=dtype), flags=flags)

    cv.destroyAllWindows()
    cv.imshow("Scan and login", frombytes(png))
    cv.waitKey()


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
        f: FeedRep | None = first(storage, lambda f: f.appid == 311)
        if f is None:
            pytest.skip("No 311 feed in storage.")
        assert f
        assert await api.emotion_msgdetail(f.uin, f.fid)

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
