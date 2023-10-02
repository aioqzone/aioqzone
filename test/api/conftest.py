from __future__ import annotations

import io
from contextlib import suppress
from os import environ
from typing import TYPE_CHECKING

import pytest

from aioqzone.api import UpLoginConfig, UpLoginManager
from qqqr.utils.net import ClientAdapter

if TYPE_CHECKING:
    from test.conftest import test_env

loginman_list = ["up"]
if environ.get("CI") is None:
    loginman_list.append("qr")


@pytest.fixture(scope="module", params=loginman_list)
def man(request, client: ClientAdapter, env: test_env):
    if request.param == "up":
        return UpLoginManager(
            client,
            config=UpLoginConfig(uin=env.uin, pwd=env.password, min_login_interval=0),
        )

    if request.param == "qr":
        from aioqzone.api import QrLoginConfig, QrLoginManager

        man = QrLoginManager(client, config=QrLoginConfig(uin=env.uin))
        with suppress(ImportError):
            from PIL import Image as image

            man.qr_fetched.add_impl(lambda png, times: image.open(io.BytesIO(png)).show())

        return man
