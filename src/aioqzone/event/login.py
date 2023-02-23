from enum import Enum
from typing import Dict, Optional, TypeVar

from qqqr.event import Event
from qqqr.event.login import QrEvent as _qrevt
from qqqr.event.login import UpEvent as _upevt


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


class QREvent(LoginEvent, _qrevt):
    """Defines usual events happens during QR login."""

    pass


class UPEvent(LoginEvent, _upevt):
    """Defines usual events happens during password login."""

    pass
