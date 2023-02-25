from os import environ as env

import pytest
import pytest_asyncio

from qqqr.constant import StatusCode
from qqqr.exception import TencentLoginError
from qqqr.up import UpEvent, UpH5Login, UpWebLogin
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def web(client: ClientAdapter):
    from qqqr.constant import QzoneAppid, QzoneProxy

    yield UpWebLogin(
        client,
        QzoneAppid,
        QzoneProxy,
        int(env["TEST_UIN"]),
        env["TEST_PASSWORD"],
    )


class TestUpWeb:
    @pytest.mark.needuser
    async def testRegisterSmsCodeGetter(self, web: UpWebLogin):
        class ntdin(UpEvent):
            async def GetSmsCode(self, phone: str, nickname: str):
                assert phone
                assert nickname
                with open("tmp/ntdin.txt") as f:
                    return int(f.readline().rstrip())

        web.register_hook(ntdin())

    async def test_encode_password(self, web: UpWebLogin):
        sess = await web.new()
        if sess.code == StatusCode.NeedCaptcha:
            sess = await web.pass_vc(sess)
        if sess.code != 1:
            assert sess.verifycode
            assert sess.check_rst.salt
            p = await web.pwder.encode(sess.check_rst.salt, sess.verifycode)
            assert len(p) > 4

    async def test_login(self, web: UpWebLogin):
        try:
            assert await web.login()
        except TencentLoginError as e:
            if e.code in [StatusCode.RiskyNetwork, StatusCode.ForceQR]:
                pytest.skip(str(e))
            elif (
                e.code == StatusCode.NeedSmsVerify
                and UpEvent.GetSmsCode.__name__ not in web.hook.__dict__
            ):
                pytest.skip(str(e))
            else:
                raise e


@pytest.fixture
def h5(client: ClientAdapter):
    from qqqr.constant import QzoneH5Appid, QzoneH5Proxy

    yield UpH5Login(
        client,
        QzoneH5Appid,
        QzoneH5Proxy,
        int(env["TEST_UIN"]),
        env["TEST_PASSWORD"],
    )


async def test_h5_login(h5: UpH5Login):
    try:
        assert await h5.login()
    except TencentLoginError as e:
        if e.code in [StatusCode.RiskyNetwork, StatusCode.ForceQR]:
            pytest.skip(str(e))
        elif (
            e.code == StatusCode.NeedSmsVerify
            and UpEvent.GetSmsCode.__name__ not in web.hook.__dict__
        ):
            pytest.skip(str(e))
        else:
            raise e
