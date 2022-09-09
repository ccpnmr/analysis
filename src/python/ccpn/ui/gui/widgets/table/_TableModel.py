"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-09-09 21:15:59 +0100 (Fri, September 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-09-08 17:27:34 +0100 (Thu, September 08, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from collections import defaultdict, OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from time import time_ns
from types import SimpleNamespace
import typing

from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, catchExceptions
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.guiSettings import getColours, GUITABLE_ITEM_FOREGROUND
from ccpn.ui.gui.widgets.Font import setWidgetFont, TABLEFONT, getFontHeight
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.ColumnViewSettings import ColumnViewSettingsPopup
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.SearchWidget import attachDFSearchWidget
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.FileDialog import TablesFileDialog
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger
from ccpn.util.Common import copyToClipboard
from ccpn.util.OrderedSet import OrderedSet


ORIENTATIONS = {'h'                 : QtCore.Qt.Horizontal,
                'horizontal'        : QtCore.Qt.Horizontal,
                'v'                 : QtCore.Qt.Vertical,
                'vertical'          : QtCore.Qt.Vertical,
                QtCore.Qt.Horizontal: QtCore.Qt.Horizontal,
                QtCore.Qt.Vertical  : QtCore.Qt.Vertical,
                }

# define a role to return a cell-value
DTYPE_ROLE = QtCore.Qt.UserRole + 1000
VALUE_ROLE = QtCore.Qt.UserRole + 1001
INDEX_ROLE = QtCore.Qt.UserRole + 1002

EDIT_ROLE = QtCore.Qt.EditRole
_EDITOR_SETTER = ('setColor', 'selectValue', 'setData', 'set', 'setValue', 'setText', 'setFile')
_EDITOR_GETTER = ('get', 'value', 'text', 'getFile')


#=========================================================================================
# _TableModel
#=========================================================================================

class _TableModel(QtCore.QAbstractTableModel):
    """A simple table-model to view pandas DataFrames
    """

    _defaultForegroundColour = QtGui.QColor(getColours()[GUITABLE_ITEM_FOREGROUND])
    _CHECKROWS = 5
    _MINCHARS = 4
    _MAXCHARS = 100
    _chrWidth = 12
    _chrHeight = 12

    showEditIcon = False
    defaultFlags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
    defaultEditable = False

    def __init__(self, data, view=None):
        """Initialise the pandas model.
        Allocates space for foreground/background colours.

        :param data: pandas DataFrame
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError('data must be of type pd.DataFrame')

        super().__init__()

        self.df = data
        self._view = view
        if view:
            fontMetric = QtGui.QFontMetricsF(view.font())
            bbox = fontMetric.boundingRect

            # get an estimate for an average character width
            self._chrWidth = 1 + bbox('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').width() / 36
            self._chrHeight = bbox('A').height() + 8

        self._sortColumn = 0
        self._sortOrder = QtCore.Qt.AscendingOrder

        # create a pixmap for the editable icon (currently a pencil)
        self._editableIcon = Icon('icons/editable').pixmap(int(self._chrHeight), int(self._chrHeight))

    @property
    def df(self):
        """Return the underlying pandas dataFrame
        """
        return self._df

    @df.setter
    def df(self, value):
        """Replace the dataFrame and update the model.

        :param value: pandas dataFrame
        :return:
        """
        self.beginResetModel()

        self._df = value

        # set the initial sort-order
        self._oldSortIndex = [row for row in range(value.shape[0])]
        self._sortIndex = [row for row in range(value.shape[0])]

        # create numpy arrays to match the data that will hold background colour
        self._colour = np.empty(value.shape, dtype=np.object)
        self._headerToolTips = {orient: np.empty(value.shape[ii], dtype=np.object)
                                for ii, orient in enumerate([QtCore.Qt.Vertical, QtCore.Qt.Horizontal])}

        # notify that the data has changed
        self.endResetModel()

    def setToolTips(self, orientation, values):
        """Set the tooltips for the horizontal/vertical headers.

        Orientation can be defined as: 'h', 'horizontal', 'v', 'vertical', QtCore.Qt.Horizontal, or QtCore.Qt.Vertical.

        :param orientation: str or Qt constant
        :param values: list of str containing new headers
        :return:
        """
        orientation = ORIENTATIONS.get(orientation)
        if orientation is None:
            raise ValueError(f'orientation not in {list(ORIENTATIONS.keys())}')

        try:
            header = self._headerToolTips[orientation]
            for ind, hText in enumerate(values):
                header[ind] = hText
        except:
            raise ValueError(f'{self.__class__.__name__}.setToolTips: Error setting values {orientation} -> {values}')

    def _insertRow(self, row, newRow):
        """Insert a new row into the table.

        :param row: index of row to be inserted
        :param newRow: new row as pandas-dataFrame or list of items
        :return:
        """
        if self._view.isSortingEnabled():
            # notify that the table is about to be changed
            self.layoutAboutToBeChanged.emit()

            self._df.loc[row] = newRow  # dependent on the index
            iLoc = self._df.index.get_loc(row)
            self._colour = np.insert(self._colour, iLoc, np.empty((self.columnCount()), dtype=np.object), axis=0)
            self._setSortOrder(self._sortColumn, self._sortOrder)

            # emit a signal to spawn an update of the table and notify headers to update
            self.layoutChanged.emit()

        else:
            # NOTE:ED - not checked
            pass
            # self._df.loc[row] = newRow
            # iLoc = self._df.index.get_loc(row)
            # self.beginInsertRows(QtCore.QModelIndex(), iLoc, iLoc)
            # self._colour = np.insert(self._colour, iLoc, np.empty((self.columnCount()), dtype=np.object), axis=0)
            # self.endInsertRows()

    def _updateRow(self, row, newRow):
        """Update a row in the table.

        :param row: index of row to be updated
        :param newRow: new row as pandas-dataFrame or list of items
        :return:
        """
        try:
            iLoc = self._df.index.get_loc(row)  # will give a keyError if the row is not found

        except KeyError:
            getLogger().debug(f'row {row} not found')

        else:
            if self._view.isSortingEnabled():
                # notify that the table is about to be changed
                self.layoutAboutToBeChanged.emit()

                self._df.iloc[iLoc] = newRow
                self._setSortOrder(self._sortColumn, self._sortOrder)

                # emit a signal to spawn an update of the table and notify headers to update
                self.layoutChanged.emit()

            else:
                # NOTE:ED - not checked
                pass
                # # print(f'>>>   _updateRow    {newRow}')
                # iLoc = self._df.index.get_loc(row)
                # if iLoc >= 0:
                #     # self.beginResetModel()
                #
                #     # notify that the table is about to be changed
                #     self.layoutAboutToBeChanged.emit()
                #
                #     self._df.loc[row] = newRow  # dependent on the index
                #     self._setSortOrder()
                #
                #     # emit a signal to spawn an update of the table and notify headers to update
                #     self.layoutChanged.emit()
                #
                #     # self.endResetModel()
                #
                #     # # print(f'>>>      _updateRow    {iLoc}')
                #     # self._df.loc[row] = newRow
                #     #
                #     # # notify change to cells
                #     # _sortedLoc = self._sortIndex.index(iLoc)
                #     # startIdx, endIdx = self.index(_sortedLoc, 0), self.index(_sortedLoc, self.columnCount() - 1)
                #     # self.dataChanged.emit(startIdx, endIdx)

    def _deleteRow(self, row):
        """Delete a row from the table.

        :param row: index of the row to be deleted
        :return:
        """
        try:
            iLoc = self._df.index.get_loc(row)

        except KeyError:
            getLogger().debug(f'row {row} not found')

        else:
            if self._view.isSortingEnabled():
                # notify rows are going to be inserted
                sortedLoc = self._sortIndex.index(iLoc)
                self.beginRemoveRows(QtCore.QModelIndex(), sortedLoc, sortedLoc)

                self._df.drop([row], inplace=True)
                self._sortIndex[:] = [(val if val < iLoc else val - 1) for val in self._sortIndex if val != iLoc]
                self._colour = np.delete(self._colour, iLoc, axis=0)

                self.endRemoveRows()

            else:
                # NOTE:ED - not checked
                # notify rows are going to be inserted
                self.beginRemoveRows(QtCore.QModelIndex(), iLoc, iLoc)

                self._df.drop([row], inplace=True)
                self._colour = np.delete(self._colour, iLoc, axis=0)

                self.endRemoveRows()

    def rowCount(self, parent=None):
        """Return the row count for the dataFrame
        """
        return self._df.shape[0]

    def columnCount(self, parent=None):
        """Return the column count for the dataFrame
        """
        return self._df.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Process the data callback for the model
        """
        if index.isValid():
            # get the source cell
            row, col = self._sortIndex[index.row()], index.column()

            if role == QtCore.Qt.DisplayRole:
                data = self._df.iat[row, col]

                # float/np.float - round to 3 decimal places
                if isinstance(data, (float, np.floating)):
                    return f'{data:.3f}'

                return str(data)

            elif role == VALUE_ROLE:
                val = self._df.iat[row, col]
                try:
                    # convert np.types to python types
                    return val.item()  # type np.generic
                except:
                    return val

            elif role == QtCore.Qt.BackgroundRole:
                if (colourDict := self._colour[row, col]):
                    # get the colour from the dict
                    return colourDict.get(role)

            elif role == QtCore.Qt.ForegroundRole:
                if (colourDict := self._colour[row, col]):
                    # get the colour from the dict
                    return colourDict.get(role)

                # return the default foreground colour
                return self._defaultForegroundColour

            elif role == QtCore.Qt.ToolTipRole:
                data = self._df.iat[row, col]

                return str(data)

            elif role == EDIT_ROLE:
                data = self._df.iat[row, col]

                # float/np.float - return float
                if isinstance(data, (float, np.floating)):
                    return float(data)

                # int/np.integer - return int
                elif isinstance(data, (int, np.integer)):
                    return int(data)

                return data

            elif role == INDEX_ROLE:
                return (row, col)

            # elif role == QtCore.Qt.DecorationRole:
            #     # return the pixmap - this works, transfer to _MultiHeader
            #     return self._editableIcon

        return None

    def setData(self, index, value, role=QtCore.Qt.EditRole) -> bool:
        """Set data in the DataFrame. Required if table is editable.
        """
        if not index.isValid():
            return False

        if role == EDIT_ROLE:
            # get the source cell
            row, col = self._sortIndex[index.row()], index.column()
            try:
                if self._df.iat[row, col] != value:
                    self._df.iat[row, col] = value
                    self.dataChanged.emit(index, index)

                    return True

            except Exception as es:
                getLogger().debug2(f'error accessing cell {index}  ({row}, {col})   {es}')

        return False

    def headerData(self, col, orientation, role=None):
        """Return the column headers
        """
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            try:
                # quickest way to get the column
                return self._df.columns[col]
            except:
                return None

        elif role == QtCore.Qt.ToolTipRole and orientation == QtCore.Qt.Horizontal:
            try:
                # quickest way to get the column
                return self._headerToolTips[orientation][col]
            except:
                return None

        # if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
        #     return self._df.index[col] if not self._df.empty else None

        elif role == QtCore.Qt.SizeHintRole:
            # process the heights/widths of the headers
            if orientation == QtCore.Qt.Horizontal:
                try:
                    # get the estimated width of the column, also for the last visible column
                    width = self._estimateColumnWidth(col)

                    header = self._view.horizontalHeader()
                    visibleCols = [col for col in range(self.columnCount()) if not header.isSectionHidden(col)]
                    if visibleCols:
                        # get the width of all the previous visible columns
                        lastCol = visibleCols[-1]
                        if col == lastCol and self._view is not None:
                            # stretch the last column to fit the table - sum the previous columns
                            colWidths = sum([self._estimateColumnWidth(cc)
                                             for cc in visibleCols[:-1]])
                            viewWidth = self._view.viewport().size().width()
                            width = max(width, viewWidth - colWidths)

                    # return the size
                    return QtCore.QSize(width, int(self._chrHeight))

                except:
                    # return the default QSize
                    return QtCore.QSize(int(self._chrWidth), int(self._chrHeight))

        elif role == QtCore.Qt.DecorationRole and self._isColumnEditable(col) and self.showEditIcon:
            # return the pixmap
            return self._editableIcon

        return None

    def _estimateColumnWidth(self, col):
        """Estimate the width for the column from the header and fixed number of rows
        """
        # get the width of the header
        try:
            # quickest way to get the column
            colName = self._df.columns[col]
        except:
            colName = None

        maxLen = max(len(colName) if colName else 0, self._MINCHARS)  # never smaller than 4 characters

        # iterate over a few rows to get an estimate
        for row in range(min(self.rowCount(), self._CHECKROWS)):
            data = self._df.iat[row, col]

            # float/np.float - round to 3 decimal places
            if isinstance(data, (float, np.floating)):
                newLen = len(f'{data:.3f}')
            else:
                data = str(data)
                if '\n' in data:
                    # get the longest row from the cell
                    dataRows = data.split('\n')
                    newLen = max([len(_chrs) for _chrs in dataRows])
                else:
                    newLen = len(data)

            # update the current maximum
            maxLen = max(newLen, maxLen)

        # return the required minimum width
        width = int(min(self._MAXCHARS, maxLen) * self._chrWidth)
        return width

    def setForeground(self, row, column, colour):
        """Set the foreground colour for dataFrame cell at position (row, column).

        :param row: row as integer
        :param column: column as integer
        :param colour: colour compatible with QtGui.QColor
        :return:
        """
        if not (0 <= row < self.rowCount() and 0 <= column < self.columnCount()):
            raise ValueError(f'({row}, {column}) must be less than ({self.rowCount()}, {self.columnCount()})')

        if not (colourDict := self._colour[row, column]):
            colourDict = self._colour[row, column] = {}
        if colour:
            colourDict[QtCore.Qt.ForegroundRole] = QtGui.QColor(colour)
        else:
            colourDict.pop(QtCore.Qt.ForegroundRole, None)

    def setBackground(self, row, column, colour):
        """Set the background colour for dataFrame cell at position (row, column).

        :param row: row as integer
        :param column: column as integer
        :param colour: colour compatible with QtGui.QColor
        :return:
        """
        if not (0 <= row < self.rowCount() and 0 <= column < self.columnCount()):
            raise ValueError(f'({row}, {column}) must be less than ({self.rowCount()}, {self.columnCount()})')

        if not (colourDict := self._colour[row, column]):
            colourDict = self._colour[row, column] = {}
        if colour:
            colourDict[QtCore.Qt.BackgroundRole] = QtGui.QColor(colour)
        else:
            colourDict.pop(QtCore.Qt.BackgroundRole, None)

    @staticmethod
    def _universalSort(values):
        """Method to apply sorting
        """
        # generate the universal sort key values for the column
        series = pd.Series(universalSortKey(val) for val in values)
        return series

    def _setSortOrder(self, column: int, order: QtCore.Qt.SortOrder = ...):
        """Get the new sort order based on the sort column and sort direction
        """
        self._oldSortIndex = self._sortIndex
        col = self._df.columns[column]
        newData = self._universalSort(self._df[col])
        self._sortIndex = list(newData.sort_values(ascending=True if order == QtCore.Qt.AscendingOrder else False).index)

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        """Sort the underlying pandas DataFrame
        Required as there is no proxy model to handle the sorting
        """
        # remember the current sort settings
        self._sortColumn = column
        self._sortOrder = order

        # notify that the table is about to be changed
        self.layoutAboutToBeChanged.emit()

        self._setSortOrder(column, order)

        # emit a signal to spawn an update of the table and notify headers to update
        self.layoutChanged.emit()

    def mapToSource(self, indexes):
        """Map the cell index to the co-ordinates in the pandas dataFrame
        Return list of tuples of dataFrame positions
        """
        idxs = [(self._sortIndex[idx.row()], idx.column()) if idx.isValid() else (None, None) for idx in indexes]
        return idxs

    def flags(self, index):
        # Set the table to be editable - need the editable columns here
        if self._isColumnEditable(index.column()):
            return QtCore.Qt.ItemIsEditable | self.defaultFlags
        else:
            return self.defaultFlags

    def _isColumnEditable(self, col):
        """Return whether the column number is editable
        """
        try:
            # return True if the column contains an edit function
            return self._view._dataFrameObject.setEditValues[col] is not None
        except:
            return self.defaultEditable

