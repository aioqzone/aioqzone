import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient

from qqqr.constant import QzoneAppid, QzoneProxy, StatusCode
from qqqr.event.login import QrEvent
from qqqr.qr import QrLogin, QrSession

from . import showqr as _showqr

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture(scope="module")
async def login(sess: AsyncClient):
    login = QrLogin(sess, QzoneAppid, QzoneProxy)

    class showqr2user(QrEvent):
        def __init__(self) -> None:
            super().__init__()
            self._cancel = asyncio.Event()
            self._refresh = asyncio.Event()

        def QrFetched(self, png: bytes, times: int):
            _showqr(png)
            assert isinstance(times, int)

        @property
        def cancel_flag(self) -> asyncio.Event:
            return self._cancel

        @property
        def refresh_flag(self) -> asyncio.Event:
            return self._refresh

    login.register_hook(showqr2user())
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


@pytest.mark.needuser
async def test_loop(login: QrLogin):
    cookie = await login.login()
    assert cookie["p_skey"]
