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
__dateModified__ = "$dateModified: 2022-02-24 19:38:24 +0000 (Thu, February 24, 2022) $"
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
from ccpn.core.ViolationTable import ViolationTable
from ccpn.core.lib.Notifiers import Notifier

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.PulldownListsForObjects import ViolationTablePulldown, RestraintTablePulldown
from ccpn.ui.gui.widgets.GuiTable import GuiTable, _getValueByHeader
from ccpn.ui.gui.widgets.Column import ColumnClass
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar

from ccpn.util.Logging import getLogger


ALL = '<all>'
_RESTRAINTTABLE = 'restraintTable'


class ViolationTableModule(CcpnModule):
    """
    This class implements the module by wrapping a ViolationTable instance
    """
    includeSettingsWidget = False
    maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
    settingsPosition = 'left'

    includePeakLists = False
    includeNmrChains = False
    includeSpectrumTable = False

    className = 'ViolationTableModule'
    _allowRename = True

    activePulldownClass = None

    def __init__(self, mainWindow=None, name='ViolationTable Module',
                 violationTable=None, selectFirstItem=False):
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
        self.violationTableWidget = ViolationTableWidget(parent=self.mainWidget,
                                                         mainWindow=self.mainWindow,
                                                         moduleParent=self,
                                                         setLayout=True,
                                                         grid=(0, 0))

        if violationTable is not None:
            self.selectViolationTable(violationTable)
        elif selectFirstItem:
            self.violationTableWidget.vtWidget.selectFirstItem()

    def _maximise(self):
        """
        Maximise the attached table
        """
        self.violationTableWidget._maximise()

    def selectViolationTable(self, violationTable=None):
        """
        Manually select a violationTable from the pullDown
        """
        self.violationTableWidget._selectViolationTable(violationTable)

    def _closeModule(self):
        """
        CCPN-INTERNAL: used to close the module
        """
        self.violationTableWidget._close()
        super()._closeModule()


class ViolationTableWidget(GuiTable):
    """
    Class to present a ViolationTable
    """
    className = 'ViolationTableWidget'
    attributeName = 'violationTables'

    def __init__(self, parent=None, mainWindow=None, moduleParent=None, violationTable=None, **kwds):
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
        self._violationTable = None

        # Initialise the scroll widget and common settings
        self._initTableCommonWidgets(parent, **kwds)

        # main window
        row = 0
        Spacer(self._widget, 5, 5,
               QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
               grid=(row, 0), gridSpan=(1, 1))
        row += 1
        self.vtWidget = ViolationTablePulldown(parent=self._widget,
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
                         dataFrameObject=None,
                         setLayout=True,
                         autoResize=True,
                         # selectionCallback=self._selectionCallback,
                         # actionCallback=self._actionCallback,
                         multiSelect=True,
                         grid=(3, 0), gridSpan=(1, 6))
        self.moduleParent = moduleParent

        if violationTable is not None:
            self._selectViolationTable(violationTable)

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        self._handleDroppedItems(pids, ViolationTable, self.vtWidget)

    def _selectViolationTable(self, violationTable=None):
        """
        Manually select a ViolationTable from the pullDown
        """
        if violationTable is None:
            self.idWidget.selectFirstItem()
        else:
            if not isinstance(violationTable, ViolationTable):
                getLogger().warning(f'select: Object {violationTable} is not of type ViolationTable')
                return
            else:
                for widgetObj in self.vtWidget.textList:
                    if violationTable.pid == widgetObj:
                        self._violationTable = violationTable
                        self.vtWidget.select(self._violationTable.pid)

    def _getPullDownSelection(self):
        return self.itWidget.getText()

    def _selectPullDown(self, value):
        self.itWidget.select(value)

    def displayTableForViolationTable(self, violationTable):
        """
        Display the table for the ViolationTable
        """
        self.vtWidget.select(violationTable.pid)
        self._update(violationTable)

    def _updateCallback(self, data):
        """
        Notifier callback for updating the table
        """
        thisViolationTable = getattr(data[Notifier.THEOBJECT], self.attributeName)  # get the violationTable
        if self._violationTable in thisViolationTable:
            self.displayTableForViolationTable(self._violationTable)
        else:
            self.clearTable()

    def _maximise(self):
        """
        Redraw the table on a maximise event
        """
        if self._violationTable:
            self.displayTableForViolationTable(self._violationTable)
        else:
            self.clear()

    def _update(self, violationTable):
        """
        Update the table
        """
        df = violationTable.data
        if len(violationTable.data) > 0:
            colDefs = ColumnClass([(x, lambda row: _getValueByHeader(row, x), None, None, None) for x in df.columns])
            columnsMap = {x: x for x in df.columns}
            dfo = self.getDataFromFrame(self, df, colDefs, columnsMap)
            self.setTableFromDataFrameObject(dataFrameObject=dfo, columnDefs=colDefs)
            self.selectIndex(0)

        _rTablePid = violationTable.getMetadata(_RESTRAINTTABLE)
        self.rtWidget.select(_rTablePid)
        self.textBox.setText(str(violationTable.metadata))
        self.lineEditComment.setText(violationTable.comment if violationTable.comment else '')

    def _selectionPulldownCallback(self, item):
        """
        Notifier Callback for selecting violationTable from the pull down menu
        """
        if item is not None:
            self._violationTable = self.project.getByPid(item)
            if self._violationTable is not None:
                self.displayTableForViolationTable(self._violationTable)
            else:
                self.clearTable()

    def _rtPulldownCallback(self, item):
        """
        Notifier Callback for selecting restraintTable from the pull down menu
        """
        try:
            with undoBlockWithoutSideBar():
                if (_rTable := self.project.getByPid(item)):
                    self._violationTable.setMetadata(_RESTRAINTTABLE, item)
                else:
                    self._violationTable.setMetadata(_RESTRAINTTABLE, None)

        except Exception as es:
            # need to immediately set back to stop error on loseFocus which also fires editingFinished
            showWarning('Violation Table', str(es))

        self.textBox.setText(str(self._violationTable.metadata))

    def _applyComment(self):
        """Set the values in the violationTable
        """
        if self._violationTable:
            comment = self.lineEditComment.text()
            try:
                with undoBlockWithoutSideBar():
                    self._violationTable.comment = comment

            except Exception as es:
                # need to immediately set back to stop error on loseFocus which also fires editingFinished
                showWarning('Violation Table', str(es))

    def _close(self):
        """
        Cleanup the notifiers when the window is closed
        """
        super()._close()
