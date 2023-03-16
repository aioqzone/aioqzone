import pytest

from aioqzone.exception import QzoneError
from aioqzone.utils.catch import QzoneErrorDispatch


class mock_error(BaseException):
    def __init__(self, code: int) -> None:
        self.code = code
        super().__init__(code)


def test_dispatch():
    r = []
    e = QzoneErrorDispatch()
    e.dispatch(-3000, dispatcher=lambda e: r.clear())
    e.dispatch(-3001, -3002, dispatcher=lambda e: r.append(e.code))

    with e:
        raise QzoneError(-3000)
    with e:
        raise QzoneError(-3001)
    with e:
        raise QzoneError(-3002)

    with e, pytest.raises(mock_error):
        raise mock_error(-3000)

    assert r == [-3001, -3002]


def test_suppress():
    e = QzoneErrorDispatch()
    e.dispatch(-3000, suppress=False)
    e.dispatch(-3001, -3002, suppress=lambda e: e.code == -3002)

    with e, pytest.raises(QzoneError):
        raise QzoneError(-3000)
    with e, pytest.raises(QzoneError):
        raise QzoneError(-3001)
    with e:
        raise QzoneError(-3002)
