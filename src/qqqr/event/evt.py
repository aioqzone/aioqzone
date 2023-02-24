"""
QQQR event and event holders.
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
    Generator,
    Generic,
    Optional,
    Set,
    Tuple,
    TypeVar,
    Union,
    final,
)

from typing_extensions import ParamSpec

from qqqr.exception import HookError

T = TypeVar("T")
P = ParamSpec("P")


class Event:
    """Base class for event system."""


Evt = TypeVar("Evt", bound=Event)


class NullEvent(Event):
    """For debugging"""

    __slots__ = ()

    def __getattribute__(self, __name: str):
        try:
            return super().__getattribute__(__name)
        except AttributeError:
            raise AttributeError(__name, "call `o.register_hook` before accessing `o.hook`")

    def __repr__(self) -> str:
        return "NullEvent()"


class Tasksets:
    """An object has some event to trigger."""

    _tasks: Dict[str, Set[asyncio.Task]]

    def __init__(self) -> None:
        super().__init__()
        self._tasks = defaultdict(set)

    def add_hook_ref(self, hook_cls: str, coro):
        # type: (str, Coroutine[Any, Any, T] | Generator[Any, Any, T] | asyncio.Task[T]) -> asyncio.Task[T]
        # NOTE: asyncio.Task becomes generic since py39
        """Add an awaitable into the given taskset.

        :param hook_cls: taskset key
        :param coro: the awaitable (`Coroutine`, `Generator` and `~asyncio.Task` supported)
        """
        if isinstance(coro, (Coroutine, Generator)):
            task = asyncio.create_task(coro)
        elif isinstance(coro, asyncio.Task):
            task = coro
        else:
            raise TypeError(coro)
        self._tasks[hook_cls].add(task)
        task.add_done_callback(lambda t: self._tasks[hook_cls].remove(t))
        return task

    @final
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
            r2 = await self.wait(*hook_cls)
            return set(chain(r[0], r2[0])), set()
        return r

    @final
    def clear(self, *hook_cls: str, cancel: bool = True):
        """Clear the given task sets.

        :param hook_cls: task class names. **If not given, all tasks will be cleared.**
        :param cancel: Cancel the task if a set is not empty, defaults to True. Else will just clear the ref.
        """
        if not hook_cls:
            hook_cls = tuple(self._tasks.keys())
        for i in hook_cls:
            s = self._tasks[i]
            if s and not cancel:
                # dangerous
                s.clear()
                continue
            for t in s:
                t.cancel()  # done callback will remove the task from this set


class Emittable(Generic[Evt], Tasksets):
    hook: Union[Evt, NullEvent] = NullEvent()

    def register_hook(self, hook: Evt):
        assert not isinstance(hook, NullEvent)
        self.hook = hook


def hook_guard(hook: Callable[P, Awaitable[T]]) -> Callable[P, Coroutine[Any, Any, T]]:
    """This can be used as a decorator to ensure a hook can only raise :exc:`HookError`.

    ..note:: If the hook is already wrapped, it will be returned as is.
    """
    if hasattr(hook, "__hook_guard__"):
        return hook  # type: ignore

    @wraps(hook)
    async def guard_wrapper(*args: P.args, **kwds: P.kwargs) -> T:
        try:
            return await hook(*args, **kwds)
        except (BaseException, Exception) as e:  # Exception to catch ExceptionGroup
            raise HookError(hook) from e

    setattr(guard_wrapper, "__hook_guard__", True)
    return guard_wrapper
