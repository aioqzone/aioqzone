from pathlib import Path
from typing import cast
from urllib.parse import unquote, urlencode

from multidict import MutableMultiMapping

from jssupport.execjs import ExecJS
from jssupport.jsdom import JSDOM
from jssupport.jsjson import json_loads


class JSDOM_tdc(JSDOM):
    def _windowjs(self):
        with open(Path(__file__).parent / "window.tdc.js") as f:
            return super()._windowjs() + f.read()


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
        assert self._js.js
        self._js.js += f"window.eval(`{vmcode}`);"

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

        return self._js("dec", self.vmcode, collect)


class Slide:
    """Exec vdata.js in plain node."""

    def __init__(self) -> None:
        self._js = ExecJS(js=self.vdatajs())

    def vdatajs(self) -> str:
        with open(Path(__file__).parent / "vdata.js") as f:
            return f.read()

    @staticmethod
    def get_key(sess: str, tlg: int):
        return "".join(sess[int(c)] for c in str(tlg))

    def get_data(self, sess: str, tlg: int):
        param = {
            "key": self.get_key(sess, tlg),
            "ss": "11%2Ctdc%2Cslide%2Cvm",
            "tp": 8393678227721880383,
            "env": 0,
            "py": 0,
            "version": 2,
            "cLod": "loadTDC",
            "inf": "iframe",
        }
        return self._js("enc", urlencode(param))
