from collections.abc import Iterable
from typing import Any

__all__ = [
    "getattr_recursive",
    "getitem",
    "getitem_recursive",
]


NOT_SET = object()


def getattr_recursive(obj: Any, names: Iterable[str], default: Any = NOT_SET):
    for name in names:
        try:
            obj = getattr(obj, name)
        except AttributeError:
            if default is NOT_SET:
                raise
            return default
    return obj


def getitem(obj: Any, name: Any, default: Any = NOT_SET) -> Any:
    try:
        return obj[name]
    except KeyError:
        if default is NOT_SET:
            raise
        return default


def getitem_recursive(obj: Any, names: Iterable[Any], default: Any = NOT_SET):
    for name in names:
        try:
            obj = obj[name]
        except (KeyError, IndexError):
            if default is NOT_SET:
                raise
            return default
    return obj
