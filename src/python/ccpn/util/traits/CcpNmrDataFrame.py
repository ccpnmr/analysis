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

import pandas as pd

from ccpn.util.AttributeDict import AttributeDict
from ccpn.util.traits.TraitJsonHandlerBase import TraitJsonHandlerBase
from ccpn.util.traits.CcpNmrJson import fileHandler, CcpNmrJson
from ccpn.util.traits.CcpNmrTraits import Adict, Instance, default, List


class DataFrameTrait(Instance):
    """A trait that defines a json serialisable Pandas DataFrame
    """
    default_value = pd.DataFrame()
    info_text = 'A json serialisable DataFrame'

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default_value', pd.DataFrame())
        kwargs['klass'] = pd.DataFrame
        Instance.__init__(self, *args, **kwargs)

    # trait-specific json handler
    class jsonHandler(TraitJsonHandlerBase):
        """Serialise DataFrame instance to be json compatible.
        Needs some complicated encoding/decoding as result of int64 rows encoding
        """
        def encode(self, obj, trait):
            df = getattr(obj, trait)
            value = dict(
                columns=list(df.columns),
                nrows=int(df.shape[0]),
                data=[(int(r), v) for r, v in df.to_dict(orient='index').items()],
                dtypes=dict([(c, str(d)) for c, d in dict(df.dtypes).items()])
            )
            return value

        def decode(self, obj, trait, value):
            # restore the DataFrame; if nrows=0 create one with the known columns.  This assures
            # the columns of an empty table (i.e. no rows, but columns defined) to be restored
            # Otherwise, create from the data tuples using Pandas from_dict() method
            nrows = value['nrows']
            columns = value['columns']
            data = value['data']
            dtypes = value['dtypes']
            if nrows == 0:
                df = pd.DataFrame(columns=columns)
            else:
                df = pd.DataFrame.from_dict(dict(data), orient='index')
            setattr(obj, trait, df)
    # end class
# end class


# we are subclassing fromJson, so need to redefine the .json fileHandler
@fileHandler('.json', 'toJson', 'fromJson')
class CcpNmrDataFrame(CcpNmrJson):
    """Class for json serialisable and easy Pandas DataFrame
    """

    version = 3.0

    # --------------------------------------------------------------------------------------------

    _state = Adict().tag(saveToJson=True)  # uses Adict json handler

    @default('_state')
    def _state_default(self):
        return AttributeDict(
            sortColumn=None,  # sorted on column; None indicated row-sorted (default)
            sortAscending=True,  # sorted ascending
        )

    # --------------------------------------------------------------------------------------------

    # actual table data (Pandas DataFrame)
    dataFrame = DataFrameTrait().tag(saveToJson=True)  # uses DataFrameTrait json handler

    # dropped collumn names, retained for later
    _droppedColumns = List(default_value=[])

    @property
    def sizes(self):
        "Return (numberOfRows, numberOfColumns) tuple"
        return tuple(self.dataFrame.shape)

    @property
    def rows(self):
        "Return rows of dataFrame as a list"
        return list(self.dataFrame.index)

    @property
    def columns(self):
        "Return columns of dataFrame as a list"
        return list(self.dataFrame.columns)

    def _dropColumns(self, drops):
        "Remove drops from dataFrame"
        # print('>>> drops:', drops)
        if len(drops) > 0:
            self.dataFrame.drop(drops, axis=1, inplace=True)
            self._droppedColumns += drops
            for d in drops:
                if d in self._formats:
                    del (self._formats[d])
            self._sortDataFrame()

    def deleteColumns(self, *columns):
        "Delete columns, retaining others"
        for c in columns:
            if c not in self.columns:
                raise KeyError('invalid column "%s" to delete' % c)
        self._dropColumns(list(columns))  # with one argument, collumns is a tuple ('name',)
        return self

    def selectColumns(self, *columns):
        "Select columns, deleting others"
        for c in columns:
            if c not in self.columns:
                raise KeyError('invalid column "%s" to select' % c)

        drops = []
        for c in self.columns:
            if c not in columns:
                drops.append(c)
        self._dropColumns(drops)
        return self

    def addColumn(self, column, fmt=None, values=None, beforeColumn=None):
        "Add a column, optional beforeColumn (default at end), optionally setting values"
        if column in self.columns:
            raise KeyError('column "%s" already exists' % column)

        if beforeColumn is None:
            loc = len(self.columns)
        else:
            if beforeColumn not in self.columns:
                raise KeyError('invalid beforeColumn "%s"' % beforeColumn)
            loc = self.columns.index(beforeColumn)

        self.dataFrame.insert(loc, column, values)
        self.setFormat(column, fmt)
        return self

    def getRow(self, row):
        "Return row as a AttributeDict"
        # NB 'into' keyword not functioning in the pandas version used during development
        row = AttributeDict(**self.dataFrame.loc[row].to_dict())
        return row

    def setRow(self, row, **kwds):
        "For each (key,value) of kwds, set (row,key) to value"
        for key, value in kwds.items():
            if key not in self.columns:
                raise KeyError('invalid key "%s"' % key)
            self.dataFrame.loc[row, key] = value
        self._sortDataFrame()

    def appendRow(self, **kwds):
        "For append each (key,value) of kwds as new row"
        if len(self.rows) > 0:
            row = max(self.rows) + 1
        else:
            row = 0
        self.setRow(row, **kwds)

    def insertRow(self, row, **kwds):
        """Insert (key, values) as row
        This will re-index (+1) all current rows >= row 
        Also replaces dataFrame with new instance
        """
        newRows = [r if r < row else r + 1 for r in self.rows]
        self.dataFrame = self.dataFrame.reindex(index=newRows)
        self.setRow(row, **kwds)

    def _sortDataFrame(self):
        "Sort dataFrame according to settings"
        if self._state.sortColumn is not None and self._state.sortColumn not in self.columns:
            # The sortColumn may have been deleted; revert to row sorting
            self._state.sortColumn = None
            self._state.sortAscending = True

        if self._state.sortColumn is not None:
            self.dataFrame.sort_values(by=self._state.sortColumn, ascending=self._state.sortAscending, inplace=True)
        else:
            self.dataFrame.sort_index(ascending=self._state.sortAscending, inplace=True)

    def sort(self, sortColumn, ascending=True):
        "Sort dataFrame by sortColumn; use None to revert to row-sorted"
        if sortColumn not in self.columns:
            raise KeyError('invalid sortColumn "%s"' % sortColumn)
        self._state.sortColumn = sortColumn
        self._state.sortAscending = ascending
        self._sortDataFrame()
        return self

    def sortRows(self):
        "Convience method to revert to ascending sorted rows"
        return self.sort(None, ascending=True)

    def allRows(self, sorted=True):
        "Iterate over each row, maintain the currently sorted order if sorted=True"
        # rows are returned in dataFrame sorted order
        rows = self.rows
        # sort the rows back in index order if sorted is False
        if not sorted: rows.sort()
        for row in rows:
            yield self.getRow(row)

    # --------------------------------------------------------------------------------------------

    def __init__(self, columns=[], **metadata):

        CcpNmrJson.__init__(self, **metadata)
        self.dataFrame = pd.DataFrame(columns=columns)

    def __str__(self):
        return '<%s: sizes=%s>' % (self.__class__.__name__, self.sizes)

    # --------------------------------------------------------------------------------------------

    def fromJson(self, string, **kwds):
        """Subclassed to execute _sortDataFrame"""
        CcpNmrJson.fromJson(self, string, **kwds)
        self._sortDataFrame()
        return self

    # --------------------------------------------------------------------------------------------

    # def save(self, path, **kwds): defined by CcpNmrJson
    # def restore(self, path, **kwds): defined by CcpNmrJson

# end class