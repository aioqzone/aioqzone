from __future__ import annotations

import asyncio
import io
from os import environ
from typing import TYPE_CHECKING, Type, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from aiohttp import ClientConnectionError as ConnectError
from aiohttp import ClientResponseError
from aiohttp import RequestInfo as Request
from PIL import Image as image
from pydantic import SecretStr
from tenacity import TryAgain

from aioqzone.api import QrLoginConfig, QrLoginManager, UpLoginConfig, UpLoginManager
from aioqzone.api.login._base import Loginable
from aioqzone.exception import QzoneError, UnexpectedLoginError
from qqqr.exception import TencentLoginError, UserBreak
from qqqr.utils.net import ClientAdapter

if TYPE_CHECKING:
    from test.conftest import test_env

pytestmark = pytest.mark.asyncio(loop_scope="module")
skip_ci = pytest.mark.skipif(bool(environ.get("CI")), reason="Skip QR loop in CI")

_fake_request = cast(Request, ...)
_fake_http_error = ClientResponseError(_fake_request, (), status=403)


@pytest_asyncio.fixture
async def up(client: ClientAdapter, env: test_env):
    yield UpLoginManager(client, config=UpLoginConfig(uin=env.uin, pwd=env.password))


class TestUP:
    @pytest.mark.parametrize(
        ["exc2r", "exc2e"],
        [
            (TencentLoginError(-3002, "mock"), TencentLoginError),
            (TencentLoginError(-3000, "请重新登录"), TryAgain),
            (NotImplementedError(), TencentLoginError),
            (GeneratorExit(), TryAgain),
            (ConnectError("mock"), TryAgain),
            (_fake_http_error, TryAgain),
            (SystemExit(), SystemExit),
        ],
    )
    async def test_exception(
        self, up: UpLoginManager, exc2r: BaseException, exc2e: Type[BaseException]
    ):
        with patch.object(up.uplogin, "login", side_effect=exc2r), pytest.raises(exc2e):
            await up._new_cookie()

    async def test_newcookie(self, up: UpLoginManager):
        pool = []
        up.login_success.add_impl(lambda uin: pool.append(uin))
        up.login_failed.add_impl(lambda uin, exc: pool.append(exc))

        success = await up.new_cookie()
        assert up.last_login > 0
        await up.ch_login_notify.wait()
        assert pool

        if not success:
            pytest.skip(str(pool[0]))

        assert "p_skey" in up.cookie
        assert up.uin == pool[0]
        assert up.cookie
        assert up.gtk > 0


@pytest_asyncio.fixture
async def qr(client: ClientAdapter, env: test_env):
    man = QrLoginManager(client, config=QrLoginConfig(uin=env.uin))

    man.qr_fetched.add_impl(
        lambda png, times, qr_renew=False: image.open(io.BytesIO(png)).show() if png else None
    )
    yield man


class TestQR:
    @pytest.mark.parametrize(
        ["exc2r", "exc2e"],
        [
            (UserBreak, UserBreak),
            (asyncio.CancelledError, UserBreak),
            (GeneratorExit(), TryAgain),
            (ConnectError("mock"), TryAgain),
            (_fake_http_error, TryAgain),
            (SystemExit, SystemExit),
        ],
    )
    async def test_exception(
        self, qr: QrLoginManager, exc2r: BaseException, exc2e: Type[BaseException]
    ):
        with patch.object(qr.qrlogin, "login", side_effect=exc2r), pytest.raises(exc2e):
            await qr._new_cookie()

    @skip_ci
    async def test_newcookie(self, qr: QrLoginManager):
        pool = []
        qr.login_success.add_impl(lambda uin: pool.append(uin))
        qr.login_failed.add_impl(lambda uin, exc: pool.append(exc))

        success = await qr.new_cookie()
        assert qr.last_login > 0
        await qr.ch_login_notify.wait()
        assert pool

        if not success:
            pytest.skip(str(pool[0]))

        assert "p_skey" in qr.cookie
        assert qr.uin == pool[0]
        assert qr.cookie
        assert qr.gtk > 0


@skip_ci
async def test_const(client: ClientAdapter, qr: QrLoginManager):
    from aioqzone.api.h5 import QzoneH5API
    from aioqzone.api.login import ConstLoginMan

    api = QzoneH5API(client, qr)
    resp1 = await api.index()
    assert resp1.qzonetoken
    assert qr.cookie
    api = QzoneH5API(client, ConstLoginMan.from_loginable(qr), retry_if_login_expire=False)
    assert isinstance(api.login, ConstLoginMan)
    assert api.login.cookie
    resp2 = await api.index()
    assert resp2.vFeeds


# ====== Exception class tests ======


async def test_qzone_error_str():
    """QzoneError __str__ should return code and msg correctly"""
    err = QzoneError(10001, "test message")
    assert err.code == 10001
    assert err.msg == "test message"
    assert str(err) == "QzoneCode 10001: test message"


async def test_qzone_error_with_robj():
    """QzoneError should support robj parameter"""
    robj = {"detail": "test"}
    err = QzoneError(-3000, robj=robj)
    assert err.robj is robj


async def test_qzone_error_default_msg():
    """QzoneError should use default msg when no msg provided"""
    err = QzoneError(0)
    assert err.msg == "unknown"
    assert "unknown" in str(err)


async def test_qzone_error_args_not_contain_self():
    """QzoneError args should not contain self (core of original bug)"""
    err = QzoneError(10001, "test message")
    assert err.args == ("test message",), "args should contain only the message"
    for arg in err.args:
        assert arg is not err, "args should not contain self"


# ====== Loginable.new_cookie exception propagation tests ======


class DummyLoginable(Loginable):
    async def _new_cookie(self):
        return {}


@pytest.mark.asyncio
async def test_keyboard_interrupt_propagated():
    """KeyboardInterrupt should not be swallowed by login"""
    man = DummyLoginable(123456)
    man._new_cookie = AsyncMock(side_effect=KeyboardInterrupt)

    with pytest.raises(KeyboardInterrupt):
        await man.new_cookie()


@pytest.mark.asyncio
async def test_system_exit_propagated():
    """SystemExit should not be swallowed by login"""
    man = DummyLoginable(123456)
    man._new_cookie = AsyncMock(side_effect=SystemExit)

    with pytest.raises(SystemExit):
        await man.new_cookie()


@pytest.mark.asyncio
async def test_generator_exit_propagated():
    """GeneratorExit should not be swallowed by login"""
    man = DummyLoginable(123456)
    man._new_cookie = AsyncMock(side_effect=GeneratorExit)

    with pytest.raises(GeneratorExit):
        await man.new_cookie()


@pytest.mark.asyncio
async def test_exception_triggers_login_failed():
    """Normal Exception should be caught and trigger login_failed"""
    man = DummyLoginable(123456)
    man._new_cookie = AsyncMock(side_effect=ValueError("test error"))

    result = await man.new_cookie()
    assert result is False


# ====== Login manager exception propagation tests ======


@pytest.fixture
def up_config():
    return UpLoginConfig(uin=123456, pwd=SecretStr("test"))


@pytest.fixture
def qr_config():
    return QrLoginConfig(uin=123456)


@pytest.mark.asyncio
async def test_up_login_manager_keyboard_interrupt(client, up_config):
    """UpLoginManager should not swallow KeyboardInterrupt"""
    man = UpLoginManager(client, up_config)
    man.uplogin = MagicMock()
    man.uplogin.login = AsyncMock(side_effect=KeyboardInterrupt)

    with pytest.raises(KeyboardInterrupt):
        await man._new_cookie()


@pytest.mark.asyncio
async def test_qr_login_manager_keyboard_interrupt(client, qr_config):
    """QrLoginManager should forward KeyboardInterrupt as UserBreak"""
    man = QrLoginManager(client, qr_config)
    man.qrlogin = MagicMock()
    man.qrlogin.login = AsyncMock(side_effect=KeyboardInterrupt)

    with pytest.raises(UserBreak):
        await man._new_cookie()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "manager_cls,config_fixture,attr",
    [
        (UpLoginManager, "up_config", "uplogin"),
        (QrLoginManager, "qr_config", "qrlogin"),
    ],
)
async def test_login_manager_system_exit(client, request, manager_cls, config_fixture, attr):
    """Login managers should not swallow SystemExit"""
    config = request.getfixturevalue(config_fixture)
    man = manager_cls(client, config)
    setattr(man, attr, MagicMock())
    getattr(man, attr).login = AsyncMock(side_effect=SystemExit)

    with pytest.raises(SystemExit):
        await man._new_cookie()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "manager_cls,config_fixture,attr",
    [
        (UpLoginManager, "up_config", "uplogin"),
        (QrLoginManager, "qr_config", "qrlogin"),
    ],
)
async def test_login_manager_wraps_unexpected_error(
    client, request, manager_cls, config_fixture, attr
):
    """Login managers should wrap unexpected errors as UnexpectedLoginError"""
    config = request.getfixturevalue(config_fixture)
    man = manager_cls(client, config)
    setattr(man, attr, MagicMock())
    original = ValueError("unexpected")
    getattr(man, attr).login = AsyncMock(side_effect=original)

    with pytest.raises(UnexpectedLoginError) as exc_info:
        await man._new_cookie()
    assert exc_info.value.__cause__ is original


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "manager_cls,config_fixture,attr,spec_cls",
    [
        (QrLoginManager, "qr_config", "qrlogin", "qqqr.qr.QrLogin"),
        (UpLoginManager, "up_config", "uplogin", "qqqr.up.h5.UpH5Login"),
    ],
)
async def test_try_again_has_cause(client, request, manager_cls, config_fixture, attr, spec_cls):
    """TryAgain should preserve original exception chain"""
    import importlib

    module_path, cls_name = spec_cls.rsplit(".", 1)
    spec_cls = getattr(importlib.import_module(module_path), cls_name)

    config = request.getfixturevalue(config_fixture)
    man = manager_cls(client, config)
    setattr(man, attr, MagicMock(spec=spec_cls))
    original = ConnectError("network error")
    getattr(man, attr).login = AsyncMock(side_effect=original)

    with pytest.raises(TryAgain) as exc_info:
        await man._new_cookie()
    assert exc_info.value.__cause__ is original
