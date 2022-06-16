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
__dateModified__ = "$dateModified: 2022-06-16 14:24:54 +0100 (Thu, June 16, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-02-28 12:23:27 +0100 (Mon, February 28, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from time import time_ns, perf_counter_ns
from types import SimpleNamespace

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
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, catchExceptions
from ccpn.core.lib.Notifiers import Notifier
from ccpn.util.Logging import getLogger
from ccpn.util.Common import copyToClipboard
from ccpn.util.OrderedSet import OrderedSet


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
        self.colours = getColours()
        self._defaultStyleSheet = self.styleSheet % self.colours
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

        # the resizeColumnsToContents is REALLY slow :|
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

    def setModel(self, model: QtCore.QAbstractItemModel) -> None:
        """Set the model for the view
        """
        super(_SimplePandasTableView, self).setModel(model)

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

        self._widgetScrollArea.setFixedHeight(self._widgetScrollArea.sizeHint().height())

    def _preChangeSelectionOrderCallback(self, *args):
        """Handle updating the selection when the table is about to change, i.e., before sorting
        """
        _model = self.model()
        _model._oldSortOrder = _model._sortOrder  # remember the old order

    def _postChangeSelectionOrderCallback(self, *args):
        """Handle updating the selection when the table has been sorted
        """
        _model = self.model()
        _selModel = self.selectionModel()
        _selection = self.selectionModel().selectedIndexes()

        if _model._sortOrder and _model._oldSortOrder:
            # get the pre-sorted mapping
            if (_rows := set(_model._oldSortOrder[itm.row()] for itm in _selection)):
                # block so no signals emitted
                self.blockSignals(True)
                _selModel.blockSignals(True)

                try:
                    _newSel = QtCore.QItemSelection()
                    for row in _rows:
                        # map to the new sort-order
                        _idx = _model.index(_model._sortOrder.index(row), 0)
                        _newSel.merge(QtCore.QItemSelection(_idx, _idx), QtCore.QItemSelectionModel.Select)

                    # Select the cells in the data view - spawns single change event
                    self.selectionModel().select(_newSel, QtCore.QItemSelectionModel.Rows | QtCore.QItemSelectionModel.ClearAndSelect)

                finally:
                    # unblock to enable again
                    _selModel.blockSignals(False)
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
            self.fontMetric = QtGui.QFontMetricsF(view.font())
            self.bbox = self.fontMetric.boundingRect
            self._chrWidth = 1 + self.bbox('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').width() / 36
            self._chrHeight = self.bbox('A').height() + 8

        self._sortColumn = 0
        self._sortDirection = QtCore.Qt.AscendingOrder

        # create a pixmap for the editable icon (currently a pencil)
        self._editableIcon = Icon('icons/editable').pixmap(self._chrHeight, self._chrHeight)

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
        self._oldSortOrder = [row for row in range(value.shape[0])]
        self._sortOrder = [row for row in range(value.shape[0])]

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
            loc = self._df.index.get_loc(row)
            self._colour = np.insert(self._colour, loc, np.empty((self.columnCount()), dtype=np.object), axis=0)
            self._setSortOrder()

            # emit a signal to spawn an update of the table and notify headers to update
            self.layoutChanged.emit()

        else:
            # not checked
            pass
            # self._df.loc[row] = newRow
            # loc = self._df.index.get_loc(row)
            #
            # self.beginInsertRows(QtCore.QModelIndex(), loc, loc)
            #
            # self._colour = np.insert(self._colour, loc, np.empty((self.columnCount()), dtype=np.object), axis=0)
            #
            # self.endInsertRows()

    def _updateRow(self, row, newRow):
        """Update a row in the table
        """
        # print(f'>>>   _updateRow    {newRow}')
        try:
            loc = self._df.index.get_loc(row)  # will give a keyError if the row is not found

        except KeyError:
            getLogger().debug(f'row {row} not found')

        else:
            if self._view.isSortingEnabled():
                # notify that the table is about to be changed
                self.layoutAboutToBeChanged.emit()

                self._df.loc[row] = newRow
                self._setSortOrder()

                # emit a signal to spawn an update of the table and notify headers to update
                self.layoutChanged.emit()

            else:
                # not checked
                pass
                # # print(f'>>>   _updateRow    {newRow}')
                # loc = self._df.index.get_loc(row)
                # if loc >= 0:
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
                #     # # print(f'>>>      _updateRow    {loc}')
                #     # self._df.loc[row] = newRow
                #     #
                #     # # notify change to cells
                #     # _sortedLoc = self._sortOrder.index(loc)
                #     # startIdx, endIdx = self.index(_sortedLoc, 0), self.index(_sortedLoc, self.columnCount() - 1)
                #     # self.dataChanged.emit(startIdx, endIdx)

    def _deleteRow(self, row):
        """Delete a row from the table
        """
        # print(f'>>>   _deleteRow')
        try:
            loc = self._df.index.get_loc(row)

        except KeyError:
            getLogger().debug(f'row {row} not found')

        else:
            if self._view.isSortingEnabled():
                # notify rows are going to be inserted
                _sortedLoc = self._sortOrder.index(loc)
                self.beginRemoveRows(QtCore.QModelIndex(), _sortedLoc, _sortedLoc)

                self._df.drop([row], inplace=True)
                self._sortOrder[:] = [(val if val < loc else val - 1) for val in self._sortOrder if val != loc]
                self._colour = np.delete(self._colour, loc, axis=0)

                self.endRemoveRows()

            else:
                # not checked
                # notify rows are going to be inserted
                self.beginRemoveRows(QtCore.QModelIndex(), loc, loc)

                self._df.drop([row], inplace=True)
                self._colour = np.delete(self._colour, loc, axis=0)

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
            _row = self._sortOrder[index.row()]
            _column = index.column()

            if role == QtCore.Qt.DisplayRole:
                _cell = self._df.iat[_row, _column]

                # float/np.float - round to 3 decimal places
                if isinstance(_cell, (float, np.floating)):
                    return f'{_cell:.3f}'

                return str(_cell)

            elif role == QtCore.Qt.BackgroundRole:
                if (_colour := self._colour[_row, _column]):
                    # get the colour from the dict
                    return _colour.get(role)

            elif role == QtCore.Qt.ForegroundRole:
                if (_colour := self._colour[_row, _column]):
                    # get the colour from the dict
                    if (_foreground := _colour.get(role)):
                        return _foreground

                # return the default foreground colour
                return self._defaultForegroundColour

            elif role == QtCore.Qt.ToolTipRole:
                _cell = self._df.iat[_row, _column]

                return str(_cell)

            elif role == QtCore.Qt.EditRole:
                _cell = self._df.iat[_row, _column]

                # float/np.float - return float
                if isinstance(_cell, (float, np.floating)):
                    return float(_cell)

                # int/np.integer - return int
                elif isinstance(_cell, (int, np.integer)):
                    return int(_cell)

                return _cell

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

                    _header = self._view.horizontalHeader()
                    _visibleCols = [col for col in range(self.columnCount()) if not _header.isSectionHidden(col)]
                    if _visibleCols:
                        # get the width of all the previous visible columns
                        _lastCol = _visibleCols[-1]
                        if col == _lastCol and self._view is not None:
                            # stretch the last column to fit the table - sum the previous columns
                            _colWidths = sum([self._estimateColumnWidth(cc)
                                              for cc in _visibleCols[:-1]])
                            _viewWidth = self._view.viewport().size().width()
                            width = max(width, _viewWidth - _colWidths)

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
            _colName = self._df.columns[col]
        except:
            _colName = None

        _len = max(len(_colName) if _colName else 0, self._MINCHARS)  # never smaller than 4 characters

        # iterate over a few rows to get an estimate
        for _row in range(min(self.rowCount(), self._CHECKROWS)):
            _cell = self._df.iat[_row, col]

            # float/np.float - round to 3 decimal places
            if isinstance(_cell, (float, np.floating)):
                _newLen = len(f'{_cell:.3f}')
            else:
                _cell = str(_cell)
                if '\n' in _cell:
                    # get the longest row from the cell
                    _cells = _cell.split('\n')
                    _newLen = max([len(_chrs) for _chrs in _cells])
                else:
                    _newLen = len(_cell)

            # update the current maximum
            _len = max(_newLen, _len)

        # return the required minimum width
        _width = int(min(self._MAXCHARS, _len) * self._chrWidth)
        return _width

    def setForeground(self, row, column, colour):
        """Set the foreground colour for dataFrame cell at position (row, column).

        :param row: row as integer
        :param column: column as integer
        :param colour: colour compatible with QtGui.QColor
        :return:
        """
        if not (0 <= row < self.rowCount() and 0 <= column < self.columnCount()):
            raise ValueError(f'({row}, {column}) must be less than ({self.rowCount()}, {self.columnCount()})')

        if not (_cols := self._colour[row, column]):
            _cols = self._colour[row, column] = {}
        if colour:
            _cols[QtCore.Qt.ForegroundRole] = QtGui.QColor(colour)
        else:
            _cols.pop(QtCore.Qt.ForegroundRole, None)

    def setBackground(self, row, column, colour):
        """Set the background colour for dataFrame cell at position (row, column).

        :param row: row as integer
        :param column: column as integer
        :param colour: colour compatible with QtGui.QColor
        :return:
        """
        if not (0 <= row < self.rowCount() and 0 <= column < self.columnCount()):
            raise ValueError(f'({row}, {column}) must be less than ({self.rowCount()}, {self.columnCount()})')

        if not (_cols := self._colour[row, column]):
            _cols = self._colour[row, column] = {}
        if colour:
            _cols[QtCore.Qt.BackgroundRole] = QtGui.QColor(colour)
        else:
            _cols.pop(QtCore.Qt.BackgroundRole, None)

    @staticmethod
    def _universalSort(values):
        """Method to apply sorting
        """
        # generate the universal sort key values for the column
        _series = pd.Series(universalSortKey(val) for val in values)
        return _series

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        """Sort the underlying pandas DataFrame
        Required as there is no proxy model to handle the sorting
        """
        self._sortColumn = column
        self._sortDirection = order

        # notify that the table is about to be changed
        self.layoutAboutToBeChanged.emit()

        # self._oldSortOrder = self._sortOrder
        col = self._df.columns[column]
        _newData = self._universalSort(self._df[col])
        self._sortOrder = list(_newData.sort_values(ascending=True if order == QtCore.Qt.AscendingOrder else False).index)

        # emit a signal to spawn an update of the table and notify headers to update
        self.layoutChanged.emit()

    def _setSortOrder(self):
        """Get the new sort order based on the sort column and sort direction
        """
        col = self._df.columns[self._sortColumn]
        _newData = self._universalSort(self._df[col])
        self._sortOrder = list(_newData.sort_values(ascending=True if self._sortDirection == QtCore.Qt.AscendingOrder else False).index)

    def mapToSource(self, indexes):
        """Map the cell index to the co-ordinates in the pandas dataFrame
        Return list of tuples of dataFrame positions
        """
        idxs = [(self._sortOrder[idx.row()], idx.column()) if idx.isValid() else (None, None) for idx in indexes]
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
                return str(self._df.iat[index.row(), index.column()])

            if role == QtCore.Qt.BackgroundRole:
                if (_col := self._colour[index.row(), index.column()]):
                    # get the colour from the dict
                    return _col.get(role)

            if role == QtCore.Qt.ForegroundRole:
                if (_col := self._colour[index.row(), index.column()]):
                    # get the colour from the dict
                    if (_foreground := _col.get(role)):
                        return _foreground

                # return the default foreground colour
                return self._defaultForegroundColour

        return None

    # def setData(self, index, value, role) -> bool:
    #     """Set the data for the index
    #     """
    #     if index.isValid():
    #         if role == QtCore.Qt.UserRole + 1:
    #             col = index.column()
    #             span = int(value)
    #             if int(value) > 0:
    #                 if (col + span - 1>= _columnCount()):
    #                     span = columnCount() - col
    #                 self._df[span, ]
    #         elif role == QtCore.Qt.UserRole + 2:
    #             pass


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
    _model = _SimplePandasTableModel(pd.DataFrame(data), view=table)
    table.setModel(_model)

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
    _model = _SimplePandasTableModel(data, view=table)
    table.setModel(_model)

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
    _model = _SimplePandasTableModel(pd.DataFrame({}), view=table)
    table.setModel(_model)


#=========================================================================================
# _SimplePandasTableViewProjectSpecific project specific
#=========================================================================================

from ccpn.util.UpdateScheduler import UpdateScheduler
from ccpn.util.UpdateQueue import UpdateQueue


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
    PRIMARYCOLUMN = 'Pid'
    defaultHidden = []
    _internalColumns = []

    columnHeaders = {}
    tipTexts = ()

    # define the notifiers that are required for the specific table-type
    tableClass = None
    rowClass = None
    cellClass = None
    tableName = None
    rowName = None
    cellName = None
    cellClassNames = None

    selectCurrent = True
    callBackClass = None
    search = False

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
        self._tableSelectionBlockingLevel = 0
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
        self._scheduler = UpdateScheduler(self._queueProcess, name='PandasTableNotifierHandler',
                                          startOnAdd=False, log=False, completeCallback=self.update)
        self._queuePending = UpdateQueue()
        self._queueActive = None
        self._lock = QtCore.QMutex()

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

    def _blockTableEvents(self, blanking=True, _disableScroll=False, _tableState=None):
        """Block all updates/signals/notifiers in the table.
        """
        # block on first entry
        if self._tableBlockingLevel == 0:
            if _disableScroll:
                self._scrollOverride = True

            # use the Qt widget to block signals - selectionModel must also be blocked
            _tableState.modelBlocker = QtCore.QSignalBlocker(self.selectionModel())
            _tableState.rootBlocker = QtCore.QSignalBlocker(self)
            # _tableState.enabledState = self.updatesEnabled()
            # self.setUpdatesEnabled(False)

            if blanking and self.project:
                if self.project:
                    self.project.blankNotification()

        self._tableBlockingLevel += 1

    def _unblockTableEvents(self, blanking=True, _disableScroll=False, _tableState=None):
        """Unblock all updates/signals/notifiers in the table.
        """
        if self._tableBlockingLevel > 0:
            self._tableBlockingLevel -= 1

            # unblock all signals on last exit
            if self._tableBlockingLevel == 0:
                if blanking and self.project:
                    if self.project:
                        self.project.unblankNotification()

                _tableState.modelBlocker = None
                _tableState.rootBlocker = None
                # self.setUpdatesEnabled(_tableState.enabledState)
                # _tableState.enabledState = None

                if _disableScroll:
                    self._scrollOverride = False

                self.update()
        else:
            raise RuntimeError('Error: tableBlockingLevel already at 0')

    @contextmanager
    def _blockTableSignals(self, callerId='', blanking=True, _disableScroll=False):
        """Block all signals from the table
        """
        _tableState = _BlockingContent()
        self._blockTableEvents(blanking, _disableScroll=_disableScroll, _tableState=_tableState)
        try:
            yield  # yield control to the calling process

        except Exception as es:
            raise es
        finally:
            self._unblockTableEvents(blanking, _disableScroll=_disableScroll, _tableState=_tableState)

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

        self.setCurrent()
        super().mousePressEvent(event)

    def getRightMouseItem(self):
        if self._rightClickedTableIndex:
            row = self._rightClickedTableIndex.row()
            return self._df.iloc[self.model()._sortOrder[row]]

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

        i = self.currentIndex()
        if i is not None:
            text = i.data().strip()
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

            # create new model and set in table
            _model = _SimplePandasTableModel(self._df, view=self)
            self.setModel(_model)
            self.resizeColumnsToContents()

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
        self._objects = []
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
                                           # self._updateTableCallback,
                                           partial(self._queueGeneralNotifier, self._updateTableCallback),
                                           onceOnly=True)

        if self.rowClass:
            # 'i-1' residue spawns rename but the 'i' residue only fires a change
            self._rowNotifier = Notifier(self.project,
                                         [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE],
                                         self.rowClass.__name__,
                                         # self._updateRowCallback,
                                         partial(self._queueGeneralNotifier, self._updateRowCallback),
                                         onceOnly=True)  # should be True, but doesn't work

        if isinstance(self.cellClassNames, list):
            for cellClass in self.cellClassNames:
                self._cellNotifiers.append(Notifier(self.project,
                                                    [Notifier.CHANGE, Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                                    cellClass[OBJECT_CLASS].__name__,
                                                    partial(self._updateCellCallback, cellClass[OBJECT_PARENT]),
                                                    onceOnly=True))
        else:
            if self.cellClassNames:
                self._cellNotifiers.append(Notifier(self.project,
                                                    [Notifier.CHANGE, Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                                    self.cellClassNames[OBJECT_CLASS].__name__,
                                                    partial(self._updateCellCallback, self.cellClassNames[OBJECT_PARENT]),
                                                    onceOnly=True))

        if self.selectCurrent:
            self._selectCurrentNotifier = Notifier(self.current,
                                                   [Notifier.CURRENT],
                                                   self.callBackClass._pluralLinkName,
                                                   self._selectCurrentCallBack
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
        self._queueAppend([func, data, data[Notifier.TRIGGER]])

    def _clearTableNotifiers(self):
        """Clean up the notifiers
        """
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
        with self._blockTableSignals('_doubleClickCallback', blanking=False, _disableScroll=True):

            idx = self.currentIndex()

            # get the current selected objects from the table - objects now persistent after single-click
            objList = []
            if self._lastSelection is not None:
                objList = self._lastSelection  #['selection']

            if idx:
                row = self.model()._sortOrder[idx.row()]
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
        # selects all the items in the row
        selection = fromSelection if fromSelection else model.selectedRows()

        if selection:
            selectedObjects = []
            valuesDict = defaultdict(list)
            for idx in selection:
                row = self.model()._sortOrder[idx.row()]  # map to sorted rows?
                col = idx.column()

                if self._objects and len(self._objects) > 0:
                    if isinstance(self._objects[0], pd.Series):
                        h = self.horizontalHeaderItem(col).text()
                        v = self.item(row, col).text()
                        valuesDict[h].append(v)

                    else:
                        _data = self._df.iloc[row]
                        objIndex = _data[self.PRIMARYCOLUMN]
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

                delta = time_ns() - self._tableSelectionBlockingLevel
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

        with self._blockTableSignals('_changeTableSelection', blanking=False, _disableScroll=True):

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

                delta = time_ns() - self._tableSelectionBlockingLevel
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

                _sOrder = self.model()._sortOrder
                _dfTemp = self._df.reset_index()
                data = [_dfTemp[_dfTemp[self._OBJECT] == obj] for obj in uniqObjs]
                rows = [_sOrder.index(_dt.index[0]) for _dt in data if not _dt.empty]
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

    def _queueProcess(self):
        """Process current items in the queue
        """
        with QtCore.QMutexLocker(self._lock):
            # protect the queue switching
            self._queueActive = self._queuePending
            self._queuePending = UpdateQueue()

        for itm in self._queueActive.items():
            try:
                func, data, trigger = itm
                func(data)
            except Exception as es:
                getLogger().debug(f'Error in {self.__class__.__name__} update: {es}')

    def _queueAppend(self, itm):
        """Append a new item to the queue
        """
        self._queuePending.put(itm)
        if not self._scheduler.isActive and not self._scheduler.isBusy:
            self._scheduler.start()

        elif self._scheduler.isBusy:
            # caught during the queue processing event, need to restart
            self._scheduler.restart = True
