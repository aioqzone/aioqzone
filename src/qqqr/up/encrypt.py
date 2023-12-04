"""This module implements (or calls) qzone password encrypt algorithm."""

import base64
import struct
from abc import ABC, abstractmethod
from binascii import hexlify
from contextlib import suppress
from hashlib import md5
from random import randint
from typing import Union

from rsa import PublicKey
from rsa import encrypt as rsa_encrypt

PUBKEY = PublicKey(
    29496410687140474961119245498915887699746044446431573370755803330798106970246404153324791276945613538908384803873682125117660027361723341249004819631069444529772469791984089750098105980017598210197651262912913003686191561807018747713133181122140185218267859189424249203315474970083525464658420601178962825467757646812713543951322998963854566864529737741968186080598661524321050149157809052160123823325600419947995213991733248714968482744503612161143440082407680406893798778565223892792085769105886059245894371386120558683710768503711260651478376959795916731934526910610532162307615665046831918144682579200585877303789,
    65537,
)


class PasswdEncoder(ABC):
    def __init__(self, passwd: str) -> None:
        super().__init__()
        self._passwd = passwd

    @abstractmethod
    async def encode(self, salt: str, verifycode: str) -> str:
        pass


class TeaEncoder(PasswdEncoder):
    """Pure python password encoder implementation using tea and rsa.

    .. note::

        Original code is from `@hoxide <https://github.com/LeoHuang2015/qqloginjs/blob/7d82f2f7d7363547763c40ce5d258d18989b9732/tea.py>`_,
        seems it has MIT license. Our code is under AGPL-3.0.

    .. hint::

        For javascript cases, we provide a `TypeScript version <_static/teaencoder.ts>` (testing).
    """

    delta = 0x9E3779B9

    @classmethod
    def _xor(cls, a: bytes, b: bytes):
        (a1,) = struct.unpack(">Q", a[:8])
        (b1,) = struct.unpack(">Q", b[:8])
        r = struct.pack(">Q", a1 ^ b1)
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

        This behaviour keeps in line with the following code in javascript:

        .. code-block:: javascript

            String.fromCharCode(parseInt(double_unsigned, 16))
        """
        e = []
        for i in range(0, len(s), 2):
            with suppress(ValueError):
                e.append(int(s[i : i + 2], 16))
                continue
            try:
                e.append(int(s[i : i + 1], 16))
            except ValueError:
                e.append(0)
        return bytes(e)

    async def encode(self, salt: str, verifycode: str, *, is_safe=False) -> str:
        assert len(self._passwd) >= 8, "password.length in [8, 16]"
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
