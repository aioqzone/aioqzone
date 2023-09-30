from abc import abstractmethod
from typing import Any, Callable, Dict, Generic, Optional, TypeVar, Union

from aiohttp import ClientResponseError
from tenacity import RetryCallState, retry_base

from aioqzone.exception import QzoneError

_E = TypeVar("_E", bound=BaseException)


class RetryIfCode(retry_base, Generic[_E]):
    code_dispatch: Dict[int, Optional[Callable[[_E], Any]]]
    code_suppress: Dict[int, Union[bool, Callable[[_E], bool]]]

    @classmethod
    @abstractmethod
    def get_code(cls, exc: _E) -> int:
        ...

    def __init__(self, *code: int) -> None:
        self.code = code

    def __call__(self, retry_state: RetryCallState) -> bool:
        if retry_state.outcome is None:
            raise RuntimeError("__call__() called before outcome was set")

        if retry_state.outcome.failed:
            exception: Optional[_E] = retry_state.outcome.exception()
            if exception is None:
                raise RuntimeError("outcome failed but the exception is None")
            return self.get_code(exception) in self.code
        else:
            return False


class retry_if_status(RetryIfCode[ClientResponseError]):
    @classmethod
    def get_code(cls, exc: ClientResponseError) -> int:
        return exc.status


class retry_if_qzone_code(RetryIfCode[QzoneError]):
    @classmethod
    def get_code(cls, exc: QzoneError) -> int:
        return exc.code
