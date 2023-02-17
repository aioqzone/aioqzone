import asyncio
from typing import Optional

from . import Event


class QrEvent(Event):
    def __init__(self) -> None:
        super().__init__()
        self.cancel_flag = asyncio.Event()
        self.refresh_flag = asyncio.Event()

    async def QrFetched(self, png: bytes, times: int):
        """Will be called on new QR code bytes are fetched. Means this will be triggered on:

        1. QR login start
        2. QR expired
        3. QR is refreshed

        :param png: QR bytes (png format)
        :param times: QR refresh times in this session
        """
        pass

    async def QrCancelled(self):
        """Will be called when QR login is cancelled.

        .. versionadded:: 0.11.1
        """
        pass


class UpEvent(Event):
    async def GetSmsCode(self, phone: str, nickname: str) -> Optional[str]:
        """Get dynamic code from sms. A sms with dynamic code will be sent to user's mobile before
        this event is emitted. This hook should return that code (from user input, etc.).

        :return: dynamic code in sms

        .. versionadded:: 0.9.0
        """
        pass
