import asyncio
import imp
from math import floor
from os import environ as env

import pytest
import pytest_asyncio
from aiohttp import ClientSession

from qqqr.constants import QzoneAppid, QzoneProxy
from qqqr.up import UPLogin, User
from qqqr.up.captcha import TDC, Captcha, IframeParser
from qqqr.up.captcha.jigsaw import Jigsaw
from qqqr.up.captcha.vm import DecryptTDC


@pytest.fixture(scope="module")
def event_loop():
    import jssupport.execjs

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def captcha():
    async with ClientSession() as sess:
        async with UPLogin(
            sess, QzoneAppid, QzoneProxy, User(int(env["TEST_UIN"]), env["TEST_PASSWORD"])
        ) as login:
            captcha = login.captcha((await login.check()).session)
            await captcha.prehandle(login.xlogin_url)
            yield captcha


@pytest_asyncio.fixture(scope="module")
async def shelper(captcha, iframe: str):
    shelper = IframeParser(captcha.appid, captcha.sid, 2)
    shelper.parseCaptchaConf(iframe)
    yield shelper


@pytest_asyncio.fixture(scope="module")
async def iframe(captcha):
    yield await captcha.iframe()


class TestCaptcha:
    pytestmark = pytest.mark.asyncio

    async def test_iframe(self, iframe):
        assert iframe

    async def test_windowconf(self, shelper: IframeParser):
        assert shelper.conf

    async def test_match_md5(self, captcha: Captcha, shelper: IframeParser, iframe: str):
        ans, duration = await captcha.match_md5(iframe, shelper.conf.powCfg)
        assert ans <= 3e5
        assert duration > 0
        ans2, _ = await captcha.match_md5(iframe, shelper.conf.powCfg)
        assert ans == ans2

    async def test_puzzle(self, captcha: Captcha, shelper: IframeParser):
        j = Jigsaw(
            *await captcha.rio(shelper.cdn(i) for i in range(3)),
            top=floor(shelper.conf.spt),
        )
        assert j.width > 0

    async def test_verify(self, captcha: Captcha):
        r = await captcha.verify()
        assert r.randstr


@pytest_asyncio.fixture(scope="class")
async def vm(captcha: Captcha, iframe: str):
    yield await captcha.get_tdc_vm(iframe)


class TestVM:
    pytestmark = pytest.mark.asyncio

    async def testGetInfo(self, vm: TDC):
        d = await vm.get_info()
        assert d
        assert d["info"]

    async def testCollectData(self, vm: TDC):
        vm.set_data({"clientType": 2})
        vm.set_data({"coordinate": [10, 24, 0.4103]})
        vm.set_data(
            {"trycnt": 1, "refreshcnt": 0, "slideValue": Captcha.imitateDrag(230), "dragobj": 1}
        )
        vm.set_data({"ft": "qf_7P_n_H"})
        d = await vm.get_data()
        assert d
        assert len(d) > 200

    async def testGetCookie(self, vm: TDC):
        cookie = await vm.get_cookie()
        assert "TDC_itoken" in cookie

    @pytest.mark.needuser
    async def test_decrypt(self, captcha: Captcha, iframe: str):
        vm = await captcha.get_tdc_vm(iframe)
        vm.set_data({"clientType": 2})
        vm.set_data({"coordinate": [10, 24, 0.4103]})
        vm.set_data(
            {"trycnt": 1, "refreshcnt": 0, "slideValue": Captcha.imitateDrag(230), "dragobj": 1}
        )
        vm.set_data({"ft": "qf_7P_n_H"})
        collect = await vm.get_data()

        dec = await captcha.get_tdc_vm(iframe, cls=DecryptTDC)
        decrypt = await dec.decrypt(collect)
        assert decrypt
