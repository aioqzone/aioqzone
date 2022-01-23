import asyncio
from typing import Optional

import pytest
from aiohttp import ClientSession as Session
from aioqzone.api.loginman import MixedLoginMan
from aioqzone.api.raw import QzoneApi
from aioqzone.type import LikeData

first = lambda it, pred: next(filter(pred, it), None)


@pytest.fixture(scope='module')
def storage():
    return []


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
async def man():
    from os import environ as env

    async with Session() as sess:
        yield MixedLoginMan(
            sess,
            int(env['TEST_UIN']),
            env.get('TEST_QRSTRATEGY', 'forbid'),    # forbid QR by default.
            pwd=env.get('TEST_PASSWORD', None)
        )


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

    async def test_complete(self, api: QzoneApi, storage: list):
        if not storage: pytest.skip('storage is empty')
        f: Optional[dict] = first(storage, None)
        if f is None: pytest.skip('No feed in storage')
        assert f
        from aioqzone.utils.html import HtmlInfo
        _, info = HtmlInfo.from_html(f['html'])
        d = await api.emotion_getcomments(f['uin'], f['key'], info.feedstype)
        assert 'newFeedXML' in d

    @pytest.mark.skip('NotImplemented')
    async def test_detail(self, api: QzoneApi, storage: list):
        if not storage: pytest.skip('storage is empty')
        f: Optional[dict] = first(storage, lambda f: f.appid == 311)
        if f is None: pytest.skip('No 311 feed in storage.')
        assert f
        await api.emotion_msgdetail(f['uin'], f['key'])

    async def test_heartbeat(self, api: QzoneApi):
        d = await api.get_feeds_count()
        for k, v in d.items():
            assert isinstance(k, str)
            assert isinstance(v, int)

    @pytest.mark.skip('NotImplemented')
    async def test_like(self, api: QzoneApi, storage: list):
        if not storage: pytest.skip('storage is empty')
        ld = LikeData()    # TODO
        assert await api.like_app(ld, True)
        assert await api.like_app(ld, False)

    @pytest.mark.skip('NotImplemented')
    async def test_photo_list(self, api: QzoneApi, storage: list):
        if not storage: pytest.skip('storage is empty')
        album = api.AlbumData()    # TODO
        await api.floatview_photo_list(album, 10)
