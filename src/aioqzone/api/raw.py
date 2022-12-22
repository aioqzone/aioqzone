"""
Basic wrapper of Qzone HTTP interface.
"""

import logging
from functools import wraps
from random import randint, random
from typing import Callable, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import parse_qs

from httpx import HTTPStatusError

import aioqzone.api.constant as const
from jssupport.jsjson import JsonValue, json_loads
from qqqr.utils.daug import du
from qqqr.utils.net import ClientAdapter, raise_for_status

from ..event.login import Loginable
from ..exception import CorruptError, QzoneError
from ..type.internal import AlbumData, LikeData
from ..utils.regex import response_callback
from ..utils.time import time_ms

logger = logging.getLogger(__name__)

StrDict = Dict[str, JsonValue]


class QzoneApi:
    """Just a wrapper for Qzone http interface. No type validating."""

    encoding = "utf-8"
    host = "https://user.qzone.qq.com"

    def __init__(self, client: ClientAdapter, loginman: Loginable) -> None:
        self.client = client
        self.login = loginman

    @property
    def referer(self):
        return self.client.headers["referer"]

    @referer.setter
    def referer(self, value: str):
        self.client.headers["referer"] = value

    async def _get_gtk(self) -> int:
        """Get gtk with async-lock

        :raises `aioqzone.exception.QzoneError`: if gtk is 0
        :return: gtk
        """
        async with self.login.lock:
            gtk = self.login.gtk
        if gtk == 0:
            raise QzoneError(-3000)
        return gtk

    async def aget(self, url: str, params: Optional[Dict[str, str]] = None):
        params = params or {}
        params = du(params, {"g_tk": str(await self._get_gtk())})
        self.referer = f"https://user.qzone.qq.com/{self.login.uin}/infocenter"
        return self.client.get(self.host + url, params=params)

    async def apost(
        self, url: str, params: Optional[Dict[str, str]] = None, data: Optional[dict] = None
    ):
        params = params or {}
        params = du(params, {"g_tk": str(await self._get_gtk())})
        self.referer = f"https://user.qzone.qq.com/{self.login.uin}/infocenter"
        if data:
            data["qzreferrer"] = self.referer
        return self.client.post(self.host + url, params=params, data=data)

    def _relogin_retry(self, func: Callable):
        """A decorator which will relogin and retry given func if cookie expired.

        'cookie expired' is indicated by:

        - `aioqzone.exception.QzoneError` code -3000 or -4002
        - HTTP response code 403

        :meta public:
        :param func: a callable, which should be rerun after login expired and relogin.

        .. note:: Decorate code as less as possible
        .. warning::

                You *SHOULD* **NOT** wrap a function with mutable input. If you change the mutable
                var in the first attempt, in the second attempt the var saves the changed value.
        """

        @wraps(func)
        async def relogin_wrapper(*args, **kwds):
            """
            This wrapper will call :meth:`aioqzone.event.login.Loginable.new_cookie` if the wrapped
            function raises an error indicating that a new login is required.

            The exceptions this wrapper may raise depends on the login manager you passed in.
            Any exceptions irrelevent to "login needed" will be passed through w/o any change.

            :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.
            """
            try:
                return await func(*args, **kwds)
            except QzoneError as e:
                if e.code not in [-3000, -4002]:
                    raise e
            except HTTPStatusError as e:
                if e.response.status_code != 403:
                    raise e

            logger.info(f"Cookie expire in {func.__qualname__}. Relogin...")
            cookie = await self.login.new_cookie()
            return await func(*args, **kwds)

        return relogin_wrapper

    def _rtext_handler(
        self,
        rtext: str,
        cb: bool = True,
        errno_key: Tuple[str, ...] = ("code", "err"),
        msg_key: Tuple[str, ...] = ("msg", "message"),
    ) -> StrDict:
        """Handles the response text recieved from Qzone API, returns the parsed json dict.

        :meta public:
        :param rtext: response text
        :param cb: The text is to be parsed by callback_regex, defaults to True.
        :param errno_key: Error # key, defaults to ('code', 'err').
        :param msg_key: Error message key, defaults to ('msg', 'message').

        :raises `aioqzone.exception.QzoneError`: if errno != 0

        :return: json response
        """
        if cb:
            match = response_callback.search(rtext)
            assert match
            rtext = match.group(1)
        r = json_loads(rtext)
        assert isinstance(r, dict)

        err = next(filter(lambda i: i is not None, (r.get(i) for i in errno_key)), None)
        assert err is not None, f"no {errno_key} in {r.keys()}"
        assert isinstance(err, (int, str))
        err = int(err)

        if err != 0:
            msg = next(filter(None, (r.get(i) for i in msg_key)), None)
            if msg:
                raise QzoneError(err, msg, rdict=r)
            else:
                raise QzoneError(err, rdict=r)
        return r  # type: ignore

    async def feeds3_html_more(
        self,
        pagenum: int,
        count: int = 10,
        *,
        external: Optional[str] = None,
        daylist: str = "",
        uinlist: str = "",
    ) -> StrDict:
        """return a dict with ``main`` and ``data`` field.
        ``main`` field contains some auxiliary information, while data is a list of dict,
        each dict represents one feed.

        :param pagenum: #page >= 0
        :param count: feed count, max as 10, defaults to 10.
        :param external: `!main.externparam` field in last response
        :param daylist: `!main.daylist` field in last response
        :param uinlist: `!main.uinlist` field in last response

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: feed attributes and html feed

        .. versionchanged:: 0.9.4a1

            let `count` <= 10;
            Use external string directly and remove `FeedsMoreTransaction`.
        """

        default = {
            "scope": 0,
            "view": 1,
            "gid": "",
            "flag": "1",
            "refresh": 0,
            "aisortEndTime": 0,
            "aisortOffset": 0,
            "getAisort": 0,
            "aisortBeginTime": 0,
            "firstGetGroup": 0,
            "icServerTime": 0,
            "mixnocache": 0,
            "scene": 0,
            "dayspac": "undefined",
            "sidomain": "qzonestyle.gtimg.cn",
            "useutf8": 1,
            "outputhtmlfeed": 1,
        }
        if external and external != "undefined":
            last_qs = {k: v[-1] for k, v in parse_qs(external, keep_blank_values=True).items()}
        else:
            last_qs = {}
        applist = "all"
        query = {
            "daylist": daylist,
            "uinlist": uinlist,
            "filter": applist,
            "applist": applist,
            "rd": random(),
            "windowId": random(),
            "uin": self.login.uin,
            "pagenum": pagenum + 1,
            "begintime": last_qs.get("basetime", "undefined"),
            "count": min(10, count),
            "usertime": time_ms(),
            "externparam": external,
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.aget(const.feeds3_html_more, du(default, query)) as r:
                r.raise_for_status()
                rtext = r.text

            return self._rtext_handler(rtext)

        r = await retry_closure()
        data = r["data"]
        assert isinstance(data, dict)

        feeds = data.get("data", [])
        assert isinstance(feeds, list)
        data["data"] = list(filter(None, feeds))  # remove null

        return cast(StrDict, data)

    async def emotion_getcomments(self, uin: int, tid: str, feedstype: int) -> StrDict:
        """Get complete html of a given feed

        :param uin: uin
        :param tid: feed id
        :param feedstype: feedstype in html

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: response dict
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
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.apost(const.emotion_getcomments, data=du(default, body)) as r:
                r.raise_for_status()
                rtext = r.text

            return self._rtext_handler(rtext)

        return await retry_closure()

    async def emotion_msgdetail(self, owner: int, fid: str) -> StrDict:
        """Get detail of a given msg.

        :param owner: owner uin
        :param fid: feed id, named fid, tid or feedkey

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: a dict represents the feed in detail.

        .. note:: share msg is not support, i.e. `appid=311`
        """
        default = {
            "t1_source": 1,
            "ftype": 0,
            "sort": 0,
            "pos": 0,
            "num": 20,
            "callback": "callback",
            "code_version": 1,
            "format": "jsonp",
            "need_private_comment": 1,
        }
        query = {"uin": owner, "tid": fid}

        @self._relogin_retry
        async def retry_closure():
            async with await self.aget(const.emotion_msgdetail, params=du(default, query)) as r:
                r.raise_for_status()
                return self._rtext_handler(r.text)

        return await retry_closure()

    async def get_feeds_count(self) -> Dict[str, Union[int, list]]:
        """Get feeds update count (new feeds, new photos, new comments, etc)

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: update counts

        .. note::
            This api is also the 'keep-alive' signal to avoid cookie from expiring.
            Call this api every 300s can help keep cookie alive.
        """
        query = {"uin": self.login.uin, "rd": random()}

        @self._relogin_retry
        async def retry_closure():
            async with await self.aget(const.get_feeds_count, query) as r:
                r.raise_for_status()
                return self._rtext_handler(r.text)

        r = await retry_closure()
        return r["data"]  # type: ignore

    async def like_app(self, likedata: LikeData, like: bool = True) -> bool:
        """Like or unlike a feed.

        :param likedata: Necessary data for like/unlike
        :param like: True as like, False as unlike, defaults to True.

        :raises `httpx.HTTPStatusError`: error http response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: success flag

        .. versionchanged:: 0.2.7
            not a @noexcept method.
        """
        default = {
            "from": 1,
            "active": 0,
            "fupdate": 1,
        }
        body = {
            "opuin": self.login.uin,
            "unikey": likedata.unikey,
            "curkey": likedata.curkey,
            "appid": likedata.appid,
            "typeid": likedata.typeid,
            "abstime": likedata.abstime,
            "fid": likedata.fid,
        }
        url = const.internal_dolike_app if like else const.internal_unlike_app

        @self._relogin_retry
        async def retry_closure():
            async with await self.apost(url, data=du(default, body)) as r:
                r.raise_for_status()
                return self._rtext_handler(r.text, errno_key=("code", "ret"))

        try:
            await retry_closure()
            return True
        except QzoneError as e:
            logger.warning(f"Error in dolike/unlike. {e}")
            if e.rdict:
                logger.debug(e.rdict)
            return False
        except HTTPStatusError:
            logger.error("Error in dolike/unlike.", exc_info=True)
            raise

    async def floatview_photo_list(self, album: AlbumData, num: int) -> StrDict:
        """Get detail of an album, including raw image url.

        :param album: Necessary album data
        :param num: pic num

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.
        :raises `aioqzone.exception.CorruptError`: maybe data is corruptted

        :return: album details

        .. warning::
            This api is a 'slow' api, means it always returns an error code,
            requesting a retry a moment later. Use :meth:`.emotion_msgdetail` to get raw photo/video in
            a feed.
        """

        default = {
            "callback": "viewer_Callback",
            "cmtOrder": 1,
            "fupdate": 1,
            "plat": "qzone",
            "source": "qzone",
            "cmtNum": 0,
            "likeNum": 0,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "callbackFun": "viewer",
            "offset": 0,
            "appid": 311,
            "isFirst": 1,
            "need_private_comment": 1,
            "shootTime": "",
        }
        query = {
            "topicId": album.topicid,
            "picKey": album.pickey,
            "hostUin": album.hostuin,
            "number": num,
            "uin": self.login.uin,
            "_": time_ms(),
            "t": randint(int(1e8), int(1e9 - 1))
            # The distribution is not consistent with photo.js; but the format is.
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.aget(const.floatview_photo_list, du(default, query)) as r:
                r.raise_for_status()
                return self._rtext_handler(r.text)

        rjson = (await retry_closure())["data"]
        if query["t"] != int(rjson.pop("t")):  # type: ignore
            raise CorruptError("Something unexpected occured in transport.")
        return rjson  # type: ignore

    async def emotion_msglist(
        self,
        uin: int,
        num: int = 20,
        pos: int = 0,
    ) -> List[StrDict]:
        """Get msg(feed?) list of a user.

        :param uin: uin
        :param num: number, defaults to 20
        :param pos: start position, defaults to 0

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: a list of messages

        .. versionadded:: 0.2.6
        """
        add = {
            "hostUin": uin,
            "notice": 0,
            "inCharset": "utf-8",
            "outCharset": "utf-8",
            "cgi_host": "https://user.qzone.qq.com" + const.emotion_msglist,
        }
        param = {
            "uin": uin,
            "ftype": 0,
            "sort": 0,
            "pos": pos,
            "num": num,
            "replynum": 0,
            "callback": "callback",
            "code_version": 1,
            "format": "jsonp",
            "need_private_comment": 1,
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.aget(
                const.emotion_msglist, du(param, add) if pos else param
            ) as r:
                r.raise_for_status()
                rtext = r.text
            return self._rtext_handler(rtext)

        data = await retry_closure()
        return data["msglist"]  # type: ignore

    async def emotion_publish(self, content: str, right: int = 0) -> StrDict:
        """Publish a feed. appid=311.

        :param content: text content.
        :param right: feed access right, defaults to 0 (Not used till now)

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: qzone response as is, containing feed html and fid.

        .. versionadded:: 0.2.6
        .. warning:: This api is under development. It has basic functions only.
        """
        default = {
            "syn_tweet_verson": 1,
            "paramstr": 1,
            "pic_template": "",
            "richtype": "",
            "richval": "",
            "special_url": "",
            "subrichtype": "",
            "who": 1,
            "ver": 1,
            "to_sign": 0,
            "code_version": 1,
            "format": "fs",
        }
        body = {
            "ugc_right": 64,
            "con": content,
            "feedversion": 1,
            "hostuin": self.login.uin,
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.apost(const.emotion_publish, data=du(default, body)) as r:
                r.raise_for_status()
                return self._rtext_handler(r.text)

        return await retry_closure()

    async def emotion_delete(
        self,
        fid: str,
        abstime: int,
        appid: int,
        typeid: int,
        topicId: str,
        uin: Optional[int] = None,
    ) -> Optional[StrDict]:
        """Delete a feed.

        :param fid: feed id, named tid, feedkey, etc.
        :param abstime: feed create time. `now` in :meth:`.emotion_publish` result dict.
        :param appid: appid
        :param typeid: typeid
        :param topicId: topic id, got from html
        :param uin: host uin, defaults to None, means current logined user.

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: qzone response as is, usually nothing meaningful.

        .. versionadded:: 0.2.6
        """
        body = {
            "uin": uin or self.login.uin,
            "topicId": topicId,
            "feedsType": typeid,
            "feedsFlag": 0,
            "feedsKey": fid,
            "feedsAppid": appid,
            "feedsTime": abstime,
            "fupdate": 1,
            "ref": "feeds",
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.apost(const.emotion_delete, data=body) as r:
                # upstream error: qzone server returns 503, but the feed operation is done.
                raise_for_status(r, 200, 503)
                if r.status_code == 503:
                    return
                return self._rtext_handler(r.text)

        return await retry_closure()

    async def emotion_update(self, fid: str, content: str, uin: Optional[int] = None) -> StrDict:
        """Update the content of a feed.

        :param fid: feed id, named feedkey, tid, etc.
        :param content: new content in text.
        :param uin: host uin, defaults to None, means current logined user.

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: qzone response as is.

        .. versionadded:: 0.2.6
        .. warning:: This api is under development. It has basic functions only.
        """
        default = {
            "syn_tweet_verson": 1,
            "paramstr": 1,
            "pic_template": "",
            "richtype": "",
            "richval": "",  # album attribute comma list
            "special_url": "",
            "subrichtype": "",
            "feedversion": 1,
            "ver": 1,
            "code_version": "1",
            "format": "fs",
        }
        body = {
            "tid": fid,
            "con": content,
            "ugc_right": 64,
            "to_sign": 0,
            "ugcright_id": "TODO",  # TODO
            "hostuin": uin or self.login.uin,
            # 'pic_bo': ''
        }

        @self._relogin_retry
        async def retry_closure():
            async with await self.apost(const.emotion_update, data=du(default, body)) as r:
                r.raise_for_status()
                return self._rtext_handler(r.text)

        return await retry_closure()

    async def emotion_re_feeds(
        self,
        comment: str,
        topicId: str,
        typeid: int,
        owner: int,
        *,
        is_private: bool = False,
    ) -> str:
        """Reply (comment) a feed. Rich types are not supported now.

        :param comment: the comment string.
        :param typeid: typeid
        :param topicId: topic id, got from html
        :param owner: owner uin

        :raises `httpx.HTTPStatusError`: error http response code
        :raises `aioqzone.exception.QzoneError`: error qzone response code
        :raises: All error that may be raised from :meth:`.login.new_cookie`, which depends on the login manager you passed in.

        :return: new feed html

        .. versionadded:: 0.9.3a1

        .. seealso:: `.emotion_getcomments`
        """
        default = dict(
            inCharset="utf-8",
            outCharset="utf-8",
            plat="qzone",
            source="ic",
            isSignIn="",
            format="fs",
            ref="feeds",
        )
        data = dict(
            topicId=topicId,
            feedsType=typeid,
            hostUin=owner,
            platformid=50,
            uin=self.login.uin,
            content=comment,
            richval="",  # no rich types
            richtype="",
            private=int(is_private),
            paramstr=1,
        )

        @self._relogin_retry
        async def retry_closure():
            async with await self.apost(const.emotion_re_feeds, data=du(default, data)) as r:
                r.raise_for_status()
                return self._rtext_handler(r.text)

        r = await retry_closure()
        assert isinstance(r["data"], dict)
        return cast(str, r["data"]["feeds"])
