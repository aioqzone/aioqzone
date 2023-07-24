import asyncio
from os import environ
from typing import List

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pydantic import BaseModel, SecretStr

from aioqzone._messages import LoginMethod
from qqqr.utils.net import ClientAdapter


class test_env(BaseModel):
    uin: int
    pwd: SecretStr
    order: List[LoginMethod]


@pytest.fixture(scope="session")
def env():
    d = dict(
        uin=environ["TEST_UIN"],
        pwd=environ["TEST_PASSWORD"],
        order=environ.get("TEST_QRSTRATEGY", ["up"]),
    )
    return test_env.model_validate(d)


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient() as client:
        client = ClientAdapter(client)
        yield client
