import asyncio
import base64
import json
import logging
import re
import typing as t
from random import random
from time import time

from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from ...utils.net import ClientAdapter
from .._model import VerifyResp
from ._model import PrehandleResp
from .capsess import BaseTcaptchaSession as TcaptchaSession
from .select._types import SelectCaptchaSession, _TyHook

PREHANDLE_URL = "https://t.captcha.qq.com/cap_union_prehandle"
SHOW_NEW_URL = "https://t.captcha.qq.com/cap_union_new_show"
VERIFY_URL = "https://t.captcha.qq.com/cap_union_new_verify"

time_ms = lambda: int(1e3 * time())
"""+new Date"""
rnd6 = lambda: str(random())[2:8]
log = logging.getLogger(__name__)


def hex_add(h: str, o: int):
    if h.endswith("#"):
        return h + str(o)
    if not h:
        return o
    return hex(int(h, 16) + o)[2:]


class Captcha:
    # (c_login_2.js)showNewVC-->prehandle
    # prehandle(recall)--call tcapcha-frame.*.js-->new_show
    # new_show(html)--js in html->loadImg(url)
    select_captcha_input: _TyHook

    def __init__(self, client: ClientAdapter, appid: int, sid: str, xlogin_url: str):
        """
        :param client: network client
        :param appid: Specify the appid of the application
        :param sid: Session id got from :meth:`UpWebLogin.new`
        :param xlogin_url: :obj:`LoginBase.xlogin_url`
        """

        super().__init__()
        self.client = client
        self.appid = appid
        self.sid = sid
        self.xlogin_url = xlogin_url
        self.client.referer = "https://xui.ptlogin2.qq.com/"

    @property
    def base64_ua(self):
        """
        The base64_ua function encodes the User-Agent header in base64.

        :return: A string containing the base64 encoded user agent
        """

        return base64.b64encode(self.client.headers["User-Agent"].encode()).decode()

    async def new(self) -> TcaptchaSession:
        """``prehandle``. Call this method to generate a new verify session.

        :raises NotImplementedError: if not a slide captcha.
        :return: a tcaptcha session
        """
        CALLBACK = "_aq_596882"
        const = {
            "protocol": "https",
            "noheader": 1,
            "showtype": "embed",
            "enableDarkMode": 0,
            "grayscale": 1,
            "clientype": 2,
            "cap_cd": "",
            "uid": "",
            "wxLang": "",
            "lang": "zh-CN",
            "sess": "",
            "fb": 1,
            "aged": 0,
            "enableAged": 0,
            "elder_captcha": 0,
            "login_appid": "",
            "wb": 2,
        }
        data = {
            "aid": self.appid,
            "accver": 1,
            "ua": self.base64_ua,
            "sid": self.sid,
            "entry_url": self.xlogin_url,
            # 'js': '/tcaptcha-frame.a75be429.js'
            "subsid": 1,
            "callback": CALLBACK,
        }
        data.update(const)

        @retry(stop=stop_after_attempt(2), retry=retry_if_exception_type(ValidationError))
        async def retry_closure():
            async with self.client.get(PREHANDLE_URL, params=data) as r:
                r.raise_for_status()
                m = re.search(CALLBACK + r"\((\{.*\})\)", await r.text())

            assert m
            return PrehandleResp.model_validate_json(m.group(1))

        sess = TcaptchaSession.factory(await retry_closure())
        if isinstance(sess, SelectCaptchaSession):
            sess.select_captcha_input = self.select_captcha_input
        return sess

    async def iframe(self):
        """call this right after calling :meth:`.prehandle`"""
        async with self.client.get("https://t.captcha.qq.com/template/drag_ele.html") as r:
            return r.text

    prehandle = new
    """alias of :meth:`.new`"""

    async def verify(self):
        """
        :raise NotImplementedError: cannot solve captcha
        """
        sess = await self.new()

        await sess.get_captcha_problem(self.client)
        sess.solve_workload()
        await sess.solve_captcha()
        await sess.get_tdc(self.client)

        collect = str(sess.tdc.getData(None, True))  # BUG: maybe a String(), convert to str

        ans = dict(
            elem_id=1,
            type=sess.data_type,
            data=await sess.solve_captcha(),
        )
        if not ans["data"]:
            raise NotImplementedError

        data = {
            "collect": collect,
            "tlg": len(collect),
            "eks": sess.tdc.getInfo()["info"],
            "sess": sess.prehandle.sess,
            "ans": json.dumps(ans),
            "pow_answer": hex_add(sess.conf.common.pow_cfg.prefix, sess.pow_ans),
            "pow_calc_time": sess.duration,
        }
        log.debug(f"verify post data: {data}")

        async with self.client.post(VERIFY_URL, data=data) as r:
            r = VerifyResp.model_validate_json(await r.text())

        return r
