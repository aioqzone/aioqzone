import asyncio
from abc import ABC, abstractmethod
from time import time
from typing import Dict

from qqqr.utils.encrypt import gtk


class Loginable(ABC):
    """Abstract class represents a login manager.
    It is a :class:`Emittable` class which can emit :class:`LoginEvent`.
    """

    last_login: float = 0
    """Last login time stamp. 0 represents no login since created."""

    def __init__(self, uin: int) -> None:
        super().__init__()
        self.uin = uin
        self._cookie = {}
        self.lock = asyncio.Lock()

    @property
    def cookie(self) -> Dict[str, str]:
        """Get a cookie dict using any method. Allows cached cookie.

        :return: cookie. Cached cookie is preferable.
        """
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
        """Calculate ``gtk`` using ``pskey`` filed in the cookie.

        :return: gtk

        .. note:: ``0`` denotes no existing login.
        .. seealso:: :meth:`qqqr.utils.encrypt.gtk`
        """
        pskey = self.cookie.get("p_skey")
        if pskey is None:
            return 0
        return gtk(pskey)
