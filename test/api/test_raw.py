import asyncio
from typing import Optional, Tuple

import pytest
import pytest_asyncio
from httpx import AsyncClient

from aioqzone.api.loginman import MixedLoginMan
from aioqzone.api.raw import QzoneApi
from aioqzone.exception import LoginError
from aioqzone.type.internal import LikeData
from aioqzone.utils import first
from aioqzone.utils.html import HtmlContent, HtmlInfo


@pytest.fixture(scope="module")
def storage():
    return []


@pytest_asyncio.fixture(scope="module")
async def api(sess: AsyncClient, man: MixedLoginMan):
    yield QzoneApi(sess, man)


class TestRaw:
    pytestmark = pytest.mark.asyncio

    async def test_more(self, api: QzoneApi, storage: list):
        future = asyncio.gather(*(api.feeds3_html_more(i) for i in range(3)))
        try:
            r = await future
        except LoginError:
            pytest.xfail("Login failed")
        for i in r:  # type: ignore
            assert isinstance(i["data"], list)
            storage.extend(i["data"])
        assert storage

    @pytest.mark.upstream
    async def test_complete(self, api: QzoneApi, storage: list):
        if not storage:
            pytest.skip("storage is empty")
        f: Optional[dict] = first(storage, None)
        assert f
        _, info = HtmlInfo.from_html(f["html"])
        d = await api.emotion_getcomments(f["uin"], f["key"], info.feedstype)
        assert "newFeedXML" in d

    async def test_detail(self, api: QzoneApi, storage: list):
        if not storage:
            pytest.skip("storage is empty")
        f: Optional[dict] = first(storage, lambda f: int(f["appid"]) == 311)
        if f is None:
            pytest.skip("No 311 feed in storage.")
        assert f
        await api.emotion_msgdetail(f["uin"], f["key"])

    async def test_heartbeat(self, api: QzoneApi):
        try:
            d = await api.get_feeds_count()
        except LoginError:
            pytest.skip("Login failed")
        assert d  # type: ignore
        assert isinstance(d.pop("newfeeds_uinlist", []), list)
        for k, v in d.items():
            assert isinstance(k, str)
            assert isinstance(v, int)

    async def test_like(self, api: QzoneApi, storage: list):
        if not storage:
            pytest.skip("storage is empty")
        f: Optional[Tuple[dict, HtmlInfo]] = first(
            ((i, HtmlInfo.from_html(i["html"])[1]) for i in storage), lambda t: t[1].unikey
        )
        if f is None:
            pytest.skip("No feed with unikey.")
        fd, info = f
        assert info.unikey
        ld = LikeData(
            unikey=str(info.unikey),
            curkey=str(info.curkey) or LikeData.persudo_curkey(fd["uin"], fd["abstime"]),
            appid=fd["appid"],
            typeid=fd["typeid"],
            fid=fd["key"],
            abstime=fd["abstime"],
        )

        assert await api.like_app(ld, not info.islike)
        assert await api.like_app(ld, bool(info.islike))

    async def test_photo_list(self, api: QzoneApi, storage: list):
        if not storage:
            pytest.skip("storage is empty")
        f: Optional[HtmlContent] = first(
            (HtmlContent.from_html(i["html"], i["uin"]) for i in storage), lambda t: t.pic
        )
        if f is None:
            pytest.skip("No feed with pic in storage")
        assert f
        assert f.album
        await api.floatview_photo_list(f.album, 10)

    @pytest.mark.upstream
    async def test_publish(self, api: QzoneApi, storage: list):
        try:
            r = await api.emotion_publish("Test")
        except LoginError:
            pytest.xfail("login failed")
        assert isinstance(r, dict)  # type: ignore
        assert r["tid"]
        storage.clear()
        storage.append(r)

    @pytest.mark.upstream
    async def test_delete(self, api: QzoneApi, storage: list):
        if not storage:
            pytest.skip("storage is empty")
        r = storage[-1]
        if not r:
            pytest.xfail("storage is empty")
        _, info = HtmlInfo.from_html(r["feedinfo"])
        r = await api.emotion_delete(r["tid"], r["now"], 311, 0, info.topicid)
