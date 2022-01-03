import asyncio
from typing import Optional

import pytest
from aiohttp import ClientSession as Session
from aioqzone.api import DummyQapi as QzoneApi
from aioqzone.api.loginman import MixedLoginMan
from aioqzone.type import FeedData, FeedRep

first = lambda it, pred: next(filter(pred, it), None)


@pytest.fixture(scope='module')
def storage():
    return []


@pytest.fixture(scope='module')
def man():
    from os import environ as env

    assert (uin := env.get('TEST_UIN'))
    return MixedLoginMan(
        int(uin),
        env.get('TEST_QRSTRATEGY', 'forbid'),    # forbid QR by default.
        pwd=env.get('TEST_PASSWORD', None)
    )


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
async def api(loop, man: MixedLoginMan):
    async with Session(loop=loop) as sess:
        yield QzoneApi(sess, man)


class TestRaw:
    pytestmark = pytest.mark.asyncio

    async def test_more(self, api: QzoneApi, storage: list):
        future = asyncio.gather(api.feeds3_html_more(i) for i in range(3))
        r = future.result()
        for i in r:
            assert isinstance(i, list)
            storage.extend(i)
        assert storage

    @pytest.mark.skip('NotImplemented')
    async def test_complete(self, api: QzoneApi, storage: list[FeedRep]):
        if not storage: pytest.skip('storage is empty')
        fd = FeedData()    # TODO
        ishtml = bool    # TODO
        assert ishtml(await api.emotion_getcomments(fd))

    async def test_detail(self, api: QzoneApi, storage: list[FeedRep]):
        if not storage: pytest.skip('storage is empty')
        f: Optional[FeedRep] = first(storage, lambda f: f.appid == 311)
        if f is None: pytest.skip('No 311 feed in storage.')
        assert f
        assert await api.emotion_msgdetail(f.uin, f.key)

    async def test_heartbeat(self, api: QzoneApi):
        assert await api.get_feeds_count()

    @pytest.mark.skip('NotImplemented')
    async def test_photo_list(self, api: QzoneApi, storage: list[FeedRep]):
        if not storage: pytest.skip('storage is empty')
        album = api.AlbumData()    # TODO
        await api.floatview_photo_list(album, 10)
