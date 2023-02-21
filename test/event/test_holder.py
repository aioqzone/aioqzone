from qqqr.event import EventManager
from qqqr.event.login import QrEvent, UpEvent


class LEM_sub1(EventManager[QrEvent, UpEvent]):
    def _sub_qrevent(self, base):
        class inner_qr(base):
            pass

        print(self.__class__, base)
        return inner_qr


class LEM_sub2(LEM_sub1):
    def _sub_qrevent(self, base):
        base = super()._sub_qrevent(base)

        class inner_qr(base):
            pass

        print(self.__class__, base)
        return inner_qr


def test_sub():
    r = LEM_sub1()
    assert (
        f"{LEM_sub1._sub_qrevent.__qualname__}.<locals>.inner_qr" in r.sub_of(QrEvent).__qualname__
    )
    r = LEM_sub2()
    assert (
        f"{LEM_sub2._sub_qrevent.__qualname__}.<locals>.inner_qr" in r.sub_of(QrEvent).__qualname__
    )
