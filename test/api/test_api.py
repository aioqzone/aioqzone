import asyncio

import pytest
from aiohttp import ClientSession as Session
from aioqzone.api import QzoneApi


@pytest.fixture(scope='module')
def storage():
    return []


@pytest.fixture(scope='module')
def man():
    from os import environ as env

    from aioqzone.api.loginman import UPLoginMan
    return UPLoginMan(env.get('TEST_UIN'), env.get('TEST_PASSWORD'))


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

    async def test_complete(self, api: QzoneApi, storage: list):
        pass

    async def test_detail(self, api: QzoneApi, storage: list):
        pass
