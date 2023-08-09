import asyncio
from typing import List

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from aioqzone._messages import LoginMethod
from qqqr.utils.net import ClientAdapter


class test_env(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="test_")
    uin: int = 0
    pwd: SecretStr = Field(default="")
    order: List[LoginMethod] = ["qr"]


@pytest.fixture(scope="session")
def env():
    return test_env()


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
