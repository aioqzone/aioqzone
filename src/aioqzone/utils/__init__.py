"Some utilities for conducting tasks."
from typing import Callable, Iterable, Optional, TypeVar, Union

T = TypeVar("T")


def first(it: Iterable[T], pred: Optional[Callable[[T], Union[object, None]]]) -> Optional[T]:
    return next(filter(pred, it), None)
