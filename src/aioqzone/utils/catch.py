from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Generic, Optional, Set, Type, TypeVar, Union, get_args

from httpx import HTTPStatusError

from aioqzone.exception import QzoneError

_E = TypeVar("_E", bound=BaseException)


class CatchCodeDispatch(ABC, Generic[_E]):
    code_dispatch: Dict[int, Optional[Callable[[_E], Any]]]
    code_suppress: Dict[int, Union[bool, Callable[[_E], bool]]]

    @classmethod
    @abstractmethod
    def get_code(cls, exc: _E) -> int:
        ...

    def __init__(self) -> None:
        super().__init__()
        self.code_dispatch = {}
        self.code_suppress = {}

    def dispatch(
        self,
        *code: int,
        dispatcher: Optional[Callable[[_E], Any]] = None,
        suppress: Union[bool, Callable[[_E], bool]] = True,
    ):
        for i in code:
            self.code_dispatch[i] = dispatcher
        for i in code:
            self.code_suppress[i] = suppress

    def __enter__(self):
        return self

    def __exit__(self, ty: Type[_E], e: _E, tb) -> bool:
        if ty is not None and issubclass(ty, get_args(self.__orig_bases__[0])):  # type: ignore
            code = self.get_code(e)
            if dispatcher := self.code_dispatch.get(code):
                dispatcher(e)
            suppress = self.code_suppress.get(code)
            if suppress is None:
                return True
            if callable(suppress):
                return suppress(e)
            return bool(suppress)
        return False


class HTTPStatusErrorDispatch(CatchCodeDispatch[HTTPStatusError]):
    @classmethod
    def get_code(cls, exc: HTTPStatusError) -> int:
        return exc.response.status_code


class QzoneErrorDispatch(CatchCodeDispatch[QzoneError]):
    @classmethod
    def get_code(cls, exc: QzoneError) -> int:
        return exc.code
