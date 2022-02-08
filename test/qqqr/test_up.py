import asyncio
from os import environ as env

from aiohttp import ClientSession
import pytest
import pytest_asyncio

from qqqr.constants import QzoneAppid
from qqqr.constants import QzoneProxy
from qqqr.constants import StatusCode
from qqqr.exception import TencentLoginError
from qqqr.up import UPLogin
from qqqr.up import User


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture.fixture(scope='module')
async def login():
    async with ClientSession() as sess:
        async with UPLogin(sess, QzoneAppid, QzoneProxy, User(
                int(env['TEST_UIN']),
                env['TEST_PASSWORD'],
        )) as login:
            await login.request()
            yield login


class TestRequest:
    pytestmark = pytest.mark.asyncio

    async def testEncodePwd(self, login):
        r = await login.check()
        if r.code == 1:
            r = await login.passVC(r)
        if r.code != 1:
            assert r.verifycode
            assert r.salt
            assert await login.encodePwd(r)

    async def testLogin(self, login):
        r = await login.check()
        try:
            assert await login.login(r)
        except TencentLoginError as e:
            if e.code in [StatusCode.RiskyNetwork, StatusCode.ForceQR]:
                pytest.skip(str(e))
            else:
                raise e
