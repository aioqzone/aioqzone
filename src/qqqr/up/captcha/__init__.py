import asyncio
import base64
import re
from math import floor
from random import choices, randint, random
from time import time
from typing import Dict, Iterable, List, Tuple, Type, TypeVar, cast
from urllib.parse import urlencode

from aiohttp import ClientSession as Session
from multidict import istr

from jssupport.execjs import ExecJS, Partial
from jssupport.jsjson import json_loads

from .jigsaw import Jigsaw
from .type import CaptchaConfig, PowCfg, PrehandleResp, VerifyResp
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


class IframeParser:
    def __init__(self, appid: int, sid: str, subsid: int) -> None:
        self.aid = appid
        self.sid = sid
        self.subsid = subsid

    def parseCaptchaConf(self, iframe: str):
        m = re.search(r"window\.captchaConfig=(\{.*\});", iframe)
        assert m
        self.conf = CaptchaConfig.parse_obj(json_loads(m.group(1)))
        return self.conf

    def cdn(self, cdn: int) -> str:
        assert cdn in (0, 1, 2)
        data = {
            "aid": self.aid,
            "sess": self.conf.sess,
            "sid": self.sid,
            "subsid": self.subsid + cdn,
        }
        if cdn:
            data["img_index"] = cdn
        path = getattr(self.conf, f"cdnPic{cdn if cdn else 1}")
        assert isinstance(path, str)
        return f"https://t.captcha.qq.com{path}?{urlencode(data)}"

    @staticmethod
    def slide_blob_url(iframe):
        m = re.search(r"https://captcha\.gtimg\.com/1/tcaptcha-slide\.\w+\.js", iframe)
        assert m
        return m.group(0)

    @staticmethod
    def tdx_js_url(iframe):
        m = re.search(r'src="(/td[xc].js.*?)"', iframe)
        assert m
        return "https://t.captcha.qq.com" + m.group(1)

    @staticmethod
    def vmslide_js_url(iframe):
        raise NotImplementedError


class Captcha:
    sess = None
    createIframeStart = 0
    subsid = 1
    __blob = None

    # (c_login_2.js)showNewVC-->prehandle
    # prehandle(recall)--call tcapcha-frame.*.js-->new_show
    # new_show(html)--js in html->loadImg(url)
    def __init__(self, session: Session, ssl_context, appid: int, sid: str):
        self.session = session
        self.ssl = ssl_context
        self.appid = appid
        self.sid = sid

        self.session.headers.update({istr("referer"): "https://xui.ptlogin2.qq.com/"})

    @property
    def base64_ua(self):
        return base64.b64encode(self.session.headers["User-Agent"].encode()).decode()

    async def prehandle(self, xlogin_url) -> PrehandleResp:
        """
        call this before calling :meth:`.iframe`.

        :param xlogin_url: the url requested in QRLogin.request
        """
        CALLBACK = "_aq_596882"
        data = {
            "aid": self.appid,
            "protocol": "https",
            "accver": 1,
            "showtype": "embed",
            "ua": self.base64_ua,
            "noheader": 1,
            "fb": 1,
            "enableDarkMode": 0,
            "sid": self.sid,
            "grayscale": 1,
            "clientype": 2,
            "cap_cd": "",
            "uid": "",
            "wxLang": "",
            "lang": "zh-CN",
            "entry_url": xlogin_url,
            # 'js': '/tcaptcha-frame.a75be429.js'
            "subsid": self.subsid,
            "callback": CALLBACK,
            "sess": "",
        }
        self.createIframeStart = time_s()
        async with self.session.get(PREHANDLE_URL, params=data, ssl=self.ssl) as r:
            r.raise_for_status()
            m = re.search(CALLBACK + r"\((\{.*\})\)", await r.text())

        assert m
        r = PrehandleResp.parse_raw(m.group(1))
        self.sess = r.sess
        self.subsid = 2
        return r

    async def iframe(self):
        """call this right after calling :meth:`.prehandle`"""
        assert self.sess, "call prehandle first"

        data = {
            "aid": self.appid,
            "protocol": "https",
            "accver": 1,
            "showtype": "embed",
            "ua": self.base64_ua,
            "noheader": 1,
            "fb": 1,
            "enableDarkMode": 0,
            "sid": self.sid,
            "grayscale": 1,
            "clientype": 2,
            "sess": self.sess,
            "fwidth": 0,
            "wxLang": "",
            "tcScale": 1,
            "uid": "",
            "cap_cd": "",
            "subsid": self.subsid,
            "rnd": rnd6(),
            "prehandleLoadTime": time_s() - self.createIframeStart,
            "createIframeStart": self.createIframeStart,
        }
        async with self.session.get(SHOW_NEW_URL, params=data, ssl=self.ssl) as r:
            self.session.headers.update({istr("referer"): str(r.url)})
            self.prehandleLoadTime = data["prehandleLoadTime"]
            return await r.text()

    show = iframe
    """alias of :meth:`.iframe`"""

    async def get_blob(self, iframe: str):
        js_url = IframeParser.slide_blob_url(iframe)
        async with self.session.get(js_url, ssl=self.ssl) as r:
            r.raise_for_status()
            js = await r.text()
        m = re.search(r"'(!function.*;')", js)
        assert m
        return m.group(1)

    async def get_tdc_vm(self, iframe: str, *, cls: Type[_TDC_TY] = TDC) -> _TDC_TY:
        js_url = IframeParser.tdx_js_url(iframe)
        self.tdc = cls(iframe, header=self.session.headers.copy())
        self.vmslide = Slide()

        async with self.session.get(js_url) as r:
            r.raise_for_status()
            self.tdc.load_vm(await r.text())

        return cast(_TDC_TY, self.tdc)

    async def match_md5(self, iframe: str, powCfg: PowCfg) -> Tuple[int, int]:
        if self.__blob is None:
            blob = await self.get_blob(iframe)
            m = re.search(r",(function\(\w,\w,\w\).*?duration.*?),", blob)
            assert m
            blob = m.group(1)
            env = ExecJS()
            env.setup.append(f"var n=Object();!{blob}(null,n,null)")
            env.setup.append(
                "function matchMd5(p, m){return n.getWorkloadResult({nonce:p,target:m})}"
            )
            self.__blob = env
        d = await self.__blob(Partial("matchMd5", powCfg.prefix, powCfg.md5))
        d = cast(Dict[str, int], json_loads(d))
        return int(d["ans"]), int(d["duration"])

    @staticmethod
    def imitateDrag(x: int) -> List[List[int]]:
        assert x < 300
        # 244, 1247
        t = randint(1200, 1300)
        n = randint(50, 65)
        X = lambda i: randint(1, max(2, i // 10)) if i < n - 15 else randint(6, 12)
        Y = lambda: choices([-1, 1, 0], cum_weights=[0.1, 0.2, 1], k=1)[0]
        T = lambda: randint(*choices(((65, 280), (6, 10)), cum_weights=(0.05, 1), k=1)[0])
        xs = ts = 0
        drag = []
        for i in range(n):
            xi, ti = X(i), T()
            drag.append([xi, Y(), ti])
            xs += xi
            ts += ti
        drag.append([max(1, x - xs), Y(), max(1, t - ts)])
        drag.reverse()
        return drag

    async def rio(self, urls: Iterable[str]) -> Tuple[bytes, ...]:
        async def inner(url):
            async with self.session.get(url, ssl=self.ssl) as r:
                r.raise_for_status()
                return await r.content.read()

        return await asyncio.gather(*(inner(i) for i in urls))

    async def verify(self):
        s = IframeParser(self.appid, self.sid, self.subsid)
        iframe = await self.iframe()
        s.parseCaptchaConf(iframe)
        Ians, duration = await self.match_md5(iframe, s.conf.powCfg)
        await self.get_tdc_vm(iframe)

        waitEnd = time() + 0.6 * random() + 0.9

        j = Jigsaw(*await self.rio(s.cdn(i) for i in range(3)), top=floor(int(s.conf.spt)))

        self.tdc.set_data({"clientType": 2})
        self.tdc.set_data({"coordinate": [10, 24, 0.4103]})
        self.tdc.set_data(
            {
                "trycnt": 1,
                "refreshcnt": 0,
                "slideValue": self.imitateDrag(floor(j.left * j.rate)),
                "dragobj": 1,
            }
        )
        self.tdc.set_data({"ft": "qf_7P_n_H"})
        collect = await self.tdc.get_data()
        tlg = len(collect)
        data = s.conf.dict(
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
        data.update(
            {
                "protocol": "https",
                "accver": 1,
                "enableDarkMode": 0,
                "grayscale": 1,
                "clientype": 2,
                "fwidth": 0,
                "wxLang": "",
                "tcScale": 1,
                "cap_cd": "",
                "cdata": 0,
                "fpinfo": "",
            }
        )
        data.update(
            {
                "aid": self.appid,
                "ua": self.base64_ua,
                "fb": 1,
                "sid": self.sid,
                "rnd": rnd6(),
                "prehandleLoadTime": self.prehandleLoadTime,
                "createIframeStart": self.createIframeStart,
                "subsid": self.subsid,
                "ans": f"{j.left},{j.top};",
                "vlg": f"{self.tdc.vmAvailable}_{self.tdc.vmByteCode}_1",
                "pow_answer": hex_add(s.conf.powCfg.prefix, Ians) if Ians else Ians,
                "pow_calc_time": duration,
                "eks": (await self.tdc.get_info())["info"],
                "tlg": tlg,
                s.conf.collectdata: collect,
                "vData": self.vmslide.get_data(s.conf.sess, tlg),
            }
        )
        await asyncio.sleep(max(0, waitEnd - time()))
        async with self.session.post(VERIFY_URL, data=data, ssl=self.ssl) as r:
            self.sess = None
            self.createIframeStart = 0
            self.prehandleLoadTime = 0
            r = VerifyResp.parse_raw(await r.text())

        if r.errorCode:
            raise RuntimeError(f"Code {r.errorCode}: {r.errMessage}")
        return r
