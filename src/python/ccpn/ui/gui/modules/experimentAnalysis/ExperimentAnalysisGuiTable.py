#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
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
__dateModified__ = "$dateModified: 2023-05-28 11:06:25 +0100 (Sun, May 28, 2023) $"
__version__ = "$Revision: 3.1.1 $"
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
import numpy as np
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
    _enableSearch = True
    _enableCopyCell = True
    _enableExport = True

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
        # initialise the table
        super().__init__(parent=parent, **kwds)

        self._hiddenColumns = [sv._ROW_UID, sv.COLLECTIONID, sv.PEAKPID, sv.NMRRESIDUEPID, sv.NMRCHAINNAME,
                               sv.NMRRESIDUETYPE, sv.NMRATOMNAMES, sv.SERIESUNIT, sv.SPECTRUMPID,
                               sv.VALUE, sv.VALUE_ERR,
                               sv.SERIES_STEP_X, sv.SERIES_STEP_Y, sv.MINIMISER_METHOD, sv.MINIMISER_MODEL, sv.CHISQR,
                               sv.REDCHI, sv.AIC, sv.BIC,
                               sv.MODEL_NAME, sv.NMRRESIDUECODETYPE]
        self._internalColumns = [sv.INDEX]
        errCols = [tt for tt in self.headerColumnMenu.columnTexts if sv._ERR in tt]
        self._hiddenColumns += errCols
        self.headerColumnMenu.setDefaultColumns(self._hiddenColumns, update=False)
        self.headerColumnMenu.setInternalColumns(self._internalColumns)
        self.guiModule = guiModule
        self.moduleParent = guiModule
        self._selectionHeader =sv.COLLECTIONPID

        # Initialise the notifier for processing dropped items
        self._postInitTableCommonWidgets()
        self._navigateTrigger = _NavigateTrigger.SINGLECLICK # Default Behaviour
        navigateTriggerName = self.guiModule.getSettings(grouped=False).get(guiNameSpaces.WidgetVarName_NavigateToOpt)
        self.setNavigateToPeakTrigger(navigateTriggerName)
        self._selectCurrentCONotifier = Notifier(self.current, [Notifier.CURRENT], targetName='collections',
                                                 callback=self._currentCollectionCallback, onceOnly=True)

        self.sortingChanged.connect(self._tableSortingChangedCallback)
        self.tableChanged.connect(self._tableChangedCallback)

    # =========================================================================================
    # dataFrame
    # =========================================================================================

    def _tableSortingChangedCallback(self, *args):
        """   Fire a notifier for other widgets to refresh their ordering (if needed). """
        self.guiModule.mainTableSortingChanged.emit()

    def _tableChangedCallback(self, *args):
        """   Fire a notifier for other widgets to refresh their ordering (if needed). """
        self.guiModule.mainTableSortingChanged.emit()

    @property
    def dataFrame(self):
        return self._dataFrame

    @dataFrame.setter
    def dataFrame(self, dataFrame):
        selectedRows = self.selectedRows()
        self._dataFrame = dataFrame
        self.build(dataFrame)
        if self._selectionHeader in self.headerColumnMenu.columnTexts and len(selectedRows)>0:
            selPids = selectedRows[sv.COLLECTIONPID].values
            self.selectRowsByValues(selPids, sv.COLLECTIONPID, scrollToSelection=True, doCallback=True)

    def build(self, dataFrame):
        if dataFrame is not None:
            self.updateDf(df=dataFrame)
            self.headerColumnMenu.setDefaultColumns(self._hiddenColumns)
            self._setBlankModelColumns()
            self._hideExcludedColumns()


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
        if self.current.collection is None:
            self.clearSelection()
            return
        df = self.guiModule.getVisibleDataFrame(includeHiddenColumns=True)
        if df is None:
            return
        pids = [co.pid for co in self.current.collections]
        print(pids)
        # filtered = df[df[sv.COLLECTIONPID].isin(pids)]
        # if filtered.empty:
        #     return

        self.selectRowsByValues(pids, headerName=sv.COLLECTIONPID)


    ## Convient Methods to toggle groups of headers.
    ## TableGrouppingHeaders = [_Assignments, _SeriesSteps, _Calculation, _Fitting, _Stats, _Errors]
    ## Called from settings Pannel in an autogenerated fashion, don't change signature.

    def _hideExcludedColumns(self):
        """Remove columns from table which contains the prefix excluded_ """
        headers = []
        columnTexts = self.headerColumnMenu.columnTexts
        for columnText in columnTexts:
            if columnText.startswith(sv.EXCLUDED_):
                headers.append(columnText)
        self._setVisibleColumns(headers, False)

    def _setBlankModelColumns(self):
        # if a blank model: toggle the columns from table (no point in showing empty columns)
        fitModel = self.guiModule.backendHandler.currentFittingModel
        calModel = self.guiModule.backendHandler.currentCalculationModel
        apperanceTab = self.guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_GeneralAppearance)
        tableHeaderWidget = apperanceTab.getWidget(guiNameSpaces.WidgetVarName_TableView)
        if tableHeaderWidget is not None:
            if fitModel and fitModel.ModelName == sv.BLANKMODELNAME:
                # tableHeaderWidget.untickTexts([guiNameSpaces._Fitting, guiNameSpaces._Stats])
                self._toggleFittingHeaders(False)
                self._toggleStatsHeaders(False)
                self._toggleFittingErrorsHeaders(False)
            if calModel and calModel.ModelName == sv.BLANKMODELNAME:
                # tableHeaderWidget.untickTexts([guiNameSpaces._Calculation])
                self._toggleCalculationHeaders(False)
                self._toggleCalculationErrorsHeaders(False)

    def _setVisibleColumns(self, headers, setVisible):
        for header in headers:
            if setVisible:
                self.headerColumnMenu._showColumnName(str(header))
            else:
                self.headerColumnMenu._hideColumnName(str(header))

    def _toggleSeriesStepsHeaders(self, setVisible=True):
        """ Show/Hide the rawData columns"""
        headers = self.guiModule.backendHandler._getSeriesStepValues()
        # need to include also the headers which are duplicates and include an _ (underscore at the end)
        extraHeaders = []
        for header in headers:
            for columnHeader in self.headerColumnMenu.columnTexts:
                if str(columnHeader).startswith(str(header)) and sv.SEP in columnHeader :
                    extraHeaders.append(columnHeader)
        headers += extraHeaders
        self._setVisibleColumns(headers, setVisible)

    def _toggleAssignmentsHeaders(self, setVisible=True):
        """ Show/Hide the assignments columns"""
        headers = sv.AssignmentPropertiesHeaders
        self._setVisibleColumns(headers, setVisible)

    def _toggleErrorsHeaders(self, setVisible=True):
        """ Show/Hide the Fitting/Calculation error columns"""
        headers = [tt for tt in self.headerColumnMenu.columnTexts if sv._ERR in tt]
        self._setVisibleColumns(headers, setVisible)

    def _toggleCalculationErrorsHeaders(self, setVisible=True):
        """ Show/Hide the Calculation error columns"""
        headers = []
        calcModel = self.guiModule.backendHandler.currentCalculationModel
        if calcModel is not None:
            headers = calcModel.modelArgumentErrorNames
            headers = calcModel.modelArgumentErrorNames
        self._setVisibleColumns(headers, setVisible)

    def _toggleFittingErrorsHeaders(self, setVisible=True):
        """ Show/Hide the Fitting error columns"""
        headers = []
        fittingModel = self.guiModule.backendHandler.currentFittingModel
        if fittingModel is not None:
            headers = fittingModel.modelArgumentErrorNames
        self._setVisibleColumns(headers, setVisible)

    def _toggleCalculationHeaders(self, setVisible=True):
        """ Show/Hide the Calculation columns"""
        headers = []
        calcModel = self.guiModule.backendHandler.currentCalculationModel
        if calcModel is not None:
            headers = calcModel.modelArgumentNames
        self._setVisibleColumns(headers, setVisible)

    def _toggleFittingHeaders(self, setVisible=True):
        """ Show/Hide the Fitting columns"""
        headers = []
        fittingModel = self.guiModule.backendHandler.currentFittingModel
        if fittingModel is not None:
            headers = fittingModel.modelArgumentNames
        self._setVisibleColumns(headers, setVisible)

    def _toggleStatsHeaders(self, setVisible=True):
        """ Show/Hide the Fitting stats columns"""
        headers = []
        fittingModel = self.guiModule.backendHandler.currentFittingModel
        if fittingModel is not None:
            headers = fittingModel.modelStatsNames
        self._setVisibleColumns(headers, setVisible)


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
        dataFrame = self.guiModule._getGuiResultDataFrame()
        self.setInputData(dataFrame)



def clearData(self):
        self.mainTable.dataFrame = None
        self.mainTable.clearTable()
