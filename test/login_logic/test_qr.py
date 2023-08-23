import asyncio
import io
from contextlib import suppress
from os import environ

import pytest
import pytest_asyncio
from tylisten import Emitter

import qqqr.message as MT
from qqqr.constant import StatusCode
from qqqr.exception import UserBreak
from qqqr.qr import QrLogin, QrSession
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio
skip_ci = pytest.mark.skipif(bool(environ.get("CI")), reason="Skip QR loop in CI")


@pytest_asyncio.fixture(scope="class")
async def login(client: ClientAdapter):
    login = QrLogin(client)

    with suppress(ImportError):
        from PIL import Image as image

        login.qr_fetched.listeners.append(lambda m: image.open(io.BytesIO(m.png)).show())

    yield login


@pytest_asyncio.fixture(scope="class")
async def qrsess(login: QrLogin):
    yield await login.new()


class TestSession:
    async def test_new(self, qrsess: QrSession):
        assert isinstance(qrsess.current_qr.sig, str)

    async def test_poll(self, login: QrLogin, qrsess: QrSession):
        poll = await login.poll(qrsess)
        assert poll
        assert poll.code == StatusCode.Waiting


class TestLoop:
    @skip_ci
    async def test_loop(self, login: QrLogin):
        cookie = await login.login()
        assert cookie["p_skey"]

    async def test_resend_cancel(self, client: ClientAdapter, login: QrLogin):
        hist = []
        refresh_emitter = Emitter(MT.qr_refresh)
        cancel_emitter = Emitter(MT.qr_cancelled)
        login.qr_cancelled.listeners.append(lambda _: hist.append("cancel"))

        login.cancel.connect(cancel_emitter)
        login.refresh.connect(refresh_emitter)

        async def __qr_fetched(m: MT.qr_fetched):
            hist.append(m.png)
            if len(hist) == 1:
                await refresh_emitter.emit()
            elif len(hist) == 2:
                await cancel_emitter.emit()

        login.qr_fetched.listeners.clear()
        login.qr_fetched.listeners.append(__qr_fetched)
        with pytest.raises(UserBreak):
            await asyncio.wait_for(login.login(), timeout=3)

        assert len(hist) == 3
        assert hist[-1] == "cancel"
        assert isinstance(hist[0], bytes)
        assert isinstance(hist[1], bytes)
        assert hist[0] != hist[1]