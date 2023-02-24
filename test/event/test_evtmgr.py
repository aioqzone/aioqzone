import logging
from typing import Type

from qqqr.event import Event, EventManager, sub_of

from . import Event2


class Event1(Event):
    async def notify(self):
        pass


class BaseApp(EventManager[Event1, Event2]):
    def __init__(self, pos_arg: int) -> None:
        super().__init__()
        self.log = logging.getLogger(__name__)
        assert isinstance(pos_arg, int)

    @sub_of(Event1)
    def _sub_event1(_self, base: Type[Event1]):
        class baseapp_event1(base):
            async def notify(self):
                await super().notify()
                _self.log.debug("baseapp notify")

        return baseapp_event1

    @sub_of(Event2)
    def _sub_event2(_self, base: Type[Event2]):
        class baseapp_event2(base):
            async def save(self, pid: int):
                await super().save(pid)
                _self.log.debug(f"baseapp save pid={pid}")

        return baseapp_event2


class SubApp(BaseApp):
    def __init__(self, *, kw_arg: int) -> None:
        super().__init__(kw_arg)
        self.log = logging.getLogger(__name__)

    @sub_of(Event1)
    def _sub_event1(_self, base: Type[Event1]):
        class subapp_event1(base):
            async def notify(self):
                await super().notify()
                _self.log.debug("subapp notify")

        return subapp_event1

    from . import _sub_event2


class StandAloneEvent2(Event2):
    async def save(self, pid: int):
        return pid + 10


def test_baseapp():
    app = BaseApp(1)
    assert (
        app.inst_of(Event1).__class__.__name__
        == (BaseApp.__name__ + "_" + Event1.__name__).lower()
    )
    assert (
        app.inst_of(Event2).__class__.__name__
        == (BaseApp.__name__ + "_" + Event2.__name__).lower()
    )
    assert app[Event1].__class__.__name__ == (BaseApp.__name__ + "_" + Event1.__name__).lower()
    assert app[Event2].__class__.__name__ == (BaseApp.__name__ + "_" + Event2.__name__).lower()


def test_subapp():
    app = SubApp(kw_arg=2)
    assert (
        app.inst_of(Event1).__class__.__name__ == (SubApp.__name__ + "_" + Event1.__name__).lower()
    )
    assert (
        app.inst_of(Event2).__class__.__name__ == (SubApp.__name__ + "_" + Event2.__name__).lower()
    )
    assert app[Event1].__class__.__name__ == (SubApp.__name__ + "_" + Event1.__name__).lower()
    assert app[Event2].__class__.__name__ == (SubApp.__name__ + "_" + Event2.__name__).lower()


def test_standalone():
    app = SubApp(kw_arg=2)
    app[Event2] = StandAloneEvent2()
    assert app.inst_of(Event2).__class__.__name__ == StandAloneEvent2.__name__

    app = SubApp(kw_arg=2)
    assert (
        app.inst_of(Event2).__class__.__name__ == (SubApp.__name__ + "_" + Event2.__name__).lower()
    )
