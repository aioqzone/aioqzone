import asyncio
from abc import ABC, abstractmethod
from time import time
from typing import Dict, Optional

from tylisten import FutureStore

import aioqzone.message as MT
from qqqr.utils.encrypt import gtk


class Loginable(ABC):
    """Abstract class represents a login manager."""

    last_login: float = 0
    """Last login time stamp. 0 represents no login since created."""

    def __init__(self, uin: int, ch_login_notify: Optional[FutureStore] = None) -> None:
        super().__init__()
        self.uin = uin
        self.cookie: Dict[str, str] = {}
        """Cached cookie."""
        self.lock = asyncio.Lock()
        self.ch_login_notify = ch_login_notify or FutureStore()

        self.login_success = MT.login_success()
        self.login_failed = MT.login_failed()

    @abstractmethod
    async def _new_cookie(self) -> Dict[str, str]:
        """Subclasses *must* implement this method to return a cookie dict.

        :meta public:
        :return: cookie dict
        """
        return

    async def new_cookie(self) -> bool:
        """Get a new cookie dict, which means cached cookie is not allowed.
        Generally, this will trigger a login.

        This method uses :class:`asyncio.Lock` to ensure that only one request can trigger
        an actual login at the same time, other requests will block until the first is complete
        and share the cookie from this single login.

        :return: cookie. Shouldn't be a cached one.
        """
        if self.lock.locked():
            last_gtk = self.gtk
            async with self.lock:
                return last_gtk == self.gtk
        else:
            # let the first request get result from Qzone.
            async with self.lock:
                try:
                    self.cookie = await self._new_cookie()
                except BaseException as e:
                    self.ch_login_notify.add_awaitable(self.login_failed.emit(self.uin, e))
                    return False
                else:
                    self.ch_login_notify.add_awaitable(self.login_success.emit(self.uin))
                    return True
                finally:
                    self.last_login = time()

    @property
    def gtk(self) -> int:
        """Calculate g_token(gtk) using ``p_skey`` or ``skey`` field in the cookie.

        :return: g_token

        .. note:: ``0`` denotes no existing login.
        .. seealso:: :meth:`qqqr.utils.encrypt.gtk`
        """
        skey = self.cookie.get("p_skey") or self.cookie.get("skey")
        if skey is None:
            return 0
        return gtk(skey)
