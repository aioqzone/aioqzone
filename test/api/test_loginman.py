from __future__ import annotations

import asyncio
import io
from contextlib import ExitStack, suppress
from typing import TYPE_CHECKING, List, Tuple, Type, cast
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ConnectError, HTTPError, Request

import aioqzone.api.loginman as api
from aioqzone._messages import LoginMethod
from aioqzone.exception import LoginError, SkipLoginInterrupt
from qqqr.exception import TencentLoginError, UserBreak
from qqqr.qr import QrLogin
from qqqr.up import UpWebLogin
from qqqr.utils.net import ClientAdapter

if TYPE_CHECKING:
    from test.conftest import test_env

    from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio

_fake_request = cast(Request, ...)
_fake_http_error = HTTPError("mock")
_fake_http_error.request = _fake_request


@pytest_asyncio.fixture
async def up(client: ClientAdapter, env: test_env):
    yield api.UPLoginMan(client, env.uin, env.pwd.get_secret_value())


class TestUP:
    @pytest.mark.parametrize(
        ["exc2r", "exc2e"],
        [
            (TencentLoginError(-3002, "mock"), TencentLoginError),
            (NotImplementedError(), TencentLoginError),
            (GeneratorExit(), api._NextMethodInterrupt),
            (ConnectError("mock", request=_fake_request), api._NextMethodInterrupt),
            (_fake_http_error, api._NextMethodInterrupt),
            (RuntimeError, RuntimeError),
        ],
    )
    async def test_exception(
        self, up: api.UPLoginMan, exc2r: BaseException, exc2e: Type[BaseException]
    ):
        pool = []
        up.login_failed.listeners.append(lambda m: pool.append(m.exc))
        up.login_success.listeners.append(lambda m: pool.append("success"))
        with pytest.raises(exc2e), patch.object(up.uplogin, "new", side_effect=exc2r):
            await up.new_cookie()
        await up.login_notify_channel.wait()
        assert pool
        assert "success" not in pool

    async def test_newcookie(self, up: api.UPLoginMan):
        pool = []
        up.login_success.listeners.append(lambda m: pool.append(m.uin))
        try:
            cookie = await up.new_cookie()
        except TencentLoginError as e:
            pytest.skip(str(e))
        else:
            assert "p_skey" in cookie
            assert up.uin in pool
            assert up.cookie
            assert up.gtk >= 0


@pytest_asyncio.fixture
async def qr(client: ClientAdapter, env: test_env):
    man = api.QRLoginMan(client, env.uin)
    with suppress(ImportError):
        from PIL import Image as image

        man.qr_fetched.listeners.append(lambda m: image.open(io.BytesIO(m.png)).show())
    yield man


class TestQR:
    @pytest.mark.parametrize(
        "exc2r,exc2e",
        [
            (NotImplementedError(), NotImplementedError),
            (asyncio.TimeoutError(), api._NextMethodInterrupt),
            (GeneratorExit(), api._NextMethodInterrupt),
            (ConnectError("mock", request=_fake_request), api._NextMethodInterrupt),
            (_fake_http_error, api._NextMethodInterrupt),
        ],
    )
    async def test_exception(
        self, qr: api.QRLoginMan, exc2r: BaseException, exc2e: Type[BaseException]
    ):
        pool = []
        qr.login_success.listeners.append(lambda m: pool.append("success"))
        qr.login_failed.listeners.append(lambda m: pool.append(m.exc))
        with pytest.raises(exc2e), patch.object(qr.qrlogin, "new", side_effect=exc2r):
            await qr.new_cookie()
        await qr.login_notify_channel.wait()
        assert pool
        assert "success" not in pool

    @pytest.mark.skip("this test should be called manually")
    async def test_newcookie(self, qr: api.QRLoginMan):
        pool = []
        qr.login_success.listeners.append(lambda m: pool.append(m.uin))
        try:
            cookie = await qr.new_cookie()
        except TencentLoginError as e:
            pytest.skip(str(e))
        else:
            assert "p_skey" in cookie
            assert qr.uin in pool
            assert qr.cookie
            assert qr.gtk >= 0


allow = ["up", "qr"]
prefer = ["qr", "up"]
mixed_loginman_exc_test_param = [
    ((TencentLoginError(20003, "mock"), UserBreak()), UserBreak, allow, ["up", "qr"]),
    ((TencentLoginError(20003, "mock"), GeneratorExit()), LoginError, allow, ["up", "qr"]),
    ((TencentLoginError(20003, "mock"), _fake_http_error), LoginError, allow, ["up", "qr"]),
    ((TencentLoginError(20003, "mock"), SystemExit()), SystemExit, allow, ["up", "qr"]),
    #
    ((SystemExit(), UserBreak()), SystemExit, allow, ["up"]),
    #
    ((TencentLoginError(20003, "mock"), UserBreak()), UserBreak, prefer, ["qr", "up"]),
    ((TencentLoginError(20003, "mock"), GeneratorExit()), LoginError, prefer, ["qr", "up"]),
    ((TencentLoginError(20003, "mock"), _fake_http_error), LoginError, prefer, ["qr", "up"]),
    ((TencentLoginError(20003, "mock"), SystemExit()), SystemExit, prefer, ["qr"]),
    #
    ((SystemExit(), UserBreak()), SystemExit, prefer, ["qr", "up"]),
    ((SystemExit(), asyncio.TimeoutError()), SystemExit, prefer, ["qr", "up"]),
    ((SystemExit(), GeneratorExit()), SystemExit, prefer, ["qr", "up"]),
    ((SystemExit(), _fake_http_error), SystemExit, prefer, ["qr", "up"]),
    ((SystemExit(), SystemExit()), SystemExit, prefer, ["qr"]),
]


@pytest.mark.parametrize(["exc2r", "exc2e", "order", "gt_hist"], mixed_loginman_exc_test_param)
async def test_mixed_loginman_exc(
    client: ClientAdapter,
    exc2r: Tuple[BaseException, BaseException],
    exc2e: Type[BaseException],
    order: List[LoginMethod],
    gt_hist: List[LoginMethod],
):
    meth_history = []
    mix = api.MixedLoginMan(client, 1, order, "e")
    mix.login_failed.listeners.append(lambda m: meth_history.append(m.method))

    with ExitStack() as stack:
        stack.enter_context(pytest.raises(exc2e))
        if c := mix.loginables.get("up"):
            assert isinstance(c, api.UPLoginMan)
            stack.enter_context(patch.object(c.uplogin, "new", side_effect=exc2r[0]))
        if c := mix.loginables.get("qr"):
            assert isinstance(c, api.QRLoginMan)
            stack.enter_context(patch.object(c.qrlogin, "new", side_effect=exc2r[1]))

        await mix.new_cookie()

    await mix.login_notify_channel.wait()
    assert meth_history == gt_hist


async def test_mixed_loginman_skip(client: ClientAdapter):
    class sub_mix_loginman(api.MixedLoginMan):
        def ordered_methods(self):
            return []

    mix = sub_mix_loginman(client, 1, ["up", "qr"], "e")
    with pytest.raises(SkipLoginInterrupt):
        await mix._new_cookie()
