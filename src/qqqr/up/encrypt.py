"""This module implements (or calls) qzone password encrypt algorithm."""

import base64
import binascii
import hashlib
import re
import struct
from abc import ABC, abstractmethod
from random import randint
from typing import Awaitable, Union

from aiohttp import ClientSession

from ..type import CheckResult
from .rsa import rsa_encrypt

LOGIN_JS = "https://qq-web.cdn-go.cn/any.ptlogin2.qq.com/v1.3.0/ptlogin/js/c_login_2.js"


class PasswdEncoder(ABC):
    def __init__(self, sess: ClientSession, passwd: str) -> None:
        self.sess = sess
        self._passwd = passwd

    def encode(self, r: CheckResult) -> Awaitable[str]:
        assert self._passwd, "password should not be empty"
        return self.getEncryption(r.salt, r.verifycode)

    async def login_js(self):
        async with self.sess.get(LOGIN_JS) as response:
            response.raise_for_status()
            return await response.text()

    @abstractmethod
    async def getEncryption(self, salt: str, verifycode: str) -> str:
        pass


class NodeEncoder(PasswdEncoder):
    """Encoder using original js code by communicating with local :program:`Node.js <node>` progress.
    Make sure this always work.
    """

    __env = None

    async def getEncryption(self, salt: str, verifycode: str) -> str:
        from jssupport.execjs import ExecJS, Partial

        if self.__env is None:
            js = await self.login_js()
            m = re.search(r"function\(module,exports,__webpack_require__\).*\}", js)
            assert m
            funcs = m.group(0)
            env = ExecJS()
            env.setup.append("var navigator = new Object; navigator.appName = 'Netscape'")
            env.setup.append(f"var a=[{funcs}]")
            env.setup.append("function n(k) {var t,e=new Object;return a[k](t,e,n),e}")
            env.setup.append(
                "function getEncryption(p,s,v){var t,e=new Object;return a[9](t,e,n),e['default'].getEncryption(p,s,v,undefined)}"
            )
            self.__env = env

        return (await self.__env(Partial("getEncryption", self._passwd, salt, verifycode))).strip()


class TeaEncoder(PasswdEncoder):
    """Pure python password encoder implementation using tea and rsa. (beta)

    .. code-block::txt
        :caption: LICENSE

        The MIT License

        Copyright (c) 2005 hoxide

        Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
        The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
        QQ Crypt module.

    .. seealso:: https://github.com/LeoHuang2015/qqloginjs/blob/7d82f2f7d7363547763c40ce5d258d18989b9732/tea.py"""

    op = 0xFFFFFFFF
    delta = 0x9E3779B9

    @classmethod
    def _xor(cls, a: bytes, b: bytes):
        a1, a2 = struct.unpack(">LL", a[0:8])
        b1, b2 = struct.unpack(">LL", b[0:8])
        r = struct.pack(">LL", (a1 ^ b1) & cls.op, (a2 ^ b2) & cls.op)
        return r

    @classmethod
    def _tea(cls, v: bytes, t: bytes):
        o, r, a, l = struct.unpack(">LLLL", t[0:16])
        y, z = struct.unpack(">LL", v[0:8])
        s = 0
        for _ in range(16):
            s += cls.delta
            s &= cls.op
            y += (z << 4) + o ^ z + s ^ (z >> 5) + r
            y &= cls.op
            z += (y << 4) + a ^ y + s ^ (y >> 5) + l
            z &= cls.op
        r = struct.pack(">LL", y, z)
        return r

    @classmethod
    def encrypt(cls, data: bytes, key: bytes) -> bytes:
        END_CHAR = b"\0"
        FILL_N_OR = 0xF8

        vl = len(data)
        filln = (8 - (vl + 2)) % 8 + 2
        fills = bytes(randint(0, 0xFF) for _ in range(filln))
        data = bytes([randint(0, FILL_N_OR) | (filln - 2)]) + fills + data + END_CHAR * 7
        assert len(data) % 8 == 0

        tr = to = o = bytes(8)
        r = b""
        for i in range(0, len(data), 8):
            o = cls._xor(data[i : i + 8], tr)
            tr = cls._xor(cls._tea(o, key), to)
            to = o
            r += tr
        return cls._bytes2hex(r)

    @staticmethod
    def _tx_md5(raw_str: Union[bytes, str]):
        if isinstance(raw_str, str):
            raw_str = raw_str.encode()
        return hashlib.md5(raw_str).hexdigest().upper()

    @staticmethod
    def _int2hex(ct: int):
        return hex(ct)[2:]

    @staticmethod
    def _fromhex(s: str):
        return bytes(bytearray.fromhex(s))

    @staticmethod
    def _hex2bytes(s: bytes):
        e = []
        for i in range(0, len(s), 2):
            try:
                e.append(int(s[i : i + 2], 16))
                continue
            except ValueError:
                pass
            try:
                e.append(int(s[i : i + 1], 16))
            except ValueError:
                e.append(0)
        return bytes(e)

    @staticmethod
    def _bytes2hex(s: bytes):
        r = b""
        if not s:
            return r
        for c in s:
            r += hex(c)[2:].encode().zfill(2)
        return r

    async def getEncryption(self, salt: str, verifycode: str, is_safe: bool = False):
        # verifycode先转换为大写，然后转换为bytes
        vcode = binascii.b2a_hex(verifycode.upper().encode())

        # verifycode length
        vcode_len = self._int2hex(int(len(vcode) / 2)).encode().zfill(4)

        passwd = self._passwd
        if not is_safe:
            passwd = self._tx_md5(self._passwd)
        passwd = passwd.encode()

        raw_salt = bytes([ord(i) for i in salt])
        p = self._tx_md5(self._hex2bytes(passwd) + raw_salt)
        enc = self.encrypt(passwd + binascii.b2a_hex(raw_salt) + vcode_len + vcode, p.encode())

        enc_len = self._int2hex(int(len(enc) / 2)).encode().zfill(4)
        enc = await rsa_encrypt(self._hex2bytes(enc_len + enc))

        return base64.b64encode(self._hex2bytes(enc.encode()), b"*-").decode().replace("=", "_")
