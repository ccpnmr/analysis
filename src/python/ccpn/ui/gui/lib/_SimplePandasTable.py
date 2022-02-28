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
__dateModified__ = "$dateModified: 2022-02-28 18:28:42 +0000 (Mon, February 28, 2022) $"
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
from ccpn.ui.gui.widgets.Font import setWidgetFont, TABLEFONT, getFontHeight
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


class _SimplePandasTableModel(QtCore.QAbstractTableModel):
    """A simple table model to view pandas DataFrames
    """
    _defaultForegroundColour = QtGui.QColor(getColours()[GUITABLE_ITEM_FOREGROUND])

    def __init__(self, data):
        """Initialise the pandas model
        Allocates space for foreground/background colours
        :param data: pandas DataFrame
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError('data must be of type pd.DataFrame')

        QtCore.QAbstractTableModel.__init__(self)
        self._data = data
        # create numpy arrays to match the data that will hold background colour
        self._colour = np.zeros(self._data.shape, dtype=np.object)

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
            _row = index.row()
            _column = index.column()

            if role == QtCore.Qt.DisplayRole:
                _cell = self._data.iat[_row, _column]

                # nan
                if pd.isnull(_cell):
                    return ''

                # Float formatting
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

                # nan
                if pd.isnull(_cell):
                    return 'nan'

                return str(_cell)

        return None

    def headerData(self, col, orientation, role=None):
        """Return the column headers
        """
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self._data.columns[col] if not self._data.empty else None
        return None

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


def _newSimplePandasTable(parent, data):
    """Create a new _SimplePandasTable from a pd.DataFrame
    """
    if not parent:
        raise ValueError('parent not defined')
    if not isinstance(data, pd.DataFrame):
        raise ValueError(f'data is not of type pd.DataFrame - {type(data)}')

    # create a new table
    table = _SimplePandasTableView(parent)

    # set the model
    _model = _SimplePandasTableModel(pd.DataFrame(data))
    table.setModel(_model)

    # # put a proxy in between view and model - REALLY SLOW for big tables
    # table._proxy = QtCore.QSortFilterProxyModel()
    # table._proxy.setSourceModel(_model)
    # table.setModel(table._proxy)

    # table.resizeColumnsToContents()  # these are REALLY slow
    # table.resizeRowsToContents()

    return table


def _updateSimplePandasTable(table, data, _resize=False):
    """Update existing _SimplePandasTable from a new pd.DataFrame
    """
    if not table:
        raise ValueError('table not defined')
    if not isinstance(data, pd.DataFrame):
        raise ValueError(f'data is not of type pd.DataFrame - {type(data)}')

    # create new model and set in table
    _model = _SimplePandasTableModel(data)
    table.setModel(_model)

    if _resize:
        # resize if required
        table.resizeColumnToContents(0)
        table.resizeRowsToContents()
