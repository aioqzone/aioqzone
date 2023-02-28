"""This module implements (or calls) qzone password encrypt algorithm."""

import base64
import re
import struct
from abc import ABC, abstractmethod
from binascii import hexlify
from hashlib import md5
from random import randint
from typing import Union

from rsa import PublicKey
from rsa import encrypt as rsa_encrypt

from ..utils.net import ClientAdapter

LOGIN_JS = "https://qq-web.cdn-go.cn/any.ptlogin2.qq.com/v1.3.0/ptlogin/js/c_login_2.js"
PUBKEY = PublicKey(
    int(
        "e9a815ab9d6e86abbf33a4ac64e9196d5be44a09bd0ed6ae052914e1a865ac8331fed863de8ea697e9a7f63329e5e23cda09c72570f46775b7e39ea9670086f847d3c9c51963b131409b1e04265d9747419c635404ca651bbcbc87f99b8008f7f5824653e3658be4ba73e4480156b390bb73bc1f8b33578e7a4e12440e9396f2552c1aff1c92e797ebacdc37c109ab7bce2367a19c56a033ee04534723cc2558cb27368f5b9d32c04d12dbd86bbd68b1d99b7c349a8453ea75d1b2e94491ab30acf6c46a36a75b721b312bedf4e7aad21e54e9bcbcf8144c79b6e3c05eb4a1547750d224c0085d80e6da3907c3d945051c13c7c1dcefd6520ee8379c4f5231ed",
        16,
    ),
    int("10001", 16),
)


class PasswdEncoder(ABC):
    def __init__(self, passwd: str) -> None:
        super().__init__()
        assert passwd, "password should not be empty"
        self._passwd = passwd

    @abstractmethod
    async def encode(self, salt: str, verifycode: str) -> str:
        pass


class NodeEncoder(PasswdEncoder):
    """Encoder using original js code by communicating with local :program:`Node.js <node>` progress.
    Make sure this always work.
    """

    __env = None

    def __init__(self, client: ClientAdapter, passwd: str) -> None:
        super().__init__(passwd)
        self.client = client

    async def login_js(self):
        async with self.client.get(LOGIN_JS) as r:
            r.raise_for_status()
            return r.text

    async def encode(self, salt: str, verifycode: str) -> str:
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
    """Pure python password encoder implementation using tea and rsa.

    .. note::

        Original code is from `@hoxide <https://github.com/LeoHuang2015/qqloginjs/blob/7d82f2f7d7363547763c40ce5d258d18989b9732/tea.py>`_,
        seems it has MIT license. Our code is under AGPL-3.0.
    """

    delta = 0x9E3779B9

    @classmethod
    def _xor(cls, a: bytes, b: bytes):
        a1, a2 = struct.unpack(">LL", a[0:8])
        b1, b2 = struct.unpack(">LL", b[0:8])
        r = struct.pack(">LL", (a1 ^ b1) & 0xFFFFFFFF, (a2 ^ b2) & 0xFFFFFFFF)
        return r

    @classmethod
    def _tea(cls, data: bytes, key: bytes):
        o, r, a, l = struct.unpack(">LLLL", key[0:16])
        y, z = struct.unpack(">LL", data[0:8])
        s = 0
        for _ in range(16):
            s += cls.delta
            s &= 0xFFFFFFFF
            y += (z << 4) + o ^ z + s ^ (z >> 5) + r
            y &= 0xFFFFFFFF
            z += (y << 4) + a ^ y + s ^ (y >> 5) + l
            z &= 0xFFFFFFFF
        r = struct.pack(">LL", y, z)
        return r

    @classmethod
    def tea_encrypt(cls, data: bytes, key: bytes) -> bytes:
        data = cls._hex2bytes(data)
        key = bytes.fromhex(key.decode())

        vl = len(data)
        filln = (vl + 10) % 8
        if filln:
            filln = 8 - filln
        fills = bytes([0xF8 & randint(0, 0xFF) | filln])
        fills += bytes(randint(0, 0xFF) for _ in range(filln + 2))
        data = fills + data + b"\0" * 7
        assert len(data) % 8 == 0

        last_out = last_in = bytes(8)
        r = bytearray()
        for i in range(0, len(data), 8):
            tmp = cls._xor(data[i : i + 8], last_out)
            last_out = cls._xor(cls._tea(tmp, key), last_in)
            last_in = tmp
            r.extend(last_out)

        return hexlify(r)

    @staticmethod
    def _upper_md5(raw_str: Union[bytes, str]) -> bytes:
        if isinstance(raw_str, str):
            raw_str = raw_str.encode()
        return md5(raw_str).hexdigest().upper().encode()

    @staticmethod
    def _rsa_encrypt(data: bytes):
        return hexlify(rsa_encrypt(data, PUBKEY))

    @staticmethod
    def _int2hex(ct: int) -> bytes:
        return hex(ct)[2:].encode()

    @staticmethod
    def _hex2bytes(s: bytes):
        """Equals to `bytes.fromxhex` if `s` is a standard hex string. If `s` contains non-hexadecimal char,
        it will try to ignore error.

        >>> _hex2bytes("1g")
        1   # ignores "g"
        >>> _hex2bytes("g1")
        0   # ignores all and gives default value

        This equals to the following code in javascript:

        .. code-block:: javascript

            String.fromCharCode(parseInt(double_unsigned))
        """
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

    async def encode(self, salt: str, verifycode: str, *, is_safe=False) -> str:
        # verifycode先转换为大写，然后转换为bytes
        vcode = hexlify(verifycode.upper().encode())

        # verifycode length
        vcode_len = self._int2hex(int(len(vcode) / 2)).zfill(4)

        passwd = self._passwd.encode()
        if not is_safe:
            passwd = self._upper_md5(self._passwd)

        raw_salt = bytes([ord(i) for i in salt])
        p = self._upper_md5(self._hex2bytes(passwd) + raw_salt)
        enc = self.tea_encrypt(passwd + hexlify(raw_salt) + vcode_len + vcode, p)

        enc_len = self._int2hex(int(len(enc) / 2)).zfill(4)
        enc = self._rsa_encrypt(self._hex2bytes(enc_len + enc))

        return base64.b64encode(self._hex2bytes(enc), b"*-").decode().replace("=", "_")
