"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-05-20 17:00:33 +0100 (Wed, May 20, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtCore, QtWidgets
import pandas as pd
import os
from pyqtgraph import TableWidget
from pyqtgraph.widgets.TableWidget import _defersort, TableWidgetItem
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.DataFrameObject import DataFrameObject, DATAFRAME_OBJECT, \
    DATAFRAME_INDEX, DATAFRAME_HASH, DATAFRAME_PID

from ccpn.ui.gui.guiSettings import getColours, BORDERNOFOCUS_COLOUR
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.FileDialog import FileDialog, USERTABLESPATH
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.ColumnViewSettings import ColumnViewSettingsPopup
from ccpn.ui.gui.widgets.SearchWidget import attachSearchWidget
from ccpn.core.lib.Notifiers import Notifier
from ccpn.util.Common import makeIterableList
from functools import partial
from ccpn.util.OrderedSet import OrderedSet
from collections import OrderedDict
from ccpn.util.Logging import getLogger
from types import SimpleNamespace
from contextlib import contextmanager
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.core.lib.Util import getParentObjectFromPid
from ccpn.core.lib.ContextManagers import catchExceptions
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showMessage


# BG_COLOR = QtGui.QColor('#E0E0E0')
# TODO:ED add some documentation here

OBJECT_CLASS = 0
OBJECT_PARENT = 1


def __ltForTableWidgetItem__(self, other):
    # new routine to overload TableWidgetItem that crashes when sorting None
    if self.sortMode == 'index' and hasattr(other, 'index'):
        return self.index < other.index
    if self.sortMode == 'value' and hasattr(other, 'value'):
        return (universalSortKey(self.value) < universalSortKey(other.value))
    else:
        if self.text() and other.text():
            return (universalSortKey(self.text()) < universalSortKey(other.text()))
        else:
            return False


def __sortByColumn__(self, col, newOrder):
    try:
        # QtWidgets.QTableWidget.sortByColumn(self, col, newOrder)
        super(QtWidgets.QTableWidget, self).sortByColumn(col, newOrder)
    except Exception as es:
        pass
        # print(str(es))


# define a simple class that can contains a simple id
blankId = SimpleNamespace(className='notDefined', serial=0)

MODULEIDS = {}


def _moduleId(module):
    return MODULEIDS[id(module)] if id(module) in MODULEIDS else -1


# Exporters

def dataFrameToExcel(dataFrame, path, sheet_name='Table', columns=None):
    if dataFrame is not None:

        if columns is not None and isinstance(columns, list):  #this is wrong. columns can be a 1d array
            dataFrame.to_excel(path, sheet_name=sheet_name, columns=columns)
        else:
            dataFrame.to_excel(path, sheet_name=sheet_name)


def dataFrameToCsv(dataFrame, path, *args):
    dataFrame.to_csv(path)


def dataFrameToTsv(dataFrame, path, *args):
    dataFrame.to_csv(path, sep='\t')


def dataFrameToJson(dataFrame, path, *args):
    dataFrame.to_json(path, orient='split', default_handler=str)


def findExportFormats(path, dataFrame, sheet_name='Table', filterType=None, columns=None):
    formatTypes = OrderedDict([
        ('.xlsx', dataFrameToExcel),
        ('.csv', dataFrameToCsv),
        ('.tsv', dataFrameToTsv),
        ('.json', dataFrameToJson)
        ])

    extension = os.path.splitext(path)[1]
    if extension in formatTypes.keys():
        formatTypes[extension](dataFrame, path, sheet_name, columns)
        return
    else:
        try:
            findExportFormats(str(path) + filterType, sheet_name)
        except:
            getLogger().warning('Format file not supported')


def exportTableDialog(dataFrame, columns=None, path='~/table.xlsx'):
    """Open the ExportDialog to export any dataFrame to different formats """
    if dataFrame is None:
        return

    from ccpn.util.Path import aPath

    path = aPath(path)

    saveDialog = FileDialog(selectFile=str(path),  # default saving name    #directory=str(path.parent),
                            fileMode=FileDialog.AnyFile,
                            filter=".xlsx;; .csv;; .tsv;; .json ",
                            text='Save as ',
                            acceptMode=FileDialog.AcceptSave,
                            preferences=None,
                            initialPath=path,
                            pathID=USERTABLESPATH)
    saveDialog._show()
    path = saveDialog.selectedFile()
    filterType = saveDialog.selectedNameFilter()
    if path:
        findExportFormats(path, dataFrame, filterType=filterType, columns=columns)


class GuiTable(TableWidget, Base):
    # selectionUserChanged = QtCore.pyqtSignal(QtCore.QItemSelection)

    ICON_FILE = os.path.join(os.path.dirname(__file__), 'icons', 'editable.png')

    styleSheet = """
GuiTable {
    background-color: %(GUITABLE_BACKGROUND)s;
    alternate-background-color: %(GUITABLE_ALT_BACKGROUND)s;
    border: 1px solid #a9a9a9;
    border-radius: 2px;
}

GuiTable::item {
    padding: 2px;
    color: %(GUITABLE_ITEM_FOREGROUND)s;
}

GuiTable::item::selected {
    background-color: %(GUITABLE_SELECTED_BACKGROUND)s;
    color: %(GUITABLE_SELECTED_FOREGROUND)s;
}"""

    def __init__(self, parent=None,
                 mainWindow=None,
                 dataFrameObject=None,  # collate into a single object that can be changed quickly
                 actionCallback=None, selectionCallback=None, checkBoxCallback=None,
                 _pulldownKwds=None, enableMouseMoveEvent = True,
                 multiSelect=False, selectRows=True, numberRows=False, autoResize=False,
                 enableExport=True, enableDelete=True, enableSearch=True,
                 hideIndex=True, stretchLastSection=True, _applyPostSort=True,
                 **kwds):
        """
        Create a new instance of a TableWidget with an attached Pandas dataFrame
        :param parent:
        :param mainWindow:
        :param dataFrameObject:
        :param actionCallback:
        :param selectionCallback:
        :param multiSelect:
        :param selectRows:
        :param numberRows:
        :param autoResize:
        :param enableExport:
        :param enableDelete:
        :param hideIndex:
        :param kwds:
        """
        super().__init__(parent)
        Base._init(self, **kwds)

        self._parent = parent

        # set the application specfic links
        self.mainWindow = mainWindow
        self.application = None
        self.project = None
        self.current = None

        if self.mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        self.moduleParent = None

        # initialise the internal data storage
        self._dataFrameObject = dataFrameObject
        self._tableBlockingLevel = 0

        # set stylesheet
        self.colours = getColours()
        styleSheet = self.styleSheet % self.colours
        self.setStyleSheet(styleSheet)
        self.setAlternatingRowColors(True)

        # set the preferred scrolling behaviour
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setVerticalScrollMode(self.ScrollPerItem)

        # define the multiselection behaviour
        self.multiSelect = multiSelect
        if multiSelect:
            self.setSelectionMode(self.ExtendedSelection)
        else:
            self.setSelectionMode(self.SingleSelection)

        # define the set selection behaviour
        self.selectRows = selectRows
        if selectRows:
            self.setSelectionBehavior(self.SelectRows)
        else:
            self.setSelectionBehavior(self.SelectItems)

        self._checkBoxCallback = checkBoxCallback
        # set all the elements to the same size
        self._pulldownKwds = _pulldownKwds or {}
        self.hideIndex = hideIndex
        self._setDefaultRowHeight()

        # enable sorting and sort on the first column
        self.setSortingEnabled(True)
        self.sortByColumn(0, QtCore.Qt.AscendingOrder)

        # enable drag and drop operations on the table - why not working?
        self.setDragEnabled(True)
        self.acceptDrops()
        self.setDragDropMode(self.InternalMove)
        self.setDropIndicatorShown(True)

        # set Interactive and last column to expanding
        self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Interactive)
        self.horizontalHeader().setStretchLastSection(stretchLastSection)
        self.horizontalHeader().setResizeContentsPrecision(0)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)

        # enable the right click menu
        self.searchWidget = None
        self._setHeaderContextMenu()
        self._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)
        self._enableSearch = enableSearch

        # populate if a dataFrame has been passed in
        if dataFrameObject:
            self.setTableFromDataFrame(dataFrameObject.dataFrame)

        # enable callbacks
        self.enableMouseMoveEvent = enableMouseMoveEvent #this will fire callbacks
        self._actionCallback = actionCallback
        self._selectionCallback = selectionCallback
        self._lastSelection = None
        #self._silenceCallback = False

        if self._actionCallback:
            self.doubleClicked.connect(self._doubleClickCallback)
        else:
            self.doubleClicked.connect(self._defaultDoubleClick)

        # set the delegate for editing
        delegate = GuiTableDelegate(self)
        self.setItemDelegate(delegate)

        # set the callback for changing selection on table
        # model = self.selectionModel()

        # try:
        #     self._superFunc = None
        #
        #     def _selectionModelSelect(*args, **kwds):
        #         print ('>>>>>>>>>', id(self), self._selectOverride, self._mousePressed,
        #                self._lastClick, self.isEnabled())
        #         if self._superFunc:
        #             self._superFunc(*args, **kwds)
        #
        #     self._superFunc = self.selectionModel().select
        #     self.selectionModel().select = _selectionModelSelect
        # except Exception as es:
        #     print(str(es))
        #
        # self.setEnabled(False)
        # need manual selection changed
        # model.selectionChanged.connect(self._selectionTableCallback)

        # model.selectionChanged.connect(self._selectionChangedCallback)
        # self.selectionUserChanged.connect(self._selectionTableCallback)

        # testing other methods - just need to disable selection callbacks during double click period
        # model.currentChanged.connect(self._selectionTableCallback)
        # self.clicked.connect(self._selectionTableCallback)

        # self.horizontalHeader().sortIndicatorChanged.connect(self._sortChanged)
        # self.horizontalHeader().sectionPressed.connect(self._preSort)

        # self.setFormat('%0.3f')

        if _applyPostSort:
            self.horizontalHeader().sectionClicked.connect(self._postSort)
        else:
            self.horizontalHeader().sectionClicked.connect(self._postDefaultSort)

        # set internal flags
        self._mousePressedPos = None
        self._userKeyPressed = False
        self._selectOverride = False
        self._scrollOverride = False

        self._lastClick = None
        self._tableData = {}
        self._rawData = None  # this is set when called setData()
        self._tableNotifier = None
        self._rowNotifier = None
        self._cellNotifiers = []
        self._selectCurrentNotifier = None
        self._searchNotifier = None
        self._droppedNotifier = None
        self._icons = [self.ICON_FILE]
        self._stretchLastSection = stretchLastSection
        self._defaultHeadings = []
        self._defaultHiddenColumns = []

        # set the minimum size the table can collapse to
        self.setMinimumSize(30, 30)
        self.searchWidget = None
        # self._parent.layout().setVerticalSpacing(0)

        self.setDefaultTableData()

        self._currentSorted = False
        self._newSorted = False

        # update method for ccpn sorting
        TableWidgetItem.__lt__ = __ltForTableWidgetItem__

    def _initTableCommonWidgets(self, parent, height=35, setGuiNotifier=None, **kwds):
        """Initialise the common table elements
        """
        # strange, need to do this when using scrollArea, but not a Widget
        parent.getLayout().setHorizontalSpacing(0)

        self._widget = ScrollableFrame(parent=parent, scrollBarPolicies=('never', 'never'), **kwds)
        self._widgetScrollArea = self._widget._scrollArea
        self._widgetScrollArea.setStyleSheet('''
                    margin-left : 2px;
                    margin-right : 2px;''')

        self._widgetScrollArea.setFixedHeight(height)  # needed for the correct sizing of the table

    def _postInitTableCommonWidgets(self):
        from ccpn.ui.gui.widgets.DropBase import DropBase
        from ccpn.ui.gui.lib.GuiNotifier import GuiNotifier
        from ccpn.ui.gui.widgets.ScrollBarVisibilityWatcher import ScrollBarVisibilityWatcher

        # add a dropped notifier to all tables
        self.droppedNotifier = GuiNotifier(self,
                                           [GuiNotifier.DROPEVENT], [DropBase.PIDS],
                                           self._processDroppedItems)

        # add a widget handler to give a clean corner widget for the scroll area
        self._cornerDisplay = ScrollBarVisibilityWatcher(self)

        # self.setStyleSheet('''
        #             NmrResidueTable {border-left-width: 1px solid  #a9a9a9;
        #             border-right-width: 1px solid  #a9a9a9;
        #             border-bottom-width: 1px solid  #a9a9a9;
        #             border-bottom-right-radius: 2px;
        #             border-bottom-left-radius: 2px;}
        #             ''')

    def _blockTableEvents(self, blanking=True, _disableScroll=False):
        """Block all updates/signals/notifiers in the table.
        """
        # block on first entry
        if self._tableBlockingLevel == 0:
            if _disableScroll:
                self._scrollOverride = True
            # self.setEnabled(False)
            self.blockSignals(True)
            self.selectionModel().blockSignals(True)
            self.setUpdatesEnabled(False)
            if blanking and self.project:
                if self.project:
                    self.project.blankNotification()

        self._tableBlockingLevel += 1

    def _unblockTableEvents(self, blanking=True, _disableScroll=False):
        """Unblock all updates/signals/notifiers in the table.
        """
        if self._tableBlockingLevel > 0:
            self._tableBlockingLevel -= 1

            # unblock all signals on last exit
            if self._tableBlockingLevel == 0:
                if blanking and self.project:
                    if self.project:
                        self.project.unblankNotification()
                self.setUpdatesEnabled(True)
                self.selectionModel().blockSignals(False)
                self.blockSignals(False)
                # self.setEnabled(True)

                if _disableScroll:
                    self._scrollOverride = False
        else:
            raise RuntimeError('Error: tableBlockingLevel already at 0')

    @contextmanager
    def _tableBlockSignals(self, callerId='', blanking=True, _disableScroll=False):
        """Block all signals from the table
        """
        self._blockTableEvents(blanking, _disableScroll=_disableScroll)
        try:
            yield  # yield control to the calling process

        except Exception as es:
            raise es
        finally:
            self._unblockTableEvents(blanking, _disableScroll=_disableScroll)

    def _preSort(self, *args):
        """
        catch the press event on a header
        """
        # header = self.horizontalHeader()
        # print ([header.columnSpan(0, col) for col in range(header.count())])
        pass

    def _postSort(self, *args):
        """Catch the click event on a header and ensure headers remain consistent
        """
        with self._tableBlockSignals('_postSort'):
            # keep highlighted objects
            if self._dataFrameObject:
                objs = self.getSelectedObjects()
                with self._guiTableUpdate(self._dataFrameObject):
                    # context manager performs the necessary operations to keep headers consistent - empty dataFrameObject is handled there
                    pass

                self._highLightObjs(objs)

    def _postDefaultSort(self, *args):
        """Catch the click event on a header and ensure headers remain consistent
        """
        self.horizontalHeader().setStretchLastSection(True)
        self.resizeColumnsToContents()

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
        CCPN-INTERNAL: Insert a comment into GuiTable
        """
        # ejb - why is it blanking a notification here?
        # NmrResidueTable._project.blankNotification()
        obj.comment = value if value else None
        # NmrResidueTable._project.unblankNotification()

    def _sortChanged(self, col, sortOrder: QtCore.Qt.SortOrder):
        # sort the _dataFrame to match
        # need to read the sorted state when repopulating table
        # this is also called when the table is populated from the pulldown :)
        return

        # rows = list(range(self.rowCount()))
        # columns = list(range(self.columnCount()))
        # headings = []
        # for c in columns:
        #     hi = self.horizontalHeaderItem(c)
        #     if hi:
        #         headings.append(self.horizontalHeaderItem(c).text())
        #     else:
        #         headings.append('*')
        #
        # # print(headings)
        # if DATAFRAME_PID in headings:
        #     pidCol = headings.index(DATAFRAME_PID)
        #     pids = []
        #     for r in rows:
        #         pids.append(self.item(r, pidCol).value)
        #     # print(pids)
        #
        # self._newSorted = True

    def setActionCallback(self, actionCallback):
        # enable callbacks
        self._actionCallback = actionCallback
        if self._actionCallback:
            self.doubleClicked.connect(self._doubleClickCallback)
        else:
            self.doubleClicked.connect(self._defaultDoubleClick)

    def setSelectionCallback(self, selectionCallback):
        # enable callbacks
        self._selectionCallback = selectionCallback

    def _handleDroppedItems(self, pids, objType, pulldown):
        """
        :param pids: the selected objects pids
        :param objType: the instance of the obj to handle. Eg. PeakList
        :param pulldown: the pulldown of the module wich updates the table
        :return: Actions: Select the dropped item on the table or/and open a new modules if multiple drops.
        If multiple different obj instances, then asks first.
        """
        from ccpn.ui.gui.lib.MenuActions import _openItemObject

        objs = [self.project.getByPid(pid) for pid in pids]

        selectableObjects = [obj for obj in objs if isinstance(obj, objType)]
        others = [obj for obj in objs if not isinstance(obj, objType)]
        if len(selectableObjects) > 0:
            pulldown.select(selectableObjects[0].pid)
            _openItemObject(self.mainWindow, selectableObjects[1:])

        else:
            from ccpn.ui.gui.widgets.MessageDialog import showYesNo

            othersClassNames = list(set([obj.className for obj in others]))
            if len(othersClassNames) > 0:
                if len(othersClassNames) == 1:
                    title, msg = 'Dropped wrong item.', 'Do you want to open the %s in a new module?' % ''.join(othersClassNames)
                else:
                    title, msg = 'Dropped wrong items.', 'Do you want to open items in new modules?'
                openNew = showYesNo(title, msg)
                if openNew:
                    _openItemObject(self.mainWindow, others)

    def _checkBoxCallback(self, data):
        getLogger().info('>>> %s _checkBoxCallback' % _moduleId(self.moduleParent))

        pass

    def _defaultDoubleClick(self, itemSelection):

        self._lastClick = 'doubleClick'
        model = self.selectionModel()

        # selects all the items in the row
        selection = model.selectedIndexes()

        if selection:
            row = itemSelection.row()
            col = itemSelection.column()
            if self._dataFrameObject:
                if self._dataFrameObject.columnDefinitions.setEditValues[col]:  # ejb - editable fields don't actionCallback:

                    item = self.item(row, col)
                    item.setEditable(True)
                    # self.itemDelegate().closeEditor.connect(partial(self._changeMe, row, col))
                    # item.textChanged.connect(partial(self._changeMe, item))
                    # self.editItem(item)

    def _doubleClickCallback(self, itemSelection):

        # if not a _dataFrameObject is a normal guiTable.
        if not self._dataFrameObject:
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
                self._actionCallback(data)
            return

        self._lastClick = 'doubleClick'
        with self._tableBlockSignals('_doubleClickCallback', blanking=False, _disableScroll=True):

            item = self.currentItem()

            # get the current selected objects from the table - objects now persistent after single-click
            objList = []
            if self._lastSelection is not None:
                objList = self._lastSelection['selection']
            # objList = self.getSelectedObjects()

            if item:
                row = item.row()
                col = item.column()

                # get the row data corresponding to the row clicked
                model = self.selectionModel()
                selection = [iSelect for iSelect in model.selectedIndexes() if iSelect.row() == row]
                obj = self.getSelectedObjects(selection)
                obj = obj[0] if obj else None

                # if objList:
                #     # return the highlight to the previous selection
                #     self._highLightObjs(objList)

                if obj and objList:
                    # store the data for the clicked row
                    data = {}
                    for cc in range(self.columnCount()):
                        colName = self.horizontalHeaderItem(cc).text()
                        data[colName] = self.item(row, cc).value

                    objIndex = item.index
                    data = CallBack(theObject=self._dataFrameObject,
                                    object=objList if self.multiSelect else obj,  # single object or multi-selection
                                    index=objIndex,
                                    targetName=obj.className,
                                    trigger=CallBack.DOUBLECLICK,
                                    row=row,
                                    col=col,
                                    rowItem=data,
                                    rowObject=obj)

                    if self._actionCallback and self._dataFrameObject and not \
                            self._dataFrameObject.columnDefinitions.setEditValues[col]:  # ejb - editable fields don't actionCallback
                        self._actionCallback(data)

                    elif self._dataFrameObject and self._dataFrameObject.columnDefinitions.setEditValues[col]:  # ejb - editable fields don't actionCallback:
                        # item = self.item(row, col)
                        # item.setEditable(True)
                        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable)
                        # self.itemDelegate().closeEditor.connect(partial(self._changeMe, row, col))
                        # item.textChanged.connect(partial(self._changeMe, item))
                        # self.editItem(item)  # enter the editing mode

                        # editItem entry is handled by the delegate
                    else:
                        if self._actionCallback:
                            self._actionCallback(data)

    @_defersort
    def setRow(self, row, vals):
        if row > self.rowCount() - 1:
            self.setRowCount(row + 1)
        for col in range(len(vals)):
            val = vals[col]
            item = self.itemClass(val, row)
            item.setEditable(self.editable)
            sortMode = self.sortModes.get(col, None)
            if sortMode is not None:
                item.setSortMode(sortMode)
            format = self._formats.get(col, self._formats[None])
            item.setFormat(format)
            self.items.append(item)

            # item.setValue(val)  # Required--the text-change callback is invoked
            # when we call setItem.
            if isinstance(val, bool):  # this will create a check box if the value is a bool
                item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                state = 2 if val else 0
                item.setCheckState(state)

            if isinstance(val, list or tuple):

                pulldown = PulldownList(None, **self._pulldownKwds)
                pulldown.setMaximumWidth(300)
                pulldown.setData(*val)

                pulldown.setObjectName(str((row, col)))
                pulldown.item = item
                model = self.selectionModel()
                # selects all the items in the row
                selection = model.selectedIndexes()

                self.setCellWidget(row, col, pulldown)
                self.setItem(row, col, item)
                item.setValue('')  # values are in the pulldown. Otherwise they are inserted inside the cell as str in a long list

            else:
                self.setItem(row, col, item)
                item.setValue(val)

    def _selectionTableCallback(self, itemSelection, mouseDrag=True):
        """Handler when selection has changed on the table
        This user changed only
        """
        # getLogger().debug('>>> %s _selectionTableCallback' % _moduleId(self.moduleParent), self._tableBlockingLevel)

        # if not a _dataFrameObject is a normal guiTable.
        if not self._dataFrameObject:
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
                if self._selectionCallback:
                    self._selectionCallback(data)
            return

        # skip selection if it already exists and hasn't changed
        # BUT, annoyingly, need an extra case for a single click on an already selected item
        objList = self.getSelectedObjects()
        if objList and self._lastSelection is not None and \
                self._lastSelection['selection'] is not None and \
                set(objList) == set(self._lastSelection['selection']):
            if mouseDrag:
                return

        # update selection
        self._lastSelection = {'clicked'       : self.currentItem(),
                               'selection'     : objList,
                               'modelSelection': self.selectionModel().selectedIndexes(),
                               'selected'      : self.currentItem().isSelected() if self.currentItem() else None}

        with self._tableBlockSignals('_selectionTableCallback', blanking=False, _disableScroll=True):

            # get whether current row is defined
            item = self.currentItem()

            if item and objList and self._selectionCallback:
                data = CallBack(theObject=self._dataFrameObject,
                                object=objList,
                                index=0,
                                targetName=objList[0].className,
                                trigger=CallBack.CLICK,
                                row=0,
                                col=0,
                                rowItem=None)

                self._selectionCallback(data)

            else:
                self.clearSelection()

    def _checkBoxTableCallback(self, itemSelection):

        state = True if itemSelection.checkState() == 2 else False
        state = not state  # as to be opposite before catches the event before you clicked
        value = itemSelection.value
        # if not state == value:

        # TODO:ED check with Luca on when this should fire
        # get the row for the checkbox item
        selection = [self.model().index(itemSelection.row(), cc) for cc in range(self.columnCount())]

        obj = self.getSelectedObjects(selection)
        obj = obj[0] if obj else None

        if obj:
            data = CallBack(theObject=self._dataFrameObject,
                            object=obj,
                            index=0,
                            targetName=obj.className,
                            trigger=CallBack.CLICK,
                            row=itemSelection.row(),
                            col=itemSelection.column(),
                            rowItem=itemSelection,
                            checked=state)
            textHeader = self.horizontalHeaderItem(itemSelection.column()).text()
            if textHeader:
                self._dataFrameObject.setObjAttr(textHeader, obj, state)
                # setattr(objList[0], textHeader, state)
        else:
            data = CallBack(theObject=self._dataFrameObject,
                            object=None,
                            index=0,
                            targetName=None,
                            trigger=CallBack.CLICK,
                            row=itemSelection.row(),
                            col=itemSelection.column(),
                            rowItem=itemSelection,
                            checked=state)
        self._checkBoxCallback(data)

    def hideDefaultColumns(self):
        """If the table is empty then check visible headers against the last header hidden list
        """
        h = self.horizontalHeader()
        for ii in range(h.count()):
            headerItem = self.horizontalHeaderItem(ii)

            # remember to hide th special column
            if headerItem.text() in self._defaultHiddenColumns or headerItem.text() == DATAFRAME_OBJECT:
                self.hideColumn(ii)

    def showColumns(self, dataFrameObject):
        # show the columns in the list
        for i, colName in enumerate(dataFrameObject.headings):
            if dataFrameObject.hiddenColumns:

                # store the current hidden columns
                self._defaultHiddenColumns = dataFrameObject.hiddenColumns

                # always hide the special column DATAFRAME_OBJECT
                if colName in dataFrameObject.hiddenColumns or colName == DATAFRAME_OBJECT:
                    self.hideColumn(i)
                else:
                    self.showColumn(i)

                    if dataFrameObject.columnDefinitions.setEditValues[i]:

                        # need to put it into the header
                        header = self.horizontalHeaderItem(i)

                        icon = QtGui.QIcon(self._icons[0])
                        # item = self.item(0, i)
                        # TableWidget.QTableWidgetItem(icon, 'Boing')  # Second argument
                        # if item:
                        #   item.setIcon(icon)
                        #   self.setItem(0, i, item)
                        if header:
                            header.setIcon(icon)
            else:
                if colName == DATAFRAME_OBJECT:
                    self.hideColumn(i)

    def _setDefaultRowHeight(self):
        # set a minimum height to the rows based on the fontmetrics of a generic character
        self.fontMetric = QtGui.QFontMetricsF(self.font())
        self.bbox = self.fontMetric.boundingRect
        rowHeight = self.bbox('A').height() + 8

        # pyqt4
        # headers = self.verticalHeader()
        # headers.setResizeMode(QtWidgets.QHeaderView.Fixed)
        # headers.setDefaultSectionSize(rowHeight)

        # pyqt5
        headers = self.verticalHeader()
        headers.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        headers.setDefaultSectionSize(rowHeight)

        # and hide the row labels
        if self.hideIndex:
            headers.hide()

        # TODO:ED check pyqt5
        # for qt5 and above
        # QHeaderView * verticalHeader = myTableView->verticalHeader();
        # verticalHeader->setSectionResizeMode(QHeaderView::Fixed);
        # verticalHeader->setDefaultSectionSize(24);

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
        if key in cursors:
            # selection handled by table widget
            self._selectionTableCallback(None)

        elif key in enter:

            # enter/return pressed
            keyMod = QtWidgets.QApplication.keyboardModifiers()

            if keyMod in addSelectionMod:
                item = self.currentItem()
                if item:
                    # set the item, which toggles selection of the row
                    self.setCurrentItem(item)

                # fire the selection callback
                self._selectionTableCallback(None)

            elif keyMod not in allKeyModifers:
                # fire the action callback (double-click on selected)
                if self._actionCallback:
                    self._doubleClickCallback(self.currentItem())
                else:
                    self._defaultDoubleClick(self.currentItem())

    def enterEvent(self, event):
        try:
            # basic tables may not have preferences defined
            if self.mainWindow:
                if self.mainWindow.application.preferences.general.focusFollowsMouse:
                    self.setFocus()
        except:
            pass

        finally:
            super(GuiTable, self).enterEvent(event)

    def mouseMoveEvent(self, event):
        if self.enableMouseMoveEvent:
            event.ignore()
            super(GuiTable, self).mouseMoveEvent(event)
            if self._mousePressedPos is not None:
                # if the mouse has been pressed, then re-enable selection if started a mouse drag, and override double-click
                if self._selectOverride and (event.pos() - self._mousePressedPos).manhattanLength() > QtWidgets.QApplication.startDragDistance():
                    # turn off selection blocking
                    self._handleCellClickedExit()

                # this is alter selection in a mouseDrag
                self._selectionTableCallback(None)

    def mousePressEvent(self, event):
        """handle mouse press events
        Clicking is handled on the mouse release
        """
        self._lastClick = 'click'
        self._buttonPressed = event.button()

        if event.button() == QtCore.Qt.RightButton:
            # stops the selection from the table when the right button is clicked
            event.accept()

        elif event.button() == QtCore.Qt.LeftButton:

            item = self.itemAt(event.pos())
            if item:
                self._currentRow = item.row()
                self._currentCol = item.column()

                if isinstance(item.value, bool) and self._checkBoxTableCallback is not None:
                    self._checkBoxTableCallback(item)
            else:
                self._currentRow = None
                self._currentCol = None

            # we are selecting from the table
            self._mousePressedPos = event.pos()

            event.accept()
            super(GuiTable, self).mousePressEvent(event)

            if self._selectOverride == False:
                # False required as may be clicking on an already selected item to deselect everything else
                self._selectionTableCallback(None, mouseDrag=False)

                # disable selecting as there may be a double click
                self.setSelectionMode(self.NoSelection)

                self._selectOverride = True

                if self.pressingModifiers():
                    # timer to re-enable table, smaller interval so that single click above doesn't look too delayed
                    # don't respond to selection if modifiers pressed
                    QtCore.QTimer.singleShot(QtWidgets.QApplication.instance().doubleClickInterval() * 0.75,
                                             self._handleCellClickedExit)
                else:
                    QtCore.QTimer.singleShot(QtWidgets.QApplication.instance().doubleClickInterval() * 0.75,
                                             partial(self._handleCellClicked, event.pos()))
            else: # odd behaviours otherwise
                self._selectionTableCallback(None)
                super(GuiTable, self).mousePressEvent(event)
        else:
            event.ignore()
            super(GuiTable, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._mousePressedPos = None
        super(GuiTable, self).mouseReleaseEvent(event)

    def _handleCellClicked(self, eventPos):
        """handle a single click event, but ignore double click events,
        with special case for clicking on an already selected item

        The best way is to disable the selection model and then re-enable after a small time interval
        """
        if self._lastClick == 'click':
            objs = self.getSelectedObjects()
            if objs and len(objs) > 1:

                # current item or item clicked?
                item = self.itemAt(eventPos)
                # item = self.currentItem()

                self.clearSelection()
                if item:

                    # re-enable selecting so new item can be picked
                    if self.multiSelect:
                        self.setSelectionMode(self.ExtendedSelection)
                    else:
                        self.setSelectionMode(self.SingleSelection)

                    # get the newly selected item
                    self.setCurrentItem(item)
                    model = self.selectionModel()
                    selection = [iSelect for iSelect in model.selectedIndexes() if iSelect.row() == item.row()]
                    obj = self.getSelectedObjects(selection)
                    obj = obj[0] if obj else None

                    if obj:
                        self._lastSelection = {'clicked'       : self.currentItem(),
                                               'selection'     : [obj],
                                               'modelSelection': self.selectionModel().selectedIndexes(),
                                               'selected'      : True}

                        # fire the selection callback
                        self._selectionTableCallback(None, mouseDrag=False)

        # cleanup after double-click
        self._handleCellClickedExit()

    def _handleCellClickedExit(self):
        # re-enable selecting
        if self.multiSelect:
            self.setSelectionMode(self.ExtendedSelection)
        else:
            self.setSelectionMode(self.SingleSelection)

        self._lastClick = None
        self._selectOverride = False  # this may be handled by NoSelection

    def _setHeaderContextMenu(self):
        """Set up the context menu for the table header
        """
        headers = self.horizontalHeader()
        headers.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        headers.customContextMenuRequested.connect(self._raiseHeaderContextMenu)

    def _getAsDataFrame(self):
        if self._dataFrameObject is not None:
            df = self._dataFrameObject.dataFrame
            return df

    def _getExportDataColums(self):
        if self._dataFrameObject is not None:
            visCol = self._dataFrameObject.visibleColumnHeadings
            return visCol

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        self.tableMenu = QtWidgets.QMenu()
        if enableExport:
            self.tableMenu.addAction("Export Visible Table", partial(self.exportTableDialog, exportAll=False))
        if enableExport:
            self.tableMenu.addAction("Export All", partial(self.exportTableDialog, exportAll=True))
        if enableDelete:
            self.tableMenu.addAction("Delete", self.deleteObjFromTable)

        # ejb - added these but don't think they are needed
        # self.tableMenu.addAction("Select All", self.selectAllObjects)
        self.tableMenu.addAction("Clear Selection", self.clearSelection)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._raiseTableContextMenu)

    def _raiseTableContextMenu(self, pos):

        pos = QtCore.QPoint(pos.x() + 10, pos.y() + 10)
        action = self.tableMenu.exec_(self.mapToGlobal(pos))

    def _raiseHeaderContextMenu(self, pos):

        if not self._dataFrameObject:
            return

        if self._enableSearch and self.searchWidget is None:
            if not attachSearchWidget(self._parent, self):
                getLogger().warning('Search option not available')

        pos = QtCore.QPoint(pos.x(), pos.y() + 10)  #move the popup a bit down. Otherwise can trigger an event if the pointer is just on top the first item

        self.headerContextMenumenu = QtWidgets.QMenu()
        columnsSettings = self.headerContextMenumenu.addAction("Column Settings...")
        searchSettings = None
        if self._enableSearch and self.searchWidget is not None:
            searchSettings = self.headerContextMenumenu.addAction("Search")
        action = self.headerContextMenumenu.exec_(self.mapToGlobal(pos))

        if action == columnsSettings:
            settingsPopup = ColumnViewSettingsPopup(parent=self._parent, dataFrameObject=self._dataFrameObject)  #, hideColumns=self._hiddenColumns, table=self)
            settingsPopup.raise_()
            settingsPopup.exec_()  # exclusive control to the menu and return _hiddencolumns

        if action == searchSettings:
            self.showSearchSettings()

    def showSearchSettings(self):
        if self.searchWidget is not None:
            self.searchWidget.show()

    def deleteObjFromTable(self):
        selected = self.getSelectedObjects()
        if selected:
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

                with catchExceptions(application=self.application, errorStringTemplate='Error deleting objects from table; "%s"'):
                    if hasattr(selected[0], 'project'):
                        thisProject = selected[0].project

                        with undoBlock():
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

    def refreshTable(self):
        self.setTableFromDataFrameObject(self._dataFrameObject)

    def refreshHeaders(self):
        self.hide()
        #self._silenceCallback = True
        # self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        self.setHorizontalHeaderLabels(self._dataFrameObject.headings)
        self.showColumns(self._dataFrameObject)
        # self.resizeColumnsToContents()
        self.horizontalHeader().setStretchLastSection(self._stretchLastSection)
        self.setColumnCount(self._dataFrameObject.numColumns)

        self.show()
        #self._silenceCallback = False
        self.resizeColumnsToContents()

        self.update()

        # self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Interactive)

    # def resizeColumnsToContents(self):
    #   self.hide()
    #   self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)
    #   super(GuiTable, self).resizeColumnsToContents()
    #   self.show()
    #   self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Interactive)

    def setData(self, data):
        """Set the data displayed in the table.
        Allowed formats are:

        * numpy arrays
        * numpy record arrays
        * metaarrays
        * list-of-lists  [[1,2,3], [4,5,6]]
        * dict-of-lists  {'x': [1,2,3], 'y': [4,5,6]}
        * list-of-dicts  [{'x': 1, 'y': 4}, {'x': 2, 'y': 5}, ...]
        * Pandas Dataframes

        """
        if isinstance(data, pd.DataFrame):
            dataFrame = data.transpose()
            data = dataFrame.to_dict(into=OrderedDict)

        self.clear()
        self.appendData(data)
        self._rawData = data

    @contextmanager
    def _guiTableUpdate(self, dataFrameObject, resize=True):
        """Context manager to ensure the headers are defined correctly after performing
        table operations
        """
        # keep the original sorting method
        sortOrder = self.horizontalHeader().sortIndicatorOrder()
        sortColumn = self.horizontalHeader().sortIndicatorSection()

        try:
            self.hide()
            yield

        finally:
            if self._dataFrameObject:
                # needed after setting the column headings
                self.setHorizontalHeaderLabels(dataFrameObject.headings)
                self.showColumns(dataFrameObject)

                # required to make the header visible
                self.setColumnCount(dataFrameObject.numColumns)
                self._reindexTableObjects()

                # re-sort the table
                if sortColumn < self.columnCount():
                    self.sortByColumn(sortColumn, sortOrder)

                # clear the dummy row
                if dataFrameObject.dataFrame.empty:
                    self.setRowCount(0)
            elif self._rawData:
                if sortColumn < self.columnCount():
                    self.sortByColumn(sortColumn, sortOrder)


            else:
                # usually called when clicking on a table header when an empty table
                self.hideDefaultColumns()
                self.setRowCount(0)

            # resize the columns if required (true by default)
            if resize:
                self.horizontalHeader().setStretchLastSection(self._stretchLastSection)
                self.resizeColumnsToContents()

            # reshow table, which will ensure column widths are updated
            self.show()

    def highlightObjects(self, objectList, scrollToSelection=True):
        """Highlight a list of objects in the table
        """
        objs = []

        if objectList:
            # get the list of objects, exclude deleted and flagged for delete
            for obj in objectList:
                if isinstance(obj, str):
                    objFromPid = self.project.getByPid(obj)

                    if objFromPid and not objFromPid.isDeleted and not objFromPid._flaggedForDelete:
                        objs.append(objFromPid)

                else:
                    objs.append(obj)

        if objs:
            self._highLightObjs(objs, scrollToSelection=scrollToSelection)
        else:
            self.clearSelection()

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
            _dataFrameObject = self.getDataFrameFromList(table=self,
                                                         buildList=rowObjects,
                                                         colDefs=columnDefs,
                                                         hiddenColumns=self._hiddenColumns)

            # populate from the Pandas dataFrame inside the dataFrameObject
            self.setTableFromDataFrameObject(dataFrameObject=_dataFrameObject, columnDefs=columnDefs)

        except Exception as es:
            raise es
            getLogger().warning('Error populating table', str(es))

        finally:
            self._highLightObjs(objs)
            self.project.unblankNotification()

    def setTableFromDataFrameObject(self, dataFrameObject, columnDefs=None):
        """Populate the table from a Pandas dataFrame
        """

        with self._tableBlockSignals('setTableFromDataFrameObject'):

            # get the currently selected objects
            objs = self.getSelectedObjects()

            self._dataFrameObject = dataFrameObject

            with self._guiTableUpdate(dataFrameObject):
                if not dataFrameObject.dataFrame.empty:
                    self.setData(dataFrameObject.dataFrame.values)
                else:
                    # set a dummy row of the correct length
                    self.setData([list(range(len(dataFrameObject.headings)))])

                # store the current headings, in case table is cleared, to stop table jumping
                self._defaultHeadings = dataFrameObject.headings
                self._defaultHiddenColumns = dataFrameObject.hiddenColumns

                if columnDefs:
                    for col, colFormat in enumerate(columnDefs.formats):
                        if colFormat is not None:
                            self.setFormat(colFormat, column=col)

            # highlight them back again
            self._highLightObjs(objs)

        # outside of the with to spawn a repaint
        self.show()

    def getDataFrameFromList(self, table=None,
                             buildList=None,
                             colDefs=None,
                             hiddenColumns=None):
        """
        Return a Pandas dataFrame from an internal list of objects
        The columns are based on the 'func' functions in the columnDefinitions

        :param buildList:
        :param colDefs:
        :return pandas dataFrameObject:
        """
        allItems = []
        objects = []

        # objectList = {}
        # indexList = {}

        if buildList:
            for col, obj in enumerate(buildList):
                listItem = OrderedDict()
                for header in colDefs.columns:
                    listItem[header.headerText] = header.getValue(obj)

                allItems.append(listItem)
                objects.append(obj)

            # indexList[str(listItem['Index'])] = obj
            # objectList[obj.pid] = listItem['Index']

            # indexList[str(col)] = obj
            # objectList[obj.pid] = col

            # indexList[str(col)] = obj
            # objectList[obj.pid] = col

        return DataFrameObject(dataFrame=pd.DataFrame(allItems, columns=colDefs.headings),
                               objectList=objects or [],
                               # indexList=indexList,
                               columnDefs=colDefs or [],
                               hiddenColumns=hiddenColumns or [],
                               table=table)

    def getDataFrameFromRows(self, table=None,
                             dataFrame=None,
                             colDefs=None,
                             hiddenColumns=None):
        """
        Return a Pandas dataFrame from the internal rows of an internal Pandas dataFrame
        The columns are based on the 'func' functions in the columnDefinitions

        :param buildList:
        :param colDefs:
        :return pandas dataFrame:
        """
        allItems = []
        objects = []
        # objectList = None
        # indexList = {}

        buildList = dataFrame.as_namedtuples()
        for ind, obj in enumerate(buildList):
            listItem = OrderedDict()
            for header in colDefs.columns:
                listItem[header.headerText] = header.getValue(obj)

            allItems.append(listItem)

        #   # TODO:ED need to add object links in here, but only the top object exists so far
        #   if 'Index' in listItem:
        #     indexList[str(listItem['Index'])] = obj
        #     objectList[obj.pid] = listItem['Index']
        #   else:
        #     indexList[str(ind)] = obj
        #     objectList[obj.pid] = ind

        return DataFrameObject(dataFrame=pd.DataFrame(allItems, columns=colDefs.headings),
                               objectList=objects,
                               # indexList=indexList,
                               columnDefs=colDefs,
                               hiddenColumns=hiddenColumns,
                               table=table)

    def rawDataToDF(self):
        try:
            df = pd.DataFrame(self._rawData)
            return df
        except:
            return pd.DataFrame()

    def tableToDataFrame(self, exportAll=True):
        """Extract the table as a dataframe for later printing
        The actual data values are exported, not the visible items which may be rounded due to the table settings

        :param exportAll: True/False - True implies export whole table - but in visible order
                                    False, export only the visible table
        """
        if not (self._dataFrameObject and self._dataFrameObject.dataFrame is not None):
            if self._rawData:
                return self.rawDataToDF()
            else:
                showWarning('Table to dataFrame', 'Table does not contain a dataFrame')

        else:
            rowList = None
            if exportAll:
                colList = self._dataFrameObject.userHeadings
                rowList = list(self._dataFrameObject.dataFrame.index)

            else:
                colList = self._dataFrameObject.visibleColumnHeadings

                # export contents of dataFrame based on the visible rows and columns
                # if self.searchWidget and self.searchWidget._listRows and self.columnCount():
                #
                #     # retrieve the correct item, checking that it is in the bounds of the table
                #     count = min(len(self.searchWidget._listRows), self.rowCount())
                #     rowList = [list(self.searchWidget._listRows)[self.item(row, 0).index] for row in range(count)]
                # else:

                if self.rowCount() and self.columnCount():
                    rowList = [self.item(row, 0).index for row in range(self.rowCount())]

            return self._tableToDataFrame(self._dataFrameObject.dataFrame, rowList=rowList, colList=colList)

    def _tableToDataFrame(self, dataFrame, rowList=None, colList=None):
        if dataFrame is not None:

            if colList:
                dataFrame = dataFrame[colList]  # returns a new dataFrame
            if rowList:
                dataFrame = dataFrame[:].iloc[rowList]

            return dataFrame

        else:
            if self._rawData is not None:
                try:
                    return pd.DataFrame(self._rawData).transpose()
                except Exception as e:
                    getLogger().warning(e)

    def exportTableDialog(self, exportAll=True):
        """export the contents of the table to a file
        The actual data values are exported, not the visible items which may be rounded due to the table settings

        :param exportAll: True/False - True implies export whole table - but in visible order
                                    False, export only the visible table
        """
        if not (self._dataFrameObject and self._dataFrameObject.dataFrame is not None):
            if self._rawData:
                self._exportTableDialog(self.rawDataToDF())
            else:
                showWarning('Export Table to File', 'Table does not contain a dataFrame')

        else:
            rowList = None
            if exportAll:
                colList = self._dataFrameObject.userHeadings
                rowList = list(self._dataFrameObject.dataFrame.index)

            else:
                colList = self._dataFrameObject.visibleColumnHeadings

                # export contents of dataFrame based on the visible rows and columns
                if self.searchWidget and self.searchWidget._listRows and self.columnCount():

                    # retrieve the correct item, checking that it is in the bounds of the table
                    count = min(len(self.searchWidget._listRows), self.rowCount())
                    rowList = [list(self.searchWidget._listRows)[self.item(row, 0).index] for row in range(count)]
                else:
                    if self.rowCount() and self.columnCount():
                        rowList = [self.item(row, 0).index for row in range(self.rowCount())]

            self._exportTableDialog(self._dataFrameObject.dataFrame, rowList=rowList, colList=colList)

    def _exportTableDialog(self, dataFrame, rowList=None, colList=None):

        if self.application and self.application.preferences:
            preferences = self.application.preferences
            workingPath = preferences.general.userWorkingPath
        else:
            preferences = None
            workingPath = self.project.path

        self.saveDialog = FileDialog(selectFile='ccpnTable.xlsx',  # default saving name
                                     fileMode=FileDialog.AnyFile,
                                     filter=".xlsx;; .csv;; .tsv;; .json ",
                                     text='Save as ',
                                     acceptMode=FileDialog.AcceptSave,
                                     preferences=preferences,
                                     initialPath=workingPath,
                                     pathID=USERTABLESPATH)
        self.saveDialog._show()
        path = self.saveDialog.selectedFile()
        if path:
            sheet_name = 'Table'
            if dataFrame is not None:

                if colList:
                    dataFrame = dataFrame[colList]  # returns a new dataFrame
                if rowList:
                    dataFrame = dataFrame[:].iloc[rowList]

                ft = self.saveDialog.selectedNameFilter()

                findExportFormats(path, dataFrame, sheet_name=sheet_name, filterType=ft, columns=colList)

            else:
                if self._rawData is not None:
                    try:
                        df = pd.DataFrame(self._rawData).transpose()
                        findExportFormats(path, df, sheet_name=sheet_name)

                        # df.to_excel(path, sheet_name=sheet_name)
                    except Exception as e:
                        getLogger().warning(e)

    def scrollToSelectedIndex(self):
        h = self.horizontalHeader()
        for i in range(h.count()):
            if not h.isSectionHidden(i) and h.sectionViewportPosition(i) >= 0:
                if self.getSelectedRows():
                    self.scrollTo(self.model().index(self.getSelectedRows()[0], i),
                                  # self.EnsureVisible)
                                  self.PositionAtCenter)
                    break

    def getSelectedRows(self):

        model = self.selectionModel()

        # selects all the items in the row
        selection = model.selectedRows()

        # if self.selectRows:
        #   selection = model.selectedRows(column=0)
        # else:
        #   selection = model.selectedIndexes()

        rows = [i.row() for i in selection]
        #rows = list(set(rows))
        #rows.sort()

        return rows

    def getSelectedObjects(self, fromSelection=None):

        model = self.selectionModel()

        # selects all the items in the row
        selection = fromSelection if fromSelection else model.selectedIndexes()

        if selection:
            selectedObjects = []
            rows = []

            for iSelect in selection:
                row = iSelect.row()
                col = iSelect.column()
                if self._dataFrameObject:
                    colName = self.horizontalHeaderItem(col).text()
                    if colName == 'Pid':

                        if row not in rows:
                            rows.append(row)
                            objIndex = model.model().data(iSelect)

                            # if str(objIndex) in self._dataFrameObject.indexList:
                            # obj = self._dataFrameObject.indexList[str(objIndex)]  # item.index needed
                            # selectedObjects.append(obj)

                            obj = self.project.getByPid(objIndex)
                            if obj:
                                selectedObjects.append(obj)

            return selectedObjects
        else:
            return None

    def clearSelection(self):
        """Clear the current selection in the table
        and remove objects from the current list
        """
        with self._tableBlockSignals('clearSelection'):

            objList = self.getSelectedObjects()
            selectionModel = self.selectionModel()
            selectionModel.clearSelection()

            # remove from the current list
            multiple = self._tableData['classCallBack']

            if self._dataFrameObject:
                tableObjs = self._dataFrameObject.objects

                if multiple:  # None if no table callback defined
                    multipleAttr = getattr(self.current, multiple)
                    if len(multipleAttr) > 0:
                        # need to remove objList from multipleAttr - fires only one current change
                        setattr(self.current, multiple, tuple(set(multipleAttr) - set(tableObjs)))

    def selectObjects(self, objList: list, setUpdatesEnabled: bool = False):
        """Select the object in the table
        """
        # skip if the table is empty
        if not self._dataFrameObject:
            return

        with self._tableBlockSignals('selectObjects'):

            selectionModel = self.selectionModel()
            if objList:

                selectionModel.clearSelection()
                for obj in objList:
                    row = self._dataFrameObject.find(self, str(obj.pid))
                    if row is not None:
                        selectionModel.select(self.model().index(row, 0),
                                              selectionModel.Select | selectionModel.Rows)

    def selectIndex(self, idx, doCallback=True):
        model = self.model()
        selectionModel = self.selectionModel()
        selectionModel.clearSelection()
        rowIndex = model.index(idx, 0)
        self.setCurrentIndex(rowIndex)
        selectionModel.select(rowIndex, selectionModel.Select | selectionModel.Rows)
        if doCallback:
            self._selectionTableCallback(None)


    def _highLightObjs(self, selection, scrollToSelection=True):

        # skip if the table is empty
        if not self._dataFrameObject:
            return

        with self._tableBlockSignals('_highLightObjs'):

            selectionModel = self.selectionModel()
            model = self.model()

            if selection:
                uniqObjs = set(selection)

                # rowObjs = []
                # for obj in uniqObjs:
                #     if obj in self._dataFrameObject.objects:
                #         rowObjs.append(obj)
                #
                # selectionModel.clearSelection()
                # for obj in rowObjs:
                #     row = self._dataFrameObject.find(self, str(obj.pid))
                #
                #     if row is not None:
                #         selectionModel.select(model.index(row, 0),
                #                               selectionModel.Select | selectionModel.Rows)

                rows = [self._dataFrameObject.find(self, str(obj.pid)) for obj in uniqObjs if obj in self._dataFrameObject.objects]
                rows = [row for row in rows if row is not None]
                if rows:
                    rows.sort(key=lambda c: int(c))

                    selectionModel.clearSelection()
                    rowIndex = model.index(rows[0], 0)
                    self.setCurrentIndex(rowIndex)

                    for row in rows[1:]:
                        rowIndex = model.index(row, 0)
                        selectionModel.select(rowIndex, selectionModel.Select | selectionModel.Rows)

                    if scrollToSelection and not self._scrollOverride:
                        self.scrollToSelectedIndex()

    def clearTable(self):
        "remove all objects from the table"
        # self.hide()
        #self._silenceCallback = True

        with self._tableBlockSignals('clearTable'):
            self.clearTableContents()

        # self.show()
        #self._silenceCallback = False
        # self.resizeColumnsToContents()
        # self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.Interactive)

    def clearTableContents(self, dataFrameObject=None):
        self.clearContents()
        self.verticalHeadersSet = True
        self.horizontalHeadersSet = True
        self.sortModes = {}

        self._dataFrameObject = dataFrameObject if dataFrameObject else None

        if self._dataFrameObject:
            # self.horizontalHeader().setResizeMode(QtWidgets.QHeaderView.ResizeToContents)

            # there must be something in the table to set the headers against
            self.setData([list(range(self._dataFrameObject.numColumns)), ])

            self.setHorizontalHeaderLabels(self._dataFrameObject.headings)
            self.showColumns(self._dataFrameObject)
            # self.resizeColumnsToContents()
            self.horizontalHeader().setStretchLastSection(self._stretchLastSection)

            # required to make the header visible
            self.setColumnCount(self._dataFrameObject.numColumns)

        self.setRowCount(0)
        self.items = []

    def getIndexList(self, classItems, attribute):
        """Get the list of objects on which to before the indexing
        To be subclassed as required
        """
        # classItem is usually a type such as PeakList, MultipletList
        # with an attribute such as peaks/peaks

        # this is a step towards making guiTableABC and subclass for each table
        return getattr(classItems, attribute, [])

    def _reindexTableObjects(self):
        """updating to make sure that the index of the item in the table matches the index of the item in the actual list
        """
        # this is for those objects that undo returns back to the table
        # because items are just given the next available 'Index' when re-inserted
        # so need to be corrected - should be done in each rename, change routine
        if self._tableData['tableSelection']:
            tSelect = getattr(self, self._tableData['tableSelection'])
            if tSelect:

                # may need a special getter here
                # e.g. a Multiplet has Multiplet.peaks
                # but may want to list peaks from a list of multiplets, so need a new object
                # currently just error check and skip
                # OR just subclass this routine!

                multiple = self._tableData['classCallBack']
                multipleAttr = self.getIndexList(tSelect, multiple)

                if multipleAttr:
                    # newIndex = [multipleAttr.index(rr) for rr in self._objects]

                    # find the columns containing the objects and the indexing
                    objCol = indCol = None
                    for cc in range(self.columnCount()):
                        colName = self.horizontalHeaderItem(cc).text()
                        if colName == DATAFRAME_INDEX:
                            indCol = cc
                            # print (DATAFRAME_INDEX, cc)
                        elif colName == DATAFRAME_OBJECT:
                            objCol = cc
                            # print (DATAFRAME_OBJECT, cc)
                    if objCol and indCol:
                        # print ('INDEXING')
                        # print (multipleAttr)
                        for rr in range(self.rowCount()):

                            thisObj = self.item(rr, objCol).value
                            if thisObj in multipleAttr:
                                # this could be slow in some cases - nmrChain.index(nmrResidue)?
                                self.item(rr, indCol).setValue(multipleAttr.index(thisObj))

    def _updateTableCallback(self, data):
        """
        Notifier callback for updating the table
        """

        with self._tableBlockSignals('_updateTableCallback'):

            # thisTableList = getattr(data[Notifier.THEOBJECT],
            #                          self._tableData['className'])   # get the table list
            table = data[Notifier.OBJECT]
            #
            # #self._silenceCallback = True
            tableSelect = self._tableData['tableSelection']

            currentTable = getattr(self, tableSelect) if tableSelect else None

            if currentTable and currentTable == table:
                trigger = data[Notifier.TRIGGER]

                if trigger == Notifier.RENAME:

                    # keep the original sorting method
                    sortOrder = self.horizontalHeader().sortIndicatorOrder()
                    sortColumn = self.horizontalHeader().sortIndicatorSection()

                    # self.displayTableForNmrTable(table)
                    self._tableData['changeFunc'](table)

                    # if tableSelect and getattr(self, tableSelect) in thisTableList:
                    #   trigger = data[Notifier.TRIGGER]
                    #
                    #   # keep the original sorting method
                    #   sortOrder = self.horizontalHeader().sortIndicatorOrder()
                    #   sortColumn = self.horizontalHeader().sortIndicatorSection()
                    #
                    #   if table.pid == self._tableData['pullDownWidget'].getText() and trigger == Notifier.DELETE:
                    #
                    #     self.clearTable()
                    #
                    #   elif table.pid == self._tableData['pullDownWidget'].getText() and trigger == Notifier.CHANGE:
                    #
                    #     # self.displayTableForNmrTable(table)
                    #     self._tableData['changeFunc'](table)
                    #
                    #   elif trigger == Notifier.RENAME:
                    #     if table == getattr(self, tableSelect):
                    #
                    #       # self.displayTableForNmrTable(table)
                    #       self._tableData['changeFunc'](table)

                    # re-sort the table
                    if sortColumn < self.columnCount():
                        self.sortByColumn(sortColumn, sortOrder)

                    self.horizontalHeader().setStretchLastSection(self._stretchLastSection)
                    self.resizeColumnsToContents()

            # else:
            #   self.clearTable()

            #self._silenceCallback = False

        getLogger().debug2('<updateTableCallback>', data['notifier'],
                           tableSelect,
                           data['trigger'], data['object'])

    def _updateRowCallback(self, data):
        """
        Notifier callback for updating the table for change in nmrRows
        :param data:
        """
        # thisTableList = getattr(data[Notifier.THEOBJECT],
        #                          self._tableData['className'])   # get the tableList

        with self._tableBlockSignals('_updateRowCallback'):
            row = data[Notifier.OBJECT]

            if not self._dataFrameObject or row is None:
                return

            #self._silenceCallback = True

            _update = False
            # try:

            # multiple delete from deleteObjFromTable messes with this
            # if thisRow.pid == self._tableData['pullDownWidget'].getText():

            # is the row in the table
            # TODO:ED move these into the table class

            # keep the original sorting method
            # sortOrder = self.horizontalHeader().sortIndicatorOrder()
            # sortColumn = self.horizontalHeader().sortIndicatorSection()

            trigger = data[Notifier.TRIGGER]
            if trigger == Notifier.DELETE:

                # remove item from self._dataFrameObject and table

                if row in self._dataFrameObject._objects:
                    self._dataFrameObject.removeObject(row)
                    _update = True

            elif trigger == Notifier.CREATE:

                # insert item into self._dataFrameObject

                if self._tableData['tableSelection']:
                    tSelect = getattr(self, self._tableData['tableSelection'])
                    if tSelect:

                        # check that the object created is in the list viewed in this table
                        # e.g. row.peakList == tSelect then add - older test
                        # if tSelect == getattr(row, self._tableData['tableName']):

                        # multiple attribute name, i.e. added 's' - and get tSelect.objs
                        multiple = self._tableData['classCallBack']
                        # multipleAttr = getattr(tSelect, multiple)
                        multipleAttr = self.getIndexList(tSelect, multiple)

                        # if item is in the list, then create
                        if row in multipleAttr:
                            # add the row to the dataFrame and table
                            self._dataFrameObject.appendObject(row)
                            _update = True

            elif trigger == Notifier.CHANGE:

                # modify the line in the table
                try:
                    _update = self._dataFrameObject.changeObject(row)

                    # TODO:ED it may not already be in the list - check indexing
                    if not _update:
                        if self._tableData['tableSelection']:
                            tSelect = getattr(self, self._tableData['tableSelection'])
                            if tSelect:

                                # check that the object created is in the list viewed in this table
                                # e.g. row.peakList == tSelect then add
                                if tSelect == getattr(row, self._tableData['tableName']):
                                    # add the row to the dataFrame and table

                                    # get the array containing the objects displayed in the table
                                    multiple = self._tableData['classCallBack']
                                    # print(tSelect, multiple)
                                    multipleAttr = getattr(tSelect, multiple)

                                    self._dataFrameObject.appendObject(row, multipleAttr=multipleAttr)
                                    _update = True

                    # else:
                    #
                    #     # delete from the table?
                    #     if row in self._dataFrameObject._objects:
                    #         self._dataFrameObject.removeObject(row)
                    #         _update = True


                except Exception as es:
                    getLogger().debug2('Error updating row in table')

            elif trigger == Notifier.RENAME:
                # get the old pid before the rename
                oldPid = data[Notifier.OLDPID]

                if row in self._dataFrameObject._objects:

                    # modify the oldPid in the objectList, change to newPid
                    _update = self._dataFrameObject.renameObject(row, oldPid)

                    # TODO:ED check whether the new object is still in the active list - remove otherwise
                    if self._tableData['tableSelection']:
                        tSelect = getattr(self, self._tableData['tableSelection'])  # eg self.nmrChain
                        if tSelect and not tSelect.isDeleted:  # eg self.nmrChain.nmrResidues
                            objList = getattr(tSelect, self._tableData['rowClass']._pluralLinkName)

                            if objList and row not in objList:
                                # TODO:ED Check current deletion
                                getLogger().debug2('>>> deleting spare object %s' % row, oldPid)
                                self._dataFrameObject.removeObject(row)

                            else:
                                getLogger().debug2('>>> creating spare object %s' % row, oldPid)
                                self._dataFrameObject.appendObject(row)
                        else:
                            self.clearTable()

                        _update = True

        if _update:
            # self.update()
            # re-sort the table
            # if sortColumn < self.columnCount():
            #   self.sortByColumn(sortColumn, sortOrder)
            #
            # # except Exception as es:
            # #   getLogger().warning(str(es)+str(data))
            #
            # #self._silenceCallback = False
            getLogger().debug2('<updateRowCallback>', data['notifier'],
                               self._tableData['tableSelection'],
                               data['trigger'], data['object'])

        return _update

    def getCellToRows(self, cellItem, attribute):
        """Get the list of objects which cellItem maps to for this table
        To be subclassed as required
        """
        # classItem is usually a type such as PeakList, MultipletList
        # with an attribute such as peaks/peaks

        # this is a step towards making guiTableABC and subclass for each table
        return getattr(cellItem, attribute, [])

    def _updateCellCallback(self, attr, data):
        """
        Notifier callback for updating the table
        :param data:
        """
        # thisTableList = getattr(data[Notifier.THEOBJECT],
        #                          self._tableData['className'])   # get the tableList

        with self._tableBlockSignals('_updateCellCallback'):
            cellData = data[Notifier.OBJECT]
            # row = getattr(cell, self._tableData['rowName'])
            # cells = getattr(cellData, attr)
            cells = makeIterableList(cellData)

            #self._silenceCallback = True
            _update = False

            for cell in cells:
                callbacktypes = self._tableData['cellClassNames']
                rowObj = None
                if isinstance(callbacktypes, list):
                    for cBack in callbacktypes:

                        # check if row is the correct type of class
                        if isinstance(cell, cBack[OBJECT_CLASS]):
                            # rowObj = getattr(cell, cBack[OBJECT_PARENT])
                            rowObj = self.getCellToRows(cell, cBack[OBJECT_PARENT])
                            rowCallback = cBack[OBJECT_PARENT]
                            break
                else:
                    try:
                        rowObj = getattr(cell, callbacktypes[OBJECT_PARENT])
                    except Exception as es:
                        pass

                    rowCallback = callbacktypes[OBJECT_PARENT]

                # concatenate the list - will always return a list
                rowObjs = makeIterableList(rowObj)

                # update the correct row by calling row handler
                for rowObj in rowObjs:
                    newData = data.copy()
                    newData[Notifier.OBJECT] = rowObj
                    newData[Notifier.TRIGGER] = Notifier.CHANGE

                    # check whether we are the row object or still a cell object
                    cellType = self._tableData['rowClass']
                    if type(rowObj) is cellType:

                        self._updateRowCallback(newData)

                        if data[Notifier.TRIGGER] == 'rename':
                            #update the original object from getParentfromPartialPid...

                            # find the original parent row object from the oldPid
                            oldPid = data[Notifier.OLDPID]
                            cellParent = getParentObjectFromPid(self.project, oldPid)
                            if cellParent is not rowObj:
                                # if it has changed then update the original row
                                newData[Notifier.OBJECT] = cellParent
                                self._updateRowCallback(newData)

                    else:
                        self._updateCellCallback(rowCallback, newData)

        #self._silenceCallback = False
        getLogger().debug2('<updateCellCallback>', data['notifier'],
                           self._tableData['tableSelection'],
                           data['trigger'], data['object'])

    def _searchCallBack(self, data):
        """
        Callback to populate the search bar with the selected item
        """

        value = getattr(data[CallBack.OBJECT], self._tableData['searchCallBack']._pluralLinkName, None)
        if value and self.searchWidget and self.searchWidget.isVisible():
            self.searchWidget.selectSearchOption(self, self._tableData['searchCallBack'], value[0].id)

    def _selectCurrentCallBack(self, data):
        """
        Callback to handle selection on the table, linked to user defined function
        :param data:
        """
        # self._sortChanged(0, 0)

        if not self._tableBlockingLevel:
            self._tableData['selectCurrentCallBack'](data)

    def setTableNotifiers(self, tableClass=None, rowClass=None, cellClassNames=None,
                          tableName=None, rowName=None, className=None,
                          changeFunc=None, updateFunc=None,
                          tableSelection=None, pullDownWidget=None,
                          callBackClass=None, selectCurrentCallBack=None,
                          searchCallBack=None, moduleParent=blankId):
        """
        Set a Notifier to call when an object is created/deleted/renamed/changed
        rename calls on name
        change calls on any other attribute

        :param tableClass - class of table object, selected by pulldown:
        :param rowClass - class identified by a row in the table:
        :param cellClassNames - list of tuples (cellClass, cellClassName):
                                class that affects row when changed
        :param tableName - name of attribute for parent name of row:
        :param rowName - name of attribute for parent name of cell:
        :param changeFunc:
        :param updateFunc:
        :param tableSelection:
        :param pullDownWidget:
        :return:
        """
        # self.clearTableNotifiers()
        self._initialiseTableNotifiers()

        if tableClass:
            self._tableNotifier = Notifier(self.project,
                                           [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                           tableClass.__name__,
                                           self._updateTableCallback,
                                           onceOnly=True)
            # self._tableNotifier.setDebug(True)

        if rowClass:
            # TODO:ED check OnceOnly residue notifiers
            # 'i-1' residue spawns a rename but the 'i' residue only fires a change
            self._rowNotifier = Notifier(self.project,
                                         [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME, Notifier.CHANGE],
                                         rowClass.__name__,
                                         self._updateRowCallback,
                                         onceOnly=True)  # should be True, but doesn't work
            # self._rowNotifier.setDebug(True)

            # for 'i-1' nmrResidues
        if isinstance(cellClassNames, list):
            for cellClass in cellClassNames:
                self._cellNotifiers.append(Notifier(self.project,
                                                    [Notifier.CHANGE, Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                                    cellClass[OBJECT_CLASS].__name__,
                                                    partial(self._updateCellCallback, cellClass[OBJECT_PARENT]),
                                                    onceOnly=True))
        else:
            if cellClassNames:
                self._cellNotifiers.append(Notifier(self.project,
                                                    [Notifier.CHANGE, Notifier.CREATE, Notifier.DELETE, Notifier.RENAME],
                                                    cellClassNames[OBJECT_CLASS].__name__,
                                                    partial(self._updateCellCallback, cellClassNames[OBJECT_PARENT]),
                                                    onceOnly=True))

        if selectCurrentCallBack:
            self._selectCurrentNotifier = Notifier(self.current,
                                                   [Notifier.CURRENT],
                                                   callBackClass._pluralLinkName,
                                                   self._selectCurrentCallBack)
            # else:
            #     self._selectCurrentNotifier = Notifier(self.current,
            #                                            [Notifier.CURRENT],
            #                                            rowName,
            #                                            self._selectCurrentCallBack)

        if searchCallBack:
            self._searchNotifier = Notifier(self.current,
                                            [Notifier.CURRENT],
                                            searchCallBack._pluralLinkName,
                                            self._searchCallBack)

        self._tableData = {'updateFunc'           : updateFunc,
                           'changeFunc'           : changeFunc,
                           'tableSelection'       : tableSelection,
                           'pullDownWidget'       : pullDownWidget,
                           'tableClass'           : tableClass,
                           'rowClass'             : rowClass,
                           'cellClassNames'       : cellClassNames,
                           'tableName'            : tableName,
                           'className'            : className,
                           'classCallBack'        : callBackClass._pluralLinkName if callBackClass else None,
                           'selectCurrentCallBack': selectCurrentCallBack,
                           'searchCallBack'       : searchCallBack,
                           'moduleParent'         : moduleParent
                           }

        # add a cleaner id to the opened guiTable list
        self.moduleParent = moduleParent
        MODULEIDS[id(moduleParent)] = len(MODULEIDS)

    def setDefaultTableData(self):
        """Populate an empty table data object
        """
        self._tableData = {'updateFunc'           : None,
                           'changeFunc'           : None,
                           'tableSelection'       : None,
                           'pullDownWidget'       : None,
                           'tableClass'           : None,
                           'rowClass'             : None,
                           'cellClassNames'       : None,
                           'tableName'            : None,
                           'className'            : None,
                           'classCallBack'        : None,
                           'selectCurrentCallBack': None,
                           'searchCallBack'       : None,
                           'moduleParent'         : blankId
                           }

    def _initialiseTableNotifiers(self):
        """Set the initial notifiers to empty
        """
        self._tableNotifier = None
        self._rowNotifier = None
        self._cellNotifiers = []
        self._selectCurrentNotifier = None
        self._droppedNotifier = None
        self._searchNotifier = None

    # @staticmethod  # has to be a static method
    # def onDestroyed(widget):
    #     # print("DEBUG on destroyed:", widget)
    #     widget._clearTableNotifiers()

    def _close(self):
        self._clearTableNotifiers()
        # self.close()

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

        self._cellNotifiers = None
        if self._selectCurrentNotifier is not None:
            self._selectCurrentNotifier.unRegister()
            self._selectCurrentNotifier = None

        if self._droppedNotifier is not None:
            self._droppedNotifier.unRegister()
            self._droppedNotifier = None

        if self._searchNotifier is not None:
            self._searchNotifier.unRegister()
            self._searchNotifier = None

    def setRowBackgroundColour(self, row, colour, columnList=None):
        """Set the background colour for the row

        :param row: row to be coloured
        :param colour: colour of type QtGui.Brush/QtGui.Color
        :param columnList: None, or list of column numbers, out-of-range columns are ignored
        :return:
        """
        # NOTE:ED - need colour/row checking, ignore for the minute
        try:
            if not isinstance(columnList, (type(None), list, tuple)):
                raise TypeError('columnList must be None, or a list of integers')

            if columnList:
                cols = [col for col in columnList if 0 <= col < self.columnCount()]
            else:
                cols = range(self.columnCount())
            for j in cols:
                self.item(row, j).setBackground(colour)
        except Exception as es:
            pass

    # def dragEnterEvent(self, event):
    #   ccpnmrJsonData = 'ccpnmr-json'
    #
    #   if event.mimeData().hasUrls():
    #     event.accept()
    #   else:
    #     pids = []
    #     for item in self.selectedItems():
    #       if item is not None:
    #
    #         # TODO:ED check the list of selected as with getSelectedObjects to get pids..
    #         # trouble is, this is working as a dropevent
    #         objFromPid = self.project.getByPid(item.data(0, QtCore.Qt.DisplayRole))
    #         if objFromPid is not None:
    #           pids.append(objFromPid.pid)
    #
    #     itemData = json.dumps({'pids':pids})
    #     event.mimeData().setData(ccpnmrJsonData, itemData)
    #     event.mimeData().setText(itemData)
    #     event.accept()


EDIT_ROLE = QtCore.Qt.EditRole


class GuiTableDelegate(QtWidgets.QStyledItemDelegate):
    """
    handle the setting of data when editing the table
    """

    def __init__(self, parent):
        """
        Initialise the delegate
        :param parent - link to the handling table:
        """
        QtWidgets.QStyledItemDelegate.__init__(self, parent)
        self.customWidget = False
        self._parent = parent
        self._editorCreated = 0
        self._returnPressed = False

    def setEditorData(self, widget, index) -> None:
        """populate the editor widget when the cell is edited
        """
        # edits occur without actually calling editItem() - and occurs twice?

        if self._editorCreated == 1:  # only populate on the first event after creation
            self._editorCreated = 2

            # if self._editorCreated:
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

        else:
            super(GuiTableDelegate, self).setEditorData(widget, index)

    def createEditor(self, parent: QtWidgets.QWidget, option: 'QtWidgets.QStyleOptionViewItem', index: QtCore.QModelIndex) -> QtWidgets.QWidget:

        # create the widget from the superClass
        widget = super(GuiTableDelegate, self).createEditor(parent, option, index)

        self._editorCreated = 1
        self._editorValue = None
        self._returnPressed = False

        if isinstance(widget, QtWidgets.QLineEdit):
            # add returnPressed capture signal - destroyed on widget destroy
            widget.returnPressed.connect(partial(self._returnPressedCallback, widget))

        return widget

    def _returnPressedCallback(self, widget):
        """Capture the returnPressed event from the widget, because the setModeData event seems to be a frame behind the widget
        when getting the text()
        """

        # check that it is a QLineEdit - check for other types later (see old table class)
        if isinstance(widget, QtWidgets.QLineEdit):
            self._editorValue = widget.text()
            self._returnPressed = True

    def setModelData(self, widget, mode, index):
        """
        Set the object to the new value
        :param widget - typically a lineedit handling the editing of the cell:
        :param mode - editing mode:
        :param index - QModelIndex of the cell:
        """

        # check the widget type
        if isinstance(widget, QtWidgets.QLineEdit):
            if self._returnPressed:
                # grab from the stored value - other value seems to be a frame behind the QLineEdit update
                text = self._editorValue
            else:
                text = widget.text()

        row = index.row()
        col = index.column()

        try:
            rowData = []
            # read the row from the table to get the pid
            for ii in range(self._parent.columnCount()):
                rowData.append(self._parent.item(row, ii).text())

            if DATAFRAME_PID in self._parent._dataFrameObject.headings:

                # get the object to apply the data to
                pidCol = self._parent._dataFrameObject.headings.index(DATAFRAME_PID)
                pid = rowData[pidCol]
                obj = self._parent.project.getByPid(pid)

                # set the data which will fire notifiers to populate all tables
                func = self._parent._dataFrameObject.setEditValues[col]
                if func and obj:
                    func(obj, text)
            else:
                getLogger().debug('table %s does not contain a Pid' % self)
                # return super(GuiTableDelegate, self).setModelData(widget, mode, index)

        except Exception as es:
            getLogger().warning('Error handling cell editing: %i %i %s' % (row, col, str(es)))


class GuiTableFrame(Frame):
    def __init__(self, *args, **kwargs):
        super(GuiTableFrame, self).__init__(parent=self.mainWidget, setLayout=True, spacing=(0, 0),
                                            showBorder=False, fShape='noFrame',
                                            grid=(1, 0),
                                            hPolicy='expanding', vPolicy='expanding')

        self.guiTable = GuiTable(self, *args, **kwargs)
        self.searchWidget = None


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Icon import Icon

    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from ccpn.util import Colour
    from ccpn.ui.gui.widgets.Column import ColumnClass, Column


    app = TestApplication()


    class mockObj(object):
        'Mock object to test the table widget editing properties'
        pid = ''
        integer = 3
        exampleFloat = 3.1  # This will create a double spin box
        exampleBool = True  # This will create a check box
        string = 'white'  # This will create a line Edit
        exampleList = [(' ', 'Mock', 'Test'), ]  # This will create a pulldown
        color = QtGui.QColor('Red')
        icon = Icon('icons/warning')
        r = Colour.colourNameToHexDict['red']
        y = Colour.colourNameToHexDict['yellow']
        b = Colour.colourNameToHexDict['blue']
        colouredIcons = [None, Icon(color=r), Icon(color=y), Icon(color=b)]

        flagsList = [[''] * len(colouredIcons), [Icon] * len(colouredIcons), 1, colouredIcons]  # This will create a pulldown. Make a list with the

        # same structure of pulldown setData function: (texts=None, objects=None, index=None,
        # icons=None, clear=True, headerText=None, headerEnabled=False, headerIcon=None)

        def editBool(self, value):
            mockObj.exampleBool = value

        def editFloat(self, value):
            mockObj.exampleFloat = value

        def editPulldown(self, value):
            mockObj.exampleList = value

        def editFlags(self, value):
            print(value)


    def _comboboxCallBack(value):
        print('called value =', value)


    def _checkBoxCallBack(data):
        s = data['checked']
        print('called value =', s)


    def table_pulldownCallback(value):
        print('NEW', value)


    def table_pulldownCallbackShow():
        print('NEW', dir(), )


    popup = CcpnDialog(windowTitle='Test Table', setLayout=True)

    columns = ColumnClass([
        (
            'Float',
            lambda i: mockObj.exampleFloat,
            'TipText: Float',
            lambda mockObj, value: mockObj.editFloat(mockObj, value),
            None,
            ),

        (
            'Bool',
            lambda i: mockObj.exampleBool,
            'TipText: Bool',
            lambda mockObj, value: mockObj.editBool(mockObj, value),
            None,
            ),

        (
            'Pulldown',
            lambda i: mockObj.exampleList,
            'TipText: Pulldown',
            lambda mockObj, value: mockObj.editPulldown(mockObj, value),
            None,
            ),

        (
            'Flags',
            lambda i: mockObj.flagsList,
            'TipText: Flags',
            lambda mockObj, value: mockObj.editFlags(mockObj, value),
            None,
            )
        ])
    table_pulldownCallbackDict = {'callback': table_pulldownCallback, 'clickToShowCallback': table_pulldownCallbackShow}
    table = GuiTable(parent=popup, dataFrameObject=None, _pulldownKwds=table_pulldownCallbackDict, checkBoxCallback=_checkBoxCallBack, grid=(0, 0))
    df = table.getDataFrameFromList(table, [mockObj] * 5, colDefs=columns)

    table.setTableFromDataFrameObject(dataFrameObject=df)
    table.item(0, 0).setBackground(QtGui.QColor(100, 100, 150))  #color the first item
    # combo = PulldownList(table, callback=_comboboxCallBack)
    # table.setCellWidget(0, 0, combo)
    # combo.addItem('DDD')
    # combo.addItem('TTTT')
    # table.item(0, 0).setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
    # table.item(0, 0).setCheckState(QtCore.Qt.Unchecked)
    # table.item(0,0).setFormat(float(table.item(0,0).format))
    # print(table.item(0,0)._format)
    print(table.horizontalHeaderItem(0).text())
    print(table.item(0, 1).text())
    table.horizontalHeaderItem(1).setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
    table.horizontalHeaderItem(1).setCheckState(QtCore.Qt.Unchecked)

    popup.show()
    popup.raise_()
    app.start()
