import asyncio
from os import environ as env

import aioqzone.api.loginman as api
import pytest
from aiohttp import ClientSession
from aioqzone.interface.hook import LoginEvent, QREvent
from qqqr.exception import TencentLoginError


@pytest.fixture(scope='module')
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='class')
async def up():
    async with ClientSession() as sess:
        man = api.MixedLoginMan(
            sess,
            int(env['TEST_UIN']),
            env.get('TEST_QRSTRATEGY', 'forbid'),
            pwd=env.get('TEST_PASSWORD', None)
        )

        class mixed_event(LoginEvent, QREvent):
            pass

        man.register_hook(mixed_event())
        yield man


@pytest.mark.incremental
class TestUP:
    @pytest.mark.asyncio
    async def test_newcookie(self, up: api.UPLoginMan):
        try:
            assert 'p_skey' in await up.new_cookie()
        except TencentLoginError:
            pytest.skip('Login failed.')

    def test_cookie(self, up: api.UPLoginMan):
        assert up.cookie

    def test_gtk(self, up: api.UPLoginMan):
        assert up.gtk


@pytest.fixture(scope='class')
async def qr():
    import cv2 as cv
    import numpy as np

    class inner_qrevent(QREvent, LoginEvent):
        def QrFetched(self, png: bytes):
            def frombytes(b: bytes, dtype='uint8', flags=cv.IMREAD_COLOR) -> np.ndarray:
                return cv.imdecode(np.frombuffer(b, dtype=dtype), flags=flags)

            cv.destroyAllWindows()
            cv.imshow('Scan and login', frombytes(png))
            cv.waitKey()

    async with ClientSession() as sess:
        man = api.QRLoginMan(sess, int(env['TEST_UIN']))
        man.register_hook(inner_qrevent())
        yield man


@pytest.mark.needuser
class TestQR:
    @pytest.mark.asyncio
    async def test_newcookie(self, qr: api.QRLoginMan):
        assert 'p_skey' in await qr.new_cookie()

    def test_cookie(self, qr: api.QRLoginMan):
        assert qr.cookie

    def test_gtk(self, qr: api.QRLoginMan):
        assert qr.gtk

    @pytest.mark.asyncio
    async def test_cancel(self, qr: api.QRLoginMan):
        await qr.new_cookie()
        await qr.hook.cancel()    # type: ignore

    @pytest.mark.asyncio
    async def test_resend(self, qr: api.QRLoginMan):
        await qr.new_cookie()
        await qr.hook.resend()    # type: ignore
