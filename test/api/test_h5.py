from os import environ as env

import pytest
import pytest_asyncio

from aioqzone.api.h5 import QzoneH5API
from aioqzone.api.h5.raw import QzoneH5RawAPI
from aioqzone.api.loginman import UPLoginMan
from aioqzone.event import UPEvent
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def h5(client: ClientAdapter):
    man = UPLoginMan(client, int(env["TEST_UIN"]), env["TEST_PASSWORD"], h5=True)
    man.register_hook(UPEvent())
    yield man


@pytest_asyncio.fixture(scope="class")
async def raw(client: ClientAdapter, h5: UPLoginMan):
    yield QzoneH5RawAPI(client, h5)


@pytest.fixture(scope="class")
def context():
    return {}


class TestH5RawAPI:
    async def test_index(self, raw: QzoneH5RawAPI, context: dict):
        d = await raw.index()
        if d["hasmore"]:
            context["attach_info"] = d["attachinfo"]

    async def test_more(self, raw: QzoneH5RawAPI, context: dict):
        if "attach_info" not in context:
            pytest.skip(msg="have youe run `test_index` before this test?")
        d = await raw.get_active_feeds(context["attach_info"])
        if d["hasmore"]:
            context["attach_info"] = d["attachinfo"]

    async def test_heartbeat(self, raw: QzoneH5RawAPI):
        d = await raw.mfeeds_get_count()
        assert "active_cnt" in d


@pytest_asyncio.fixture(scope="class")
async def api(client: ClientAdapter, h5: UPLoginMan):
    yield QzoneH5API(client, h5)


class TestH5API:
    async def test_index(self, api: QzoneH5API, context: dict):
        d = await api.index()
        if d.hasmore:
            context["attach_info"] = d.attachinfo

    async def test_more(self, api: QzoneH5API, context: dict):
        if "attach_info" not in context:
            pytest.skip(msg="have youe run `test_index` before this test?")
        d = await api.get_active_feeds(context["attach_info"])
        if d.hasmore:
            context["attach_info"] = d.attachinfo

    async def test_heartbeat(self, api: QzoneH5API):
        await api.mfeeds_get_count()
