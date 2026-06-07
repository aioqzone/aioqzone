"""Tenacity retry predicates for Qzone API errors.

Defines :class:`RetryIfCode` ABC and concrete predicates
:func:`retry_if_status` (HTTP errors) and :func:`retry_if_qzone_code`
(Qzone business errors).
"""

from abc import abstractmethod
from typing import ClassVar, Generic, Type, TypeVar

from aiohttp import ClientResponseError
from tenacity import retry_if_exception

from aioqzone.exception import QzoneError

_E = TypeVar("_E", bound=BaseException)


class RetryIfCode(retry_if_exception, Generic[_E]):
    """Abstract retry predicate that extracts an error code from an exception.

    Subclasses implement :meth:`get_code` to extract the relevant code.
    """

    _exc_cls: ClassVar[Type[_E]]  # type: ignore

    @classmethod
    @abstractmethod
    def get_code(cls, exc: _E) -> int:
        """Extract error code from exception.

        :param exc: the exception to inspect
        :returns: error code integer
        """

    def __init__(self, *code: int) -> None:
        super().__init__(lambda exc: isinstance(exc, self._exc_cls) and self.get_code(exc) in code)


class retry_if_status(RetryIfCode[ClientResponseError]):
    """Retry predicate for HTTP status codes.

    Retries if ``exc.status`` matches one of the given codes.
    """

    _exc_cls = ClientResponseError

    @classmethod
    def get_code(cls, exc: ClientResponseError) -> int:
        return exc.status


class retry_if_qzone_code(RetryIfCode[QzoneError]):
    """Retry predicate for Qzone business error codes.

    Retries if ``exc.code`` matches one of the given codes.
    """

    _exc_cls = QzoneError

    @classmethod
    def get_code(cls, exc: QzoneError) -> int:
        return exc.code
