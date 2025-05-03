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
    f = filter(pred, it)
    if default is ...:
        return next(f)
    return next(f, default)


def firstn(it: t.Iterable[T], pred: t.Optional[t.Callable[[T], t.Optional[object]]] = None):
    return first(it, pred, default=None)
