import asyncio
from os import environ as env

import aioqzone.api.loginman as api
import pytest
import pytest_asyncio
from aiohttp import ClientSession
from aioqzone.interface.hook import LoginEvent, QREvent
from qqqr.exception import TencentLoginError


class LoginEvent_Test(LoginEvent):
    async def LoginSuccess(self):
        self.login_succ = True

    async def LoginFailed(self, msg: str = None):
        self.login_fail = msg


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope='class')
async def up():
    async with ClientSession() as sess:
        man = api.UPLoginMan(sess, int(env['TEST_UIN']), pwd=env['TEST_PASSWORD'])

        man.register_hook(LoginEvent_Test())
        yield man


@pytest.mark.incremental
class TestUP:
    @pytest.mark.asyncio
    async def test_newcookie(self, up: api.UPLoginMan):
        try:
            cookie = await up.new_cookie()
        except TencentLoginError:
            await asyncio.sleep(1)
            assert hasattr(up.hook, 'login_fail')
            pytest.skip(up.hook.login_fail or 'login failed')    # type: ignore
        else:
            assert 'p_skey' in cookie
            await asyncio.sleep(1)
            assert hasattr(up.hook, 'login_succ')

    def test_cookie(self, up: api.UPLoginMan):
        assert up.cookie

    def test_gtk(self, up: api.UPLoginMan):
        assert up.gtk >= 0


def showqr(png: bytes):
    import cv2 as cv
    import numpy as np

    def frombytes(b: bytes, dtype='uint8', flags=cv.IMREAD_COLOR) -> np.ndarray:
        return cv.imdecode(np.frombuffer(b, dtype=dtype), flags=flags)

    cv.destroyAllWindows()
    cv.imshow('Scan and login', frombytes(png))
    cv.waitKey()


@pytest_asyncio.fixture(scope='class')
async def qr():
    class inner_qrevent(QREvent, LoginEvent_Test):
        async def QrFetched(self, png: bytes):
            showqr(png)

        async def QrSucceess(self):
            self.qr_succ = True

    async with ClientSession() as sess:
        man = api.QRLoginMan(sess, int(env['TEST_UIN']))
        man.register_hook(inner_qrevent())
        yield man


@pytest.mark.needuser
@pytest.mark.incremental
class TestQR:
    @pytest.mark.asyncio
    async def test_newcookie(self, qr: api.QRLoginMan):
        try:
            cookie = await qr.new_cookie()
        except TencentLoginError:
            await asyncio.sleep(1)
            assert hasattr(qr.hook, 'login_fail')
            pytest.skip(qr.hook.login_fail or 'login failed')    # type: ignore
        else:
            assert 'p_skey' in cookie
            await asyncio.sleep(1)
            assert hasattr(qr.hook, 'login_succ')
            assert hasattr(qr.hook, 'qr_succ')

    def test_cookie(self, qr: api.QRLoginMan):
        assert qr.cookie

    def test_gtk(self, qr: api.QRLoginMan):
        assert qr.gtk >= 0

    @pytest.mark.asyncio
    async def test_cancel(self, qr: api.QRLoginMan):
        await qr.new_cookie()
        await qr.hook.cancel()    # type: ignore

    @pytest.mark.asyncio
    async def test_resend(self, qr: api.QRLoginMan):
        await qr.new_cookie()
        await qr.hook.resend()    # type: ignore


@pytest_asyncio.fixture(scope='class')
async def mixed():
    async with ClientSession() as sess:
        man = api.MixedLoginMan(
            sess,
            int(env['TEST_UIN']),
            env.get('TEST_QRSTRATEGY', 'forbid'),
            pwd=env.get('TEST_PASSWORD', None)
        )

        class inner_qrevent(QREvent, LoginEvent_Test):
            async def QrFetched(self, png: bytes):
                showqr(png)

        man.register_hook(inner_qrevent())
        yield man
