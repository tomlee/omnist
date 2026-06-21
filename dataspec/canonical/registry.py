"""Format registry — read/write a Document by format name, and register plugins.

A :class:`Format` bundles a name with ``read(text) -> node`` and
``write(node, **opts) -> str`` callables.  The four built-ins register
themselves on import; :func:`register_format` adds your own, usable everywhere
(including ``Doc.from_format`` / ``Doc.to_format``).
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, NamedTuple

from ..errors import DataspecError


class Format(NamedTuple):
    name: str
    read: Callable[[str], Any]                  # text -> node
    write: Callable[..., str]                   # (node, **opts) -> text


_REGISTRY: Dict[str, Format] = {}
_LOCK = threading.Lock()


def register_format(fmt: Format) -> None:
    """Register (or replace) a format plugin."""
    with _LOCK:
        _REGISTRY[fmt.name] = fmt


def get_format(name: str) -> Format:
    """The registered :class:`Format` for ``name`` (raises if unknown)."""
    with _LOCK:
        try:
            return _REGISTRY[name]
        except KeyError:
            known = ", ".join(sorted(_REGISTRY)) or "(none)"
            raise DataspecError(f"unknown format {name!r}; registered: {known}") from None


def formats() -> List[str]:
    """The names of all registered formats, sorted."""
    with _LOCK:
        return sorted(_REGISTRY)


def _register_builtins() -> None:
    from .formats import (
        read_json,
        read_toml,
        read_xml,
        read_yaml,
        write_json,
        write_toml,
        write_xml,
        write_yaml,
    )
    register_format(Format("json", read_json, write_json))
    register_format(Format("yaml", read_yaml, write_yaml))
    register_format(Format("toml", read_toml, write_toml))
    register_format(Format("xml", read_xml, write_xml))
