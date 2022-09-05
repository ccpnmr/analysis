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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-08-25 16:21:44 +0100 (Thu, August 25, 2022) $"
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
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
from ccpn.core.Peak import Peak
######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Column import ColumnClass, Column
import ccpn.ui.gui.widgets.GuiTable as gt
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.lib._SimplePandasTable import _updateSimplePandasTable, _SimplePandasTableView, _SearchTableView, _clearSimplePandasTable


class _ExperimentalAnalysisTableABC(gt.GuiTable):
    """
    Table containing fitting results.
    Wrapper GuiTable built from the backend outputDataTable.
    See SeriesTablesBC for more information about the underlined dataframe.
    """

    className = guiNameSpaces.TablePanel
    defaultHidden = []
    _internalColumns = []
    _hiddenColumns = []

    def __init__(self, parent, guiModule,  **kwds):
        self.mainWindow = guiModule.mainWindow
        self.dataFrameObject = None
        super().__init__(parent=parent, mainWindow=self.mainWindow, dataFrameObject=None,  # class collating table and objects and headings,
                        setLayout=True, autoResize=True, multiSelect=True,
                        enableMouseMoveEvent=False,
                        selectionCallback=self.selection,
                        actionCallback=self.action,
                        checkBoxCallback=self.actionCheckBox,  grid=(0, 0))
        self.guiModule = guiModule
        self.current = self.guiModule.current
        self._columns = None
        self._hiddenColumns = []
        self._dataFrame = None
        self._dataFrameObject = None
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustIgnored)
        self._selectOverride = True # otherwise very odd behaviour
        self.setMinimumWidth(200)
        self._navigateToPeakOnSelection = True

    @property
    def dataFrame(self):
        return self._dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self._dataFrame = dataFrame
        self.build(dataFrame)

    def build(self, dataFrame):
        if dataFrame is not None:
            self.setData(dataFrame)

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        print('Not implemented')

    def _close(self):
        """
        Cleanup the notifiers when the window is closed
        """
        pass

    def mousePressEvent(self, event):
        self._currentIndex = self.indexAt(event.pos())
        if  self._currentIndex is None:
            self.clearSelection()
            return
        else:
            super().mousePressEvent(event)

    def clearSelection(self):
        super().clearSelection()
        self.current.collections = []

    def getSelectedObjects(self, fromSelection=None):
        """
        :param fromSelection:
        :return: get a list of table objects. If the table has a header called pid, the object is a ccpn Core obj like Peak,
         otherwise is a Pandas series object corresponding to the selected row(s).
        """
        from collections import defaultdict
        model = self.selectionModel()
        # selects all the items in the row
        selection = fromSelection if fromSelection else model.selectedIndexes()
        if selection:
            selectedObjects = []
            valuesDict = defaultdict(list)
            for iSelect in selection:
                row = iSelect.row()
                col = iSelect.column()
                if self.dataFrame is not None and len(self.dataFrame.columns)>col: #just in case
                    h = self.dataFrame.columns[col]
                    v = self.dataFrame.iloc[row, col]
                    valuesDict[h].append(v)
            if valuesDict:
                selectedObjects = [row for i, row in pd.DataFrame(valuesDict).iterrows()]
            return selectedObjects
        else:
            return []

    def getSelectedCollections(self):
        selectedObjs = self.getSelectedObjects()

        collections = set()
        for selectedRow in selectedObjs:
            coPid = selectedRow[sv.COLLECTIONPID]
            co = self.project.getByPid(coPid)
            collections.add(co)
        return list(collections)

    def getPeaksFromCollection(self, collection):
        peaks = set()
        for item in collection.items:
            if isinstance(item, Peak):
                peaks.add(item)
        return list(peaks)

    def selection(self, data, *args):
        """
        :param args:
        :return:
        """
        collections = self.getSelectedCollections()
        peaks = set()
        for collection in collections:
            peaks.update(self.getPeaksFromCollection(collection))
        self.current.collections = collections
        self.current.peaks = list(peaks)
        if self._navigateToPeakOnSelection:
            self._navigateToPeak()

    def action(self, *args):
        self._navigateToPeak()

    def _navigateToPeak(self):
        from ccpn.ui.gui.lib.StripLib import navigateToPositionInStrip, _getCurrentZoomRatio

        # peaks should have been set to current by the click
        peaks = self.current.peaks
        if len(peaks)== 0:
            return
        peak = peaks[-1]
        # get the display from settings
        appearanceTab = self.guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_GeneralAppearance)
        displayWidget = appearanceTab.getWidget(guiNameSpaces.WidgetVarName_SpectrumDisplSelection)
        if displayWidget is None:
            getLogger().debug(f'Not found widget in Appearance tab {guiNameSpaces.WidgetVarName_SpectrumDisplSelection}')
            return
        displays = displayWidget.getDisplays()
        for display in displays:
            for strip in display.strips:
                widths = _getCurrentZoomRatio(strip.viewRange())
                navigateToPositionInStrip(strip=strip, positions=peak.position, widths=widths)

    def actionCheckBox(self, data):
        pass


    def _setContextMenu(self):
        """Subclass guiTable to add new items to context menu
        """
        super()._setContextMenu()

        _actions = self.tableMenu.actions()
        if _actions:
            _topMenuItem = _actions[0]
            self.tableMenu.insertSeparator(_topMenuItem)
            editCollection = self.tableMenu.addAction('Edit Collection', self._editCollection)
            self.tableMenu.moveActionAboveName(editCollection, 'Export Visible Table')

    def _editCollection(self):
        from ccpn.ui.gui.popups.CollectionPopup import CollectionPopup
        collections = self.getSelectedCollections()
        if len(collections)>0:
            co = collections[-1]
            if co is not None:
                popup = CollectionPopup(self, mainWindow=self.mainWindow, obj=co, editMode=True)
                popup.exec()
                popup.raise_()


class TablePanel(GuiPanel):

    position = 1
    panelName = 'TablePanel'
    TABLE = _ExperimentalAnalysisTableABC

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)


    def initWidgets(self):
        row = 0
        Label(self, 'TablePanel', grid=(row, 0))
        self.mainTable = self.TABLE(self,
                                     mainWindow=self.mainWindow,
                                     guiModule = self.guiModule, grid=(0, 0))

    
    def setInputData(self, dataFrame):
        """Provide the DataFrame to populate the table."""
        self.mainTable.dataFrame = dataFrame

    def updatePanel(self, *args, **kwargs):
        getLogger().info('Updating Relaxation table panel')
        dataFrame = self.guiModule.getGuiOutputDataFrame()
        self.setInputData(dataFrame)

    def clearData(self):
        self.mainTable.dataFrame = None
        self.mainTable.clearTable()
