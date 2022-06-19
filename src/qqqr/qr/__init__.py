import asyncio
import re
from random import random
from typing import Awaitable, Callable, Dict, Optional

from qqqr.qr.type import PollResp

from ..base import LoginBase, LoginSession
from ..constant import StatusCode
from ..exception import UserBreak
from ..utils.encrypt import hash33

SHOW_QR = "https://ssl.ptlogin2.qq.com/ptqrshow"
XLOGIN_URL = "https://xui.ptlogin2.qq.com/cgi-bin/xlogin"
POLL_QR = "https://ssl.ptlogin2.qq.com/ptqrlogin"
LOGIN_URL = "https://ptlogin2.qzone.qq.com/check_sig"


class QR(LoginSession):
    def __init__(
        self,
        content: bytes,
        signature: str,
        *,
        create_time: float = ...,
        expired: bool = False,
    ) -> None:
        super().__init__(create_time=create_time)
        self.png = content
        self.sig = signature
        self.expired = expired


class QRLogin(LoginBase[QR]):
    async def new(self) -> QR:
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
        r = await self.client.get(SHOW_QR, params=data)
        r.raise_for_status()
        return QR(r.content, r.cookies["qrsig"])

    async def poll(self, qr: QR) -> PollResp:
        """Poll QR status.

        :raises `aiohttp.ClientResponseError`: if response status code != 200

        :return: a poll response object
        """
        data = {
            "u1": self.proxy.s_url,
            "ptqrtoken": hash33(qr.sig),
            "ptredirect": 0,
            "h": 1,
            "t": 1,
            "g": 1,
            "from_ui": 1,
            "ptlang": 2052,
            # 'action': 3-2-1626611307380,
            # 'js_ver': 21071516,
            "js_type": 1,
            "login_sig": "",
            "pt_uistyle": 40,
            "aid": self.app.appid,
            "daid": self.app.daid,
            # 'ptdrvs': 'JIkvP2N0eJUzU3Owd7jOvAkvMctuVfODUMSPltXYZwCLh8aJ2y2hdSyFLGxMaH1U',
            # 'sid': 6703626068650368611,
            "has_onekey": 1,
        }
        r = await self.client.get(POLL_QR, params=data)
        r.raise_for_status()
        rlist = re.findall(r"'(.*?)'[,\)]", r.text)
        poll = PollResp.parse_obj(dict(zip(["code", "?", "url", "?", "msg", "my_name"], rlist)))
        if poll.code == StatusCode.Authenticated:
            qr.login_url = poll.url
        return poll

    async def _loop(
        self,
        *,
        send_callback: Callable[[bytes, int], Awaitable],
        cancel_flag: asyncio.Event,
        refresh_flag: asyncio.Event,
        refresh_times: int = 6,
        polling_freq: float = 3,
    ):
        refreshed = 0
        try:
            while refreshed < refresh_times:
                qr = await self.new()
                await send_callback(qr.png, refreshed)
                # future.set_exception(UserBreak)
                while not refresh_flag.is_set():
                    if cancel_flag.is_set():
                        raise UserBreak
                    await asyncio.sleep(polling_freq)
                    stat = await self.poll(qr)
                    if stat.code == StatusCode.Expired:
                        qr.expired = True
                        refreshed += 1
                        break
                    if stat.code == StatusCode.Authenticated:
                        return await self.login(qr)
                refresh_flag.clear()

        except (KeyboardInterrupt, asyncio.CancelledError) as e:
            raise UserBreak from e
        raise TimeoutError

    def loop(
        self,
        send_callback: Callable[[bytes, int], Awaitable],
        cancel_flag: asyncio.Event,
        refresh_flag: asyncio.Event,
        refresh_time: int = 6,
        polling_freq: float = 3,
    ):
        return asyncio.create_task(
            self._loop(
                send_callback=send_callback,
                cancel_flag=cancel_flag,
                refresh_flag=refresh_flag,
                refresh_times=refresh_time,
                polling_freq=polling_freq,
            )
        )
