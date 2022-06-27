import asyncio

import pytest
import pytest_asyncio
from httpx import AsyncClient

from qqqr.constant import UA
from qqqr.ssl import ssl_context
from qqqr.utils.net import ClientAdapter


@pytest.fixture(scope="module")
def event_loop():
    import jssupport.execjs  # set policy

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(verify=ssl_context()) as client:
        client = ClientAdapter(client)
        client.ua = UA
        yield client
