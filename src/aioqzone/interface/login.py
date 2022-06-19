import asyncio
from abc import ABC, abstractmethod
from enum import Enum
from time import time
from typing import Dict, Optional, TypeVar

from qqqr.event import Emittable, Event
from qqqr.event.login import QrEvent as _qrevt
from qqqr.event.login import UpEvent as _upevt
from qqqr.utils.encrypt import gtk


class LoginMethod(str, Enum):
    qr = "qr"
    up = "up"


class LoginEvent(Event):
    """Defines usual events happens during login."""

    async def LoginFailed(self, meth: LoginMethod, msg: Optional[str] = None):
        """Will be emitted on login failed.

        :param meth: indicate what login method this login attempt used
        :param msg: Err msg, defaults to None.
        """
        pass

    async def LoginSuccess(self, meth: LoginMethod):
        """Will be emitted after login success.

        :param meth: indicate what login method this login attempt used
        """
        pass


LgEvt = TypeVar("LgEvt", bound=LoginEvent)


class QREvent(LoginEvent, _qrevt):
    """Defines usual events happens during QR login."""

    pass


class UPEvent(LoginEvent, _upevt):
    """Defines usual events happens during password login."""

    pass


class Loginable(ABC, Emittable[LgEvt]):
    last_login: float = 0

    def __init__(self, uin: int) -> None:
        super().__init__()
        self.uin = uin
        self._cookie = {}
        self.lock = asyncio.Lock()

    @property
    def cookie(self) -> Dict[str, str]:  # type: ignore
        """Get cookie in any way. Allow cached result.

        Returns:
            int: cookie. Cached cookie is preferable.
        """
        return self._cookie

    @abstractmethod
    async def _new_cookie(self) -> Dict[str, str]:
        return

    async def new_cookie(self):
        """Get a new cookie. Means, cached cookie is not allowed.

        Returns:
            int: cookie. Shouldn't be a cached one.
        """
        if self.lock.locked():
            # if there is coro. updating cookie, then wait for its result.
            async with self.lock:
                return self.cookie
        else:
            # let the first coro. get result from Qzone.
            async with self.lock:
                self._cookie = await self._new_cookie()
                self.last_login = time()
                return self._cookie

    @property
    def gtk(self) -> int:
        """cal gtk from pskey.

        Returns:
            int: gtk. NOTE: 0 denotes no-login.
        """
        pskey = self.cookie.get("p_skey")
        if pskey is None:
            return 0
        return gtk(pskey)
