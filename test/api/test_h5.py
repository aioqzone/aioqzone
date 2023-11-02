from __future__ import annotations

import io
from contextlib import suppress
from os import environ

import pytest
import pytest_asyncio
from tenacity import RetryError

from aioqzone.api import Loginable
from aioqzone.api.h5 import QzoneH5API
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio
skip_ci = pytest.mark.skipif(bool(environ.get("CI")), reason="Skip QR loop in CI")


@pytest.fixture(scope="class")
def context():
    return {}


@pytest_asyncio.fixture(scope="class")
async def api(client: ClientAdapter, man: Loginable):
    yield QzoneH5API(client, man)


class TestH5API:
    async def test_index(self, api: QzoneH5API, context: dict):
        try:
            d = await api.index()
        except RetryError:
            pytest.skip("login failed")
        context["first_page"] = d.vFeeds
        if d.hasmore:
            context["attach_info"] = d.attachinfo

    async def test_more(self, api: QzoneH5API, context: dict):
        if "attach_info" not in context:
            pytest.skip("have youe run `test_index` before this test?")
        d = await api.get_active_feeds(context["attach_info"])
        if d.hasmore:
            context["attach_info"] = d.attachinfo

    async def test_detail(self, api: QzoneH5API, context: dict):
        if "first_page" not in context:
            pytest.skip("have you run `test_index` before this test?")
        first_page = context["first_page"]

        f = next(filter(lambda d: d.common.appid == 311, first_page), None)
        if f is None:
            pytest.skip("no 311 feed in first page")

        d = await api.shuoshuo(f.fid, f.userinfo.uin, f.common.appid)
        assert len(d.summary.summary) >= len(f.summary.summary)

    async def test_heartbeat(self, api: QzoneH5API):
        try:
            await api.mfeeds_get_count()
        except RetryError:
            pytest.skip("login failed")
