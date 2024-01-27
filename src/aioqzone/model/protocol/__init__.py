"""This module defines types that are used internally by aioqzone and its plugins.
These types are not designed to represent responses from Qzone.
"""

from pydantic import BaseModel

from .config import *
from .entity import *


class PersudoCurkey(str):
    def __new__(cls, uin: int, abstime: int):
        return str.__new__(cls, cls.build(uin, abstime))

    def __init__(self, uin: int, abstime: int) -> None:
        super().__init__()
        self.uin = uin
        self.abstime = abstime

    @classmethod
    def build(cls, uin: int, abstime: int):
        return str(uin).rjust(12, "0") + str(abstime).rjust(12, "0")

    @classmethod
    def from_str(cls, curkey: str):
        uin = curkey[:12]
        abstime = curkey[12:]
        uin = int(uin.lstrip("0"))
        abstime = int(abstime.lstrip("0"))
        return cls(uin=uin, abstime=abstime)


class AlbumData(BaseModel):
    topicid: str
    pickey: str
    hostuin: int


# LikeData is not a response of any API. It's just a type def.
class LikeData(BaseModel):
    unikey: str
    curkey: str
    appid: int
    typeid: int
    fid: str
    abstime: int

    @staticmethod
    def persudo_curkey(uin: int, abstime: int):
        return str(PersudoCurkey(uin, abstime))

    @staticmethod
    def persudo_unikey(appid: int, uin: int, fid: str):
        if appid == 311:
            return f"https://user.qzone.qq.com/{uin}/mood/{fid}"

        raise ValueError(appid)
