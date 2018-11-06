"""
Cache object
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2018"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: geertenv $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2018-05-14 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import decorator
import inspect

DEBUG = False

class Cache(object):
    """
    A chache object;

    - Retains (item, value) pairs; item must be a hash-able object (e.g. tuple)
    - Retains either maxItem or unlimited number of objects.
    - Clearing cache is responsibility of the instantiating code
    """

    def __init__(self, maxItems=None):
        """
        Initialise the cache
        :param maxItems: maximum number of items to hold; unlimited for
               maxItems==0 or maxItems == None
        """
        self._maxItems = maxItems
        self.clear()  # sets self._cacheDict and self._items

    def add(self, item, value):
        """add item,value to the cache
        """
        if DEBUG: print('DEBUG> Adding to cache:', item)
        if self.hasItem(item):
            return   # item is already cached

        if self._maxItems and len(self._items) == self._maxItems:
            # need to remove one item first
            itm = self._items.pop(0)
            if DEBUG: print('DEBUG> removing item from cache:', itm)
            del(self._cacheDict[itm])

        self._cacheDict[item] = value
        self._items.append(item)

    def get(self, item):
        """Get item from cache; return None if not present
        """
        if DEBUG: print('DEBUG> getting from cache:', item)
        if not self.hasItem(item):
            return None
        return self._cacheDict[item]

    def hasItem(self, item):
        """Return True of item is in cache
        """
        return item in self._items

    def clear(self):
        """Clear all items from the cache
        """
        if DEBUG: print('DEBUG> clearing cache')
        self._cacheDict = {}
        self._items = []


def cached(attributeName, maxItems=0):
    """
    A decorator for initiating cached function call
    Works on functions that pass an object as the first argument; e.g. self
    attributeName defines the cache object
    """

    @decorator.decorator
    def decoratedFunc(*args, **kwds):
        # def myFunc(obj, *args, **kwds):
        # to avoid potential conflicts with potential 'func' named keywords
        func = args[0]
        args = args[1:]

        ba = inspect.signature(func).bind(*args, **kwds)
        ba.apply_defaults()
        allArgs = ba.arguments # ordered dict of (argument,value) pairs; first corresponds to object

        obj = [v for v in allArgs.values()][0]

        argumentNames = [k for k in allArgs.keys()][1:]  # skip the first one which is the object
        # sort to maintain a consistent tuple of tuples item to cache
        argumentNames.sort()
        item = tuple([ (k,allArgs[k]) for k in argumentNames ])
        # convert to a string
        item = repr(item)

        print('Decorator>>>', item)

        if not hasattr(obj, attributeName):
            setattr(obj, attributeName, Cache(maxItems=maxItems))
        cache = getattr(obj, attributeName)
        if not isinstance(cache, Cache):
            raise RuntimeError('%s, %s is not a Cache object' % (obj, attributeName))

        # Check the cache if item exists
        result = cache.get(item)
        if result is None:
            # execute the function
            result = func(*args, **kwds)
            cache.add(item, result)

        return result

    return decoratedFunc


if __name__ == "__main__":

    class myclass(object):
        def __init__(self):
            self.cache = Cache(maxItems=2)

        def add(self, values):
            result = self.cache.get(tuple(values))
            if result is None:
                result = [v.capitalize() for v in values]
                self.cache.add(tuple(values), result)
            return result

        @cached('cache')
        def add2(self, values, test=True):
            return [v.capitalize() for v in values]

    a = myclass()
    print(a.add('aap noot mies'.split()))
    print(a.add('aap noot mies'.split()))
    print(a.add('kees hallo'.split()))
    print(a.add('dag week'.split()))

    v = 'fijn zo'.split()
    print(a.add2(v))
    print(a.add2(v, False))
