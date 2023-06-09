"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-06-09 12:06:24 +0100 (Fri, June 09, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-06-05 13:01:10 +0100 (Mon, June 05, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import pandas as pd
import json
import typing
from typing import Union, List, Tuple, Optional, Any
# from functools import partial
# from collections import Counter

# from ccpn.core._implementation.DataFrameABC import DataFrameABC
from ccpn.core.Project import Project
# from ccpn.core.lib.Pid import Pid
# from ccpn.core.lib.ContextManagers import newV3Object, undoBlockWithoutSideBar, undoStackBlocking
# from ccpn.core._implementation.V3CoreObjectABC import _UNIQUEID, _ISDELETED, _NAME, _COMMENT
# from ccpn.util.decorators import logCommand
from ccpn.util.Logging import getLogger
# from ccpn.util.Common import makeIterableList

# import time
import numpy as np
# import scipy
# import math
import warnings
from operator import mul
from scipy.sparse import csr_matrix, csc_matrix, SparseEfficiencyWarning
# from collections import OrderedDict
from functools import reduce
# from contextlib import contextmanager, suppress
from ccpn.util.Common import NOTHING
from ccpn.framework.Application import getProject


# from ccpn.util.FrozenDict import FrozenDict
# from ccpn.util.OrderedSet import OrderedSet, FrozenOrderedSet


VALIDMATRIXTYPES = csr_matrix, csc_matrix

# definitions for building the dict
INDICES = 'indices'
INDPTR = 'indptr'
DATA = 'data'
SHAPE = 'shape'
DTYPE = 'dtype'
DFORMAT = 'dformat'
ROWCLASSNAME = 'rowClassName'
COLUMNCLASSNAME = 'columnClassName'
ROWPIDS = 'rowPids'
COLUMNPIDS = 'columnPids'

ROWDATA = 'rowData'
COLUMNDATA = 'columnData'
_PID2OBJ = '_pid2Obj'
_OBJ2PID = '_obj2Pid'
_INDEX2PID = '_index2Pid'
_PID2INDEX = '_pid2Index'  # not sure if I need this
_PIDS = '_pids'
_KLASS = '_klass'
_KLASSNAME = '_klassName'
_BUILDFROMPROJECT = '_BUILDFROMPROJECT'

warnings.simplefilter('ignore', SparseEfficiencyWarning)


class _CrossReference():
    """
    Class to hold the cross-references between project core-objects.
    
    It is defined by two core class-types, e.g. Mark and Strip.
    
    Internally stored as:

        _indexing = {ROWDATA   : {_KLASS    : None,
                                  _KLASSNAME: None,
                                  _PIDS     : [],
                                  _PID2OBJ  : {},
                                  _OBJ2PID  : {},
                                  },
                     COLUMNDATA: {_KLASS    : None,
                                  _KLASSNAME: None,
                                  _PIDS     : [],
                                  _PID2OBJ  : {},
                                  _OBJ2PID  : {},
                                  },
                     }
    """

    @classmethod
    def _newFromJson(cls, jsonData):
        """Create a new instance from a json class.
        """
        project = getProject()
        values = cls.fromJson(jsonData)

        return _CrossReference(project=project, **values)

    def __init__(self, project: Project,
                 rowClassName: str = None, columnClassName: str = None,
                 indices: List[int] = NOTHING, indptr: List[int] = NOTHING, data: List[int] = NOTHING,
                 shape: Tuple[int, int] = NOTHING,
                 dtype: str = 'int8', dformat: str = 'csr',
                 rowPids: list = NOTHING, columnPids: list = NOTHING,
                 ):
        """Create a new instance of cross-reference.
        
        If shape is not specified, then a new cross-reference is created from 
        rowClassName and columnClassName, and from the project attributes.
        
        :param project: current project instance. 
        :param str rowClassName: name of the first core object type, e.g., 'Mark' or 'Strip'.
        :param str columnClassName: name of the second core object type, e.g., 'Mark' or 'Strip'. 
        :param list[int] indices: parameters defining a sparse matrix in column-row format. 
        :param list[int] indptr: parameters defining a sparse matrix in column-row format.
        :param list[Any] data: parameters defining a sparse matrix in column-row format.
        :param tuple[int, int] shape: size of the matrix. 
        :param str dtype: type of the matrix data, most-probably int8.
        :param str dformat: either sparse-row row or sparse-column.
        :param list[str] rowPids: list of pids for the first axis.
        :param list[str] columnPids: list of pids for the second axis.
        """
        self._indices = indices
        self._indptr = indptr
        self._data = data
        self._shape = shape
        self._dtype = dtype
        self._dformat = dformat
        self._storageType = csr_matrix if dformat == 'csr' else csc_matrix

        self._axes = {}
        self._buildFromProject = None
        self._matrix = None

        if shape == NOTHING:
            # nothing defined yet so get from project properties
            self._makeNewIndexing(project, rowClassName, columnClassName)

        else:
            # rebuild from the loaded sparse-matrix
            self._makeIndexing(project, rowClassName, columnClassName, rowPids, columnPids)

    def _initialiseAxis(self, project, axis: str, className: str) -> dict:
        """Initialise the klass and name for axis.
        """
        dd = self._axes[axis] = {}
        dd[_KLASS] = project._className2Class.get(className)
        dd[_KLASSNAME] = className

        # if klass is None:
        #     RuntimeError(f'{self.__class__.__name__}: className is not defined')

        return dd

    def _newAxis(self, project: Project, axis: str) -> dict:
        """Create a new axis from the project core-object list defined by the axis class.
        """
        dd = self._axes[axis]
        klass = dd[_KLASS]

        coreObjs = getattr(project, klass._pluralLinkName, [])  # e.g. project.peaks
        _corePids = [obj.pid for obj in coreObjs]

        # make sure to use the correct matching pids/core-objects - order doesn't matter
        dd[_PIDS] = _corePids
        dd[_PID2OBJ] = dict(zip(_corePids, coreObjs))
        dd[_OBJ2PID] = dict(zip(coreObjs, _corePids))

        return dd

    def _makeNewIndexing(self, project, rowClassName, columnClassName):
        """Make new cross-reference from core-class definitions.
        """
        self._axes = {}
        self._initialiseAxis(project, ROWDATA, rowClassName)
        self._initialiseAxis(project, COLUMNDATA, columnClassName)

        self._buildFromProject = True

    def _verifyAxis(self, project: Project, axis: str) -> dict:
        """Verify that the pids are correct.
        """
        # the order is not necessarily the same as the project order
        dd = self._axes[axis]
        klass = dd[_KLASS]

        coreObjs = getattr(project, klass._pluralLinkName, [])  # e.g. project.peaks

        # check the row pids - order may be different, but not an issue
        _corePids = [obj.pid for obj in coreObjs]
        pids = dd[_PIDS]

        if set(_corePids) != set(pids):
            raise RuntimeError(f'{self.__class__.__name__}: unknown pids in {dd[_KLASSNAME]}')

        # make sure to use the correct matching pids/core-objects - order doesn't matter
        dd[_PID2OBJ] = dict(zip(_corePids, coreObjs))
        dd[_OBJ2PID] = dict(zip(coreObjs, _corePids))

        return dd

    def _makeIndexing(self, project: Project,
                      rowClassName: str, columnClassName: str,
                      rowPids: list[str], columnPids: list[str]):
        """Make the indexing from the current list of indexes and pids.
        """
        # should handle empty lists
        self._axes = {}

        ddRow = self._initialiseAxis(project, ROWDATA, rowClassName)
        ddRow[_PIDS] = rowPids
        ddCol = self._initialiseAxis(project, COLUMNDATA, columnClassName)
        ddCol[_PIDS] = columnPids

        self._buildFromProject = False

    #=========================================================================================
    # Sparse operations
    #=========================================================================================

    @staticmethod
    def sparse_memory_usage(matrix) -> int:
        """Return the number of bytes used for a scipy.sparse-matrix.

        Returns -1 if the matrix is missing any attributes.

        :param sparse matrix: scipy.sparse.csr_matrix or scipy.sparse.csc_matrix.
        :return int: number of bytes used or -1.
        :raise TypeError: If matrix is not the correct type.
        """
        if not isinstance(matrix, VALIDMATRIXTYPES):
            raise TypeError(f'insertRow: matrix type is not in ({", ".join(tt.__name__ for tt in VALIDMATRIXTYPES)})')

        try:
            return matrix.data.nbytes + matrix.indptr.nbytes + matrix.indices.nbytes
        except AttributeError:
            return -1

    def insertCol(self, matrix, insert_col) -> Union[csr_matrix, csc_matrix]:
        """Insert an empty column into a scipy.sparse-matrix.

        matrix must be a scipy sparse-matrix of type csr_matrix or csc_matrix.
        insert_col must be a valid column number for the matrix.

        :param sparse matrix: sparse-matrix.
        :param int insert_col: column number.
        :return csr_matrix or csc_matrix: modified sparse-matrix.
        :raise ValueError, TypeError: Incorrect input parameters.
        """
        if not isinstance(matrix, VALIDMATRIXTYPES):
            raise TypeError(f'insertCol: matrix type is not in ({", ".join(tt.__name__ for tt in VALIDMATRIXTYPES)})')
        if not isinstance(insert_col, int):
            raise TypeError('insertCol: insert_col is not an int')
        if not (0 <= insert_col <= matrix.shape[1]):
            raise ValueError(f'insertCol: insert_col {insert_col} is out-of-bounds, must be [0, {matrix.shape[1]}]')

        return self._storageType((matrix.data, np.where(matrix.indices < insert_col, matrix.indices, matrix.indices + 1), matrix.indptr),
                                 shape=(matrix.shape[0], matrix.shape[1] + 1))

        # if inplace:  # Idea for inplace
        #     matrix.indices = np.where(matrix.indices < insert_col, matrix.indices, matrix.indices + 1)
        #     matrix._shape = (matrix.shape[0], matrix.shape[1] + 1)
        #     return matrix
        # else:
        #     return csr_matrix((matrix.data, np.where(matrix.indices < insert_col, matrix.indices, matrix.indices + 1), matrix.indptr),
        #                   shape=(matrix.shape[0], matrix.shape[1] + 1))

    def appendCol(self, matrix) -> Union[csr_matrix, csc_matrix]:
        """Add a new column to right of the matrix.

        matrix must be a scipy sparse-matrix of type csr_matrix or csc_matrix.
        
        :param sparse matrix: sparse-matrix.
        :return csr_matrix or csc_matrix: modified sparse-matrix.
        """
        return self.insertCol(matrix, matrix.shape[1])

    def deleteCol(self, matrix, delete_col) -> Union[csr_matrix, csc_matrix]:
        """Delete a column from a scipy.sparse-matrix.

        matrix must be a scipy sparse-matrix of type csr_matrix or csc_matrix.
        delete_col must be a valid column number for the matrix.

        :param sparse matrix: sparse-matrix.
        :param int delete_col: column number.
        :return csr_matrix or csc_matrix: modified sparse-matrix.
        :raise ValueError, TypeError: Incorrect input parameters.
        """
        if not isinstance(matrix, VALIDMATRIXTYPES):
            raise TypeError(f'deleteCol: matrix type is not in ({", ".join(tt.__name__ for tt in VALIDMATRIXTYPES)})')
        if not isinstance(delete_col, int):
            raise TypeError('deleteCol: delete_col is not an int')
        if not (0 <= delete_col < matrix.shape[1]):
            raise ValueError(f'deleteCol: delete_col {delete_col} is out-of-bounds, must be [0, {matrix.shape[1] - 1}]')

        # get the indices and data arrays for the remaining elements
        indices = matrix.indices.copy()
        indptr = matrix.indptr.copy()
        data = matrix.data.copy()

        # modify the indices and data arrays to remove the deleted column
        for row in range(matrix.shape[0]):
            row_start = indptr[row]
            row_end = indptr[row + 1]
            if row_end > row_start:
                if (ind := next((col for col in range(row_start, row_end) if indices[col] == delete_col), -1)) != -1:
                    # delete row from the data and decrease indptrs
                    indices = np.delete(indices, ind, 0)
                    data = np.delete(data, ind, 0)
                    indptr[row + 1:] = indptr[row + 1:] - 1

        # move the larger columns to the left
        indices = np.where(indices < delete_col, indices, indices - 1)

        # create a new CSR matrix with the modified indices and data arrays
        return self._storageType((data, indices, indptr), shape=(matrix.shape[0], matrix.shape[1] - 1))

    def insertRow(self, matrix, insert_row) -> Union[csr_matrix, csc_matrix]:
        """Insert an empty row into a scipy.sparse-matrix.

        matrix must be a scipy sparse-matrix of type csr_matrix or csc_matrix.
        insert_row must be a valid row number for the matrix.

        :param sparse matrix: sparse-matrix.
        :param int insert_row: row number.
        :return csr_matrix or csc_matrix: modified sparse-matrix.
        :raise ValueError, TypeError: Incorrect input parameters.
        """
        if not isinstance(matrix, VALIDMATRIXTYPES):
            raise TypeError(f'insertRow: matrix type is not in ({", ".join(tt.__name__ for tt in VALIDMATRIXTYPES)})')
        if not isinstance(insert_row, int):
            raise TypeError('insertRow: insert_row is not an int')
        if not (0 <= insert_row <= matrix.shape[0]):
            raise ValueError(f'insertRow: insert_row {insert_row} is out-of-bounds, must be [0, {matrix.shape[0]}]')

        return self._storageType((matrix.data, matrix.indices, np.insert(matrix.indptr, insert_row, matrix.indptr[insert_row])),
                                 shape=(matrix.shape[0] + 1, matrix.shape[1]))

    def appendRow(self, matrix) -> Union[csr_matrix, csc_matrix]:
        """Add a new row to bottom of the matrix.

        matrix must be a scipy sparse-matrix of type csr_matrix or csc_matrix.

        :param sparse matrix: sparse-matrix.
        :return csr_matrix or csc_matrix: modified sparse-matrix.
        """
        return self.insertRow(matrix, matrix.shape[0])

    def deleteRow(self, matrix, delete_row) -> Union[csr_matrix, csc_matrix]:
        """Delete a row from a scipy.sparse-matrix.

        matrix must be a scipy sparse-matrix of type csr_matrix or csc_matrix.
        delete_row must be a valid row number for the matrix.

        :param sparse matrix: sparse-matrix.
        :param int delete_row: row number.
        :return csr_matrix or csc_matrix: modified sparse-matrix.
        :raise ValueError, TypeError: Incorrect input parameters.
        """
        if not isinstance(matrix, VALIDMATRIXTYPES):
            raise TypeError(f'deleteRow: matrix type is not in ({", ".join(tt.__name__ for tt in VALIDMATRIXTYPES)})')
        if not isinstance(delete_row, int):
            raise TypeError('deleteRow: delete_row is not an int')
        if not (0 <= delete_row < matrix.shape[0]):
            raise ValueError(f'deleteRow: delete_row {delete_row} is out-of-bounds, must be [0, {matrix.shape[0] - 1}]')

        indices = matrix.indices.copy()
        indptr = matrix.indptr.copy()
        data = matrix.data.copy()

        row_start = indptr[delete_row]
        row_end = indptr[delete_row + 1]
        indptr = np.delete(indptr, delete_row + 1, 0)

        if row_end != row_start:
            indptr[delete_row + 1:] = indptr[delete_row + 1:] - (row_end - row_start)

            indices = np.delete(indices, range(row_start, row_end), 0)
            data = np.delete(data, range(row_start, row_end), 0)

        # create a new CSR matrix with the modified indices and data arrays
        return self._storageType((data, indices, indptr), shape=(matrix.shape[0] - 1, matrix.shape[1]))

    @staticmethod
    def sparseInfo(matrix):
        """Information for sparse-matrix
        """
        nnz = matrix.getnnz()
        shp = matrix.shape
        # information can also be retrieved with repr(matrix)
        return f'{matrix.__class__.__name__}: ' \
               f'shape={shp}, ' \
               f'dtype={str(matrix.dtype)!r}, ' \
               f'format={str(matrix.format)!r}, ' \
               f'ndim={matrix.ndim}, ' \
               f'stored-elements={nnz}, ' \
               f'density={nnz / reduce(mul, shp):.2g}, ' \
               f'nbytes={matrix.data.nbytes + matrix.indptr.nbytes + matrix.indices.nbytes}'

    #=========================================================================================
    # Store/restore operations
    #=========================================================================================

    def _getValidIndexing(self, axis: str = None):
        """Return the list of indexed core-objects that are not deleted.
        """
        if axis := self._axes.get(axis):
            pids = axis.get(_PIDS)
            pid2Obj = axis.get(_PID2OBJ)
            goodPids = [pid for pid in pids if not pid2Obj[pid].isDeleted]
            badInds = [ii for ii, pid in enumerate(pids) if pid2Obj[pid].isDeleted]

            return goodPids, badInds

        return [], []

    def toJson(self):
        """Convert the cross-referencing to json for store/restore.
        """
        if self._data is None:
            raise RuntimeError(f'{self.__class__.__name__}:toJson contains no data')

        rowPids, badRowInds = self._getValidIndexing(ROWDATA)
        columnPids, badColInds = self._getValidIndexing(COLUMNDATA)

        # remove the missing columns/rows and update the indexing if there are gaps
        newSparseMatrix = self._matrix.copy()
        # remove columns from right-to-left
        for col in reversed(sorted(badColInds)):
            self.deleteCol(newSparseMatrix, col)
        # remove rows from bottom-to-top
        for row in reversed(sorted(badRowInds)):
            self.deleteRow(newSparseMatrix, row)
        newSparseMatrix.eliminate_zeros()

        dd = {INDICES        : newSparseMatrix.indices.tolist(),
              INDPTR         : newSparseMatrix.indptr.tolist(),
              DATA           : newSparseMatrix.data.tolist(),
              SHAPE          : newSparseMatrix.shape,
              DTYPE          : str(newSparseMatrix.dtype),
              DFORMAT        : str(newSparseMatrix.format),
              ROWPIDS        : rowPids,
              COLUMNPIDS     : columnPids,
              ROWCLASSNAME   : self._axes[ROWDATA][_KLASSNAME],
              COLUMNCLASSNAME: self._axes[COLUMNDATA][_KLASSNAME],
              }
        return json.dumps(dd)

    @staticmethod
    def fromJson(jsonData):
        """Recover from json.
        """
        return json.loads(jsonData)

    def _restoreObject(self, project, apiObj=None):
        """Restore the core objects from the indexing.
        """
        ddRow, ddCol = self._axes[ROWDATA], self._axes[COLUMNDATA]
        if self._buildFromProject:

            self._newAxis(project, ROWDATA)
            self._newAxis(project, COLUMNDATA)

            # create blank matrix
            self._matrix = self._storageType((len(ddRow[_PIDS]), len(ddCol[_PIDS])), dtype=self._dtype)

        else:
            self._verifyAxis(project, ROWDATA)
            self._verifyAxis(project, COLUMNDATA)

            # create matrix from existing data
            self._matrix = self._storageType((self._data, self._indices, self._indptr), shape=self._shape, dtype=self._dtype)

    def _updateClass(self, axis, coreObject, oldPid=None, action='create', func=None):
        """Update the state for a row core-object
        """
        dd = self._axes[axis]
        if coreObject.className != dd[_KLASSNAME]:
            return

        if action == 'create':
            pid = coreObject.pid
            if coreObject in dd[_OBJ2PID]:
                # undo has created the object
                newPid = coreObject.pid
                delPid = f'{newPid}-Deleted'

                del dd[_PID2OBJ][delPid]  # 'deleted' pid
                dd[_PID2OBJ][pid] = coreObject
                dd[_OBJ2PID][coreObject] = pid

                # replace in the pid list
                ind = dd[_PIDS].index(delPid)
                dd[_PIDS][ind] = pid

            else:
                # new object
                pid = coreObject.pid
                dd[_PIDS].append(pid)
                dd[_PID2OBJ][pid] = coreObject
                dd[_OBJ2PID][coreObject] = pid
                self._matrix = func(self._matrix)

        elif action == 'delete':
            if coreObject in dd[_OBJ2PID]:
                # undo has created the object
                del dd[_PID2OBJ][coreObject.pid]  # 'live' pid

                # make new deleted-pid, not really a good place :|
                pid = f'{coreObject.pid}-Deleted'
                dd[_OBJ2PID][coreObject] = pid
                dd[_PID2OBJ][pid] = coreObject

                # replace in the pid list
                ind = dd[_PIDS].index(coreObject.pid)
                dd[_PIDS][ind] = pid

        elif action == 'rename':
            # NOTE:ED - not tested yet - need a valid cross-reference for this
            if coreObject in dd[_OBJ2PID]:
                # undo has created the object
                del dd[_PID2OBJ][oldPid]  # pid before rename

                # make new deleted-pid, not really a good place :|
                pid = coreObject.pid
                dd[_OBJ2PID][coreObject] = pid
                dd[_PID2OBJ][pid] = coreObject

                # replace in the pid list
                ind = dd[_PIDS].index(oldPid)
                dd[_PIDS][ind] = pid

    def _resetItemPids(self, coreObject, oldPid=None, action='create'):
        """Update the pids from the creation/deletion of the pid.
        """
        # pid is contained in one of the lists
        self._updateClass(ROWDATA, coreObject, oldPid, action, func=self.appendRow)
        self._updateClass(COLUMNDATA, coreObject, oldPid, action, func=self.appendCol)

    #=========================================================================================
    # Get/set values in cross-reference
    #=========================================================================================

    def getValues(self, coreObject, axis) -> Tuple[Any, ...]:
        """Get the cross-reference objects from the class.
        """
        # apply caching?
        pid = coreObject.pid

        if axis == 0:
            # primary object is in row-pids, get information from the columnAxis
            ddRow = self._axes[ROWDATA]

            if pid not in ddRow[_PIDS]:
                getLogger().debug(f'not found {coreObject}')
                return ()

            ddCol = self._axes[COLUMNDATA]
            # get the single row matrix and extract indices which reference pids from other axis
            rr = self._matrix.getrow(ddRow[_PIDS].index(pid))

            outPids = [ddCol[_PIDS][ind] for ind in rr.indices]
            return tuple(filter(lambda obj: not obj.isDeleted, (ddCol[_PID2OBJ][pid] for pid in outPids)))

        else:
            # primary object is in column-pids
            ddCol = self._axes[COLUMNDATA]

            if pid not in ddCol[_PIDS]:
                getLogger().debug(f'not found {coreObject}')
                return ()

            ddRow = self._axes[ROWDATA]
            # get the single row matrix and extract indices which reference pids from other axis
            cc = self._matrix.getcol(ddCol[_PIDS].index(pid)).tocsc()

            outPids = [ddRow[_PIDS][ind] for ind in cc.indices]
            return tuple(filter(lambda obj: not obj.isDeleted, (ddRow[_PID2OBJ][pid] for pid in outPids)))

    def setValues(self, coreObject, axis, values):
        """Set the cross-reference objects from the class.
        """
        pid = coreObject.pid

        if axis == 0:
            # primary object is in row-pids, get information from the columnAxis
            ddRow = self._axes[ROWDATA]

            if pid not in ddRow[_PIDS]:
                getLogger().debug(f'not found {coreObject}')
                return ()

            ddCol = self._axes[COLUMNDATA]
            ind = ddRow[_PIDS].index(pid)
            self._matrix[ind, :] = 0  # quicker way of doing this?

            objs = coreObject.project.getByPids(values)
            for obj in objs:
                self._matrix[ind, ddCol[_PIDS].index(ddCol[_OBJ2PID][obj])] = 1

        else:
            # primary object is in column-pids
            ddCol = self._axes[COLUMNDATA]

            if pid not in ddCol[_PIDS]:
                getLogger().debug(f'not found {coreObject}')
                return ()

            ddRow = self._axes[ROWDATA]
            ind = ddCol[_PIDS].index(pid)
            self._matrix[:, ind] = 0  # quicker way of doing this?

            objs = coreObject.project.getByPids(values)
            for obj in objs:
                self._matrix[ddRow[_PIDS].index(ddRow[_OBJ2PID][obj]), ind] = 1

        # quickly clean-up
        self._matrix.eliminate_zeros()
