import re
from dataclasses import dataclass
from random import random
from urllib.parse import parse_qs, quote, unquote

import aioqzone.api.constant as const
from aiohttp import ClientSession as Session
from jssupport.jsjson import json_loads

from ..exception import QzoneError
from ..interface.login import Loginable
from ..utils.time import time_ms


class QzoneApi:
    """A wrapper for Qzone http interface.
    """
    encoding = 'utf-8'
    host = "https://user.qzone.qq.com"
    cb_regex = re.compile(r"callback\((\{.*\})", re.S | re.I)

    def __init__(self, session: Session, loginman: Loginable) -> None:
        self.sess = session
        self.login = loginman

    def aget(self, url: str, params: dict[str, str] = None):
        params = params or {}
        params |= {'g_tk': self.login.gtk}
        return self.sess.get(self.host + url, params=params)

    def apost(self, url: str, params: dict[str, str] = None, data: dict = None):
        params = params or {}
        params |= {'g_tk': self.login.gtk}
        return self.sess.get(self.host + url, params=params, data=data)

    class FeedsMoreTransaction:
        def __init__(self, default=None) -> None:
            self.extern = default or {}

        def parse(self, page):
            unquoted = self.extern[page]
            if unquoted == "undefined": return {}
            return {k: v[-1] for k, v in parse_qs(unquoted, keep_blank_values=True).items()}

    async def feeds3_html_more(self, pagenum: int, trans: FeedsMoreTransaction = None) -> list:
        """return a list of dict, each dict reps a feed.

        Args:
            pagenum (int): #page >= 0
            trans: reps a skim transaction. Mutable.

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
            'count': 10,    # fixed
            'usertime': time_ms(),
            'externparam': quote(trans.extern[pagenum])
        }
        async with self.aget(const.feeds3_html_more, default | query) as r:
            r.raise_for_status()
            rtext = await r.text(encoding=self.encoding)

        rtext = self.cb_regex.search(rtext).group(1)
        rjson = json_loads(rtext)
        if rjson['code'] != 0:
            raise QzoneError(r['code'], r['message'])

        data: dict = r['data']
        trans.extern[pagenum + 1] = unquote(data['main']["externparam"])
        return data['data']

    @dataclass(frozen=True)
    class FeedData:
        uin: int
        tid: str
        feedstype: str

    async def emotion_getcomments(self, feedData: FeedData) -> str:
        """Get complete html of a given feed

        Args:
            feedData (dict): [description]

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
            "uin": feedData.uin,
            "tid": feedData.tid,
            "feedsType": feedData.feedstype,
            "qzreferrer": f"https://user.qzone.qq.com/{self.login.uin}",
        }

        async with self.apost(const.emotion_getcomments, default | body) as r:
            r.raise_for_status()
            rtext = await r.text(encoding=self.encoding)

        r = self.cb_regex.search(rtext).group(1)
        r = json_loads(r)
        if r["err"] == 0: return r["newFeedXML"].strip()
        raise QzoneError(r['err'], rdict=r)

    async def emotion_msgdetail(self, owner: int, fid: str):
        """Get detail of a given msg.
        NOTE: share msg is not support, i.e. `appid=311`

        Args:
            owner (int): owner uin
            fid (str): feed id, named fid, tid or feedkey

        Returns:
            dict: a dict reps the feed in detail
        """
        query = {
            'uin': owner,
            'tid': fid,
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
        async with self.aget(const.emotion_msgdetail, params=query) as r:
            r.raise_for_status()
            rtext = await r.text(encoding=self.encoding)

        r = self.cb_regex.search(rtext).group(1)
        return json_loads(r)
