"""
QQQR event system.
"""

import asyncio
from collections import defaultdict
from functools import wraps
from itertools import chain
from typing import (
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Dict,
    Generic,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec

from qqqr.exception import HookError

T = TypeVar("T")
P = ParamSpec("P")


class Event(Generic[T]):
    """Base class for event system.

    .. code-block:: python
        :linenos:
        :caption: my_events.py

        class Event1(Event):
            async def database_query(self, pid: int) -> str:
                pass

    .. code-block:: python
        :linenos:
        :caption: my_hooks.py

        from typing import TYPE_CHECKING

        if TYPE_CHECKING:
            from app import AppClass    # to avoid circular import

        class Event1Hook(Event1["AppClass"]):
            async def database_query(self, pid: int) -> str:
                return await self.scope.db.query(pid) or ""   # typing of scope is ok

    .. code-block:: python
        :linenos:
        :caption: service.py

        from my_event import Event1

        class Service(Emittable[Event1]):
            async def run(self):
                ...
                name = await self.hook.database_query(pid)
                ...

    .. code-block:: python
        :linenos:
        :caption: app.py

        from my_hooks import Event1Hook
        from service import Service

        class AppClass:
            db: Database

            def __init__(self):
                self.event1_hook = Event1Hook()
                self.event1_hook.link_to_scope(self)
                self.service = Service()
                self.service.register_hook(self.event1_hook)
    """

    scope: T
    """Access to a larger scope. This may allow hooks to achieve more functions.

    .. warning:: Can only be access after calling `link_to_scope`."""

    def link_to_scope(self, scope: T):
        """Set the :obj:`scope`."""
        self.scope = scope


Evt = TypeVar("Evt", bound=Event)


class NullEvent(Event):
    """For debugging"""

    __slots__ = ()

    def __getattribute__(self, __name: str):
        try:
            return super().__getattribute__(__name)
        except AttributeError:
            raise AssertionError("call `o.register_hook` before accessing `o.hook`")

    def __repr__(self) -> str:
        return "NullEvent()"


class Emittable(Generic[Evt]):
    """An object has some event to trigger."""

    hook: Union[Evt, NullEvent] = NullEvent()
    _tasks: Dict[str, Set[asyncio.Task]]
    _loop: asyncio.AbstractEventLoop

    def __init__(self) -> None:
        self._tasks = defaultdict(set)

    def register_hook(self, hook: Evt):
        assert not isinstance(hook, NullEvent)
        self.hook = hook

    def add_hook_ref(self, hook_cls, coro):
        # type: (str, Coroutine[Any, Any, T]) -> asyncio.Task[T]
        # NOTE: asyncio.Task becomes generic since py39
        task = asyncio.create_task(coro)
        self._tasks[hook_cls].add(task)
        task.add_done_callback(lambda t: self._tasks[hook_cls].remove(t))
        return task

    async def wait(
        self,
        *hook_cls: str,
        timeout: Optional[float] = None,
    ) -> Tuple[Set[asyncio.Task], Set[asyncio.Task]]:
        """Wait for all task in the specific task set(s).

        :param timeout: timeout, defaults to None
        :type timeout: float, optional
        :return: done, pending

        .. note::
            If `timeout` is None, this method will loop until all tasks in the set(s) are done.
            That means if other tasks are added during awaiting, the added task will be waited as well.

        .. seealso:: :meth:`asyncio.wait`
        """
        s: Set[asyncio.Task] = set()
        for i in hook_cls:
            s.update(self._tasks[i])
        if not s:
            return set(), set()
        r = await asyncio.wait(s, timeout=timeout)
        if timeout is None and any(self._tasks[i] for i in hook_cls):
            # await potential new tasks in these sets, only if no timeout.
            r2 = await Emittable.wait(self, *hook_cls)
            return set(chain(r[0], r2[0])), set()
        return r

    def clear(self, *hook_cls: str, cancel: bool = True):
        """Clear the given task sets

        :param hook_cls: task class names
        :param cancel: Cancel the task if a set is not empty, defaults to True. Else will just clear the ref.
        """
        for i in hook_cls:
            s = self._tasks[i]
            if s and not cancel:
                # dangerous
                s.clear()
                continue
            for t in s:
                t.cancel()  # done callback will remove the task from this set


def hook_guard(hook: Callable[P, Awaitable[T]]) -> Callable[P, Coroutine[Any, Any, T]]:
    """This can be used as a decorator to ensure a hook can only raise :exc:`HookError`."""
    assert not hasattr(hook, "__hook_guard__")

    @wraps(hook)
    async def guard_wrapper(*args: P.args, **kwds: P.kwargs) -> T:
        try:
            return await hook(*args, **kwds)
        except (BaseException, Exception) as e:  # Exception to catch ExceptionGroup
            raise HookError(hook) from e

    setattr(guard_wrapper, "__hook_guard__", True)
    return guard_wrapper
