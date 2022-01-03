import subprocess
from functools import partial
from typing import Union


class ExecJS:
    def __init__(self, node: Union[str, list[str]] = 'node', *, js=None):
        self.js = js
        self.que = []

        self.node = node.copy() if isinstance(node, list) else node.split()
        assert self.version() is not None, f"`{self.node[0]}` is not installed."

    @staticmethod
    def callstr(func, *args, asis: bool = False) -> str:
        quoted = (
            tostr[ty]() if not asis and (ty := type(i))
            in (tostr := {
                str: lambda: f'"{i}"',
                bool: lambda: {
                    True: 'true',
                    False: 'false'
                }[i]
            }) else str(i) for i in args
        )
        return f'{func}({",".join(quoted)})'

    def addfunc(self, func: str, *args):
        self.que.append((func, *args))

    def _exec(self, js: str):
        p = subprocess.Popen(
            self.node, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate(js.encode())
        if stderr:
            raise RuntimeError(stderr.decode())
        return stdout.decode()

    def __call__(self, func: str, *args, asis: bool = False) -> str:
        js = self.js
        for i in self.que:
            js += self.callstr(*i, asis=asis)
            js += ';'
        self.que.clear()
        js += f'\nconsole.log({self.callstr(func, *args, asis=asis)});'
        return self._exec(js)

    def get(self, prop: str):
        js = self.js + f'\nconsole.log({prop});'
        return self._exec(js)

    def bind(self, func: str, new: bool = True):
        n = ExecJS(self.node, js=self.js) if new else self
        return partial(n.__call__, func)

    def version(self):
        try:
            p = subprocess.Popen(
                self.node + ['-v'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            return
        stdout, stderr = p.communicate()
        if stderr:
            raise RuntimeError(stderr.decode())
        return stdout.decode()
