"""
Basic wrapper of Qzone HTTP interface.
"""

import logging
from functools import wraps
from random import randint, random
from typing import Any, Callable
from urllib.parse import parse_qs, quote, unquote

import aioqzone.api.constant as const
from aiohttp import ClientSession as Session
from aiohttp.client_exceptions import ClientResponseError
from jssupport.jsjson import json_loads
from pydantic import BaseModel

from ..exception import QzoneError
from ..interface.login import Loginable
from ..type import LikeData
from ..utils.regex import response_callback
from ..utils.time import time_ms

logger = logging.getLogger(__name__)


class QzoneApi:
    """A wrapper for Qzone http interface.
    """
    encoding = 'utf-8'
    host = "https://user.qzone.qq.com"

    def __init__(self, session: Session, loginman: Loginable) -> None:
        self.sess = session
        self.login = loginman

    async def _get_gtk(self):
        """Get gtk with async-lock.

        Raises:
            QzoneError: if gtk is 0

        Returns:
            int: gtk != 0
        """
        async with self.login.lock:
            gtk = self.login.gtk
        if gtk == 0: raise QzoneError(-3000)
        return gtk

    async def aget(self, url: str, params: dict[str, str] = None):
        params = params or {}
        params = params | {'g_tk': str(await self._get_gtk())}
        return self.sess.get(self.host + url, params=params)

    async def apost(self, url: str, params: dict[str, str] = None, data: dict = None):
        params = params or {}
        params = params | {'g_tk': str(await self._get_gtk())}
        return self.sess.get(self.host + url, params=params, data=data)

    def _relogin_retry(self, func: Callable):
        """A decorator which will relogin and retry given func if cookie expired.

        'cookie expired' is indicated by:
        1. QzoneError code -3000 or -4002
        2. HTTP response code 403

        NOTE: Decorate code as less as possible; Do NOT modify args in the wrapped code.
        """
        @wraps(func)
        async def relogin_wrapper(*args, **kwds):
            try:
                return await func(*args, **kwds)
            except QzoneError as e:
                if e.code not in [-3000, -4002]: raise e
            except ClientResponseError as e:
                if e.status != 403: raise e

            logger.info(f'Cookie expire in {func.__name__}. Relogin...')
            await self.login.new_cookie()
            return await func(*args, **kwds)

        return relogin_wrapper

    def _rtext_handler(
        self,
        rtext: str,
        cb: bool = True,
        errno: Callable[[dict], int] = None,
        msg: Callable[[dict], str] = None
    ) -> dict[str, Any]:
        """Deal with rtext from Qzone api response, returns parsed json dict.
        Inner used only.

        Args:
            rtext (str): response.text()
            cb (bool, optional): The text is to be parsed by callback_regex. Defaults to True.
            errno (callable[[dict], int], optional): Error # getter. Defaults to get `code` field of the dict.
            msg (callable[[dict], str], optional): Error message getter. Defaults to None.

        Raises:
            QzoneError: if errno != 0

        Returns:
            dict: json response
        """
        if cb:
            match = response_callback.search(rtext)
            assert match
            rtext = match.group(1)
        r = json_loads(rtext)
        assert isinstance(r, dict)
        errno = errno or (lambda d: int(d['code']))

        if (err := errno(r)) != 0:
            if msg: raise QzoneError(err, msg(r), rdict=r)
            else: raise QzoneError(err, rdict=r)
        return r    # type: ignore

    class FeedsMoreTransaction:
        def __init__(self, default: dict[int, str] = None) -> None:
            self.extern = default or {}

        def parse(self, page: int):
            unquoted = self.extern.get(page, 'undefined')
            if unquoted == "undefined": return {}
            return {k: v[-1] for k, v in parse_qs(unquoted, keep_blank_values=True).items()}

    async def feeds3_html_more(
        self, pagenum: int, trans: FeedsMoreTransaction = None, count: int = 10
    ):
        """return a list of dict, each dict reps a page of feeds.

        Args:
            pagenum (int): #page >= 0
            trans: reps a skim transaction. Mutable.
            count: feed count

        Raises:
            `ClientResponseError`
            `QzoneError`
        """
        default = {
            'scope': 0,
            'view': 1,
            'daylist': '',
            'uinlist': '',
            'gid': '',
            'flag': 1,
            'filter': 'all',
            'applist': 'all',
            'refresh': 0,
            'aisortEndTime': 0,
            'aisortOffset': 0,
            'getAisort': 0,
            'aisortBeginTime': 0,
            'firstGetGroup': 0,
            'icServerTime': 0,
            'mixnocache': 0,
            'scene': 0,
            'dayspac': 'undefined',
            'sidomain': 'qzonestyle.gtimg.cn',
            'useutf8': 1,
            'outputhtmlfeed': 1,
        }
        trans = trans or self.FeedsMoreTransaction()
        query = {
            'rd': random(),
            'uin': self.login.uin,
            'pagenum': pagenum + 1,
            'begintime': trans.parse(pagenum).get("basetime", "undefined"),
            'count': count,
            'usertime': time_ms(),
            'externparam': quote(trans.extern.get(pagenum, 'undefined'))
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.aget(const.feeds3_html_more, default | query) as r:
                r.raise_for_status()
                rtext = await r.text(encoding=self.encoding)

            return self._rtext_handler(rtext, msg=lambda d: d['message'])

        r = await retry_closure()
        data: dict[str, Any] = r['data']
        trans.extern[pagenum + 1] = unquote(data['main']["externparam"])
        return data

    async def emotion_getcomments(self, uin: int, tid: str, feedstype: int):
        """Get complete html of a given feed

        Args:
            uin (int):
            tid (str):
            feedstype (int):

        Returns:
            str: complete feed html

        Raises:
            `ClientResponseError`
            `QzoneError`
        """
        default = {
            "pos": 0,
            "num": 1,
            "cmtnum": 1,
            "t1_source": 1,
            "who": 1,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "plat": "qzone",
            "source": "ic",
            "paramstr": 1,
            "fullContent": 1,
        }
        body = {
            "uin": uin,
            "tid": tid,
            "feedsType": feedstype,
            "qzreferrer": f"https://user.qzone.qq.com/{self.login.uin}",
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.apost(const.emotion_getcomments, default | body) as r:
                r.raise_for_status()
                rtext = await r.text(encoding=self.encoding)

            return self._rtext_handler(rtext, errno=lambda d: int(d['err']))

        return await retry_closure()

    async def emotion_msgdetail(self, owner: int, fid: str):
        """Get detail of a given msg.
        NOTE: share msg is not support, i.e. `appid=311`

        Args:
            owner (int): owner uin
            fid (str): feed id, named fid, tid or feedkey

        Returns:
            dict: a dict reps the feed in detail

        Raises:
            `ClientResponseError`
            `QzoneError`
        """
        default = {
            't1_source': 1,
            'ftype': 0,
            'sort': 0,
            'pos': 0,
            'num': 20,
            'callback': 'callback',
            'code_version': 1,
            'format': 'jsonp',
            'need_private_comment': 1,
        }
        query = {'uin': owner, 'tid': fid}

        @self._relogin_retry
        async def retry_closure():
            async with await self.aget(const.emotion_msgdetail, params=default | query) as r:
                r.raise_for_status()
                rtext = await r.text(encoding=self.encoding)

            return self._rtext_handler(rtext, msg=lambda d: d['message'])

        return await retry_closure()

    async def get_feeds_count(self) -> dict[str, int]:
        """Get feeds update count (new feeds, new photos, new comments, etc)
        NOTE: This api is also the 'keep-alive' signal to avoid cookie from expiring.
        Call this api every 300s can help keep cookie alive.

        Returns:
            dict[str, int]: dict of all kinds of updates

        Raises:
            `ClientResponseError`
            `QzoneError`
        """
        query = {'uin': self.login.uin, 'rd': random()}

        @self._relogin_retry
        async def retry_closure():
            async with await self.aget(const.get_feeds_count, query) as r:
                r.raise_for_status()
                rtext = await r.text(encoding=self.encoding)

            return self._rtext_handler(rtext, msg=lambda d: d['message'])

        r = await retry_closure()
        return r['data']

    async def like_app(self, likedata: LikeData, like: bool = True):
        """Like or unlike a feed.

        Args:
            likedata (LikeData): Necessary data for like/unlike
            like (bool, optional): True as like, False as unlike. Defaults to True.

        Returns:
            bool: if success

        @noexcept
        """
        default = {
            'from': 1,
            'active': 0,
            'fupdate': 1,
        }
        body = {
            'qzreferrer': f'https://user.qzone.qq.com/{self.login.uin}',
            'opuin': self.login.uin,
            'unikey': likedata.unikey,
            'curkey': likedata.curkey,
            'appid': likedata.appid,
            'typeid': likedata.typeid,
            'fid': likedata.fid
        }
        url = const.internal_dolike_app if like else const.internal_unlike_app

        @self._relogin_retry
        async def retry_closure():
            async with await self.apost(url, data=default | body) as r:
                r.raise_for_status()
                rtext = await r.text(encoding=self.encoding)
            return self._rtext_handler(rtext, msg=lambda d: d['message'])

        try:
            return bool(await retry_closure())
        except:
            logger.error('Error in dolike/unlike.', exc_info=True)
            return False

    class AlbumData(BaseModel):
        topicid: str
        pickey: str
        hostuin: int

    async def floatview_photo_list(self, album: AlbumData, num: int):
        """Get detail of an album, including raw image url.

        Args:
            album (AlbumData): Necessary album data
            num (int): pic num

        Returns:
            dict: album details

        Raises:
            `ClientResponseError`
            `QzoneError`
            `RuntimeError`: transport error (maybe data is hooked)
        """
        default = {
            'callback': 'viewer_Callback',
            'cmtOrder': 1,
            'fupdate': 1,
            'plat': 'qzone',
            'source': 'qzone',
            'cmtNum': 0,
            'likeNum': 0,
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'callbackFun': 'viewer',
            'offset': 0,
            'appid': 311,
            'isFirst': 1,
            'need_private_comment': 1,
        }
        query = {
            'topicId': album.topicid,
            'picKey': album.pickey,
            'hostUin': album.hostuin,
            'number': num,
            'uin': self.login.uin,
            '_': time_ms(),
            't': randint(1e8, 1e9 - 1)    # type: ignore
        # The distribution is not consistent with photo.js; but the format is.
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.aget(const.floatview_photo_list, params=default | query) as r:
                r.raise_for_status()
                rtext = await r.text()
            return self._rtext_handler(rtext, msg=lambda d: d['message'])

        rjson: dict = (await retry_closure())['data']
        if query['t'] != int(rjson.pop('t')):
            raise RuntimeError('Something unexpected occured in transport.')
        return rjson
