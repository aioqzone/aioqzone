from typing import List

import pytest
from pydantic import BaseSettings, Field, SecretStr, root_validator
from pydantic.env_settings import SettingsSourceCallable

from aioqzone.api.loginman import LoginMethod, strategy_to_order


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
