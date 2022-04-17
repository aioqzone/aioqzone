"""
Offers a class to execute js by communicating with subprocess.

.. warning:: On win32 platform, importing this module will change asyncio event loop policy to
:external:class:`asyncio.WindowsProactorEventLoopPolicy`!
"""

import asyncio
from collections import defaultdict
from functools import partial
from itertools import chain
from shutil import which
from sys import platform
from typing import List, Optional, Union

from .exception import JsRuntimeError, NodeNotFoundError

JsExpr = Union[str, "Partial"]


class Partial:
    __slots__ = "func", "args", "asis"

    def __init__(self, name: str, *args, asis: bool = False) -> None:
        self.func = name
        self.args = args
        self.asis = asis

    def __str__(self) -> str:
        tostr = {bool: lambda i: ["false", "true"][i], Partial: str}
        tostr = defaultdict(lambda: repr, tostr)
        quoted = (repr(i) if self.asis else tostr[type(i)](i) for i in self.args)
        return f"{self.func}({','.join(quoted)})"

    def __repr__(self) -> str:
        return f"JsPartial: {self.func}(...)"

    def __call__(self, env: Optional["ExecJS"] = None):
        env = env or ExecJS()
        return env(self)


class ExecJS:
    """Execute javascript in such order:

    * setup: :obj:`.setup`, :meth:`.add_setup`
    * run: :obj:`.run`, :meth:`.add_run`
    * post: :obj:`.post`, :meth:`.add_post`

    If it is required to change executable name, use classvar :obj:`.node`. Note that this must be a
    executable name, so something like ``bash -c`` is illegal.
    """

    __slots__ = "setup", "run", "post", "__dict__"

    node: str = "node"
    """node executable name. Default as :program:`node`."""

    setup: List[JsExpr]
    """Expressions executed before :obj:`.run`.
    Will not be cleared after executing."""

    run: List[JsExpr]
    """Expressions to be executed, after :obj:`.setup` but before :obj:`.post`.
    Will be cleared after executing."""

    post: List[JsExpr]
    """Expressions executed after :obj:`.run`.
    Will not be cleared after executing."""

    @classmethod
    def check_node(cls):
        return which(cls.node) is not None

    @classmethod
    def loop_policy_check(cls):
        """On Windows, the default event loop :external:class:`asyncio.ProactorEventLoop` supports subprocesses,
        whereas :external:class:`asyncio.SelectorEventLoop` does not.
        """
        if platform == "win32" and isinstance(
            asyncio.get_event_loop_policy(), asyncio.WindowsSelectorEventLoopPolicy
        ):
            return False
        return True

    def check_all(self):
        if not self.check_node():
            raise NodeNotFoundError(self.node)
        assert self.loop_policy_check(), "loop policy cannot be `WindowsSelectorEventLoopPolicy`"

    def __init__(self):
        self.check_all()
        self.setup = []
        self.run = []
        self.post = []

    def add_setup(self, func: str, *args, asis: bool = False):
        self.setup.append(Partial(func, *args, asis=asis))
        return self

    def add_run(self, func: str, *args, asis: bool = False):
        self.run.append(Partial(func, *args, asis=asis))
        return self

    def add_post(self, func: str, *args, asis: bool = False):
        self.post.append(Partial(func, *args, asis=asis))
        return self

    @staticmethod
    async def exec(node: str, js: str) -> str:
        p = await asyncio.subprocess.create_subprocess_exec(
            node,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            executable=which(node),
        )
        stdout, stderr = await p.communicate(js.encode())
        removesuffix = lambda s: s[:-1] if str.endswith(s, "\n") else s
        if stderr:
            raise JsRuntimeError(p.returncode or 1, node, removesuffix(stderr.decode()))
        return removesuffix(stdout.decode())

    def bind(self, expr: Optional[JsExpr] = None):
        js = ""
        if expr is None:
            pass
        elif isinstance(expr, Partial):
            self.add_run("console.log", expr)
        else:
            self.run.append(f"console.log({expr})")
        for expr in chain(self.setup, self.run, self.post):
            js += str(expr)
            js += ";"
        return partial(self.exec, node=self.node, js=js)

    def __call__(self, expr: Optional[JsExpr]):
        f = self.bind(expr)
        self.run.clear()
        return f()

    def get(self, prop: str):
        return self(prop)


if platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
