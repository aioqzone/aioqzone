import asyncio
from typing import List, Optional, Tuple

import pytest
import pytest_asyncio
from httpx import HTTPStatusError

from aioqzone.api import QzoneWebAPI
from aioqzone.api.loginman import MixedLoginMan
from aioqzone.api.web.raw import QzoneWebRawAPI
from aioqzone.exception import LoginError, QzoneError
from aioqzone.type.internal import LikeData
from aioqzone.type.resp import FeedRep
from aioqzone.utils.html import HtmlContent, HtmlInfo
from qqqr.utils.iter import first
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="class")
def storage():
    return []


@pytest_asyncio.fixture(scope="module")
async def raw(client: ClientAdapter, man: MixedLoginMan):
    yield QzoneWebRawAPI(client, man)


class TestWebRawAPI:
    async def test_more(self, raw: QzoneWebRawAPI, storage: list):
        try:
            f = await raw.feeds3_html_more(0)
            r = await asyncio.gather(*(raw.feeds3_html_more(i) for i in range(1, 3)))
        except LoginError:
            pytest.xfail("Login failed")
        for i in [f] + list(r):
            assert isinstance(i["data"], list)
            storage.extend(i["data"])
        assert storage

    @pytest.mark.skip("this test fails by chance for upstream reason")
    async def test_complete(self, raw: QzoneWebRawAPI, storage: list):
        if not storage:
            pytest.skip("storage is empty")
        f: Optional[dict] = first(storage, default=None)
        assert f
        _, info = HtmlInfo.from_html(f["html"])
        d = await raw.emotion_getcomments(f["uin"], f["key"], info.feedstype)
        assert "newFeedXML" in d

    async def test_detail(self, raw: QzoneWebRawAPI, storage: list):
        if not storage:
            pytest.skip("storage is empty")
        f: Optional[dict] = first(storage, lambda f: int(f["appid"]) == 311, default=None)
        if f is None:
            pytest.skip("No 311 feed in storage.")
        assert f
        await raw.emotion_msgdetail(f["uin"], f["key"])

    async def test_heartbeat(self, raw: QzoneWebRawAPI):
        try:
            d = await raw.get_feeds_count()
        except LoginError:
            pytest.skip("Login failed")
        assert d  # type: ignore
        assert isinstance(d.pop("newfeeds_uinlist", []), list)
        for k, v in d.items():
            assert isinstance(k, str)
            assert isinstance(v, int)

    async def test_like(self, raw: QzoneWebRawAPI, storage: list):
        if not storage:
            pytest.skip("storage is empty")
        f: Optional[Tuple[dict, HtmlInfo]] = first(
            ((i, HtmlInfo.from_html(i["html"])[1]) for i in storage),
            lambda t: t[1].unikey,
            default=None,
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

        assert await raw.like_app(ld, not info.islike)
        assert await raw.like_app(ld, bool(info.islike))

    async def test_photo_list(self, raw: QzoneWebRawAPI, storage: list):
        if not storage:
            pytest.skip("storage is empty")
        f: Optional[HtmlContent] = first(
            (HtmlContent.from_html(i["html"], i["uin"]) for i in storage),
            lambda t: t.pic,
            default=None,
        )
        if f is None:
            pytest.skip("No feed with pic in storage")
        assert f
        assert f.album
        await raw.floatview_photo_list(f.album, 10)


@pytest_asyncio.fixture(scope="class")
async def published(raw: QzoneWebRawAPI):
    try:
        r = await raw.emotion_publish("Test")
    except LoginError:
        return
    assert isinstance(r, dict)
    assert r["tid"]
    return r


@pytest.mark.skip("these tests fails by chance for upstream reason")
class TestUpload:
    async def test_publish(self, published: Optional[dict]):
        if published is None:
            pytest.xfail("login failed")
            # should fail this entire class

    async def test_comment(self, raw: QzoneWebRawAPI, published: Optional[dict]):
        if published is None:
            pytest.skip("login failed")
        _, info = HtmlInfo.from_html(published["feedinfo"])
        r = await raw.emotion_re_feeds("comment", info.topicid, 0, raw.login.uin)
        assert isinstance(r, str)

    async def test_delete(self, raw: QzoneWebRawAPI, published: Optional[dict]):
        if published is None:
            pytest.skip("login failed")
        _, info = HtmlInfo.from_html(published["feedinfo"])
        r = await raw.emotion_delete(published["tid"], published["now"], 311, 0, info.topicid)
        assert r


@pytest_asyncio.fixture(scope="class")
async def api(client: ClientAdapter, man: MixedLoginMan):
    yield QzoneWebAPI(client, man)


class TestWebAPI:
    async def test_heartbeat(self, api: QzoneWebAPI):
        try:
            assert await api.get_feeds_count()
        except LoginError:
            pytest.xfail("Login failed")

    async def test_more(self, api: QzoneWebAPI, storage: list):
        try:
            f = await api.feeds3_html_more(0)
            r = await asyncio.gather(*(api.feeds3_html_more(i) for i in range(1, 3)))
        except LoginError:
            pytest.xfail("Login failed")
        for i in [f] + list(r):
            assert isinstance(i.feeds, list)
            assert i.aux.dayspac >= 0
            storage.extend(i.feeds)
        assert storage

    @pytest.mark.skip("this test fails by chance for upstream reason")
    async def test_complete(self, api: QzoneWebAPI, storage: List[FeedRep]):
        if not storage:
            pytest.xfail("storage is empty")
        f: Optional[FeedRep] = first(storage, default=None)
        assert f
        from aioqzone.utils.html import HtmlInfo

        _, info = HtmlInfo.from_html(f.html)
        assert await api.emotion_getcomments(f.uin, f.fid, info.feedstype)

    async def test_detail(self, api: QzoneWebAPI, storage: List[FeedRep]):
        if not storage:
            pytest.xfail("storage is empty")
        for f in storage:
            try:
                assert await api.emotion_msgdetail(f.uin, f.fid)
            except (QzoneError, HTTPStatusError) as e:
                continue

    async def test_photo_list(self, api: QzoneWebAPI, storage: List[FeedRep]):
        if not storage:
            pytest.xfail("storage is empty")
        f: Optional[HtmlContent] = first(
            (HtmlContent.from_html(i.html, i.uin) for i in storage),
            lambda t: bool(t.pic),
            default=None,
        )
        if f is None:
            pytest.skip("No feed with pic in storage")
        assert f
        assert f.album
        await api.floatview_photo_list(f.album, 10)
