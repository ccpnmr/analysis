"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-01-13 17:00:00 +0000 (Thu, January 13, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-10-26 15:52:47 +0100 (Tue, October 26, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Optional, List, Tuple, Any, Sequence, Union
from collections import namedtuple
import fnmatch

from ccpn.core.Project import Project
from ccpn.core.lib.ContextManagers import undoBlock, ccpNmrV3CoreSetter
from ccpn.core._implementation.CollectionList import CO_COMMENT, CO_ISDELETED, \
    CO_ITEMS, CO_UNIQUEID, CO_NAME, _checkItems, _checkDuplicates
from ccpn.core._implementation.V3CoreObjectABC import V3CoreObjectABC
from ccpn.util.decorators import logCommand
from ccpn.util.OrderedSet import OrderedSet


CollectionParameters = namedtuple('CollectionParameters', f'{CO_UNIQUEID} {CO_ISDELETED} {CO_NAME} {CO_ITEMS} {CO_COMMENT} ')


class _searchCollections():
    """
    Iterator to recursively search collections for items of type specified in objectTypes

    depth defines the maximum number of nested collections that the search will through.
    Set depth=1, will return only the items in the specified collection.
    Set depth=0 for fully recursive, default=0

    Search is protected against infinite loops of collections

    objectTypes must be a tuple of types
    collection must be a list of core objects
    search must be None or regex string, * is automatically added at beginning and end, unless disabled
    caseSensitive must be True/False
    """
    _MAXITERATIONS = 100

    # iterator to search through nested collections and collate all items
    def __init__(self, collection, objectTypes=None,
                 search=None, useLongPid=None, caseSensitive=False, disableLeadingTrailingSearch=None,
                 depth=0):
        """Initialise the iterator
        """
        if not (isinstance(depth, int) and depth >= 0):
            raise ValueError('depth must be an int >= 0')

        self._items = OrderedSet(collection)
        self._objectTypes = objectTypes
        self._search = None
        self._caseSensitive = caseSensitive
        self._useLongPid = useLongPid
        self._disableLeadingTrailingSearch = disableLeadingTrailingSearch
        if search:
            # add extra wildcard searches to the leading/trailing edges
            if not search.endswith('*') and not disableLeadingTrailingSearch:
                search = search + '*'
            if not search.startswith('*') and not disableLeadingTrailingSearch:
                search = '*' + search
            self._search = search
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
        elif self._search and self._useLongPid:
            return tuple(filter(lambda obj: fnmatch.fnmatch(obj.longPid, self._search) or
                                            (False if self._caseSensitive else
                                             fnmatch.fnmatch(obj.longPid.lower(), self._search.lower())), self._items))
        elif self._search:
            return tuple(filter(lambda obj: fnmatch.fnmatch(obj.pid, self._search) or
                                            (False if self._caseSensitive else
                                             fnmatch.fnmatch(obj.pid.lower(), self._search.lower())), self._items))
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


class Collection(V3CoreObjectABC):
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
    _isGuiClass = False

    # the attribute name used by current
    _currentAttributeName = 'collections'

    def __init__(self, project, collectionList, _uniqueId):
        """Create a new instance of v3 collection

        _unique Id links the collection to the dataFrame storage and MUST be specified
        before the collection can be used
        """
        super().__init__(project, collectionList, _uniqueId)

    #=========================================================================================
    # CCPN Properties
    #=========================================================================================

    #=========================================================================================
    # Class Properties and methods
    #=========================================================================================

    @property
    def items(self) -> Tuple[Any, ...]:
        """List of items attached to the collection"""
        try:
            _getByPid = self._project.getByPid
            _itms = self._wrapperList._getAttribute(self._uniqueId, CO_ITEMS, list)

            # hiding the Nones handles the undo/redo behaviour for items
            return tuple(filter(None, map(_getByPid, _itms or ())))
        except:
            return ()

    @items.setter
    @logCommand(get='self', isProperty=True)
    @ccpNmrV3CoreSetter()
    def items(self, values):
        """Set the items in the collection"""
        values = _checkItems(self.project, values)
        if self in values:
            raise ValueError(f'Cannot add {self} to itself')
        _checkDuplicates(values)

        _oldItems = set(self.items)
        self._wrapperList._setAttribute(self._uniqueId, CO_ITEMS, [itm.pid for itm in values])

        # notify the items have been added to/removed from collection
        _notify = set(values) ^ _oldItems - {self}
        self._finaliseChildren.extend((itm, 'change') for itm in _notify)

    def __len__(self):
        """Return the number of items in the collection
        """
        return len(self.items)

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    def _rename(self, value):
        """Rename the collection
        """
        # validate the name
        name = self._uniqueName(project=self.project, name=value)

        # rename functions from here
        oldName = self.name
        self._oldPid = self.pid

        self._wrapperList.renameCollection(self, name=name)

        return (oldName,)

    #=========================================================================================
    # Implementation functions - necessary as there is no abstractWrapper object
    #=========================================================================================

    def delete(self):
        """Delete the collection
        """
        self._wrapperList.deleteCollection(uniqueId=self._uniqueId)
        # raise RuntimeError(f'{self.className}.delete: Please use CollectionList.deleteCollection()')  # optional error-trap

    def _updateItems(self):
        """Restore the links to the nmrAtoms
        CCPN Internal - called from first creation from _restoreObject
        """
        pass

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

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
        items = _checkItems(self.project, items)
        if self in items:
            raise ValueError(f'Cannot add {self} to itself')
        _checkDuplicates(items)

        if items:
            _currentItms = self.items
            _exists = tuple(filter(lambda itm: itm in _currentItms, items))
            if _exists:
                # check already exists
                if len(_exists) > 1:
                    raise ValueError(f'items {_exists} already in collection {self}')
                else:
                    raise ValueError(f'item {_exists[0]} already in collection {self}')

            with undoBlock():
                # NOTE:ED - any item could cause a nested loop - can't check until each object has been added
                #   then need to reset if there is an error
                for itm in items:
                    _currentItms += (itm,)
                self.items = _currentItms

    @logCommand(get='self')
    def removeItems(self, items: Sequence[Any]):
        """
        Remove an object or list of core objects from the collection.
        The items must belong to the collection.
        Action is ignored if the list is empty.

        Raise an error if there are any non-core objects.

        :param items: single object or list of core objects, as objects or pid strings.
        """
        items = _checkItems(self.project, items)

        if items:
            _currentItms = list(self.items)
            _exists = tuple(filter(lambda itm: itm not in _currentItms, items))
            if _exists:
                if len(_exists) > 1:
                    raise ValueError(f'items {_exists} not in collection {self}')
                else:
                    raise ValueError(f'item {_exists[0]} not in collection {self}')

            with undoBlock():
                for itm in items:
                    _currentItms.remove(itm)
                self.items = _currentItms

    @logCommand(get='self')
    def getByObjectType(self, objectTypes=None,
                        search=None, useLongPid=None, caseSensitive=None, disableLeadingTrailingSearch=None,
                        recursive=None, depth=None,
                        ):
        """Return a list of items of types specified in objectTypes list.

        ObjectTypes is a list of core objects expressed as object classes or short/long classnames.
        If objectTypes is not specified then all objects will be returned.

        For example, class Note can be specified as Note, 'Note', 'NO', 'note' or 'no'.
        caseSensitive is False by default, if caseSensitive is True, objectTypes as class names must be specified exactly.

        ObjectTypes can be a single item or tuple/list, or None to return all items.
        Any Nones in lists will be ignored.

        search is a regex search string applied to the pids of objects in the collection.
        useLongPid can be specified with the search option to use the londPid descriptor of core objects as the search item.
        if caseSensitive is True, the exact pid or longPid is used for simple searches, although more detailed regex searches
        can be used to override this.

        Simple searches can use * as wildcard to represent 1 or more characters. Use ? to specify a single charaacter.
        Leading and trailing *'s are added by default. This can be disabled with disableLeadingTrailingSearch=True

        Set depth=0 or recursive=True to search through all nested collections,
        recursion=False or depth=1 will only search through the top collection, ignoring nested collections.
        Full recursion is the default setting.

        Please specify either recursive OR depth.

        Examples:

        ::

            collection.getByObjectTypes()
            collection.getByObjectTypes(objectTypes=Note)
            collection.getByObjectTypes(objectTypes='NO', recursive=False)
            collection.getByObjectTypes(objectTypes='Note', depth=2)
            collection.getByObjectTypes(objectTypes=['Note', Spectrum])
            collection.getByObjectTypes(search='someNotes', useLongPid=True, caseSensiive=True)

        :param objectTypes: optional single item, or list of core objects as object class or classnames
        :param search: optional regex search string
        :param useLongPid: optional True/False, only use with search
        :param caseSensitive: optional True/False
        :param disableLeadingTrailingSearch: optional True/False
        :param recursive: optional True/False, only use with search
        :param depth: optional int >= 0
        :return: tuple of core items.
        """

        # check that the parameters are the correct, compatible types
        if (recursive is not None and depth is not None):
            raise ValueError('Please specify either recursive or depth')
        if (objectTypes is not None and search is not None):
            raise ValueError('Please specify either objectTypes or search')
        if depth is not None and not (isinstance(depth, int) and depth >= 0):
            raise ValueError('depth must be int >= 0; use 0 for full depth')
        if not isinstance(search, (str, type(None))):
            raise ValueError('search must be a regex string')

        for param, paramName in [(useLongPid, 'useLongPid'),
                                 (caseSensitive, 'caseSensitive'),
                                 (recursive, 'recursive'),
                                 (disableLeadingTrailingSearch, 'disableLeadingTrailingSearch')]:
            if param not in [None, True, False]:
                raise ValueError(f'{paramName} must be True/False')

        if useLongPid is not None and not search:
            raise ValueError('useLongPid only valid when search is specified')
        if disableLeadingTrailingSearch is not None and not search:
            raise ValueError('disableLeadingTrailingSearch only valid when search is specified')

        if isinstance(objectTypes, str) or (objectTypes is not None and hasattr(objectTypes, 'pid')):
            # change a single item to a list, if is a str or a core object (object with .pid), strings are checked later
            objectTypes = [objectTypes, ]

        if not isinstance(objectTypes, (list, tuple, type(None))):
            raise ValueError('objectTypes must be list/tuple of core objects or classnames, or single core object or None')

        # remove any Nones from the list
        if objectTypes is not None:
            objectTypes = list(filter(lambda itm: itm is not None, objectTypes))

        _objectTypes = None
        if objectTypes:

            # check the list of object types against the project classNames
            if caseSensitive:
                _allObjectTypes = self.project._className2Class
                _allList = self.project._className2ClassList

                # case sensitive search - check against all defined core objects in project
                _objectTypes = list(filter(lambda itm: (itm in _allList), objectTypes))

                if len(_objectTypes) != len(objectTypes):
                    _badObjectTypes = list(filter(lambda itm: itm not in _allList, objectTypes))
                    raise ValueError(f'objectTypes contains bad items: {_badObjectTypes}')

                # change all valid strings to core object types
                _objectTypes = tuple(_allObjectTypes[itm] if isinstance(itm, str) else itm for itm in _objectTypes)

            else:
                _allObjectTypes = self.project._classNameLower2Class
                _allList = self.project._classNameLower2ClassList

                # case insensitive search - change all to lowercase
                _objectTypes = list(filter(lambda itm: (itm.lower() if isinstance(itm, str) else itm) in _allList, objectTypes))

                if len(_objectTypes) != len(objectTypes):
                    _badObjectTypes = list(filter(lambda itm: (itm.lower() if isinstance(itm, str) else itm) not in _allList, objectTypes))
                    raise ValueError(f'objectTypes contains bad items: {_badObjectTypes}')

                # change all valid strings to core object types
                _objectTypes = tuple(_allObjectTypes[itm.lower()] if isinstance(itm, str) else itm for itm in _objectTypes)

        # create a search iterator
        recurse = _searchCollections(self.items,
                                     objectTypes=_objectTypes,
                                     search=search,
                                     useLongPid=useLongPid,
                                     caseSensitive=caseSensitive,
                                     disableLeadingTrailingSearch=disableLeadingTrailingSearch,
                                     depth=depth or (1 if recursive == False else 0))
        for _ in recurse:
            pass

        # return the filtered list
        return recurse.items if recurse else ()

    def searchCycles(self, depth=0):
        """Check whether there are any cycles in the collections
        """
        # create a search iterator
        recurse = _searchCycles(self, depth=depth)
        for _ in recurse:
            pass

        # return the list of cycles
        return recurse._cycles if recurse else ()

    #===========================================================================================
    # new<Object> and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================


#=========================================================================================
# Connections to parents:
#=========================================================================================

def _newCollection(project: Project, collectionList, _uniqueId: Optional[int] = None):
    """Create a new collection attached to the collectionList.

    :param project: core project
    :param collectionList: parent collectionList
    :param _uniqueId: _unique int identifier
    :return: a new Collection instance.
    """

    result = Collection(project, collectionList, _uniqueId=_uniqueId)
    if result is None:
        raise RuntimeError(f'{collectionList.__class__.__name__}._newCollection: unable to generate new Collection item')

    return result


def _getByTuple(collectionList,
                name: str,
                items: Union[List[Union[Any, str, None]], Tuple[Union[Any, str, None]]] = None,
                comment: str = None):
    """Create a new tuple object from the supplied parameters
    Check whether a valid tuple can be created, otherwise raise the appropriate errors
    CCPN Internal
    """
    if items:
        items = _checkItems(collectionList._project, items)
        _checkDuplicates(items)

    newRow = (None,
              None,
              str(name),
              str([itm.pid for itm in items]) if items else None,
              comment,)
    newRow = CollectionParameters(*newRow)

    return newRow
