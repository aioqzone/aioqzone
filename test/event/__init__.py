from typing import Type

from qqqr.event import Event, sub_of


class Event2(Event):
    async def save(self, pid: int):
        pass


@sub_of(Event2)
def _sub_event2(_self, base: Type[Event2]):
    class subapp_event2(base):
        async def save(self, pid: int):
            await super().save(pid)
            _self.log.debug(f"subapp save pid={pid}")

    return subapp_event2
