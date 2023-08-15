from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

pytest.importorskip("numpy")
pytest.importorskip("PIL")
pytest.importorskip("chaosvm")

import pytest_asyncio

from qqqr.constant import captcha_status_description
from qqqr.up import UpWebLogin
from qqqr.up.captcha import Captcha, TcaptchaSession

if TYPE_CHECKING:
    from test.conftest import test_env

    from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def captcha(client: ClientAdapter, env: test_env):
    login = UpWebLogin(client, env.uin, env.password.get_secret_value())
    upsess = await login.new()
    await login.check(upsess)
    captcha = login.captcha(upsess.check_rst.session)
    yield captcha


@pytest_asyncio.fixture(scope="class")
async def sess(captcha: Captcha):
    return await captcha.new()


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

    async def test_puzzle(self, captcha: Captcha, sess: TcaptchaSession):
        await captcha.get_captcha_problem(sess)
        captcha.solve_captcha(sess)
        assert sess.jig_ans[0]
        assert sess.jig_ans[1]
        assert sess.mouse_track

    async def test_tdc(self, captcha: Captcha, sess: TcaptchaSession):
        await captcha.get_tdc(sess)
        assert sess.tdc
        assert callable(sess.tdc.getData)
        assert callable(sess.tdc.getInfo)

    async def test_verify(self, captcha: Captcha):
        r = await captcha.verify()
        if r.code == 0:
            assert r.verifycode
            assert r.ticket
            return

        pytest.fail(msg=captcha_status_description.get(r.code))


@pytest_asyncio.fixture(scope="class")
async def vm(captcha: Captcha, sess: TcaptchaSession):
    await captcha.get_tdc(sess)
    yield sess.tdc
