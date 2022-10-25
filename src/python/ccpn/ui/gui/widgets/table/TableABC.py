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
__dateModified__ = "$dateModified: 2022-10-25 15:59:09 +0100 (Tue, October 25, 2022) $"
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
from dataclasses import dataclass
from contextlib import contextmanager
from functools import partial
import typing

from ccpn.ui.gui.guiSettings import getColours
from ccpn.ui.gui.widgets.Font import setWidgetFont, TABLEFONT, getFontHeight
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.table._TableModel import _TableModel, VALUE_ROLE, INDEX_ROLE
from ccpn.ui.gui.widgets.table._TableAdditions import _TableHeaderColumns, \
    _TableCopyCell, _TableExport, _TableSearch, _TableDelete
from ccpn.ui.gui.widgets.table._TableDelegate import _TableDelegateABC
from ccpn.util.OrderedSet import OrderedSet
from ccpn.util.Logging import getLogger
from ccpn.util.Common import NOTHING


# simple class to store the blocking state of the table
@dataclass
class _BlockingContent:
    modelBlocker = None
    rootBlocker = None


#=========================================================================================
# TableABC
#=========================================================================================

class TableABC(_TableHeaderColumns, _TableCopyCell, _TableExport, _TableSearch, _TableDelete, QtWidgets.QTableView):
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
                        margin: 0px;
                        padding: %(_CELL_PADDING)spx;
                    }
                    QTableView::item:focus {
                        margin: 0px;
                        border: %(_FOCUS_BORDER_WIDTH)spx solid %(BORDER_FOCUS)s;
                        padding: %(_CELL_PADDING_OFFSET)spx;
                    }
                    QTableView::item:selected {
                        background-color: %(GUITABLE_SELECTED_BACKGROUND)s;
                        color: %(GUITABLE_SELECTED_FOREGROUND)s;
                    }
                    """

    # NOTE:ED overrides QtCore.Qt.ForegroundRole
    # QTableView::item - color: %(GUITABLE_ITEM_FOREGROUND)s;
    # QTableView::item:selected - color: %(GUITABLE_SELECTED_FOREGROUND)s;
    # cell uses alternate-background-role for unselected-focused cell

    _columnDefs = None
    _enableSelectionCallback = False
    _enableActionCallback = False
    _actionCallback = NOTHING
    _selectionCallback = NOTHING
    _defaultEditable = True
    _rowHeightScale = None

    # define the default TableModel class
    defaultTableModel = _TableModel

    def __init__(self, parent, df=None,
                 multiSelect=True, selectRows=True,
                 showHorizontalHeader=True, showVerticalHeader=True,
                 borderWidth=2, cellPadding=2, focusBorderWidth=0,
                 _resize=False, setWidthToColumns=False, setHeightToRows=False,
                 setOnHeaderOnly=False, showGrid=False, wordWrap=False,
                 selectionCallback=NOTHING, selectionCallbackEnabled=NOTHING,
                 actionCallback=NOTHING, actionCallbackEnabled=NOTHING,
                 enableExport=NOTHING, enableDelete=NOTHING, enableSearch=NOTHING, enableCopyCell=NOTHING,
                 **kwds
                 ):
        """Initialise the table.

        :param parent:
        :param df:
        :param multiSelect:
        :param selectRows:
        :param showHorizontalHeader:
        :param showVerticalHeader:
        :param borderWidth:
        :param cellPadding:
        :param focusBorderWidth:
        :param _resize:
        :param setWidthToColumns:
        :param setHeightToRows:
        :param setOnHeaderOnly:
        :param showGrid:
        :param wordWrap:
        :param selectionCallback:
        :param selectionCallbackEnabled:
        :param actionCallback:
        :param actionCallbackEnabled:
        :param enableExport:
        :param enableDelete:
        :param enableSearch:
        :param enableCopyCell:
        :param kwds:
        """
        super().__init__(parent)

        # parameters that are NOTHING can be set on the subclass, these are ignored in the parameter-list

        _TableCopyCell._init(self, enableCopyCell)
        _TableExport._init(self, enableExport)
        _TableSearch._init(self, enableSearch)
        _TableDelete._init(self, enableDelete)

        self.setShowGrid(showGrid)
        self._parent = parent

        # set stylesheet
        colours = getColours()
        # add border-width/cell-padding options
        self._borderWidth = colours['_BORDER_WIDTH'] = borderWidth
        self._cellPadding = colours['_CELL_PADDING'] = cellPadding  # the extra padding for the selected cell-item
        self._focusBorderWidth = colours['_FOCUS_BORDER_WIDTH'] = focusBorderWidth
        self._cellPaddingOffset = colours['_CELL_PADDING_OFFSET'] = cellPadding - focusBorderWidth
        self._defaultStyleSheet = self.styleSheet % colours
        self.setStyleSheet(self._defaultStyleSheet)
        self.setAlternatingRowColors(True)
        self.setWordWrap(wordWrap)

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
        self.setMinimumSize(2 * height, 2 * height + self.horizontalScrollBar().height())

        # set up the menus
        self.setTableMenu()
        self.setHeaderMenu()

        self._tableBlockingLevel = 0

        # initialise the table
        self.updateDf(df, _resize, setHeightToRows, setWidthToColumns, setOnHeaderOnly=setOnHeaderOnly)

        # set selection/action callbacks
        self.doubleClicked.connect(self._actionConnect)

        if selectionCallback is not NOTHING:
            self.setSelectionCallback(selectionCallback)  # can set to None
        if selectionCallbackEnabled is not NOTHING:
            self.setSelectionCallbackEnabled(selectionCallbackEnabled)
        if actionCallback is not NOTHING:
            self.setActionCallback(actionCallback)  # can be set to None
        if actionCallbackEnabled is not NOTHING:
            self.setActionCallbackEnabled(actionCallbackEnabled)

        self.setItemDelegate(_TableDelegateABC())

    def updateDf(self, df, resize=True, setHeightToRows=False, setWidthToColumns=False, setOnHeaderOnly=False, newModel=False):
        """Initialise the dataFrame
        """
        if not isinstance(df, (type(None), pd.DataFrame)):
            raise ValueError(f'data is not of type pd.DataFrame - {type(df)}')

        if df is not None and (setOnHeaderOnly or not df.empty):
            # set the model
            if newModel or not (model := self.model()):
                # create a new model if required
                model = self.defaultTableModel(df, view=self)
                self.setModel(model)
            else:
                model.df = df

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
            df = pd.DataFrame({})
            if newModel or not (model := self.model()):
                # create a new model if required
                model = self.defaultTableModel(df, view=self)
                self.setModel(model)
            else:
                model.df = df

        return model

    def setModel(self, model: QtCore.QAbstractItemModel) -> None:
        """Set the model for the view
        """
        super().setModel(model)

        # attach a handler for updating the selection on sorting
        model.layoutAboutToBeChanged.connect(self._preChangeSelectionOrderCallback)
        model.layoutChanged.connect(self._postChangeSelectionOrderCallback)

        # set selection callback because the model has changed?
        self.selectionModel().selectionChanged.connect(self._selectionConnect)
        model._defaultEditable = self._defaultEditable

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
        except Exception:
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
        _header.setStretchLastSection(False)
        # only look at visible section
        _header.setResizeContentsPrecision(5)
        _header.setDefaultAlignment(QtCore.Qt.AlignLeft)
        _header.setFixedWidth(10)  # gives enough of a handle to resize if required
        _header.setVisible(showVerticalHeader)
        _header.setHighlightSections(self.font().bold())

        setWidgetFont(_header, name=TABLEFONT)
        if self._rowHeightScale:
            _header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
            _height *= self._rowHeightScale
        else:
            _header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)

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
            if rows := {model._oldSortIndex[itm.row()] for itm in selection if itm.row() in model._oldSortIndex}:
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

    def isEditable(self):
        """Return True if the default state of the table is editable
        """
        return self._defaultEditable

    def setEditable(self, value):
        """Set the default editable state of the table.
        Individual columns can be set in the columns-settings.
        """
        if not isinstance(value, bool):
            raise ValueError(f'{self.__class__.__name__}.setEditable: value is not True|False')

        self._defaultEditable = value
        if self.model():
            # keep the model in-sync with the view
            self.model()._defaultEditable = value

    #=========================================================================================
    # Selection callbacks
    #=========================================================================================

    def setSelectionCallback(self, selectionCallback):
        """Set the selection-callback for the table.
        """
        # update callbacks - overwrite method
        if not (selectionCallback is None or callable(selectionCallback)):
            raise ValueError(f'{self.__class__.__name__}.setSelectionCallback: selectionCallback is not None|callable')

        self._selectionCallback = selectionCallback

    def resetSelectionCallback(self):
        """Reset the selection-callback for the table back to the class-method.
        """
        self._selectionCallback = NOTHING

    def selectionCallbackEnabled(self):
        """Return True if selection-callback is enabled.
        """
        return self._enableSelectionCallback

    def setSelectionCallbackEnabled(self, value):
        """Enable/disable the selection-callback
        """
        if not isinstance(value, bool):
            raise ValueError(f'{self.__class__.__name__}.setSelectionCallbackEnabled: value is not True|False')

        self._enableSelectionCallback = value

    def _selectionConnect(self, selected, deselected):
        """Handle the callback for a selection
        """
        if self._enableSelectionCallback and self._selectionCallback is not None:
            # get the unique df-rows from the selections
            newRows = OrderedSet([(dd := idx.data(INDEX_ROLE)) is not None and dd[0] for sel in selected for idx in sel.indexes()]) - {False}
            oldRows = OrderedSet([(dd := idx.data(INDEX_ROLE)) is not None and dd[0] for sel in deselected for idx in sel.indexes()]) - {False}
            sRows = OrderedSet([(dd := idx.data(INDEX_ROLE)) is not None and dd[0] for idx in self.selectedIndexes()]) - {False}

            df = self._df
            new = df.iloc[list(newRows)]
            old = df.iloc[list(oldRows)]
            sel = df.iloc[list(sRows)]
            try:
                last = df.iloc[[self.currentIndex().data(INDEX_ROLE)[0]]]
            except Exception:
                last = []

            with self._blockTableSignals('_selectionCallback', blanking=False, disableScroll=True):
                if self._selectionCallback is NOTHING:
                    # pass the dfs to the class-method callback
                    self.selectionCallback(new, old, sel, last)
                else:
                    self._selectionCallback(new, old, sel, last)

    #=========================================================================================
    # Action callbacks
    #=========================================================================================

    def setActionCallback(self, actionCallback):
        """Set the action-callback for the table.
        """
        # update callbacks - overwrite method
        if not (actionCallback is None or callable(actionCallback)):
            raise ValueError(f'{self.__class__.__name__}.setActionCallback: actionCallback is not None|callable')

        self._actionCallback = actionCallback

    def resetActionCallback(self):
        """Reset the action-callback for the table back to the class-method.
        """
        self._actionCallback = NOTHING

    def actionCallbackEnabled(self):
        """Return True if action-callback is enabled.
        """
        return self._enableActionCallback

    def setActionCallbackEnabled(self, value):
        """Enable/disable the action-callback
        """
        if not isinstance(value, bool):
            raise ValueError(f'{self.__class__.__name__}.setActionCallbackEnabled: value is not True|False')

        self._enableActionCallback = value

    def _actionConnect(self, modelIndex):
        """Handle the callback for a selection
        """
        if bool(modelIndex.flags() & QtCore.Qt.ItemIsEditable):
            # item is editable so skip the action
            return
        if not self.actionCallback:
            return

        if self._enableActionCallback and self._actionCallback is not None:
            # get the df-rows from the selection
            sRows = OrderedSet([(dd := idx.data(INDEX_ROLE)) is not None and dd[0] for idx in self.selectedIndexes()]) - {False}

            df = self._df
            sel = df.iloc[list(sRows)]
            try:
                last = df.iloc[[self.currentIndex().data(INDEX_ROLE)[0]] if sRows else []]
            except Exception:
                last = []

            with self._blockTableSignals('_actionCallback', blanking=False, disableScroll=True):
                if self._actionCallback is NOTHING:
                    # pass the dfs to the class-method callback
                    self.actionCallback(sel, last)
                else:
                    self._actionCallback(sel, last)

    #=========================================================================================
    # Selection/Action methods
    #=========================================================================================

    def selectionCallback(self, selected, deselected, selection, lastItem):
        """Handle item selection has changed in table - call user callback
        :param selected: table indexes selected
        :param deselected: table indexes deselected
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}.selectionCallback not implemented')

    def actionCallback(self, selection, lastItem):
        """Handle item selection has changed in table - call user callback
        """
        # MUST BE SUBCLASSED
        raise NotImplementedError(f'Code error: {self.__class__.__name__}.actionCallback not implemented')

    def selectedRows(self):
        """
        :return: a DataFrame with selected rows
        """
        sRows = OrderedSet([(dd := idx.data(INDEX_ROLE)) is not None and dd[0] for idx in self.selectedIndexes()]) - {False}
        df = self._df
        return df.iloc[list(sRows)]

    def selectRowsByValues(self, values, headerName, scrollToSelection=True, doCallback=True):
        """
        Select rows if the given values are present in the table.
        :param values: list of value to select
        :param headerName: the column name for the column where to search the values
        :param scrollToSelection: navigate to the table to show the result
        :return: None
        For obj table use the "highlightObjects" method.
        """
        if self._df is None or self._df.empty:
            return
        if headerName not in self._df.columns:
            return
        from ccpn.core.lib.ContextManagers import nullContext

        context = nullContext if doCallback else self._blockTableSignals

        with context('selectRowsByValues'):
            selectionModel = self.selectionModel()
            model = self.model()
            selectionModel.clearSelection()
            columnTextIx = self.columnTexts.index(headerName)
            for i in model._sortIndex:
                cell = model.index(i, columnTextIx)
                if cell is None:
                    continue
                tableValue = cell.data()
                for valueToSelect in values:
                    if tableValue == valueToSelect:
                        rowIndex = model.index(i, 0)
                        if rowIndex is None:
                            continue
                        selectionModel.select(rowIndex, selectionModel.Select | selectionModel.Rows)
                        if scrollToSelection:
                            self.scrollTo(rowIndex, self.EnsureVisible)

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
        self._clickedInTable = bool(self._currentIndex)

        super().mousePressEvent(e)

    def keyPressEvent(self, event):
        """Handle keyPress events on the table
        """
        super().keyPressEvent(event)

        # key = event.key()
        # cursors = [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]
        enter = [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]
        allKeyModifers = [QtCore.Qt.ShiftModifier, QtCore.Qt.ControlModifier, QtCore.Qt.AltModifier, QtCore.Qt.MetaModifier]

        # for MacOS ControlModifier is 'cmd' and MetaModifier is 'ctrl'
        addSelectionMod = [QtCore.Qt.ControlModifier]

        key = event.key()
        if key in enter:

            # enter/return pressed - select/deselect current item
            keyMod = QtWidgets.QApplication.keyboardModifiers()

            if keyMod in addSelectionMod:
                if idx := self.currentIndex():
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
                self.project.blankNotification()

            # list to store any deferred functions until blocking has finished
            self._deferredFuncs = []

        self._tableBlockingLevel += 1

    def _unblockTableEvents(self, blanking=True, disableScroll=False, tableState=None):
        """Unblock all updates/signals/notifiers in the table.
        """
        if self._tableBlockingLevel <= 0:
            raise RuntimeError('Error: tableBlockingLevel already at 0')

        self._tableBlockingLevel -= 1

        # unblock all signals on last exit
        if self._tableBlockingLevel == 0:
            if blanking and self.project:
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
    # Other methods
    #=========================================================================================

    def rowCount(self):
        """Return the number of rows in the table
        """
        return (model := self.model()) and model.rowCount()

    def columnCount(self):
        """Return the number of columns in the table
        """
        return (model := self.model()) and model.columnCount()

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

    def setForeground(self, row, column, colour):
        """Set the foreground colour for cell at position (row, column).

        :param row: row as integer
        :param column: column as integer
        :param colour: colour compatible with QtGui.QColor
        """
        if (model := self.model()):
            model.setForeground(row, column, colour)

    def setBackground(self, row, column, colour):
        """Set the background colour for cell at position (row, column).

        :param row: row as integer
        :param column: column as integer
        :param colour: colour compatible with QtGui.QColor
        """
        if (model := self.model()):
            model.setBackground(row, column, colour)

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    def setTableMenu(self) -> Menu:
        """Set up the context menu for the main table
        """
        menu = Menu('', self, isFloatWidget=True)
        setWidgetFont(menu, )

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(partial(self._raiseTableContextMenu, menu))

        self.addTableMenuOptions(menu)

        return menu

    def addTableMenuOptions(self, menu):
        """Add options to the right-mouse menu
        """
        # self._copySelectedCellAction = menu.addAction('Copy clicked cell value', self._copySelectedCell)

        # NOTE:ED - call additional addTableMenuOptions here to add options to the table menu
        _TableCopyCell.addTableMenuOptions(self, menu)
        _TableExport.addTableMenuOptions(self, menu)
        _TableSearch.addTableMenuOptions(self, menu)
        _TableDelete.addTableMenuOptions(self, menu)

    def setTableMenuOptions(self, menu):
        """Update options in the right-mouse menu
        """
        # Subclass to add extra options
        pass

    def _raiseTableContextMenu(self, menu, pos):
        """Create a new menu and popup at cursor position
        """
        if not menu:
            raise ValueError('menu is not defined')

        # call the class setup
        self.setTableMenuOptions(menu)

        # NOTE:ED - call additional setTableMenuOptions here to update options in the table menu
        _TableCopyCell.setTableMenuOptions(self, menu)
        _TableExport.setTableMenuOptions(self, menu)
        _TableSearch.setTableMenuOptions(self, menu)
        _TableDelete.setTableMenuOptions(self, menu)

        pos = QtCore.QPoint(pos.x() + 5, pos.y())
        menu.exec_(self.mapToGlobal(pos))

    #=========================================================================================
    # Header context menu
    #=========================================================================================

    def setHeaderMenu(self) -> Menu:
        """Set up the context menu for the table header
        """
        menu = Menu('', self, isFloatWidget=True)
        setWidgetFont(menu, )

        headers = self.horizontalHeader()
        headers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        headers.customContextMenuRequested.connect(partial(self._raiseHeaderContextMenu, menu))

        self.addHeaderMenuOptions(menu)

        return menu

    def addHeaderMenuOptions(self, menu):
        """Add options to the right-mouse menu
        """
        # NOTE:ED - call additional setHeaderMenu here to add options to the header menu
        _TableHeaderColumns.addHeaderMenuOptions(self, menu)

    def setHeaderMenuOptions(self, menu):
        """Update options in the right-mouse menu
        """
        # Subclass to add extra options
        pass

    def _raiseHeaderContextMenu(self, menu, pos):
        """Raise the menu on the header
        """
        if not menu:
            raise ValueError('menu is not defined')
        if self._df is None or self._df.empty:
            return

        pos = QtCore.QPoint(pos.x() + 5, pos.y())  # move the popup a bit down; otherwise can trigger an event if the pointer is just on top the first item

        # call the class setup
        self.setHeaderMenuOptions(menu)

        # NOTE:ED - call additional setHeaderMenuOptions here to add enable/disable/hide options in the header menu
        _TableHeaderColumns.setHeaderMenuOptions(self, menu)

        if len(menu.actions()):
            menu.exec_(self.mapToGlobal(pos))

    #=========================================================================================
    # Table functions
    #=========================================================================================

    pass


#=========================================================================================
# Table testing
#=========================================================================================

def main():
    """Show the test-table
    """
    MAX_ROWS = 8

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
    rowIndex = ["AAA", "BBB", "CCC", "DDD", "EEE"]  # duplicate index

    for ii in range(MAX_ROWS):
        chrs = ''.join(chr(random.randint(65, 68)) for _ in range(5))
        rowIndex.append(chrs[:3])
        data.append([6 + ii,
                     300 + random.randint(1, MAX_ROWS),
                     random.random() * 1e6,
                     450 + random.randint(-100, 400),
                     700 + random.randint(-MAX_ROWS, MAX_ROWS),
                     150.3 + random.random() * 1e2,
                     ('bravo' + chrs[3:]) if ii % 2 else ('delta' + chrs[3:])
                     ])

    df = pd.DataFrame(data, columns=cols, index=rowIndex)

    # show the example table
    app = TestApplication()
    win = QtWidgets.QMainWindow()
    frame = QtWidgets.QFrame()
    layout = QtWidgets.QGridLayout()
    frame.setLayout(layout)

    table = TableABC(None, df=df, focusBorderWidth=1)

    # set some background colours
    cells = ((0, 0, '#80C0FF'),
             (1, 1, '#fe83cc'), (1, 2, '#fe83cc'),
             (2, 3, '#83fbcc'),
             (3, 2, '#e0ff87'), (3, 3, '#e0ff87'), (3, 4, '#e0ff87'), (3, 5, '#e0ff87'),
             (4, 2, '#e0f08a'), (4, 3, '#e0f08a'), (4, 4, '#e0f08a'), (4, 5, '#e0f08a'),
             (6, 2, '#70a04f'), (6, 6, '#70a04f'),
             (7, 1, '#eebb43'), (7, 2, '#eebb43'),
             (8, 4, '#7090ef'), (8, 5, '#7090ef'),
             (9, 0, '#30f06f'), (9, 1, '#30f06f'),
             (10, 2, '#e0d0e6'), (10, 3, '#e0d0e6'), (10, 4, '#e0d0e6'),
             (11, 2, '#e0d0e6'), (11, 3, '#e0d0e6'), (11, 4, '#e0d0e6'),
             )

    for row, col, colour in cells:
        if 0 <= row < table.rowCount() and 0 <= col < table.columnCount():
            table.setBackground(row, col, colour)

    win.setCentralWidget(frame)
    frame.layout().addWidget(table, 0, 0)

    win.setWindowTitle(f'Testing {table.__class__.__name__}')
    win.show()

    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
