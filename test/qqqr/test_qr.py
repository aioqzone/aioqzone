import asyncio
from os import environ as env

import pytest

from qqqr.constants import QzoneAppid
from qqqr.constants import QzoneProxy
from qqqr.constants import StatusCode
from qqqr.qr import QRLogin

need_interact = pytest.mark.skipif(
    not env.get('QR_OK', 0), reason='need user interaction'
)


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='module')
async def login():
    async with QRLogin(QzoneAppid, QzoneProxy) as login:
        await login.request()
        yield login


class TestProcedure:
    pytestmark = pytest.mark.asyncio

    async def test_new(self, login):
        assert await login.show()
        assert isinstance(login.qrsig, str)

    async def test_poll(self, login):
        assert (r := await login.pollStat())
        assert r[0] == StatusCode.Waiting


@need_interact
class TestLoop:
    pytestmark = pytest.mark.asyncio

    @staticmethod
    async def writeqr(b: bytes):
        with open('tmp/r.png', 'wb') as f:
            f.write(b)

    async def test_Loop(self, login):
        future = await login.loop(self.writeqr)
        cookie = await future
        assert cookie['p_skey']
