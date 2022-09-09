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
__dateModified__ = "$dateModified: 2022-09-09 21:15:58 +0100 (Fri, September 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-09-08 17:12:49 +0100 (Thu, September 08, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from collections import OrderedDict
# from contextlib import contextmanager
# from dataclasses import dataclass
from functools import partial
# from time import time_ns
# from types import SimpleNamespace
import typing

# from ccpn.core.lib.CallBack import CallBack
# from ccpn.core.lib.CcpnSorting import universalSortKey
# from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, catchExceptions
# from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.guiSettings import getColours, GUITABLE_ITEM_FOREGROUND
from ccpn.ui.gui.widgets.Font import setWidgetFont, TABLEFONT, getFontHeight
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
# from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.ColumnViewSettings import ColumnViewSettingsPopup
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.SearchWidget import attachSimpleSearchWidget
# from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.FileDialog import TablesFileDialog
from ccpn.ui.gui.widgets.table._TableModel import _TableModel
from ccpn.ui.gui.widgets.table._TableAdditions import _TableHeaderColumns, _TableExport, _TableSearch, _TableDelete
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger
from ccpn.util.Common import copyToClipboard


# from ccpn.util.OrderedSet import OrderedSet


# ORIENTATIONS = {'h'                 : QtCore.Qt.Horizontal,
#                 'horizontal'        : QtCore.Qt.Horizontal,
#                 'v'                 : QtCore.Qt.Vertical,
#                 'vertical'          : QtCore.Qt.Vertical,
#                 QtCore.Qt.Horizontal: QtCore.Qt.Horizontal,
#                 QtCore.Qt.Vertical  : QtCore.Qt.Vertical,
#                 }

# # define a role to return a cell-value
# DTYPE_ROLE = QtCore.Qt.UserRole + 1000
# VALUE_ROLE = QtCore.Qt.UserRole + 1001
# INDEX_ROLE = QtCore.Qt.UserRole + 1002
#
# EDIT_ROLE = QtCore.Qt.EditRole
# _EDITOR_SETTER = ('setColor', 'selectValue', 'setData', 'set', 'setValue', 'setText', 'setFile')
# _EDITOR_GETTER = ('get', 'value', 'text', 'getFile')


#=========================================================================================
# TableABC
#=========================================================================================

class TableABC(_TableHeaderColumns, _TableExport, _TableSearch, _TableDelete, QtWidgets.QTableView):
    styleSheet = """QTableView {
                        background-color: %(GUITABLE_BACKGROUND)s;
                        alternate-background-color: %(GUITABLE_ALT_BACKGROUND)s;
                        border: %(_BORDER_WIDTH)spx solid %(BORDER_NOFOCUS)s;
                        border-radius: 2px;
                    }
                    QTableView::focus {
                        background-color: %(GUITABLE_BACKGROUND)s;
                        alternate-background-color: %(GUITABLE_ALT_BACKGROUND)s;
                        border: %(_BORDER_WIDTH)spx solid %(BORDER_FOCUS)s;
                        border-radius: 2px;
                    }
                    QTableView::item {
                        padding: %(_CELL_PADDING)spx;
                    }
                    QTableView::item::selected {
                        background-color: %(GUITABLE_SELECTED_BACKGROUND)s;
                        color: %(GUITABLE_SELECTED_FOREGROUND)s;
                    }
                    """

    # NOTE:ED overrides QtCore.Qt.ForegroundRole
    # QTableView::item - color: %(GUITABLE_ITEM_FOREGROUND)s;
    # QTableView::item:selected - color: %(GUITABLE_SELECTED_FOREGROUND)s;

    # columnDefs = None
    # _enableExport = True
    # _enableDelete = False
    # _enableSearch = True

    # _tableBlockingLevel = 0

    _enableSelectionCallback = False
    _enableActionCallback = False

    def __init__(self, parent=None, df=None,
                 multiSelect=True, selectRows=True,
                 showHorizontalHeader=True, showVerticalHeader=True,
                 borderWidth=2, cellPadding=2,
                 _resize=False, setWidthToColumns=False, setHeightToRows=False
                 ):
        super().__init__(parent)
        # Base._init(self, **kwds)

        self._parent = parent

        # # initialise the internal data storage
        # self._defaultDf = None
        # self._tableBlockingLevel = 0

        # set stylesheet
        colours = getColours()
        # add border-width/cell-padding options
        self._borderWidth = colours['_BORDER_WIDTH'] = borderWidth
        self._cellPadding = colours['_CELL_PADDING'] = cellPadding  # the extra padding for the selected cell-item
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

        height = getFontHeight(name=TABLEFONT, size='MEDIUM')
        self._setHeaderWidgets(height, showHorizontalHeader, showVerticalHeader)
        self.setMinimumSize(3 * height, 3 * height + self.horizontalScrollBar().height())

        # set up the menus
        self.setTableMenu()
        self.setHeaderMenu()

        # initialise the table
        self._initialiseDf(df, _resize, setHeightToRows, setWidthToColumns)

        # set selection/action callbacks
        self.doubleClicked.connect(self._actionConnect)

    def _initialiseDf(self, df, resize, setHeightToRows, setWidthToColumns):
        """Initialise the dataFrame
        """
        if df is not None and not df.empty:
            # set the model
            data = pd.DataFrame(df)
            model = _TableModel(data, view=self)
            self.setModel(model)

            self.resizeColumnsToContents()
            if resize:
                # resize if required
                self.resizeRowsToContents()

            if setWidthToColumns:
                self.setWidthToColumns()
            if setHeightToRows:
                self.setHeightToRows()

        else:
            # set a default empty model
            data = pd.DataFrame({})
            model = _TableModel(data, view=self)
            self.setModel(model)

    def setModel(self, model: QtCore.QAbstractItemModel) -> None:
        """Set the model for the view
        """
        super().setModel(model)

        # attach a handler for updating the selection on sorting
        self.model().layoutAboutToBeChanged.connect(self._preChangeSelectionOrderCallback)
        self.model().layoutChanged.connect(self._postChangeSelectionOrderCallback)

        # set selection callback because the model has changed?
        self.selectionModel().selectionChanged.connect(self._selectionConnect)

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

    def _setHeaderWidgets(self, _height, showHorizontalHeader, showVerticalHeader):
        """Initialise the headers
        """
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
        _header.setDefaultSectionSize(_height)
        _header.setMinimumSectionSize(_height)

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
    # Properties
    #=========================================================================================

    @property
    def _df(self):
        """Return the Pandas-dataFrame holding the data
        """
        return self.model().df

    @_df.setter
    def _df(self, value):
        self.model().df = value

    # @property
    # def enableExport(self):
    #     """Return True of the export options are enabled in the table menu
    #     """
    #     return self._enableExport

    # @property
    # def enableDelete(self):
    #     """Return True of the delete options are enabled in the table menu
    #     """
    #     return self._enableDelete

    # @property
    # def enableSearch(self):
    #     """Return True of the search options are enabled in the table menu
    #     """
    #     return self._enableSearch

    #=========================================================================================
    # Notifier callbacks
    #=========================================================================================

    def _selectionConnect(self, selected, deselected):
        """Handle the callback for a selection
        """
        getLogger().debug2(f'selection {selected}  {deselected}')
        if self._enableSelectionCallback:
            # currently passes QItemSelections
            self.selectionCallback(selected, deselected)

    def _actionConnect(self, modelIndex):
        """Handle the callback for a selection
        """
        getLogger().debug2(f'action {modelIndex}')
        if self._enableActionCallback:
            # currently passes a QModelIndex
            self.actionCallback(modelIndex)

    def selectionCallback(self, selected, deselected):
        """Handle item selection has changed in table - call user callback
        :param selected: table indexes selected
        :param deselected: table indexes deselected
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}.selectionCallback not implemented')

    def actionCallback(self, index):
        """Handle item selection has changed in table - call user callback
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}.actionCallback not implemented')

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

            elif keyMod not in allKeyModifers:
                # fire the action callback (double-click on selected)
                self._actionConnect(self.currentIndex())

        elif key in [QtCore.Qt.Key_Escape]:
            # press the escape-key to clear the selection
            self.clearSelection()

    def _processDroppedItems(self, data):
        """CallBack for Drop events
        """
        pass

    def _handleDroppedItems(self, pids, objType, pulldown):
        """Handle dropped items.
        
        :param pids: the selected objects pids
        :param objType: the instance of the obj to handle, E.g. PeakList
        :param pulldown: the pulldown of the module wich updates the table
        :return: Actions: Select the dropped item on the table or/and open a new modules if multiple drops.
        If multiple different obj instances, then asks first.
        """
        pass

    def scrollToSelectedIndex(self):
        """Scroll table to show the nearest selected index
        """
        h = self.horizontalHeader()
        for i in range(h.count()):
            if not h.isSectionHidden(i) and h.sectionViewportPosition(i) >= 0:
                if (selection := self.selectionModel().selectedIndexes()):
                    self.scrollTo(selection[0], self.EnsureVisible)  # doesn't dance around so much
                    return

    #=========================================================================================
    # Other methods
    #=========================================================================================

    # def setExportEnabled(self, value):
    #     """Enable/disable the export option from the right-mouse menu.
    #
    #     :param bool value: enabled True/False
    #     """
    #     if not isinstance(value, bool):
    #         raise TypeError(f'{self.__class__.__name__}.setExportEnabled: value must be True/False')
    #
    #     self._enableExport = value

    # def setDeleteEnabled(self, value):
    #     """Enable/disable the delete option from the right-mouse menu.
    #
    #     :param bool value: enabled True/False
    #     """
    #     if not isinstance(value, bool):
    #         raise TypeError(f'{self.__class__.__name__}.setDeleteEnabled: value must be True/False')
    #
    #     self._enableDelete = value

    # def setSearchEnabled(self, value):
    #     """Enable/disable the search option from the right-mouse menu.
    #
    #     :param bool value: enabled True/False
    #     """
    #     if not isinstance(value, bool):
    #         raise TypeError(f'{self.__class__.__name__}.setSearchEnabled: value must be True/False')
    #
    #     self._enableSearch = value

    def setWidthToColumns(self):
        """Set the width of the table to the column widths
        """
        # need to get values from padding
        header = self.horizontalHeader()
        width = -2  # left/right borders
        for nn in range(header.count()):
            if not header.isSectionHidden(nn) and header.sectionViewportPosition(nn) >= 0:
                width += (self.columnWidth(nn) + 1)  # cell border on right-hand-side

        self.setFixedWidth(width)

    def setHeightToRows(self):
        """Set the height of the table to the row heights
        """
        height = 2 * self.horizontalHeader().height()

        header = self.verticalHeader()
        for nn in range(header.count()):
            if not header.isSectionHidden(nn) and header.sectionViewportPosition(nn) >= 0:
                height += (self.rowHeight(nn) + 1)

        self.setFixedHeight(height)

    def mapToSource(self, positions=None):
        """Return a tuple of the locations of the specified visible-table positions in the dataFrame.

        positions must be an iterable of table-positions, each a list|tuple of the form [row, col].

        :param positions: iterable of list|tuples
        :return: tuple to tuples
        """
        if not isinstance(positions, typing.Iterable):
            raise TypeError(f'{self.__class__.__name__}.mapToSource: positions must be an iterable of list|tuples of the form [row, col]')
        if not all(isinstance(pos, (list, tuple)) and
                   len(pos) == 2 and isinstance(pos[0], int) and isinstance(pos[1], int) for pos in positions):
            raise TypeError(f'{self.__class__.__name__}.mapToSource: positions must be an iterable of list|tuples of the form [row, col]')

        sortIndex = self.model()._sortIndex
        df = self.model().df
        if not all((0 <= pos[0] < df.shape[0]) and (0 <= pos[1] < df.shape[1]) for pos in positions):
            raise TypeError(f'{self.__class__.__name__}.mapToSource: positions contains invalid values')

        return tuple((sortIndex[pos[0]], pos[1]) for pos in positions)

    def mapRowsToSource(self, rows=None) -> tuple:
        """Return a tuple of the source rows in the dataFrame.

        rows must be an iterable of integers, or None.
        None will return the source rows for the whole table.

        :param rows: iterable of ints
        :return: tuple of ints
        """
        sortIndex = self.model()._sortIndex
        if rows is None:
            return tuple(self.model()._sortIndex)

        if not isinstance(rows, typing.Iterable):
            raise TypeError(f'{self.__class__.__name__}.mapRowsToSource: rows must be an iterable of ints')
        if not all(isinstance(row, int) for row in rows):
            raise TypeError(f'{self.__class__.__name__}.mapRowsToSource: rows must be an iterable of ints')

        df = self.model().df
        if not all((0 <= row < df.shape[0]) for row in rows):
            raise TypeError(f'{self.__class__.__name__}.mapToSource: rows contains invalid values')

        return tuple(sortIndex[row] if 0 <= row < len(sortIndex) else None for row in rows)

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    def setTableMenu(self, menu=None):
        """Set up the context menu for the main table
        """
        self.tableMenu = menu or Menu('', self, isFloatWidget=True)
        setWidgetFont(self.tableMenu, )

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._raiseTableContextMenu)

        self._copySelectedCellAction = self.tableMenu.addAction('Copy clicked cell value', self._copySelectedCell)

        # NOTE:ED - call additional _inits here to add options to the table menu
        _TableExport.setTableMenu(self, self.tableMenu)
        _TableSearch.setTableMenu(self, self.tableMenu)
        _TableDelete.setTableMenu(self, self.tableMenu)

        # self.tableMenu.addAction('Export Visible Table', partial(self.exportTableDialog, exportAll=False))
        # self.tableMenu.addAction('Export All Columns', partial(self.exportTableDialog, exportAll=True))
        # self.tableMenu.addAction('Delete Selection', self.deleteObjFromTable)

        # self._searchAction = self.tableMenu.addAction('Filter...', self.showSearchSettings)

        return self.tableMenu

    def _raiseTableContextMenu(self, pos):
        """Create a new menu and popup at cursor position
        """
        # self.initSearchWidget()

        # NOTE:ED - call additional _inits here to add options to the table menu
        _TableExport.setTableMenuOptions(self, self.tableMenu)
        _TableSearch.setTableMenuOptions(self, self.tableMenu)

        # # disable the export options if not available
        # if (actions := [act for act in self.tableMenu.actions() if act.text() == 'Export Visible Table']):
        #     actions[0].setEnabled(self._enableExport)
        # if (actions := [act for act in self.tableMenu.actions() if act.text() == 'Export All Columns']):
        #     actions[0].setEnabled(self._enableExport)

        # disable the delete action if not available
        if (actions := [act for act in self.tableMenu.actions() if act.text() == 'Delete Selection']):
            actions[0].setEnabled(self._enableDelete)

        # # disable the search action if not available
        # if (actions := [act for act in self.tableMenu.actions() if act.text() == 'Filter...']):
        #     actions[0].setEnabled(self.searchWidget is not None)

        pos = QtCore.QPoint(pos.x() + 10, pos.y() + 10)
        self.tableMenu.exec_(self.mapToGlobal(pos))

    #=========================================================================================
    # Header context menu
    #=========================================================================================

    def setHeaderMenu(self, menu=None):
        """Set up the context menu for the table header
        """
        headers = self.horizontalHeader()
        headers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        headers.customContextMenuRequested.connect(self._raiseHeaderContextMenu)

        self.tableHeaderMenu = menu or QtWidgets.QMenu()
        setWidgetFont(self.tableHeaderMenu, )

        # NOTE:ED - call additional _inits here to add options to the header menu
        _TableHeaderColumns.setHeaderMenu(self, self.tableHeaderMenu)

        return self.tableHeaderMenu

    def _raiseHeaderContextMenu(self, pos):
        """Raise the menu on the header
        """
        if self._df is None or self._df.empty:
            return

        pos = QtCore.QPoint(pos.x() + 10, pos.y() + 10)  # move the popup a bit down; otherwise can trigger an event if the pointer is just on top the first item

        # NOTE:ED - call additional _inits here to add enable/disable/hide to the header menu
        _TableHeaderColumns.setHeaderMenuOptions(self, self.tableHeaderMenu)

        if len(self.tableHeaderMenu.actions()):
            self.tableHeaderMenu.exec_(self.mapToGlobal(pos))

    #=========================================================================================
    # Table functions
    #=========================================================================================

    def _copySelectedCell(self):
        """Copy the current cell-value to the clipboard
        """
        idx = self.currentIndex()
        if idx is not None:
            text = idx.data().strip()
            copyToClipboard([text])

    # def exportTableDialog(self, exportAll=True):
    #     """export the contents of the table to a file
    #     The actual data values are exported, not the visible items which may be rounded due to the table settings
    #
    #     :param exportAll: True/False - True implies export whole table - but in visible order
    #                                 False, export only the visible table
    #     """
    #     model = self.model()
    #     df = model.df
    #     rows, cols = model.rowCount(), model.columnCount()
    #
    #     if df is None or df.empty:
    #         MessageDialog.showWarning('Export Table to File', 'Table does not contain a dataFrame')
    #
    #     else:
    #         rowList = [model._sortIndex[row] for row in range(rows)]
    #         if exportAll:
    #             colList = list(self.model().df.columns)  # assumes that the dataFrame column-headings match the table
    #         else:
    #             colList = [col for ii, col, in enumerate(list(self.model().df.columns)) if not self.horizontalHeader().isSectionHidden(ii)]
    #
    #         self._exportTableDialog(df, rowList=rowList, colList=colList)

    # def deleteObjFromTable(self):
    #     """Delete all objects in the selection from the project
    #     """
    #     # MUST BE SUBCLASSED
    #     raise NotImplementedError("Code error: function not implemented")

    # #=========================================================================================
    # # Exporters
    # #=========================================================================================
    #
    # @staticmethod
    # def _dataFrameToExcel(dataFrame, path, sheet_name='Table', columns=None):
    #     if dataFrame is not None:
    #         path = aPath(path)
    #         path = path.assureSuffix('xlsx')
    #         if columns is not None and isinstance(columns, list):  #this is wrong. columns can be a 1d array
    #             dataFrame.to_excel(path, sheet_name=sheet_name, columns=columns, index=False)
    #         else:
    #             dataFrame.to_excel(path, sheet_name=sheet_name, index=False)
    #
    # @staticmethod
    # def _dataFrameToCsv(dataFrame, path, *args):
    #     dataFrame.to_csv(path)
    #
    # @staticmethod
    # def _dataFrameToTsv(dataFrame, path, *args):
    #     dataFrame.to_csv(path, sep='\t')
    #
    # @staticmethod
    # def _dataFrameToJson(dataFrame, path, *args):
    #     dataFrame.to_json(path, orient='split', default_handler=str)
    #
    # def findExportFormats(self, path, dataFrame, sheet_name='Table', filterType=None, columns=None):
    #     formatTypes = OrderedDict([
    #         ('.xlsx', self._dataFrameToExcel),
    #         ('.csv', self._dataFrameToCsv),
    #         ('.tsv', self._dataFrameToTsv),
    #         ('.json', self._dataFrameToJson)
    #         ])
    #
    #     # extension = os.path.splitext(path)[1]
    #     extension = aPath(path).suffix
    #     if not extension:
    #         extension = '.xlsx'
    #     if extension in formatTypes.keys():
    #         formatTypes[extension](dataFrame, path, sheet_name, columns)
    #         return
    #     else:
    #         try:
    #             self._findExportFormats(str(path) + filterType, sheet_name)
    #         except:
    #             MessageDialog.showWarning('Could not export', 'Format file not supported or not provided.'
    #                                                           '\nUse one of %s' % ', '.join(formatTypes))
    #             getLogger().warning('Format file not supported')
    #
    # def _exportTableDialog(self, dataFrame, rowList=None, colList=None):
    #
    #     self.saveDialog = TablesFileDialog(parent=None, acceptMode='save', selectFile='ccpnTable.xlsx',
    #                                        fileFilter=".xlsx;; .csv;; .tsv;; .json ")
    #     self.saveDialog._show()
    #     path = self.saveDialog.selectedFile()
    #     if path:
    #         sheet_name = 'Table'
    #         if dataFrame is not None and not dataFrame.empty:
    #
    #             if colList:
    #                 dataFrame = dataFrame[colList]  # returns a new dataFrame
    #             if rowList:
    #                 dataFrame = dataFrame[:].iloc[rowList]
    #
    #             ft = self.saveDialog.selectedNameFilter()
    #
    #             self.findExportFormats(path, dataFrame, sheet_name=sheet_name, filterType=ft, columns=colList)

    # #=========================================================================================
    # # Search methods
    # #=========================================================================================
    #
    # def initSearchWidget(self):
    #     if self._enableSearch and self.searchWidget is None:
    #         if not attachSimpleSearchWidget(self._parent, self):
    #             getLogger().warning('Filter option not available')
    #
    # def hideSearchWidget(self):
    #     if self.searchWidget is not None:
    #         self.searchWidget.hide()
    #
    # def showSearchSettings(self):
    #     """ Display the search frame in the table"""
    #
    #     self.initSearchWidget()
    #     if self.searchWidget is not None:
    #         if not self.searchWidget.isVisible():
    #             self.searchWidget.show()
    #         else:
    #             self.searchWidget.hideSearch()
    #
    # def refreshTable(self):
    #     # subclass to refresh the groups
    #     if self._defaultDf is not None:
    #         _updateSimplePandasTable(self, self._defaultDf)
    #     else:
    #         getLogger().warning(f'{self.__class__.__name__}.refreshTable: defaultDf is not defined')
    #     # self.updateTableExpanders()
    #
    # def setDataFromSearchWidget(self, dataFrame):
    #     """Set the data for the table from the search widget
    #     """
    #     _updateSimplePandasTable(self, dataFrame)
    #
    #=========================================================================================
    # hidden column information
    #=========================================================================================

    # def getHiddenColumns(self):
    #     """
    #     get a list of currently hidden columns
    #     """
    #     hiddenColumns = self._hiddenColumns
    #     ll = list(set(hiddenColumns))
    #     return [x for x in ll if x in self.columnTexts]
    #
    # def setHiddenColumns(self, texts, update=True):
    #     """
    #     set a list of columns headers to be hidden from the table.
    #     """
    #     ll = [x for x in texts if x in self.columnTexts and x not in self._internalColumns]
    #     self._hiddenColumns = ll
    #     if update:
    #         self.showColumns(None)
    #
    # def hideDefaultColumns(self):
    #     """If the table is empty then check visible headers against the last header hidden list
    #     """
    #     for i, columnName in enumerate(self.columnTexts):
    #         # remember to hide the special column
    #         if columnName in self._internalColumns:
    #             self.hideColumn(i)
    #
    # @property
    # def columnTexts(self):
    #     """return a list of column texts.
    #     """
    #     try:
    #         return list(self._df.columns)
    #     except:
    #         return []
    #
    # def showColumns(self, df):
    #     # show the columns in the list
    #     hiddenColumns = self.getHiddenColumns()
    #
    #     for i, colName in enumerate(self.columnTexts):
    #         # always hide the internal columns
    #         if colName in (hiddenColumns + self._internalColumns):
    #             self._hideColumn(colName)
    #         else:
    #             self._showColumn(colName)
    #
    # def _showColumn(self, name):
    #     if name not in self.columnTexts:
    #         return
    #     if name in self._hiddenColumns:
    #         self._hiddenColumns.remove(name)
    #     i = self.columnTexts.index(name)
    #     self.showColumn(i)
    #
    # def _hideColumn(self, name):
    #     if name not in self.columnTexts:
    #         return
    #     if name not in (self._hiddenColumns + self._internalColumns):
    #         self._hiddenColumns.append(name)
    #     i = self.columnTexts.index(name)
    #     self.hideColumn(i)


#=========================================================================================
# Table testing
#=========================================================================================

def main():
    """Show the test-table
    """
    MAX_ROWS = 5

    from ccpn.ui.gui.widgets.Application import TestApplication
    import pandas as pd
    import random

    data = [[1, 150, 300, 900, float('nan'), 80.1, 'delta'],
            [2, 200, 500, 300, float('nan'), 34.2, ['help', 'more', 'chips']],
            [3, 100, np.nan, 1000, None, -float('Inf'), 'charlie'],
            [4, 999, np.inf, 500, None, float('Inf'), 'echo'],
            [5, 300, -np.inf, 450, 700, 150.3, 'bravo']
            ]

    # multiIndex columnHeaders
    cols = ("No", "Toyota", "Ford", "Tesla", "Nio", "Other", "NO")
    rowIndex = ["AAA", "BBB", "CCC", "DDD", "EEE"]

    for ii in range(MAX_ROWS):
        chrs = ''.join(chr(random.randint(65, 68)) for _ in range(5))
        rowIndex.append(chrs[:3])
        data.append([6 + ii,
                     300 + random.randint(1, MAX_ROWS),
                     random.random() * 1e6,
                     450 + random.randint(-100, 400),
                     700 + random.randint(-MAX_ROWS, MAX_ROWS),
                     150.3 + random.random() * 1e2,
                     'bravo' + chrs[3:]])

    df = pd.DataFrame(data, columns=cols, index=rowIndex)

    # show the example table
    app = TestApplication()
    win = QtWidgets.QMainWindow()
    frame = QtWidgets.QFrame()
    layout = QtWidgets.QGridLayout()
    frame.setLayout(layout)

    table = TableABC(df=df)
    win.setCentralWidget(frame)
    frame.layout().addWidget(table, 0, 0)

    win.setWindowTitle(f'Testing {table.__class__.__name__}')
    win.show()

    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
