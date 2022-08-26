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
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons, EditableRadioButtons
import ccpn.ui.gui.widgets.SettingsWidgets as settingWidgets
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Label import maTex2Pixmap
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as seriesVariables
from ccpn.ui.gui.widgets.HLine import LabeledHLine
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER, setColourScheme, FONTLIST, ZPlaneNavigationModes
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBar import PanelUpdateState
from ccpn.ui.gui.widgets.MessageDialog import showInfo, showWarning
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv

SettingsWidgeMinimumWidths =  (180, 180, 180)
SettingsWidgetFixedWidths = (200, 350, 350)

DividerColour = getColours()[DIVIDER]

class GuiSettingPanel(Frame):
    """
    Base class for GuiSettingPanel.
    A panel is Frame which will create a tab in the Gui Module settings
    Tabs are not added automatically. They need to be manually added from the SettingsHandler.
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
        self._setCreateDataTableButtonCallback()

    def setWidgetDefinitions(self):
        """ Define the widgets in a dict."""
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
                                         'entryText': 'SeriesAnalysis_DataTable',
                                         'tipText': guiNameSpaces.TipText_dataTableNameSelectionWidget,
                                         'fixedWidths': SettingsWidgetFixedWidths}, }),
            (guiNameSpaces.WidgetVarName_CreateDataTable,
             {'label': guiNameSpaces.Label_CreateInput,
                                'tipText': guiNameSpaces.TipText_createInputdataTableWidget,
                                'callBack': None,
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

        self.guiModule.updateAll()

    def _setCreateDataTableButtonCallback(self):
        "Set callback for create-input-DataTable button."
        buttonWidget = self.getWidget(guiNameSpaces.WidgetVarName_CreateDataTable)
        if buttonWidget:
            buttonWidget.button.clicked.connect(self._createInputDataTableCallback)

    def _setPeakPropertySelection(self):
        "Allow  selection of 'Position' or 'LineWidth' for creating a new input DataTable. "
        peakPropertyWidget = self.getWidget(guiNameSpaces.WidgetVarName_PeakProperty)
        if peakPropertyWidget:
            properties = [seriesVariables._PPMPOSITION, seriesVariables._LINEWIDTH]
            peakPropertyWidget.setTexts(properties)


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
        self.widgetDefinitions = od((
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
                                        'selectedInd':4,
                                        }}}),

            (guiNameSpaces.WidgetVarName_IncludeAtoms,
             {'label': guiNameSpaces.Label_IncludeAtoms,
              'tipText': guiNameSpaces.TipText_IncludeAtoms,
              'type': settingWidgets.UniqueNmrAtomNamesSelectionWidget,
              'postInit': self._setFixedHeightPostInit,
              'callBack': self._setCalculationOptionsToBackend,
              'enabled': False,
              'kwds': {
                  'labelText': guiNameSpaces.Label_IncludeAtoms,
                  'tipText': guiNameSpaces.TipText_IncludeAtoms,
                  'objectWidgetChangedCallback': self._setCalculationOptionsToBackend,
                  'pulldownCallback': self._setCalculationOptionsToBackend,
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
              'callBack': self._setCalculationOptionsToBackend,
              'kwds': {
                  'labelText': guiNameSpaces.Label_ExcludeResType,
                  'tipText': guiNameSpaces.TipText_ExcludeResType,
                  'objectWidgetChangedCallback': self._setCalculationOptionsToBackend,
                  'pulldownCallback': self._setCalculationOptionsToBackend,
                  'texts': [],
                  'defaults': [],
                  'standardListItems': [],
                  'objectName': guiNameSpaces.WidgetVarName_ExcludeResType,
                  'fixedWidths': SettingsWidgetFixedWidths
              }}),
        ))
        calculationModels = self.guiModule.backendHandler.calculationModels
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
              'callBack': self._setCalculationOptionsToBackend,
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
        self.widgetDefinitions.update(calculationWidgetDefinitions)

        return self.widgetDefinitions

    def _setFixedHeightPostInit(self, widget, *args):
        widget.listWidget.setFixedHeight(100)
        widget.setMaximumWidths(SettingsWidgetFixedWidths)
        widget.getLayout().setAlignment(QtCore.Qt.AlignTop)

    def _followGroupSelectionCallback(self, *args):
        widget = self.getWidget(guiNameSpaces.WidgetVarName_IncludeGroups)
        value = widget.getByText()
        groupObj = ALL_GROUPINGNMRATOMS.get(value, None)
        # todo to  be implemented: pre-fill the nmrAtoms selection and Excluded nmrRes.
        pass

    def _setCalculationOptionsToBackend(self):
        """ Update the backend """
        getLogger().info('_setCalculationOptionsToBackend: NIY...')
        pass

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
              'callBack': None,
              'tipText': guiNameSpaces.TipText_PeakPropertySelectionWidget,
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_OptimiserMethod,
                       'tipText': guiNameSpaces.TipText_OptimiserMethod,
                       'texts': ['leastsq', 'differential_evolution', 'ampgo', 'newton'],
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (guiNameSpaces.WidgetVarName_ErrorMethod,
             {'label': guiNameSpaces.Label_ErrorMethod,
              'callBack': None,
              'tipText': guiNameSpaces.TipText_ErrorMethod,
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_ErrorMethod,
                       'tipText': guiNameSpaces.TipText_ErrorMethod,
                       'texts': ['parametric bootstrapping', 'non-parametric bootstrapping', 'Monte-Carlo', ],
                       'fixedWidths': SettingsWidgetFixedWidths}}),
        ))
        ## Set the models definitions
        extraLabels_ddCalculationsModels = [model.MaTex for model in models]
        tipTexts_ddCalculationsModels = [model.FullDescription for model in models]
        modelNames = [model.ModelName for model in models]
        extraLabelPixmaps = [maTex2Pixmap(maTex) for maTex in extraLabels_ddCalculationsModels]
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
              'callback': self.updateFittingModel,
              'tipText': guiNameSpaces.TipText_FittingModel,
              'enabled': True,
              'kwds': {'labelText': guiNameSpaces.Label_FittingModel,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {'texts': modelNames,
                                        'extraLabels': extraLabels_ddCalculationsModels,
                                        'tipTexts': tipTexts_ddCalculationsModels,
                                        'direction': 'v',
                                        'tipText': '',
                                        'hAlign': 'l',
                                        'extraLabelIcons': extraLabelPixmaps}}}),
        ))
        self.widgetDefinitions.update(settingsDict)

        return self.widgetDefinitions

    def updateFittingModel(self, *args):
        """ Update FittingModel Settings at Backend"""
        self._setFittingSettingToBackend()

    def _getSelectedFittingModel(self):
        fittingSettings = self.getSettingsAsDict()
        currentFittingModel = fittingSettings.get(guiNameSpaces.WidgetVarName_FittingModel, None)

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
        print('Selected currentFittingModel', currentFittingModel)
        backend.currentFittingModel = currentFittingModel
        # todo Add the optimiser options (method, fitting Error etc)
        # set update detected.
        backend._needsRefitting = True
        self._setUpdatedDetectedState()

    def _calculateFittingCallback(self, *args):
        getLogger().info(f'Recalculating Fitting values ...')
        backend = self.guiModule.backendHandler
        backend.fitInputData()
        self.guiModule.updateAll()


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
              'enabled': False,
              '_init': None,
              'type': settingWidgets.SpectrumDisplaySelectionWidget,
              'kwds': {'texts': ['Current'],
                       'displayText': ['Current'],
                       'defaults': ['Current'],
                       'objectName': guiNameSpaces.WidgetVarName_SpectrumDisplSelection,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'tipText': guiNameSpaces.TipText_SpectrumDisplSelection}}),
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
        allOptions = [sv.COLLECTIONID, sv.COLLECTIONPID, sv.NMRRESIDUECODE, sv.NMRRESIDUECODETYPE]
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
        """Subclassed. Backend/values may vary for experiment """
        pass

    def _commonCallback(self, *args):
        """ _commonCallback to set the updateState icon"""
        self._setUpdatedDetectedState()

TABPOS += 1


#####################################################################
#####################   Filtering Panel   ###########################
#####################################################################

## Not yet Implemeted
