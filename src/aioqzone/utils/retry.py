from abc import abstractmethod
from typing import ClassVar, Generic, Type, TypeVar

from aiohttp import ClientResponseError
from tenacity import retry_if_exception

from aioqzone.exception import QzoneError

_E = TypeVar("_E", bound=BaseException)


class RetryIfCode(retry_if_exception, Generic[_E]):
    _exc_cls: ClassVar[Type[_E]]  # type: ignore

    @classmethod
    @abstractmethod
    def get_code(cls, exc: _E) -> int: ...

    def __init__(self, *code: int) -> None:
        super().__init__(lambda exc: isinstance(exc, self._exc_cls) and self.get_code(exc) in code)


class retry_if_status(RetryIfCode[ClientResponseError]):
    _exc_cls = ClientResponseError

    @classmethod
    def get_code(cls, exc: ClientResponseError) -> int:
        return exc.status


class retry_if_qzone_code(RetryIfCode[QzoneError]):
    _exc_cls = QzoneError

    @classmethod
    def get_code(cls, exc: QzoneError) -> int:
        return exc.code
