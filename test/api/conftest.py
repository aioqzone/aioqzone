from __future__ import annotations

import io
from contextlib import suppress
from typing import TYPE_CHECKING

import pytest

from aioqzone.api.loginman import MixedLoginMan
from qqqr.utils.net import ClientAdapter

if TYPE_CHECKING:
    from test.conftest import test_env


@pytest.fixture(scope="module")
def man(client: ClientAdapter, env: test_env):
    man = MixedLoginMan(
        client,
        env.uin,
        env.order,  # forbid QR by default.
        pwd=env.pwd.get_secret_value(),
    )
    with suppress(ImportError):
        from PIL import Image as image

        man.qr_fetched.listeners.append(lambda m: image.open(io.BytesIO(m.png)).show())

    yield man
