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
__dateModified__ = "$dateModified: 2022-06-30 14:25:24 +0100 (Thu, June 30, 2022) $"
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
from ccpn.framework.lib.experimentAnalysis.CSMFittingModels import ChemicalShiftCalculationModes, ChemicalShiftCalculationModels
from ccpn.util.Logging import getLogger
import numpy as np

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

SettingsWidgeMinimumWidths =  (180, 180, 180)
SettingsWidgetFixedWidths = (250, 300, 300)

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
        self._guiModule = guiModule
        self.getLayout().setAlignment(QtCore.Qt.AlignTop)
        self._moduleSettingsWidget = None # the widgets the collects all autogen widgets
        self.initWidgets()

    def initWidgets(self):
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
                print('Could not find get for: varName, widget',  varName, widget, e)
        return settingsDict



TABPOS = 0
## Make a default tab ordering as they are added to this file.
## Note: Tabs are not added automatically.
## Tabs are added from the SettingsHandler defined in the main GuiModule which allows more customisation in subclasses.

class GuiInputDataPanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = guiNameSpaces.Label_InputData
    tabTipText = guiNameSpaces.TipText_GuiInputDataPanel

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        settingsDict = od((
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
            (guiNameSpaces.WidgetVarName_PeakProperty,
             {'label': guiNameSpaces.Label_PeakProperty,
                                'callBack': None,
                                'tipText': guiNameSpaces.TipText_PeakPropertySelectionWidget,
                                'type': compoundWidget.PulldownListCompoundWidget,
                                'kwds': {'labelText': guiNameSpaces.Label_PeakProperty,
                                       'tipText': guiNameSpaces.TipText_PeakPropertySelectionWidget,
                                       'texts': [],
                                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (guiNameSpaces.WidgetVarName_DataTableName,
             {'label': guiNameSpaces.Label_InputDataTableName,
                                'tipText': guiNameSpaces.TipText_dataTableNameSelectionWidget,
                                'callBack': None,
                                'enabled': True,
                                'type': compoundWidget.EntryCompoundWidget,
                                '_init': None,
                                'kwds': {'labelText': guiNameSpaces.Label_InputDataTableName,
                                         'entryText': 'CSM_Input_DataTable',
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
              'callBack': None,
              'type': settingWidgets.DataTableSelectionWidget,
              'kwds': {
                  'labelText': guiNameSpaces.Label_SelectDataTable,
                  'tipText': guiNameSpaces.TipText_DataTableSelection,
                  'displayText': [],
                  'defaults': [],
                  'standardListItems': [],
                  'objectName': guiNameSpaces.WidgetVarName_DataTablesSelection,
                  'fixedWidths': SettingsWidgetFixedWidths}, }),
            ))
        self._moduleSettingsWidget = settingWidgets.ModuleSettingsWidget(parent=self, mainWindow=mainWindow,
                                               settingsDict=settingsDict,
                                               grid=(0, 0))
        self._moduleSettingsWidget.getLayout().setAlignment(QtCore.Qt.AlignLeft)

TABPOS += 1


class CSMGuiInputDataPanel(GuiInputDataPanel):

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiInputDataPanel.__init__(self, guiModule, *args, **Framekwargs)

        self._limitSelectionOnInputData()
        self._setPeakPropertySelection()
        self._setCreateDataTableButtonCallback()

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
        settingsPanelHandler = self._guiModule.settingsPanelHandler
        inputSettings = settingsPanelHandler.getInputDataSettings()
        sgPids = inputSettings.get(guiNameSpaces.WidgetVarName_SpectrumGroupsSelection, [None])
        spGroup = self._guiModule.project.getByPid(sgPids[-1])
        dataTableName = inputSettings.get(guiNameSpaces.WidgetVarName_DataTableName, None)
        peakProperty = inputSettings.get(guiNameSpaces.WidgetVarName_PeakProperty, seriesVariables._PPMPOSITION)  #this should give a warning if wrong
        if not spGroup:
            getLogger().warn('Cannot create an input DataTable without a SpectrumGroup. Select one first')
            return
        backend = self._guiModule.backendHandler
        newDataTable = backend.newDataTableFromSpectrumGroup(spGroup, dataTableName=dataTableName, thePeakProperty=peakProperty)
        backend.addInputDataTable(newDataTable)
        getLogger().info('Successfully created new Input Data. Item available on the DataTable selection')
        ## add as first selection in the datatable. clear first.
        dtSelectionWidget = self.getWidget(guiNameSpaces.WidgetVarName_DataTablesSelection)
        if dtSelectionWidget:
            dtSelectionWidget.clearList()
            dtSelectionWidget.updatePulldown()
            dtSelectionWidget.select(newDataTable.pid)
            #   update module
            self._guiModule.updateAll()

TABPOS += 1


class CSMCalculationPanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = guiNameSpaces.Label_Calculation
    tabTipText = guiNameSpaces.TipText_CSMCalculationPanelPanel

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        extraLabels_ddCalculationsModes = [model.MaTex for modelName, model in ChemicalShiftCalculationModes.items()]
        tipTexts_ddCalculationsModes = [model.FullDescription for modelName, model in
                                        ChemicalShiftCalculationModes.items()]
        extraLabelPixmaps = [maTex2Pixmap(maTex) for maTex in extraLabels_ddCalculationsModes]
        settingsDict = od((
            (guiNameSpaces.WidgetVarName_DeltaDeltasSeparator,
             {'label': guiNameSpaces.Label_DeltaDeltas,
               'type': LabeledHLine,
               'kwds': {'text':  guiNameSpaces.Label_DeltaDeltas,
                        'height': 30,
                        'gridSpan':(1,2),
                        'colour': DividerColour,
                        'tipText': guiNameSpaces.TipText_DeltaDeltasSeparator}}),
            (guiNameSpaces.WidgetVarName_DDCalculationMode,
             {'label': guiNameSpaces.Label_DDCalculationMode,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': self._calculationModePostInit,
              'callBack': self._setCalculationOptionsToBackend,
              'kwds': {'labelText' : guiNameSpaces.Label_DDCalculationMode,
                       'hAlign':'l',
                       'tipText' :'',
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds':{'texts' : list(ChemicalShiftCalculationModes.keys()),
                                       'extraLabels': extraLabels_ddCalculationsModes,
                                       'tipTexts': tipTexts_ddCalculationsModes,
                                       
                                       'direction': 'v',
                                       'extraLabelIcons': extraLabelPixmaps}}}),
        ))
        ## add the weighting Factor widgets
        factorsDict = od(())
        for atomName, factorValue in seriesVariables.DEFAULT_ALPHA_FACTORS.items():
            label = guiNameSpaces.Label_Factor.format(**{guiNameSpaces.AtomName:atomName})
            att = guiNameSpaces.WidgetVarName_Factor.format(**{guiNameSpaces.AtomName:atomName})
            tT = guiNameSpaces.TipText_Factor.format(**{guiNameSpaces.AtomName:atomName, guiNameSpaces.FactorValue:factorValue})
            factorsDict[att] = {'label': label,
            'tipText': guiNameSpaces.TipText_Factor,
            'type': compoundWidget.DoubleSpinBoxCompoundWidget,
            'callBack': self._setCalculationOptionsToBackend,
            'kwds': {'labelText': label,
                    'tipText': tT,
                    'value':factorValue,
                    'range': (0.001, 1), 'step': 0.01, 'decimals': 4,
                    'fixedWidths': SettingsWidgetFixedWidths}}
        settingsDict.update(factorsDict)
        restOfWidgetDict = od((
            (guiNameSpaces.WidgetVarName_FollowAtoms,
             {'label': guiNameSpaces.Label_FollowAtoms,
              'tipText': guiNameSpaces.TipText_FollowAtoms,
              'type': settingWidgets.UniqueNmrAtomNamesSelectionWidget,
              'postInit': self._followAtomsWidgetPostInit,
              'callBack': self._setCalculationOptionsToBackend,
              'kwds': {
                  'labelText': guiNameSpaces.Label_FollowAtoms,
                  'tipText': guiNameSpaces.TipText_FollowAtoms,
                  'texts': seriesVariables.DEFAULT_FILTERING_ATOMS,
                  'defaults': seriesVariables.DEFAULT_FILTERING_ATOMS,
                  'objectName': guiNameSpaces.WidgetVarName_FollowAtoms,
                  'standardListItems': [],
                  'fixedWidths': SettingsWidgetFixedWidths
              }}),
            (guiNameSpaces.WidgetVarName_ExcludeResType,
             {'label': guiNameSpaces.Label_ExcludeResType,
              'tipText': guiNameSpaces.TipText_ExcludeResType,
              'postInit': self._excludeResiduesWidgetPostInit,
              'type': settingWidgets.UniqueNmrResidueTypeSelectionWidget,
              'callBack': self._setCalculationOptionsToBackend,
              'kwds': {
                  'labelText': guiNameSpaces.Label_ExcludeResType,
                  'tipText': guiNameSpaces.TipText_ExcludeResType,
                  'texts': [],
                  'defaults': [],
                  'standardListItems': [],
                  'objectName': guiNameSpaces.WidgetVarName_ExcludeResType,
                  'fixedWidths': SettingsWidgetFixedWidths
              }}),

            (guiNameSpaces.WidgetVarName_DisappearedPeak,
             {'label': guiNameSpaces.Label_DisappearedPeak,
              'tipText': guiNameSpaces.TipText_DisappearedPeak,
              'enabled': True,
              'type': compoundWidget.DoubleSpinBoxCompoundWidget,
              'callBack': self._setCalculationOptionsToBackend,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_DisappearedPeak,
                       'tipText': guiNameSpaces.TipText_DisappearedPeak,
                       'value': 1,
                       'fixedWidths': SettingsWidgetFixedWidths}, }),

            ))
        settingsDict.update(restOfWidgetDict)
        self._moduleSettingsWidget = settingWidgets.ModuleSettingsWidget(parent=self, mainWindow=mainWindow,
                                                                         settingsDict=settingsDict,
                                                                         grid=(0, 0))
        self._moduleSettingsWidget.getLayout().setAlignment(QtCore.Qt.AlignLeft)
        Spacer(self, 0, 2, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(1, 0), gridSpan=(1, 1))

    def _followAtomsWidgetPostInit(self, widget, *args):
        widget.listWidget.setFixedHeight(100)
        widget.setMaximumWidths(SettingsWidgetFixedWidths)
        widget.getLayout().setAlignment(QtCore.Qt.AlignTop)

    def _excludeResiduesWidgetPostInit(self, widget, *args):
        widget.listWidget.setFixedHeight(100)
        widget.setFixedWidths(SettingsWidgetFixedWidths)
        widget.getLayout().setAlignment(QtCore.Qt.AlignTop)

    def _calculationModePostInit(self, widget):
        pass
        # widget.label.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        # widget.getLayout().setAlignment(QtCore.Qt.AlignLeft)

    def _getAlphaFactors(self):
        factors = {}
        for atomName, factorValue in seriesVariables.DEFAULT_ALPHA_FACTORS.items():
            att = guiNameSpaces.WidgetVarName_Factor.format(**{guiNameSpaces.AtomName:atomName})
            widget = self.getWidget(att)
            if widget is not None:
                factors.update({atomName:widget.getValue()})
        return factors

    def getSettingsAsDict(self):
        """Add the Factors in a dict, instead of single entries for each atom """
        extraSettings = {guiNameSpaces.ALPHA_FACTORS:self._getAlphaFactors()}
        settings = super(CSMCalculationPanel, self).getSettingsAsDict()
        settings.update(extraSettings)
        return settings

    def _setCalculationOptionsToBackend(self):
        """ Update the backend """
        calculationSettings = self.getSettingsAsDict()
        _filteringAtoms = calculationSettings.get(guiNameSpaces.WidgetVarName_FollowAtoms, [])
        _alphaFactors = calculationSettings.get(guiNameSpaces.ALPHA_FACTORS, {})
        # could be done more efficiently
        useAlphaFactors = {}
        for atom in _filteringAtoms:
            useAlphaFactors.update({atom:_alphaFactors.get(atom[0])})
        backend = self._guiModule.backendHandler
        backend._AlphaFactors = list(useAlphaFactors.values())
        backend._FilteringAtoms = list(useAlphaFactors.keys())


TABPOS += 1
class CSMGuiFittingPanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = 'Fitting'
    tabTipText = 'Set the various fitting modes and options'

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        extraLabels_ddCalculationsModels = [model.MaTex for modelName, model in ChemicalShiftCalculationModels.items()]
        tipTexts_ddCalculationsModels = [model.FullDescription for modelName, model in
                                        ChemicalShiftCalculationModels.items()]
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
              'tipText': guiNameSpaces.TipText_FittingModel,
              'enabled': False,
              'kwds': {'labelText': guiNameSpaces.Label_FittingModel,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {'texts': list(ChemicalShiftCalculationModels.keys()),
                                        'extraLabels': extraLabels_ddCalculationsModels,
                                        'tipTexts': tipTexts_ddCalculationsModels,
                                        'direction': 'v',
                                        'tipText': '',
                                        'hAlign': 'l',
                                        'extraLabelIcons': extraLabelPixmaps}}}),
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
              'enabled': False,
              'kwds': {'labelText': guiNameSpaces.Label_OptimiserMethod,
                       'tipText': guiNameSpaces.TipText_OptimiserMethod,
                       'texts': ['leastsq', 'differential_evolution', 'ampgo', 'newton'],
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (guiNameSpaces.WidgetVarName_ErrorMethod,
             {'label': guiNameSpaces.Label_ErrorMethod,
              'callBack': None,
              'tipText': guiNameSpaces.TipText_ErrorMethod,
              'type': compoundWidget.PulldownListCompoundWidget,
              'enabled': False,
              'kwds': {'labelText': guiNameSpaces.Label_ErrorMethod,
                       'tipText': guiNameSpaces.TipText_ErrorMethod,
                       'texts': ['parametric bootstrapping', 'non-parametric bootstrapping', 'Monte-Carlo',],
                       'fixedWidths': SettingsWidgetFixedWidths}}),

            ('Fitting_separator',
             {'label': 'Fitting_separator',
              'type': LabeledHLine,
              'kwds': {'text': '',
                       # 'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': ''}}),

            (guiNameSpaces.WidgetVarName_CalculateFitting,
             {'label': guiNameSpaces.Label_CalculateFitting,
              'tipText': guiNameSpaces.TipText_CalculateFitting,
              'callBack': None,
              'type': compoundWidget.ButtonCompoundWidget,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_CalculateFitting,
                       'text': guiNameSpaces.Button_CalculateFitting,  # this is the Button name
                       'callback': self._calculateFittingCallback,
                       'hAlign': 'left',
                       'tipText': guiNameSpaces.TipText_CalculateFitting,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

        ))
        # fittersDict = should be taken from guiModule.backend.fittingModels.
        # For now add to see the widgets layout

        self._moduleSettingsWidget = settingWidgets.ModuleSettingsWidget(parent=self, mainWindow=mainWindow,
                                                                         settingsDict=settingsDict,
                                                                         grid=(0, 0))
        self._moduleSettingsWidget.getLayout().setAlignment(QtCore.Qt.AlignLeft)
        Spacer(self, 0, 2, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(1, 0), gridSpan=(1, 1))

    def _calculateFittingCallback(self, *args):
        getLogger().info(f'Recalculating {guiNameSpaces.DELTAdelta} ...')
        backend = self._guiModule.backendHandler
        backend.fitInputData(**{seriesVariables.OUTPUT_DATATABLE_NAME: 'CSM_outPut_fitting'})
        self._guiModule.updateAll()



TABPOS += 1

class AppearancePanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = guiNameSpaces.AppearancePanel
    tabTipText = ''

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        settingsDict = od((
            (guiNameSpaces.WidgetVarName_GenAppearanceSeparator,
             {'label': guiNameSpaces.Label_GeneralAppearance,
              'type': LabeledHLine,
              'kwds': {'text': guiNameSpaces.Label_GeneralAppearance,
                       'height': 30,
                       'colour': DividerColour,
                       'gridSpan': (1, 2),
                       'tipText': guiNameSpaces.TipText_GeneralAppearance}}),
            (guiNameSpaces.WidgetVarName_ThreshValue,
             {'label': guiNameSpaces.Label_ThreshValue,
              'tipText': guiNameSpaces.TipText_ThreshValue,
              'callBack': None,
              'enabled': True,
              'type': compoundWidget.DoubleSpinBoxCompoundWidget,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_ThreshValue,
                       'tipText': guiNameSpaces.TipText_ThreshValue,
                       'value': 0.1,
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (guiNameSpaces.WidgetVarName_PredefThreshValue,
             {'label': guiNameSpaces.Label_PredefThreshValue,
              'tipText': guiNameSpaces.TipText_PredefThreshValue,
              'callBack': None,
              'enabled': True,
              'type': compoundWidget.ButtonCompoundWidget,
              '_init': None,
              'kwds': {'labelText': guiNameSpaces.Label_PredefThreshValue,
                       'tipText': guiNameSpaces.TipText_PredefThreshValue,
                       'text':guiNameSpaces.Label_StdThreshValue,
                       'fixedWidths': SettingsWidgetFixedWidths
                       }}),
            (guiNameSpaces.WidgetVarName_AboveThrColour,
             {'label': guiNameSpaces.Label_AboveThrColour,
              'callBack': None,
              'tipText': guiNameSpaces.TipText_AboveThrColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': guiNameSpaces.Label_AboveThrColour,
                       'tipText': guiNameSpaces.TipText_PeakPropertySelectionWidget,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds':{'includeGradients': True}}}),
            (guiNameSpaces.WidgetVarName_BelowThrColour,
             {'label': guiNameSpaces.Label_BelowThrColour,
              'callBack': None,
              'tipText': guiNameSpaces.TipText_BelowThrColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': guiNameSpaces.Label_BelowThrColour,
                       'tipText': guiNameSpaces.TipText_BelowThrColour,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds':{'includeGradients': True}}}),
            (guiNameSpaces.WidgetVarName_UntraceableColour,
             {'label': guiNameSpaces.Label_UntraceableColour,
              'callBack': None,
              'tipText': guiNameSpaces.TipText_UntraceableColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': guiNameSpaces.Label_UntraceableColour,
                       'tipText': guiNameSpaces.TipText_UntraceableColour,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds':{'includeGradients': True}}}),
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
                        'compoundKwds': {'lineEditMinimumWidth':300}
                       }}),

        ))
        self._moduleSettingsWidget = settingWidgets.ModuleSettingsWidget(parent=self, mainWindow=mainWindow,
                                                                         settingsDict=settingsDict,
                                                                         grid=(0, 0))
        self._moduleSettingsWidget.getLayout().setAlignment(QtCore.Qt.AlignLeft)

TABPOS += 1
