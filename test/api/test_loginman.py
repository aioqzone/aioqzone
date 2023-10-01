from __future__ import annotations

import asyncio
import io
from contextlib import ExitStack, suppress
from os import environ
from typing import TYPE_CHECKING, List, Tuple, cast
from unittest.mock import patch

import pytest
import pytest_asyncio
from aiohttp import ClientConnectionError as ConnectError
from aiohttp import ClientResponseError
from aiohttp import RequestInfo as Request

from aioqzone.api import LoginMethod, QrLoginConfig, UnifiedLoginManager, UpLoginConfig
from aioqzone.exception import LoginError, SkipLoginInterrupt
from qqqr.exception import TencentLoginError, UserBreak
from qqqr.utils.net import ClientAdapter

if TYPE_CHECKING:
    from test.conftest import test_env

    from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio
skip_ci = pytest.mark.skipif(bool(environ.get("CI")), reason="Skip QR loop in CI")

_fake_request = cast(Request, ...)
_fake_http_error = ClientResponseError(_fake_request, (), code=403)


@pytest_asyncio.fixture
async def up(client: ClientAdapter, env: test_env):
    man = UnifiedLoginManager(client, up_config=UpLoginConfig(uin=env.uin, pwd=env.password))
    man.order = ["up"]
    yield man


class TestUP:
    @pytest.mark.parametrize(
        ["exc2r"],
        [
            (TencentLoginError(-3002, "mock"),),
            (NotImplementedError(),),
            (GeneratorExit(),),
            (ConnectError("mock"),),
            (_fake_http_error,),
        ],
    )
    async def test_exception(self, up: UnifiedLoginManager, exc2r: BaseException):
        with patch.object(up.uplogin, "new", side_effect=exc2r):
            r = await up._try_up_login()
            assert isinstance(r, str)

    async def test_newcookie(self, up: UnifiedLoginManager):
        pool = []
        up.login_success.add_impl(lambda uin, method: pool.append(uin))
        try:
            cookie = await up.new_cookie()
            await up.channel.wait()
        except LoginError as e:
            pytest.skip(str(e))
        else:
            assert "p_skey" in cookie
            assert up.uin in pool
            assert up.cookie
            assert up.gtk >= 0


@pytest_asyncio.fixture
async def qr(client: ClientAdapter, env: test_env):
    man = UnifiedLoginManager(client, qr_config=QrLoginConfig(uin=env.uin))
    with suppress(ImportError):
        from PIL import Image as image

        man.qr_fetched.add_impl(lambda png, times: image.open(io.BytesIO(png)).show())
    man.order = ["qr"]
    yield man


class TestQR:
    @pytest.mark.parametrize(
        ["exc2r"],
        [
            (asyncio.TimeoutError(),),
            (GeneratorExit(),),
            (ConnectError("mock"),),
            (_fake_http_error,),
        ],
    )
    async def test_exception(self, qr: UnifiedLoginManager, exc2r: BaseException):
        with patch.object(qr.qrlogin, "new", side_effect=exc2r):
            r = await qr._try_qr_login()
            assert isinstance(r, str)

    @skip_ci
    async def test_newcookie(self, qr: UnifiedLoginManager):
        pool = []
        qr.login_success.add_impl(lambda uin, method: pool.append(uin))
        try:
            cookie = await qr.new_cookie()
            await qr.channel.wait()
        except LoginError as e:
            pytest.skip(str(e))
        else:
            assert "p_skey" in cookie
            assert qr.uin in pool
            assert qr.cookie
            assert qr.gtk >= 0


@pytest.fixture
def mix(client: ClientAdapter, env: test_env):
    man = UnifiedLoginManager(
        client,
        up_config=UpLoginConfig(uin=env.uin, pwd=env.password),
        qr_config=QrLoginConfig(uin=env.uin),
    )
    with suppress(ImportError):
        from PIL import Image as image

        man.qr_fetched.add_impl(lambda png, times: image.open(io.BytesIO(png)).show())

    yield man


allow = ["up", "qr"]
prefer = ["qr", "up"]
mixed_loginman_exc_test_param = [
    ((TencentLoginError(20003, "mock"), UserBreak()), allow, ["up", "qr"]),
    ((TencentLoginError(20003, "mock"), GeneratorExit()), allow, ["up", "qr"]),
    ((TencentLoginError(20003, "mock"), _fake_http_error), allow, ["up", "qr"]),
    ((TencentLoginError(20003, "mock"), SystemExit()), allow, ["up", "qr"]),
    #
    ((SystemExit(), UserBreak()), allow, ["up"]),
    #
    ((TencentLoginError(20003, "mock"), UserBreak()), prefer, ["qr", "up"]),
    ((TencentLoginError(20003, "mock"), GeneratorExit()), prefer, ["qr", "up"]),
    ((TencentLoginError(20003, "mock"), _fake_http_error), prefer, ["qr", "up"]),
    ((TencentLoginError(20003, "mock"), SystemExit()), prefer, ["qr"]),
    #
    ((SystemExit(), UserBreak()), prefer, ["qr", "up"]),
    ((SystemExit(), asyncio.TimeoutError()), prefer, ["qr", "up"]),
    ((SystemExit(), GeneratorExit()), prefer, ["qr", "up"]),
    ((SystemExit(), _fake_http_error), prefer, ["qr", "up"]),
    ((SystemExit(), SystemExit()), prefer, ["qr"]),
]


@pytest.mark.parametrize(["exc2r", "order", "gt_hist"], mixed_loginman_exc_test_param)
async def test_mixed_loginman_exc(
    mix: UnifiedLoginManager,
    exc2r: Tuple[BaseException, BaseException],
    order: List[LoginMethod],
    gt_hist: List[LoginMethod],
):
    mix.order = order
    meth_history = []
    mix.login_failed.add_impl(lambda uin, method, exc: meth_history.append(method))

    with ExitStack() as stack:
        stack.enter_context(pytest.raises(LoginError))
        stack.enter_context(patch.object(mix.uplogin, "new", side_effect=exc2r[0]))
        stack.enter_context(patch.object(mix.qrlogin, "new", side_effect=exc2r[1]))
        await mix.new_cookie()

    await mix.channel.wait()
    assert meth_history == gt_hist


async def test_unified_loginman_skip(mix: UnifiedLoginManager):
    mix.order = []
    with pytest.raises(SkipLoginInterrupt):
        await mix.new_cookie()


async def test_suppress(mix: UnifiedLoginManager):
    mix.order = ["qr"]
    with patch.object(mix.qrlogin, "new", side_effect=_fake_http_error):
        with pytest.raises(LoginError):
            await mix.new_cookie()
        assert mix.last_qr_attempt

        with pytest.raises(SkipLoginInterrupt):
            await mix.new_cookie()

        with pytest.raises(LoginError), mix.force_login():
            await mix.new_cookie()
