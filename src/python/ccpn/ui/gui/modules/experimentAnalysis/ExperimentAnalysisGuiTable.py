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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-05-26 12:38:12 +0100 (Thu, May 26, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================


import pandas as pd

######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.GuiTable import GuiTable, _getValueByHeader, _selectRowsOnTable, _makeTipText, _getHiddenColumns
import ccpn.ui.gui.widgets.GuiTable as gt
from ccpn.ui.gui.widgets.Column import ColumnClass, Column


class _ExperimentalAnalysisTableABC(gt.GuiTable):
    """
    Table containing reference information. Scores and values are calculated on the fly from the main dataframe
    stored in datasets.
    """
    className = 'ExperimentalAnalysisTable'
    OBJECT = 'object'
    TABLE = 'table'

    _columnsDefs = {
        '#':      {gt.NAME: '#',
                  gt.GETTER: lambda row: _getValueByHeader(row, '#'),
                  gt.TIPTEXT: _makeTipText('#', "Enumerated entry value."),
                  gt.WIDTH: 40,
                  gt.HIDDEN: False
                  },
        }

    def __init__(self, parent, guiModule, dataFrame, **kwds):
        self.mainWindow = guiModule.mainWindow
        self.dataFrameObject = None

        super().__init__(parent=parent, mainWindow=self.mainWindow, dataFrameObject=None,  # class collating table and objects and headings,
                        setLayout=True, autoResize=True, multiSelect=True,
                        enableMouseMoveEvent=False,
                        selectionCallback=self.selection,
                        actionCallback=self.selection,
                        checkBoxCallback=self.actionCheckBox,  grid=(0, 0))
        self.guiModule = guiModule
        self.current = self.guiModule.current
        self._columns = ColumnClass([])
        for colName, defs in self._columnsDefs.items():
            columnObject = Column(colName,defs.get(gt.GETTER), tipText= defs.get(gt.TIPTEXT),
                                  setEditValue= defs.get(gt.SETTER), format=defs.get(gt.FORMAT))
            self._columns.columns.append(columnObject)
        self._hiddenColumns = _getHiddenColumns(self)
        self._dataFrame = dataFrame
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self.setMinimumHeight(100)
        self._selectOverride = True # otherwise very odd behaviour
        gt._resizeColumnWidths(self)

    @property
    def dataFrame(self):
        return self._dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self._dataFrame = dataFrame
        self.build(dataFrame)

    def build(self, dataFrame):
        self.clear()
        self.dfo = self.getDataFromFrame(table=self, df=dataFrame, colDefs=self._columns)
        self.setTableFromDataFrameObject(dataFrameObject=self.dfo, columnDefs=self._columns)
        self.setHiddenColumns(_getHiddenColumns(self))

    def mousePressEvent(self, event):
        if self.itemAt(event.pos()) is None:
            self.clearSelection()
            return
        else:
            GuiTable.mousePressEvent(self, event)

    def clearSelection(self):
        self.moduleParent.matchingTable.clean()
        if self.current:
            self.current.peaks = []
        self.selectionModel().clearSelection()
        self.moduleParent.hitScatterPlot.selectByPids([])

    def selection(self, *args):
        pass

    def action(self, *args):
        pass

    def actionCheckBox(self, data):
        pass


    def _rebuild(self):
        self.build(self._dataFrame)

    def _setContextMenu(self, enableExport=True, enableDelete=True):
        """Subclass guiTable to add new items to context menu
        """
        super()._setContextMenu(enableExport=enableExport, enableDelete=enableDelete)
        _actions = self.tableMenu.actions()
        if _actions:
            _topMenuItem = _actions[0]
            _topSeparator = self.tableMenu.insertSeparator(_topMenuItem)
            pass

    def _exportRawData(self):
        if self.moduleParent:
            self.moduleParent._exportRawData()


class TablePanel(GuiPanel):

    position = 1
    panelName = 'TablePanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setMaximumHeight(100)

    def initWidgets(self):
        row = 0
        Label(self, 'Test TablePanel', grid=(row, 0))
        self.mainTable = _ExperimentalAnalysisTableABC(self,
                                                     dataFrame=pd.DataFrame(),
                                                     guiModule = self.guiModule, grid=(0, 0))
        self.mainTable.dataFrame = pd.DataFrame([1, 2, 3, 4], columns=['#'])
