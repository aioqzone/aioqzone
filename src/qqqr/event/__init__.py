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
    ClassVar,
    Coroutine,
    Dict,
    Generator,
    Generic,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from typing_extensions import ParamSpec, Self, final

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


class EventManager:
    """EventManager is a convenient way to create/trace/manage friend classes.

    .. versionchanged:: 0.12.0
    """

    __events_mro__: ClassVar[
        Dict[Type[Event], Tuple[Callable[[Self, Type[Event]], Type[Event]], ...]]
    ]
    """Keys as base classes, values as hook classes."""
    __hooks__: Dict[Type[Event], Event]
    """Keys as base classes, values as hook instances."""

    def type_of(self, event: Type[Evt]) -> Type[Evt]:
        """Get current hook class by the given type.

        .. versionadded:: 0.12.0
        """
        base: Type[Evt] = event
        for level in self.__events_mro__[event]:
            base = level(self, base)  # type: ignore
        return base

    def inst_of(self, event: Type[Evt], *args, **kwds) -> Evt:
        """A helper function that initiate a hook with given args.

        .. versionadded:: 0.12.0
        """
        if event in self.__hooks__:
            return self[event]

        self.__hooks__[event] = o = self.type_of(event)(*args, **kwds)
        return o

    def __getitem__(self, event: Type[Evt]) -> Evt:
        return self.__hooks__[event]  # type: ignore

    def __repr__(self) -> str:
        events = [c.__name__ for c in self.__events_mro__.keys()]
        return f"<EventManager {events}>"

    def __class_getitem__(cls, events: List[Type[Event]]):
        """Factory. Create a EventManager class of the given events.

        :meta public:
        """

        name = "evtmgr_" + "_".join(
            i.__name__.lower() for i in sorted(events, key=lambda c: c.__name__)
        )
        cls = type(name, (cls,), dict(__events_mro__={k: () for k in events}))
        return cls

    def __new__(cls, *_, **__):
        self = super().__new__(cls)
        self.__hooks__ = {}
        return self


class sub_of(Generic[Evt]):
    """Add a hook class scope.

    .. code-block:: python
        :linenos:
        :caption: Example

        class App(EventManager[Event1, Event2]):
            @sub_of(Event1)
            def _sub_event1(self, base):
                class app_event1(base): ...
                return app_event1
    """

    def __init__(self, event: Type[Evt]) -> None:
        self.event = event

    def __call__(self, meth: Callable[[Any, Type[Evt]], Type[Evt]]):
        self.meth = meth
        return self

    def __set_name__(self, owner: Type[EventManager], name):
        if not "__events_mro__" in owner.__dict__:
            owner.__events_mro__ = owner.__events_mro__.copy()
        owner.__events_mro__[self.event] = (*owner.__events_mro__[self.event], self.meth)  # type: ignore
        setattr(owner, name, self.meth)


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
