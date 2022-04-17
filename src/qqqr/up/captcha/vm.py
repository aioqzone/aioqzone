from pathlib import Path
from textwrap import dedent
from typing import cast
from urllib.parse import unquote, urlencode

from multidict import MutableMultiMapping

from jssupport.execjs import Partial
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

    def __init__(self, iframe: str, header: MutableMultiMapping[str]) -> None:
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

    def set_data(self, d: dict):
        self._js.add_eval(f"window.TDC.setData({d})")

    def clear_tc(self):
        return self._js.eval("window.TDC.clearTc()")

    async def get_cookie(self):
        return (await self._js.eval("window.document.cookie")).strip()


class DecryptTDC(TDC):
    class DecryptTDC(JSDOM):
        def _windowjs(self):
            with open(Path(__file__).parent / "decrypt.js") as f:
                return super()._windowjs() + f.read()

    def __init__(self, iframe: str, header: MutableMultiMapping[str]) -> None:
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


class Slide:
    """Encode and encrypt params into vdata."""

    from .vdata import VData

    @staticmethod
    def get_key(sess: str, tlg: int):
        return "".join(sess[int(c)] for c in str(tlg))

    @classmethod
    def get_data(cls, sess: str, tlg: int):
        param = {
            "key": cls.get_key(sess, tlg),
            "ss": "11%2Ctdc%2Cslide%2Cvm",
            "tp": 8393678227721880383,
            "env": 0,
            "py": 0,
            "version": 2,
            "cLod": "loadTDC",
            "inf": "iframe",
        }
        return cls.VData.encrypt(urlencode(param))
