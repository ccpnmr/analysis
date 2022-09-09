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
__date__ = "$Date: 2022-09-08 17:13:11 +0100 (Thu, September 08, 2022) $"
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
from ccpn.ui.gui.widgets.table.TableABC import TableABC
from ccpn.ui._implementation.QueueHandler import QueueHandler
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger
from ccpn.util.Common import copyToClipboard
from ccpn.util.OrderedSet import OrderedSet


#=========================================================================================
# _ProjectTableABC project specific
#=========================================================================================

# define a simple class that can contain a simple id
blankId = SimpleNamespace(className='notDefined', serial=0)

OBJECT_CLASS = 0
OBJECT_PARENT = 1
MODULEIDS = {}


# simple class to store the blocking state of the table
@dataclass
class _BlockingContent:
    modelBlocker = None
    rootBlocker = None




class _ProjectTableABC(TableABC):
    _tableSelectionChanged = QtCore.pyqtSignal(list)

    className = '_ProjectTableABC'
    attributeName = '_ProjectTableABC'

    _OBJECT = '_object'
    _ISDELETED = 'isDeleted'
    # _internalColumns = []

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
    _logQueue = False

    def __init__(self, parent=None, mainWindow=None, moduleParent=None,
                 actionCallback=None, selectionCallback=None, checkBoxCallback=None,
                 enableMouseMoveEvent=True,
                 allowRowDragAndDrop=False,
                 hiddenColumns=None,
                 multiSelect=False, selectRows=True, numberRows=False, autoResize=False,
                 enableExport=True, enableDelete=True, enableSearch=True,
                 hideIndex=True, stretchLastSection=True,
                 showHorizontalHeader=True, showVerticalHeader=False,
                 enableDoubleClick=True,
                 **kwds):
        """Initialise the widgets for the module.
        """
        # required before initialising
        self._enableExport = enableExport
        self._enableDelete = enableDelete
        self._enableSearch = enableSearch

        super().__init__(parent=parent,
                         multiSelect=multiSelect, selectRows=selectRows,
                         showHorizontalHeader=showHorizontalHeader, showVerticalHeader=showVerticalHeader,
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

        self._rightClickedTableIndex = None  # last selected item in a table before raising the context menu. Enabled with mousePress event filter

        self._enableDoubleClick = enableDoubleClick
        if enableDoubleClick:
            self.doubleClicked.connect(self._doubleClickCallback)

        # notifier queue handling
        self._queueHandler = QueueHandler(self,
                                          completeCallback=self.update,
                                          queueFullCallback=self.queueFull,
                                          name=f'PandasTableNotifierHandler-{self}',
                                          maximumQueueLength=self._maximumQueueLength,
                                          log=self._logQueue)

        if self.enableEditDelegate:
            # set the delegate for editing
            delegate = _SimpleTableDelegate(self, objectColumn=self.OBJECTCOLUMN)
            self.setItemDelegate(delegate)

    def setModel(self, model: QtCore.QAbstractItemModel) -> None:
        """Set the model for the view
        """
        super().setModel(model)

        # # attach a handler to respond to the selection changing
        # self.selectionModel().selectionChanged.connect(self._selectionChangedCallback)
        model.showEditIcon = True

    # @property
    # def _df(self):
    #     """Return the Pandas-dataFrame holding the data
    #     """
    #     return self.model().df
    #
    # @_df.setter
    # def _df(self, value):
    #     self.model().df = value

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
            try:
                row = self._rightClickedTableIndex.row()
                return self._df.iloc[self.model()._sortIndex[row]]
            except:
                return None

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

    # @staticmethod
    # def pressingModifiers(self):
    #     """Is the user clicking while holding a modifier
    #     """
    #     allKeyModifers = [QtCore.Qt.ShiftModifier, QtCore.Qt.ControlModifier, QtCore.Qt.AltModifier, QtCore.Qt.MetaModifier]
    #     keyMod = QtWidgets.QApplication.keyboardModifiers()
    #
    #     return keyMod in allKeyModifers

    # def keyPressEvent(self, event):
    #     """Handle keyPress events on the table
    #     """
    #     super().keyPressEvent(event)
    #
    #     cursors = [QtCore.Qt.Key_Up, QtCore.Qt.Key_Down, QtCore.Qt.Key_Left, QtCore.Qt.Key_Right]
    #     enter = [QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return]
    #     allKeyModifers = [QtCore.Qt.ShiftModifier, QtCore.Qt.ControlModifier, QtCore.Qt.AltModifier, QtCore.Qt.MetaModifier]
    #
    #     # for MacOS ControlModifier is 'cmd' and MetaModifier is 'ctrl'
    #     addSelectionMod = [QtCore.Qt.ControlModifier]
    #
    #     key = event.key()
    #     if key in enter:
    #
    #         # enter/return pressed - select/deselect current item
    #         keyMod = QtWidgets.QApplication.keyboardModifiers()
    #
    #         if keyMod in addSelectionMod:
    #             idx = self.currentIndex()
    #             if idx:
    #                 # set the item, which toggles selection of the row
    #                 self.setCurrentIndex(idx)
    #
    #         elif keyMod not in allKeyModifers and self._enableDoubleClick:
    #             # fire the action callback (double-click on selected)
    #             self._doubleClickCallback(self.currentIndex())
    #
    #     # elif key == QtCore.Qt.Key_Escape:
    #     #     print(f' escape pressed')

    #=========================================================================================
    # Table context menu
    #=========================================================================================

    # def setTableMenu(self):
    #     """Set up the context menu for the main table
    #     """
    #     self.tableMenu = Menu('', self, isFloatWidget=True)
    #     setWidgetFont(self.tableMenu, )
    #     self.tableMenu.addAction('Copy clicked cell value', self._copySelectedCell)
    #
    #     if self._enableExport:
    #         self.tableMenu.addAction('Export Visible Table', partial(self.exportTableDialog, exportAll=False))
    #         self.tableMenu.addAction('Export All Columns', partial(self.exportTableDialog, exportAll=True))
    #
    #     self.tableMenu.addSeparator()
    #
    #     if self._enableDelete:
    #         self.tableMenu.addAction('Delete Selection', self.deleteObjFromTable)
    #
    #     self.tableMenu.addAction('Clear Selection', self._clearSelectionCallback)
    #
    #     self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    #     self.customContextMenuRequested.connect(self._raiseTableContextMenu)
    #
    # def _raiseTableContextMenu(self, pos):
    #     """Create a new menu and popup at cursor position
    #     """
    #     pos = QtCore.QPoint(pos.x() + 10, pos.y() + 10)
    #     self.tableMenu.exec_(self.mapToGlobal(pos))

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

    #=========================================================================================
    # Exporters
    #=========================================================================================

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

    # def _rawDataToDF(self):
    #     try:
    #         # TODO:ED - check _rawData
    #         df = pd.DataFrame(self._rawData)
    #         return df
    #     except:
    #         return pd.DataFrame()

    def exportTableDialog(self, exportAll=True):
        """export the contents of the table to a file
        The actual data values are exported, not the visible items which may be rounded due to the table settings

        :param exportAll: True/False - True implies export whole table - but in visible order
                                    False, export only the visible table
        """
        model = self.model()
        df = model.df
        rows, cols = model.rowCount(), model.columnCount()

        if df is None or df.empty:
            MessageDialog.showWarning('Export Table to File', 'Table does not contain a dataFrame')

        else:
            rowList = [model._sortIndex[row] for row in range(rows)]
            if exportAll:
                colList = self._dataFrameObject.userHeadings
            else:
                colList = self._dataFrameObject.visibleColumnHeadings

            self._exportTableDialog(df, rowList=rowList, colList=colList)

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

    def deleteSelectionFromTable(self):
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

    # def _setHeaderContextMenu(self):
    #     """Set up the context menu for the table header
    #     """
    #     headers = self.horizontalHeader()
    #     headers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
    #     headers.customContextMenuRequested.connect(self._raiseHeaderContextMenu)
    #
    # def _raiseHeaderContextMenu(self, pos):
    #     """Raise the menu on the header
    #     """
    #     if self._df is None or self._df.empty:
    #         return
    #
    #     self.initSearchWidget()
    #     pos = QtCore.QPoint(pos.x(), pos.y() + 10)  #move the popup a bit down. Otherwise can trigger an event if the pointer is just on top the first item
    #
    #     self.headerContextMenumenu = QtWidgets.QMenu()
    #     setWidgetFont(self.headerContextMenumenu, )
    #     columnsSettings = self.headerContextMenumenu.addAction("Column Settings...")
    #     searchSettings = None
    #     if self._enableSearch and self.searchWidget is not None:
    #         searchSettings = self.headerContextMenumenu.addAction("Filter...")
    #     action = self.headerContextMenumenu.exec_(self.mapToGlobal(pos))
    #
    #     if action == columnsSettings:
    #         settingsPopup = ColumnViewSettingsPopup(parent=self._parent, table=self,
    #                                                 dataFrameObject=self._df,
    #                                                 hiddenColumns=self.getHiddenColumns(),
    #                                                 )
    #         hiddenColumns = settingsPopup.getHiddenColumns()
    #         self.setHiddenColumns(texts=hiddenColumns, update=False)
    #         settingsPopup.raise_()
    #         settingsPopup.exec_()  # exclusive control to the menu and return _hiddencolumns
    #
    #     if action == searchSettings:
    #         self.showSearchSettings()

    #=========================================================================================
    # Search methods
    #=========================================================================================

    # def initSearchWidget(self):
    #     if self._enableSearch and self.searchWidget is None:
    #         if not attachDFSearchWidget(self._parent, self):
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
        # import here to stop circular import
        from ccpn.ui.gui.lib.MenuActions import _openItemObject

        objs = [self.project.getByPid(pid) for pid in pids]

        selectableObjects = [obj for obj in objs if isinstance(obj, objType)]
        others = [obj for obj in objs if not isinstance(obj, objType)]
        if len(selectableObjects) > 0:
            _openItemObject(self.mainWindow, selectableObjects[1:])
            pulldown.select(selectableObjects[0].pid)

        else:
            othersClassNames = list(set([obj.className for obj in others if hasattr(obj, 'className')]))
            if len(othersClassNames) > 0:
                if len(othersClassNames) == 1:
                    title, msg = 'Dropped wrong item.', 'Do you want to open the %s in a new module?' % ''.join(othersClassNames)
                else:
                    title, msg = 'Dropped wrong items.', 'Do you want to open items in new modules?'
                openNew = MessageDialog.showYesNo(title, msg)
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
            self._defaultDf = self._df.copy()  # make a copy for the search-widget

            self.resizeColumnsToContents()

            # re-sort the table
            if oldModel and (0 <= sortColumn < model.columnCount()) and self.isSortingEnabled():
                model._sortColumn = sortColumn
                model._sortOrder = sortOrder
                self.sortByColumn(sortColumn, sortOrder)

            self.showColumns(None)
            self._highLightObjs(objs)

            # set the tipTexts
            if self._columnDefs is not None:
                model.setToolTips('horizontal', self._columnDefs.tipTexts)

        except Exception as es:
            getLogger().warning('Error populating table', str(es))
            self.populateEmptyTable()
            if self.application and self.application._isInDebugMode:
                raise

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
        self._defaultDf = self._df.copy()  # make a copy for the search-widget

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
        self._queueHandler.queueAppend([func, data])

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
                    minInd = model.index(min(rows), 0)
                    for row in rows:
                        rowIndex = model.index(row, 0)
                        selectionModel.select(rowIndex, selectionModel.Select | selectionModel.Rows)

                    if scrollToSelection and not self._scrollOverride and minInd is not None:
                        self.scrollTo(minInd, self.EnsureVisible)

    def highlightObjects(self, objectList, scrollToSelection=True):
        """Highlight a list of objects in the table
        """
        objs = []

        if objectList:
            # get the list of objects, exclude deleted
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
        raise NotImplementedError(f'Code error: {self.__class__.__name__}.queueFull not implemented')

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
