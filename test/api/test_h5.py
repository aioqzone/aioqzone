from __future__ import annotations

import io
from contextlib import suppress
from os import environ

import pytest
import pytest_asyncio

from aioqzone.api import UnifiedLoginManager
from aioqzone.api.h5 import QzoneH5API
from aioqzone.api.h5.raw import QzoneH5RawAPI
from aioqzone.exception import LoginError
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio
skip_ci = pytest.mark.skipif(bool(environ.get("CI")), reason="Skip QR loop in CI")


@pytest_asyncio.fixture(scope="class")
async def raw(client: ClientAdapter, man: UnifiedLoginManager):
    yield QzoneH5RawAPI(client, man)


@pytest.fixture(scope="class")
def context():
    return {}


class TestH5RawAPI:
    async def test_index(self, raw: QzoneH5RawAPI, context: dict):
        try:
            d = await raw.index()
        except LoginError:
            pytest.skip("login failed")
        if d["hasmore"]:
            context["attach_info"] = d["attachinfo"]

    async def test_more(self, raw: QzoneH5RawAPI, context: dict):
        if "attach_info" not in context:
            pytest.skip("have youe run `test_index` before this test?")
        d = await raw.get_active_feeds(context["attach_info"])
        if d["hasmore"]:
            context["attach_info"] = d["attachinfo"]

    async def test_heartbeat(self, raw: QzoneH5RawAPI):
        try:
            d = await raw.mfeeds_get_count()
        except LoginError:
            pytest.skip("login failed")
        assert "active_cnt" in d


@pytest_asyncio.fixture(scope="class")
async def api(client: ClientAdapter, man: UnifiedLoginManager):
    yield QzoneH5API(client, man)


class TestH5API:
    async def test_index(self, api: QzoneH5API, context: dict):
        try:
            d = await api.index()
        except LoginError:
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
        except LoginError:
            pytest.skip("login failed")


@skip_ci
async def test_h5_qr_login(client: ClientAdapter, man: UnifiedLoginManager):
    man.order = ["qr"]
    api = QzoneH5API(client, man)

    with suppress(ImportError):
        from PIL import Image as image

        man.qr_fetched.add_impl(lambda png, times: image.open(io.BytesIO(png)).show())

    d = await api.mfeeds_get_count()
    print(d.active_cnt)
