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
__date__ = "$Date: 2021-10-29 16:38:09 +0100 (Fri, October 29, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
import pandas as pd
from ccpn.core.DataTable import DataTable
from ccpn.core.lib.Notifiers import Notifier

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.PulldownListsForObjects import DataTablePulldown, RestraintTablePulldown
from ccpn.ui.gui.widgets.GuiTable import GuiTable, _getValueByHeader
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.lib._SimplePandasTable import _SimplePandasTableView, _updateSimplePandasTable
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar

from ccpn.util.Logging import getLogger


ALL = '<all>'
_RESTRAINTTABLE = 'restraintTable'


class DataTableModule(CcpnModule):
    """
    This class implements the module by wrapping a DataTable instance
    """
    includeSettingsWidget = False
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False

    className = 'DataTableModule'
    _allowRename = True

    activePulldownClass = None

    def __init__(self, mainWindow=None, name='DataTable Module',
                 dataTable=None, selectFirstItem=False):
        """
        Initialise the Module widgets
        """
        super().__init__(mainWindow=mainWindow, name=name)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        # guiTable
        self.dataTableWidget = DataTableWidget(parent=self.mainWidget,
                                               mainWindow=self.mainWindow,
                                               moduleParent=self,
                                               setLayout=True,
                                               grid=(0, 0))

        if dataTable is not None:
            self.selectDataTable(dataTable)
        elif selectFirstItem:
            self.dataTableWidget.dtWidget.selectFirstItem()

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.dataTableWidget._maximise()

    def selectDataTable(self, dataTable=None):
        """
        Manually select a dataTable from the pullDown
        """
        self.dataTableWidget._selectDataTable(dataTable)

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self.dataTableWidget._close()
        super()._closeModule()


class DataTableWidget(_SimplePandasTableView):
    """
    Class to present a DataTable
    """
    className = 'DataTableWidget'
    attributeName = 'dataTables'

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, dataTable=None, **kwds):
        """
        Initialise the widgets for the module.
        """
        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        kwds['setLayout'] = True
        self._dataTable = None

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        # main window
        row = 0
        Spacer(self._widget, 5, 5,
               QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
               grid=(0, 0), gridSpan=(1, 1))
        row += 1
        self.dtWidget = DataTablePulldown(parent=self._widget,
                                          mainWindow=self.mainWindow, default=None,
                                          grid=(row, 0), gridSpan=(1, 2), minimumWidths=(0, 100),
                                          showSelectName=True,
                                          sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                          callback=self._selectionPulldownCallback,
                                          )
        row += 1
        HLine(parent=self._widget, grid=(row, 0), gridSpan=(1, 4), height=16, colour=getColours()[DIVIDER])

        row += 1
        self.rtWidget = RestraintTablePulldown(parent=self._widget,
                                               mainWindow=self.mainWindow, default=None,
                                               grid=(row, 0), gridSpan=(1, 2), minimumWidths=(0, 100),
                                               showSelectName=True,
                                               sizeAdjustPolicy=QtWidgets.QComboBox.AdjustToContents,
                                               callback=self._rtPulldownCallback,
                                               )
        row += 1
        Label(self._widget, text='metadata', grid=(row, 0), hAlign='r')
        self.textBox = TextEditor(self._widget, grid=(row, 1), gridSpan=(1, 3), editable=False)

        row += 1
        self.labelComment = Label(self._widget, text='comment', grid=(row, 0), hAlign='r')
        self.lineEditComment = LineEdit(self._widget, grid=(row, 1), gridSpan=(1, 3),
                                        textAlignment='l', backgroundText='> Optional <')
        self.lineEditComment.editingFinished.connect(self._applyComment)

        row += 1
        Spacer(self._widget, 5, 5,
               QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
               grid=(row, 3), gridSpan=(1, 1))
        self._widget.getLayout().setColumnStretch(3, 1)

        # initialise the currently attached dataFrame
        self._hiddenColumns = []
        self.dataFrameObject = None

        # initialise the table
        super().__init__(parent=parent,
                         mainWindow=self.mainWindow,
                         # dataFrameObject=None,
                         # setLayout=True,
                         # autoResize=True,
                         # # selectionCallback=self._selectionCallback,
                         # # actionCallback=self._actionCallback,
                         # multiSelect=True,
                         showHorizontalHeader=True,
                         showVerticalHeader=False,
                         grid=(3, 0), gridSpan=(1, 6))
        self.moduleParent = moduleParent

        if dataTable is not None:
            self._selectDataTable(dataTable)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, DataTable, self.dtWidget)

    def _selectDataTable(self, dataTable=None):
        """
        Manually select a DataTable from the pullDown
        """
        if dataTable is None:
            self.idWidget.selectFirstItem()
        else:
            if not isinstance(dataTable, DataTable):
                getLogger().warning(f'select: Object {dataTable} is not of type DataTable')
                return
            else:
                for widgetObj in self.dtWidget.textList:
                    if dataTable.pid == widgetObj:
                        self._dataTable = dataTable
                        self.dtWidget.select(self._dataTable.pid)

    def _getPullDownSelection(self):
        return self.itWidget.getText()

    def _selectPullDown(self, value):
        self.itWidget.select(value)

    def displayTableForDataTable(self, dataTable):
        """
        Display the table for the DataTable
        """
        self.dtWidget.select(dataTable.pid)
        self._update(dataTable)

    def _updateCallback(self, data):
        """
        Notifier callback for updating the table
        """
        thisDataTable = getattr(data[Notifier.THEOBJECT], self.attributeName)  # get the dataTable
        if self._dataTable in thisDataTable:
            self.displayTableForDataTable(self._dataTable)
        else:
            self.clearTable()

    def _maximise(self):
        """
        Redraw the table on a maximise event
        """
        if self._dataTable:
            self.displayTableForDataTable(self._dataTable)
        else:
            self.clear()

    def _update(self, dataTable):
        """
        Update the table
        """
        df = dataTable.data
        if len(dataTable.data) > 0:
            # colDefs = ColumnClass([(x, lambda row: _getValueByHeader(row, x), None, None, None) for x in df.columns])
            # columnsMap = {x: x for x in df.columns}
            # dfo = self.getDataFromFrame(self, df, colDefs, columnsMap)
            # self.setTableFromDataFrameObject(dataFrameObject=dfo, columnDefs=colDefs)
            # self.selectIndex(0)
            _updateSimplePandasTable(self, df, _resize=False)
        else:
            _updateSimplePandasTable(self, pd.DataFrame({}))

        _rTablePid = dataTable.getMetadata(_RESTRAINTTABLE)
        self.rtWidget.select(_rTablePid)
        self.textBox.setText(str(dataTable.metadata))
        self.lineEditComment.setText(dataTable.comment if dataTable.comment else '')

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting dataTable from the pull down menu
        """
        if item is not None:
            self._dataTable = self.project.getByPid(item)
            if self._dataTable is not None:
                self.displayTableForDataTable(self._dataTable)
            else:
                # self.clearTable()
                _updateSimplePandasTable(self, pd.DataFrame({}))

    def _rtPulldownCallback(self, item):
        """
        Notifier Callback for selecting restraintTable from the pull down menu
        """
        try:
            with undoBlockWithoutSideBar():
                if (_rTable := self.project.getByPid(item)):
                    self._dataTable.setMetadata(_RESTRAINTTABLE, item)
                else:
                    self._dataTable.setMetadata(_RESTRAINTTABLE, None)

        except Exception as es:
            # need to immediately set back to stop error on loseFocus which also fires editingFinished
            showWarning('Data Table', str(es))

        self.textBox.setText(str(self._dataTable.metadata))

    def _applyComment(self):
        """Set the values in the dataTable
        """
        if self._dataTable:
            comment = self.lineEditComment.text()
            try:
                with undoBlockWithoutSideBar():
                    self._dataTable.comment = comment

            except Exception as es:
                # need to immediately set back to stop error on loseFocus which also fires editingFinished
                showWarning('Data Table', str(es))

    def _close(self):
        """
        Cleanup the notifiers when the window is closed
        """
        pass

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
