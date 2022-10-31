import asyncio
from os import environ as env
from typing import List, Tuple, Type, cast
from unittest import mock

import pytest
import pytest_asyncio
from httpx import ConnectError, HTTPError, Request

import aioqzone.api.loginman as api
from aioqzone.event.login import LoginMethod, QREvent, UPEvent
from aioqzone.exception import LoginError
from jssupport.exception import JsRuntimeError
from qqqr.event.login import QrEvent, UpEvent
from qqqr.exception import HookError, TencentLoginError, UserBreak
from qqqr.utils.net import ClientAdapter

from . import showqr

pytestmark = pytest.mark.asyncio

_fake_request = cast(Request, ...)
_fake_http_error = HTTPError("mock")
_fake_http_error.request = _fake_request


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
    @pytest.mark.parametrize(
        "exc2r,exc2e",
        [
            (TencentLoginError(-3002, "mock"), TencentLoginError),
            (NotImplementedError(), TencentLoginError),
            (JsRuntimeError(-1, "node", b"mock"), TencentLoginError),
            (GeneratorExit(), api._NextMethodInterrupt),
            (ConnectError("mock", request=_fake_request), api._NextMethodInterrupt),
            (_fake_http_error, api._NextMethodInterrupt),
            (HookError(UpEvent.GetSmsCode), HookError),
            (RuntimeError, SystemExit),
        ],
    )
    async def test_exception(
        self, up: api.UPLoginMan, exc2r: BaseException, exc2e: Type[BaseException]
    ):
        with pytest.raises(exc2e), mock.patch("qqqr.up.UpLogin.new", side_effect=exc2r):
            await up.new_cookie()

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
    @pytest.mark.parametrize(
        "exc2r,exc2e",
        [
            (NotImplementedError(), SystemExit),
            (asyncio.TimeoutError(), api._NextMethodInterrupt),
            (GeneratorExit(), api._NextMethodInterrupt),
            (ConnectError("mock", request=_fake_request), api._NextMethodInterrupt),
            (_fake_http_error, api._NextMethodInterrupt),
            (HookError(QrEvent.QrFetched), HookError),
        ],
    )
    async def test_exception(
        self, qr: api.QRLoginMan, exc2r: BaseException, exc2e: Type[BaseException]
    ):
        with pytest.raises(exc2e), mock.patch("qqqr.qr.QrLogin.new", side_effect=exc2r):
            await qr.new_cookie()

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


class MixFailureRecord(api.MixedLoginEvent):
    def __init__(self) -> None:
        self.record = []

    async def LoginFailed(self, meth: LoginMethod, _=None):
        self.record.append(meth)

    @property
    def cancel_flag(self) -> asyncio.Event:
        return asyncio.Event()

    @property
    def refresh_flag(self) -> asyncio.Event:
        return self.cancel_flag


mixed_loginman_exc_test_param = [
    ((TencentLoginError(20003, "mock"), UserBreak()), UserBreak, "allow", ["up", "qr"]),
    ((HookError(UpEvent.GetSmsCode), TimeoutError()), LoginError, "allow", ["up", "qr"]),
    ((TencentLoginError(20003, "mock"), GeneratorExit()), LoginError, "allow", ["up", "qr"]),
    ((TencentLoginError(20003, "mock"), _fake_http_error), LoginError, "allow", ["up", "qr"]),
    ((TencentLoginError(20003, "mock"), SystemExit()), SystemExit, "allow", ["up", "qr"]),
    #
    ((SystemExit(), UserBreak()), SystemExit, "allow", ["up"]),
    #
    ((TencentLoginError(20003, "mock"), UserBreak()), UserBreak, "prefer", ["qr", "up"]),
    ((HookError(UpEvent.GetSmsCode), TimeoutError()), LoginError, "prefer", ["qr", "up"]),
    ((TencentLoginError(20003, "mock"), GeneratorExit()), LoginError, "prefer", ["qr", "up"]),
    ((TencentLoginError(20003, "mock"), _fake_http_error), LoginError, "prefer", ["qr", "up"]),
    ((TencentLoginError(20003, "mock"), SystemExit()), SystemExit, "prefer", ["qr"]),
    #
    ((SystemExit(), UserBreak()), SystemExit, "prefer", ["qr", "up"]),
    ((SystemExit(), TimeoutError()), SystemExit, "prefer", ["qr", "up"]),
    ((SystemExit(), GeneratorExit()), SystemExit, "prefer", ["qr", "up"]),
    ((SystemExit(), _fake_http_error), SystemExit, "prefer", ["qr", "up"]),
    ((SystemExit(), SystemExit()), SystemExit, "prefer", ["qr"]),
]


@pytest.mark.parametrize("exc2r,exc2e,strategy,meth", mixed_loginman_exc_test_param)
async def test_mixed_loginman_exc(
    client: ClientAdapter,
    exc2r: Tuple[BaseException, BaseException],
    exc2e: Type[BaseException],
    strategy: api.QrStrategy,
    meth: List[api.LoginMethod],
):
    hook = MixFailureRecord()
    mix = api.MixedLoginMan(client, 1, strategy, "e")
    mix.register_hook(hook)
    with pytest.raises(exc2e), mock.patch(
        f"qqqr.up.UpLogin.new", side_effect=exc2r[0]
    ), mock.patch(f"qqqr.qr.QrLogin.new", side_effect=exc2r[1]):
        await mix.new_cookie()
    await asyncio.sleep(0)
    assert hook.record == meth
