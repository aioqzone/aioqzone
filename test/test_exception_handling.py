from unittest.mock import AsyncMock

import pytest
from aioqzone.api.login._base import Loginable
from aioqzone.exception import QzoneError


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
