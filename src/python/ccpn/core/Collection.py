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
__dateModified__ = "$dateModified: 2021-10-28 19:32:34 +0100 (Thu, October 28, 2021) $"
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

from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Collection as apiCollection
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newObject, undoBlockWithoutSideBar, \
    renameObject, ccpNmrV3CoreSetter
from ccpn.util.Common import makeIterableList
from ccpn.util.decorators import logCommand
from ccpn.util.OrderedSet import OrderedSet


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
        if values:
            self._wrappedData.collectionItems = [itm._wrappedData for itm in values]

    @property
    def numItems(self) -> int:
        """return number of items in the collection"""
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

    @logCommand(get='self')
    def addItems(self, items: Sequence[Any]):
        """
        Add an object or list of core objects to the collection.
        Action is ignored if the list is empty.

        Raise an error if there are any non-core objects

        :param items: single object or list of core objects, as objects or pid strings.
        """
        items = Collection._checkItems(self.project, items)

        if items:
            with undoBlockWithoutSideBar():
                for itm in items:
                    self._wrappedData.addCollectionItem(itm._wrappedData)

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
            for itm in items:
                if itm._wrappedData not in self._wrappedData.collectionItems:
                    raise ValueError(f'{itm.pid} does not belong to collection: {self.pid}')

            with undoBlockWithoutSideBar():
                for itm in items:
                    self._wrappedData.removeCollectionItem(itm._wrappedData)

    @logCommand(get='self')
    def getByObjectType(self, objectType=None, recursive=False):
        """Return a list of items of type objectType
        """

        class _recurseCollections():
            # iterator to search through nested collections and collate all items
            def __init__(self, collection):
                self.items = OrderedSet(collection)

            def __iter__(self):
                # initial iterator settings
                self._len = 0
                return self

            def __next__(self):
                if not recursive:
                    # if not recursive then only return the original list
                    raise StopIteration

                # get the newly added, nested collections
                collections = list(filter(lambda obj: isinstance(obj, Collection),
                                          list(self.items)[self._len:]))
                if not collections:
                    # if no more then reached the bottom
                    raise StopIteration

                self._len = len(self.items)
                for coll in collections:
                    # update the list of items
                    self.items |= OrderedSet(coll.items)

                return self

        # create an iterator
        val = _recurseCollections(self.items)
        for count, _ in enumerate(val):
            if count == 50:
                # set an arbitrary limit to stop searching too deep
                # - should never happen though because using orderedSet
                raise RuntimeError('Max search depth reached')

        if objectType:
            # filter by objectType if specified
            return tuple(filter(lambda obj: isinstance(obj, objectType), val.items))
        else:
            return tuple(val.items)

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
