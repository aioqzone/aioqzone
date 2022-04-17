"""Encrypt and decrypt tcaptcha vdata.

Translated from :file:`.vdata.js`.
"""

import re
from ctypes import c_int32
from typing import Iterable, List, Union


def btoi(s: bytes):
    # little-endian encoding
    return [
        int.from_bytes(s[i : i + 4], "little", signed=False) for i in range(0, len(s), 4)
    ]  # note running off the end of the string generates nulls since


def itob(l: Iterable[int]):
    a = b""
    for i in l:
        a += bytes([i & 0xFF, i >> 8 & 0xFF, i >> 16 & 0xFF, i >> 24 & 0xFF])

    return a  # use Array.join() rather than repeated string appends for efficiency in IE


class i32(c_int32):
    def __xor__(self, i: "i32"):
        return i32(self.value ^ i.value)

    def __lshift__(self, i: int):
        return i32(self.value << i)

    def __rshift__(self, i: int):
        """signed rshift (sign-fill at left)"""
        return i32(self.value >> i)

    def urshift(self, i: int):
        """unsigned rshift (zfill at left)"""
        return i32(self.value >> i & 0xFFFFFFFF >> i)

    def __and__(self, i: Union[int, "i32"]):
        if isinstance(i, i32):
            return i32(self.value & i.value)
        return i32(self.value & i)

    def __add__(self, i: Union[int, "i32"]):
        if isinstance(i, int):
            return i32(self.value + i)
        return i32(self.value + i.value)

    def __sub__(self, i: Union[int, "i32"]):
        if isinstance(i, int):
            return i32(self.value - i)
        return i32(self.value - i.value)

    def __repr__(self) -> str:
        return repr(self.value)

    @classmethod
    def from_bytes(cls, i: bytes, byteorder):
        return cls(int.from_bytes(i, byteorder, signed=True))


class Base64:
    _keyStr = "GV5yc1_twaSpHPOE7R3jv9fqC2L-0TxMi4FuolBAbQeIgJU*XzZKWkDNh6n8dsrmY"

    @classmethod
    def encode(cls, input: bytes):
        output = ""
        sg = lambda l, i, d=0: l[i] if len(l) > i else d

        for i in range(0, len(input), 3):
            enc = [64] * 4
            slc = input[i : i + 3]

            enc[0] = slc[0] >> 2
            enc[1] = ((slc[0] & 3) << 4) | (sg(slc, 1) >> 4)

            if len(slc) > 1:
                enc[2] = ((slc[1] & 15) << 2) | (sg(slc, 2) >> 6)

                if len(slc) > 2:
                    enc[3] = slc[2] & 63

            for c in enc:
                output += cls._keyStr[c]

        return output

    @classmethod
    def decode(cls, input):
        input = re.sub(r"[^A-Za-z0-9_\*\-]", "", input)
        assert len(input) % 4 == 0
        output = b""

        for i in range(0, len(input), 4):
            enc1, enc2, enc3, enc4 = [cls._keyStr.index(c) for c in input[i : i + 4]]
            chr1 = (enc1 << 2) | (enc2 >> 4)
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2)
            chr3 = ((enc3 & 3) << 6) | enc4

            output += bytes([chr1])
            if enc3 != 64:
                output += bytes([chr2])
            if enc4 != 64:
                output += bytes([chr3])

        return output


class TeaBlock:
    Key = [i32(i) for i in (845493299, 812005475, 825582135, 1684093238)]  # 34e2c8f07b5169ad
    delta = 0x9E3779B9

    @classmethod
    def encrypt(cls, EncryData: List[int]):
        x, y = EncryData
        sum = 0
        for _ in range(32):
            x += (((i32(y) << 4 ^ i32(y).urshift(5)) + y) ^ (cls.Key[sum & 3] + sum)).value
            sum += cls.delta
            y += (((i32(x) << 4 ^ i32(x).urshift(5)) + x) ^ (cls.Key[sum >> 11 & 3] + sum)).value

        return x, y

    @classmethod
    def decrypt(cls, DecryData: List[int]):
        x, y = DecryData
        sum = cls.delta * 32
        for _ in range(32):
            y -= (((i32(x) << 4 ^ i32(x).urshift(5)) + x) ^ (cls.Key[(sum >> 11)] & 3 + sum)).value
            sum -= cls.delta
            x -= (((i32(y) << 4 ^ i32(y).urshift(5)) + y) ^ (cls.Key[sum & 3] + sum)).value
        return x, y


class Tea:
    @classmethod
    def decrypt(cls, msg: bytes):
        res = Base64.decode(msg)
        rounds = len(res) >> 3
        final = b""
        for i in range(rounds):
            tmp = TeaBlock.decrypt(btoi(res[i * 8 : i * 8 + 8]))
            final += itob(tmp)
        return final

    @classmethod
    def encrypt(cls, msg: bytes):
        final = b""
        rounds = len(msg) >> 3
        for i in range(rounds):
            tmp = TeaBlock.encrypt(btoi(msg[i * 8 : i * 8 + 8]))
            final += itob(tmp)

        return Base64.encode(final)


class SeqOrder:
    @classmethod
    def disorder(cls, msg: str):
        tmp = len(msg) % 16
        ch = "0abcdefghijklmnop"[tmp]
        while tmp and (16 - tmp):
            msg += ch
            tmp += 1

        keyMap = [0, 4, 8, 12, 5, 9, 13, 1, 10, 14, 2, 6, 15, 3, 7, 11]
        tmp = len(msg) >> 4

        res = ""
        for i in range(tmp):
            cut = msg[i * 16 : i * 16 + 16]
            for j in range(16):
                res += cut[keyMap[j]]

        return res

    @classmethod
    def order(cls, msg):
        keyMap = [0, 7, 10, 13, 1, 4, 11, 14, 2, 5, 8, 15, 3, 6, 9, 12]
        tmp = len(msg) >> 4
        res = ""
        for i in range(tmp):
            cut = msg[i * 16 : i * 16 + 16]
            for j in range(16):
                res += cut[keyMap[j]]
        return res


class VData:
    @classmethod
    def encrypt(cls, params: str):
        return Tea.encrypt(SeqOrder.disorder(params).encode())

    @classmethod
    def decrypt(cls, vdata: str):
        return SeqOrder.order(Tea.decrypt(vdata.encode()))
