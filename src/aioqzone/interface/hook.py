"""
Define hooks that can trigger user actions.
"""

import asyncio
from collections import defaultdict
from typing import Awaitable, Callable, Generic, Optional, TypeVar


class Event:
    """Base class for event system."""
    pass


Evt = TypeVar('Evt', bound=Event)
T = TypeVar('T')


class NullEvent(Event):
    """For debugging"""
    __slots__ = ()

    def __getattribute__(self, __name: str):
        assert False, "call `o.register_hook` before accessing o.hook"


class Emittable(Generic[Evt]):
    """An object has some event to trigger.
    """
    hook: Evt = NullEvent()    # type: ignore
    _tasks: dict[str, set[asyncio.Task]]

    def __init__(self) -> None:
        self._tasks = defaultdict(set)

    def register_hook(self, hook: Evt):
        assert not isinstance(hook, NullEvent)
        self.hook = hook

    def add_hook_ref(self, hook_cls: str, coro: Awaitable[T]) -> asyncio.Task[T]:
        task = asyncio.create_task(coro)
        self._tasks[hook_cls].add(task)
        task.add_done_callback(lambda t: self._tasks[hook_cls].remove(t))
        return task

    async def wait(self, *hook_cls: str, timeout: float = None):
        s = set()
        for i in hook_cls:
            s |= self._tasks[i]
        if not s: return set(), set()
        r = await asyncio.wait(s, timeout=timeout)
        if timeout is None and any(self._tasks[i] for i in hook_cls):
            # await potential new tasks in these sets, only if no timeout.
            return self.wait(*hook_cls)
        return r

    def clear(self, *hook_cls: str, cancel: bool = True):
        """Clear the given task sets

        :param hook_cls: task class names
        :param cancel: Cancel the task if a set is not empty, defaults to True. Else will just clear the ref.
        """
        for i in hook_cls:
            if (s := self._tasks[i]) and not cancel:
                s.clear()
                continue
            while s:
                t = s.pop()
                t.cancel()


class LoginEvent(Event):
    """Defines usual events happens during login."""
    async def LoginFailed(self, msg: str = None):
        """Will be emitted on login failed.

        .. note::
            This event will be triggered on every failure of login attempt.
            Means that logic in this event may be executed multiple times.

        :param msg: Err msg, defaults to None.
        """
        pass

    async def LoginSuccess(self):
        """Will be emitted after login success. Low prior, scheduled by loop instead of awaiting.
        """
        pass


class QREvent(LoginEvent):
    """Defines usual events happens during QR login."""

    cancel: Optional[Callable[[], Awaitable[None]]]
    resend: Optional[Callable[[], Awaitable[None]]]

    async def QrFetched(self, png: bytes, renew: bool = False):
        """Will be called on new QR code bytes are fetched. Means this will be triggered on:
        1. QR login start
        2. QR expired
        3. QR is refreshed

        :param png: QR bytes (png format)
        :param renew: this QR is a refreshed QR, defaults to False

        .. warning::
            Develpers had better not rely on the parameter :param renew:.
            Maintain the state by yourself is not difficult.
        """
        pass

    async def QrFailed(self, msg: str = None):
        """QR login failed.

        .. note: This event should always be called before :meth:`.LoginEvent.LoginFailed`.

        :param msg: Error msg, defaults to None.
        """
        pass

    async def QrSucceess(self):
        """QR login success.
        """
        pass
