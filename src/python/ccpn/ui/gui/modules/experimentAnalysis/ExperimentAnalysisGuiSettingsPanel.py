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
__dateModified__ = "$dateModified: 2023-05-16 16:28:35 +0100 (Tue, May 16, 2023) $"
__version__ = "$Revision: 3.1.1 $"
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
from ccpn.util.OrderedSet import OrderedSet
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
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBars import PanelUpdateState
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.ui.gui.widgets.SettingsWidgets import ALL, UseCurrent
from ccpn.ui.gui.widgets.BarGraphWidget import TICKOPTIONS

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
        # self.postInitWidgets()

    def postInitWidgets(self):
        """ Override to apply preselection of widgets after creation"""
        pass

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
    tabName = guiNameSpaces.Label_SetupTab
    tabTipText = guiNameSpaces.TipText_GuiInputDataPanel

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiSettingPanel.__init__(self, guiModule, *args, **Framekwargs)

    def _getExperimentSelectorNames(self):
        settingsHandler = self.guiModule.settingsPanelHandler
        experimentSelectorHandler = settingsHandler.experimentSelectorHandler
        moduleAnalysisType = self.guiModule.analysisType
        experimentSelectorsNames = []
        experimentSelectorsTipTexts = []
        for selectorName, selector in experimentSelectorHandler.ExperimentSelectors.items():
            if selector.analysisType in [moduleAnalysisType, None]:
                experimentSelectorsNames.append(selectorName)
                experimentSelectorsTipTexts.append(selector._makeTipText())
        return experimentSelectorsNames, experimentSelectorsTipTexts

    def setWidgetDefinitions(self):
        """ Define the widgets in a dict."""
        backend = self.guiModule.backendHandler
        settingsHandler = self.guiModule.settingsPanelHandler
        experimentSelectorHandler = settingsHandler.experimentSelectorHandler
        expNames, expTipTexts = self._getExperimentSelectorNames()
        self.widgetDefinitions = od((
            (guiNameSpaces.WidgetVarName_ExperimentSeparator,
             {'label': guiNameSpaces.Label_ExperimentSeparator,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_ExperimentSeparator,
                       'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': guiNameSpaces.TipText_ExperimentSeparator}}),
            (guiNameSpaces.WidgetVarName_ExperimentName,
             {'label': guiNameSpaces.Label_ExperimentOption,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': None,
              'callBack':  self._experimentSelectorChanged,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_ExperimentOption,
                       'hAlign': 'l',
                       'tipText': '',
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {'texts': expNames,
                                        'tipTexts': expTipTexts,
                                        'direction': 'v',
                                        'selectedInd': 0,
                                        }}}),

            (guiNameSpaces.WidgetVarName_GeneralSetupSeparator,
             {'label': guiNameSpaces.Label_GeneralSetup,
                                 'type': LabeledHLine,
                                 'kwds': {'text': guiNameSpaces.Label_GeneralSetup,
                                          'colour':DividerColour,
                                          'gridSpan':(1,2),
                                          'tipText': guiNameSpaces.TipText_GeneralSetup}}),


            (guiNameSpaces.WidgetVarName_CreateSGroup,
             {'label': guiNameSpaces.Label_CreateSGroup,
                                 'tipText': guiNameSpaces.TipText_CreateSGroup,
                                 'callBack': self._createSpectrumGroupCallback,
                                 'type': compoundWidget.ButtonCompoundWidget,
                                 '_init': None,
                                 'kwds': {'labelText': guiNameSpaces.Label_CreateSGroup,
                                           'text': 'Create ...',  # this is the Button name
                                           'hAlign': 'left',
                                           'tipText': guiNameSpaces.TipText_CreateSGroup,
                                           'fixedWidths': SettingsWidgetFixedWidths}}),
            (guiNameSpaces.WidgetVarName_SpectrumGroupsSelection,
             {'label':  guiNameSpaces.Label_SelectSpectrumGroups,
                                'tipText': guiNameSpaces.TipText_SpectrumGroupSelectionWidget,
                                'callBack': None,
                                'type': settingWidgets.SpectrumGroupSelectionWidget,
                                'postInit': self._setFixedHeightPostInit,
                                'kwds': {
                                        'labelText': guiNameSpaces.Label_SelectSpectrumGroups,
                                        'tipText': guiNameSpaces.TipText_SpectrumGroupSelectionWidget,
                                        'pulldownCallback': self._spectrumGroupSelectionChanged,
                                        'objectWidgetChangedCallback': self._spectrumGroupSelectionChanged,
                                        'displayText': [],
                                        'defaults': [],
                                        'standardListItems':[],
                                        'objectName': guiNameSpaces.WidgetVarName_SpectrumGroupsSelection,
                                        'fixedWidths': SettingsWidgetFixedWidths}, }),
            (guiNameSpaces.WidgetVarName_SetupCollection,
             {'label': guiNameSpaces.Label_SetupCollection,
              'tipText': guiNameSpaces.TipText_SetupCollection,
              'callBack': self._createInputCollectionCallback,
              'type': compoundWidget.ButtonCompoundWidget,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_SetupCollection,
                       'text': 'Setup ...',  # this is the Button name
                       'hAlign': 'left',
                       'tipText': guiNameSpaces.TipText_SetupCollection,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (guiNameSpaces.WidgetVarName_InputCollectionSelection,
             {'label': guiNameSpaces.Label_InputCollectionSelection,
              'tipText': guiNameSpaces.TipText_InputCollectionSelection,
              'type': objectPulldowns.CollectionPulldown,
              'kwds': {'labelText': guiNameSpaces.Label_InputCollectionSelection,
                       'tipText': guiNameSpaces.TipText_InputCollectionSelection,
                       'filterFunction': self._filterInputCollections,
                       'callback': self._addInputCollectionCallback,
                       'showSelectName': True,
                       'objectName': guiNameSpaces.WidgetVarName_InputCollectionSelection,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (guiNameSpaces.WidgetVarName_DataTableSeparator,
             {'label': guiNameSpaces.Label_DataTables,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_DataTables,
                       # 'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': guiNameSpaces.TipText_DataTableSeparator}}),

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

            (guiNameSpaces.WidgetVarName_DataTablesSelection,
             {'label': guiNameSpaces.Label_SelectDataTable,
              'tipText': guiNameSpaces.TipText_DataTableSelection,
              'type': settingWidgets._SeriesInputDataTableSelectionWidget,
              'postInit': self._setFixedHeightPostInit,
              'kwds': {
                  'labelText': guiNameSpaces.Label_SelectDataTable,
                  'tipText': guiNameSpaces.TipText_DataTableSelection,
                  'displayText': [],
                  'defaults': [],
                  'standardListItems': [],
                  'objectWidgetChangedCallback':self._changedInputDataCallback,
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
              'callBack': self._fitAndFetchOutputData,
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
              'callBack': self._resultDataTablePulldownCallback,
              'type': objectPulldowns.DataTablePulldown,
              'kwds': {'labelText': guiNameSpaces.Label_SelectOutputDataTable,
                       'tipText': guiNameSpaces.TipText_OutputDataTableSelection,
                       'filterFunction': self._filterOutputDataOnPulldown,
                       'showSelectName':True,
                       'objectName': guiNameSpaces.WidgetVarName_OutputDataTablesSelection,
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            ))
        return self.widgetDefinitions

    def _setFixedHeightPostInit(self, widget, *args):
        widget.listWidget.setFixedHeight(50)
        widget.setMaximumWidths(SettingsWidgetFixedWidths)
        widget.getLayout().setAlignment(QtCore.Qt.AlignTop)

    def _changedInputDataCallback(self, *args):

        backend = self.guiModule.backendHandler
        dataTablePids = self.getSettingsAsDict().get(guiNameSpaces.WidgetVarName_DataTablesSelection, [])
        if not dataTablePids:
            self.guiModule.backendHandler.clearInputDataTables()
            getLogger().info(f'{self.guiModule.className}:{self.tabName}. Cleaned inputDataTables')
            return
        objectDisplayed = []
        for pid in dataTablePids:
            obj = self.guiModule.project.getByPid(pid)
            if obj:
                objectDisplayed.append(obj)
        ## remove not needed
        for currObj in backend.inputDataTables:
            if currObj not in objectDisplayed:
                backend.removeInputDataTable(currObj)
        ## add new
        for obj in objectDisplayed:
            if obj not in backend.inputDataTables:
                backend.addInputDataTable(obj)
                getLogger().info(f'{self.guiModule.className}:{self.tabName}. {obj} added to inputDataTables')

    def _createInputCollectionCallback(self):
        """ Show the relevant Popup"""

        from ccpn.ui.gui.popups.SeriesPeakCollectionPopup import SeriesPeakCollectionPopup
        settingsHandler = self.guiModule.settingsPanelHandler
        experimentSelectorHandler = settingsHandler.experimentSelectorHandler
        experimentSelector =  experimentSelectorHandler.experimentSelector
        if experimentSelector is not None:
            collectionName = experimentSelector.inputCollection
        else:
            collectionName = 'MyCollection'
        spectrumGroups = self.guiModule.backendHandler.inputSpectrumGroups
        if len(spectrumGroups)>0:
            spectrumGroup = spectrumGroups[-1]
        else:
            spectrumGroup = None
        popup = SeriesPeakCollectionPopup(parent=self.guiModule.mainWindow,
                                          collectionName=collectionName,
                                          mainWindow=self.guiModule.mainWindow,
                                          spectrumGroup = spectrumGroup)
        popup.exec_()
        if popup is not None:
            topCollection = popup._topCollection
            if topCollection is not None:
                widget = self.getWidget(guiNameSpaces.WidgetVarName_InputCollectionSelection)
                widget.update()
                if widget is not None:
                    widget.select(topCollection.pid)

    def _experimentSelectorChanged(self, *args, **kwargs):
        widget = self.getWidget(guiNameSpaces.WidgetVarName_ExperimentName)
        value = widget.getByText()
        settingsHandler = self.guiModule.settingsPanelHandler
        experimentSelectorHandler = settingsHandler.experimentSelectorHandler
        experimentSelectorHandler.experimentSelector = value


    def _createSpectrumGroupCallback(self):
        """ Show the relevant Popup """
        from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
        sge = SpectrumGroupEditor(parent=self, mainWindow=self.guiModule.mainWindow, editMode=False)
        sge.exec_()
        sg = sge.obj
        if sg is not None:
            # add automatically to input
            sgSelectionWidget = self.getWidget(guiNameSpaces.WidgetVarName_SpectrumGroupsSelection)
            sgSelectionWidget.updatePulldown()
            if sgSelectionWidget is not None:
                sgSelectionWidget.select(sg.pid)

    def _addInputCollectionCallback(self, *args):
        """Add Input Collection to backend  """
        backend = self.guiModule.backendHandler
        pid = self.getSettingsAsDict().get(guiNameSpaces.WidgetVarName_InputCollectionSelection)
        backend.inputCollection = self.guiModule.project.getByPid(pid)

    def _spectrumGroupSelectionChanged(self, *args):

        backend = self.guiModule.backendHandler
        sgPids = self.getSettingsAsDict().get(guiNameSpaces.WidgetVarName_SpectrumGroupsSelection, [])
        if not sgPids:
            self.guiModule.backendHandler.clearInputSpectrumGroups()
            getLogger().info(f'{self.guiModule.className}:{self.tabName}. Cleaned inputSpectrumGroups')
            return
        objectDisplayed = []
        for pid in sgPids:
            obj = self.guiModule.project.getByPid(pid)
            if obj:
                objectDisplayed.append(obj)

        ## remove not needed
        for currObj in backend.inputSpectrumGroups:
            if currObj not in objectDisplayed:
                backend.removeInputSpectrumGroup(currObj)

        ## add new
        for obj in objectDisplayed:
            if obj not in backend.inputSpectrumGroups:
                backend.addInputSpectrumGroup(obj)
                getLogger().info(f'{self.guiModule.className}:{self.tabName}. {obj} added to InputSpectrumGroups')

    def _fitAndFetchOutputData(self, *args):
        getLogger().info('Starting fit')
        backend = self.guiModule.backendHandler
        name = self.getSettingsAsDict().get(guiNameSpaces.WidgetVarName_OutPutDataTableName, sv.SERIESANALYSISOUTPUTDATA)
        backend.outputDataTableName = name
        if len(backend.inputDataTables) == 0:
            dataTablePids = self.getSettingsAsDict().get(guiNameSpaces.WidgetVarName_DataTablesSelection, [])
            if len(dataTablePids) == 0:
                msg = 'Cannot create any output DataTable. Select/add an input DataTable first.'
                getLogger().warning(msg)
                showWarning('Missing InputData', msg)
                return
            for pid in dataTablePids:
                obj = self.guiModule.project.getByPid(pid)
                if obj:
                    backend.addInputDataTable(obj)

        outputDataTable = backend.fitInputData()
        outputPulldown = self.getWidget(guiNameSpaces.WidgetVarName_OutputDataTablesSelection)
        if outputPulldown and outputDataTable is not None:
            outputPulldown.update() #there seems to be a bug on pulldown not updating straight-away
            outputPulldown.select(outputDataTable.pid)

        # preselect the NmrResidue code if available in the bar graph
        appearancePanel = self.guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_GeneralAppearance)
        appearancePanel._preselectDefaultXaxisBarGraph()

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

    def _resultDataTablePulldownCallback(self, selectedName,  *args):
        """Callback upon widget selection """
        # TODO check leaking notifiers  after closing the module
        selectedDataTable = self.guiModule.project.getByPid(selectedName)
        self.guiModule.backendHandler.resultDataTable = selectedDataTable
        appearanceTab = self.guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_GeneralAppearance)
        appearanceTab._resetXYBarPlotOptions()
        self.guiModule.updateAll()
        appearanceTab._refitYZoomOnBarPlot(None, updateGuiModule=False)

    def _filterInputCollections(self, pids, *args):
        """ Add collections only if contain a subset of other collections. Avoid massive lists! """
        collections = self.guiModule.project.getByPids(pids)
        filteredCollectionPids = []
        for collection in collections:
            types = [type(item) for item in collection.items]
            if type(collection) in types:
                filteredCollectionPids.append(collection.pid)
        return filteredCollectionPids

    def _createInputDataTableCallback(self, *args):
        """ Create InputDataTable from widget Callback. """
        settingsPanelHandler = self.guiModule.settingsPanelHandler
        inputSettings = settingsPanelHandler.getInputDataSettings()
        sgPids = inputSettings.get(guiNameSpaces.WidgetVarName_SpectrumGroupsSelection, [None])
        if not sgPids:
            showWarning('Select SpectrumGroup', 'Cannot create an input DataTable without a SpectrumGroup')
            return
        spGroup = self.guiModule.project.getByPid(sgPids[-1])
        dataTableName = inputSettings.get(guiNameSpaces.WidgetVarName_DataTableName, None)
        experimentName = inputSettings.get(guiNameSpaces.WidgetVarName_ExperimentName, sv.USERDEFINEDEXPERIMENT)
        if not spGroup:
            getLogger().warn('Cannot create an input DataTable without a SpectrumGroup. Select one first')
            return
        backend = self.guiModule.backendHandler
        newDataTable = backend.newInputDataTableFromSpectrumGroup(spGroup, dataTableName=dataTableName,
                                                                  experimentName=experimentName)
        ## add as first selection in the datatable. clear first.
        dtSelectionWidget = self.getWidget(guiNameSpaces.WidgetVarName_DataTablesSelection)
        if dtSelectionWidget:
            # dtSelectionWidget.clearList()
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
              'callBack': self._calculationModeChanged,
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
        # self.widgetDefinitions.update(filteringWidgetDefinitions)

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

    def _calculationModeChanged(self, *args):
        """Triggered after a change in the Calculation widget.
         Auto-set the BarGraph to show the first Argument Result based on the model"""
        self._commonCallback(*args)
        appearancePanel = self.guiModule.settingsPanelHandler.getTab(guiNameSpaces.Label_GeneralAppearance)
        yAxisWidget = appearancePanel.getWidget(guiNameSpaces.WidgetVarName_BarGraphYcolumnName)
        backend = self.guiModule.backendHandler
        currentCalculationModel = backend.currentCalculationModel
        if currentCalculationModel is not None and currentCalculationModel.ModelName != sv.BLANKMODELNAME:
            firstArg, *_ = currentCalculationModel.modelArgumentNames or [None]
            if yAxisWidget:
                yAxisWidget.select(firstArg)

    def _commonCallback(self, *args):
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
        enabledModels = [model.isEnabled for model in models]
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
              'callBack': self._fittingModeChanged,
              'tipText': guiNameSpaces.TipText_FittingModel,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_FittingModel,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'selectedText': currentFittingModelName,
                       'compoundKwds': {'texts': modelNames,
                                        'extraLabels': extraLabels_ddFittingModels,
                                        'tipTexts': tipTexts_ddFittingModels,
                                        'enabledTexts': enabledModels,
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

    def _fittingModeChanged(self, *args):
        """Triggered after a change in the fitting widget.
         Auto-set the BarGraph Y widget to show the first Argument Result based on the model"""
        self._commonCallback(*args)

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

            (guiNameSpaces.WidgetVarName_PlotViewMode,
             {'label': guiNameSpaces.Label_PlotViewMode,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': None,
              'callBack': self._viewModeChanged,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_PlotViewMode,
                       'hAlign': 'l',
                       'tipText': '',
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {'texts': guiNameSpaces.PlotViewModes,
                                        'tipTexts': guiNameSpaces.PlotViewModesTT,
                                        'direction': 'v',
                                        'selectedInd': 0,
                                        }}}),

            (guiNameSpaces.WidgetVarName_Chain,
             {'label': guiNameSpaces.Label_Chain,
              'callBack': self._commonCallback,
              'tipText': guiNameSpaces.TipText_Chain,
              'type': objectPulldowns.ChainPulldown,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_Chain,
                       'tipText': guiNameSpaces.TipText_Chain,
                       'callback': self._commonCallback,
                       'objectName': guiNameSpaces.WidgetVarName_Chain,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            (guiNameSpaces.WidgetVarName_BarGraphXcolumnName,
             {'label': guiNameSpaces.Label_XcolumnName,
              'callBack': self._commonCallback,
              'tipText': guiNameSpaces.TipText_XcolumnName,
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_XcolumnName,
                       'tipText': guiNameSpaces.TipText_XcolumnName,
                       'texts': [],
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (guiNameSpaces.WidgetVarName_BarGraphYcolumnName,
             {'label': guiNameSpaces.Label_YcolumnName,
              'callBack': self._refitYZoomOnBarPlot,
              'tipText': guiNameSpaces.TipText_YcolumnName,
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_YcolumnName,
                       'tipText': guiNameSpaces.TipText_YcolumnName,
                       'texts': [],
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

            (guiNameSpaces.WidgetVarName_WindowRollingAverage,
             {'label': guiNameSpaces.Label_WindowRollingAverage,
              'tipText': guiNameSpaces.TipText_WindowRollingAverage,
              'callBack': self._commonCallback,
              'enabled': True,
              'type': compoundWidget.DoubleSpinBoxCompoundWidget,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_WindowRollingAverage,
                       'tipText': guiNameSpaces.TipText_WindowRollingAverage,
                       'value': 7,
                       'step': 1,
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
            (guiNameSpaces.WidgetVarName_RALColour,
             {'label': guiNameSpaces.Label_RALColour,
              'callBack': self._commonCallback,
              'tipText': guiNameSpaces.TipText_RALColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': guiNameSpaces.Label_RALColour,
                       'tipText': guiNameSpaces.TipText_RALColour,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'selectItem': guiNameSpaces.BAR_rollingAvLine,
                       'compoundKwds': {'includeGradients': False,
                                        }}}),
            (guiNameSpaces.WidgetVarName_BarXTickOpt,
             {'label': guiNameSpaces.Label_BarXTickOpt,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': None,
              'callBack': self._changeBarXTicks,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_BarXTickOpt,
                       'hAlign': 'l',
                       'tipText': guiNameSpaces.TipText_BarXTickOpt,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {
                           'texts': TICKOPTIONS,
                           'tipTexts': ["Always show all ticks", "Show minimal ticks on zoom-in/out",],
                           'direction': 'v',
                           'selectedInd': 0,
                           }}}),

            ##Tables
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
              'enabled': True,
              'type': compoundWidget.CheckBoxesCompoundWidget,
              'kwds': {
                  'labelText': guiNameSpaces.Label_TableView,
                  'tipText': guiNameSpaces.TipText_TableView,
                  'texts': guiNameSpaces.TableGrouppingHeaders,
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

    def postInitWidgets(self):
        self._preselectDefaultXaxisBarGraph()
        self._preselectDefaultYaxisBarGraph()

    def _refitYZoomOnBarPlot(self, selection, updateGuiModule=True, *args):
        if updateGuiModule:
            self.guiModule.updateAll()
        barPlot = self.guiModule.panelHandler.getPanel(guiNameSpaces.BarPlotPanel)
        if barPlot is not None:
            try:
                barPlot.fitYZoom()
            except Exception as err:
                getLogger().debug(f'BarPlot not found or not ready to zoom {err}')

    def _preselectDefaultXaxisBarGraph(self):
        """ Preselect the NmrResidue code if available """
        xAxisWidget = self.getWidget(guiNameSpaces.WidgetVarName_BarGraphXcolumnName)
        valueToSelect = guiNameSpaces.ASHTAG
        dataFrame = self.guiModule.getGuiResultDataFrame()
        if dataFrame is None:
            return
        codes = dataFrame.get(sv.NMRRESIDUECODE)
        if codes is None:
            return
        if codes.all():
            valueToSelect = sv.NMRRESIDUECODE
        if xAxisWidget:
            xAxisWidget.select(valueToSelect)

    def _preselectDefaultYaxisBarGraph(self):
        pass

    def _viewModeChanged(self, *args):
        barGraphPanel = self.guiModule.panelHandler.getPanel(guiNameSpaces.BarPlotPanel)
        if barGraphPanel is not None:
            viewModeWidget = self.getWidget(guiNameSpaces.WidgetVarName_PlotViewMode)
            viewMode = viewModeWidget.getByText()
            barGraphPanel.setViewMode(viewMode)
            self._commonCallback()


    def _getModelNameFromData(self, data, modelNameColumn):
        modelName = None
        if modelNameColumn in data.columns:
            modelNames = data[modelNameColumn].values
            if len(modelNames) > 0:
                modelName = modelNames[0]
            else:
                modelName = None
        return modelName

    def _getAxisYOptions(self):
        """ Get the columns names for plottable data. E.g.: the Fitting results and stats. """
        allOptions = []
        preferredSelection = None
        backend = self.guiModule.backendHandler
        data = backend.getMergedResultDataFrame()
        if data is None:
            return allOptions, preferredSelection

        modelName = self._getModelNameFromData(data, sv.MODEL_NAME)
        calModelName = self._getModelNameFromData(data, sv.CALCULATION_MODEL)

        _model = backend.getFittingModelByName(modelName)
        _calcModel = backend.getCalculationModelByName(calModelName)

        if _model is not None:
            model = _model()
            if model.ModelName != sv.BLANKMODELNAME:
                allArgs = model.getAllArgNames()
                allOptions.extend(allArgs)
                preferredSelection = model._preferredYPlotArgName
        if _calcModel is not None: # if we have the calculation model, then it's the preferred
            model = _calcModel()
            if model.ModelName != sv.BLANKMODELNAME:
                moArgs = model.modelArgumentNames
                allOptions.extend(moArgs)
                preferredSelection = model._preferredYPlotArgName

        if len(allOptions) == 0:
            # fallback options
            data.dropna(axis=1, how='all', inplace=False) # remove all non plottable columns. remove columns with all None values
            fallbackColumns = data.select_dtypes(include=[float, int])  # remove all non plottable columns. remove columns with non Int or float values
            fallbackOptions = list(fallbackColumns.columns)
            excludedFromPreferred = guiNameSpaces._ExcludedFromPreferredYAxisOptions
            fallbackOptions = [i for i in fallbackOptions if i not in excludedFromPreferred]
            allOptions = fallbackOptions
            preferredSelection = allOptions[0] if len (allOptions)>0 else None

        return allOptions, preferredSelection

    def _getAxisXOptions(self):
        """ Get the columns names for plottable data. E.g.: the Fitting results and stats. """

        allowed = [
                   sv.INDEX,
                   sv.COLLECTIONID,
                   sv.COLLECTIONPID,
                   sv.NMRRESIDUECODE,
                   sv.NMRRESIDUECODETYPE
                ]
        return allowed, sv.NMRRESIDUECODE

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
        value = mo.backendHandler.getThresholdValueForData(data=mo.getGuiResultDataFrame(), columnName=columnName,
                                                           calculationMode=calculationMode, factor=factor)
        return value

    def _resetXYBarPlotOptions(self,):
        """ """
        # reset the XYwidget options
        xColumnNameW = self.getWidget(guiNameSpaces.WidgetVarName_BarGraphXcolumnName)
        xOptions, xPreferredSelection = self._getAxisXOptions()
        xColumnNameW.setTexts(xOptions)
        if len(xOptions) > 0:
            xColumnNameW.select(xPreferredSelection)

        yColumnNameW = self.getWidget(guiNameSpaces.WidgetVarName_BarGraphYcolumnName)
        yOptions, yPreferredSelection = self._getAxisYOptions()
        yColumnNameW.setTexts(yOptions)
        if len(yOptions)>0:
            yColumnNameW.select(yPreferredSelection)

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

    def _getMainBarGraphWidget(self):

        barGraphPanel = self.guiModule.panelHandler.getPanel(guiNameSpaces.BarPlotPanel)
        if barGraphPanel is not None:
            barGraphWidget = barGraphPanel.barGraphWidget
            return barGraphWidget

    def _mainTableColumnViewCallback(self, *args):

        widget = self.getWidget(guiNameSpaces.WidgetVarName_TableView)
        if not widget:
            return
        checked = widget.get() #get the checked values
        table = self._getMainTable()
        for value in widget.getTexts():
            funcName = f'_toggle{value}Headers'
            func = getattr(table, funcName)
            try:
                func(setVisible=value in checked)
            except Exception as err:
                getLogger().warning(f'Failed to call the function {funcName}. Error:{err}')

    def _changeNavigateToDisplayTrigger(self, *args):
        table = self._getMainTable()
        widget = self.getWidget(guiNameSpaces.WidgetVarName_NavigateToOpt)
        if table and widget:
            table.setNavigateToPeakTrigger(widget.getByText())

    def _changeBarXTicks(self, *args):
        widget = self.getWidget(guiNameSpaces.WidgetVarName_BarXTickOpt)
        if widget:
            value = widget.getByText()
            barGraph = self._getMainBarGraphWidget()
            barGraph.setTickOption(value)
            self._commonCallback()


TABPOS += 1


#####################################################################
#####################   Filtering Panel   ###########################
#####################################################################

## Not yet Implemeted
