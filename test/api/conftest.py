from __future__ import annotations

from typing import TYPE_CHECKING, Type

import pytest

from aioqzone.api.loginman import MixedLoginMan
from aioqzone.event import QREvent
from qqqr.event import sub_of
from qqqr.utils.net import ClientAdapter

from . import showqr

if TYPE_CHECKING:
    from test.conftest import test_env


@pytest.fixture(scope="module")
def man(client: ClientAdapter, env: test_env):
    class show_qr_in_test(MixedLoginMan):
        @sub_of(QREvent)
        def _sub_qrevent(_self, base: Type[QREvent]):
            class showqr_qrevent(base):
                async def QrFetched(self, png: bytes, times: int):
                    showqr(png)

            return showqr_qrevent

    man = show_qr_in_test(
        client,
        env.uin,
        env.order,  # forbid QR by default.
        pwd=env.pwd.get_secret_value(),
    )

    yield man
