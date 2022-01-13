"""
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
__dateModified__ = "$dateModified: 2022-01-13 17:23:25 +0000 (Thu, January 13, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pandas as pd
from typing import Sequence, Union, Optional, Any
from functools import partial
from collections import Counter

from ccpn.core._implementation.DataFrameABC import DataFrameABC
from ccpn.core.Project import Project
from ccpn.core.NmrAtom import NmrAtom
from ccpn.core.lib import Pid
from ccpn.core.lib.ContextManagers import newV3Object, undoBlockWithoutSideBar, undoStackBlocking
from ccpn.core._implementation.V3CoreObjectABC import _UNIQUEID, _ISDELETED, _NAME, _COMMENT
from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger
from ccpn.util.Common import makeIterableList


CO_UNIQUEID = _UNIQUEID  # 'uniqueId'
CO_ISDELETED = _ISDELETED  # 'isDeleted'
CO_NAME = _NAME  # 'name'
CO_ITEMS = 'items'
CO_COMMENT = _COMMENT  #'comment'
CO_COLUMNS = (CO_UNIQUEID, CO_ISDELETED, CO_NAME, CO_ITEMS, CO_COMMENT)

CO_PID = 'pid'
CO_OBJECT = '_object'  # this must match the object search for guiTable
CO_TABLECOLUMNS = (CO_UNIQUEID, CO_ISDELETED, CO_PID, CO_NAME, CO_ITEMS, CO_COMMENT, CO_OBJECT)

CO_CLASSNAME = 'Collection'
CO_SHORTCLASSNAME = 'CO'


class _CollectionFrame(DataFrameABC):
    """
    Collection data - as a Pandas DataFrame.
    CCPNInternal - only for access from CollectionList
    """
    # Class added to wrap the model data in a core class
    pass


def _checkItems(project, items: Sequence[Any]) -> Optional[list]:
    """Check the list of items, as core object or pid strings
    Raise an error if there are any non-core objects
    """
    items = makeIterableList(items)
    _itms = [project.getByPid(itm) if isinstance(itm, str) else itm for itm in items]
    # check all items have a pid
    itms = list(filter(lambda obj: hasattr(obj, 'pid'), _itms))

    if items and (len(itms) != len(items)):
        _itms = list(filter(lambda obj: not hasattr(obj, 'pid'), _itms))
        raise ValueError(f'items contains non-core objects: {_itms}')

    return itms


def _checkDuplicates(items: Sequence[Any]):
    """Check the list of items, as core objects
    Raise an error if there are any duplicates
    CCPNInternal - to be used after _checkItem on flat list
    """
    duplicateCheck = Counter(items)
    if any(v > 1 for k, v in duplicateCheck.items()):
        raise ValueError(f'items contains duplicates {tuple(k for k, v in duplicateCheck.items() if v > 1)}')


class CollectionList():

    def __init__(self, project: Project):
        self._project = project

        # internal lists to hold the current collections and deletedCollection
        self._collections = []
        self._deletedCollections = []

    @property
    def className(self):
        return self.__class__.__name__

    @property
    def _data(self):
        """Helper method to get the stored dataframe
        CCPN Internal
        """
        return self._project._collectionStore

    @_data.setter
    def _data(self, data):
        if not isinstance(data, (_CollectionFrame, type(None))):
            if isinstance(data, pd.DataFrame):
                data = _CollectionFrame(data)
                getLogger().warning(f'Data must be of type {_CollectionFrame}. The value pd.DataFrame was converted to {_CollectionFrame}.')
            else:
                raise RuntimeError(f'Unable to set _data: not of type {_CollectionFrame}, pd.DataFrame or None')

        self._project._collectionStore = data

    @property
    def collections(self):
        """Return the collections belonging to CollectionList
        """
        return self._collections

    def getCollection(self, uniqueId: Union[int, None] = None, _includeDeleted: bool = False):
        """Return a collection by uniqueId
        Collection is returned as a namedTuple
        """
        # if nmrAtom and uniqueId:
        #     raise ValueError('CollectionList.getCollection: use either nmrAtom or uniqueId')

        _data = self._data
        if _data is None:
            return

        rows = None
        # if nmrAtom:
        #     # get collection by nmrAtom
        #     nmrAtom = self.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
        #     if not isinstance(nmrAtom, (NmrAtom, type(None))):
        #         raise ValueError('CollectionList.getCollection: nmrAtom must be of type NmrAtom or str')
        #     if nmrAtom:
        #         # search dataframe
        #         rows = _data[_data[CO_NMRATOM] == nmrAtom.pid]

        if uniqueId is not None:
            # get collection by uniqueId
            if not isinstance(uniqueId, int):
                raise ValueError(f'{self.className}.getCollection: uniqueId must be an int')

            # search dataframe
            rows = _data[_data[CO_UNIQUEID] == uniqueId]

        if rows is not None:
            if len(rows) > 1:
                raise RuntimeError(f'{self.className}.getCollection: bad number of collections in list')
            if len(rows) == 1:
                uniqueId = rows.iloc[0].uniqueId
                _shs = [sh for sh in self._collections if sh._uniqueId == uniqueId]
                if _shs and len(_shs) == 1:
                    return _shs[0]
                else:
                    if _includeDeleted:
                        _shs = [sh for sh in self._deletedCollections if sh._uniqueId == uniqueId]
                        if _shs and len(_shs) == 1:
                            return _shs[0]

                    raise ValueError(f'{self.className}.getCollection: collection not found')

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    def _getByUniqueId(self, uniqueId):
        """Get the collection data from the dataFrame by the uniqueId
        """
        try:
            return self._data.loc[uniqueId]
        except:
            raise ValueError(f'{self.className}._getByUniqueId: uniqueId {uniqueId} not found')

    def _getAttribute(self, uniqueId, name, attribType):
        """Get the named attribute from the collection with supplied uniqueId

        Check the attribute for None, nan, inf, etc., and cast to attribType
        CCPN Internal - Pandas dataframe changes values after saving through api
        """
        row = self._getByUniqueId(uniqueId)
        if name in row:
            # get the value and cast to the correct type
            _val = row[name]
            return None if (_val is None or (_val != _val)) else attribType(_val)
        else:
            raise ValueError(f'{self.className}._getAttribute: attribute {name} not found in collection')

    def _setAttribute(self, uniqueId, name, value):
        """Set the attribute of the collection with the supplied uniqueId
        """
        row = self._getByUniqueId(uniqueId)
        if name in row:
            try:
                # use 'at' to put into single element as may be a list
                self._data.at[uniqueId, name] = value
            except:
                raise ValueError(f'{self.className}._setAttribute: error setting attribute {name} in collection {self}')
        else:
            raise ValueError(f'{self.className}._setAttribute: attribute {name} not found in collection {self}')

    def _getAttributes(self, uniqueId, startName, endName, attribTypes):
        """Get the named attributes from the collection with supplied uniqueId
        """
        row = self._getByUniqueId(uniqueId)
        if startName in row and endName in row:
            _val = row[startName:endName]
            _val = tuple(None if (val is None or (val != val)) else attribType(val) for val, attribType in zip(_val, attribTypes))
            return _val
        else:
            raise ValueError(f'{self.className}._getAttributes: attribute {startName}|{endName} not found in collection')

    def _setAttributes(self, uniqueId, startName, endName, value):
        """Set the attributes of the collection with the supplied uniqueId
        """
        row = self._getByUniqueId(uniqueId)
        if startName in row and endName in row:
            try:
                self._data.loc[uniqueId, startName:endName] = value
            except:
                raise ValueError(f'{self.className}._setAttributes: error setting attribute {startName}|{endName} in collection {self}')

        else:
            raise ValueError(f'{self.className}._setAttributes: attribute {startName}|{endName} not found in collection {self}')

    def _undoRedoObjects(self, collections):
        """update to collections after undo/redo
        collections should be a simple, non-nested dict of int:<collection> pairs
        """
        # keep the same collection list
        self._collections[:] = collections

    def _undoRedoDeletedObjects(self, deletedCollections):
        """update to deleted collections after undo/redo
        deletedCollections should be a simple, non-nested dict of int:<deletedCollection> pairs
        """
        # keep the same deleted collection list
        self._deletedCollections[:] = deletedCollections

    @staticmethod
    def _setDeleted(collection, state):
        """Set the deleted state of the collection
        """
        collection._deleted = state

    def _searchCollections(self, uniqueId=None):
        """Return True if the nmrAtom/uniqueId already exists in the collections dataframe
        """
        # if nmrAtom and uniqueId:
        #     raise ValueError('CollectionList._searchCollections: use either nmrAtom or uniqueId')

        if self._data is None:
            return

        # if nmrAtom:
        #     # get collection by nmrAtom
        #     nmrAtom = self.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
        #     if not isinstance(nmrAtom, NmrAtom):
        #         raise ValueError('CollectionList._searchCollections: nmrAtom must be of type NmrAtom, str')
        #
        #     # search dataframe for single element
        #     _data = self._wrappedData.data
        #     rows = _data[_data[CO_NMRATOM] == nmrAtom.pid]
        #     return len(rows) > 0

        if uniqueId is not None:
            # get collection by uniqueId
            if not isinstance(uniqueId, int):
                raise ValueError(f'{self.className}._searchCollections: uniqueId must be an int - {uniqueId}')

            # search dataframe for single element
            _data = self._data
            rows = _data[_data[CO_UNIQUEID] == uniqueId]
            return len(rows) > 0

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    @classmethod
    def _restoreObject(cls, project, apiObj):
        """Subclassed to allow for initialisations on restore, not on creation via newCollectionList
        """
        from ccpn.core.Collection import _newCollection as _newCollection

        # create a set of new collection objects linked to the pandas rows - discard deleted
        _data = project._collectionStore

        if _data is not None:
            # check that is the new DataFrameABC class, update as required - for later use
            # if not isinstance(_data, DataFrameABC):
            #     getLogger().debug(f'updating classType {collectionData} -> _CollectionListFrame')
            #     _data = _CollectionListFrame(_data)

            _data = _data[_data[CO_ISDELETED] == False]
            _data.set_index(_data[CO_UNIQUEID], inplace=True, )

            project._collectionStore = _data

            for ii in range(len(_data)):
                _row = _data.iloc[ii]

                # create a new collection with the uniqueId from the old collection
                collection = _newCollection(project, project._collectionList, _uniqueId=int(_row[CO_UNIQUEID]))
                project._collectionList._collections.append(collection)

                # add the new object to the _pid2Obj dict
                project._finalisePid2Obj(collection, 'create')

                # # restore the nmrAtom, etc., for the new collection
                # collection._updateItemCollections()

        return project._collectionList

    def renameCollection(self, collection, name: str):
        """Rename the specified collection
        """
        _data = self._data
        if _data is None:
            return

        uniqueId = collection.uniqueId
        if uniqueId is not None:
            # get collection by uniqueId
            if not isinstance(uniqueId, int):
                raise ValueError(f'{self.className}.renameCollection: uniqueId must be an int')

            # search dataframe for single element
            _data = self._data
            rows = _data[_data[CO_UNIQUEID] == uniqueId]
            if len(rows) > 1:
                raise RuntimeError(f'{self.className}.renameCollection: bad number of collections in list')
            elif len(rows) == 0:
                raise ValueError(f'{self.className}.renameCollection: uniqueId {uniqueId} not found')

            # should be handled in the Collection class
            # if name in list(_data[CO_NAME]):
            #     raise ValueError(f'{self.className}.renameCollection: name {name} already exists')

            _oldPid = collection.pid
            _data.loc[uniqueId, CO_NAME] = name

            # pid should have automatically have changed
            _newPid = collection.pid
            for ii in range(len(_data)):
                _row = _data.iloc[ii]
                if _oldPid in (_row[CO_ITEMS] or []):
                    # replace the pids in the list - use 'at' to put list into single element
                    _uniqueId = _row[CO_UNIQUEID]
                    _data.at[_uniqueId, CO_ITEMS] = [_newPid if vv == _oldPid else vv for vv in _row[CO_ITEMS]]

    def searchCollections(self, item):
        """Get the list of collections containing the specified item
        """
        _data = self._data
        if _data is None:
            return

        return tuple(col for col in self._collections if item in col.items)

    def _resetItemPids(self, oldPid, newPid):
        """Rename an item in collections by change of pid
        """
        _data = self._data
        if _data is None:
            return

        for ii in range(len(_data)):
            _row = _data.iloc[ii]
            if oldPid in (_row[CO_ITEMS] or []):
                # replace the pids in the list - use 'at' to put list into single element
                _uniqueId = _row[CO_UNIQUEID]
                _data.at[_uniqueId, CO_ITEMS] = [newPid if vv == oldPid else vv for vv in _row[CO_ITEMS]]

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newCollection(self, name: str = None, items: Sequence[Any] = None, comment: str = None):
        """Create new Collection.

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

        data = self._data
        if items:
            items = _checkItems(self._project, items)
            _checkDuplicates(items)

        collection = self._newCollectionObject(data, name, items, comment)

        return collection

    @newV3Object()
    def _newCollectionObject(self, data=None, name: str = None, items: Union[NmrAtom, str, Pid.Pid, None] = None, comment: str = None):
        """Create a new pure V3 Collection object
        Method is wrapped with create/delete notifier
        """
        from ccpn.core.Collection import _getByTuple, _newCollection as _newCollection

        # make new tuple - verifies contents
        _row = _getByTuple(self, name, items, comment)
        _nextUniqueId = self._project._getNextUniqueIdValue(CO_CLASSNAME)
        # add to dataframe - this is in undo stack and marked as modified
        _dfRow = pd.DataFrame(((_nextUniqueId, False, name, None, comment),), columns=CO_COLUMNS)

        if data is None:
            # set as the new subclassed DataFrameABC
            self._data = _CollectionFrame(_dfRow)
        else:
            self._data = self._data.append(_dfRow)

        _data = self._data
        _data.set_index(_data[CO_UNIQUEID], inplace=True, )  # drop=False)

        # create new collection object
        # new Collection only needs collectionData and uniqueId - properties are linked to dataframe
        collection = _newCollection(self._project, self, _uniqueId=int(_nextUniqueId))

        if items:
            collection.items = items

        _oldCollections = self._collections[:]
        self._collections.append(collection)
        _newCollections = self._collections[:]

        with undoBlockWithoutSideBar():
            # add an undo/redo item to recover collections
            with undoStackBlocking() as addUndoItem:
                addUndoItem(undo=partial(self._undoRedoObjects, _oldCollections),
                            redo=partial(self._undoRedoObjects, _newCollections))

        return collection

    @logCommand(get='self')
    def deleteCollection(self, uniqueId: int = None):
        """Delete a collection by nmrAtom or uniqueId
        """
        # if nmrAtom and uniqueId:
        #     raise ValueError('CollectionList.deleteCollection: use either nmrAtom or uniqueId')

        _data = self._data
        if _data is None:
            return

        # if nmrAtom:
        #     # get collection by nmrAtom
        #     nmrAtom = self.project.getByPid(nmrAtom) if isinstance(nmrAtom, str) else nmrAtom
        #     if not isinstance(nmrAtom, NmrAtom):
        #         raise ValueError('CollectionList.deleteCollection: nmrAtom must be of type NmrAtom, str')
        #
        #     # search dataframe for single element
        #     _data = self._wrappedData.data
        #     rows = _data[_data[CO_NMRATOM] == nmrAtom.pid]
        #     if len(rows) > 1:
        #         raise RuntimeError('CollectionList.deleteCollection: bad number of collections in list')
        #     elif len(rows) == 0:
        #         raise ValueError(f'CollectionList.deleteCollection: nmrAtom {nmrAtom.pid} not found')
        #
        #     self._deleteCollectionObject(rows)

        if uniqueId is not None:
            # get collection by uniqueId
            if not isinstance(uniqueId, int):
                raise ValueError(f'{self.className}.deleteCollection: uniqueId must be an int')

            # search dataframe for single element
            _data = self._data
            rows = _data[_data[CO_UNIQUEID] == uniqueId]
            if len(rows) > 1:
                raise RuntimeError(f'{self.className}.deleteCollection: bad number of collections in list')
            elif len(rows) == 0:
                raise ValueError(f'{self.className}.deleteCollection: uniqueId {uniqueId} not found')

            self._deleteCollectionObject(rows)

    def _deleteCollectionObject(self, rows):
        """Update the dataframe and handle notifiers
        """
        _oldCollections = self._collections[:]
        _oldDeletedCollections = self._deletedCollections[:]

        uniqueId = rows.iloc[0].uniqueId
        _shs = [sh for sh in self._collections if sh._uniqueId == uniqueId]
        _val = _shs[0]

        self._collections.remove(_val)
        self._deletedCollections.append(_val)  # not sorted - sort?

        # Check whether needs removing from any nested collections

        _newCollections = self._collections[:]
        _newDeletedCollections = self._deletedCollections[:]

        _val._deleteWrapper(self, _newDeletedCollections, _newCollections, _oldDeletedCollections, _oldCollections)
