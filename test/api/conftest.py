from __future__ import annotations

import io
from typing import TYPE_CHECKING, Type

import pytest

from aioqzone.api.loginman import MixedLoginMan
from aioqzone.event import QREvent
from qqqr.event import sub_of
from qqqr.utils.net import ClientAdapter

if TYPE_CHECKING:
    from test.conftest import test_env


@pytest.fixture(scope="module")
def man(client: ClientAdapter, env: test_env):
    try:
        from PIL import Image as image
    except ImportError:
        cls = MixedLoginMan
    else:

        class show_qr_in_test(MixedLoginMan):
            @sub_of(QREvent)
            def _sub_qrevent(_self, base: Type[QREvent]):
                class showqr_qrevent(base):
                    async def QrFetched(self, png: bytes, times: int):
                        image.open(io.BytesIO(png)).show()

                return showqr_qrevent

        cls = show_qr_in_test

    man = cls(
        client,
        env.uin,
        env.order,  # forbid QR by default.
        pwd=env.pwd.get_secret_value(),
    )

    yield man
