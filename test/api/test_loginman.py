import asyncio
from os import environ as env
from typing import Optional

from aiohttp import ClientSession
import pytest
import pytest_asyncio

import aioqzone.api.loginman as api
from aioqzone.interface.hook import LoginEvent
from aioqzone.interface.hook import QREvent
from qqqr.exception import TencentLoginError

from . import showqr


class LoginEvent_Test(LoginEvent):
    async def LoginSuccess(self):
        self.login_succ = True

    async def LoginFailed(self, msg: Optional[str] = None):
        self.login_fail = msg


@pytest_asyncio.fixture(scope="class")
async def up():
    async with ClientSession() as sess:
        man = api.UPLoginMan(sess, int(env["TEST_UIN"]), pwd=env["TEST_PASSWORD"])

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
    class inner_qrevent(QREvent, LoginEvent_Test):
        async def QrFetched(self, png: bytes):
            showqr(png)

        async def QrSucceess(self):
            self.qr_succ = True

    async with ClientSession() as sess:
        man = api.QRLoginMan(sess, int(env["TEST_UIN"]))
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

    @pytest.mark.asyncio
    async def test_cancel(self, qr: api.QRLoginMan):
        pytest.skip("NotImplemented")
        await qr.new_cookie()
        await qr.hook.cancel()  # type: ignore

    @pytest.mark.asyncio
    async def test_resend(self, qr: api.QRLoginMan):
        await qr.new_cookie()
        await qr.hook.resend()  # type: ignore
