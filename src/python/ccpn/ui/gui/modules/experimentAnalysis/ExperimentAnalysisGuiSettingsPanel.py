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
__dateModified__ = "$dateModified: 2022-06-29 20:15:38 +0100 (Wed, June 29, 2022) $"
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
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as nameSpaces
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
    tabName = nameSpaces.Label_InputData
    tabTipText = nameSpaces.TipText_GuiInputDataPanel

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        settingsDict = od((
            (nameSpaces.WidgetVarName_SpectrumGroupsSeparator,
                                {'label': nameSpaces.Label_SpectrumGroups,
                                 'type': LabeledHLine,
                                 'kwds': {'text': nameSpaces.Label_SpectrumGroups,
                                          # 'height': 30,
                                          'colour':DividerColour,
                                          'gridSpan':(1,2),
                                          'tipText': nameSpaces.TipText_SpectrumGroupsSeparator}}),
            (nameSpaces.WidgetVarName_SpectrumGroupsSelection,
                                {'label':  nameSpaces.Label_SelectSpectrumGroups,
                                'tipText': nameSpaces.TipText_SpectrumGroupSelectionWidget,
                                'callBack': None,
                                'type': settingWidgets.SpectrumGroupSelectionWidget,
                                'kwds': {
                                        'labelText': nameSpaces.Label_SelectSpectrumGroups,
                                        'tipText': nameSpaces.TipText_SpectrumGroupSelectionWidget,
                                        'displayText': [],
                                        'defaults': [],
                                        'standardListItems':[],
                                        'objectName': nameSpaces.WidgetVarName_SpectrumGroupsSelection,
                                        'fixedWidths': SettingsWidgetFixedWidths}, }),
            (nameSpaces.WidgetVarName_PeakProperty,
                                {'label': nameSpaces.Label_PeakProperty,
                                'callBack': None,
                                'tipText': nameSpaces.TipText_PeakPropertySelectionWidget,
                                'type': compoundWidget.PulldownListCompoundWidget,
                                'kwds': {'labelText': nameSpaces.Label_PeakProperty,
                                       'tipText': nameSpaces.TipText_PeakPropertySelectionWidget,
                                       'texts': [],
                                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (nameSpaces.WidgetVarName_DataTableName,
                                {'label': nameSpaces.Label_InputDataTableName,
                                'tipText': nameSpaces.TipText_dataTableNameSelectionWidget,
                                'callBack': None,
                                'enabled': True,
                                'type': compoundWidget.EntryCompoundWidget,
                                '_init': None,
                                'kwds': {'labelText': nameSpaces.Label_InputDataTableName,
                                         'entryText': 'CSM_Input_DataTable',
                                         'tipText': nameSpaces.TipText_dataTableNameSelectionWidget,
                                         'fixedWidths': SettingsWidgetFixedWidths}, }),
            (nameSpaces.WidgetVarName_CreateDataTable,
                                {'label': nameSpaces.Label_CreateInput,
                                'tipText': nameSpaces.TipText_createInputdataTableWidget,
                                'callBack': None,
                                'type': compoundWidget.ButtonCompoundWidget,
                                '_init': None,
                                'kwds': {'labelText': nameSpaces.Label_CreateInput,
                                         'text': 'Create', # this is the Button name
                                         'hAlign': 'left',
                                         'tipText': nameSpaces.TipText_createInputdataTableWidget,
                                         'fixedWidths': SettingsWidgetFixedWidths}}),
            (nameSpaces.WidgetVarName_DataTableSeparator,
                                {'label': nameSpaces.Label_DataTables,
                                 'type': LabeledHLine,
                                 'kwds': {'text':nameSpaces.Label_DataTables,
                                          # 'height': 30,
                                          'gridSpan':(1,2),
                                          'colour': DividerColour,
                                          'tipText': nameSpaces.TipText_DataTableSeparator}}),
            (nameSpaces.WidgetVarName_DataTablesSelection,
             {'label': nameSpaces.Label_SelectDataTable,
              'tipText': nameSpaces.TipText_DataTableSelection,
              'callBack': None,
              'type': settingWidgets.DataTableSelectionWidget,
              'kwds': {
                  'labelText': nameSpaces.Label_SelectDataTable,
                  'tipText': nameSpaces.TipText_DataTableSelection,
                  'displayText': [],
                  'defaults': [],
                  'standardListItems': [],
                  'objectName': nameSpaces.WidgetVarName_DataTablesSelection,
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
        buttonWidget = self.getWidget(nameSpaces.WidgetVarName_CreateDataTable)
        if buttonWidget:
            buttonWidget.button.clicked.connect(self._createInputDataTableCallback)

    def _setPeakPropertySelection(self):
        "Allow  selection of 'Position' or 'LineWidth' for creating a new input DataTable. "
        peakPropertyWidget = self.getWidget(nameSpaces.WidgetVarName_PeakProperty)
        if peakPropertyWidget:
            properties = [seriesVariables._PPMPOSITION, seriesVariables._LINEWIDTH]
            peakPropertyWidget.setTexts(properties)

    def _limitSelectionOnInputData(self):
        "Allow only one selection on SpectrumGroups and DataTable. "
        sgSelectionWidget = self.getWidget(nameSpaces.WidgetVarName_SpectrumGroupsSelection)
        dtSelectionWidget = self.getWidget(nameSpaces.WidgetVarName_DataTablesSelection)

        if sgSelectionWidget:
            sgSelectionWidget.setMaximumItemSelectionCount(1)
        if dtSelectionWidget:
            dtSelectionWidget.setMaximumItemSelectionCount(1)

    def _createInputDataTableCallback(self, *args):
        """ """
        settingsPanelHandler = self._guiModule.settingsPanelHandler
        inputSettings = settingsPanelHandler.getInputDataSettings()
        sgPids = inputSettings.get(nameSpaces.WidgetVarName_SpectrumGroupsSelection, [None])
        spGroup = self._guiModule.project.getByPid(sgPids[-1])
        dataTableName = inputSettings.get(nameSpaces.WidgetVarName_DataTableName, None)
        peakProperty = inputSettings.get(nameSpaces.WidgetVarName_PeakProperty, seriesVariables._PPMPOSITION)  #this should give a warning if wrong
        if not spGroup:
            getLogger().warn('Cannot create an input DataTable without a SpectrumGroup. Select one first')
            return
        backend = self._guiModule.backendHandler
        da = backend.newDataTableFromSpectrumGroup(spGroup, dataTableName=dataTableName, thePeakProperty=peakProperty)
        backend.addInputDataTable(da)
        getLogger().info('Successfully created new Input Data. Item available on the DataTable selection')

TABPOS += 1


class CSMCalculationPanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = nameSpaces.Label_Calculation
    tabTipText = nameSpaces.TipText_CSMCalculationPanelPanel

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        extraLabels_ddCalculationsModes = [model.MaTex for modelName, model in ChemicalShiftCalculationModes.items()]
        tipTexts_ddCalculationsModes = [model.FullDescription for modelName, model in
                                        ChemicalShiftCalculationModes.items()]
        extraLabelPixmaps = [maTex2Pixmap(maTex) for maTex in extraLabels_ddCalculationsModes]
        settingsDict = od((
            (nameSpaces.WidgetVarName_DeltaDeltasSeparator,
             {'label': nameSpaces.Label_DeltaDeltas,
               'type': LabeledHLine,
               'kwds': {'text':  nameSpaces.Label_DeltaDeltas,
                        'height': 30,
                        'gridSpan':(1,2),
                        'colour': DividerColour,
                        'tipText': nameSpaces.TipText_DeltaDeltasSeparator}}),
            (nameSpaces.WidgetVarName_DDCalculationMode,
             {'label': nameSpaces.Label_DDCalculationMode,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': self._calculationModePostInit,
              'kwds': {'labelText' : nameSpaces.Label_DDCalculationMode,
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
            label = nameSpaces.Label_Factor.format(**{nameSpaces.AtomName:atomName})
            att = nameSpaces.WidgetVarName_Factor.format(**{nameSpaces.AtomName:atomName})
            tT = nameSpaces.TipText_Factor.format(**{nameSpaces.AtomName:atomName, nameSpaces.FactorValue:factorValue})
            factorsDict[att] = {'label': label,
            'callBack': None,
            'tipText': nameSpaces.TipText_Factor,
            'type': compoundWidget.DoubleSpinBoxCompoundWidget,
            'kwds': {'labelText': label,
                    'tipText': tT,
                    'value':factorValue,
                    'range': (0.001, 1), 'step': 0.01, 'decimals': 4,
                    'fixedWidths': SettingsWidgetFixedWidths}}
        settingsDict.update(factorsDict)
        restOfWidgetDict = od((
            (nameSpaces.WidgetVarName_FollowAtoms,
             {'label': nameSpaces.Label_FollowAtoms,
              'tipText': nameSpaces.TipText_FollowAtoms,
              'callBack': None,
              'type': settingWidgets.UniqueNmrAtomNamesSelectionWidget,
              'postInit': self._followAtomsWidgetPostInit,
              'kwds': {
                  'labelText': nameSpaces.Label_FollowAtoms,
                  'tipText': nameSpaces.TipText_FollowAtoms,
                  'texts': seriesVariables.DEFAULT_FILTERING_ATOMS,
                  'defaults': seriesVariables.DEFAULT_FILTERING_ATOMS,
                  'objectName': nameSpaces.WidgetVarName_FollowAtoms,
                  'standardListItems': [],
                  'fixedWidths': SettingsWidgetFixedWidths
              }}),
            (nameSpaces.WidgetVarName_ExcludeResType,
             {'label': nameSpaces.Label_ExcludeResType,
              'tipText': nameSpaces.TipText_ExcludeResType,
              'postInit': self._excludeResiduesWidgetPostInit,
              'callBack': None,
              'type': settingWidgets.UniqueNmrResidueTypeSelectionWidget,
              'kwds': {
                  'labelText': nameSpaces.Label_ExcludeResType,
                  'tipText': nameSpaces.TipText_ExcludeResType,
                  'texts': [],
                  'defaults': [],
                  'standardListItems': [],
                  'objectName': nameSpaces.WidgetVarName_ExcludeResType,
                  'fixedWidths': SettingsWidgetFixedWidths
              }}),

            (nameSpaces.WidgetVarName_DisappearedPeak,
             {'label': nameSpaces.Label_DisappearedPeak,
              'tipText': nameSpaces.TipText_DisappearedPeak,
              'callBack': None,
              'enabled': True,
              'type': compoundWidget.DoubleSpinBoxCompoundWidget,
              '_init': None,
              'kwds': {'labelText': nameSpaces.Label_DisappearedPeak,
                       'tipText': nameSpaces.TipText_DisappearedPeak,
                       'value': 1,
                       'fixedWidths': SettingsWidgetFixedWidths}, }),
            ('CalculateDeltaDelta_separator',
             {'label': 'CalculateDeltaDelta_separator',
              'type': LabeledHLine,
              'kwds': {'text': '',
                       # 'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': ''}}),

            (nameSpaces.WidgetVarName_CalculateDeltaDelta,
             {'label': nameSpaces.WidgetVarName_CalculateDeltaDelta,
              'tipText': nameSpaces.TipText_CalculateDeltaDelta,
              'callBack': None,
              'type': compoundWidget.ButtonCompoundWidget,
              '_init': None,
              'kwds': {'labelText': nameSpaces.Label_CalculateDeltaDelta,
                       'text': 'Calculate',  # this is the Button name
                       'callback': self._calculateDeltaDeltaCallback,
                       'hAlign': 'left',
                       'tipText': nameSpaces.TipText_CalculateDeltaDelta,
                       'fixedWidths': SettingsWidgetFixedWidths}}),

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
            att = nameSpaces.WidgetVarName_Factor.format(**{nameSpaces.AtomName:atomName})
            widget = self.getWidget(att)
            if widget is not None:
                factors.update({atomName:widget.getValue()})
        return factors

    def getSettingsAsDict(self):
        """Add the Factors in a dict, instead of single entries for each atom """
        extraSettings = {nameSpaces.ALPHA_FACTORS:self._getAlphaFactors()}
        settings = super(CSMCalculationPanel, self).getSettingsAsDict()
        settings.update(extraSettings)
        return settings

    def _calculateDeltaDeltaCallback(self, *args):
        getLogger().info(f'Recalculating {nameSpaces.DELTAdelta} ...')
        settingsPanelHandler = self._guiModule.settingsPanelHandler
        calculationSettings = self.getSettingsAsDict()
        _filteringAtoms = calculationSettings.get(nameSpaces.WidgetVarName_FollowAtoms, [])
        _alphaFactors = calculationSettings.get(nameSpaces.ALPHA_FACTORS, {})
        # need to remove this hack asap:
        useAlphaFactors = {}
        for atom in _filteringAtoms:
            useAlphaFactors.update({atom:_alphaFactors.get(atom[0])})
        backend = self._guiModule.backendHandler
        backend._AlphaFactors = list(useAlphaFactors.values())
        backend._FilteringAtoms = list(useAlphaFactors.keys())
        inputDataTables = backend.inputDataTables
        if not inputDataTables:
            getLogger().warning('Cannot calculate DeltaShifts. No inputData available')
            return
        dataTable = inputDataTables[-1]
        deltasDF = backend.calculateDeltaDeltaShifts(dataTable.data,
                                                     FilteringAtoms=list(useAlphaFactors.keys()),
                                                     AlphaFactors=list(useAlphaFactors.values()) ,
                                                    )


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
            (nameSpaces.WidgetVarName_FittingSeparator,
             {'label': nameSpaces.Label_FittingSeparator,
              'type': LabeledHLine,
              'kwds': {'text': nameSpaces.Label_FittingSeparator,
                       'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': nameSpaces.TipText_FittingSeparator}}),
            (nameSpaces.WidgetVarName_FittingModel,
             {'label': nameSpaces.Label_FittingModel,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': None,
              'tipText': nameSpaces.TipText_FittingModel,
              'kwds': {'labelText': nameSpaces.Label_FittingModel,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {'texts': list(ChemicalShiftCalculationModels.keys()),
                                        'extraLabels': extraLabels_ddCalculationsModels,
                                        'tipTexts': tipTexts_ddCalculationsModels,
                                        'direction': 'v',
                                        'tipText': '',
                                        'hAlign': 'l',
                                        'extraLabelIcons': extraLabelPixmaps}}}),
            (nameSpaces.WidgetVarName_OptimiserSeparator,
             {'label': nameSpaces.Label_OptimiserSeparator,
              'type': LabeledHLine,
              'kwds': {'text': nameSpaces.Label_OptimiserSeparator,
                       'height': 30,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': nameSpaces.TipText_OptimiserSeparator}}),
            (nameSpaces.WidgetVarName_OptimiserMethod,
             {'label': nameSpaces.Label_OptimiserMethod,
              'callBack': None,
              'tipText': nameSpaces.TipText_PeakPropertySelectionWidget,
              'type': compoundWidget.PulldownListCompoundWidget,
              'kwds': {'labelText': nameSpaces.Label_OptimiserMethod,
                       'tipText': nameSpaces.TipText_OptimiserMethod,
                       'texts': ['leastsq', 'differential_evolution', 'ampgo', 'newton'],
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (nameSpaces.WidgetVarName_ErrorMethod,
             {'label': nameSpaces.Label_ErrorMethod,
              'callBack': None,
              'tipText': nameSpaces.TipText_ErrorMethod,
              'type': compoundWidget.PulldownListCompoundWidget,
              'kwds': {'labelText': nameSpaces.Label_ErrorMethod,
                       'tipText': nameSpaces.TipText_ErrorMethod,
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

            (nameSpaces.WidgetVarName_CalculateFitting,
             {'label': nameSpaces.Label_CalculateFitting,
              'tipText': nameSpaces.TipText_CalculateFitting,
              'callBack': None,
              'type': compoundWidget.ButtonCompoundWidget,
              '_init': None,
              'kwds': {'labelText': nameSpaces.Label_CalculateDeltaDelta,
                       'text': 'Calculate',  # this is the Button name
                       'callback': self._calculateFittingCallback,
                       'hAlign': 'left',
                       'tipText': nameSpaces.TipText_CalculateFitting,
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
        getLogger().info(f'Recalculating {nameSpaces.DELTAdelta} ...')

        backend = self._guiModule.backendHandler
        backend.fitInputData(**{seriesVariables.OUTPUT_DATATABLE_NAME: 'CSM_outPut_fitting'})



TABPOS += 1

class AppearancePanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = nameSpaces.AppearancePanel
    tabTipText = ''

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        settingsDict = od((
            (nameSpaces.WidgetVarName_GenAppearanceSeparator,
             {'label': nameSpaces.Label_GeneralAppearance,
              'type': LabeledHLine,
              'kwds': {'text': nameSpaces.Label_GeneralAppearance,
                       'height': 30,
                       'colour': DividerColour,
                       'gridSpan': (1, 2),
                       'tipText': nameSpaces.TipText_GeneralAppearance}}),
            (nameSpaces.WidgetVarName_ThreshValue,
             {'label': nameSpaces.Label_ThreshValue,
              'tipText': nameSpaces.TipText_ThreshValue,
              'callBack': None,
              'enabled': True,
              'type': compoundWidget.DoubleSpinBoxCompoundWidget,
              '_init': None,
              'kwds': {'labelText': nameSpaces.Label_ThreshValue,
                       'tipText': nameSpaces.TipText_ThreshValue,
                       'value': 0.1,
                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (nameSpaces.WidgetVarName_PredefThreshValue,
             {'label': nameSpaces.Label_PredefThreshValue,
              'tipText': nameSpaces.TipText_PredefThreshValue,
              'callBack': None,
              'enabled': True,
              'type': compoundWidget.ButtonCompoundWidget,
              '_init': None,
              'kwds': {'labelText': nameSpaces.Label_PredefThreshValue,
                       'tipText': nameSpaces.TipText_PredefThreshValue,
                       'text':nameSpaces.Label_StdThreshValue,
                       'fixedWidths': SettingsWidgetFixedWidths
                       }}),
            (nameSpaces.WidgetVarName_AboveThrColour,
             {'label': nameSpaces.Label_AboveThrColour,
              'callBack': None,
              'tipText': nameSpaces.TipText_AboveThrColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': nameSpaces.Label_AboveThrColour,
                       'tipText': nameSpaces.TipText_PeakPropertySelectionWidget,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds':{'includeGradients': True}}}),
            (nameSpaces.WidgetVarName_BelowThrColour,
             {'label': nameSpaces.Label_BelowThrColour,
              'callBack': None,
              'tipText': nameSpaces.TipText_BelowThrColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': nameSpaces.Label_BelowThrColour,
                       'tipText': nameSpaces.TipText_BelowThrColour,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds':{'includeGradients': True}}}),
            (nameSpaces.WidgetVarName_UntraceableColour,
             {'label': nameSpaces.Label_UntraceableColour,
              'callBack': None,
              'tipText': nameSpaces.TipText_UntraceableColour,
              'type': compoundWidget.ColourSelectionCompoundWidget,
              'kwds': {'labelText': nameSpaces.Label_UntraceableColour,
                       'tipText': nameSpaces.TipText_UntraceableColour,
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds':{'includeGradients': True}}}),
            (nameSpaces.WidgetVarName_MolStrucSeparator,
             {'label': nameSpaces.Label_MolStrucSeparator,
              'type': LabeledHLine,
              'kwds': {'text': nameSpaces.Label_MolStrucSeparator,
                       'height': 30,
                       'colour': DividerColour,
                       'gridSpan': (1, 2),
                       'tipText': nameSpaces.TipText_MolStrucSeparator}}),
            (nameSpaces.WidgetVarName_MolStructureFile,
             {'label': nameSpaces.Label_MolStructureFile,
              'tipText': nameSpaces.TipText_MolStructureFile,
              'enabled': True,
              'type': compoundWidget.EntryPathCompoundWidget,
              '_init': None,
              'kwds': {
                  'labelText': nameSpaces.Label_MolStructureFile,
                       'tipText': nameSpaces.TipText_MolStructureFile,
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
