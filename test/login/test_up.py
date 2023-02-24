from os import environ as env

import pytest
import pytest_asyncio

from qqqr.constant import QzoneAppid, QzoneProxy, StatusCode
from qqqr.exception import TencentLoginError
from qqqr.up import UpEvent, UpLogin
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def login(client: ClientAdapter):
    yield UpLogin(
        client,
        QzoneAppid,
        QzoneProxy,
        int(env["TEST_UIN"]),
        env["TEST_PASSWORD"],
    )


class TestRequest:
    @pytest.mark.needuser
    async def testRegisterSmsCodeGetter(self, login: UpLogin):
        class ntdin(UpEvent):
            async def GetSmsCode(self, phone: str, nickname: str):
                assert phone
                assert nickname
                with open("tmp/ntdin.txt") as f:
                    return int(f.readline().rstrip())

        login.register_hook(ntdin())

    async def testEncodePwd(self, login: UpLogin):
        sess = await login.new()
        if sess.code == StatusCode.NeedCaptcha:
            sess = await login.pass_vc(sess)
        if sess.code != 1:
            assert sess.verifycode
            assert sess.check_rst.salt
            p = await login.pwder.encode(sess.check_rst.salt, sess.verifycode)
            assert len(p) > 4

    async def testLogin(self, login: UpLogin):
        try:
            assert await login.login()
        except TencentLoginError as e:
            if e.code in [StatusCode.RiskyNetwork, StatusCode.ForceQR]:
                pytest.skip(str(e))
            elif (
                e.code == StatusCode.NeedSmsVerify
                and UpEvent.GetSmsCode.__name__ not in login.hook.__dict__
            ):
                pytest.skip(str(e))
            else:
                raise e
