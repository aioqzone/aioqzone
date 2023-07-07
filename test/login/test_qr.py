import io

import pytest
import pytest_asyncio

from qqqr.constant import QzoneAppid, QzoneProxy, StatusCode
from qqqr.event.login import QrEvent
from qqqr.exception import HookError
from qqqr.qr import QrLogin, QrSession
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def login(client: ClientAdapter):
    login = QrLogin(client, QzoneAppid, QzoneProxy)
    hook = QrEvent()

    try:
        from PIL import Image as image
    except ImportError:
        pass
    else:

        async def __qr_fetched(png: bytes, times: int):
            image.open(io.BytesIO(png)).show()
            assert isinstance(times, int)

        hook.QrFetched = __qr_fetched

    login.register_hook(hook)
    yield login


@pytest.fixture
def trouble_hook(client: ClientAdapter):
    login = QrLogin(client, QzoneAppid, QzoneProxy)

    class trouble(QrEvent):
        def QrFetched(self, png: bytes, times: int):
            raise RuntimeError

    login.register_hook(trouble())
    yield login


@pytest_asyncio.fixture(scope="class")
async def qrsess(login: QrLogin):
    yield await login.new()


class TestProcedure:
    async def test_new(self, qrsess: QrSession):
        assert isinstance(qrsess.current_qr.sig, str)

    async def test_poll(self, login: QrLogin, qrsess: QrSession):
        poll = await login.poll(qrsess)
        assert poll
        assert poll.code == StatusCode.Waiting

    async def test_guard(self, trouble_hook: QrLogin):
        with pytest.raises(HookError):
            cookie = await trouble_hook.login()


@pytest.mark.skip("this test should be called manually")
async def test_loop(login: QrLogin):
    cookie = await login.login()
    assert cookie["p_skey"]
