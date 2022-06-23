from pathlib import Path
from textwrap import dedent
from typing import Dict, MutableMapping, Tuple, cast
from urllib.parse import unquote

from jssupport.execjs import ExecJS, Partial
from jssupport.jsdom import JSDOM
from jssupport.jsjson import json_loads


class JSDOM_tdc(JSDOM):
    def _windowjs(self):
        js = """
        window = new Proxy({
            document: new Proxy(
                { createElement: (e) => { return {}; } },
                {
                    get: (targ, name) => {
                        if (name == "addEventListener") return undefined;
                        if (targ[name] !== undefined) return targ[name];
                        return dom.window.document[name];
                    }
                }
            )
        }, {
            get: (targ, name) => {
                if (name == "addEventListener") return undefined;
                if (targ[name] !== undefined) return targ[name];
                return dom.window[name];
            }
        })
        """
        return super()._windowjs() + dedent(js)


class TDC:
    """Exec tdc.js in JSDOM."""

    vmAvailable = 0
    vmByteCode = 0

    def __init__(self, iframe: str, header: MutableMapping[str, str]) -> None:
        self._js = JSDOM_tdc(
            src=iframe,
            ua=header["User-Agent"],
            location=header["Referer"],
            referrer="https://xui.ptlogin2.qq.com/",
        )

    def load_vm(self, vmcode: str):
        self._js.setup.append(f"window.eval(`{vmcode}`);")

    async def get_data(self):
        return unquote((await self._js.eval("window.TDC.getData(!0)")).strip())

    async def get_info(self) -> dict:
        return cast(dict, json_loads(await self._js.eval("window.TDC.getInfo()")))

    def set_data(self, **data):
        self._js.add_eval(f"window.TDC.setData({data})")

    def clear_tc(self):
        return self._js.eval("window.TDC.clearTc()")

    async def get_cookie(self):
        return (await self._js.eval("window.document.cookie")).strip()


class DecryptTDC(TDC):
    class DecryptTDC(JSDOM):
        def _windowjs(self):
            with open(Path(__file__).parent / "decrypt.js") as f:
                return super()._windowjs() + f.read()

    def __init__(self, iframe: str, header: MutableMapping[str, str]) -> None:
        self._js = self.DecryptTDC(
            src=iframe,
            ua=header["User-Agent"],
            location=header["Referer"],
            referrer="https://xui.ptlogin2.qq.com/",
        )

    def load_vm(self, vmcode: str):
        self.vmcode = vmcode

    def decrypt(self, collect: str):
        """.. seealso:: https://www.52pojie.cn/thread-1521480-1-1.html"""

        return self._js(Partial("dec", self.vmcode, collect))


class MatchMd5:
    __js = """
    function r(t, n) {
        var e = (65535 & t) + (65535 & n);
        return (t >> 16) + (n >> 16) + (e >> 16) << 16 | 65535 & e
    }
    function o(t, n, e, o, u, f) {
        return r(function (t, n) {
            return t << n | t >>> 32 - n
        }
            (r(r(n, t), r(o, f)), u), e)
    }
    function u(t, n, e, r, u, f, a) {
        return o(n & e | ~n & r, t, n, u, f, a)
    }
    function f(t, n, e, r, u, f, a) {
        return o(n & r | e & ~r, t, n, u, f, a)
    }
    function a(t, n, e, r, u, f, a) {
        return o(n ^ e ^ r, t, n, u, f, a)
    }
    function i(t, n, e, r, u, f, a) {
        return o(e ^ (n | ~r), t, n, u, f, a)
    }
    function c(t, n) {
        var e, o, c, l, s; t[n >> 5] |= 128 << n % 32, t[14 + (n + 64 >>> 9 << 4)] = n; var d = 1732584193, p = -271733879, g = -1732584194, _ = 271733878; for (e = 0; e < t.length; e += 16)o = d, c = p, l = g, s = _, p = i(p = i(p = i(p = i(p = a(p = a(p = a(p = a(p = f(p = f(p = f(p = f(p = u(p = u(p = u(p = u(p, g = u(g, _ = u(_, d = u(d, p, g, _, t[e], 7, -680876936), p, g, t[e + 1], 12, -389564586), d, p, t[e + 2], 17, 606105819), _, d, t[e + 3], 22, -1044525330), g = u(g, _ = u(_, d = u(d, p, g, _, t[e + 4], 7, -176418897), p, g, t[e + 5], 12, 1200080426), d, p, t[e + 6], 17, -1473231341), _, d, t[e + 7], 22, -45705983), g = u(g, _ = u(_, d = u(d, p, g, _, t[e + 8], 7, 1770035416), p, g, t[e + 9], 12, -1958414417), d, p, t[e + 10], 17, -42063), _, d, t[e + 11], 22, -1990404162), g = u(g, _ = u(_, d = u(d, p, g, _, t[e + 12], 7, 1804603682), p, g, t[e + 13], 12, -40341101), d, p, t[e + 14], 17, -1502002290), _, d, t[e + 15], 22, 1236535329), g = f(g, _ = f(_, d = f(d, p, g, _, t[e + 1], 5, -165796510), p, g, t[e + 6], 9, -1069501632), d, p, t[e + 11], 14, 643717713), _, d, t[e], 20, -373897302), g = f(g, _ = f(_, d = f(d, p, g, _, t[e + 5], 5, -701558691), p, g, t[e + 10], 9, 38016083), d, p, t[e + 15], 14, -660478335), _, d, t[e + 4], 20, -405537848), g = f(g, _ = f(_, d = f(d, p, g, _, t[e + 9], 5, 568446438), p, g, t[e + 14], 9, -1019803690), d, p, t[e + 3], 14, -187363961), _, d, t[e + 8], 20, 1163531501), g = f(g, _ = f(_, d = f(d, p, g, _, t[e + 13], 5, -1444681467), p, g, t[e + 2], 9, -51403784), d, p, t[e + 7], 14, 1735328473), _, d, t[e + 12], 20, -1926607734), g = a(g, _ = a(_, d = a(d, p, g, _, t[e + 5], 4, -378558), p, g, t[e + 8], 11, -2022574463), d, p, t[e + 11], 16, 1839030562), _, d, t[e + 14], 23, -35309556), g = a(g, _ = a(_, d = a(d, p, g, _, t[e + 1], 4, -1530992060), p, g, t[e + 4], 11, 1272893353), d, p, t[e + 7], 16, -155497632), _, d, t[e + 10], 23, -1094730640), g = a(g, _ = a(_, d = a(d, p, g, _, t[e + 13], 4, 681279174), p, g, t[e], 11, -358537222), d, p, t[e + 3], 16, -722521979), _, d, t[e + 6], 23, 76029189), g = a(g, _ = a(_, d = a(d, p, g, _, t[e + 9], 4, -640364487), p, g, t[e + 12], 11, -421815835), d, p, t[e + 15], 16, 530742520), _, d, t[e + 2], 23, -995338651), g = i(g, _ = i(_, d = i(d, p, g, _, t[e], 6, -198630844), p, g, t[e + 7], 10, 1126891415), d, p, t[e + 14], 15, -1416354905), _, d, t[e + 5], 21, -57434055), g = i(g, _ = i(_, d = i(d, p, g, _, t[e + 12], 6, 1700485571), p, g, t[e + 3], 10, -1894986606), d, p, t[e + 10], 15, -1051523), _, d, t[e + 1], 21, -2054922799), g = i(g, _ = i(_, d = i(d, p, g, _, t[e + 8], 6, 1873313359), p, g, t[e + 15], 10, -30611744), d, p, t[e + 6], 15, -1560198380), _, d, t[e + 13], 21, 1309151649), g = i(g, _ = i(_, d = i(d, p, g, _, t[e + 4], 6, -145523070), p, g, t[e + 11], 10, -1120210379), d, p, t[e + 2], 15, 718787259), _, d, t[e + 9], 21, -343485551), d = r(d, o), p = r(p, c), g = r(g, l), _ = r(_, s); return [d, p, g, _]
    }
    function l(t) {
        var n, e = ""; for (n = 0; n < 32 * t.length; n += 8)e += String.fromCharCode(t[n >> 5] >>> n % 32 & 255); return e
    }
    function s(t) {
        var n, e = []; for (e[(t.length >> 2) - 1] = void 0, n = 0; n < e.length; n += 1)e[n] = 0; for (n = 0; n < 8 * t.length; n += 8)e[n >> 5] |= (255 & t.charCodeAt(n / 8)) << n % 32; return e
    }
    function d(t) {
        var n, e, r = "0123456789abcdef", o = ""; for (e = 0; e < t.length; e += 1)n = t.charCodeAt(e), o += r.charAt(n >>> 4 & 15) + r.charAt(15 & n); return o
    }
    function p(t) {
        return unescape(encodeURIComponent(t))
    }
    function g(t) {
        return function (t) {
            return l(c(s(t), 8 * t.length))
        }
            (p(t))
    }
    function _(t, n) {
        return function (t, n) {
            var e, r, o = s(t), u = [], f = []; for (u[15] = f[15] = void 0, o.length > 16 && (o = c(o, 8 * t.length)), e = 0; e < 16; e += 1)u[e] = 909522486 ^ o[e], f[e] = 1549556828 ^ o[e]; return r = c(u.concat(s(n)), 512 + 8 * n.length), l(c(f.concat(r), 640))
        }
            (p(t), p(n))
    }
    function cal_md5(t, n, e) {
        return n ? e ? _(n, t) : function (t, n) {
            return d(_(t, n))
        }
            (n, t) : e ? g(t) : function (t) {
                return d(g(t))
            }
                (t)
    }
    function getWorkloadResult(nonce, target, n) {
        var start = +new Date,
            cnt = 0,
            timeout = "number" == typeof n ? n : 3e4;
        for (; cal_md5("" + nonce + cnt) !== target && (cnt += 1, !(+new Date - start > timeout)););
        return {
            ans: cnt, duration: +new Date - start
        }
    }
    """

    def __init__(self) -> None:
        self.env = ExecJS()
        self.env.setup.append(self.__js)

    async def __call__(self, prefix: str, md5: str) -> Tuple[int, int]:
        d = await self.env(Partial("getWorkloadResult", prefix, md5))
        d = cast(Dict[str, int], json_loads(d))
        return d["ans"], d["duration"]
