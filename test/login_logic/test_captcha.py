from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Tuple

import pytest
import pytest_asyncio

from qqqr.constant import captcha_status_description
from qqqr.up import UpH5Login
from qqqr.up.captcha import Captcha, SelectCaptchaSession, TcaptchaSession

if TYPE_CHECKING:
    from qqqr.up.web import UpWebSession
    from qqqr.utils.net import ClientAdapter
    from test.conftest import test_env

pytestmark = pytest.mark.asyncio(loop_scope="module")


def select_captcha_input(prompt: str, imgs: Tuple[bytes, ...]):
    if (root := Path("data/debug")).exists():
        for i, b in enumerate(imgs, start=1):
            with open(root / f"{i}.png", "wb") as f:
                f.write(b)
    r = []
    return r


@pytest_asyncio.fixture(loop_scope="module")
async def login(client: ClientAdapter, env: test_env, CI: bool):
    login = UpH5Login(client, env.uin, env.password.get_secret_value())
    if not CI:
        login.captcha.solve_select_captcha.add_impl(select_captcha_input)
    yield login


@pytest_asyncio.fixture(loop_scope="module")
async def upsess(login: UpH5Login):
    upsess = await login.new()
    await login.check(upsess)
    yield upsess


@pytest_asyncio.fixture(loop_scope="module")
async def captcha(login: UpH5Login):
    yield login.captcha


@pytest_asyncio.fixture(loop_scope="module")
async def sess(captcha: Captcha, upsess: UpWebSession):
    try:
        return await captcha.new(upsess.sid)
    except NotImplementedError:
        pytest.skip("current type of captcha has not been implemented")


class TestCaptcha:
    async def test_windowconf(self, sess: TcaptchaSession):
        assert sess.conf

    async def test_match_md5(self, sess: TcaptchaSession):
        sess.solve_workload()
        ans = sess.pow_ans
        assert 0 < ans <= 3e5
        assert sess.duration >= 50, f"{ans}, {sess.duration}"
        sess.solve_workload()
        assert ans == sess.pow_ans, f"{ans} != {sess.pow_ans}"

    async def test_puzzle(self, client: ClientAdapter, sess: TcaptchaSession):
        await sess.get_captcha_problem(client)

        def _23(prompt: str, imgs: Tuple[bytes, ...]):
            return [2, 3]

        if isinstance(sess, SelectCaptchaSession):
            sess.solve_captcha_hook.impls.insert(0, _23)

        ans = (await sess.solve_captcha()).split(",")
        assert all(i.isdigit() for i in ans)

        if isinstance(sess, SelectCaptchaSession):
            sess.solve_captcha_hook.impls.pop(0)
            assert ans == [
                str(sess.render.json_payload.picture_ids[1]),
                str(sess.render.json_payload.picture_ids[2]),
            ]

    async def test_tdc(self, client: ClientAdapter, sess: TcaptchaSession):
        try:
            await sess.get_tdc(client)
        except Exception:
            pytest.xfail("failed getting TDC")
        assert sess.tdc
        assert callable(sess.tdc.getData)
        assert callable(sess.tdc.getInfo)

    async def test_verify(self, captcha: Captcha, upsess: UpWebSession):
        try:
            r = await captcha.verify(upsess.sid)
        except NotImplementedError:
            if captcha.solve_select_captcha.has_impl:
                pytest.fail("cannot solve captcha")
            pytest.skip("cannot solve captcha")

        if r.code == 0:
            assert r.verifycode
            assert r.ticket
            return

        pytest.fail(captcha_status_description.get(r.code, ""))


# ====== Exception handling tests ======


async def test_get_tdc_collect_logs_and_returns_empty(caplog):
    """get_tdc failure should log debug and return empty string"""
    import logging
    from unittest.mock import AsyncMock, MagicMock

    captcha = Captcha(MagicMock(), 123, "https://test.com")
    from qqqr.up.captcha.capsess import BaseTcaptchaSession as TcaptchaSession

    sess = MagicMock(spec=TcaptchaSession)
    sess.get_tdc = AsyncMock(side_effect=ValueError("test error"))
    sess.tdc = MagicMock()
    client = MagicMock()

    with caplog.at_level(logging.DEBUG, logger="qqqr.up.captcha"):
        result = await captcha._get_tdc_collect(sess, client)

    assert result == ""
    assert "get_tdc failed" in caplog.text


async def test_prehandle_callback_not_found():
    """Captcha.new should raise RuntimeError when prehandle callback not found"""
    from unittest.mock import AsyncMock, MagicMock

    captcha = Captcha(MagicMock(), 123, "https://test.com")
    captcha.client.headers = {"User-Agent": "test-agent"}
    mock_resp = MagicMock()
    mock_resp.text = AsyncMock(return_value="invalid response without callback")
    captcha.client.get = MagicMock()
    captcha.client.get.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    captcha.client.get.return_value.__aexit__ = AsyncMock(return_value=False)

    with pytest.raises(RuntimeError, match="prehandle callback not found"):
        await captcha.new("test_sid")


async def test_tdc_info_type_check():
    """Captcha.verify should raise TypeError when tdc info is not str"""
    from unittest.mock import AsyncMock, MagicMock, patch

    captcha = Captcha(MagicMock(), 123, "https://test.com")
    from qqqr.up.captcha.capsess import BaseTcaptchaSession as TcaptchaSession

    sess = MagicMock(spec=TcaptchaSession)
    sess.data_type = "test"
    sess.tdc = MagicMock()
    sess.tdc.getInfo = MagicMock(return_value={"info": 12345})
    sess.prehandle = {"sess": "test", "captcha": {"common": {"pow_cfg": {"prefix": "0", "md5": "0"}}}}
    sess.conf = {"common": {"pow_cfg": {"prefix": "0", "md5": "0"}}}
    sess.pow_ans = 0
    sess.duration = 50
    sess.solve_captcha = AsyncMock(return_value="test_ans")

    with patch.object(captcha, "new", AsyncMock(return_value=sess)):
        with patch.object(captcha, "_get_tdc_collect", AsyncMock(return_value="")):
            with pytest.raises(TypeError, match="tdc info"):
                await captcha.verify("test_sid")
