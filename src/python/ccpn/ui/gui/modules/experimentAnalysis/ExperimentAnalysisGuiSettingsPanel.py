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
__dateModified__ = "$dateModified: 2022-06-01 16:20:00 +0100 (Wed, June 01, 2022) $"
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

######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets, QtGui
from ccpn.ui.gui.widgets.Label import Label, DividerLabel
import ccpn.ui.gui.widgets.CompoundWidgets as compoundWidget
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons, EditableRadioButtons
import ccpn.ui.gui.widgets.SettingsWidgets as settingWidgets
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.Label import maTex2Pixmap
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisNamespaces as nameSpaces
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
        self.initWidgets()

    def initWidgets(self):
        pass

    def getWidget(self, name):
        pass


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
                                        'objectName': nameSpaces.WidgetVarName_SpectrumGroupsSelection,
                                        'fixedWidths': SettingsWidgetFixedWidths}, }),
            (nameSpaces.WidgetVarName_PeakProperty,
                                {'label': nameSpaces.Label_PeakProperty,
                                'callBack': None,
                                'tipText': nameSpaces.TipText_PeakPropertySelectionWidget,
                                'type': compoundWidget.PulldownListCompoundWidget,
                                'kwds': {'labelText': nameSpaces.Label_PeakProperty,
                                       'tipText': nameSpaces.TipText_PeakPropertySelectionWidget,
                                       'texts': ['Position', 'Height', 'Line-width', 'Volume'],
                                       'fixedWidths': SettingsWidgetFixedWidths}}),
            (nameSpaces.WidgetVarName_DataTableName,
                                {'label': nameSpaces.Label_InputDataTableName,
                                'tipText': nameSpaces.TipText_dataTableNameSelectionWidget,
                                'callBack': None,
                                'enabled': True,
                                'type': compoundWidget.EntryCompoundWidget,
                                '_init': None,
                                'kwds': {'labelText': nameSpaces.Label_InputDataTableName,
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
                                          'gridSpan':(1,2),
                                          'colour': DividerColour,
                                          'tipText': nameSpaces.TipText_DataTableSeparator}}),
            (nameSpaces.WidgetVarName_DataTablesSelection,
             {'label': nameSpaces.Label_SelectDataTable,
              'tipText': nameSpaces.TipText_DataTableSelection,
              'callBack': None,
              'type': settingWidgets.SpectrumGroupSelectionWidget,
              'kwds': {
                  'labelText': nameSpaces.Label_SelectDataTable,
                  'tipText': nameSpaces.TipText_DataTableSelection,
                  'displayText': [],
                  'defaults': [],
                  'objectName': nameSpaces.WidgetVarName_DataTablesSelection,
                  'fixedWidths': SettingsWidgetFixedWidths}, }),
            ))
        self._moduleSettingsWidget = settingWidgets.ModuleSettingsWidget(parent=self, mainWindow=mainWindow,
                                               settingsDict=settingsDict,
                                               grid=(0, 0))
        self._moduleSettingsWidget.getLayout().setAlignment(QtCore.Qt.AlignLeft)

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
        compoundKwds = {'extraLabels': extraLabels_ddCalculationsModes, 'extraLabelIcons': extraLabelPixmaps}
        settingsDict = od((
            (nameSpaces.WidgetVarName_DeltaDeltasSeparator,
             {'label': nameSpaces.Label_DeltaDeltas,
               'type': LabeledHLine,
               'kwds': {'text':  nameSpaces.Label_DeltaDeltas,
                        'gridSpan':(1,2),
                        'colour': DividerColour,
                        'tipText': nameSpaces.TipText_DeltaDeltasSeparator}}),
            (nameSpaces.WidgetVarName_DDCalculationMode,
             {'label': nameSpaces.Label_DDCalculationMode,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': self._calculationModePostInit,
              'kwds': {'labelText' : nameSpaces.Label_DDCalculationMode,
                       'texts' : list(ChemicalShiftCalculationModes.keys()),
                       'tipTexts' : tipTexts_ddCalculationsModes,
                       'direction' : 'v',
                       'hAlign':'l',
                       'tipText' :'',
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds':compoundKwds}}),
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
                    'range': (0.001, 1), 'step': 0.01, 'decimals': 3,
                    'fixedWidths': SettingsWidgetFixedWidths}}
        settingsDict.update(factorsDict)
        restOfWidgetDict = od((
            (nameSpaces.WidgetVarName_FollowAtoms,
             {'label': nameSpaces.Label_FollowAtoms,
              'tipText': nameSpaces.TipText_FollowAtoms,
              'callBack': None,
              'type': settingWidgets.ListCompoundWidget,
              'postInit': self._followAtomsWidgetPostInit,
              'kwds': {
                  'labelText': nameSpaces.Label_FollowAtoms,
                  'tipText': nameSpaces.TipText_FollowAtoms,
                  'texts': [],
                  'defaults': [],
                  'objectName': nameSpaces.WidgetVarName_FollowAtoms,
                  'minimumWidths': (50,50,50)
              }}),
            (nameSpaces.WidgetVarName_ExcludeResType,
             {'label': nameSpaces.Label_ExcludeResType,
              'tipText': nameSpaces.TipText_ExcludeResType,
              'postInit': self._excludeResiduesWidgetPostInit,
              'callBack': None,
              'type': settingWidgets.ListCompoundWidget,
              'kwds': {
                  'labelText': nameSpaces.Label_ExcludeResType,
                  'tipText': nameSpaces.TipText_ExcludeResType,
                  'texts': [],
                  'defaults': [],
                  'objectName': nameSpaces.WidgetVarName_ExcludeResType,
              }}),
            (nameSpaces.WidgetVarName_DDOtherCalculationMode,
             {'label': nameSpaces.Label_DDOtherCalculationMode,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': self._calculationModePostInit,
              'kwds': {'labelText': f'{nameSpaces.Label_DDOtherCalculationMode}',
                       'tipText': nameSpaces.TipText_DDOtherCalculationMode,
                       'texts': ['Ratio', '% Change'],
                       'callback': self._calculationModePostInit,
                       'direction': 'v',
                       'tipTexts': ['Calculate Ratio', 'Calculate the % Change'],
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': {}}}),
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


TABPOS += 1
class GuiCSMFittingPanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = 'Fitting'
    tabTipText = 'Set the various fitting modes and options'

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        extraLabels_ddCalculationsModels = [model.MaTex for modelName, model in ChemicalShiftCalculationModels.items()]
        tipTexts_ddCalculationsModels = [model.FullDescription for modelName, model in
                                        ChemicalShiftCalculationModels.items()]
        extraLabelPixmaps = [maTex2Pixmap(maTex) for maTex in extraLabels_ddCalculationsModels]
        compoundKwds = {'extraLabels': extraLabels_ddCalculationsModels, 'extraLabelIcons': extraLabelPixmaps}
        settingsDict = od((
            (nameSpaces.WidgetVarName_FittingSeparator,
             {'label': nameSpaces.Label_FittingSeparator,
              'type': LabeledHLine,
              'kwds': {'text': nameSpaces.Label_FittingSeparator,
                       'gridSpan': (1, 2),
                       'colour': DividerColour,
                       'tipText': nameSpaces.TipText_FittingSeparator}}),
            (nameSpaces.WidgetVarName_FittingModel,
             {'label': nameSpaces.Label_FittingModel,
              'type': compoundWidget.RadioButtonsCompoundWidget,
              'postInit': None,
              'tipText': nameSpaces.TipText_FittingModel,
              'kwds': {'labelText': nameSpaces.Label_FittingModel,
                       'texts': list(ChemicalShiftCalculationModels.keys()),
                       'tipTexts': tipTexts_ddCalculationsModels,
                       'direction': 'v',
                       'hAlign': 'l',
                       'tipText': '',
                       'fixedWidths': SettingsWidgetFixedWidths,
                       'compoundKwds': compoundKwds}}),
            (nameSpaces.WidgetVarName_OptimiserSeparator,
             {'label': nameSpaces.Label_OptimiserSeparator,
              'type': LabeledHLine,
              'kwds': {'text': nameSpaces.Label_OptimiserSeparator,
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

        ))
        # fittersDict = should be taken from guiModule.backend.fittingModels.
        # For now add to see the widgets layout

        self._moduleSettingsWidget = settingWidgets.ModuleSettingsWidget(parent=self, mainWindow=mainWindow,
                                                                         settingsDict=settingsDict,
                                                                         grid=(0, 0))
        self._moduleSettingsWidget.getLayout().setAlignment(QtCore.Qt.AlignLeft)
        Spacer(self, 0, 2, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding,
               grid=(1, 0), gridSpan=(1, 1))

TABPOS += 1

class AppearancePanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = 'Appearance'
    tabTipText = ''

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        settingsDict = od((
            (nameSpaces.WidgetVarName_GenAppearanceSeparator,
             {'label': nameSpaces.Label_GeneralAppearance,
              'type': LabeledHLine,
              'kwds': {'text': nameSpaces.Label_GeneralAppearance,
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
