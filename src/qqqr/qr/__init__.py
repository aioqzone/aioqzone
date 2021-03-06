import asyncio
import re
from dataclasses import dataclass
from random import random

import httpx

from qqqr.qr.type import PollResp

from ..base import LoginBase, LoginSession
from ..constant import StatusCode
from ..event import Emittable
from ..event.login import QrEvent
from ..exception import UserBreak
from ..utils.daug import du
from ..utils.encrypt import hash33

SHOW_QR = "https://ssl.ptlogin2.qq.com/ptqrshow"
POLL_QR = "https://ssl.ptlogin2.qq.com/ptqrlogin"
LOGIN_URL = "https://ptlogin2.qzone.qq.com/check_sig"


@dataclass(unsafe_hash=True)
class QR:
    png: bytes
    sig: str
    expired: bool = False


class QrSession(LoginSession):
    def __init__(self, first_qr: QR, *, create_time: float = ..., refresh_times: int = 0) -> None:
        super().__init__(create_time=create_time)
        self.refreshed = refresh_times
        self.current_qr = first_qr

    def new_qr(self, qr: QR):
        self.current_qr.expired = True
        self.current_qr = qr
        self.refreshed += 1


class QrLogin(LoginBase[QrSession], Emittable[QrEvent]):
    async def new(self) -> QrSession:
        return QrSession(await self.show())

    async def show(self) -> QR:
        data = {
            "appid": self.app.appid,
            "e": 2,
            "l": "M",
            "s": 3,
            "d": 72,
            "v": 4,
            "t": random(),
            "daid": self.app.daid,
            "pt_3rd_aid": 0,
        }
        async with await self.client.get(SHOW_QR, params=data) as r:
            return QR(r.content, r.cookies["qrsig"])

    async def poll(self, sess: QrSession) -> PollResp:
        """Poll QR status.

        :raises `httpx.HTTPStatusError`: if response status code != 200

        :return: a poll response object
        """
        const = {
            "h": 1,
            "t": 1,
            "g": 1,
            "from_ui": 1,
            "ptredirect": 0,
            "ptlang": 2052,
            "js_type": 1,
            "pt_uistyle": 40,
            "has_onekey": 1,
        }
        data = {
            "u1": self.proxy.s_url,
            "ptqrtoken": hash33(sess.current_qr.sig),
            # 'js_ver': 21071516,
            "login_sig": "",
            "aid": self.app.appid,
            "daid": self.app.daid,
        }

        async with await self.client.get(POLL_QR, params=du(data, const)) as r:
            r.raise_for_status()
            rl = re.findall(r"'(.*?)'[,\)]", r.text)

        resp = PollResp.parse_obj(dict(zip(["code", "", "url", "", "msg", "nickname"], rl)))

        return resp

    async def _loop(
        self,
        *,
        refresh_times: int = 6,
        polling_freq: float = 3,
    ):
        expired = 0
        refresh_flag = self.hook.refresh_flag
        cancel_flag = self.hook.cancel_flag
        sess = await self.new()

        while expired < refresh_times:
            await self.hook.QrFetched(sess.current_qr.png, expired)
            # future.set_exception(UserBreak)
            while not refresh_flag.is_set():
                if cancel_flag.is_set():
                    raise UserBreak
                await asyncio.sleep(polling_freq)
                stat = await self.poll(sess)
                if stat.code == StatusCode.Expired:
                    expired += 1
                    break
                elif stat.code == StatusCode.Authenticated:
                    sess.login_url = str(stat.url)
                    return await self._get_login_url(sess)
            sess.new_qr(await self.show())
            refresh_flag.clear()

        raise TimeoutError

    async def login(self, refresh_time: int = 6, polling_freq: float = 3):
        try:
            return await self._loop(refresh_times=refresh_time, polling_freq=polling_freq)
        except (KeyboardInterrupt, asyncio.CancelledError) as e:
            raise UserBreak from e
