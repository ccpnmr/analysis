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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-06-24 10:08:31 +0100 (Fri, June 24, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-02-28 12:23:27 +0100 (Mon, February 28, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from time import time_ns
from types import SimpleNamespace

from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, catchExceptions
from ccpn.core.lib.Notifiers import Notifier, _removeDuplicatedNotifiers
from ccpn.ui.gui.guiSettings import getColours, GUITABLE_ITEM_FOREGROUND
from ccpn.ui.gui.widgets.Font import setWidgetFont, TABLEFONT, getFontHeight
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.ColumnViewSettings import ColumnViewSettingsPopup
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.SearchWidget import attachDFSearchWidget
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.lib.MenuActions import _openItemObject
from ccpn.util.Logging import getLogger
from ccpn.util.Common import copyToClipboard
from ccpn.util.OrderedSet import OrderedSet
from ccpn.util.UpdateScheduler import UpdateScheduler
from ccpn.util.UpdateQueue import UpdateQueue


#=========================================================================================
# _SimplePandasTableView
#=========================================================================================

class _SimplePandasTableView(QtWidgets.QTableView, Base):
    styleSheet = """QTableView {
                        background-color: %(GUITABLE_BACKGROUND)s;
                        alternate-background-color: %(GUITABLE_ALT_BACKGROUND)s;
                        border: 2px solid %(BORDER_NOFOCUS)s;
                        border-radius: 2px;
                    }
                    QTableView::focus {
                        background-color: %(GUITABLE_BACKGROUND)s;
                        alternate-background-color: %(GUITABLE_ALT_BACKGROUND)s;
                        border: 2px solid %(BORDER_FOCUS)s;
                        border-radius: 2px;
                    }
                    QTableView::item {
                        padding: 2px;
                    }
                    QTableView::item::selected {
                        background-color: %(GUITABLE_SELECTED_BACKGROUND)s;
                        color: %(GUITABLE_SELECTED_FOREGROUND)s;
                    }
                    """

    # overrides QtCore.Qt.ForegroundRole
    # QTableView::item - color: %(GUITABLE_ITEM_FOREGROUND)s;
    # QTableView::item:selected - color: %(GUITABLE_SELECTED_FOREGROUND)s;

    def __init__(self, parent=None,
                 multiSelect=False, selectRows=True,
                 showHorizontalHeader=True, showVerticalHeader=True,
                 **kwds):
        super().__init__(parent)
        Base._init(self, **kwds)

        self._parent = parent

        # initialise the internal data storage
        self._df = None
        self._tableBlockingLevel = 0

        # set stylesheet
        colours = getColours()
        self._defaultStyleSheet = self.styleSheet % colours
        self.setStyleSheet(self._defaultStyleSheet)
        self.setAlternatingRowColors(True)

        # set the preferred scrolling behaviour
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        if selectRows:
            self.setSelectionBehavior(self.SelectRows)

        # define the multi-selection behaviour
        self.multiSelect = multiSelect
        if multiSelect:
            self._selectionMode = self.ExtendedSelection
        else:
            self._selectionMode = self.SingleSelection
        self.setSelectionMode(self._selectionMode)
        self._clickInterval = QtWidgets.QApplication.instance().doubleClickInterval() * 1e6  # change to ns
        self._clickedInTable = False
        self._currentIndex = None

        # enable sorting and sort on the first column
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)

        setWidgetFont(self, name=TABLEFONT)

        # set the horizontalHeader information
        _header = self.horizontalHeader()
        # set Interactive and last column to expanding
        _header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        _header.setStretchLastSection(True)
        # only look at visible section
        _header.setResizeContentsPrecision(5)
        _header.setDefaultAlignment(QtCore.Qt.AlignLeft)
        _header.setMinimumSectionSize(20)
        _header.setHighlightSections(self.font().bold())
        _header.setVisible(showHorizontalHeader)

        setWidgetFont(_header, name=TABLEFONT)
        setWidgetFont(self.verticalHeader(), name=TABLEFONT)

        # set the verticalHeader information
        _header = self.verticalHeader()
        # set Interactive and last column to expanding
        _header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        _header.setStretchLastSection(False)
        # only look at visible section
        _header.setResizeContentsPrecision(5)
        _header.setDefaultAlignment(QtCore.Qt.AlignLeft)
        _header.setFixedWidth(10)  # gives enough of a handle to resize if required
        _header.setVisible(showVerticalHeader)

        _header.setHighlightSections(self.font().bold())
        setWidgetFont(_header, name=TABLEFONT)

        _height = getFontHeight(name=TABLEFONT, size='MEDIUM')
        _header.setDefaultSectionSize(_height)
        _header.setMinimumSectionSize(_height)
        self.setMinimumSize(3 * _height, 3 * _height + self.horizontalScrollBar().height())

        # set a default empty model
        _clearSimplePandasTable(self)

    def setModel(self, model: QtCore.QAbstractItemModel) -> None:
        """Set the model for the view
        """
        super().setModel(model)

        # attach a handler for updating the selection on sorting
        self.model().layoutAboutToBeChanged.connect(self._preChangeSelectionOrderCallback)
        self.model().layoutChanged.connect(self._postChangeSelectionOrderCallback)

    def _initTableCommonWidgets(self, parent, height=35, setGuiNotifier=None, **kwds):
        """Initialise the common table elements
        """
        # strange, need to do this when using scrollArea, but not a widget
        parent.getLayout().setHorizontalSpacing(0)

        self._widget = ScrollableFrame(parent=parent, scrollBarPolicies=('never', 'never'), **kwds)
        self._widgetScrollArea = self._widget._scrollArea
        self._widgetScrollArea.setStyleSheet('''
                    margin-left : 2px;
                    margin-right : 2px;''')

    def _postInitTableCommonWidgets(self):
        from ccpn.ui.gui.widgets.DropBase import DropBase
        from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
        from ccpn.ui.gui.widgets.ScrollBarVisibilityWatcher import ScrollBarVisibilityWatcher

        # add a dropped notifier to all tables
        if self.moduleParent is not None:
            # set the dropEvent to the mainWidget of the module, otherwise the event gets stolen by Frames
            self.moduleParent.mainWidget._dropEventCallback = self._processDroppedItems

        self.droppedNotifier = GuiNotifier(self,
                                           [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                           self._processDroppedItems)

        # add a widget handler to give a clean corner widget for the scroll area
        self._cornerDisplay = ScrollBarVisibilityWatcher(self)

        try:
            # may refactor the remaining modules so this isn't needed
            self._widgetScrollArea.setFixedHeight(self._widgetScrollArea.sizeHint().height())
        except:
            getLogger().debug2(f'{self.__class__.__name__} has no _widgetScrollArea')

    def _preChangeSelectionOrderCallback(self, *args):
        """Handle updating the selection when the table is about to change, i.e., before sorting
        """
        pass

    def _postChangeSelectionOrderCallback(self, *args):
        """Handle updating the selection when the table has been sorted
        """
        model = self.model()
        selModel = self.selectionModel()
        selection = self.selectionModel().selectedIndexes()

        if model._sortIndex and model._oldSortIndex:
            # get the pre-sorted mapping
            if (rows := set(model._oldSortIndex[itm.row()] for itm in selection
                            if itm.row() in model._oldSortIndex)):
                # block so no signals emitted
                self.blockSignals(True)
                selModel.blockSignals(True)

                try:
                    newSel = QtCore.QItemSelection()
                    for row in rows:
                        if row in model._sortIndex:
                            # map to the new sort-order
                            idx = model.index(model._sortIndex.index(row), 0)
                            newSel.merge(QtCore.QItemSelection(idx, idx), QtCore.QItemSelectionModel.Select)

                    # Select the cells in the data view - spawns single change event
                    self.selectionModel().select(newSel, QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.ClearAndSelect)

                finally:
                    # unblock to enable again
                    selModel.blockSignals(False)
                    self.blockSignals(False)

    #=========================================================================================
    # keyboard and mouse handling - modified to allow double-click to keep current selection
    #=========================================================================================

    @staticmethod
    def _keyModifierPressed():
        """Is the user clicking while holding a modifier
        """
        allKeyModifers = [QtCore.Qt.ShiftModifier, QtCore.Qt.ControlModifier, QtCore.Qt.AltModifier, QtCore.Qt.MetaModifier]
        keyMod = QtWidgets.QApplication.keyboardModifiers()

        return keyMod in allKeyModifers

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        """Handle mouse-press event so that double-click keeps any multi-selection
        """
        # doesn't respond in double-click interval - minor behaviour change to ExtendedSelection
        self._currentIndex = self.indexAt(e.pos())

        # user can click in the blank space under the table
        self._clickedInTable = True if self._currentIndex else False

        super().mousePressEvent(e)

    def keyPressEvent(self, event):
        """Handle keyPress events on the table
        """
        super().keyPressEvent(event)

        key = event.key()
        if key in [QtCore.Qt.Key_Escape]:
            # press the escape-key to clear the selection
            self.clearSelection()

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        pass

    def _handleDroppedItems(self, pids, objType, pulldown):
        """Handle dropped items
        :param pids: the selected objects pids
        :param objType: the instance of the obj to handle, E.g. PeakList
        :param pulldown: the pulldown of the module wich updates the table
        :return: Actions: Select the dropped item on the table or/and open a new modules if multiple drops.
        If multiple different obj instances, then asks first.
        """
        pass


#=========================================================================================
# _SimplePandasTableModel
#=========================================================================================

class _SimplePandasTableModel(QtCore.QAbstractTableModel):
    """A simple table model to view pandas DataFrames
    """

    _defaultForegroundColour = QtGui.QColor(getColours()[GUITABLE_ITEM_FOREGROUND])
    _CHECKROWS = 5
    _MINCHARS = 4
    _MAXCHARS = 100
    _chrWidth = 12
    _chrHeight = 12

    showEditIcon = False
    defaultFlags = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def __init__(self, data, view=None):
        """Initialise the pandas model
        Allocates space for foreground/background colours
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
        """replace the dataFrame and update the model
        """
        self.beginResetModel()

        self._df = value

        # set the initial sort-order
        self._oldSortIndex = [row for row in range(value.shape[0])]
        self._sortIndex = [row for row in range(value.shape[0])]

        # create numpy arrays to match the data that will hold background colour
        self._colour = np.empty(value.shape, dtype=np.object)

        # notify that the data has changed
        self.endResetModel()

    def _insertRow(self, row, newRow):
        """Insert a new row into the table
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
        """Update a row in the table
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
        """Delete a row from the table
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
            row = self._sortIndex[index.row()]
            col = index.column()

            if role == QtCore.Qt.DisplayRole:
                data = self._df.iat[row, col]

                # float/np.float - round to 3 decimal places
                if isinstance(data, (float, np.floating)):
                    return f'{data:.3f}'

                return str(data)

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

            elif role == QtCore.Qt.EditRole:
                data = self._df.iat[row, col]

                # float/np.float - return float
                if isinstance(data, (float, np.floating)):
                    return float(data)

                # int/np.integer - return int
                elif isinstance(data, (int, np.integer)):
                    return int(data)

                return data

            # elif role == QtCore.Qt.DecorationRole:
            #     # return the pixmap - this works, transfer to _MultiHeader
            #     return self._editableIcon

        return None

    def headerData(self, col, orientation, role=None):
        """Return the column headers
        """
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            try:
                # quickest way to get the column
                return self._df.columns[col]
            except:
                return None

        # if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
        #     return self._df.index[col] if not self._df.empty else None

        if role == QtCore.Qt.SizeHintRole:
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

    def _setSortOrder(self, column: int, order: QtCore.Qt.SortOrder = ...):
        """Get the new sort order based on the sort column and sort direction
        """
        self._oldSortIndex = self._sortIndex
        col = self._df.columns[column]
        newData = self._universalSort(self._df[col])
        self._sortIndex = list(newData.sort_values(ascending=True if order == QtCore.Qt.AscendingOrder else False).index)

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
            return False


#=========================================================================================
# _SimplePandasTableHeaderModel
#=========================================================================================

class _SimplePandasTableHeaderModel(QtCore.QAbstractTableModel):
    """A simple table model to view pandas DataFrames
    """
    _defaultForegroundColour = QtGui.QColor(getColours()[GUITABLE_ITEM_FOREGROUND])

    def __init__(self, row, column):
        """Initialise the pandas model
        Allocates space for foreground/background colours
        """
        QtCore.QAbstractTableModel.__init__(self)
        # create numpy arrays to match the data that will hold background colour
        self._colour = np.zeros((row, column), dtype=np.object)
        self._df = np.zeros((row, column), dtype=np.object)

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
            if role == QtCore.Qt.DisplayRole:
                return str(self._df[index.row(), index.column()])

            if role == QtCore.Qt.BackgroundRole:
                if (colourDict := self._colour[index.row(), index.column()]):
                    # get the colour from the dict
                    return colourDict.get(role)

            if role == QtCore.Qt.ForegroundRole:
                if (colourDict := self._colour[index.row(), index.column()]):
                    # get the colour from the dict
                    return colourDict.get(role)

                # return the default foreground colour
                return self._defaultForegroundColour

        return None


#=========================================================================================
# New/Update objects
#=========================================================================================

def _newSimplePandasTable(parent, data, _resize=False):
    """Create a new _SimplePandasTable from a pd.DataFrame
    """
    if not parent:
        raise ValueError('parent not defined')
    if not isinstance(data, pd.DataFrame):
        raise ValueError(f'data is not of type pd.DataFrame - {type(data)}')

    # create a new table
    table = _SimplePandasTableView(parent)

    # set the model
    model = _SimplePandasTableModel(pd.DataFrame(data), view=table)
    table.setModel(model)

    # # put a proxy in between view and model - REALLY SLOW for big tables
    # table._proxy = QtCore.QSortFilterProxyModel()
    # table._proxy.setSourceModel(_model)
    # table.setModel(table._proxy)

    table.resizeColumnsToContents()
    if _resize:
        # resize if required
        table.resizeRowsToContents()

    return table


def _updateSimplePandasTable(table, data, _resize=False):
    """Update existing _SimplePandasTable from a new pd.DataFrame
    """
    if not table:
        raise ValueError('table not defined')
    if not isinstance(data, pd.DataFrame):
        raise ValueError(f'data is not of type pd.DataFrame - {type(data)}')

    # create new model and set in table
    model = _SimplePandasTableModel(data, view=table)
    table.setModel(model)

    # # put a proxy in between view and model - REALLY SLOW for big tables
    # table._proxy.setSourceModel(_model)

    table.resizeColumnsToContents()  # crude but very quick
    if _resize:
        # resize if required
        table.resizeRowsToContents()


def _clearSimplePandasTable(table):
    """Clear existing _SimplePandasTable from a new pd.DataFrame
    """
    if not table:
        raise ValueError('table not defined')

    # create new model and set in table
    model = _SimplePandasTableModel(pd.DataFrame({}), view=table)
    table.setModel(model)


#=========================================================================================
# _SimplePandasTableViewProjectSpecific project specific
#=========================================================================================

# define a simple class that can contains a simple id
blankId = SimpleNamespace(className='notDefined', serial=0)

OBJECT_CLASS = 0
OBJECT_PARENT = 1
MODULEIDS = {}


# simple class to store the blocking state of the table
@dataclass
class _BlockingContent:
    modelBlocker = None
    rootBlocker = None


class _SimplePandasTableViewProjectSpecific(_SimplePandasTableView):
    _tableSelectionChanged = QtCore.pyqtSignal(list)

    className = '_SimplePandasTableViewProjectSpecific'
    attributeName = '_SimplePandasTableViewProjectSpecific'

    _OBJECT = '_object'
    _ISDELETED = 'isDeleted'
    _internalColumns = []

    OBJECTCOLUMN = '_object'
    INDEXCOLUMN = 'index'
    _INDEX = None

    defaultHidden = []
    columnHeaders = {}
    tipTexts = ()

    # define the notifiers that are required for the specific table-type
    tableClass = None
    rowClass = None
    cellClass = None
    tableName = None
    rowName = None
    cellClassNames = None

    selectCurrent = True
    callBackClass = None
    search = False
    enableEditDelegate = True

    # set the queue handling parameters
    _maximumQueueLength = 0
    _logQueueTime = False

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None, checkBoxCallback=None,
                 enableMouseMoveEvent=True,
                 allowRowDragAndDrop=False,
                 hiddenColumns=None,
                 multiSelect=False, selectRows=True, numberRows=False, autoResize=False,
                 enableExport=True, enableDelete=True, enableSearch=True,
                 hideIndex=True, stretchLastSection=True,
                 showHorizontalHeader=True, showVerticalHeader=True,
                 enableDoubleClick=True,
                 **kwds):
        """Initialise the widgets for the module.
        """
        super().__init__(parent=parent,
                         multiSelect=multiSelect, selectRows=selectRows,
                         showHorizontalHeader=True, showVerticalHeader=False,
                         **kwds)

        # Derive application, project, and current from mainWindow
        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current

        self.moduleParent = moduleParent
        self._table = None
        self._dataFrameObject = None

        self._setTableNotifiers()

        self._lastMouseItem = None
        self._mousePressed = False
        self._lastTimeClicked = time_ns()
        self._clickInterval = QtWidgets.QApplication.instance().doubleClickInterval() * 1e6
        self._tableSelectionBlockingTime = 0
        self._currentRow = None
        self._lastSelection = [None]

        # set internal flags
        self._mousePressedPos = None
        self._userKeyPressed = False
        self._selectOverride = False
        self._scrollOverride = False

        # enable the right click menu
        self.searchWidget = None
        self._setHeaderContextMenu()
        self._enableExport = enableExport
        self._enableDelete = enableDelete
        self._enableSearch = enableSearch

        self._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)
        self._rightClickedTableIndex = None  # last selected item in a table before raising the context menu. Enabled with mousePress event filter

        self._enableDoubleClick = enableDoubleClick
        if enableDoubleClick:
            self.doubleClicked.connect(self._doubleClickCallback)

        # notifier queue handling
        self._scheduler = UpdateScheduler(self.project, self._queueProcess, name='PandasTableNotifierHandler',
                                          startOnAdd=False, log=False, completeCallback=self.update)
        self._queuePending = UpdateQueue()
        self._queueActive = None
        self._lock = QtCore.QMutex()

        if self.enableEditDelegate:
            # set the delegate for editing
            delegate = _SimpleTableDelegate(self, objectColumn=self.OBJECTCOLUMN)
            self.setItemDelegate(delegate)

    def setModel(self, model: QtCore.QAbstractItemModel) -> None:
        """Set the model for the view
        """
        super().setModel(model)

        # attach a handler for to respond to the selection changing
        self.selectionModel().selectionChanged.connect(self._selectionChangedCallback)
        model.showEditIcon = True

    #=========================================================================================
    # Block table signals
    #=========================================================================================

    def _blockTableEvents(self, blanking=True, disableScroll=False, tableState=None):
        """Block all updates/signals/notifiers in the table.
        """
        # block on first entry
        if self._tableBlockingLevel == 0:
            if disableScroll:
                self._scrollOverride = True

            # use the Qt widget to block signals - selectionModel must also be blocked
            tableState.modelBlocker = QtCore.QSignalBlocker(self.selectionModel())
            tableState.rootBlocker = QtCore.QSignalBlocker(self)
            # tableState.enabledState = self.updatesEnabled()
            # self.setUpdatesEnabled(False)

            if blanking and self.project:
                if self.project:
                    self.project.blankNotification()

            # list to store any deferred functions until blocking has finished
            self._deferredFuncs = []

        self._tableBlockingLevel += 1

    def _unblockTableEvents(self, blanking=True, disableScroll=False, tableState=None):
        """Unblock all updates/signals/notifiers in the table.
        """
        if self._tableBlockingLevel > 0:
            self._tableBlockingLevel -= 1

            # unblock all signals on last exit
            if self._tableBlockingLevel == 0:
                if blanking and self.project:
                    if self.project:
                        self.project.unblankNotification()

                tableState.modelBlocker = None
                tableState.rootBlocker = None
                # self.setUpdatesEnabled(tableState.enabledState)
                # tableState.enabledState = None

                if disableScroll:
                    self._scrollOverride = False

                self.update()

                for func in self._deferredFuncs:
                    # process simple deferred functions - required so that qt signals are not blocked
                    func()
                self._deferredFuncs = []

        else:
            raise RuntimeError('Error: tableBlockingLevel already at 0')

    @contextmanager
    def _blockTableSignals(self, callerId='', blanking=True, disableScroll=False):
        """Block all signals from the table
        """
        tableState = _BlockingContent()
        self._blockTableEvents(blanking, disableScroll=disableScroll, tableState=tableState)
        try:
            yield  # yield control to the calling process

        except Exception as es:
            raise es
        finally:
            self._unblockTableEvents(blanking, disableScroll=disableScroll, tableState=tableState)

    #=========================================================================================
    # Mouse/Keyboard handling
    #=========================================================================================

    def mousePressEvent(self, event):
        """handle mouse press events
        Clicking is handled on the mouse release
        """
        if event.button() == QtCore.Qt.RightButton:
            # stops the selection from the table when the right button is clicked
            self._rightClickedTableIndex = self.indexAt(event.pos())
        else:
            self._rightClickedTableIndex = None

        super().mousePressEvent(event)

        self.setCurrent()

    def getRightMouseItem(self):
        if self._rightClickedTableIndex:
            row = self._rightClickedTableIndex.row()
            return self._df.iloc[self.model()._sortIndex[row]]

    def setCurrent(self):
        """Set self to current.guiTable"""
        if self.current is not None:
            self.current.guiTable = self
            # self._setCurrentStyleSheet()

    def unsetCurrent(self):
        """Set self to current.guiTable"""
        if self.current is not None:
            self.current.guiTable = None
            # self.setStyleSheet(self._defaultStyleSheet)

    @staticmethod
    def pressingModifiers(self):
        """Is the user clicking while holding a modifier
        """
        allKeyModifers = [QtCore.Qt.ShiftModifier, QtCore.Qt.ControlModifier, QtCore.Qt.AltModifier, QtCore.Qt.MetaModifier]
        keyMod = QtWidgets.QApplication.keyboardModifiers()

        return keyMod in allKeyModifers

    def keyPressEvent(self, event):
        """Handle keyPress events on the table
        """
        super().keyPressEvent(event)

        cursors = [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]
        enter = [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]
        allKeyModifers = [QtCore.Qt.ShiftModifier, QtCore.Qt.ControlModifier, QtCore.Qt.AltModifier, QtCore.Qt.MetaModifier]

        # for MacOS ControlModifier is 'cmd' and MetaModifier is 'ctrl'
        addSelectionMod = [QtCore.Qt.ControlModifier]

        key = event.key()
        if key in enter:

            # enter/return pressed - select/deselect current item
            keyMod = QtWidgets.QApplication.keyboardModifiers()

            if keyMod in addSelectionMod:
                idx = self.currentIndex()
                if idx:
                    # set the item, which toggles selection of the row
                    self.setCurrentIndex(idx)

            elif keyMod not in allKeyModifers and self._enableDoubleClick:
                # fire the action callback (double-click on selected)
                self._doubleClickCallback(self.currentIndex())

        # elif key == QtCore.Qt.Key_Escape:
        #     print(f' escape pressed')

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        """Set up the context menu for the main table
        """
        self.tableMenu = Menu('', self, isFloatWidget=True)
        setWidgetFont(self.tableMenu, )
        self.tableMenu.addAction('Copy clicked cell value', self._copySelectedCell)
        if enableExport:
            self.tableMenu.addAction('Export Visible Table', partial(self.exportTableDialog, exportAll=False))
            self.tableMenu.addAction('Export All Columns', partial(self.exportTableDialog, exportAll=True))

        self.tableMenu.addSeparator()

        if enableDelete:
            self.tableMenu.addAction('Delete Selection', self.deleteObjFromTable)

        self.tableMenu.addAction('Clear Selection', self._clearSelectionCallback)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._raiseTableContextMenu)

    def _raiseTableContextMenu(self, pos):
        """Create a new menu and popup at cursor position
        """
        pos = QtCore.QPoint(pos.x() + 10, pos.y() + 10)
        self.tableMenu.exec_(self.mapToGlobal(pos))

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _copySelectedCell(self):
        # from ccpn.util.Common import copyToClipboard

        idx = self.currentIndex()
        if idx is not None:
            text = idx.data().strip()
            copyToClipboard([text])

    def _clearSelectionCallback(self):
        """Callback for the context menu clear;
        For now just a placeholder
        """
        self.clearSelection()

    def exportTableDialog(self, exportAll=True):
        pass

    def deleteObjFromTable(self):
        """Delete all objects in the selection from the project
        """
        if (selected := self.getSelectedObjects()):
            n = len(selected)

            # make a list of the types of objects to delete
            objNames = OrderedSet()
            for obj in selected:
                if hasattr(obj, 'pid'):
                    objNames.add('%s%s' % (obj.className, '' if n == 1 else 's'))
            objStr = ', '.join(objNames)

            # put into the dialog message
            title = 'Delete Item%s' % ('' if n == 1 else 's')
            if objStr:
                msg = 'Delete %s %s from the project?' % ('' if n == 1 else '%d' % n, objStr)
            else:
                msg = 'Delete %sselected item%s from the project?' % ('' if n == 1 else '%d ' % n, '' if n == 1 else 's')
            if MessageDialog.showYesNo(title, msg):

                with catchExceptions(application=self.application,
                                     errorStringTemplate='Error deleting objects from table; "%s"'):
                    if hasattr(selected[0], 'project'):
                        thisProject = selected[0].project

                        with undoBlockWithoutSideBar():
                            # echo [sI.pid for sI in selected])
                            for obj in selected:
                                if hasattr(obj, 'pid'):
                                    obj.delete()

                    else:

                        # TODO:ED this is deleting from PandasTable, check for another way to get project
                        for obj in selected:
                            if hasattr(obj, 'pid'):
                                obj.delete()

                self.clearSelection()
                return True

    #=========================================================================================
    # Header context menu
    #=========================================================================================

    def _setHeaderContextMenu(self):
        """Set up the context menu for the table header
        """
        headers = self.horizontalHeader()
        headers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        headers.customContextMenuRequested.connect(self._raiseHeaderContextMenu)

    def _raiseHeaderContextMenu(self, pos):
        """Raise the menu on the header
        """
        if self._df is None or self._df.empty:
            return

        self.initSearchWidget()
        pos = QtCore.QPoint(pos.x(), pos.y() + 10)  #move the popup a bit down. Otherwise can trigger an event if the pointer is just on top the first item

        self.headerContextMenumenu = QtWidgets.QMenu()
        setWidgetFont(self.headerContextMenumenu, )
        columnsSettings = self.headerContextMenumenu.addAction("Column Settings...")
        searchSettings = None
        if self._enableSearch and self.searchWidget is not None:
            searchSettings = self.headerContextMenumenu.addAction("Filter...")
        action = self.headerContextMenumenu.exec_(self.mapToGlobal(pos))

        if action == columnsSettings:
            settingsPopup = ColumnViewSettingsPopup(parent=self._parent, table=self,
                                                    dataFrameObject=self._df,
                                                    hiddenColumns=self.getHiddenColumns(),
                                                    )
            hiddenColumns = settingsPopup.getHiddenColumns()
            self.setHiddenColumns(texts=hiddenColumns, update=False)
            settingsPopup.raise_()
            settingsPopup.exec_()  # exclusive control to the menu and return _hiddencolumns

        if action == searchSettings:
            self.showSearchSettings()

    #=========================================================================================
    # Search methods
    #=========================================================================================

    def initSearchWidget(self):
        if self._enableSearch and self.searchWidget is None:
            if not attachDFSearchWidget(self._parent, self):
                getLogger().warning('Filter option not available')

    def hideSearchWidget(self):
        if self.searchWidget is not None:
            self.searchWidget.hide()

    def showSearchSettings(self):
        """ Display the search frame in the table"""

        self.initSearchWidget()
        if self.searchWidget is not None:
            self.searchWidget.show()

    #=========================================================================================
    # Handle dropped items
    #=========================================================================================

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        if self.tableClass and data:
            pids = data.get('pids', [])
            self._handleDroppedItems(pids, self.tableClass, self.moduleParent._modulePulldown)

    def _handleDroppedItems(self, pids, objType, pulldown):
        """Handle dropping an item onto the module.
        :param pids: the selected objects pids
        :param objType: the instance of the obj to handle. Eg. PeakList
        :param pulldown: the pulldown of the module wich updates the table
        :return: Actions: Select the dropped item on the table or/and open a new modules if multiple drops.
        If multiple different obj instances, then asks first.
        """
        objs = [self.project.getByPid(pid) for pid in pids]

        selectableObjects = [obj for obj in objs if isinstance(obj, objType)]
        others = [obj for obj in objs if not isinstance(obj, objType)]
        if len(selectableObjects) > 0:
            _openItemObject(self.mainWindow, selectableObjects[1:])
            pulldown.select(selectableObjects[0].pid)

        else:
            from ccpn.ui.gui.widgets.MessageDialog import showYesNo

            othersClassNames = list(set([obj.className for obj in others if hasattr(obj, 'className')]))
            if len(othersClassNames) > 0:
                if len(othersClassNames) == 1:
                    title, msg = 'Dropped wrong item.', 'Do you want to open the %s in a new module?' % ''.join(othersClassNames)
                else:
                    title, msg = 'Dropped wrong items.', 'Do you want to open items in new modules?'
                openNew = showYesNo(title, msg)
                if openNew:
                    _openItemObject(self.mainWindow, others)

    #=========================================================================================
    # Table updates
    #=========================================================================================

    def _getTableColumns(self, source=None):
        """format of column = ( Header Name, value, tipText, editOption)
        editOption allows the user to modify the value content by doubleclick
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._getTableColumns not implemented')

    def populateTable(self, rowObjects=None, columnDefs=None,
                      selectedObjects=None):
        """Populate the table with a set of objects to highlight, or keep current selection highlighted
        with the first item visible.

        Use selectedObjects = [] to clear the selected items

        :param rowObjects: list of objects to set each row
        """
        self.project.blankNotification()

        # if nothing passed in then keep the current highlighted objects
        objs = selectedObjects if selectedObjects is not None else self.getSelectedObjects()

        try:
            self._dataFrameObject = self.buildTableDataFrame()
            self._df = self._dataFrameObject.dataFrame

            # remember the old values
            sortColumn, sortOrder = 0, 0
            if (oldModel := self.model()):
                sortColumn = oldModel._sortColumn
                sortOrder = oldModel._sortOrder

            # create new model and set in table
            model = _SimplePandasTableModel(self._df, view=self)
            self.setModel(model)
            self.resizeColumnsToContents()

            # re-sort the table
            if oldModel and (0 <= sortColumn < model.columnCount()) and self.isSortingEnabled():
                model._sortColumn = sortColumn
                model._sortOrder = sortOrder
                self.sortByColumn(sortColumn, sortOrder)

            self.showColumns(None)
            self._highLightObjs(objs)

        except Exception as es:
            getLogger().warning('Error populating table', str(es))
            self.populateEmptyTable()

        finally:
            self.project.unblankNotification()

    def populateEmptyTable(self):
        """Populate with an empty dataFrame containing the correct column headers.
        """
        self._dataFrameObject = None
        self._df = pd.DataFrame({val: [] for val in self.columnHeaders.keys()})

        if self.OBJECTCOLUMN in self._df.columns:
            # use the object as the index, object always exists even if isDeleted
            self._df.set_index(self._df[self.OBJECTCOLUMN], inplace=True, )

        _updateSimplePandasTable(self, self._df, _resize=True)
        self.showColumns(None)

    #=========================================================================================
    # hidden column information
    #=========================================================================================

    def getHiddenColumns(self):
        """
        get a list of currently hidden columns
        """
        hiddenColumns = self._hiddenColumns
        ll = list(set(hiddenColumns))
        return [x for x in ll if x in self.columnTexts]

    def setHiddenColumns(self, texts, update=True):
        """
        set a list of columns headers to be hidden from the table.
        """
        ll = [x for x in texts if x in self.columnTexts and x not in self._internalColumns]
        self._hiddenColumns = ll
        if update:
            self.showColumns(None)

    def hideDefaultColumns(self):
        """If the table is empty then check visible headers against the last header hidden list
        """
        for i, columnName in enumerate(self.columnTexts):
            # remember to hide the special column
            if columnName in self._internalColumns:
                self.hideColumn(i)

    @property
    def columnTexts(self):
        """return a list of column texts.
        """
        try:
            return list(self._df.columns)
        except:
            return []

    def showColumns(self, df):
        # show the columns in the list
        hiddenColumns = self.getHiddenColumns()

        for i, colName in enumerate(self.columnTexts):
            # always hide the internal columns
            if colName in (hiddenColumns + self._internalColumns):
                self._hideColumn(colName)
            else:
                self._showColumn(colName)

    def _showColumn(self, name):
        if name not in self.columnTexts:
            return
        if name in self._hiddenColumns:
            self._hiddenColumns.remove(name)
        i = self.columnTexts.index(name)
        self.showColumn(i)

    def _hideColumn(self, name):
        if name not in self.columnTexts:
            return
        if name not in (self._hiddenColumns + self._internalColumns):
            self._hiddenColumns.append(name)
        i = self.columnTexts.index(name)
        self.hideColumn(i)

    #=========================================================================================
    # Build the dataFrame for the table
    #=========================================================================================

    def buildTableDataFrame(self):
        """Return a Pandas dataFrame from an internal list of objects
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}.buildTableDataFrame not implemented')

    #=========================================================================================
    # Notifiers
    #=========================================================================================

    def _initialiseTableNotifiers(self):
        """Set the initial notifiers to empty
        """
        self._tableNotifier = None
        self._rowNotifier = None
        self._cellNotifiers = []
        self._selectCurrentNotifier = None
        self._droppedNotifier = None
        self._searchNotifier = None

    def _setTableNotifiers(self):
        """Set a Notifier to call when an object is created/deleted/renamed/changed
        rename calls on name
        change calls on any other attribute
        """
        self._initialiseTableNotifiers()

        if self.tableClass:
            self._tableNotifier = Notifier(self.project,
                                           [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                           self.tableClass.__name__,
                                           partial(self._queueGeneralNotifier, self._updateTableCallback),
                                           onceOnly=True)

        if self.rowClass:
            # 'i-1' residue spawns rename but the 'i' residue only fires a change
            self._rowNotifier = Notifier(self.project,
                                         [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE],
                                         self.rowClass.__name__,
                                         partial(self._queueGeneralNotifier, self._updateRowCallback),
                                         onceOnly=True)  # should be True, but doesn't work

        if self.cellClassNames:
            for cellClass, attr in self.cellClassNames.items():
                self._cellNotifiers.append(Notifier(self.project,
                                                    [Notifier.CHANGE, Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                                    cellClass.__name__,
                                                    partial(self._queueGeneralNotifier, self._updateCellCallback),
                                                    onceOnly=True))

        if self.selectCurrent:
            self._selectCurrentNotifier = Notifier(self.current,
                                                   [Notifier.CURRENT],
                                                   self.callBackClass._pluralLinkName,
                                                   self._selectCurrentCallBack,  # strange behaviour if deferred
                                                   # partial(self._queueGeneralNotifier, self._selectCurrentCallBack),
                                                   )

        if self.search:
            self._searchNotifier = Notifier(self.current,
                                            [Notifier.CURRENT],
                                            self.search._pluralLinkName,
                                            self._searchCallBack
                                            )

        # add a cleaner id to the opened guiTable list
        MODULEIDS[id(self.moduleParent)] = len(MODULEIDS)

    def _queueGeneralNotifier(self, func, data):
        """Add the notifier to the queue handler
        """
        self._queueAppend([func, data])

    def _clearTableNotifiers(self):
        """Clean up the notifiers
        """
        getLogger().debug(f'clearing table notifiers {self}')

        if self._tableNotifier is not None:
            self._tableNotifier.unRegister()
            self._tableNotifier = None

        if self._rowNotifier is not None:
            self._rowNotifier.unRegister()
            self._rowNotifier = None

        if self._cellNotifiers:
            for cell in self._cellNotifiers:
                if cell is not None:
                    cell.unRegister()
            self._cellNotifiers = []

        if self._selectCurrentNotifier is not None:
            self._selectCurrentNotifier.unRegister()
            self._selectCurrentNotifier = None

        if self._droppedNotifier is not None:
            self._droppedNotifier.unRegister()
            self._droppedNotifier = None

        if self._searchNotifier is not None:
            self._searchNotifier.unRegister()
            self._searchNotifier = None

    def _close(self):
        self._clearTableNotifiers()

    def clearCurrentCallback(self):
        """Clear the callback function for current object/list change
        """
        self.selectCurrent = False
        if self._selectCurrentNotifier is not None:
            self._selectCurrentNotifier.unRegister()
            self._selectCurrentNotifier = None

    #=========================================================================================
    # Notifier callbacks
    #=========================================================================================

    def _updateTableCallback(self, data):
        """Notifier callback when the table has changed
        :param data: notifier content
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._updateTableCallback not implemented')

    def _updateRowCallback(self, data):
        """Notifier callback to update a row in the table
        :param data: notifier content
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._updateRowCallback not implemented')

    def _updateCellCallback(self, data):
        """Notifier callback to update a cell in the table
        :param data: notifier content
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._updateCellCallback not implemented')

    def _selectCurrentCallBack(self, data):
        """Callback from a current changed notifier to highlight the current objects
        :param data
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._selectCurrentCallBack not implemented')

    def _searchCallBack(self, data):
        """Callback to populate the search bar with the selected item
        :param data: notifier content
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._searchCallBack not implemented')

    def _selectionChangedCallback(self, selected, deselected):
        """Handle item selection has changed in table - call user callback
        :param selected: table indexes selected
        :param deselected: table indexes deselected
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._selectionChangedCallback not implemented')

    def actionCallback(self, data):
        """Handle item selection has changed in table - call user callback
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._selectionChangedCallback not implemented')

    def _doubleClickCallback(self, itemSelection):

        if bool(itemSelection.flags() & QtCore.Qt.ItemIsEditable):
            # item is editable so skip the action
            return

        if not self.actionCallback:
            return

        # if not a _dataFrameObject is a normal guiTable.
        if self._df is None or self._df.empty:
            item = self.currentItem()
            if item is not None:
                data = CallBack(value=item.value,
                                theObject=None,
                                object=None,
                                index=item.index,
                                targetName=None,
                                trigger=CallBack.CLICK,
                                row=item.row(),
                                col=item.column(),
                                rowItem=item)
                self.actionCallback(data)

            return

        self._lastClick = 'doubleClick'
        with self._blockTableSignals('_doubleClickCallback', blanking=False, disableScroll=True):

            idx = self.currentIndex()

            # get the current selected objects from the table - objects now persistent after single-click
            objList = []
            if self._lastSelection is not None:
                objList = self._lastSelection  #['selection']

            if idx:
                row = self.model()._sortIndex[idx.row()]
                col = idx.column()
                _data = self._df.iloc[row]
                obj = _data.get(self._OBJECT)

                if obj is not None and objList:
                    if hasattr(obj, 'className'):
                        targetName = obj.className

                    # objIndex = idx  # item.index
                    data = CallBack(theObject=self._df,
                                    object=objList if self.multiSelect else obj,  # single object or multi-selection
                                    index=idx,
                                    targetName=targetName,
                                    trigger=CallBack.DOUBLECLICK,
                                    row=row,
                                    col=col,
                                    rowItem=_data,
                                    rowObject=obj)

                    self.actionCallback(data)

    def setActionCallback(self, actionCallback=None):
        # enable callbacks
        self.actionCallback = actionCallback

        for act in [self._doubleClickCallback]:
            try:
                self.doubleClicked.disconnect(act)
            except Exception:
                getLogger().debug2('nothing to disconnect')

        if self.actionCallback:
            self.doubleClicked.connect(self._doubleClickCallback)

    def setCheckBoxCallback(self, checkBoxCallback):
        # enable callback on the checkboxes
        self._checkBoxCallback = checkBoxCallback

    #=========================================================================================
    # Table methods
    #=========================================================================================

    def getSelectedObjects(self, fromSelection=None):
        """Return the selected core objects
        :param fromSelection:
        :return: get a list of table objects. If the table has a header called pid, the object is a ccpn Core obj like Peak,
        otherwise is a Pandas series object corresponding to the selected row(s).
        """
        model = self.selectionModel()
        # selects all the items in the row - may need to check selectionMode
        selection = fromSelection if fromSelection else model.selectedRows()

        if selection:
            selectedObjects = []
            valuesDict = defaultdict(list)
            col = self._df.columns.get_loc(self.OBJECTCOLUMN)
            _sortIndex = self.model()._sortIndex
            for idx in selection:
                row = _sortIndex[idx.row()]  # map to sorted rows?

                # col = idx.column()
                # if self._objects and len(self._objects) > 0:
                #     if isinstance(self._objects[0], pd.Series):
                #         h = self.horizontalHeaderItem(col).text()
                #         v = self.item(row, col).text()
                #         valuesDict[h].append(v)
                #
                #     else:

                objIndex = self._df.iat[row, col]
                if (obj := self.project.getByPid(objIndex.strip('<>')) if isinstance(objIndex, str) else objIndex):
                    selectedObjects.append(obj)

            if valuesDict:
                selectedObjects = [row for i, row in pd.DataFrame(valuesDict).iterrows()]

            return selectedObjects

    def clearSelection(self):
        """Clear the current selection in the table
        and remove objects from the current list
        """
        with self._blockTableSignals('clearSelection'):
            # get the selected objects from the table
            objList = self.getSelectedObjects() or []
            self.selectionModel().clearSelection()

            # remove from the current list
            multiple = self.callBackClass._pluralLinkName if self.callBackClass else None
            if (self._df is not None and not self._df.empty) and multiple:
                multipleAttr = getattr(self.current, multiple, [])
                if len(multipleAttr) > 0:
                    # need to remove objList from multipleAttr - fires only one current change
                    setattr(self.current, multiple, tuple(set(multipleAttr) - set(objList)))

            self._lastSelection = [None]

        self._tableSelectionChanged.emit([])

    def _changeTableSelection(self, itemSelection):
        """Manually change the selection on the table and call the necessary callbacks
        """
        # print(f'>>>     _selectionTableCallback  {self} ')
        # if not a _dataFrameObject is a normal guiTable.
        if self._df is None or self._df.empty:
            idx = self.selectionModel().currentIndex()
            if idx is not None and self.selectionCallback:

                # TODO:ED - check this bit
                data = CallBack(value=idx.data(),
                                theObject=None,
                                object=None,
                                index=idx,
                                targetName=None,
                                trigger=CallBack.CLICK,
                                row=idx.row(),
                                col=idx.column(),
                                rowItem=idx)

                delta = time_ns() - self._lastTimeClicked
                # if interval large enough then reset timer and return True
                if delta > self._clickInterval:
                    self.selectionCallback(data)

            return

        objList = self.getSelectedObjects()
        # if objList and isinstance(objList[0], pd.Series):
        #     pass
        # else:
        #     if self._clickedInTable:
        #         if not objList:
        #             return
        #         if set(objList or []) == set(self._lastSelection or []):  # pd.Series should never reach here or will crash here. Cannot use set([series])== because Series are mutable, thus they cannot be hashed
        #             return

        self._lastSelection = objList

        with self._blockTableSignals('_changeTableSelection', blanking=False, disableScroll=True):

            # get whether current row is defined
            idx = self.currentIndex()
            targetName = ''

            # if objList is not None:
            if objList and len(objList) > 0 and hasattr(objList[0], 'className'):
                targetName = objList[0].className

            if idx and self.selectionCallback:
                data = CallBack(theObject=self._df,
                                object=objList,
                                index=0,
                                targetName=targetName,
                                trigger=CallBack.CLICK,
                                row=0,
                                col=0,
                                rowItem=None)

                delta = time_ns() - self._lastTimeClicked
                # if interval large enough then reset timer and return True
                if delta > self._clickInterval:
                    self.selectionCallback(data)

    #=========================================================================================
    # Highlight objects in table
    #=========================================================================================

    def _highLightObjs(self, selection, scrollToSelection=True):

        # skip if the table is empty
        if self._df is None or self._df.empty:
            return

        with self._blockTableSignals('_highLightObjs'):

            selectionModel = self.selectionModel()
            model = self.model()
            selectionModel.clearSelection()

            if selection:
                if len(selection) > 0:
                    if isinstance(selection[0], pd.Series):
                        # not sure how to handle this
                        return
                uniqObjs = set(selection)

                _sortIndex = self.model()._sortIndex
                dfTemp = self._df.reset_index(drop=True)
                data = [dfTemp[dfTemp[self._OBJECT] == obj] for obj in uniqObjs]
                rows = [_sortIndex.index(_dt.index[0]) for _dt in data if not _dt.empty]
                if rows:
                    minRow = rows.index(min(rows))
                    for row in rows:
                        rowIndex = model.index(row, 0)
                        selectionModel.select(rowIndex, selectionModel.Select | selectionModel.Rows)

                    if scrollToSelection and not self._scrollOverride:
                        self.scrollTo(model.index(minRow, 0))

    def highlightObjects(self, objectList, scrollToSelection=True):
        """Highlight a list of objects in the table
        """
        objs = []

        if objectList:
            # get the list of objects, exclude deleted and flagged for delete
            for obj in objectList:
                if isinstance(obj, str):
                    objFromPid = self.project.getByPid(obj)

                    if objFromPid and not objFromPid.isDeleted:
                        objs.append(objFromPid)

                else:
                    objs.append(obj)

        if objs:
            self._highLightObjs(objs, scrollToSelection=scrollToSelection)
        else:
            self.clearSelection()

    #=========================================================================================
    # Notifier queue handling
    #=========================================================================================

    def queueFull(self):
        """Method that is called when the queue is deemed to be too big.
        Apply overall operation instead of all individual notifiers.
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}._updateTableCallback not implemented')

    def _queueProcess(self):
        """Process current items in the queue
        """
        with QtCore.QMutexLocker(self._lock):
            # protect the queue switching
            self._queueActive = self._queuePending
            self._queuePending = UpdateQueue()

        _startTime = time_ns()
        _useQueueFull = (self._maximumQueueLength not in [0, None] and len(self._queueActive) > self._maximumQueueLength)
        if self._logQueueTime:
            # log the queue-time if required
            getLogger().debug(f'_queueProcess  {self}  len: {len(self._queueActive)}  useQueueFull: {_useQueueFull}')

        if _useQueueFull:
            # rebuild from scratch if the queue is too big
            try:
                self._queueActive = None
                self.queueFull()
            except Exception as es:
                getLogger().debug(f'Error in {self.__class__.__name__} update queueFull: {es}')

        else:
            executeQueue = _removeDuplicatedNotifiers(self._queueActive)
            for itm in executeQueue:
                # process item if different from previous
                try:
                    func, data = itm
                    func(data)
                except Exception as es:
                    getLogger().debug(f'Error in {self.__class__.__name__} update - {es}')

        if self._logQueueTime:
            getLogger().debug(f'elapsed time {(time_ns() - _startTime) / 1e9}')

    def _queueAppend(self, itm):
        """Append a new item to the queue
        """
        self._queuePending.put(itm)
        if not self._scheduler.isActive and not self._scheduler.isBusy:
            self._scheduler.start()

        elif self._scheduler.isBusy:
            # caught during the queue processing event, need to restart
            self._scheduler.signalRestart()

    #=========================================================================================
    # Common object properties
    #=========================================================================================

    @staticmethod
    def _getCommentText(obj):
        """
        CCPN-INTERNAL: Get a comment from GuiTable
        """
        try:
            if obj.comment == '' or not obj.comment:
                return ''
            else:
                return obj.comment
        except:
            return ''

    @staticmethod
    def _setComment(obj, value):
        """
        CCPN-INTERNAL: Insert a comment into object
        """
        obj.comment = value if value else None

    @staticmethod
    def _getAnnotation(obj):
        """
        CCPN-INTERNAL: Get an annotation from GuiTable
        """
        try:
            if obj.annotation == '' or not obj.annotation:
                return ''
            else:
                return obj.annotation
        except:
            return ''

    @staticmethod
    def _setAnnotation(obj, value):
        """
        CCPN-INTERNAL: Insert an annotation into object
        """
        obj.annotation = value if value else None


#=========================================================================================
# Table delegate to handle editing
#=========================================================================================

EDIT_ROLE = QtCore.Qt.EditRole


class _SimpleTableDelegate(QtWidgets.QStyledItemDelegate):
    """handle the setting of data when editing the table
    """

    def __init__(self, parent, objectColumn=None):
        """Initialise the delegate
        :param parent - link to the handling table
        """
        QtWidgets.QStyledItemDelegate.__init__(self, parent)
        self.customWidget = False
        self._parent = parent
        self._objectColumn = objectColumn

    def setEditorData(self, widget, index) -> None:
        """populate the editor widget when the cell is edited
        """
        model = index.model()
        value = model.data(index, EDIT_ROLE)

        if not isinstance(value, (list, tuple)):
            value = (value,)

        if hasattr(widget, 'setColor'):
            widget.setColor(*value)

        elif hasattr(widget, 'setData'):
            widget.setData(*value)

        elif hasattr(widget, 'set'):
            widget.set(*value)

        elif hasattr(widget, 'setValue'):
            widget.setValue(*value)

        elif hasattr(widget, 'setText'):
            widget.setText(*value)

        elif hasattr(widget, 'setFile'):
            widget.setFile(*value)

        else:
            msg = 'Widget %s does not expose "setData", "set" or "setValue" method; ' % widget
            msg += 'required for table proxy editing'
            raise Exception(msg)

    def setModelData(self, widget, mode, index):
        """Set the object to the new value
        :param widget - typically a lineedit handling the editing of the cell
        :param mode - editing mode:
        :param index - QModelIndex of the cell
        """
        if hasattr(widget, 'get'):
            value = widget.get()

        elif hasattr(widget, 'value'):
            value = widget.value()

        elif hasattr(widget, 'text'):
            value = widget.text()

        elif hasattr(widget, 'getFile'):
            files = widget.selectedFiles()
            if not files:
                return
            value = files[0]

        else:
            msg = f'Widget {widget} does not expose "get", "value" or "text" method; required for table editing'
            raise Exception(msg)

        row = index.row()
        col = index.column()
        try:
            # get the sorted element from the dataFrame
            df = self._parent._df
            iRow = self._parent.model()._sortIndex[row]
            iCol = df.columns.get_loc(self._objectColumn)
            obj = df.iat[iRow, iCol]

            # set the data which will fire notifiers to populate all tables (including this)
            func = self._parent._dataFrameObject.setEditValues[col]
            if func and obj:
                func(obj, value)

        except Exception as es:
            getLogger().debug('Error handling cell editing: %i %i - %s    %s    %s' % (row, col, str(es), self._parent.model()._sortIndex, value))


#=========================================================================================
# SearchMethods - class holding methods for implementing searches on a table
#=========================================================================================

from ccpn.ui.gui.widgets.SearchWidget import attachSimpleSearchWidget


class _SearchTableView():

    def _initSearchTableView(self):
        # enable the right click menu
        self.searchWidget = None
        self._setHeaderContextMenu()
        self._enableExport = False
        self._enableDelete = False
        self._enableSearch = True
        self._dataFrameObject = None

    #=========================================================================================
    # hidden column information
    #=========================================================================================

    def getHiddenColumns(self):
        """
        get a list of currently hidden columns
        """
        hiddenColumns = self._hiddenColumns
        ll = list(set(hiddenColumns))
        return [x for x in ll if x in self.columnTexts]

    def setHiddenColumns(self, texts, update=True):
        """
        set a list of columns headers to be hidden from the table.
        """
        ll = [x for x in texts if x in self.columnTexts and x not in self._internalColumns]
        self._hiddenColumns = ll
        if update:
            self.showColumns(None)

    def hideDefaultColumns(self):
        """If the table is empty then check visible headers against the last header hidden list
        """
        for i, columnName in enumerate(self.columnTexts):
            # remember to hide the special column
            if columnName in self._internalColumns:
                self.hideColumn(i)

    @property
    def columnTexts(self):
        """return a list of column texts.
        """
        try:
            return list(self._df.columns)
        except:
            return []

    def showColumns(self, df):
        # show the columns in the list
        hiddenColumns = self.getHiddenColumns()

        for i, colName in enumerate(self.columnTexts):
            # always hide the internal columns
            if colName in (hiddenColumns + self._internalColumns):
                self._hideColumn(colName)
            else:
                self._showColumn(colName)

    def _showColumn(self, name):
        if name not in self.columnTexts:
            return
        if name in self._hiddenColumns:
            self._hiddenColumns.remove(name)
        i = self.columnTexts.index(name)
        self.showColumn(i)

    def _hideColumn(self, name):
        if name not in self.columnTexts:
            return
        if name not in (self._hiddenColumns + self._internalColumns):
            self._hiddenColumns.append(name)
        i = self.columnTexts.index(name)
        self.hideColumn(i)

    #=========================================================================================
    # Header context menu
    #=========================================================================================

    def _setHeaderContextMenu(self):
        """Set up the context menu for the table header
        """
        headers = self.horizontalHeader()
        headers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        headers.customContextMenuRequested.connect(self._raiseHeaderContextMenu)

    def _raiseHeaderContextMenu(self, pos):
        """Raise the menu on the header
        """
        if self._df is None or self._df.empty:
            return

        self.initSearchWidget()
        pos = QtCore.QPoint(pos.x(), pos.y() + 10)  #move the popup a bit down. Otherwise can trigger an event if the pointer is just on top the first item

        self.headerContextMenumenu = QtWidgets.QMenu()
        setWidgetFont(self.headerContextMenumenu, )
        columnsSettings = self.headerContextMenumenu.addAction("Column Settings...")
        searchSettings = None
        if self._enableSearch and self.searchWidget is not None:
            searchSettings = self.headerContextMenumenu.addAction("Filter...")
        action = self.headerContextMenumenu.exec_(self.mapToGlobal(pos))

        if action == columnsSettings:
            settingsPopup = ColumnViewSettingsPopup(parent=self._parent, table=self,
                                                    dataFrameObject=self._df,
                                                    hiddenColumns=self.getHiddenColumns(),
                                                    )
            hiddenColumns = settingsPopup.getHiddenColumns()
            self.setHiddenColumns(texts=hiddenColumns, update=False)
            settingsPopup.raise_()
            settingsPopup.exec_()  # exclusive control to the menu and return _hiddencolumns

        if action == searchSettings:
            self.showSearchSettings()

    #=========================================================================================
    # Search methods
    #=========================================================================================

    def initSearchWidget(self):
        if self._enableSearch and self.searchWidget is None:
            if not attachSimpleSearchWidget(self._parent, self):
                getLogger().warning('Filter option not available')

    def hideSearchWidget(self):
        if self.searchWidget is not None:
            self.searchWidget.hide()

    def showSearchSettings(self):
        """ Display the search frame in the table"""

        self.initSearchWidget()
        if self.searchWidget is not None:
            self.searchWidget.show()

    def refreshTable(self):
        # easier to re-populate from scratch
        try:
            df = self.moduleParent._table.data
            _updateSimplePandasTable(self, df, _resize=False)
        except Exception:
            _updateSimplePandasTable(self, pd.DataFrame({}))

    def setDataFromSearchWidget(self, dataFrame):
        """Set the data for the table from the search widget
        """
        # update to the new sub-table
        _updateSimplePandasTable(self, dataFrame)
        self.model()._df = dataFrame
