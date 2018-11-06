"""
Cache object
"""

def cached(func, *args, **kwds):
    """
    A decorator for initiating cached function call
    """
    pass


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
        print('>>> Adding to cache:', item, value)
        if self.hasItem(item):
            return   # item is already cached

        if self._maxItems and len(self._items) == self._maxItems:
            # need to remove one item first
            itm = self._items.pop()
            print('>>> removing item', itm)
            del(self._cacheDict[itm])

        self._cacheDict[item] = value
        self._items.append(item)

    def get(self, item):
        """Get item from cache; return None if not present
        """
        if not self.hasItem(item):
            return None
        print('>>> getting from cache:', item)
        return self._cacheDict[item]

    def hasItem(self, item):
        """Return True of item is in cache
        """
        return item in self._items

    def clear(self):
        """Clear all items from the cache
        """
        self._cacheDict = {}
        self._items = []


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

    a = myclass()
    print(a.add('aap noot mies'.split()))
    print(a.add('aap noot mies'.split()))
    print(a.add('kees hallo'.split()))
    print(a.add('dag week'.split()))
