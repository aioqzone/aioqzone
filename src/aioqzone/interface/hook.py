"""
Define hooks that can trigger user actions.
"""

from typing import Awaitable, Callable, Optional


class Event:
    """Base class for event system."""
    pass


class NullEvent(Event):
    """For debugging"""
    __slots__ = ()

    def __getattribute__(self, __name: str):
        assert False, "call `o.register_hook` before accessing o.hook"


class Emittable:
    """An object has some event to trigger.
    """
    hook: Event = NullEvent()

    def register_hook(self, hook: 'Event'):
        assert not isinstance(hook, NullEvent)
        self.hook = hook


class QREvent(Event):
    """Defines usual events happens during QR login."""

    cancel: Optional[Callable[[], Awaitable[None]]]
    resend: Optional[Callable[[], Awaitable[None]]]

    async def QrFetched(self, png: bytes, renew: bool = False):
        """Will be called on new QR code bytes are fetched. Means this will be triggered on:
        1. QR login start
        2. QR expired
        3. QR is refreshed

        Args:
            png (bytes): QR bytes (png format)
            renew (bool): this QR is a refreshed QR.
        """
        pass

    async def QrFailed(self, msg: str = None):
        """QR login failed.
        NOTE: Always be called before `LoginEvent.LoginFailed`.

        Args:
            msg (str, optional): Error msg. Defaults to None.
        """
        pass

    async def QrSucceess(self):
        """QR login success.
        """
        pass


class LoginEvent(Event):
    """Defines usual events happens during login."""
    async def LoginFailed(self, msg: str = None):
        """Will be emitted on login failed.
        NOTE: This event will be triggered on every failure of login attempt.
        Means that logic in this event may be executed multiple times.

        Args:
            msg (str, optional): Err msg. Defaults to None.
        """
        pass

    async def LoginSuccess(self):
        """Will be emitted after login success. Low prior, scheduled by loop instead of awaiting.
        """
        pass
