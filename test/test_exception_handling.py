import logging
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientError
from pydantic import SecretStr

from aioqzone.api.login import QrLoginManager, UpLoginManager
from aioqzone.api.login._base import Loginable
from aioqzone.exception import QzoneError, UnexpectedLoginError
from aioqzone.model import QrLoginConfig, UpLoginConfig


def test_qzone_error_str():
    """QzoneError __str__ should return code and msg correctly"""
    err = QzoneError(10001, "test message")
    assert err.code == 10001
    assert err.msg == "test message"
    assert str(err) == "QzoneCode 10001: test message"


def test_qzone_error_with_robj():
    """QzoneError should support robj parameter"""
    robj = {"detail": "test"}
    err = QzoneError(-3000, robj=robj)
    assert err.robj is robj


def test_qzone_error_default_msg():
    """QzoneError should use default msg when no msg provided"""
    err = QzoneError(0)
    assert err.msg == "unknown"
    assert "unknown" in str(err)


def test_qzone_error_args_not_contain_self():
    """QzoneError args should not contain self (core of original bug)"""
    err = QzoneError(10001, "test message")
    assert err.args == ("test message",), "args should contain only the message"
    for arg in err.args:
        assert arg is not err, "args should not contain self"


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
    """QrLoginManager should not swallow KeyboardInterrupt"""
    man = QrLoginManager(client, qr_config)
    man.qrlogin = MagicMock()
    man.qrlogin.login = AsyncMock(side_effect=KeyboardInterrupt)

    with pytest.raises(KeyboardInterrupt):
        await man._new_cookie()


@pytest.mark.asyncio
async def test_up_login_manager_system_exit(client, up_config):
    """UpLoginManager should not swallow SystemExit"""
    man = UpLoginManager(client, up_config)
    man.uplogin = MagicMock()
    man.uplogin.login = AsyncMock(side_effect=SystemExit)

    with pytest.raises(SystemExit):
        await man._new_cookie()


@pytest.mark.asyncio
async def test_qr_login_manager_system_exit(client, qr_config):
    """QrLoginManager should not swallow SystemExit"""
    man = QrLoginManager(client, qr_config)
    man.qrlogin = MagicMock()
    man.qrlogin.login = AsyncMock(side_effect=SystemExit)

    with pytest.raises(SystemExit):
        await man._new_cookie()


@pytest.mark.asyncio
async def test_up_login_manager_wraps_unexpected_error(client, up_config):
    """UpLoginManager should wrap unexpected errors as UnexpectedLoginError"""
    man = UpLoginManager(client, up_config)
    man.uplogin = MagicMock()
    original = ValueError("unexpected")
    man.uplogin.login = AsyncMock(side_effect=original)

    with pytest.raises(UnexpectedLoginError) as exc_info:
        await man._new_cookie()
    assert exc_info.value.__cause__ is original


@pytest.mark.asyncio
async def test_qr_login_manager_wraps_unexpected_error(client, qr_config):
    """QrLoginManager should wrap unexpected errors as UnexpectedLoginError"""
    man = QrLoginManager(client, qr_config)
    man.qrlogin = MagicMock()
    original = ValueError("unexpected")
    man.qrlogin.login = AsyncMock(side_effect=original)

    with pytest.raises(UnexpectedLoginError) as exc_info:
        await man._new_cookie()
    assert exc_info.value.__cause__ is original


@pytest.mark.asyncio
async def test_get_tdc_collect_logs_and_returns_empty(caplog):
    """get_tdc failure should log debug and return empty string"""
    from qqqr.up.captcha import Captcha
    from qqqr.up.captcha.capsess import BaseTcaptchaSession as TcaptchaSession

    captcha = Captcha(MagicMock(), 123, "https://test.com")
    sess = MagicMock(spec=TcaptchaSession)
    sess.get_tdc = AsyncMock(side_effect=ValueError("test error"))
    sess.tdc = MagicMock()
    client = MagicMock()

    with caplog.at_level(logging.DEBUG, logger="qqqr.up.captcha"):
        result = await captcha._get_tdc_collect(sess, client)

    assert result == ""
    assert "get_tdc failed" in caplog.text


@pytest.mark.asyncio
async def test_pass_vc_keyboard_interrupt_propagated():
    """pass_vc should not swallow KeyboardInterrupt"""
    from qqqr.up.web import UpWebSession

    sess = UpWebSession("test_sig")
    sess.check_rst = MagicMock()
    sess.check_rst.session = "test_session"
    solver = MagicMock()
    solver.verify = AsyncMock(side_effect=KeyboardInterrupt)

    with pytest.raises(KeyboardInterrupt):
        await sess.pass_vc(solver)


@pytest.mark.asyncio
async def test_qr_try_again_has_cause(client):
    """TryAgain from QrLoginManager should preserve original exception chain"""
    from aiohttp import ClientError
    from qqqr.up.h5 import UpH5Login
    from qqqr.qr import QrLogin
    from tenacity import TryAgain

    config = QrLoginConfig(uin=123456)
    man = QrLoginManager(client, config)
    man.qrlogin = MagicMock(spec=QrLogin)
    original = ClientError("network error")
    man.qrlogin.login = AsyncMock(side_effect=original)

    with pytest.raises(TryAgain) as exc_info:
        await man._new_cookie()

    assert exc_info.value.__cause__ is original


@pytest.mark.asyncio
async def test_up_try_again_has_cause(client, up_config):
    """TryAgain from UpLoginManager should preserve original exception chain"""
    from aiohttp import ClientError
    from qqqr.up.h5 import UpH5Login
    from tenacity import TryAgain

    man = UpLoginManager(client, up_config)
    man.uplogin = MagicMock(spec=UpH5Login)
    original = ClientError("network error")
    man.uplogin.login = AsyncMock(side_effect=original)

    with pytest.raises(TryAgain) as exc_info:
        await man._new_cookie()

    assert exc_info.value.__cause__ is original
