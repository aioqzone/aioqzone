from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

pytest.importorskip("numpy")
pytest.importorskip("PIL")
pytest.importorskip("chaosvm")

import pytest_asyncio

from qqqr.constant import captcha_status_description
from qqqr.up import UpH5Login
from qqqr.up.captcha import Captcha, TcaptchaSession

if TYPE_CHECKING:
    from test.conftest import test_env

    from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def captcha(client: ClientAdapter, env: test_env):
    login = UpH5Login(client, env.uin, env.password.get_secret_value())
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

    async def test_puzzle(self, client: ClientAdapter, sess: TcaptchaSession):
        await sess.get_captcha_problem(client)
        ans = (await sess.solve_captcha()).split(",")[0]
        assert ans.isdigit()

    async def test_tdc(self, client: ClientAdapter, sess: TcaptchaSession):
        await sess.get_tdc(client)
        assert sess.tdc
        assert callable(sess.tdc.getData)
        assert callable(sess.tdc.getInfo)

    async def test_verify(self, captcha: Captcha):
        try:
            r = await captcha.verify()
        except NotImplementedError:
            pytest.xfail("cannot solve captcha")
        if r.code == 0:
            assert r.verifycode
            assert r.ticket
            return

        pytest.fail(msg=captcha_status_description.get(r.code))


@pytest_asyncio.fixture(scope="class")
async def vm(client: ClientAdapter, sess: TcaptchaSession):
    await sess.get_tdc(client)
    yield sess.tdc
