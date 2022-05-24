import asyncio

import pytest
import pytest_asyncio
from aiohttp import ClientSession

from aioqzone.api.loginman import MixedLoginMan, QrStrategy
from aioqzone.interface.hook import QREvent, UPEvent

from . import showqr


@pytest.fixture(scope="module")
def event_loop():
    import jssupport.execjs  # set policy

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def sess():
    async with ClientSession() as sess:
        yield sess


@pytest_asyncio.fixture(scope="module")
async def man(sess: ClientSession):
    from os import environ as env

    man = MixedLoginMan(
        sess,
        int(env["TEST_UIN"]),
        QrStrategy[env.get("TEST_QRSTRATEGY", "forbid")],  # forbid QR by default.
        pwd=env.get("TEST_PASSWORD", None),
    )

    class mixed_event(QREvent, UPEvent):
        async def QrFetched(self, png: bytes):
            showqr(png)

    man.register_hook(mixed_event())
    yield man
