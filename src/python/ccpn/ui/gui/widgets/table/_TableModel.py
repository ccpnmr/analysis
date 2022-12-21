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
__dateModified__ = "$dateModified: 2022-12-21 12:16:48 +0000 (Wed, December 21, 2022) $"
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
# from operator import or_
# from functools import reduce

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
BACKGROUNDCOLOR_ROLE = QtCore.Qt.BackgroundColorRole
FOREGROUND_ROLE = QtCore.Qt.ForegroundRole
CHECK_ROLE = QtCore.Qt.CheckStateRole
ICON_ROLE = QtCore.Qt.DecorationRole
SIZE_ROLE = QtCore.Qt.SizeHintRole
ALIGNMENT_ROLE = QtCore.Qt.TextAlignmentRole
FONT_ROLE = QtCore.Qt.FontRole
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

    _defaultForegroundColour = None
    _CHECKROWS = 5
    _MINCHARS = 4
    _MAXCHARS = 100
    _chrWidth = 12
    _chrHeight = 12

    showEditIcon = False
    defaultFlags = ENABLED | SELECTABLE  # add CHECKABLE to enable check-boxes
    _defaultEditable = True

    _colour = None

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

            # get an estimate for an average character width/height - must be floats for estimate-column-widths
            self._chrWidth = 1 + bbox('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').width() / 36
            self._chrHeight = bbox('A').height() + 6

        # set default colours
        self._defaultForegroundColour = QtGui.QColor(getColours()[GUITABLE_ITEM_FOREGROUND])

        # initialise sorting/filtering
        self._sortColumn = 0
        self._sortOrder = QtCore.Qt.AscendingOrder
        self._filterIndex = None

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

        # set the initial sort-order
        self._oldSortIndex = list(range(value.shape[0]))
        self._sortIndex = list(range(value.shape[0]))
        self._filterIndex = list(range(value.shape[0]))

        # create numpy arrays to match the data that will hold background colour
        self._colour = np.empty(value.shape, dtype=np.object)
        self._headerToolTips = {orient: np.empty(value.shape[ii], dtype=np.object)
                                for ii, orient in enumerate([QtCore.Qt.Vertical, QtCore.Qt.Horizontal])}

        self._df = value
        self._filterIndex = None

        # notify that the data has changed
        self.endResetModel()

    @property
    def filteredDf(self):
        """Return the filtered dataFrame
        """
        if self._filterIndex is not None:
            # the filtered df
            return self._df.iloc[self._filterIndex]
        else:
            return self._df

    @property
    def displayedDf(self):
        """Return the visible dataFrame as displayed, sorted and filtered
        """
        from ccpn.util.OrderedSet import OrderedSet

        df = self._df
        table = self._view
        rows, cols = df.shape[0], df.shape[1]

        if df.empty:
            return df

        colList = [col for ii, col, in enumerate(list(df.columns)) if
                   not table.horizontalHeader().isSectionHidden(ii)]

        if self._filterIndex is None:
            rowList = [self._sortIndex[row] for row in range(rows)]
        else:
            #  map to sorted indexes
            rowList = list(OrderedSet(self._sortIndex[row] for row in range(rows)) & OrderedSet(
                    self._sortIndex[ii] for ii in self._filterIndex))

        df = df[colList]
        df = df[:].iloc[rowList]
        return df

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
            raise ValueError('values must be a list|tuple of str|None')

        try:
            self._headerToolTips[orientation] = values

        except Exception as es:
            raise ValueError(f'{self.__class__.__name__}.setToolTips: Error setting values {orientation} -> {values}\n{es}') from es

    def _insertRow(self, row, newRow):
        """Insert a new row into the table.

        :param row: index of row to be inserted
        :param newRow: new row as pandas-dataFrame or list of items
        :return:
        """
        if self._view.isSortingEnabled():
            # notify that the table is about to be changed
            self.layoutAboutToBeChanged.emit()

            # keep sorted
            self._df.loc[row] = newRow  # dependent on the index
            self._df.sort_index(inplace=True)
            iLoc = self._df.index.get_loc(row)

            # update the sorted list
            self._sortIndex[:] = [(val if val < iLoc else val + 1) for val in self._sortIndex]

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
                sortedLoc = self._sortIndex.index(iLoc)
                self.beginRemoveRows(QtCore.QModelIndex(), sortedLoc, sortedLoc)

                # remove the row from the dataFrame
                self._df.drop([row], inplace=True)

                if self._filterIndex is not None:
                    # remove from the filtered list - undo?
                    filt = self._sortIndex.index(iLoc)
                    self._filterIndex[:] = [(val if val < filt else val - 1) for val in self._filterIndex if val != filt]

                # remove from the sorted list
                self._sortIndex[:] = [(val if val < iLoc else val - 1) for val in self._sortIndex if val != iLoc]

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
        if self._filterIndex is not None:
            return len(self._filterIndex)
        else:
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
            fRow = self._filterIndex[index.row()] if self._filterIndex is not None and 0 <= index.row() < len(self._filterIndex) else index.row()
            row, col = self._sortIndex[fRow], index.column()

            if role == DISPLAY_ROLE:
                # need to discard columns that include check-boxes
                data = self._df.iat[row, col]

                # float/np.float - round to 3 decimal places
                return f'{data:.3f}' if isinstance(data, (float, np.floating)) else str(data)

            elif role == VALUE_ROLE:
                val = self._df.iat[row, col]
                try:
                    # convert np.types to python types
                    return val.item()  # type np.generic
                except Exception:
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

            elif role == FONT_ROLE:
                if (colourDict := self._colour[row, col]):
                    # get the font from the dict
                    return colourDict.get(role)

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
            fRow = self._filterIndex[index.row()] if self._filterIndex is not None else index.row()
            row, col = self._sortIndex[fRow], index.column()

            try:
                if self._df.iat[row, col] != value:
                    self._df.iat[row, col] = value
                    self.dataChanged.emit(index, index)

                    return True

            except Exception as es:
                getLogger().debug2(f'error accessing cell {index}  ({row}, {col})   {es}')

        # elif role == CHECK_ROLE:
        #     # set state in cell/object
        #     return True

        return False

    def headerData(self, col, orientation, role=None):
        """Return the information for the row/column headers
        """
        if role == DISPLAY_ROLE and orientation == QtCore.Qt.Horizontal:
            try:
                # quickest way to get the column header
                return self._df.columns[col]
            except Exception:
                return None
        elif role == DISPLAY_ROLE and orientation == QtCore.Qt.Vertical:
            try:
                # quickest way to get the column header
                return col + 1
            except Exception:
                return None

        elif role == TOOLTIP_ROLE and orientation == QtCore.Qt.Horizontal:
            try:
                # quickest way to get the column tooltip
                return self._headerToolTips[orientation][col]
            except Exception:
                return None

        elif role == SIZE_ROLE:
            # process the heights/widths of the headers
            if orientation == QtCore.Qt.Horizontal:
                try:
                    txt = str(self.headerData(col, orientation, role=DISPLAY_ROLE))
                    height = len(txt.split('\n')) * int(self._chrHeight)

                    # get the estimated width of the column, also for the last visible column\
                    if (self._view._columnDefs and self._view._columnDefs._columns):
                        colObj = self._view._columnDefs._columns[col]
                        width = colObj.columnWidth
                        if width is not None:
                            return QtCore.QSize(width, height)

                    width = self._estimateColumnWidth(col)

                    header = self._view.horizontalHeader()
                    if visibleCols := [col for col in range(self.columnCount()) if not header.isSectionHidden(col)]:
                        # get the width of all the previous visible columns
                        lastCol = visibleCols[-1]
                        if col == lastCol and self._view is not None:
                            # stretch the last column to fit the table - sum the previous columns
                            # I think setStretchLastSection automatically does this
                            colWidths = sum(self._estimateColumnWidth(cc) for cc in visibleCols[:-1])
                            viewWidth = self._view.viewport().size().width()
                            width = max(width, viewWidth - colWidths)

                    # return the size
                    return QtCore.QSize(width, height)

                except Exception:
                    # return the default QSize
                    return QtCore.QSize(int(self._chrWidth), int(self._chrHeight))

            # return the default QSize for vertical header
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
        except Exception:
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
                    newLen = max(len(_chrs) for _chrs in dataRows)
                else:
                    newLen = len(data)

            # update the current maximum
            maxLen = max(newLen, maxLen)

        return int(min(self._MAXCHARS, maxLen) * self._chrWidth)

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

    def setCellFont(self, row, column, font):
        """Set the font for dataFrame cell at position (row, column).

        :param row: row as integer
        :param column: column as integer
        :param font: font compatible with QtGui.QFont
        :return:
        """
        if not (0 <= row < self.rowCount() and 0 <= column < self.columnCount()):
            raise ValueError(f'({row}, {column}) must be less than ({self.rowCount()}, {self.columnCount()})')

        if not (colourDict := self._colour[row, column]):
            colourDict = self._colour[row, column] = {}
        if font:
            colourDict[FONT_ROLE] = font
        else:
            colourDict.pop(FONT_ROLE, None)

    @staticmethod
    def _universalSort(values):
        """Method to apply sorting
        """
        # generate the universal sort key values for the column
        return pd.Series(universalSortKey(val) for val in values)

    def _setSortOrder(self, column: int, order: QtCore.Qt.SortOrder = ...):
        """Get the new sort order based on the sort column and sort direction
        """
        self._oldSortIndex = self._sortIndex
        col = self._df.columns[column]
        newData = self._universalSort(self._df[col])
        self._sortIndex = list(newData.sort_values(ascending=(order == QtCore.Qt.AscendingOrder)).index)

        # map the old sort-order to the new sort-order
        if self._filterIndex is not None:
            self._oldFilterIndex = self._filterIndex
            self._filterIndex = sorted([self._sortIndex.index(self._oldSortIndex[fi]) for fi in self._filterIndex])

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
        return [(self._sortIndex[idx.row()], idx.column()) if idx.isValid() else (None, None) for idx in indexes]

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
            # return True if the column contains an edit function and table is editable
            # NOTE:ED - need to remove _dataFrameObject, move options to TableABC? BUT Column class is still good
            return self._defaultEditable and self._view._dataFrameObject.setEditValues[col] is not None
        except Exception:
            return self._defaultEditable

    def resetFilter(self):
        """Reset the table to unsorted
        """
        if self._filterIndex:
            self.beginResetModel()
            self._filterIndex = None
            self.endResetModel()


#=========================================================================================
# _TableObjectModel
#=========================================================================================

def _getDisplayRole(colDef, obj):
    return None if isinstance((value := colDef.getFormatValue(obj)), bool) else value


def _getCheckRole(colDef, obj):
    if isinstance((value := colDef.getValue(obj)), bool):
        return CHECKED if value else UNCHECKED

    return None


class _TableObjectModel(_TableModel):
    """Table-model that supports defining a list of objects for the table.

    Objects are defined as a list, and table is populated with information from the Column classes.
    """
    # NOTE:ED - not tested

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
            fRow = self._filterIndex[index.row()] if self._filterIndex is not None else index.row()
            row, col = self._sortIndex[fRow], index.column()

            obj = self._view._objects[row]
            colDef = self._view._columnDefs._columns[col]

            if (func := self.getAttribRole.get(role)):
                return func(colDef, obj)

        return result

    def setData(self, index, value, role=EDIT_ROLE) -> bool:
        # super(AdminModel, self).setData(index, role, value)  # super not required?

        if index.isValid():
            fRow = self._filterIndex[index.row()] if self._filterIndex is not None else index.row()
            row, col = self._sortIndex[fRow], index.column()

            obj = self._view._objects[row]
            colDef = self._view._columnDefs._columns[col]

            if (func := self.setAttribRole.get(role)):
                func(colDef, obj, value)
                self.dataChanged.emit(index, index)

                self._view.viewport().update()  # repaint the view
                return True

        return False
