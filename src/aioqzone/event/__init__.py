"aioqzone interface defination"

from qqqr.event import Emittable, Event, EventManager

from .login import LoginEvent, LoginMethod, QREvent, UPEvent

__all__ = ["Emittable", "Event", "EventManager", "LoginMethod", "LoginEvent", "QREvent", "UPEvent"]
