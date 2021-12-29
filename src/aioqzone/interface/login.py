from abc import ABC, abstractmethod, abstractproperty

from qqqr.encrypt import gtk

from ..interface.hook import Emittable


class Loginable(ABC, Emittable):
    def __init__(self, uin: int) -> None:
        self.uin = uin

    @property
    def cookie(self):
        """Get cookie in any way. Allow cached result.

        Returns:
            int: cookie. Cached cookie is preferable.
        """
        return self.new_cookie()

    @abstractmethod
    def new_cookie(self) -> dict[str, str]:
        """Get a new cookie. Means, cached cookie is not allowed.

        Returns:
            int: cookie. Shouldn't be a cached one.
        """
        return

    @property
    def gtk(self) -> int:
        return gtk(self.cookie['p_skey'])
