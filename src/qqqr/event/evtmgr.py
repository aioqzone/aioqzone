from typing import Any, Callable, ClassVar, Dict, Generic, List, Tuple, Type

from typing_extensions import Self

from .evt import Event, Evt


class EventManager:
    """`EventManager` is a convenient way to create/trace/manage friend classes.

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

    def __setitem__(self, event: Type[Evt], hook: Evt):
        """User can replace a hook of an :class:`EventManager` instance manually. This will not influence
        other instance of this :class:`EventManager` class.

        .. versionadded:: 0.12.2

        :meta public:
        """
        self.__hooks__[event] = hook

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
        if not issubclass(owner, EventManager):
            return
        if not "__events_mro__" in owner.__dict__:
            owner.__events_mro__ = owner.__events_mro__.copy()
        owner.__events_mro__[self.event] = (*owner.__events_mro__[self.event], self.meth)  # type: ignore
        setattr(owner, name, self.meth)
