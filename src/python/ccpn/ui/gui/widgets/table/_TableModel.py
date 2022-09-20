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
__dateModified__ = "$dateModified: 2022-09-20 10:48:16 +0100 (Tue, September 20, 2022) $"
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
from PyQt5 import QtCore, QtGui
from operator import or_
from functools import reduce

from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.ui.gui.guiSettings import getColours, GUITABLE_ITEM_FOREGROUND
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.util.Logging import getLogger


ORIENTATIONS = {'h'                 : QtCore.Qt.Horizontal,
                'horizontal'        : QtCore.Qt.Horizontal,
                'v'                 : QtCore.Qt.Vertical,
                'vertical'          : QtCore.Qt.Vertical,
                QtCore.Qt.Horizontal: QtCore.Qt.Horizontal,
                QtCore.Qt.Vertical  : QtCore.Qt.Vertical,
                }

# standard definitions for roles applicable to QTableModel
USER_ROLE = QtCore.Qt.UserRole
EDIT_ROLE = QtCore.Qt.EditRole
DISPLAY_ROLE = QtCore.Qt.DisplayRole
TOOLTIP_ROLE = QtCore.Qt.ToolTipRole
STATUS_ROLE = QtCore.Qt.StatusTipRole
BACKGROUND_ROLE = QtCore.Qt.BackgroundRole
FOREGROUND_ROLE = QtCore.Qt.ForegroundRole
CHECK_ROLE = QtCore.Qt.CheckStateRole
ICON_ROLE = QtCore.Qt.DecorationRole
SIZE_ROLE = QtCore.Qt.SizeHintRole
ALIGNMENT_ROLE = QtCore.Qt.TextAlignmentRole
NO_PROPS = QtCore.Qt.NoItemFlags
CHECKABLE = QtCore.Qt.ItemIsUserCheckable
ENABLED = QtCore.Qt.ItemIsEnabled
SELECTABLE = QtCore.Qt.ItemIsSelectable
EDITABLE = QtCore.Qt.ItemIsEditable
CHECKED = QtCore.Qt.Checked
UNCHECKED = QtCore.Qt.Unchecked
PARTIALLYECHECKED = QtCore.Qt.PartiallyChecked

# define roles to return cell-values
DTYPE_ROLE = QtCore.Qt.UserRole + 1000
VALUE_ROLE = QtCore.Qt.UserRole + 1001

# a role to map the table-index to the cell in the df
INDEX_ROLE = QtCore.Qt.UserRole + 1002

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
    defaultFlags = ENABLED | SELECTABLE  # add CHECKABLE to enable check-boxes
    _defaultEditable = True

    _defaultDf = None
    _dfIndex = None
    _colour = None
    _defaultColour = None

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

        # initialise sorting
        self._sortColumn = 0
        self._sortOrder = QtCore.Qt.AscendingOrder
        # NOTE:ED - could I use another self._filterIndex here? so _df doesn't need to be changed

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

        self._colour = None
        if self._defaultDf is not None:
            # must have unique indices - otherwise ge arrays for multiple rows in here
            idx = self._defaultDf.index
            lastIdx = list(value.index)
            if (mapping := [idx.get_loc(cc) for cc in lastIdx if cc in idx]):
                newMapping = np.zeros(len(lastIdx), dtype=np.int32)

                # remove any duplicated rows - there SHOULDN'T be any, but could be a generic df
                for ind, rr in enumerate(mapping):
                    if isinstance(rr, int):
                        newMapping[ind] = rr
                    elif isinstance(rr, np.ndarray):
                        # get the index of the first duplicate - may not be the correct order with other matching index :|
                        indT = list(rr).index(True)
                        newMapping[ind] = indT
                        for mm in mapping[ind + 1:]:
                            if isinstance(mm, np.ndarray):
                                mm[indT] = False
                    else:
                        # anything else is a missing row
                        raise RuntimeError(f'{self.__class__.__name__}.df: new df is not a sub-set of the original')

                if self._defaultColour is not None:
                    # can be used for other table-information
                    self._colour = self._defaultColour[newMapping, :]

        if self._colour is None:
            # create numpy arrays to match the data that will hold background colour
            self._colour = np.empty(value.shape, dtype=np.object)

        # set the initial sort-order
        self._oldSortIndex = [row for row in range(value.shape[0])]
        self._sortIndex = [row for row in range(value.shape[0])]

        # # create numpy arrays to match the data that will hold background colour
        # self._colour = np.empty(value.shape, dtype=np.object)
        self._headerToolTips = {orient: np.empty(value.shape[ii], dtype=np.object)
                                for ii, orient in enumerate([QtCore.Qt.Vertical, QtCore.Qt.Horizontal])}

        self._df = value
        self._dfIndex = list(value.index)

        # notify that the data has changed
        self.endResetModel()

    def setDefaultDf(self, value):
        """Set the default unfiltered table
        """
        if value is not None:
            self._defaultDf = value
            if self._colour is not None:
                self._defaultColour = self._colour.copy()

        else:
            # reset the values to star again
            self._defaultDf = None
            self._defaultColour = None

    def setToolTips(self, orientation, values):
        """Set the tooltips for the horizontal/vertical headers.

        Orientation can be defined as: 'h', 'horizontal', 'v', 'vertical', QtCore.Qt.Horizontal, or QtCore.Qt.Vertical.

        :param orientation: str or Qt constant
        :param values: list of str containing new headers
        :return:
        """
        if not (orientation := ORIENTATIONS.get(orientation)):
            raise ValueError(f'orientation not in {list(ORIENTATIONS.keys())}')
        if not (isinstance(values, (list, tuple)) and all(isinstance(val, (type(None), str)) for val in values)):
            raise ValueError(f'values must be a list|tuple of str|None')

        try:
            self._headerToolTips[orientation] = values

        except Exception as es:
            raise ValueError(f'{self.__class__.__name__}.setToolTips: Error setting values {orientation} -> {values}\n{es}')

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

            # sLoc = self._sortIndex[iLoc]  # signals?
            # self.beginInsertRows(QtCore.QModelIndex(), sLoc, sLoc)
            self._colour = np.insert(self._colour, iLoc, np.empty((self.columnCount()), dtype=np.object), axis=0)
            self._setSortOrder(self._sortColumn, self._sortOrder)
            # self.endInsertRows()

            # NOTE:ED insert into the unfiltered df?
            # connect to signals in the view?

            # emit a signal to spawn an update of the table and notify headers to update
            self.layoutChanged.emit()

        else:
            # NOTE:ED - not checked, keep for reference
            pass
            # self._df.loc[row] = newRow
            # iLoc = self._df.index.get_loc(row)
            # self.beginInsertRows(QtCore.QModelIndex(), iLoc, iLoc)
            # self._colour = np.insert(self._colour, iLoc, np.empty((self.columnCount()), dtype=np.object), axis=0)
            # self.endInsertRows()
            # indexA = model.index(0, 0)
            # indexB = model.index(n - 1, c - 1)
            # model.dataChanged.emit(indexA, indexB)  # all visible cells

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

    def data(self, index, role=DISPLAY_ROLE):
        """Process the data callback for the model
        """
        if index.isValid():
            # get the source cell
            row, col = self._sortIndex[index.row()], index.column()

            if role == DISPLAY_ROLE:
                # need to discard columns that include check-boxes
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

            elif role == BACKGROUND_ROLE:
                if (colourDict := self._colour[row, col]):
                    # get the colour from the dict
                    return colourDict.get(role)

            elif role == FOREGROUND_ROLE:
                if (colourDict := self._colour[row, col]):
                    # get the colour from the dict
                    return colourDict.get(role)

                # return the default foreground colour
                return self._defaultForegroundColour

            elif role == TOOLTIP_ROLE:
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
                # return a dict of item-data?
                return (row, col)

            # if role == CHECK_ROLE and col == 0:
            #     # need flags to include CHECKABLE and return QtCore.Qt.checked/unchecked/PartiallyChecked here
            #     return CHECKED

            # elif role == ICON_ROLE:
            #     # return the pixmap - this works, transfer to _MultiHeader
            #     return self._editableIcon

            # elif role == ALIGNMENT_ROLE:
            #     pass

        return None

    def setData(self, index, value, role=EDIT_ROLE) -> bool:
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

                    # need to store in the parent (unfiltered table)
                    self._setDataParentDf(row, col, value)

                    self.dataChanged.emit(index, index)

                    return True

            except Exception as es:
                getLogger().debug2(f'error accessing cell {index}  ({row}, {col})   {es}')

        # elif role == CHECK_ROLE:
        #     # set state in cell/object
        #     return True

        return False

    def _setDataParentDf(self, row, col, value):
        try:
            # can't think of a better way of doing this yet :|

            # set in the top-level as well - map the index to the _defaultDf - background/foreground colours?
            idx = self._df.index[row]
            if self._defaultDf is not None and not self._defaultDf.empty:
                row = self._defaultDf.index.get_loc(idx)
                self._defaultDf.iat[row, col] = value

        except Exception as es:
            getLogger().debug2(f'error accessing parent cell ({row}, {col})   {es}')

    def headerData(self, col, orientation, role=None):
        """Return the column headers
        """
        if role == DISPLAY_ROLE and orientation == QtCore.Qt.Horizontal:
            try:
                # quickest way to get the column
                return self._df.columns[col]
            except:
                return None

        elif role == TOOLTIP_ROLE and orientation == QtCore.Qt.Horizontal:
            try:
                # quickest way to get the column
                return self._headerToolTips[orientation][col]
            except:
                return None

        # if orientation == QtCore.Qt.Vertical and role == DISPLAY_ROLE:
        #     return self._df.index[col] if not self._df.empty else None

        elif role == SIZE_ROLE:
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

        elif role == ICON_ROLE and self._isColumnEditable(col) and self.showEditIcon:
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
            colourDict[FOREGROUND_ROLE] = QtGui.QColor(colour)
        else:
            colourDict.pop(FOREGROUND_ROLE, None)

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
            colourDict[BACKGROUND_ROLE] = QtGui.QColor(colour)
        else:
            colourDict.pop(BACKGROUND_ROLE, None)

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
        """Map the cell index to the co-ordinates in the pandas dataFrame.
        Return list of tuples of dataFrame positions.
        """
        idxs = [(self._sortIndex[idx.row()], idx.column()) if idx.isValid() else (None, None) for idx in indexes]
        return idxs

    def flags(self, index):
        # Set the table to be editable - need the editable columns here
        if self._isColumnEditable(index.column()):
            return EDITABLE | self.defaultFlags
        else:
            return self.defaultFlags

    def _isColumnEditable(self, col):
        """Return whether the column number is editable.
        """
        try:
            # return True if the column contains an edit function
            # NOTE:ED - need to remove _dataFrameObject, move options to TableABC? BUT Column class is still good
            return self._view._dataFrameObject.setEditValues[col] is not None
        except:
            return self._defaultEditable


#=========================================================================================
# _TableObjectModel
#=========================================================================================

def _getDisplayRole(colDef, obj):
    if isinstance((value := colDef.getFormatValue(obj)), bool):
        return None
    else:
        return value


def _getCheckRole(colDef, obj):
    if isinstance((value := colDef.getValue(obj)), bool):
        return CHECKED if value else UNCHECKED

    return None


class _TableObjectModel(_TableModel):
    """Table-model that supports defining a list of objects for the table.

    Objects are defined as a list, and table is populated with information from the Column classes.
    """

    defaultFlags = ENABLED | SELECTABLE | CHECKABLE

    getAttribRole = {DISPLAY_ROLE   : _getDisplayRole,
                     CHECK_ROLE     : _getCheckRole,
                     ICON_ROLE      : lambda colDef, obj: colDef.getIcon(obj),
                     EDIT_ROLE      : lambda colDef, obj: colDef.getEditValue(obj),
                     TOOLTIP_ROLE   : lambda colDef, obj: colDef.tipText,
                     BACKGROUND_ROLE: lambda colDef, obj: colDef.getColor(obj),
                     ALIGNMENT_ROLE : lambda colDef, obj: colDef.alignment
                     }

    setAttribRole = {EDIT_ROLE : lambda colDef, obj, value: colDef.setEditValue(obj, value),
                     CHECK_ROLE: lambda colDef, obj, value: colDef.setEditValue(obj, True if (value == CHECKED) else False)
                     }

    # # NOTE:ED - not tested
    # def _setSortOrder(self, column: int, order: QtCore.Qt.SortOrder = ...):
    #     """Sort the object-list
    #     """
    #     colDef = self._view._columnDefs._columns
    #     getValue = colDef[column].getValue
    #     self._view._objects.sort(key=getValue, reverse=False if order == QtCore.Qt.AscendingOrder else True)

    def data(self, index, role=DISPLAY_ROLE):
        result = None  # super(AdminModel, self).data(index, role)  # super not required?

        # special control over the object properties
        if index.isValid():
            # get the source cell
            row, col = self._sortIndex[index.row()], index.column()
            obj = self._view._objects[row]
            colDef = self._view._columnDefs._columns[col]

            if (func := self.getAttribRole.get(role)):
                return func(colDef, obj)

        return result

    def setData(self, index, value, role=EDIT_ROLE) -> bool:
        # super(AdminModel, self).setData(index, role, value)  # super not required?

        if index.isValid():
            row, col = self._sortIndex[index.row()], index.column()
            obj = self._view._objects[row]
            colDef = self._view._columnDefs._columns[col]

            if (func := self.setAttribRole.get(role)):
                func(colDef, obj, value)

                self._view.viewport().update()  # repaint the view
                return True

        return False
