import asyncio
from math import floor
from os import environ as env

from aiohttp import ClientSession
import pytest
import pytest_asyncio

from qqqr.constants import QzoneAppid
from qqqr.constants import QzoneProxy
from qqqr.up import UPLogin
from qqqr.up import User
from qqqr.up.captcha import Captcha
from qqqr.up.captcha import ScriptHelper
from qqqr.up.captcha import VM
from qqqr.up.captcha.jigsaw import Jigsaw


@pytest.fixture(scope="module")
def event_loop():
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
async def shelper(captcha, iframe):
    shelper = ScriptHelper(captcha.appid, captcha.sid, 2)
    shelper.parseCaptchaConf(iframe)
    yield shelper


@pytest_asyncio.fixture(scope="module")
async def iframe(captcha):
    yield await captcha.iframe()


class TestCaptcha:
    pytestmark = pytest.mark.asyncio

    async def test_iframe(self, iframe):
        assert iframe

    async def test_windowconf(self, shelper):
        assert shelper.conf
        assert shelper.conf["nonce"]
        assert shelper.conf["powCfg"]

    async def test_match_md5(self, captcha, shelper, iframe):
        ans, duration = await captcha.matchMd5(iframe, shelper.conf["powCfg"])
        assert ans <= 3e5
        assert duration > 0

    async def test_puzzle(self, captcha, shelper):
        j = Jigsaw(
            *await captcha.rio(shelper.cdn(i) for i in range(3)),
            top=floor(int(shelper.conf["spt"])),
        )
        assert j.width > 0

    async def test_verify(self, captcha: Captcha):
        r = await captcha.verify()
        assert r["randstr"]


@pytest_asyncio.fixture(scope="class")
async def vm(captcha, iframe):
    yield await captcha.getTdx(iframe)


class TestVM:
    # TODO: stucked?
    pytestmark = pytest.mark.asyncio

    async def testGetInfo(self, vm: VM):
        assert (d := await vm.getInfo())
        assert d["info"]

    async def testCollectData(self, vm: VM):
        vm.setData({"clientType": 2})
        vm.setData({"coordinate": [10, 24, 0.4103]})
        vm.setData(
            {"trycnt": 1, "refreshcnt": 0, "slideValue": Captcha.imitateDrag(230), "dragobj": 1}
        )
        vm.setData({"ft": "qf_7P_n_H"})
        assert (d := await vm.getData())
        assert len(d) > 200

    async def testGetCookie(self, vm: VM):
        assert await vm.getCookie()
