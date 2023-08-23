from __future__ import annotations

import io
from contextlib import suppress
from os import environ
from typing import TYPE_CHECKING

import pytest

from aioqzone.api import QrLoginConfig, UnifiedLoginManager, UpLoginConfig
from qqqr.utils.net import ClientAdapter

if TYPE_CHECKING:
    from test.conftest import test_env


@pytest.fixture(scope="module")
def man(client: ClientAdapter, env: test_env):
    man = UnifiedLoginManager(
        client,
        up_config=UpLoginConfig(uin=env.uin, pwd=env.password, min_login_interval=0),
        qr_config=QrLoginConfig(uin=env.uin),
    )
    man.order = env.order

    if environ.get("CI"):
        yield man
        return

    with suppress(ImportError):
        from PIL import Image as image

        man.qr_fetched.listeners.append(lambda m: image.open(io.BytesIO(m.png)).show())

    yield man
