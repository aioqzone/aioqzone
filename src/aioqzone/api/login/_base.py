import asyncio
from abc import ABC, abstractmethod
from time import time
from typing import Dict

from tylisten import Emitter

import aioqzone.message as MT
from qqqr.utils.encrypt import gtk


class Loginable(ABC):
    """Abstract class represents a login manager."""

    last_login: float = 0
    """Last login time stamp. 0 represents no login since created."""

    def __init__(self, uin: int) -> None:
        super().__init__()
        self.uin = uin
        self._cookie = {}
        self.lock = asyncio.Lock()

        self.login_success = Emitter(MT.login_success)
        self.login_failed = Emitter(MT.login_failed)

    @property
    def cookie(self) -> Dict[str, str]:
        """Cached cookie."""
        return self._cookie

    @abstractmethod
    async def _new_cookie(self) -> Dict[str, str]:
        """Subclasses *must* implement this method to return a cookie dict.

        :meta public:
        :return: cookie dict
        """
        return

    async def new_cookie(self):
        """Get a new cookie dict, which means cached cookie is not allowed.
        Generally, this will trigger a login.

        This method uses :class:`asyncio.Lock` to ensure that only one request can trigger
        an actual login at the same time, other requests will block until the first is complete
        and share the cookie from this single login.

        :return: cookie. Shouldn't be a cached one.
        """
        if self.lock.locked():
            # if there is other requests trying to update cookie, reuse the result.
            async with self.lock:
                return self.cookie
        else:
            # let the first request get result from Qzone.
            async with self.lock:
                self._cookie = await self._new_cookie()
                self.last_login = time()
                return self._cookie

    @property
    def gtk(self) -> int:
        """Calculate ``gtk`` using ``pskey`` field in the cookie.

        :return: gtk

        .. note:: ``0`` denotes no existing login.
        .. seealso:: :meth:`qqqr.utils.encrypt.gtk`
        """
        pskey = self.cookie.get("p_skey")
        if pskey is None:
            return 0
        return gtk(pskey)
