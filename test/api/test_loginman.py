import asyncio
from os import environ as env

import pytest
import pytest_asyncio
from aiohttp import ClientSession

import aioqzone.api.loginman as api
from aioqzone.interface.hook import LoginMethod, QREvent, UPEvent
from qqqr.exception import TencentLoginError

from . import showqr

pytestmark = pytest.mark.asyncio


class UPEvent_Test(UPEvent):
    async def LoginSuccess(self, meth):
        assert meth == LoginMethod.up
        self.login_succ = True

    async def LoginFailed(self, meth, msg):
        assert meth == LoginMethod.up
        self.login_fail = msg


class QREvent_Test(QREvent):
    async def QrFetched(self, png: bytes, renew):
        showqr(png)
        self.renew_flag = renew

    async def LoginSuccess(self, meth):
        assert meth == LoginMethod.qr
        self.qr_succ = True


@pytest_asyncio.fixture(scope="class")
async def up():
    async with ClientSession() as sess:
        man = api.UPLoginMan(sess, int(env["TEST_UIN"]), pwd=env["TEST_PASSWORD"])

        man.register_hook(UPEvent_Test())
        yield man


@pytest.mark.incremental
class TestUP:
    async def test_newcookie(self, up: api.UPLoginMan):
        try:
            cookie = await up.new_cookie()
        except TencentLoginError:
            await asyncio.sleep(1)
            assert hasattr(up.hook, "login_fail")
            pytest.skip(up.hook.login_fail or "login failed")  # type: ignore
        else:
            assert "p_skey" in cookie
            await asyncio.sleep(1)
            assert hasattr(up.hook, "login_succ")

    def test_cookie(self, up: api.UPLoginMan):
        assert up.cookie

    def test_gtk(self, up: api.UPLoginMan):
        assert up.gtk >= 0


@pytest_asyncio.fixture(scope="class")
async def qr():
    async with ClientSession() as sess:
        man = api.QRLoginMan(sess, int(env["TEST_UIN"]))
        man.register_hook(QREvent_Test())
        yield man


@pytest.mark.needuser
@pytest.mark.incremental
class TestQR:
    async def test_newcookie(self, qr: api.QRLoginMan):
        try:
            cookie = await qr.new_cookie()
        except TencentLoginError:
            await asyncio.sleep(1)
            assert hasattr(qr.hook, "login_fail")
            pytest.skip(qr.hook.login_fail or "login failed")  # type: ignore
        else:
            assert "p_skey" in cookie
            await asyncio.sleep(1)
            assert hasattr(qr.hook, "login_succ")
            assert hasattr(qr.hook, "qr_succ")

    def test_cookie(self, qr: api.QRLoginMan):
        assert qr.cookie

    def test_gtk(self, qr: api.QRLoginMan):
        assert qr.gtk >= 0

    async def test_cancel(self, qr: api.QRLoginMan):
        pytest.skip("NotImplemented")
        await qr.new_cookie()
        assert qr.hook.cancel
        await qr.hook.cancel()

    async def test_resend(self, qr: api.QRLoginMan):
        await qr.new_cookie()
        assert qr.hook.resend
        await qr.hook.resend()
        assert qr.hook.renew_flag  # type: ignore
