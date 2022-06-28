from pathlib import Path
from textwrap import dedent
from typing import Dict, MutableMapping, Tuple, cast
from urllib.parse import unquote

from jssupport.execjs import ExecJS, Partial
from jssupport.jsdom import JSDOM
from jssupport.jsjson import json_loads


class TDC(JSDOM):
    """Exec tdc.js in JSDOM."""

    def __init__(self, iframe: str, header: MutableMapping[str, str]) -> None:
        super().__init__(
            src=iframe,
            ua=header["User-Agent"],
            location=header["Referer"],
            referrer="https://xui.ptlogin2.qq.com/",
        )

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

    def load_vm(self, vmcode: str):
        self.setup.append(f"window.eval(`{vmcode}`);")

    async def get_data(self):
        return unquote((await self.eval("window.TDC.getData(!0)")).strip())

    async def get_info(self) -> dict:
        return cast(dict, json_loads(await self.eval("window.TDC.getInfo()")))

    def set_data(self, **data):
        self.add_eval(f"window.TDC.setData({data})")

    def clear_tc(self):
        return self.eval("window.TDC.clearTc()")

    async def get_cookie(self):
        return (await self.eval("window.document.cookie")).strip()


class DecryptTDC(TDC):
    def __init__(self, iframe: str, header: MutableMapping[str, str]) -> None:
        super().__init__(iframe, header)
        self.add_post("process.exit", 0)

    def _windowjs(self):
        with open(Path(__file__).parent / "archive/decrypt.js") as f:
            return JSDOM._windowjs(self) + f.read()

    def load_vm(self, vmcode: str):
        self.vmcode = vmcode

    async def decrypt(self, collect: str):
        """.. seealso:: https://www.52pojie.cn/thread-1521480-1-1.html"""

        return await self(Partial("dec", self.vmcode, collect))
