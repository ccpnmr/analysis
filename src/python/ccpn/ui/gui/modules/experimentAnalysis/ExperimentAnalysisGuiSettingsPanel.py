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
__dateModified__ = "$dateModified: 2022-05-31 10:23:00 +0100 (Tue, May 31, 2022) $"
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
from ccpn.framework.lib.experimentAnalysis.CSMFittingModels import ChemicalShiftCalculationModes, DeltaDeltaShiftsCalculation

######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets

from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets.Label import Label, DividerLabel
import ccpn.ui.gui.widgets.CompoundWidgets as compoundWidget
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons, EditableRadioButtons
import ccpn.ui.gui.widgets.SettingsWidgets as settingWidgets
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.Label import maTex2Pixmap
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisNamespaces as nameSpaces
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as seriesVariables


SettingsWidgeMinimumWidths =  (180, 180, 180)
SettingsWidgetFixedWidths = (200, 200, 200)

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
    tabTipText = nameSpaces.tipText_GuiInputDataPanel

    def initWidgets(self):
        mainWindow = self._guiModule.mainWindow
        settingsDict = od((
            (nameSpaces.WidgetVarName_SpectrumGroupsSeparator,
                                {'label': nameSpaces.Label_SpectrumGroups,
                                 'type': compoundWidget.LabelCompoundWidget,
                                 'kwds': {'labelText': nameSpaces.Label_SpectrumGroups,
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
                                'type': compoundWidget.LabelCompoundWidget,
                                'kwds': {'labelText': nameSpaces.Label_DataTables,
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
        journalReference = nameSpaces.TipText_DeltaDeltasSeparator
        settingsDict = od((
            (nameSpaces.WidgetVarName_DeltaDeltasSeparator,
             {'label': nameSpaces.Label_DeltaDeltas,
              'type': compoundWidget.LabelCompoundWidget,
              'kwds': {'labelText': nameSpaces.Label_DeltaDeltas,
                       'tipText': journalReference}}),
            (nameSpaces.WidgetVarName_DDCalculationMode,
            {'label': nameSpaces.Label_DDCalculationMode,
             'type': compoundWidget.LabelCompoundWidget,
             'kwds': {'labelText': f'{nameSpaces.Label_DDCalculationMode}:\n{DeltaDeltaShiftsCalculation.ModelName}',
                      'tipText': DeltaDeltaShiftsCalculation.FullDescription,
                      'label2Text': DeltaDeltaShiftsCalculation.ModelName,
                      'icon':maTex2Pixmap(f'{DeltaDeltaShiftsCalculation.MaTex}'),
                      'compoundKwds':{}}}),
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
              }})
        ))
        settingsDict.update(restOfWidgetDict)
        self._moduleSettingsWidget = settingWidgets.ModuleSettingsWidget(parent=self, mainWindow=mainWindow,
                                                                         settingsDict=settingsDict,
                                                                         grid=(0, 0))
        self._moduleSettingsWidget.getLayout().setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)

    def _followAtomsWidgetPostInit(self, widget, *args):
        widget.listWidget.setFixedHeight(100)
        widget.setMaximumWidths(SettingsWidgetFixedWidths)
        widget.getLayout().setAlignment(QtCore.Qt.AlignTop)

    def _excludeResiduesWidgetPostInit(self, widget, *args):
        widget.listWidget.setFixedHeight(100)
        widget.setFixedWidths(SettingsWidgetFixedWidths)
        widget.getLayout().setAlignment(QtCore.Qt.AlignTop)


class GuiFittingPanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = 'Fitting'
    tabTipText = 'Set the various fitting modes and options'

    def initWidgets(self):
        row = 0
        self.calculationModeLabel = Label(self, 'Test Mode', grid=(row, 0))
        texts = ['A', 'B', 'C']
        objectNames = ['calculationMode_' + x for x in texts]
        self.calculationModeOptions = EditableRadioButtons(self, selectedInd=0, texts=texts,
                                                           direction='v',
                                                           callback=None,
                                                           objectName='calculationMode',
                                                           objectNames=objectNames,
                                                           grid=(row, 1))
TABPOS += 1

class AppearancePanel(GuiSettingPanel):

    tabPosition = TABPOS
    tabName = 'Appearance'
    tabTipText = ''

    def initWidgets(self):
        row = 0
        Label(self, 'Test Colour', grid=(row, 0))
        EditableRadioButtons(self, selectedInd=0, texts=['A','B','C',],
                                                           direction='v',
                                                           callback=None,
                                                           objectName='TestColour',
                                                           grid=(row, 1))

TABPOS += 1
