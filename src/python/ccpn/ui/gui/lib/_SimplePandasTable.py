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
__dateModified__ = "$dateModified: 2022-03-02 16:24:47 +0000 (Wed, March 02, 2022) $"
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

from ccpn.ui.gui.guiSettings import getColours, GUITABLE_ITEM_FOREGROUND
from ccpn.ui.gui.widgets.Font import setWidgetFont, TABLEFONT, getFontHeight, getFont
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.widgets.Base import Base


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

    def __init__(self, parent=None, mainWindow=None, showHorizontalHeader=True, showVerticalHeader=True, **kwds):
        super().__init__(parent)
        Base._init(self, **kwds)

        self._parent = parent
        if mainWindow:
            self.mainWindow = mainWindow
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current

        # set stylesheet
        self.colours = getColours()
        self._defaultStyleSheet = self.styleSheet % self.colours
        self.setStyleSheet(self._defaultStyleSheet)
        self.setAlternatingRowColors(True)

        # set the preferred scrolling behaviour
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setSelectionBehavior(self.SelectRows)

        # enable sorting and sort on the first column
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)

        # the resizeColumnsToContents is REALLY slow :|
        _header = self.horizontalHeader()
        # set Interactive and last column to expanding
        _header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        _header.setStretchLastSection(True)
        # only look at visible section
        _header.setResizeContentsPrecision(5)
        _header.setDefaultAlignment(QtCore.Qt.AlignLeft)
        _header.setMinimumSectionSize(16)
        _header.setHighlightSections(self.font().bold())
        setWidgetFont(self, name=TABLEFONT)
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
        setWidgetFont(self, name=TABLEFONT)
        setWidgetFont(_header, name=TABLEFONT)
        setWidgetFont(self.verticalHeader(), name=TABLEFONT)

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
        pass

    def _postChangeSelectionOrderCallback(self, *args):
        """Handle updating the selection when the table has been sorted
        """
        _model = self.model()
        _selModel = self.selectionModel()
        _selection = self.selectionModel().selectedIndexes()

        if _model._sortOrder and _model._oldSortOrder:
            # get the pre-sorted mapping
            if (_rows := set(_model._oldSortOrder[itm.row()] for itm in _selection)):
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
                    # unblock so nothing responds
                    _selModel.blockSignals(False)
                    self.blockSignals(False)


class _SimplePandasTableModel(QtCore.QAbstractTableModel):
    """A simple table model to view pandas DataFrames
    """
    _defaultForegroundColour = QtGui.QColor(getColours()[GUITABLE_ITEM_FOREGROUND])
    _CHECKROWS = 5
    _MINCHARS = 4
    _MAXCHARS = 100
    _chrWidth = 12
    _chrHeight = 12

    def __init__(self, data, view=None):
        """Initialise the pandas model
        Allocates space for foreground/background colours
        :param data: pandas DataFrame
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError('data must be of type pd.DataFrame')

        QtCore.QAbstractTableModel.__init__(self)
        self._data = data

        # set the initial sort-order
        self._oldSortOrder = [row for row in range(data.shape[0])]
        self._sortOrder = [row for row in range(data.shape[0])]

        # create numpy arrays to match the data that will hold background colour
        self._colour = np.zeros(self._data.shape, dtype=np.object)

        self._view = view
        if view:
            self.fontMetric = QtGui.QFontMetricsF(view.font())
            self.bbox = self.fontMetric.boundingRect
            self._chrWidth = 1 + self.bbox('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789').width() / 36
            self._chrHeight = self.bbox('A').height() + 8

    def rowCount(self, parent=None):
        """Return the row count for the dataFrame
        """
        return self._data.shape[0]

    def columnCount(self, parent=None):
        """Return the column count for the dataFrame
        """
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Process the data callback for the model
        """
        if index.isValid():
            # get the source cell
            _row = self._sortOrder[index.row()]
            _column = index.column()

            if role == QtCore.Qt.DisplayRole:
                _cell = self._data.iat[_row, _column]

                # # nan
                # if pd.isnull(_cell):
                #     return ''

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
                _cell = self._data.iat[_row, _column]

                # # nan
                # if pd.isnull(_cell):
                #     return 'nan'

                return str(_cell)

        return None

    def headerData(self, col, orientation, role=None):
        """Return the column headers
        """
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col] if not self._data.empty else None
        # if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
        #     return self._data.index[col] if not self._data.empty else None

        if role == QtCore.Qt.SizeHintRole:
            # process the heights/widths of the headers

            if orientation == QtCore.Qt.Horizontal:
                try:
                    # get the estimated width of the column
                    _width = self._estimateColumnWidth(col)

                    if col == self.columnCount() - 1 and self._view is not None:
                        # stretch the last column to fit the table - sum the previous columns
                        _colWidths = sum([self._estimateColumnWidth(cc)
                                          for cc in range(self.columnCount() - 1)])
                        _viewWidth = self._view.viewport().size().width()
                        _width = max(_width, _viewWidth - _colWidths)

                    # return the size
                    return QtCore.QSize(_width, self._chrHeight)

                except Exception:
                    # return the default QSize
                    return QtCore.QSize(self._chrWidth, self._chrHeight)

        return None

    def _estimateColumnWidth(self, col):
        """Estimate the width for the column from the header and fixed number of rows
        """
        # get the width of the header
        _colName = self._data.columns[col] if not self._data.empty else None
        _len = max(len(_colName) if _colName else 0, self._MINCHARS)  # never smaller than 4 characters
        # iterate over a few rows to get an estimate
        for _row in range(min(self.rowCount(), self._CHECKROWS)):
            _cell = self._data.iat[_row, col]

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
        _width = min(self._MAXCHARS, _len) * self._chrWidth
        return _width

    def setForeground(self, row, column, colour):
        """Set the foreground colour for cell at position (row, column).

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
        """Set the background colour for cell at position (row, column).

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

    def sort(self, column: int, order: QtCore.Qt.SortOrder = ...) -> None:
        """Sort the underlying pandas DataFrame
        Required as there is no poxy model to handle the sorting
        """
        self.layoutAboutToBeChanged.emit()

        col = self._data.columns[column]

        _newData = self._data.copy()
        # create temporary column to facilitate the new ordering after pandas sorting
        _newData['_sortOrder'] = range(_newData.shape[0])

        # perform the sort on the specified column
        _newData.sort_values(by=col, ascending=True if order else False, inplace=True)
        self._oldSortOrder = self._sortOrder
        self._sortOrder = list(_newData['_sortOrder'])

        # # store the new ordering and remove from the dataFrame
        # self._sortOrder = list(self._data['_sortOrder'])
        # self._data.drop(['_sortOrder'], axis=1, inplace=True)

        # emit a signal to spawn an update of the table and notify headers to update
        self.layoutChanged.emit()

    def mapToSource(self, indexes):
        """Map the cell index to the co-ordinates in the pandas dataFrame
        Return list of tuples of dataFrame positions
        """
        idxs = [(self._sortOrder[idx.row()], idx.column()) if idx.isValid() else (None, None) for idx in indexes]
        return idxs


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
        self._data = np.zeros((row, column), dtype=np.object)

    def rowCount(self, parent=None):
        """Return the row count for the dataFrame
        """
        return self._data.shape[0]

    def columnCount(self, parent=None):
        """Return the column count for the dataFrame
        """
        return self._data.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Process the data callback for the model
        """
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                return str(self._data.iat[index.row(), index.column()])

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
    #                 self._data[span, ]
    #         elif role == QtCore.Qt.UserRole + 2:
    #             pass


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
