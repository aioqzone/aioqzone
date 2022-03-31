"""
Offers a class to execute js by communicating with subprocess.

... warning:: On win32 platform, importing this module will change asyncio event loop policy to
:external:class:`asyncio.WindowsProactorEventLoopPolicy`!
"""

import asyncio
from collections import defaultdict
from functools import partial
from sys import platform
from typing import Any, Coroutine, Optional


class ExecJS:
    def __init__(self, node: str = "node", *, js: Optional[str] = None):
        self.js = js
        self.que = []
        self.node = node
        assert self.version() is not None, f"`{self.node}` is not installed."
        assert self.loop_policy_check()

    @staticmethod
    def callstr(func, *args, asis: bool = False) -> str:
        tostr = {bool: lambda i: ["false", "true"][i]}
        tostr = defaultdict(lambda: repr, tostr)
        quoted = (repr(i) if asis else tostr[type(i)](i) for i in args)
        return f'{func}({",".join(quoted)})'

    def addfunc(self, func: str, *args):
        self.que.append((func, *args))

    async def _exec(self, js: str):
        p = await asyncio.subprocess.create_subprocess_exec(
            self.node,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await p.communicate(js.encode())
        removesuffix = lambda s: s[:-1] if str.endswith(s, "\n") else s
        if stderr:
            raise RuntimeError(removesuffix(stderr.decode()))
        return removesuffix(stdout.decode())

    def __call__(self, func: str, *args, asis: bool = False) -> Coroutine[Any, Any, str]:
        js = self.js
        assert js is not None
        for i in self.que:
            js += self.callstr(*i, asis=asis)
            js += ";"
        self.que.clear()
        js += f"\nconsole.log({self.callstr(func, *args, asis=asis)});process.exit();"
        return self._exec(js)

    def get(self, prop: str):
        assert self.js is not None
        js = self.js + f"\nconsole.log({prop});process.exit();"
        return self._exec(js)

    def bind(self, func: str, new: bool = True):
        n = ExecJS(self.node, js=self.js) if new else self
        return partial(n.__call__, func)

    def version(self):
        import subprocess

        try:
            p = subprocess.Popen(
                [self.node, "-v"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            return
        stdout, stderr = p.communicate()
        if stderr:
            raise RuntimeError(stderr.decode())
        return stdout.decode()

    def loop_policy_check(self):
        """On Windows, the default event loop :external:class:`asyncio.ProactorEventLoop` supports subprocesses,
        whereas :external:class:`asyncio.SelectorEventLoop` does not.
        """
        if platform == "win32" and isinstance(
            asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy
        ):
            return False
        return True


if platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
