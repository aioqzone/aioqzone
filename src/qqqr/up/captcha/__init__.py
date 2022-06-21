import asyncio
import base64
import re
from math import floor
from random import random
from time import time
from typing import Dict, List, Type, TypeVar, cast

from httpx import URL

from jssupport.execjs import ExecJS, Partial
from jssupport.jsjson import json_loads

from ...utils.daug import du
from ...utils.net import ClientAdapter
from ..type import CaptchaConfig, PrehandleResp, VerifyResp
from .jigsaw import Jigsaw, imitate_drag
from .vm import TDC, Slide

PREHANDLE_URL = "https://t.captcha.qq.com/cap_union_prehandle"
SHOW_NEW_URL = "https://t.captcha.qq.com/cap_union_new_show"
VERIFY_URL = "https://t.captcha.qq.com/cap_union_new_verify"

time_s = lambda: int(1e3 * time())
rnd6 = lambda: str(random())[2:8]

_TDC_TY = TypeVar("_TDC_TY", bound=TDC)


def hex_add(h: str, o: int):
    if h.endswith("#"):
        return h + str(o)
    if not h:
        return o
    return hex(int(h, 16) + o)[2:]


class TcaptchaSession:
    prehandleLoadTime: int

    def __init__(
        self,
        prehandle: PrehandleResp,
        appid: int,
        sid: str,
        subsid: int,
        prehandle_time: int = ...,
    ) -> None:
        self.prehandle = prehandle
        self.aid = appid
        self.sid = sid
        self.subsid = subsid
        self.prehandle_time = time_s() if prehandle_time == ... else prehandle_time

    def set_iframe(self, iframe: str):
        self._iframe = iframe
        self.conf = self.parse_captcha_conf(iframe)
        self.cdn_urls = tuple(self._cdn(i) for i in range(3))
        self.cdn_imgs: List[bytes] = []

    def set_js_env(self, tdc: TDC, slide: Slide):
        self.tdc = tdc
        self.slide = slide

    def set_pow_answer(self, ans: int, duration: int):
        self.pow_ans = ans
        self.duration = duration

    def set_captcha_answer(self, left: int, top: int):
        self.jig_ans = left, top

    @staticmethod
    def parse_captcha_conf(iframe: str):
        m = re.search(r"window\.captchaConfig=(\{.*\});", iframe)
        assert m
        return CaptchaConfig.parse_obj(json_loads(m.group(1)))

    def _cdn(self, cdn: int) -> URL:
        assert cdn in (0, 1, 2)
        data = {
            "aid": self.aid,
            "sess": self.conf.sess,
            "sid": self.sid,
            "subsid": self.subsid + cdn,
        }
        if cdn:
            data["img_index"] = cdn

        if cdn == 2:
            path = self.conf.cdnPic2
        else:
            path = self.conf.cdnPic1

        return URL("https://t.captcha.qq.com" + path).copy_merge_params(data)

    def slide_blob_url(self):
        m = re.search(r"https://captcha\.gtimg\.com/1/tcaptcha-slide\.\w+\.js", self._iframe)
        assert m
        return m.group(0)

    def tdx_js_url(self):
        m = re.search(r'src="(/td[xc].js.*?)"', self._iframe)
        assert m
        return "https://t.captcha.qq.com" + m.group(1)

    def vmslide_js_url(self):
        raise NotImplementedError


class Captcha:
    __match_md5 = None
    """Static js environment to match md5"""

    # (c_login_2.js)showNewVC-->prehandle
    # prehandle(recall)--call tcapcha-frame.*.js-->new_show
    # new_show(html)--js in html->loadImg(url)
    def __init__(self, client: ClientAdapter, appid: int, sid: str, xlogin_url: str):
        self.client = client
        self.appid = appid
        self.sid = sid
        self.xlogin_url = xlogin_url
        self.client.referer = "https://xui.ptlogin2.qq.com/"

    @property
    def base64_ua(self):
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
        createIframeStart = time_s()
        async with await self.client.get(PREHANDLE_URL, params=du(const, data)) as r:
            r.raise_for_status()
            m = re.search(CALLBACK + r"\((\{.*\})\)", r.text)

        assert m
        r = PrehandleResp.parse_raw(m.group(1))
        return TcaptchaSession(r, self.appid, self.sid, 2, createIframeStart)

    prehandle = new
    """alias of :meth:`.new`"""

    async def iframe(self, sess: TcaptchaSession):
        """Generate a captcha iframe. The iframe is the foundation of the following procedures."""
        const = {
            "protocol": "https",
            "accver": 1,
            "noheader": 1,
            "enableDarkMode": 0,
            "grayscale": 1,
            "clientype": 2,
            "cap_cd": "",
            "wxLang": "",
            "tcScale": 1,
            "uid": "",
            "showtype": "embed",
        }
        data = {
            "aid": self.appid,
            "ua": self.base64_ua,
            "fb": 1,
            "sid": self.sid,
            "sess": sess.prehandle.sess,
            "fwidth": 0,
            "subsid": sess.subsid,
            "rnd": rnd6(),
            "prehandleLoadTime": time_s() - sess.prehandle_time,
            "createIframeStart": sess.prehandle_time,
        }

        sess.prehandleLoadTime = data["prehandleLoadTime"]
        async with await self.client.get(SHOW_NEW_URL, params=du(const, data)) as r:
            r.raise_for_status()
            self.client.referer = str(r.url)
            iframe = "".join([i async for i in r.aiter_text()])

        sess.set_iframe(iframe)

    show = iframe
    """alias of :meth:`.iframe`"""

    async def get_blob(self, sess: TcaptchaSession) -> str:
        js_url = sess.slide_blob_url()
        async with await self.client.get(js_url) as r:
            r.raise_for_status()
            js = "".join([i async for i in r.aiter_text()])

        m = re.search(r"'(!function.*;')", js)
        assert m
        return m.group(1)

    async def get_tdc_vm(self, sess: TcaptchaSession, *, cls: Type[_TDC_TY] = TDC):
        js_url = sess.tdx_js_url()
        tdc = cls(sess._iframe, header=self.client.headers)

        async with await self.client.get(js_url) as r:
            r.raise_for_status()
            tdc.load_vm("".join([i async for i in r.aiter_text()]))

        sess.set_js_env(tdc, Slide())

    async def match_md5(self, sess: TcaptchaSession):
        if self.__match_md5 is None:
            blob = await self.get_blob(sess)
            m = re.search(r",(function\(\w,\w,\w\).*?duration.*?),", blob)
            assert m
            blob = m.group(1)
            env = ExecJS()
            env.setup.append(f"var n=Object();!{blob}(null,n,null)")
            env.setup.append(
                "function matchMd5(p, m){return n.getWorkloadResult({nonce:p,target:m})}"
            )
            self.__match_md5 = env

        pow_cfg = sess.conf.powCfg
        d = await self.__match_md5(Partial("matchMd5", pow_cfg.prefix, pow_cfg.md5))
        d = cast(Dict[str, int], json_loads(d))
        sess.set_pow_answer(d["ans"], d["duration"])

    async def get_captcha_problem(self, sess: TcaptchaSession):
        async def r(url):
            async with await self.client.get(url) as r:
                r.raise_for_status()
                return b"".join([i async for i in r.aiter_bytes()])

        for i in await asyncio.gather(*(r(i) for i in sess.cdn_urls)):
            sess.cdn_imgs.append(i)

    async def solve_captcha(self, sess: TcaptchaSession):
        if not sess.cdn_imgs:
            await self.get_captcha_problem(sess)
        assert sess.cdn_imgs

        jig = Jigsaw(*sess.cdn_imgs, top=sess.conf.spt)
        sess.set_captcha_answer(jig.left, jig.top)

        sess.tdc.set_data(clientType=2)
        sess.tdc.set_data(coordinate=[10, 24, 0.4103])
        sess.tdc.set_data(
            trycnt=1,
            refreshcnt=0,
            slideValue=imitate_drag(floor(jig.left * jig.rate)),
            dragobj=1,
        )
        sess.tdc.set_data(ft="qf_7P_n_H")

    async def verify(self):
        sess = await self.new()
        await self.iframe(sess)
        await self.get_tdc_vm(sess)

        waitEnd = time() + 0.6 * random() + 0.9

        await self.match_md5(sess)
        await self.get_captcha_problem(sess)
        await self.solve_captcha(sess)

        collect = await sess.tdc.get_data()
        tlg = len(collect)

        cfg = sess.conf.dict(
            include={
                "showtype",
                "noheader",
                "sess",
                "uid",
                "vsig",
                "websig",
                "subcapclass",
                "nonce",
            }
        )

        const = {
            "protocol": "https",
            "accver": 1,
            "enableDarkMode": 0,
            "grayscale": 1,
            "clientype": 2,
            "wxLang": "",
            "cap_cd": "",
            "cdata": 0,
            "fpinfo": "",
            "fwidth": 0,
            "tcScale": 1,
        }

        data = {
            "aid": self.appid,
            "ua": self.base64_ua,
            "fb": 1,
            "sid": self.sid,
            "rnd": rnd6(),
            "prehandleLoadTime": sess.prehandleLoadTime,
            "createIframeStart": sess.prehandle_time,
            "subsid": sess.subsid,
            "ans": "{0},{1};".format(*sess.jig_ans),
            "vlg": f"{sess.tdc.vmAvailable}_{sess.tdc.vmByteCode}_1",
            "pow_answer": hex_add(sess.conf.powCfg.prefix, sess.pow_ans)
            if sess.pow_ans
            else sess.pow_ans,
            "pow_calc_time": sess.duration,
            "eks": (await sess.tdc.get_info())["info"],
            "tlg": tlg,
            sess.conf.collectdata: collect,
            "vData": sess.slide.get_data(sess.conf.sess, tlg),
        }
        await asyncio.sleep(max(0, waitEnd - time()))
        async with await self.client.post(VERIFY_URL, data=du(const, cfg, data)) as r:
            r = VerifyResp.parse_raw(r.text)

        if r.code:
            raise RuntimeError(f"Code {r.code}: {r.errMessage}")
        return r
