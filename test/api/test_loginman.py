import asyncio
from os import environ as env

import pytest
import pytest_asyncio

import aioqzone.api.loginman as api
from aioqzone.event.login import LoginMethod, QREvent, UPEvent
from qqqr.exception import TencentLoginError
from qqqr.utils.net import ClientAdapter

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
    def __init__(self) -> None:
        super().__init__()
        self._cancel = asyncio.Event()
        self._refresh = asyncio.Event()

    async def QrFetched(self, png: bytes, renew):
        showqr(png)
        self.renew_flag = renew

    async def LoginSuccess(self, meth):
        assert meth == LoginMethod.qr
        self.login_succ = True

    async def LoginFailed(self, meth, msg):
        assert meth == LoginMethod.qr
        self.login_fail = msg

    @property
    def cancel_flag(self) -> asyncio.Event:
        return self._cancel

    @property
    def refresh_flag(self) -> asyncio.Event:
        return self._refresh


@pytest_asyncio.fixture(scope="class")
async def up(client: ClientAdapter):
    man = api.UPLoginMan(client, int(env["TEST_UIN"]), pwd=env["TEST_PASSWORD"])
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
async def qr(client: ClientAdapter):
    man = api.QRLoginMan(client, int(env["TEST_UIN"]))
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

    def test_cookie(self, qr: api.QRLoginMan):
        assert qr.cookie

    def test_gtk(self, qr: api.QRLoginMan):
        assert qr.gtk >= 0

    async def test_cancel(self, qr: api.QRLoginMan):
        await qr.new_cookie()
        qr.hook.cancel_flag.set()

    async def test_resend(self, qr: api.QRLoginMan):
        await qr.new_cookie()
        qr.hook.refresh_flag.set()
        assert qr.hook.renew_flag  # type: ignore
