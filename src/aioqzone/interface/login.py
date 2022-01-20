from abc import ABC, abstractmethod, abstractproperty

from qqqr.encrypt import gtk
import asyncio

from ..interface.hook import Emittable


class Loginable(ABC, Emittable):
    def __init__(self, uin: int) -> None:
        self.uin = uin
        self.lock = asyncio.Lock()

    @abstractproperty
    def cookie(self) -> dict[str, str]:    # type: ignore
        """Get cookie in any way. Allow cached result.

        Returns:
            int: cookie. Cached cookie is preferable.
        """
        pass

    @abstractmethod
    async def _new_cookie(self) -> dict[str, str]:
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
                return await self._new_cookie()

    @property
    def gtk(self) -> int:
        return gtk(self.cookie['p_skey'])
