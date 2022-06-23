import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient

from aioqzone.api.loginman import MixedLoginEvent, MixedLoginMan, QrStrategy
from qqqr.ssl import ssl_context
from qqqr.utils.net import ClientAdapter

from . import showqr


@pytest.fixture(scope="module")
def event_loop():
    import jssupport.execjs  # set policy

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(verify=ssl_context()) as client:
        yield ClientAdapter(client)


@pytest_asyncio.fixture(scope="module")
async def man(client: ClientAdapter):
    from os import environ as env

    man = MixedLoginMan(
        client,
        int(env["TEST_UIN"]),
        QrStrategy[env.get("TEST_QRSTRATEGY", "forbid")],  # forbid QR by default.
        pwd=env.get("TEST_PASSWORD", None),
    )

    class mixed_event(MixedLoginEvent):
        def __init__(self) -> None:
            super().__init__()
            self._cancel = asyncio.Event()
            self._refresh = asyncio.Event()

        async def QrFetched(self, png: bytes, times: int):
            showqr(png)

        @property
        def cancel_flag(self) -> asyncio.Event:
            return self._cancel

        @property
        def refresh_flag(self) -> asyncio.Event:
            return self._refresh

    man.register_hook(mixed_event())
    yield man
