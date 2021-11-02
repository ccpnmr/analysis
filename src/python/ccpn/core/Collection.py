"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-11-02 11:47:06 +0000 (Tue, November 02, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-10-26 15:52:47 +0100 (Tue, October 26, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Optional, Tuple, Any, Sequence
from collections import Counter

from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Collection as apiCollection
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, undoBlock, \
    renameObject, ccpNmrV3CoreSetter
from ccpn.util.Common import makeIterableList
from ccpn.util.decorators import logCommand
from ccpn.util.OrderedSet import OrderedSet


class _searchCollections():
    """
    Iterator to recursively search collections for items of type specified in objectTypes

    depth defines the maximum number of nested collections that the search will through.
    Set depth=1, will return only the items in the specified collection.
    Set depth=0 for fully recursive, default=0

    Search is protected against infinite loops of collections

    objectTypes must be a tuple of types
    collection must be a list of core objects
    """
    _MAXITERATIONS = 100

    # iterator to search through nested collections and collate all items
    def __init__(self, collection, objectTypes=None, depth=0):
        """Initialise the iterator
        """
        if not (isinstance(depth, int) and depth >= 0):
            raise ValueError('depth must be an int >= 0')

        self._items = OrderedSet(collection)
        self._objectTypes = objectTypes
        self._maxDepth = depth

    def __iter__(self):
        # initial iterator settings
        self._len = 0
        self._iteration = 0
        return self

    def __next__(self):
        """Generate the next ordered set of collection items
        """
        self._iteration += 1
        if self._iteration > self._MAXITERATIONS:
            # code check, just to make sure that a bug doesn't cause an infinite loop
            raise RuntimeError('Max search depth reached')

        if self._maxDepth and self._iteration >= self._maxDepth:
            # if reached specified/maximum depth then stop
            raise StopIteration

        # get the newly added, nested collections
        collections = list(filter(lambda obj: isinstance(obj, Collection),
                                  list(self._items)[self._len:]))
        if not collections:
            # if no more added to the orderedSet then reached the bottom
            raise StopIteration

        self._len = len(self._items)
        for coll in collections:
            # update the list of items
            self._items |= OrderedSet(coll.items)

        return self.items

    def __bool__(self):
        """Return True if there are items
        """
        return len(self._items) > 0

    __nonzero__ = __bool__

    def __len__(self):
        """Current number of filtered items in the iterator
        """
        return len(self.items)

    @property
    def items(self):
        """Return the filtered list of items
        """
        if self._objectTypes:
            return tuple(filter(lambda obj: isinstance(obj, self._objectTypes), self._items))
        else:
            return tuple(self._items)


class _searchCycles():
    """
    Iterator to recursively search collections for cycles

    depth defines the maximum number of nested collections that the search will through.
    Set depth=0 for fully recursive, default=0
    """
    _MAXITERATIONS = 100

    # iterator to search through nested collections and return any cycles
    def __init__(self, collection, depth=0):
        """Initialise the iterator
        """
        if not (isinstance(depth, int) and depth >= 0):
            raise ValueError('depth must be an int >= 0')

        self._items = [[(collection, [collection])]]
        self._maxDepth = depth

    def __iter__(self):
        # initial iterator settings
        self._len = 0
        self._iteration = 0
        self._cycles = ()
        return self

    def __next__(self):
        """Generate the next ordered set of collection items
        """
        self._iteration += 1
        if self._iteration > self._MAXITERATIONS:
            # code check, just to make sure that a bug doesn't cause an infinite loop
            raise RuntimeError('Max search depth reached')

        if self._maxDepth and self._iteration > self._maxDepth:
            # if reached specified/maximum depth then stop
            raise StopIteration
        if not self._items:
            raise StopIteration

        states = self._items.pop()
        for state, path in states:
            nextCollections = list(filter(lambda obj: isinstance(obj, Collection), state.items))

            _more = [(nextCol, path + [nextCol]) for nextCol in nextCollections if nextCol not in path]
            self._items.append(_more)
            _cycles = [tuple(path[path.index(nextCol):]) for nextCol in nextCollections if nextCol in path]
            self._cycles += tuple(_cycles)

        return self._cycles

    def __bool__(self):
        """Return True if there are cycles
        """
        return len(self._cycles) > 0

    __nonzero__ = __bool__

    def __len__(self):
        """Current number of cycles in the iterator
        """
        return len(self._cycles)


class Collection(AbstractWrapperObject):
    """Collection object, holding a list of core objects.
    """

    #: Short class name, for PID.
    shortClassName = 'CO'
    # Attribute it necessary as subclasses must use superclass className
    className = 'Collection'

    _parentClass = Project

    #: Name of plural link to instances of class
    _pluralLinkName = 'collections'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = apiCollection._metaclass.qualifiedName()

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiCollection(self) -> apiCollection:
        """API collections matching Collection"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string"""
        _name = self._wrappedData.name or ''
        return _name.translate(Pid.remapSeparators)

    @property
    def serial(self) -> int:
        """serial number of Collection, used in Pid and to identify the Collection. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> Optional['Project']:
        """parent containing collection."""
        try:
            return self._project._data2Obj[self._wrappedData.collectionParent]
        except:
            return None

    collectionParent = _parent

    @property
    def name(self) -> str:
        """Name of collection, part of identifier"""
        return self._wrappedData.name

    @name.setter
    @logCommand(get='self', isProperty=True)
    def name(self, value: str):
        """set Name of collection, part of identifier"""
        self.rename(value)

    @property
    def items(self) -> Optional[Tuple[Any]]:
        """List of items attached to the collection"""
        try:
            _data2Obj = self._project._data2Obj
            return tuple([_data2Obj[pk] for pk in self._wrappedData.collectionItems])
        except:
            return None

    @items.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def items(self, values):
        """Set the items in the collection"""
        values = Collection._checkItems(self.project, values)
        if self in values:
            raise ValueError(f'Cannot add {self} to itself')
        self._checkDuplicates(values)

        if values:
            self._wrappedData.collectionItems = [itm._wrappedData for itm in values]

    def __bool__(self):
        """Return True if there are items
        """
        return len(self._wrappedData.collectionItems) > 0

    __nonzero__ = __bool__

    def __len__(self):
        """Return the number of items in the collection
        """
        return len(self._wrappedData.collectionItems)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: 'Project') -> Tuple[apiCollection]:
        """get _wrappedData (Collections) for all Collection children of parent"""
        return parent._wrappedData.sortedPrimaryCollections()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename Collection, changing its name and Pid.
        """
        return self._rename(value)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    @staticmethod
    def _checkItems(project, items: Sequence[Any]) -> Optional[list]:
        """Check the list of items, as core object or pid strings
        Raise an error if there are any non-core objects
        """
        items = makeIterableList(items)
        _itms = [project.getByPid(itm) if isinstance(itm, str) else itm for itm in items]
        itms = list(filter(lambda obj: isinstance(obj, AbstractWrapperObject), _itms))

        if items and (len(itms) != len(items)):
            _itms = list(filter(lambda obj: not isinstance(obj, AbstractWrapperObject), _itms))
            raise ValueError(f'items contains non-core objects: {_itms}')

        return itms

    @staticmethod
    def _checkDuplicates(items: Sequence[Any]):
        """Check the list of items, as core objects
        Raise an error if there are any duplicates
        CCPNInternal - to be used after _checkItem on flat list
        """
        duplicateCheck = Counter(items)
        if any(v > 1 for k, v in duplicateCheck.items()):
            raise ValueError(f'items contains duplicates {tuple(k for k, v in duplicateCheck.items() if v > 1)}')

    def _checkNestedCollections(self, items: Sequence[Any]):
        """Check the list of items, as core objects
        Raise an error if there are any cycles
        CCPNInternal - to be used after _checkItem on flat list, not used yet but searchCycles available
        """
        pass

    @logCommand(get='self')
    def addItems(self, items: Sequence[Any]):
        """
        Add an object or list of core objects to the collection.
        Action is ignored if the list is empty.

        Raise an error if there are any non-core objects

        :param items: single object or list of core objects, as objects or pid strings.
        """
        items = Collection._checkItems(self.project, items)
        if self in items:
            raise ValueError(f'Cannot add {self} to itself')
        self._checkDuplicates(items)

        if items:
            _items = self._wrappedData.collectionItems
            _exists = tuple(itm for itm in items if itm._wrappedData in _items)
            if _exists:
                if len(_exists) > 1:
                    raise ValueError(f'items {_exists} already in collection {self.pid}')
                else:
                    raise ValueError(f'item {_exists[0]} already in collection {self.pid}')

            with undoBlock():
                # NOTE:ED - any item could cause a nested loop - can't check until each object has been added
                #   then need to reset if there is an error
                for itm in items:
                    self._wrappedData.addCollectionItem(itm._wrappedData)

            # possibly check cycles here
            # and return to previous state if there are any

    @logCommand(get='self')
    def removeItems(self, items: Sequence[Any]):
        """
        Remove an object or list of core objects from the collection.
        The items must belong to the collection.
        Action is ignored if the list is empty.

        Raise an error if there are any non-core objects

        :param items: single object or list of core objects, as objects or pid strings.
        """
        items = Collection._checkItems(self.project, items)

        if items:
            _items = self._wrappedData.collectionItems
            _exists = tuple(itm for itm in items if itm._wrappedData not in _items)
            if _exists:
                if len(_exists) > 1:
                    raise ValueError(f'items {_exists} not in collection {self.pid}')
                else:
                    raise ValueError(f'item {_exists[0]} not in collection {self.pid}')

            with undoBlock():
                for itm in items:
                    self._wrappedData.removeCollectionItem(itm._wrappedData)

    @logCommand(get='self')
    def getByObjectType(self, objectTypes=None, recursive=True, depth=0):
        """Return a list of items of type objectType

        ObjectTypes is a list of core objects expressed as object classes or short/long classnames.
        For example, class Note can be specified as Note, 'Note' or 'NO'

        ObjectTypes can be a single item or tuple/list, or None to return all items.

        Any Nones in lists will be ignored

        If recursive is True, will search through all nested collections, set by default
        recursion=False or depth=1 will only search through the top list, ignoring nested collections
        Set depth=0 for fully recursive, default=0

        Examples:

        ::

            collection.getByObjectTypes()
            collection.getByObjectTypes(objectTypes=Note, recursive=False)
            collection.getByObjectTypes(objectTypes='NO')
            collection.getByObjectTypes(objectTypes=['Note', Spectrum])
            collection.getByObjectTypes(objectTypes='Note', depth=2)

        :param objectTypes: single item, or list of core objects as object class or classnames
        :param recursive: True/False
        :return: tuple of core items.
        """

        if isinstance(objectTypes, (str, type(AbstractWrapperObject))):
            # change a single item to a list, if is a str or a core object
            objectTypes = [objectTypes, ]
        if not isinstance(objectTypes, (list, tuple, type(None))):
            raise ValueError('objectTypes must be list/tuple of core objects or classnames, or single core object or None')
        # remove any Nones from the list
        if objectTypes is not None:
            objectTypes = list(filter(lambda itm: itm is not None, objectTypes))

        _objectTypes = None
        if objectTypes:

            # check the list of object types against the project classNames
            _allObjectTypes = self.project._className2Class
            _all = list(_allObjectTypes.keys()) + list(_allObjectTypes.values())
            _objectTypes = list(filter(lambda itm: (itm in _all), objectTypes))

            if len(_objectTypes) != len(objectTypes):
                _badObjectTypes = list(filter(lambda itm: itm not in _all, objectTypes))
                raise ValueError(f'objectTypes contains bad items: {_badObjectTypes}')

            # change all valid strings to core object types
            _objectTypes = tuple(_allObjectTypes[itm] if isinstance(itm, str) else itm for itm in _objectTypes)

        # create an iterator
        recurse = _searchCollections(self.items, _objectTypes, depth=0 if recursive else depth)
        for _ in recurse:
            pass

        # return the filtered list
        return recurse.items if recurse else ()

    def searchCycles(self, depth=0):
        """Check whether there are any cycles in the collections
        """
        # create an iterator
        recurse = _searchCycles(self, depth=depth)
        for _ in recurse:
            pass

        # return the list of cycles
        return recurse._cycles if recurse else ()

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(Collection)
def _newCollection(self: Project, name: str = None, items: Sequence[Any] = None, comment: str = None) -> Collection:
    """Create new Collection.

    See the Collection class for details.

    Name is a non-empty string.
    If name is not supplied, the next available name will be generated.

    Items is a list of CCPN core-objects, e.g. Note, Peak, PeakList, etc.
    The list of items may also contain other collections.
    Comment is any user supplide string, if required.

    An error is raised if there are any non-core objects.

    Examples:

    ::

        project.newCollection()
        project.newCollection(name='smallCollection', items=(Note0, Peak1, Collection2), comment='A small collection')

    :param name: unique name for the Collection
    :param items: optional single object or list of core objects, as objects or pid strings.
    :param comment: optional user comment
    :return: a new Collection instance.
    """

    # generate a unique name is not supplied
    name = Collection._uniqueName(project=self, name=name)

    apiParent = self._wrappedData
    if items:
        # create a new Collection with supplied core objects
        items = Collection._checkItems(self.project, items)

        apiCollection = apiParent.newCollection(name=name, collectionItems=[itm._wrappedData for itm in items],
                                                details=comment)
    else:
        # create a new Collection
        apiCollection = apiParent.newCollection(name=name, details=comment)

    result = self._project._data2Obj.get(apiCollection)
    if result is None:
        raise RuntimeError('Unable to generate new Collection')

    return result
