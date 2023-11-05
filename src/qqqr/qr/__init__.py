import asyncio
import logging
import re
import typing as t
from dataclasses import dataclass
from random import random

import qqqr.message as MT
from qqqr.base import LoginBase, LoginSession
from qqqr.constant import StatusCode
from qqqr.exception import UserBreak, UserTimeout
from qqqr.qr.type import PollResp
from qqqr.utils.encrypt import hash33

log = logging.getLogger(__name__)

SHOW_QR = "https://ssl.ptlogin2.qq.com/ptqrshow"
POLL_QR = "https://ssl.ptlogin2.qq.com/ptqrlogin"
LOGIN_URL = "https://ptlogin2.qzone.qq.com/check_sig"


@dataclass(unsafe_hash=True)
class QR:
    png: bytes
    sig: str
    expired: bool = False


class QrSession(LoginSession):
    def __init__(
        self, first_qr: QR, *, create_time: t.Optional[float] = None, refresh_times: int = 0
    ) -> None:
        super().__init__(create_time=create_time)
        self.refreshed = refresh_times
        self.current_qr = first_qr

    def new_qr(self, qr: QR):
        self.current_qr.expired = True
        self.current_qr = qr
        self.refreshed += 1


class _QrHookMixin:
    def __init__(self, *args, **kwds) -> None:
        super().__init__(*args, **kwds)
        self.qr_fetched = MT.qr_fetched()
        self.qr_cancelled = MT.qr_cancelled()
        self.cancel = asyncio.Event()
        self.refresh = asyncio.Event()


class QrLogin(_QrHookMixin, LoginBase[QrSession]):
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
        async with self.client.get(SHOW_QR, params=data) as r:
            return QR(await r.content.read(), r.cookies["qrsig"].value)

    async def poll(self, sess: QrSession) -> PollResp:
        """Poll QR status.

        :raise `httpx.HTTPStatusError`: if response status code != 200

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

        async with self.client.get(POLL_QR, params=data.update(const) or data) as r:
            r.raise_for_status()
            rl = re.findall(r"'(.*?)'[,\)]", await r.text())

        resp = PollResp.model_validate(dict(zip(["code", "", "url", "", "msg", "nickname"], rl)))
        log.debug(resp)
        return resp

    async def login(
        self,
        *,
        refresh_times: int = 6,
        poll_freq: float = 3,
    ):
        """Loop until cookie is returned or max `refresh_times` exceeds.
        - This method will emit :meth:`QrEvent.QrFetched` event if a new qrcode is fetched.
        - If qr is not scanned after `refresh_times`, it will raise :exc:`asyncio.TimeoutError`.
        - If :obj:`QrEvent.refresh_flag` is set, it will refresh qrcode at once without increasing expire counter.
        - If :obj:`QrEvent.cancel_flag` is set, it will raise :exc:`UserBreak` before next polling.

        :meta public:
        :param refresh_times: max qr expire times.
        :param poll_freq: interval between two status polling, in seconds, default as 3.

        :raise `UserTimeout`: if qr is not scanned after `refresh_times` expires.
        :raise `UserBreak`: if :obj:`QrEvent.cancel_flag` is set.
        """
        self.refresh.clear()
        self.cancel.clear()

        cnt_expire = 0
        renew = False
        sess = await self.new()

        while cnt_expire < refresh_times:
            # BUG: should we wrap hook errors here?
            await self.qr_fetched.emit(png=sess.current_qr.png, times=cnt_expire, qr_renew=renew)
            renew = False

            while not self.refresh.is_set():
                if self.cancel.is_set():
                    await self.qr_cancelled.emit()
                    raise UserBreak

                await asyncio.sleep(poll_freq)
                stat = await self.poll(sess)
                if stat.code == StatusCode.Expired:
                    cnt_expire += 1
                    break
                elif stat.code == StatusCode.Authenticated:
                    sess.login_url = str(stat.url)
                    return await self._get_login_url(sess)
            else:
                self.refresh.clear()
                renew = True

            sess.new_qr(await self.show())

        raise UserTimeout("qrscan")
