import asyncio

from aiohttp import ClientSession
import pytest
import pytest_asyncio

from qqqr.constants import QzoneAppid
from qqqr.constants import QzoneProxy
from qqqr.constants import StatusCode
from qqqr.qr import QRLogin

from . import showqr as _showqr


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def login():
    async with ClientSession() as sess:
        async with QRLogin(sess, QzoneAppid, QzoneProxy) as login:
            await login.request()
            yield login


class TestProcedure:
    pytestmark = pytest.mark.asyncio

    async def test_new(self, login):
        assert await login.show()
        assert isinstance(login.qrsig, str)

    async def test_poll(self, login):
        r = await login.pollStat()
        assert r
        assert r[0] == StatusCode.Waiting


@pytest.mark.needuser
class TestLoop:
    pytestmark = pytest.mark.asyncio

    async def test_Loop(self, login: QRLogin):
        async def showqr(b):
            return _showqr(b)

        cookie = await login.loop(showqr)
        assert cookie["p_skey"]
