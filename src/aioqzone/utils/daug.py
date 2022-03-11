"""Augment python `dict` since we cannot use py37+ features...

Maybe these are user-defined syntax-sugars?
"""

from itertools import chain
from typing import Dict, Hashable, Iterable, Mapping, MutableMapping, Tuple, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


def u_(*dicts: Mapping[K, V]) -> Iterable[Tuple[K, V]]:
    return chain(*(i.items() for i in dicts))


def ud(*dicts: Mapping[K, V]) -> Dict[K, V]:
    """returns union of these dict."""
    return dict(u_(*dicts))


def di(d: MutableMapping[K, V], **kw) -> MutableMapping[K, V]:
    """insert kw into this dict."""
    d.update(**kw)
    return d
