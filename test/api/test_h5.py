from __future__ import annotations

import io
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from aioqzone.api.h5 import QzoneH5API
from aioqzone.api.h5.raw import QzoneH5RawAPI
from aioqzone.api.loginman import UPLoginMan
from aioqzone.event import UPEvent
from qqqr.exception import TencentLoginError

if TYPE_CHECKING:
    from test.conftest import test_env

    from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def h5(client: ClientAdapter, env: test_env):
    man = UPLoginMan(client, env.uin, env.pwd.get_secret_value(), h5=True)
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
        try:
            d = await raw.index()
        except TencentLoginError:
            pytest.xfail("login failed")
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
        except TencentLoginError:
            pytest.xfail("login failed")
        assert "active_cnt" in d


@pytest_asyncio.fixture(scope="class")
async def api(client: ClientAdapter, h5: UPLoginMan):
    yield QzoneH5API(client, h5)


class TestH5API:
    async def test_index(self, api: QzoneH5API, context: dict):
        try:
            d = await api.index()
        except TencentLoginError:
            pytest.xfail("login failed")
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
        except TencentLoginError:
            pytest.xfail("login failed")


@pytest.mark.skip("this test should be called manually")
async def test_h5_up_login(client: ClientAdapter, env: test_env):
    from aioqzone.api.loginman import QREvent, QRLoginMan

    man = QRLoginMan(client, env.uin, h5=True)
    api = QzoneH5API(client, man)

    hook = QREvent()

    try:
        from PIL import Image as image
    except ImportError:
        pass
    else:

        async def __qr_fetched(png, times):
            image.open(io.BytesIO(png)).show()

        hook.QrFetched = __qr_fetched
    man.register_hook(hook)

    d = await api.mfeeds_get_count()
    print(d.active_cnt)
