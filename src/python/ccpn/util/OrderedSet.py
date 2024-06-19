"""Based on Ordered Set
By Raymond Hettinger, http://code.activestate.com/recipes/576694/

"""
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
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-06-19 13:15:42 +0100 (Wed, June 19, 2024) $"
__version__ = "$Revision: 3.2.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import collections.abc


class OrderedSet(collections.abc.MutableSet):

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self.map = {}  # key --> [key, prev, next]
        if iterable is not None:
            # bypass the mutable method
            for value in iterable:
                self.add(value)
            # self |= iterable

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def add(self, key):
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def discard(self, key):
        if key in self.map:
            key, _prev, _next = self.map.pop(key)
            _prev[2] = _next
            _next[1] = _prev

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def pop(self, last=True):
        if not self:
            raise KeyError('set is empty')
        key = self.end[1][0] if last else self.end[2][0]
        self.discard(key)
        return key

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, (OrderedSet, FrozenOrderedSet)):
            return len(self) == len(other) and list(self) == list(other)
        # revert to more lenient set behaviour
        return set(self) == set(other)


class FrozenOrderedSet(collections.abc.MutableSet):

    def __init__(self, iterable=None):
        self.end = end = []
        end += [None, end, end]  # sentinel node for doubly linked list
        self.map = {}  # key --> [key, prev, next]
        if iterable is not None:
            # bypass the mutable method
            for value in iterable:
                self._frozenAdd(value)

    def _immutable(self, *args, **kws):
        """Raise error when performing illegal operation on immutable object
        """
        raise RuntimeError('Operation not allowed on {} - object is immutable'.format(self.__class__.__name__))

    __setitem__ = _immutable
    __delitem__ = _immutable
    add = _immutable
    discard = _immutable
    remove = _immutable
    pop = _immutable
    clear = _immutable

    def _frozenAdd(self, key):
        """Add elements during initial creation, frozen at all other times
        """
        if key not in self.map:
            end = self.end
            curr = end[1]
            curr[2] = end[1] = self.map[key] = [key, curr, end]

    def __len__(self):
        return len(self.map)

    def __contains__(self, key):
        return key in self.map

    def __iter__(self):
        end = self.end
        curr = end[2]
        while curr is not end:
            yield curr[0]
            curr = curr[2]

    def __reversed__(self):
        end = self.end
        curr = end[1]
        while curr is not end:
            yield curr[0]
            curr = curr[1]

    def __repr__(self):
        if not self:
            return '%s()' % (self.__class__.__name__,)
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __eq__(self, other):
        if isinstance(other, (OrderedSet, FrozenOrderedSet)):
            return len(self) == len(other) and list(self) == list(other)
        # revert to more lenient set behaviour
        return set(self) == set(other)


if __name__ == '__main__':
    # quick for now, but should use some nose-tests
    s = OrderedSet('hgfedcbaace')  # a-h
    t = OrderedSet('nmlkjihggik')  # g-n
    print('OR - {}'.format(s | t))
    print('AND - {}'.format(s & t))
    print('MINUS - {}'.format(s - t))
    print('MINUS - {}'.format(t - s))
    print('SAME - {}'.format(s==t))

    print('SET s - {}'.format(s))
    s.pop()
    print('POP - {}'.format(s))
    s.pop(last=False)
    print('POP - {}'.format(s))
    s.discard('d')
    print('DISCARD - {}'.format(s))

    s = OrderedSet('hgfedcbaace')
    t = FrozenOrderedSet('nmlkjihggik')
    print('OR - {}'.format(s | t))
    print('AND - {}'.format(s & t))
    print('MINUS - {}'.format(s - t))

    print('SET s - {}'.format(s))
    s.pop()
    print('POP - {}'.format(s))

    print('SET t - {}'.format(s))
    try:
        t |= 'Z'
    except Exception as es:
        print(str(es))
    try:
        t.pop()
    except Exception as es:
        print(str(es))
    print('SET t - {}'.format(s))
    print('SAME - {}'.format(s==t))
    t = FrozenOrderedSet('hgfedcb')
    print('SAME - {}'.format(s==t))
    print('SAME - {}'.format(t==s))
    print('SAME - {}'.format(t=='bcdefgh'))
    print(t)
    print(repr(t))
