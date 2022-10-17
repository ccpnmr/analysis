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
__dateModified__ = "$dateModified: 2022-10-17 18:56:01 +0100 (Mon, October 17, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.DataEnum import DataEnum
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
from ccpn.core.lib.Notifiers import Notifier
######## gui/ui imports ########
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
from ccpn.ui.gui.widgets.table.Table import Table


class _NavigateTrigger(DataEnum):
    """
    _NavigateTrigger = 0 # status: No callback, don't navigate to SpectrumDisplay.
    _NavigateTrigger = 1 # status: Callback on single click, navigate to SpectrumDisplay at each table selection.
    _NavigateTrigger = 2 # status: Callback on double click, navigate only with a doubleClick on a table row.
    """
    DISABLED        = 0, guiNameSpaces.Disabled
    SINGLECLICK     = 1, guiNameSpaces.SingleClick
    DOUBLECLICK     = 2, guiNameSpaces.DoubleClick

class _ExperimentalAnalysisTableABC(Table):
    """
    A table to display results from the series Analysis DataTables and interact to source spectra on SpectrumDisplays.
    """
    className = '_TableWidget'
    defaultHidden = []
    _internalColumns = []
    _hiddenColumns = []
    _defaultEditable = False
    _enableDelete = False
    _OBJECT = sv.COLLECTIONPID

    def __init__(self, parent, mainWindow=None, guiModule=None, **kwds):
        """Initialise the widgets for the module.
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

        # initialise the currently attached dataFrame

        self._hiddenColumns = [sv._ROW_UID, sv.COLLECTIONID, sv.PEAKPID, sv.NMRRESIDUEPID, sv.NMRCHAINNAME,
                               sv.NMRRESIDUETYPE, sv.NMRATOMNAMES, sv.SERIESUNIT,
                               sv.SERIESSTEP, sv.SERIESSTEPVALUE, sv.MINIMISER_METHOD, sv.MINIMISER_MODEL, sv.CHISQR,
                               sv.REDCHI, sv.AIC, sv.BIC,
                               sv.MODEL_NAME, sv.NMRRESIDUECODETYPE]
        errCols = [tt for tt in self.columnTexts if sv._ERR in tt]
        self._hiddenColumns += errCols

        # initialise the table
        super().__init__(parent=parent, **kwds)

        self.guiModule = guiModule
        self.moduleParent = guiModule

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()
        self._navigateTrigger = _NavigateTrigger.SINGLECLICK # Default Behaviour
        navigateTriggerName = self.guiModule.getSettings(grouped=False).get(guiNameSpaces.WidgetVarName_NavigateToOpt)
        self.setNavigateToPeakTrigger(navigateTriggerName)
        self._selectCurrentCONotifier = Notifier(self.current, [Notifier.CURRENT], targetName='collections',
                                                 callback=self._currentCollectionCallback, onceOnly=True)

    # =========================================================================================
    # dataFrame
    # =========================================================================================

    @property
    def dataFrame(self):
        return self._dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        self._dataFrame = dataFrame
        self.build(dataFrame)

    def build(self, dataFrame):
        if dataFrame is not None:
            self.updateDf(df=dataFrame)
            self.setHiddenColumns(texts=self._hiddenColumns)

    #=========================================================================================
    # Selection/action callbacks
    #=========================================================================================

    def selectionCallback(self, selected, deselected, selection, lastItem):
        """Set the current collection and navigate to SpectrumDisplay if the trigger is enabled as singleClick. """
        from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiModuleBC import _navigateToPeak, \
            getPeaksFromCollection
        collections = self.getSelectedCollections()
        if len(collections) == 0:
            return
        peaks = getPeaksFromCollection(collections[-1])
        self.current.collections = collections
        self.current.peaks = peaks
        if len(peaks) == 0:
            return
        if self._navigateTrigger == _NavigateTrigger.SINGLECLICK:
            _navigateToPeak(self.guiModule, self.current.peaks[-1])

    def actionCallback(self, selection, lastItem):
        """Perform a navigate to SpectrumDisplay if the trigger is enabled as doubleClick"""
        if self._navigateTrigger == _NavigateTrigger.DOUBLECLICK:
            from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiModuleBC import _navigateToPeak
            _navigateToPeak(self.guiModule, self.current.peaks[-1])

    def setNavigateToPeakTrigger(self, trigger):
        """
        Set the navigation Trigger to single/Double click or Disabled when selecting a row on the table.
        :param trigger: int or str, one of _NavigateTrigger value or name. See _NavigateTrigger for details.
        :return: None
        """
        for enumTrigger in _NavigateTrigger:
            if enumTrigger == trigger or enumTrigger.description == trigger:
                self._navigateTrigger = enumTrigger
                return

    #=========================================================================================
    # Handle drop events
    #=========================================================================================

    def _processDroppedItems(self, data):
        """
        CallBack for Drop events
        """
        pids = data.get('pids', [])
        # self._handleDroppedItems(pids, KlassTable, self.moduleParent._modulePulldown)
        getLogger().warning('Drop not yet implemented for this module.')

    def _close(self):
        """
        Cleanup the notifiers when the window is closed
        """
        pass


    #=========================================================================================
    # Table context menu
    #=========================================================================================

    # add edit/add parameters to meta-data table

    def addTableMenuOptions(self, menu):
        super().addTableMenuOptions(menu)
        editCollection = menu.addAction('Edit Collection', self._editCollection)
        menu.moveActionAboveName(editCollection, 'Export Visible Table')

    def _editCollection(self):
        from ccpn.ui.gui.popups.CollectionPopup import CollectionPopup
        collections = self.getSelectedCollections()
        if len(collections)>0:
            co = collections[-1]
            if co is not None:
                popup = CollectionPopup(self, mainWindow=self.mainWindow, obj=co, editMode=True)
                popup.exec()
                popup.raise_()

    def getSelectedCollections(self):
        selectedRowsDf = self.selectedRows()
        collections = set()
        for ix, selectedRow in selectedRowsDf.iterrows():
            coPid = selectedRow[sv.COLLECTIONPID]
            co = self.project.getByPid(coPid)
            collections.add(co)
        return list(collections)

    def _currentCollectionCallback(self, *args):
        # select collection on table.
        backendHandler = self.guiModule.backendHandler
        if not backendHandler.inputCollection:
            return
        pids = []
        for collection in self.current.collections:
            if collection in backendHandler.inputCollection.items:
                pids.append(collection.pid)
        self.selectRowsByValues(pids, headerName=sv.COLLECTIONPID)

    def clearSelection(self):
        super().clearSelection()
        self.current.collections = []
        self.guiModule.updateAll()

class TablePanel(GuiPanel):

    position = 1
    panelName = 'TablePanel'
    TABLE = _ExperimentalAnalysisTableABC

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)

    def initWidgets(self):
        row = 0
        # Label(self, 'TablePanel', grid=(row, 0))
        self.mainTable = self.TABLE(self,
                                    mainWindow=self.mainWindow,
                                    guiModule = self.guiModule,
                                    grid=(0, 0), gridSpan=(1, 2))
    
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
