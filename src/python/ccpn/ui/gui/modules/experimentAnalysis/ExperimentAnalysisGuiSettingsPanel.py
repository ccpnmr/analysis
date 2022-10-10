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
__dateModified__ = "$dateModified: 2022-10-10 16:26:28 +0100 (Mon, October 10, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

"""
This module contains the GUI Settings panels.
"""

from collections import OrderedDict as od
from ccpn.framework.lib.experimentAnalysis.SeriesAnalysisABC import ALL_GROUPINGNMRATOMS
from ccpn.util.Logging import getLogger
import numpy as np
from ccpn.util.isotopes import name2IsotopeCode
######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.widgets.Label import Label, DividerLabel
import ccpn.ui.gui.widgets.CompoundWidgets as compoundWidget
import ccpn.ui.gui.widgets.PulldownListsForObjects as objectPulldowns
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons, EditableRadioButtons
import ccpn.ui.gui.widgets.SettingsWidgets as settingWidgets
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Label import maTex2Pixmap
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as seriesVariables
from ccpn.ui.gui.widgets.HLine import LabeledHLine, HLine
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER, setColourScheme, FONTLIST, ZPlaneNavigationModes
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBar import PanelUpdateState
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.ui.gui.widgets.SettingsWidgets import ALL, UseCurrent

SettingsWidgeMinimumWidths =  (180, 180, 180)
SettingsWidgetFixedWidths = (200, 350, 350)

DividerColour = getColours()[DIVIDER]

class GuiSettingPanel(Frame):
    """
    Base class for GuiSettingPanel.
    A panel is Frame which will create a tab in the Gui Module settings
    Tabs are not added automatically. They need to be manually added from the SettingsHandler.

    Macros from IPython Console: get the settingsPanel, e.g. for the calculation Tab:
        guiModule = ui.getByGid('MO:Relaxation (Alpha)')    ## get the guiModule
        guiModule.settingsPanelHandler.tabs                 ## get all tabs as dict. Key the tab name , value the Obj
        calculationPanel = guiModule.settingsPanelHandler.tabs.get('Calculation')
        allSettings = calculationPanel.getSettingsAsDict()  ## Key the variable name , value the widget current value
    """

    tabPosition = -1
    tabName = 'tab'
    tabTipText = 'What this panel will allow to do'

    def __init__(self, guiModule,  *args, **Framekwargs):
        Frame.__init__(self, setLayout=True, **Framekwargs)
        self.guiModule = guiModule
        self.getLayout().setAlignment(QtCore.Qt.AlignTop)
        self._moduleSettingsWidget = None # the widgets the collects all autogen widgets
        self.widgetDefinitions = self.setWidgetDefinitions()
        self.initWidgets()
        self.guiModule.settingsChanged.connect(self._settingsChangedCallback)

    def setWidgetDefinitions(self) -> od:
        """ Override in subclass. Define the widgets in an orderedDict.
        See ccpn.ui.gui.widgets.SettingsWidgets.ModuleSettingsWidget. Example:
            od((
                (WidgetVarName,
                {'label': Label_toShow,
                'type': WidgetClass-not-init,
                'kwds': {'text': Label_toShow,
                       'height': 30,
                       'gridSpan': (1, 2),
                       'tipText': TipText}})
            ))
        """
        return od()

    def initWidgets(self):
        mainWindow = self.guiModule.mainWindow
        self._moduleSettingsWidget = settingWidgets.ModuleSettingsWidget(parent=self, mainWindow=mainWindow,
                                                                         settingsDict=self.widgetDefinitions,
                                                                         grid=(0, 0))
        self._moduleSettingsWidget.getLayout().setAlignment(QtCore.Qt.AlignLeft)
        Spacer(self, 0, 2, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(1, 0), gridSpan=(1, 1))

    def getWidget(self, name):
        if self._moduleSettingsWidget is not None:
            w = self._moduleSettingsWidget.getWidget(name)
            return w

    def getSettingsAsDict(self):
        settingsDict = {}
        for varName, widget in self._moduleSettingsWidget.widgetsDict.items():
            try:
                settingsDict[varName] = widget._getSaveState()
            except Exception as e:
                getLogger().warn('Could not find get for: varName, widget',  varName, widget, e)
        return settingsDict

    def _setUpdatedDetectedState(self):
        """ set update detected on toolbar icons. """
        toolbar = self.guiModule.panelHandler.getToolBarPanel()
        if toolbar:
            toolbar.setUpdateState(PanelUpdateState.DETECTED)

    def _commonCallback(self, *args):
        """ _commonCallback to all tabs. Usually to set the updateState icon"""
        self._setUpdatedDetectedState()
        self.guiModule.settingsChanged.emit(self.getSettingsAsDict())

    def _settingsChangedCallback(self, settingsDict, *args):
        """Callback when a core settings has changed.
        E.g.: the fittingModel and needs to update some of the appearance Widgets
        :param settingsDict: dict with settings {widgetVarName:value}
        To be Subclassed"""
        self._setUpdatedDetectedState()

    def _getCoreSettings(self):
        """
        Get a dict of core settings used in the generation of Fitting/calculation data.
        Used to set as metaData in the OutputDataTable
        :return: orderedDict

        NIY

        """

        dd = {
            'spectrumGroups' : [],
            'inputDataTables' : [],
            'calculationPeakProperty' : '',
            'calculationOption' : '',
            'filteringNmrGroup' : '',
            'excludedNmrResidues' : [],
            'fittingOptimiser' : '',
            'fittingErrorMethod' : '',
            'fittingModel' : '',
            'thresholdValueMode' : '',
            'thresholdValue' : ''
            }
        return dd
        

TABPOS = 0
## Make a default tab ordering as they are added to this file.
## Note: Tabs are not added automatically.
## Tabs are added from the SettingsHandler defined in the main GuiModule which allows more customisation in subclasses.


#####################################################################
#####################   InputData Panel   ###########################
#####################################################################

class GuiInputDataPanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = guiNameSpaces.Label_InputData
    tabTipText = guiNameSpaces.TipText_GuiInputDataPanel

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiSettingPanel.__init__(self, guiModule, *args, **Framekwargs)

        self._limitSelectionOnInputData() ## This constrain might be removed on future implementations

    def setWidgetDefinitions(self):
        """ Define the widgets in a dict."""
        backend = self.guiModule.backendHandler
        self.widgetDefinitions = od((
            (guiNameSpaces.WidgetVarName_SpectrumGroupsSeparator,
             {'label': guiNameSpaces.Label_SpectrumGroups,
                                 'type': LabeledHLine,
                                 'kwds': {'text': guiNameSpaces.Label_SpectrumGroups,
                                          # 'height': 30,
                                          'colour':DividerColour,
                                          'gridSpan':(1,2),
                                          'tipText': guiNameSpaces.TipText_SpectrumGroupsSeparator}}),
            (guiNameSpaces.WidgetVarName_SpectrumGroupsSelection,
             {'label':  guiNameSpaces.Label_SelectSpectrumGroups,
                                'tipText': guiNameSpaces.TipText_SpectrumGroupSelectionWidget,
                                'callBack': None,
                                'type': settingWidgets.SpectrumGroupSelectionWidget,
                                'kwds': {
                                        'labelText': guiNameSpaces.Label_SelectSpectrumGroups,
                                        'tipText': guiNameSpaces.TipText_SpectrumGroupSelectionWidget,
                                        'displayText': [],
                                        'defaults': [],
                                        'standardListItems':[],
                                        'objectName': guiNameSpaces.WidgetVarName_SpectrumGroupsSelection,
                                        'fixedWidths': SettingsWidgetFixedWidths}, }),
            (guiNameSpaces.WidgetVarName_DataTableName,
             {'label': guiNameSpaces.Label_InputDataTableName,
                                'tipText': guiNameSpaces.TipText_dataTableNameSelectionWidget,
                                'callBack': None,
                                'enabled': True,
                                'type': compoundWidget.EntryCompoundWidget,
                                '_init': None,
                                'kwds': {'labelText': guiNameSpaces.Label_InputDataTableName,
                                         'entryText': sv.SERIESANALYSISINPUTDATA,
                                         'tipText': guiNameSpaces.TipText_dataTableNameSelectionWidget,
                                         'fixedWidths': SettingsWidgetFixedWidths}, }),
            (guiNameSpaces.WidgetVarName_CreateDataTable,
             {'label': guiNameSpaces.Label_CreateInput,
                                'tipText': guiNameSpaces.TipText_createInputdataTableWidget,
                                'callBack': self._createInputDataTableCallback,
                                'type': compoundWidget.ButtonCompoundWidget,
                                '_init': None,
                                'kwds': {'labelText': guiNameSpaces.Label_CreateInput,
                                         'text': 'Create', # this is the Button name
                                         'hAlign': 'left',
                                         'tipText': guiNameSpaces.TipText_createInputdataTableWidget,
                                         'fixedWidths': SettingsWidgetFixedWidths}}),
            (guiNameSpaces.WidgetVarName_DataTableSeparator,
             {'label': guiNameSpaces.Label_DataTables,
                                 'type': LabeledHLine,
                                 'kwds': {'text':guiNameSpaces.Label_DataTables,
                                          # 'height': 30,
                                          'gridSpan':(1,2),
                                          'colour': DividerColour,
                                          'tipText': guiNameSpaces.TipText_DataTableSeparator}}),
            (guiNameSpaces.WidgetVarName_DataTablesSelection,
             {'label': guiNameSpaces.Label_SelectDataTable,
              'tipText': guiNameSpaces.TipText_DataTableSelection,
              'type': settingWidgets._SeriesInputDataTableSelectionWidget,
              'kwds': {
                  'objectWidgetChangedCallback':self._addInputDataCallback,
                  'labelText': guiNameSpaces.Label_SelectDataTable,
                  'tipText': guiNameSpaces.TipText_DataTableSelection,
                  'displayText': [],
                  'defaults': [],
                  'standardListItems': [],
                  'objectName': guiNameSpaces.WidgetVarName_DataTablesSelection,
                  'fixedWidths': SettingsWidgetFixedWidths}, }),

            (guiNameSpaces.WidgetVarName_OutPutDataTableName,
             {'label': guiNameSpaces.Label_OutputDataTableName,
              'tipText': guiNameSpaces.TipText_OutputDataTableName,
              'callBack': None,
              'enabled': True,
              'type': compoundWidget.EntryCompoundWidget,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_OutputDataTableName,
                       'entryText': backend.outputDataTableName,
                       'tipText': guiNameSpaces.TipText_OutputDataTableName,
                       'fixedWidths': SettingsWidgetFixedWidths},}),
            (guiNameSpaces.WidgetVarName_FitInputData,
             {'label': guiNameSpaces.Label_FitInput,
              'tipText': guiNameSpaces.TipText_createOutputdataTableWidget,
              'callBack': self._fitAndFecthOutputData,
              'type': compoundWidget.ButtonCompoundWidget,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_FitInput,
                       'text': 'Fit',  # this is the Button name
                       'hAlign': 'left',
                       'tipText': guiNameSpaces.TipText_createOutputdataTableWidget,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (guiNameSpaces.WidgetVarName_OutputDataTableSeparator,
             {'label': guiNameSpaces.Label_OutputDataTable,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_OutputDataTable,
                       # 'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': guiNameSpaces.TipText_OutputDataTableSeparator}}),

            (guiNameSpaces.WidgetVarName_OutputDataTablesSelection,
             {'label': guiNameSpaces.Label_SelectOutputDataTable,
              'tipText': guiNameSpaces.TipText_OutputDataTableSelection,
              'type': objectPulldowns.DataTablePulldown,
              'kwds': {'labelText': guiNameSpaces.Label_SelectOutputDataTable,
                       'tipText': guiNameSpaces.TipText_OutputDataTableSelection,
                       'filterFunction': self._filterOutputDataOnPulldown,
                       'showSelectName':True,
                       'objectName': guiNameSpaces.WidgetVarName_OutputDataTablesSelection,
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            ))
        return self.widgetDefinitions

    def _addInputDataCallback(self, *args):

        backend = self.guiModule.backendHandler
        dataTablePids = self.getSettingsAsDict().get(guiNameSpaces.WidgetVarName_DataTablesSelection, [])
        if not dataTablePids:
            self.guiModule.backendHandler.clearInputDataTables()
            getLogger().info(f'{self.guiModule.className}:{self.tabName}. Cleaned inputDataTables')
            return
        for pid in dataTablePids:
            obj = self.guiModule.project.getByPid(pid)
            if obj:
                backend.addInputDataTable(obj)
                getLogger().info(f'{self.guiModule.className}:{self.tabName}. {obj} added to inputDataTables')

    def _fitAndFecthOutputData(self, *args):
        getLogger().info('Starting fit')
        backend = self.guiModule.backendHandler
        name = self.getSettingsAsDict().get(guiNameSpaces.WidgetVarName_OutPutDataTableName, sv.SERIESANALYSISOUTPUTDATA)
        backend.outputDataTableName = name
        if len(backend.inputDataTables) == 0:
            dataTablePids = self.getSettingsAsDict().get(guiNameSpaces.WidgetVarName_DataTablesSelection, [])
            if len(dataTablePids) == 0:
                getLogger().warning('Cannot create any output DataTable. Select an input DataTable first.')
            for pid in dataTablePids:
                obj = self.guiModule.project.getByPid(pid)
                if obj:
                    backend.addInputDataTable(obj)
        outputDataTable = backend.fitInputData()
        outputPulldown = self.getWidget(guiNameSpaces.WidgetVarName_OutputDataTablesSelection)
        if outputPulldown:
            outputPulldown.update() #there seems to be a bug on pulldown not updating straight-away
            outputPulldown.select(outputDataTable.pid)
        self.guiModule.updateAll()

    def _filterOutputDataOnPulldown(self, pids, *args):
        dataTables = self.guiModule.project.getByPids(pids)
        # filter out only the SeriesAnalysisDtaTable by its metadata
        filteredDataTables = []
        for dataTable in dataTables:
            if dataTable.getMetadata(sv.DATATABLETYPE) == sv.SERIESANALYSISOUTPUTDATA:
                filteredDataTables.append(dataTable)
        pids = self.guiModule.project.getPidsByObjects(filteredDataTables)
        return pids


    def _limitSelectionOnInputData(self):
        "Allow only one selection on SpectrumGroups and DataTable. "
        sgSelectionWidget = self.getWidget(guiNameSpaces.WidgetVarName_SpectrumGroupsSelection)
        dtSelectionWidget = self.getWidget(guiNameSpaces.WidgetVarName_DataTablesSelection)

        if sgSelectionWidget:
            sgSelectionWidget.setMaximumItemSelectionCount(1)
        if dtSelectionWidget:
            dtSelectionWidget.setMaximumItemSelectionCount(1)

    def _createInputDataTableCallback(self, *args):
        """ """
        settingsPanelHandler = self.guiModule.settingsPanelHandler
        inputSettings = settingsPanelHandler.getInputDataSettings()
        sgPids = inputSettings.get(guiNameSpaces.WidgetVarName_SpectrumGroupsSelection, [None])
        if not sgPids:
            showWarning('Select SpectrumGroup', 'Cannot create an input DataTable without a SpectrumGroup')
            return
        spGroup = self.guiModule.project.getByPid(sgPids[-1])
        dataTableName = inputSettings.get(guiNameSpaces.WidgetVarName_DataTableName, None)
        if not spGroup:
            getLogger().warn('Cannot create an input DataTable without a SpectrumGroup. Select one first')
            return
        backend = self.guiModule.backendHandler
        newDataTable = backend.newInputDataTableFromSpectrumGroup(spGroup, dataTableName=dataTableName)
        ## add as first selection in the datatable. clear first.
        dtSelectionWidget = self.getWidget(guiNameSpaces.WidgetVarName_DataTablesSelection)
        if dtSelectionWidget:
            dtSelectionWidget.clearList()
            dtSelectionWidget.updatePulldown()
            dtSelectionWidget.select(newDataTable.pid)

TABPOS += 1


#####################################################################
#####################  Calculation Panel  ###########################
#####################################################################

class GuiCalculationPanel(GuiSettingPanel):
    tabPosition = TABPOS
    tabName = guiNameSpaces.Label_Calculation
    tabTipText = guiNameSpaces.Label_Calculation

    def setWidgetDefinitions(self):
        """Common calculation Widgets"""

        backendHandler = self.guiModule.backendHandler
        self.widgetDefinitions = od((
            (guiNameSpaces.WidgetVarName_CalcPeakProperty,
             {'label': guiNameSpaces.Label_CalcPeakProperty,
              'type': compoundWidget.PulldownListCompoundWidget,
              'callBack': self._commonCallback,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_CalcPeakProperty,
                       'tipText': guiNameSpaces.TipText_CalcPeakProperty,
                       'texts': backendHandler._allowedPeakProperties,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

        ))
        calculationModels = backendHandler.calculationModels
        ## autogenerate labels/tiptexts from the calculationModes.
        extraLabels_ddCalculationsModes = [model.MaTex for modelName, model in
                                           calculationModels.items()]
        tipTexts_ddCalculationsModes = [model.FullDescription for modelName, model in
                                        calculationModels.items()]
        extraLabelPixmaps = [maTex2Pixmap(maTex) for maTex in extraLabels_ddCalculationsModes]
        calculationWidgetDefinitions = od((
            (guiNameSpaces.WidgetVarName_CalcModeSeparator,
             {'label': guiNameSpaces.Label_CalcModeSeparator,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_CalcModeSeparator,
                       'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': guiNameSpaces.TipText_CalculationSeparator}}),
            (guiNameSpaces.WidgetVarName_CalcMode,
             {'label': guiNameSpaces.Label_CalculationOptions,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': None,
              'callBack': self._commonCallback,
              'kwds': {'labelText': guiNameSpaces.Label_CalculationOptions,
                       'hAlign': 'l',
                       'tipText': '',
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {'texts': list(calculationModels.keys()),
                                        'extraLabels': extraLabels_ddCalculationsModes,
                                        'tipTexts': tipTexts_ddCalculationsModes,
                                        'direction': 'v',
                                        'extraLabelIcons': extraLabelPixmaps}}}),
        ))
        ## add the new items to the main dict
        filteringWidgetDefinitions = od((
            (guiNameSpaces.WidgetVarName_FilteringAtomsSeparator,
             {'label': guiNameSpaces.Label_FilteringAtomsSeparator,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_FilteringAtomsSeparator,
                       'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': guiNameSpaces.TipText_FilteringAtomsSeparator}}),
            (guiNameSpaces.WidgetVarName_IncludeGroups,
             {'label': guiNameSpaces.Label_IncludeGroups,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': None,
              'callBack': self._followGroupSelectionCallback,
              'enabled': False,
              'kwds': {'labelText': guiNameSpaces.Label_IncludeGroups,
                       'hAlign': 'l',
                       'tipText': '',
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {'texts': [g.groupType for g in ALL_GROUPINGNMRATOMS.values()],
                                        'tipTexts': [g.groupInfo for g in ALL_GROUPINGNMRATOMS.values()],
                                        'direction': 'v',
                                        'selectedInd': 4,
                                        }}}),

            (guiNameSpaces.WidgetVarName_IncludeAtoms,
             {'label': guiNameSpaces.Label_IncludeAtoms,
              'tipText': guiNameSpaces.TipText_IncludeAtoms,
              'type': settingWidgets.UniqueNmrAtomNamesSelectionWidget,
              'postInit': self._setFixedHeightPostInit,
              'callBack': self._commonCallback,
              'enabled': False,
              'kwds': {
                  'labelText': guiNameSpaces.Label_IncludeAtoms,
                  'tipText': guiNameSpaces.TipText_IncludeAtoms,
                  'objectWidgetChangedCallback': self._commonCallback,
                  'pulldownCallback': self._commonCallback,
                  'texts': seriesVariables.DEFAULT_FILTERING_ATOMS,
                  'defaults': seriesVariables.DEFAULT_FILTERING_ATOMS,
                  'objectName': guiNameSpaces.WidgetVarName_IncludeAtoms,
                  'standardListItems': [],
                  'fixedWidths': SettingsWidgetFixedWidths
              }}),
            (guiNameSpaces.WidgetVarName_ExcludeResType,
             {'label': guiNameSpaces.Label_ExcludeResType,
              'tipText': guiNameSpaces.TipText_ExcludeResType,
              'postInit': self._setFixedHeightPostInit,
              'enabled': False,
              'type': settingWidgets.UniqueNmrResidueTypeSelectionWidget,
              'callBack': self._commonCallback,
              'kwds': {
                  'labelText': guiNameSpaces.Label_ExcludeResType,
                  'tipText': guiNameSpaces.TipText_ExcludeResType,
                  'objectWidgetChangedCallback': self._commonCallback,
                  'pulldownCallback': self._commonCallback,
                  'texts': [],
                  'defaults': [],
                  'standardListItems': [],
                  'objectName': guiNameSpaces.WidgetVarName_ExcludeResType,
                  'fixedWidths': SettingsWidgetFixedWidths
              }}),
        ))
        self.widgetDefinitions.update(calculationWidgetDefinitions)
        self.widgetDefinitions.update(filteringWidgetDefinitions)

        return self.widgetDefinitions

    def _setFixedHeightPostInit(self, widget, *args):
        widget.listWidget.setFixedHeight(100)
        widget.setMaximumWidths(SettingsWidgetFixedWidths)
        widget.getLayout().setAlignment(QtCore.Qt.AlignTop)

    def _followGroupSelectionCallback(self, *args):
        pass

    def _setCalculationOptionsToBackend(self):
        """ Update the backend """
        getLogger().info('_setCalculationOptionsToBackend: NIY...')
        pass

    def _commonCallback(self, *args):
        print('setting callback')
        calculationSettings = self.getSettingsAsDict()
        selectedCalcPeakProperty = calculationSettings.get(guiNameSpaces.WidgetVarName_CalcPeakProperty, None)

        selectedCalcModelName = calculationSettings.get(guiNameSpaces.WidgetVarName_CalcMode, None)

        ## update the backend
        backend = self.guiModule.backendHandler
        currentCalculationModel = backend.currentCalculationModel
        if currentCalculationModel is not None:
            if currentCalculationModel.ModelName != selectedCalcModelName:

                modelObj = backend.getCalculationModelByName(selectedCalcModelName)
                if modelObj is not None:
                    currentCalculationModel = modelObj()
        backend.currentCalculationModel = currentCalculationModel
        backend.currentFittingModel.PeakProperty = selectedCalcPeakProperty
        backend.currentCalculationModel.PeakProperty = selectedCalcPeakProperty
        backend._needsRefitting = True
        self._setUpdatedDetectedState()
        self.guiModule.settingsChanged.emit(self.getSettingsAsDict())


TABPOS += 1

#####################################################################
#####################    Fitting Panel    ###########################
#####################################################################

class GuiFittingPanel(GuiSettingPanel):
    tabPosition = TABPOS
    tabName = guiNameSpaces.Label_Fitting
    tabTipText = 'Set the various Fitting modes and options'

    def setWidgetDefinitions(self):
        """Common fitting Widgets"""
        models = list(self.guiModule.backendHandler.fittingModels.values())
        currentFittingModel = self.guiModule.backendHandler.currentFittingModel
        currentFittingModelName = currentFittingModel.ModelName if currentFittingModel is not None else None
        self.widgetDefinitions = od((
            (guiNameSpaces.WidgetVarName_OptimiserSeparator,
             {'label': guiNameSpaces.Label_OptimiserSeparator,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_OptimiserSeparator,
                       'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': guiNameSpaces.TipText_OptimiserSeparator}}),
            (guiNameSpaces.WidgetVarName_OptimiserMethod,
             {'label': guiNameSpaces.Label_OptimiserMethod,
              'callBack': self._commonCallback,
              'tipText': '',
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': False,
              'kwds': {'labelText': guiNameSpaces.Label_OptimiserMethod,
                       'tipText': guiNameSpaces.TipText_OptimiserMethod,
                       'texts': ['leastsq', 'differential_evolution', 'ampgo', 'newton'],
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (guiNameSpaces.WidgetVarName_ErrorMethod,
             {'label': guiNameSpaces.Label_ErrorMethod,
              'callBack': self._commonCallback,
              'tipText': guiNameSpaces.TipText_ErrorMethod,
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': False,
              'kwds': {'labelText': guiNameSpaces.Label_ErrorMethod,
                       'tipText': guiNameSpaces.TipText_ErrorMethod,
                       'texts': ['Default','parametric bootstrapping', 'non-parametric bootstrapping', 'Monte-Carlo', ],
                       'fixedWidths': SettingsWidgetFixedWidths}}),
        ))
        ## Set the models definitions
        extraLabels_ddFittingModels = [model.MaTex for model in models]
        tipTexts_ddFittingModels = [model.FullDescription for model in models]
        modelNames = [model.ModelName for model in models]
        extraLabelPixmaps = [maTex2Pixmap(maTex) for maTex in extraLabels_ddFittingModels]
        settingsDict = od((
            (guiNameSpaces.WidgetVarName_FittingSeparator,
             {'label': guiNameSpaces.Label_FittingSeparator,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_FittingSeparator,
                       'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': guiNameSpaces.TipText_FittingSeparator}}),
            (guiNameSpaces.WidgetVarName_FittingModel,
             {'label': guiNameSpaces.Label_FittingModel,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': None,
              'callBack': self._commonCallback,
              'tipText': guiNameSpaces.TipText_FittingModel,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_FittingModel,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'selectedText': currentFittingModelName,
                       'compoundKwds': {'texts': modelNames,
                                        'extraLabels': extraLabels_ddFittingModels,
                                        'tipTexts': tipTexts_ddFittingModels,

                                        'direction': 'v',
                                        'tipText': '',
                                        'hAlign': 'l',
                                        'extraLabelIcons': extraLabelPixmaps}}}),
        ))
        self.widgetDefinitions.update(settingsDict)

        return self.widgetDefinitions

    def _commonCallback(self, *args):
        """ Update FittingModel Settings at Backend"""
        self._setFittingSettingToBackend()
        super()._commonCallback(self, *args)

    def _setFittingSettingToBackend(self):
        """ Update the backend """
        getLogger().info('Setting Fitting changed...')
        fittingSettings = self.getSettingsAsDict()
        selectedFittingModelName = fittingSettings.get(guiNameSpaces.WidgetVarName_FittingModel, None)

        ## update the backend
        backend = self.guiModule.backendHandler
        currentFittingModel = backend.currentFittingModel
        modelObj = backend.getFittingModelByName(selectedFittingModelName)
        if modelObj is not None:
            currentFittingModel = modelObj()
        backend.currentFittingModel = currentFittingModel
        # todo Add the optimiser options (method, fitting Error etc)
        # set update detected.
        backend._needsRefitting = True


TABPOS += 1

#####################################################################
#####################   Appearance Panel  ###########################
#####################################################################

class AppearancePanel(GuiSettingPanel):
    tabPosition = TABPOS
    tabName = guiNameSpaces.Label_GeneralAppearance
    tabTipText = ''

    def setWidgetDefinitions(self):
        self.widgetDefinitions = od((
            (guiNameSpaces.WidgetVarName_SpectrumDisplSeparator,
             {'label': guiNameSpaces.Label_SpectrumDisplSeparator,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_SpectrumDisplSeparator,
                       'height': 30,
                       'colour': DividerColour,
                       'gridSpan': (1, 2),
                       'tipText': guiNameSpaces.TipText_SpectrumDisplSeparator}}),
            (guiNameSpaces.WidgetVarName_SpectrumDisplSelection,
             {'label': guiNameSpaces.Label_SpectrumDisplSelection,
              'callBack': None,
              'enabled': True,
              '_init': None,
              'type': settingWidgets.SpectrumDisplaySelectionWidget,
              'kwds': {'texts': [UseCurrent],
                       'displayText': [UseCurrent],
                       'defaults': [UseCurrent],
                       'standardListItems':[UseCurrent],
                       'objectName': guiNameSpaces.WidgetVarName_SpectrumDisplSelection,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'tipText': guiNameSpaces.TipText_SpectrumDisplSelection}}),

            (guiNameSpaces.WidgetVarName_NavigateToOpt,
             {'label': guiNameSpaces.Label_NavigateToOpt,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': None,
              'callBack': self._changeNavigateToDisplayTrigger,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_NavigateToOpt,
                       'hAlign': 'l',
                       'tipText': '',
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {'texts': [guiNameSpaces.SingleClick, guiNameSpaces.DoubleClick, guiNameSpaces.Disabled ],
                                        'tipTexts': ["","", "Don't navigate to SpectrumDisplay(s)"],
                                        'direction': 'v',
                                        'selectedInd': 0,
                                        }}}),

            (guiNameSpaces.WidgetVarName_BarGraphSeparator,
             {'label': guiNameSpaces.Label_BarGraphAppearance,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_BarGraphAppearance,
                       'height': 30,
                       'colour': DividerColour,
                       'gridSpan': (1, 2),
                       'tipText': guiNameSpaces.TipText_BarGraphAppearance}}),
            (guiNameSpaces.WidgetVarName_BarGraphXcolumnName,
             {'label': guiNameSpaces.Label_XcolumnName,
              'callBack': self._commonCallback,
              'tipText': guiNameSpaces.TipText_XcolumnName,
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_XcolumnName,
                       'tipText': guiNameSpaces.TipText_XcolumnName,
                       'texts': self._axisXOptions,
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (guiNameSpaces.WidgetVarName_BarGraphYcolumnName,
             {'label': guiNameSpaces.Label_YcolumnName,
              'callBack': self._commonCallback,
              'tipText': guiNameSpaces.TipText_YcolumnName,
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_YcolumnName,
                       'tipText': guiNameSpaces.TipText_YcolumnName,
                       'texts': self._axisYOptions,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (guiNameSpaces.WidgetVarName_ThreshValueCalcOptions,
             {'label': guiNameSpaces.Label_ThreshValueCalcOptions,
              'callBack': self._setThresholdValueForData,
              'tipText': guiNameSpaces.TipText_ThreshValueCalcOptions,
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_ThreshValueCalcOptions,
                       'tipText': guiNameSpaces.TipText_ThreshValueCalcOptions,
                       'texts': ["<Select>"] + guiNameSpaces.ThrValuesCalcOptions,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (guiNameSpaces.WidgetVarName_ThreshValueFactor,
             {'label': guiNameSpaces.Label_ThreshValueFactor,
              'tipText': guiNameSpaces.TipText_ThreshValueFactor,
              'callBack': self._setThresholdValueForData,
              'enabled': True,
              'type': compoundWidget.DoubleSpinBoxCompoundWidget,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_ThreshValueFactor,
                       'tipText': guiNameSpaces.TipText_ThreshValueFactor,
                       'value': 1,
                       'step': 0.01,
                       'decimals': 4,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (guiNameSpaces.WidgetVarName_ThreshValue,
             {'label': guiNameSpaces.Label_ThreshValue,
              'tipText': guiNameSpaces.TipText_ThreshValue,
              'callBack': self._commonCallback,
              'enabled': True,
              'type': compoundWidget.DoubleSpinBoxCompoundWidget,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_ThreshValue,
                       'tipText': guiNameSpaces.TipText_ThreshValue,
                       'value': 0.1,
                       'step': 0.01,
                       'decimals': 4,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (guiNameSpaces.WidgetVarName_AboveThrColour,
             {'label': guiNameSpaces.Label_AboveThrColour,
              'callBack': self._commonCallback,
              'tipText': guiNameSpaces.TipText_AboveThrColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': guiNameSpaces.Label_AboveThrColour,
                       'tipText': guiNameSpaces.TipText_AboveThrColour,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'selectItem': guiNameSpaces.BAR_aboveBrush,
                       'compoundKwds': {'includeGradients': True,
                                        }}}),
            (guiNameSpaces.WidgetVarName_BelowThrColour,
             {'label': guiNameSpaces.Label_BelowThrColour,
              'callBack': self._commonCallback,

              'tipText': guiNameSpaces.TipText_BelowThrColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': guiNameSpaces.Label_BelowThrColour,
                       'tipText': guiNameSpaces.TipText_BelowThrColour,
                       'selectItem': guiNameSpaces.BAR_belowBrush,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {'includeGradients': False}}}),
            (guiNameSpaces.WidgetVarName_UntraceableColour,
             {'label': guiNameSpaces.Label_UntraceableColour,
              'callBack': self._commonCallback,

              'tipText': guiNameSpaces.TipText_UntraceableColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': guiNameSpaces.Label_UntraceableColour,
                       'tipText': guiNameSpaces.TipText_UntraceableColour,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'selectItem': guiNameSpaces.BAR_untracBrush,
                       'compoundKwds': {'includeGradients': False}}}),
            (guiNameSpaces.WidgetVarName_ThrColour,
             {'label': guiNameSpaces.Label_ThrColour,
              'callBack': self._commonCallback,
              'tipText': guiNameSpaces.TipText_ThrColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': guiNameSpaces.Label_ThrColour,
                       'tipText': guiNameSpaces.TipText_ThrColour,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'selectItem': guiNameSpaces.BAR_thresholdLine,
                       'compoundKwds': {'includeGradients': False,
                                        }}}),
            (guiNameSpaces.WidgetVarName_TableSeparator,
             {'label': guiNameSpaces.Label_TableSeparator,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_TableSeparator,
                       'height': 30,
                       'colour': DividerColour,
                       'gridSpan': (1, 2),
                       'tipText': guiNameSpaces.TipText_TableSeparator}}),
            (guiNameSpaces.WidgetVarName_TableView,
             {'label': guiNameSpaces.Label_TableView,
              'tipText': guiNameSpaces.TipText_TableView,
              'enabled': False,
              'type': compoundWidget.CheckBoxesCompoundWidget,
              'kwds': {
                  'labelText': guiNameSpaces.Label_TableView,
                  'tipText': guiNameSpaces.TipText_TableView,
                  'texts': ['Assignments', 'Raw Data', 'Calculation', 'Fitting', 'Stats', 'Errors', ],
                  'callback': self._mainTableColumnViewCallback,
                  'fixedWidths': SettingsWidgetFixedWidths,
                  'compoundKwds': {'direction': 'v',
                                   'selectAll':True,
                                   'hAlign':'left'
                                   }
              }}),
            (guiNameSpaces.WidgetVarName_MolStrucSeparator,
             {'label': guiNameSpaces.Label_MolStrucSeparator,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_MolStrucSeparator,
                       'height': 30,
                       'colour': DividerColour,
                       'gridSpan': (1, 2),
                       'tipText': guiNameSpaces.TipText_MolStrucSeparator}}),
            (guiNameSpaces.WidgetVarName_MolStructureFile,
             {'label': guiNameSpaces.Label_MolStructureFile,
              'tipText': guiNameSpaces.TipText_MolStructureFile,
              'enabled': True,
              'type': compoundWidget.EntryPathCompoundWidget,
              '_init': None,
              'kwds': {
                  'labelText': guiNameSpaces.Label_MolStructureFile,
                  'tipText': guiNameSpaces.TipText_MolStructureFile,
                  'entryText': '~',
                  'fixedWidths': SettingsWidgetFixedWidths,
                  'compoundKwds': {'lineEditMinimumWidth': 300}
              }}),

        ))
        return self.widgetDefinitions

    @property
    def _axisYOptions(self):
        """ Get the columns names for plottable data. E.g.: the Fitting results and stats. """
        backend = self.guiModule.backendHandler
        currentFittingModel = backend.currentFittingModel
        currentCalculationModel = backend.currentCalculationModel
        fittingArgumentNames = currentFittingModel.modelArgumentNames
        calculationArgumentNames = currentCalculationModel.modelArgumentNames
        statNames = currentFittingModel.modelStatsNames
        allOptions = calculationArgumentNames + fittingArgumentNames + statNames
        return allOptions

    @property
    def _axisXOptions(self):
        """ Get the columns names for plottable data. E.g.: the Fitting results and stats. """
        backend = self.guiModule.backendHandler
        ## Todo: populate the list using headers that are definitely inside the Data
        allOptions = [sv.ASHTAG, sv.COLLECTIONID, sv.COLLECTIONPID, sv.NMRRESIDUECODE, sv.NMRRESIDUECODETYPE]
        return allOptions

    def _setThresholdValueForData(self, *args):
        mode = None
        factor = 1
        calculcationModeW = self.getWidget(guiNameSpaces.WidgetVarName_ThreshValueCalcOptions)
        if calculcationModeW:
            mode = calculcationModeW.getText()
        factorW = self.getWidget(guiNameSpaces.WidgetVarName_ThreshValueFactor)
        if factorW:
            factor = factorW.getValue()
        yColumnNameW = self.getWidget(guiNameSpaces.WidgetVarName_BarGraphYcolumnName)
        if yColumnNameW:
            yColumnName = yColumnNameW.getText()
        else:
            return
        if mode:
            value = self._getThresholdValueFromBackend(columnName=yColumnName, calculationMode=mode, factor=factor)
            if isinstance(value, (float,int)):
                thresholdValueW = self.getWidget(guiNameSpaces.WidgetVarName_ThreshValue)
                if thresholdValueW and value:
                    thresholdValueW.setValue(round(value, 3))

    def _getThresholdValueFromBackend(self, columnName, calculationMode, factor):

        """ Get the threshold value based on selected Y axis. called from _setThresholdValueForData"""
        mo = self.guiModule
        value = mo.backendHandler.getThresholdValueForData(data=mo.getGuiOutputDataFrame(), columnName=columnName,
                                            calculationMode=calculationMode, factor=factor)
        return value

    def _settingsChangedCallback(self, settingsDict, *args):
        """Callback when a core settings has changed.
        E.g.: the fittingModel and needs to update some of the appearance Widgets"""
        # reset the Ywidget options
        yColumnNameW = self.getWidget(guiNameSpaces.WidgetVarName_BarGraphYcolumnName)
        if yColumnNameW:
            yColumnNameW.setTexts(self._axisYOptions)

    def _getSelectedDisplays(self):
        displays = []
        displayWidget = self.getWidget(guiNameSpaces.WidgetVarName_SpectrumDisplSelection)
        if displayWidget:
            displays = displayWidget.getDisplays()
        return displays

    def _getMainTable(self):

        tablePanel = self.guiModule.panelHandler.getPanel(guiNameSpaces.TablePanel)
        if tablePanel is not None:
            table = tablePanel.mainTable
            return table

    def _mainTableColumnViewCallback(self, *args):

        widget = self.getWidget(guiNameSpaces.WidgetVarName_TableView)
        if not widget:
            return
        checked = widget.get() #get the checked values
        table = self._getMainTable()

    def _changeNavigateToDisplayTrigger(self, *args):
        table = self._getMainTable()
        widget = self.getWidget(guiNameSpaces.WidgetVarName_NavigateToOpt)
        if table and widget:
            table.setNavigateToPeakTrigger(widget.getByText())

TABPOS += 1


#####################################################################
#####################   Filtering Panel   ###########################
#####################################################################

## Not yet Implemeted
