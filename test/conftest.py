import asyncio
from typing import List

import pytest
import pytest_asyncio
from httpx import AsyncClient
from pydantic import BaseSettings, Field, SecretStr, root_validator
from pydantic.env_settings import SettingsSourceCallable

from aioqzone.api.loginman import LoginMethod, strategy_to_order
from qqqr.ssl import ssl_context
from qqqr.utils.net import ClientAdapter


class test_env(BaseSettings):
    uin: int = Field(env="TEST_UIN")
    pwd: SecretStr = Field(env="TEST_PASSWORD")
    order: List[LoginMethod] = Field(env="TEST_QRSTRATEGY")

    @root_validator(pre=True)
    def strategy_to_order(cls, v: dict):
        v["order"] = strategy_to_order[v.get("order", "forbid")]
        return v

    class Config:
        @classmethod
        def customise_sources(
            cls,
            init_settings: SettingsSourceCallable,
            env_settings: SettingsSourceCallable,
            file_secret_settings: SettingsSourceCallable,
        ):
            return (env_settings,)


@pytest.fixture(scope="session")
def env():
    return test_env()  # type: ignore


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="module")
async def client():
    async with AsyncClient(verify=ssl_context()) as client:
        client = ClientAdapter(client)
        yield client
