import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import ClientError
from pydantic import SecretStr
from tenacity import TryAgain

from aioqzone.api.h5 import QzoneH5API
from aioqzone.api.login import ConstLoginMan, QrLoginManager, UpLoginManager
from aioqzone.api.login._base import Loginable
from aioqzone.exception import QzoneError, UnexpectedLoginError
from aioqzone.model import QrLoginConfig, UpLoginConfig
from aioqzone.model.api import IndexPageApi
from aioqzone.model.api.response import (
    AddCommentLegacyResp,
    DeleteCommentResp,
    PhotosPreuploadResponse,
    UploadPicResponse,
)


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
    from tenacity import TryAgain

    from qqqr.qr import QrLogin
    from qqqr.up.h5 import UpH5Login

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
    from tenacity import TryAgain

    from qqqr.up.h5 import UpH5Login

    man = UpLoginManager(client, up_config)
    man.uplogin = MagicMock(spec=UpH5Login)
    original = ClientError("network error")
    man.uplogin.login = AsyncMock(side_effect=original)

    with pytest.raises(TryAgain) as exc_info:
        await man._new_cookie()

    assert exc_info.value.__cause__ is original


# ====== 7a: response.py assert replacements ======


@pytest.mark.asyncio
async def test_add_comment_legacy_callback_not_found():
    """AddCommentLegacyResp.response_to_object should raise TryAgain when callback not found"""
    mock_resp = AsyncMock()
    mock_resp.text = AsyncMock(
        return_value="""<html><body>
<script type="text/javascript">frameElement.callback</script>
</body></html>"""
    )
    with pytest.raises(TryAgain, match="callback not found"):
        await AddCommentLegacyResp.response_to_object(mock_resp)


@pytest.mark.asyncio
async def test_delete_comment_callback_not_found():
    """DeleteCommentResp.response_to_object should raise TryAgain when callback not found"""
    mock_resp = AsyncMock()
    mock_resp.text = AsyncMock(
        return_value="""<html><body>
<script type="text/javascript">frameElement.callback</script>
</body></html>"""
    )
    with pytest.raises(TryAgain, match="callback not found"):
        await DeleteCommentResp.response_to_object(mock_resp)


@pytest.mark.asyncio
async def test_upload_pic_callback_not_found():
    """UploadPicResponse.response_to_object should raise TryAgain when callback not found"""
    mock_resp = AsyncMock()
    mock_resp.text = AsyncMock(return_value="""<html><body>no callback here</body></html>""")
    with pytest.raises(TryAgain, match="callback not found"):
        await UploadPicResponse.response_to_object(mock_resp)


@pytest.mark.asyncio
async def test_photos_preupload_callback_not_found():
    """PhotosPreuploadResponse.response_to_object should raise TryAgain when callback not found"""
    mock_resp = AsyncMock()
    mock_resp.text = AsyncMock(return_value="""<html><body>no callback here</body></html>""")
    with pytest.raises(TryAgain, match="callback not found"):
        await PhotosPreuploadResponse.response_to_object(mock_resp)


@pytest.mark.asyncio
async def test_profile_page_not_list_raises():
    """ProfilePagePesp should raise TryAgain when data is not list"""
    from aioqzone.model.api.response import ProfilePagePesp

    mock_resp = AsyncMock()
    mock_resp.text = AsyncMock(
        return_value="""<html><body>
<script type="application/javascript">window.shine0callback || return "abc123"; var FrontPage = {data: ["not_a_list"]};</script>
</body></html>"""
    )
    with pytest.raises(TryAgain, match="profile not returned"):
        await ProfilePagePesp.response_to_object(mock_resp)


# ====== 7c: qr/__init__.py assert replacements ======


@pytest.mark.asyncio
async def test_show_without_qrsig_raises():
    """show should raise RuntimeError when qrsig cookie not found in response"""
    from qqqr.qr import QrLogin

    login = QrLogin(MagicMock(), 123456)
    mock_response = MagicMock()
    mock_response.cookies = {}
    mock_response.content.read = AsyncMock(return_value=b"png_data")
    login.client.get = MagicMock()
    login.client.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    login.client.get.return_value.__aexit__ = AsyncMock(return_value=False)

    with pytest.raises(RuntimeError, match="qrsig"):
        await login.show(push_qr=False)


@pytest.mark.asyncio
async def test_show_push_qr_no_callback_raises():
    """show(push_qr=True) should raise RuntimeError when ptui_qrcode_CB not found"""
    from qqqr.qr import QrLogin

    login = QrLogin(MagicMock(), 123456)
    mock_response = MagicMock()
    mock_response.cookies = {}
    mock_response.text = AsyncMock(return_value="invalid response")
    login.client.get = MagicMock()
    login.client.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
    login.client.get.return_value.__aexit__ = AsyncMock(return_value=False)

    with pytest.raises(RuntimeError, match="ptui_qrcode_CB"):
        await login.show(push_qr=True)


# ====== 8: h5/model.py AssertionError -> RuntimeError ======


@pytest.mark.asyncio
async def test_call_retry_exhausted_raises():
    """call should raise RuntimeError when retries exhausted"""
    client = MagicMock()
    login = ConstLoginMan(123456)
    # Set cookie so gtk > 0 (call checks gtk before reaching the patched retry)
    login.cookie = {"p_skey": "dummy"}
    api = QzoneH5API(client, login)

    async def _no_iter():
        return
        yield  # make it an async generator that yields nothing

    with patch.object(api, "_relogin_retry", new_callable=MagicMock) as mock_retry:
        mock_retry.__aiter__ = MagicMock(return_value=_no_iter())

        with pytest.raises(RuntimeError, match="max retry exceeded"):
            await api.call(IndexPageApi())
