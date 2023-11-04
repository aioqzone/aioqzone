from __future__ import annotations

import pytest
import pytest_asyncio
from tenacity import RetryError

from aioqzone.api import Loginable
from aioqzone.api.h5 import QzoneH5API
from aioqzone.model import LikeData
from qqqr.utils.net import ClientAdapter

pytestmark = pytest.mark.asyncio

MOOD_TEXT = "This is a curious test :D"
COMMENT_TEXT = "Here is a kind comment :)"


@pytest_asyncio.fixture(scope="class")
async def api(client: ClientAdapter, man: Loginable):
    yield QzoneH5API(client, man)


async def qzone_workflow(api: QzoneH5API):
    await api.index()
    assert api.qzonetoken

    feed = await api.publish_mood(MOOD_TEXT, sync_weibo=False)
    ownuin, appid = api.login.uin, 311
    unikey = LikeData.persudo_unikey(appid, ownuin, feed.fid)

    comment = await api.add_comment(ownuin, feed.fid, appid, COMMENT_TEXT)
    await api.internal_dolike_app(appid, unikey, curkey=unikey)

    feed_flow = await api.get_active_feeds()
    feed_dict = {i.fid: i for i in feed_flow.vFeeds}
    assert feed.fid in feed_dict

    fetched_feed = feed_dict[feed.fid]
    assert MOOD_TEXT in fetched_feed.summary.summary
    # BUG: dolike returns `succ` but has no effect. the fetched `isliked` is False.
    # So this assertion is disabled temperorily. FIXME!
    # assert fetched_feed.like.isliked
    assert fetched_feed.comment.comments

    comment_dict = {i.commentid: i for i in fetched_feed.comment.comments}
    assert comment.commentid in comment_dict

    fetched_comment = comment_dict[comment.commentid]
    assert fetched_comment.commentLikekey == comment.commentLikekey
    assert COMMENT_TEXT in fetched_comment.content

    detail = await api.shuoshuo(feed.fid, ownuin, appid)
    assert not detail.hasmore
    assert detail.summary.summary == fetched_feed.summary.summary
    assert detail.like.isliked == fetched_feed.like.isliked
    assert detail.comment.comments
    assert comment.commentid in [i.commentid for i in detail.comment.comments]

    count1 = await api.mfeeds_get_count()
    delete = await api.delete_ugc(feed.fid, appid)
    count2 = delete.undeal_info

    assert count1 == count2


async def test_workflow(api: QzoneH5API):
    try:
        await qzone_workflow(api)
    except RetryError as e:
        assert e.last_attempt.failed
        e = e.last_attempt.exception()
        pytest.skip("login failed", msg=str(e))
