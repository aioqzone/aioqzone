import asyncio

import pytest
from aiohttp import ClientSession as Session
from aioqzone.api.loginman import MixedLoginMan
from aioqzone.api.raw import QzoneApi


@pytest.fixture(scope='module')
def storage():
    return []


@pytest.fixture(scope='module')
def man():
    from os import environ as env

    return MixedLoginMan(
        env.get('TEST_UIN'),
        env.get('TEST_QRSTRATEGY', 'forbid'),    # forbid QR by default.
        pwd=env.get('TEST_PASSWORD', None)
    )


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
async def api(loop):
    async with Session(loop=loop) as sess:
        yield QzoneApi(sess, man)


class TestFeedMore:
    pytestmark = pytest.mark.asyncio

    async def test_more(self, api: QzoneApi, storage: list):
        future = asyncio.gather(api.feeds3_html_more(i) for i in range(3))
        r = future.result()
        for i in r:
            storage.extend(i)
        assert storage

    @pytest.skip('NotImplemented')
    async def test_complete(self, api: QzoneApi, storage: list):
        if not storage: pytest.skip('storage is empty')
        fd = api.FeedData()    # TODO
        await api.emotion_getcomments(fd)

    @pytest.skip('NotImplemented')
    async def test_detail(self, api: QzoneApi, storage: list):
        if not storage: pytest.skip('storage is empty')
        await api.emotion_msgdetail()

    async def test_heartbeat(self, api: QzoneApi):
        d = await api.get_feeds_count()
        for k, v in d.items():
            assert isinstance(k, str)
            assert isinstance(v, int)

    @pytest.skip('NotImplemented')
    async def test_like(self, api: QzoneApi, storage: list):
        if not storage: pytest.skip('storage is empty')
        ld = api.LikeData()    # TODO
        assert await api.like_app(ld, True)
        assert await api.like_app(ld, False)

    @pytest.skip('NotImplemented')
    async def test_photo_list(self, api: QzoneApi, storage: list):
        if not storage: pytest.skip('storage is empty')
        album = api.AlbumData()    # TODO
        await api.floatview_photo_list(album, 10)
