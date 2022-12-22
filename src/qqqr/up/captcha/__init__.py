import asyncio
import base64
import json
import re
from hashlib import md5
from ipaddress import IPv4Address
from math import floor
from random import random
from time import time
from typing import List, Type, TypeVar

from httpx import URL

from ...constant import StatusCode
from ...exception import TencentLoginError
from ...utils.daug import du
from ...utils.iter import first
from ...utils.net import ClientAdapter
from ..type import PrehandleResp, VerifyResp
from .jigsaw import Jigsaw, imitate_drag
from .vm import CollectEnv

PREHANDLE_URL = "https://t.captcha.qq.com/cap_union_prehandle"
SHOW_NEW_URL = "https://t.captcha.qq.com/cap_union_new_show"
VERIFY_URL = "https://t.captcha.qq.com/cap_union_new_verify"

time_ms = lambda: int(1e3 * time())
"""+new Date"""
rnd6 = lambda: str(random())[2:8]

_TDC_TY = TypeVar("_TDC_TY", bound=CollectEnv)


def hex_add(h: str, o: int):
    if h.endswith("#"):
        return h + str(o)
    if not h:
        return o
    return hex(int(h, 16) + o)[2:]


class TcaptchaSession:
    def __init__(
        self,
        prehandle: PrehandleResp,
    ) -> None:
        self.prehandle = prehandle

        self.set_captcha()

    def set_captcha(self):
        self.conf = self.prehandle.captcha
        self.cdn_urls = (
            self._cdn(self.conf.render.bg.img_url),
            self._cdn(self.conf.render.sprite_url),
        )
        self.cdn_imgs: List[bytes] = []
        self.piece_sprite = first(self.conf.render.sprites, lambda s: s.move_cfg)

    def set_js_env(self, tdc: CollectEnv):
        self.tdc = tdc

    def solve_workload(self, *, timeout: float = 30.0):
        """
        The solve_workload function solves the workload from Tcaptcha:
        It solves md5(:obj:`PowCfg.prefix` + str(?)) == :obj:`PowCfg.md5`.
        The result and the calculating duration will be saved into this session.

        :param timeout: Calculating timeout, default as 30 seconds.
        :return: None
        """

        pow_cfg = self.conf.common.pow_cfg
        nonce = str(pow_cfg.prefix).encode()
        target = pow_cfg.md5.lower()

        start = time()
        cnt = 0

        while time() - start < timeout:
            if md5(nonce + str(cnt).encode()).hexdigest() == target:
                break
            cnt += 1

        self.pow_ans = cnt
        # on some environment this time is too low... add a limit
        self.duration = max(int((time() - start) * 1e3), 50)

    def set_captcha_answer(self, left: int, top: int):
        self.jig_ans = left, top

    def _cdn(self, rel_path: str) -> URL:
        return URL("https://t.captcha.qq.com").join(rel_path)

    def tdx_js_url(self):
        assert self.conf
        return URL("https://t.captcha.qq.com").join(self.conf.common.tdc_path)

    def vmslide_js_url(self):
        raise NotImplementedError


class Captcha:
    # (c_login_2.js)showNewVC-->prehandle
    # prehandle(recall)--call tcapcha-frame.*.js-->new_show
    # new_show(html)--js in html->loadImg(url)
    def __init__(self, client: ClientAdapter, appid: int, sid: str, xlogin_url: str):
        """
        :param client: network client
        :param appid: Specify the appid of the application
        :param sid: Session id got from :meth:`UpLogin.new`
        :param xlogin_url: :obj:`LoginBase.xlogin_url`
        """

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

        return base64.b64encode(self.client.ua.encode()).decode()

    async def new(self):
        """``prehandle``. Call this method to generate a new verify session.

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
        async with self.client.get(PREHANDLE_URL, params=du(const, data)) as r:
            r.raise_for_status()
            m = re.search(CALLBACK + r"\((\{.*\})\)", r.text)

        assert m
        r = PrehandleResp.parse_raw(m.group(1))
        return TcaptchaSession(r)

    async def iframe(self):
        """call this right after calling :meth:`.prehandle`"""
        async with self.client.get("https://t.captcha.qq.com/template/drag_ele.html") as r:
            return r.text

    prehandle = new
    """alias of :meth:`.new`"""

    async def get_ipv4(self):
        """Get the client's public IP(v4) address.

        :return: ipv4 str, or empty str if all apis failed."""
        for api in ["api.ipify.org", "v4.ident.me"]:
            async with self.client.get("https://" + api) as r:
                cand = r.text.strip()
                try:
                    IPv4Address(cand)
                    return cand
                except ValueError:
                    continue
        return ""

    async def get_tdc(self, sess: TcaptchaSession, *, cls: Type[_TDC_TY] = CollectEnv):
        """
        The get_tdc function is a coroutine that sets an instance of the :class:`TDC` class to `sess`.

        :param sess: captcha session
        :param cls: Specify the type of :class:`TDC` instance to be returned, default as :class:`TDC`.
        :return: None
        """
        js_url = sess.tdx_js_url()
        tdc = cls(
            xlogin_url=self.xlogin_url,
            ipv4=await self.get_ipv4(),
            ua=self.client.headers["User-Agent"],
            # iframe=await self.iframe(),
        )

        async with self.client.get(js_url) as r:
            r.raise_for_status()
            tdc.load_vm(r.text)

        sess.set_js_env(tdc)

    async def get_captcha_problem(self, sess: TcaptchaSession):
        """
        The get_captcha_problem function is a coroutine that accepts a TcaptchaSession object as an argument.
        It then uses the session to make an HTTP GET request to the captcha images (the problem). The images
        will be stored in the given session.

        :param sess: captcha session
        :return: None
        """

        async def r(url):
            async with self.client.get(url) as r:
                r.raise_for_status()
                return r.content

        for i in await asyncio.gather(*(r(i) for i in sess.cdn_urls)):
            sess.cdn_imgs.append(i)

    async def solve_captcha(self, sess: TcaptchaSession):
        """
        The solve_captcha function solves the captcha problem. If captcha images is not set,
        it will call :meth:`.get_captcha_problem` firstly.

        It then solve the captcha as that in :class:`.Jigsaw`. The answer is saved into `sess`.

        This function will also call :meth:`TDC.set_data` to imitate human behavior when solving captcha.

        :param sess: Store the information of the current session
        :return: None
        """

        if not sess.cdn_imgs:
            await self.get_captcha_problem(sess)
        assert sess.cdn_imgs

        piece_pos = tuple(
            slice(
                sess.piece_sprite.sprite_pos[i],
                sess.piece_sprite.sprite_pos[i] + sess.piece_sprite.size_2d[i],
            )
            for i in range(2)
        )

        jig = Jigsaw(*sess.cdn_imgs, piece_pos=piece_pos, top=sess.piece_sprite.init_pos[1])
        sess.set_captcha_answer(jig.left, jig.top)

        xs, ys = imitate_drag(floor(50 * jig.rate), floor(jig.left * jig.rate), jig.top)
        sess.tdc.add_run("simulate_slide", xs, ys)

    async def verify(self):
        sess = await self.new()
        await self.get_tdc(sess)

        waitEnd = time() + 0.6 * random() + 0.9

        sess.solve_workload()
        await self.get_captcha_problem(sess)
        await self.solve_captcha(sess)

        collect = await sess.tdc.get_data()

        ans = dict(
            elem_id=1,
            type=sess.piece_sprite.move_cfg.data_type[0],  # type: ignore
            data="{0},{1}".format(*sess.jig_ans),
        )
        data = {
            "collect": collect,
            "tlg": len(collect),
            "eks": (await sess.tdc.get_info())["info"],
            "sess": sess.prehandle.sess,
            "ans": json.dumps(ans),
            "pow_answer": hex_add(sess.conf.common.pow_cfg.prefix, sess.pow_ans),
            "pow_calc_time": sess.duration,
        }
        await asyncio.sleep(max(0, waitEnd - time()))
        async with self.client.post(VERIFY_URL, data=data) as r:
            r = VerifyResp.parse_raw(r.text)

        if r.code:
            raise TencentLoginError(StatusCode.NeedCaptcha, r.errMessage, subcode=r.code)
        return r
