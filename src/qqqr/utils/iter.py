"""Iteration utility functions.

Provides :func:`first` and :func:`firstn` for finding the first matching
item in an iterable.
"""

import typing as t

T = t.TypeVar("T")
D = t.TypeVar("D")


@t.overload
def first(
    it: t.Iterable[T], pred: t.Optional[t.Callable[[T], t.Optional[object]]] = None
) -> T: ...


@t.overload
def first(
    it: t.Iterable[T],
    pred: t.Optional[t.Callable[[T], t.Optional[object]]] = None,
    *,
    default: D,
) -> t.Union[T, D]: ...


def first(
    it: t.Iterable[T],
    pred: t.Optional[t.Callable[[T], t.Optional[object]]] = None,
    *,
    default: D = ...,
) -> t.Union[T, D]:
    """Return the first item in ``it`` matching ``pred``.

    :param it: iterable to search
    :param pred: optional predicate function
    :param default: fallback if no match (raises :exc:`StopIteration` if not given)
    :returns: the first matching item, or *default*
    """
    f = filter(pred, it)
    if default is ...:
        return next(f)
    return next(f, default)


def firstn(it: t.Iterable[T], pred: t.Optional[t.Callable[[T], t.Optional[object]]] = None):
    """Return the first matching item, or ``None``.

    Thin wrapper around :func:`first` with ``default=None``.
    """
    return first(it, pred, default=None)
