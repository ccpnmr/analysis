"""Based on Ordered Set
By Raymond Hettinger, https://code.activestate.com/recipes/576694/
"""
from __future__ import annotations


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-06-11 12:50:32 +0100 (Wed, June 11, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import AbstractSet, Any, cast, Generic, Hashable, Iterable, Iterator, TypeVar
import collections.abc

from typing_extensions import Self


_TOrd = TypeVar('_TOrd')


class OrderedSet(collections.abc.MutableSet, Generic[_TOrd]):
    """
    A mutable set that remembers the order of insertion.

    This class provides set-like functionality while maintaining the insertion
    order of its elements. It behaves like a regular Python set for membership
    testing and uniqueness, but its iteration order is predictable and
    matches the order in which elements were first added.

    It uses a combination of a dictionary for O(1) lookups and a
    doubly linked list for maintaining order.

    :param iterable: An optional iterable of elements to initialize the set with.
                     Elements will be added in the order they appear in the iterable.
    :type iterable: Iterable[_TOrd] or None
    """
    end: list[Any]
    map: dict[_TOrd, list[Any]]

    def __init__(self, iterable: Iterable[_TOrd] | None = None):
        end: list[Any]
        self.end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self.map = {}  # key --> [key, prev, next]
        if iterable is not None:
            # bypass the mutable method
            for value in iterable:
                self.add(value)

    def __len__(self) -> int:
        """
        Return the number of elements in the set.

        :returns: The number of elements.
        :rtype: int
        """
        return len(self.map)

    def __contains__(self, key: object) -> bool:
        """
        Check if an element is in the set.

        :param key: The element to check for.
        :type key: object
        :returns: True if the element is in the set, False otherwise.
        :rtype: bool
        """
        return key in self.map

    def add(self, key: _TOrd):
        """
        Add an element to the set.

        If the element is already present, its position in the order
        remains unchanged.

        :param key: The element to add.
        :type key: _TOrd
        """
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key: _TOrd):
        """
        Remove an element from the set if it is present.

        If the element is not found, no action is taken.

        :param key: The element to remove.
        :type key: _TOrd
        """
        if key in self.map:
            key, _prev, _next = self.map.pop(key)
            _prev[2] = _next
            _next[1] = _prev

    def __iter__(self) -> Iterator[_TOrd]:
        """
        Return an iterator over the elements of the set in insertion order.

        :returns: An iterator over the elements.
        :rtype: Iterator[_TOrd]
        """
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self) -> Iterator[_TOrd]:
        """
        Return a reverse iterator over the elements of the set in reverse insertion order.

        :returns: A reverse iterator over the elements.
        :rtype: Iterator[_TOrd]
        """
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last: bool = True):
        """
        Remove and return an element from the set.

        By default, removes and returns the last (most recently added) element.
        If `last` is False, removes and returns the first (least recently added) element.

        :param last: If True, remove the last element; otherwise, remove the first.
        :type last: bool
        :returns: The removed element.
        :rtype: _TOrd
        :raises KeyError: If the set is empty.
        """
        key: _TOrd
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __str__(self) -> str:
        """
        Return a string representation of the set.

        The representation matches the standard set literal format,
        but elements are ordered by insertion.

        :returns: A string representation of the ordered set.
        :rtype: str
        """
        if not self:
            return f'{self.__class__.__name__}()'
        return f'{self.__class__.__name__}({list(self)!r})'

    def __repr__(self) -> str:
        """
        Return the canonical string representation of the set.

        This typically returns a string that could be used to recreate the object.

        :returns: The canonical string representation.
        :rtype: str
        """
        return f'{str(self)!r}'

    def __eq__(self, other: AbstractSet[_TOrd]) -> bool:  # type: ignore[override]
        """
        Check if this ordered set is equal to another object.

        If `other` is an `OrderedSet` or `FrozenOrderedSet`, equality requires
        both sets to have the same length and elements in the same order.
        Otherwise, it delegates to the superclass's `__eq__` method, which typically
        performs order-agnostic set equality (i.e. by converting both to standard sets).

        :param other: The object to compare against.
        :type other: AbstractSet[_TOrd]
        :returns: True if the sets are equal, False otherwise.
        :rtype: bool
        """
        if isinstance(other, (OrderedSet, FrozenOrderedSet)):  # Assuming FrozenOrderedSet is defined elsewhere
            return len(self) == len(other) and list(self) == list(other)
        # Delegate to the superclass's __eq__ (e.g., collections.abc.Set's implementation)
        return super().__eq__(other)

    def __ne__(self, other: AbstractSet[_TOrd]) -> bool:  # type: ignore[override]
        """
        Check if this ordered set is not equal to another object.

        This method is implemented by negating the result of the `__eq__` method.
        If `__eq__` returns `NotImplemented`, `__ne__` will also return `NotImplemented`.

        :param other: The object to compare against.
        :type other: AbstractSet[_TOrd]
        :returns: True if the sets are not equal, False otherwise.
        :rtype: bool
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __or__(self, other: AbstractSet[_TOrd]) -> Self:  # type: ignore[override]
        """
        Return the union of this set and another abstract set (`self | other`).

        The result is a new `OrderedSet` containing all unique elements from both
        sets. The order of elements from `self` is preserved first, followed by
        elements from `other` that were not already in `self`, in their original
        order from `other`.

        This method leverages the superclass's union logic to perform the operation.

        :param other: The other abstract set to union with.
        :type other: AbstractSet[_TOrd]
        :returns: A new `OrderedSet` representing the union.
        :rtype: Self
        """
        return cast(Self, super().__or__(other))
        # if not isinstance(other, collections.abc.Iterable):
        #     return NotImplemented
        # result = self.__class__(self)
        # if other is not None:
        #     # bypass the mutable method
        #     for value in other:
        #         self.add(value)
        # return result

    def __ior__(self, other: AbstractSet[_TOrd]) -> Self:  # type: ignore[override]
        """
        Perform an in-place union of this set with another abstract set (`self |= other`).

        This method adds all unique elements from `other` into `self`.
        The order of existing elements in `self` is maintained, and new elements
        from `other` are appended in their original order.

        This method leverages the superclass's in-place union logic to perform the operation.

        :param other: The other abstract set to union with.
        :type other: AbstractSet[_TOrd]
        :returns: The modified `OrderedSet` instance.
        :rtype: Self
        """
        return cast(Self, super().__ior__(other))
        # return cast(Self, super().__ior__(cast(AbstractSet[_TOrd], other)))
        # if not isinstance(other, collections.abc.Iterable):
        #     return NotImplemented
        # # Perform in-place union by iterating and adding
        # for item in other:
        #     self.add(item)
        # return self


#=========================================================================================
# FrozenOrderedSet
#=========================================================================================

_TFroz = TypeVar('_TFroz', bound=Hashable)


class FrozenOrderedSet(collections.abc.Set, Generic[_TFroz]):
    """
    An immutable set that remembers the order of insertion.

    This class provides set-like functionality similar to `frozenset`,
    but it maintains the insertion order of its elements. Once created,
    elements cannot be added, removed, or reordered.

    It uses a combination of a dictionary for O(1) lookups and a
    doubly linked list for maintaining order during initialization and iteration.

    :param iterable: An optional iterable of elements to initialize the set with.
                     Elements will be added in the order they appear in the iterable
                     during construction.
    :type iterable: Iterable[_TFroz] or None
    """
    end: list[Any]
    map: dict[_TFroz, list[Any]]
    _cached_hash: int

    def __init__(self, iterable: Iterable[_TFroz] | None = None):
        end: list[Any]
        self.end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self.map = {}  # key --> [key, prev, next]
        if iterable is not None:
            # Elements are added during initialization using _frozenAdd
            for value in iterable:
                self._frozenAdd(value)
        # Calculate and cache hash for immutability
        # Note: __hash__ method is typically implemented separately,
        #       but caching it in __init__ is a common optimization.
        #       Ensure __hash__ method calls this or calculates it correctly.
        if not hasattr(self, '_cached_hash'):  # Added for clarity with hash
            self._cached_hash = hash(tuple(self))

    def _immutable(self, *args: Any, **kwargs: Any) -> None:
        """
        Raise an error when an illegal operation is attempted on an immutable object.

        This method is assigned to all mutating methods (e.g. `add`, `discard`, `pop`)
        to prevent modifications after the `FrozenOrderedSet` has been created.

        :param args: Positional arguments (ignored).
        :type args: Any
        :param kwargs: Keyword arguments (ignored).
        :type kwargs: Any
        :raises RuntimeError: Always - indicating that the object is immutable.
        """
        raise RuntimeError(f'Operation not allowed on {self.__class__.__name__} - object is immutable')

    def _frozenAdd(self, key: _TFroz):
        """
        Add elements internally during the initial construction of the `FrozenOrderedSet`.

        This is an internal helper method used by `__init__` to populate the set.
        It is not intended for external use after the object has been created.

        :param key: The element to add.
        :type key: _TFroz
        """
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def __len__(self) -> int:
        """
        Return the number of elements in the set.

        :returns: The number of elements.
        :rtype: int
        """
        return len(self.map)

    def __contains__(self, key: object) -> bool:
        """
        Check if an element is in the set.

        :param key: The element to check for.
        :type key: object
        :returns: True if the element is in the set, False otherwise.
        :rtype: bool
        """
        return key in self.map

    def __iter__(self) -> Iterator[_TFroz]:
        """
        Return an iterator over the elements of the set in insertion order.

        :returns: An iterator over the elements.
        :rtype: Iterator[_TFroz]
        """
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self) -> Iterator[_TFroz]:
        """
        Return a reverse iterator over the elements of the set in reverse insertion order.

        :returns: A reverse iterator over the elements.
        :rtype: Iterator[_TFroz]
        """
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def __str__(self) -> str:
        """
        Return a string representation of the set.

        The representation matches the standard `frozenset` literal format,
        but elements are ordered by insertion.

        :returns: A string representation of the frozen ordered set.
        :rtype: str
        """
        if not self:
            return f'{self.__class__.__name__}()'
        return f'{self.__class__.__name__}({list(self)!r})'

    def __repr__(self) -> str:
        """
        Return the canonical string representation of the set.

        This typically returns a string that could be used to recreate the object.

        :returns: The canonical string representation.
        :rtype: str
        """
        return f'{str(self)!r}'

    def __eq__(self, other: AbstractSet[_TFroz]) -> bool:  # type: ignore[override]
        """
        Check if this frozen ordered set is equal to another object.

        If `other` is an `OrderedSet` or `FrozenOrderedSet`, equality requires
        both sets to have the same length and elements in the same order.
        Otherwise, it delegates to the superclass's `__eq__` method, which typically
        performs order-agnostic set equality (i.e. by converting both to standard sets).

        :param other: The object to compare against.
        :type other: AbstractSet[_TFroz]
        :returns: True if the sets are equal, False otherwise.
        :rtype: bool
        """
        if isinstance(other, (OrderedSet, FrozenOrderedSet)):
            return len(self) == len(other) and list(self) == list(other)
        # Delegate to the superclass's __eq__ (collections.abc.Set's implementation)
        return super().__eq__(other)

    def __ne__(self, other: AbstractSet[_TFroz]) -> bool:  # type: ignore[override]
        """
        Check if this ordered set is not equal to another object.

        This method is implemented by negating the result of the `__eq__` method.
        If `__eq__` returns `NotImplemented`, `__ne__` will also return `NotImplemented`.

        :param other: The object to compare against.
        :type other: AbstractSet[_TFroz]
        :returns: True if the sets are not equal, False otherwise.
        :rtype: bool
        """
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result

    def __hash__(self) -> int:
        """
        Compute and return the hash value of the frozen ordered set.

        The hash value is cached for efficiency because the set is immutable.

        :returns: The hash value of the set.
        :rtype: int
        """
        # Ensure the hash is calculated and cached during initialization.
        # If not, calculate it now (e.g., if the object was deserialized without __init__ call).
        if not hasattr(self, '_cached_hash'):
            self._cached_hash = hash(tuple(self))
        return self._cached_hash


#=========================================================================================
# main
#=========================================================================================

def main():
    # quick for now, but should use some nose-tests
    r = OrderedSet('nmlkjihggik')  # g-n
    s = OrderedSet[str]('hgfedcbaace')  # a-h
    print(f'OR - {s | r}')
    print(f'AND - {s & r}')
    print(f'MINUS - {s - r}')
    print(f'MINUS - {r - s}')
    print(f'SAME - {s == r}')
    sr = OrderedSet('hgfedcbaacenmlkjihggik')  # a-n
    rs = OrderedSet('hg')  # g-h
    sr_min = OrderedSet('fedcbaace')  # a-f
    rs_min = OrderedSet('nmlkjiik')  # i-n
    assert (s | r) == sr
    assert (s & r) == rs
    assert (s - r) == sr_min
    assert (r - s) == rs_min

    print(f'SET s - {s}')
    s.pop()
    print(f'POP - {s}')
    s.pop(last=False)
    print(f'POP - {s}')
    s.discard('d')
    print(f'DISCARD - {s}')

    s = OrderedSet('hgfedcbaace')  # a-h
    t = FrozenOrderedSet[str]('nmlkjihggik')  # g-n
    print(f'OR - {s | t}')
    print(f'AND - {s & t}')
    print(f'MINUS - {s - t}')
    st = OrderedSet('hgfedcbanmlkji')  # a-n
    ts = OrderedSet('hg')  # g-h
    st_min = OrderedSet('fedcba')  # a-f
    assert (s | t) == st
    assert (s & t) == ts
    assert (s - t) == st_min
    assert s != 2.5

    print(f'SET s - {s}')
    s.pop()
    print(f'POP - {s}')
    assert s == OrderedSet('hgfedcb')  # `a` added last

    print(f'REVERSED {list(reversed(s))}')
    m = OrderedSet(s)
    print(f'COPY - {m}')
    assert s is not m
    assert s == m
    m.clear()
    print(f'CLEAR - {m}')
    assert m == OrderedSet()

    print(f'SET t - {t}')
    try:
        t |= 'Z'
    except Exception as ex:
        print(f'***  ==> {str(ex)}')
    try:
        t.pop()
    except Exception as ex:
        print(f'***  ==> {str(ex)}')
    try:
        t.clear()
    except Exception as ex:
        print(f'***  ==> {str(ex)}')
    print(f'SET t - {s}')
    print(f'SAME - {s == t}')
    assert s != t
    u = FrozenOrderedSet[str]('hgfehedhcb')
    print(f'SAME - {s == u}')
    print(f'SAME - {u == s}')
    print(f'SAME - {u == "bcdefgh"}')
    assert s == u
    assert u == s
    assert u != list('bcdefgh')

    print(u)
    print(repr(u))
    print(f'REVERSED {list(reversed(u))}')
    assert list(reversed(u)) == list('bcdefgh')


    class oo:
        ...


    x = OrderedSet([1, 3, 4.0, 'help'])
    print(x)
    w = OrderedSet[int]([1, 3, 4, 5])
    print(w)
    w |= {'x', 'y', oo()}

    z = OrderedSet[int | float]([1, 3, 4.0, 'help'])
    print(z)
    print(s | z)
    y = OrderedSet[int | str]([1, 3, 4.0, 'help'])
    print(y)
    print(f'SAME - {u == oo()}')
    print(f'{z}    -    {z!r}')


if __name__ == '__main__':
    main()
