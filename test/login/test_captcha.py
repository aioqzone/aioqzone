from os import environ as env

import pytest
import pytest_asyncio

from qqqr.constant import QzoneAppid, QzoneProxy
from qqqr.up import UpLogin
from qqqr.up.captcha import TDC, Captcha, TcaptchaSession
from qqqr.up.captcha.jigsaw import imitate_drag
from qqqr.up.captcha.vm import DecryptTDC
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def captcha(client: ClientAdapter):
    login = UpLogin(client, QzoneAppid, QzoneProxy, int(env["TEST_UIN"]), env["TEST_PASSWORD"])
    upsess = await login.new()
    captcha = login.captcha(upsess.check_rst.session)
    yield captcha


@pytest_asyncio.fixture(scope="class")
async def sess(captcha: Captcha):
    sess = await captcha.new()
    await captcha.get_tdc_vm(sess)
    yield sess


@pytest.mark.incremental
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
        await captcha.solve_captcha(sess)
        assert sess.jig_ans[0]
        assert sess.jig_ans[1]

    async def test_verify(self, captcha: Captcha):
        r = await captcha.verify()
        assert r.verifycode
        assert r.code == 0


@pytest_asyncio.fixture(scope="class")
async def vm(captcha: Captcha, sess: TcaptchaSession):
    await captcha.get_tdc_vm(sess)
    yield sess.tdc


class TestVM:
    async def testGetInfo(self, vm: TDC):
        d = await vm.get_info()
        assert d
        assert d["info"]

    async def testCollectData(self, vm: TDC):
        vm.set_data(clientType=2)
        vm.set_data(coordinate=[10, 24, 0.4103])
        vm.set_data(trycnt=1, refreshcnt=0, slideValue=imitate_drag(230), dragobj=1)
        vm.set_data(ft="qf_7P_n_H")
        d = await vm.get_data()
        assert d
        assert len(d) > 200

    async def testGetCookie(self, vm: TDC):
        cookie = await vm.get_cookie()
        assert "TDC_itoken" in cookie


@pytest.mark.needuser
async def test_decrypt(vm: TDC, captcha: Captcha, sess: TcaptchaSession):
    vm.set_data(clientType=2)
    vm.set_data(coordinate=[10, 24, 0.4103])
    vm.set_data(trycnt=1, refreshcnt=0, slideValue=imitate_drag(230), dragobj=1)
    vm.set_data(ft="qf_7P_n_H")

    collect = await vm.get_data()

    await captcha.get_tdc_vm(sess, cls=DecryptTDC)
    decrypt = await DecryptTDC.decrypt(sess.tdc, collect)  # type: ignore
    print(decrypt)
