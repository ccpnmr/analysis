"""
Module Documentation here
"""
from __future__ import annotations


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-06-09 18:21:37 +0100 (Mon, June 09, 2025) $"
__version__ = "$Revision: $"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2025-06-09 18:21:37 +0100 (Mon, June 09, 2025) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import AbstractSet, Any, Generic, Hashable, Iterable, Iterator, TypeVar
import collections.abc

from typing_extensions import Self


_TOrd = TypeVar('_TOrd', bound=Hashable)


# --- Type hints for OrderedSet (all methods present) ---
class OrderedSet(collections.abc.MutableSet, Generic[_TOrd]):
    end: list[Any]
    map: dict[_TOrd, list[Any]]

    def __init__(self, iterable: Iterable[_TOrd] | None = ...) -> None: ...
    def __len__(self) -> int: ...
    def __contains__(self, key: object) -> bool: ...
    def add(self, key: _TOrd) -> None: ...  # <-- Include mutable methods here
    def discard(self, key: _TOrd) -> None: ...  # <-- Include mutable methods here
    def __iter__(self) -> Iterator[_TOrd]: ...
    def __reversed__(self) -> Iterator[_TOrd]: ...
    def pop(self, last: bool = ...) -> _TOrd: ...  # <-- Include mutable methods here
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: AbstractSet[_TOrd]) -> bool: ...  # type: ignore[override]
    def __ne__(self, other: AbstractSet[_TOrd]) -> bool: ...  # type: ignore[override]
    def __or__(self, other: AbstractSet[_TOrd]) -> Self: ...  # type: ignore[override]
    def __ior__(self, other: AbstractSet[_TOrd]) -> Self: ...  # type: ignore[override]
    # Add other methods like clear, remove, __setitem__, __delitem__ if they exist in runtime
    ...  # No method bodies, just ellipsis or pass for definition.


# --- Type hints for FrozenOrderedSet (omit mutable methods) ---
_TFroz = TypeVar('_TFroz', bound=Hashable)


class FrozenOrderedSet(collections.abc.Set, Generic[_TFroz]):
    end: list[Any]
    map: dict[_TFroz, list[Any]]
    _cached_hash: int

    def __init__(self, iterable: Iterable[_TFroz] | None = ...) -> None: ...
    def _immutable(self, *args: Any, **kwargs: Any) -> None: ...
    def _frozenAdd(self, key: _TFroz) -> None: ...  # <-- Include mutable methods here
    # Important: Do NOT list 'add', 'discard', 'pop', 'clear', '__setitem__', '__delitem__', 'remove' here.
    # MyPy will then infer that FrozenOrderedSet instances do not have these methods.
    # Other inherited methods like __len__, __contains__, __iter__, __eq__, __or__, etc.
    # will be inherited correctly from OrderedSet, and their signatures remain the same.
    def __len__(self) -> int: ...
    def __contains__(self, key: object) -> bool: ...
    def __iter__(self) -> Iterator[_TFroz]: ...
    def __reversed__(self) -> Iterator[_TFroz]: ...
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...
    def __eq__(self, other: AbstractSet[_TFroz]) -> bool: ...  # type: ignore[override]
    def __ne__(self, other: AbstractSet[_TFroz]) -> bool: ...  # type: ignore[override]
    def __hash__(self) -> int: ...
    ...  # No method bodies, just ellipsis or pass for definition.
