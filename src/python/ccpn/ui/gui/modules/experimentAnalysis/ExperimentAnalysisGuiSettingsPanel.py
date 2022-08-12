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
__dateModified__ = "$dateModified: 2022-08-12 10:46:29 +0100 (Fri, August 12, 2022) $"
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
                getLogger().warn('Could not find get for: varName, widget',  varName, widget, e)
        return settingsDict

    def _setUpdatedDetectedState(self):
        """ set update detected on toolbar icons. """
        toolbar = self._guiModule.panelHandler.getToolBarPanel()
        if toolbar:
            toolbar.setUpdateState(PanelUpdateState.DETECTED)

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
        self._moduleSettingsWidget = settingWidgets.ModuleSettingsWidget(parent=self, mainWindow=mainWindow,
                                               settingsDict=settingsDict,
                                               grid=(0, 0))
        self._moduleSettingsWidget.getLayout().setAlignment(QtCore.Qt.AlignLeft)


    def _addInputDataCallback(self, *args):

        backend = self._guiModule.backendHandler
        dataTablePids = self.getSettingsAsDict().get(guiNameSpaces.WidgetVarName_DataTablesSelection, [])
        if not dataTablePids:
            self._guiModule.backendHandler.clearInputDataTables()
            getLogger().info(f'{self._guiModule.className}:{self.tabName}. Cleaned inputDataTables')
            return
        for pid in dataTablePids:
            obj = self._guiModule.project.getByPid(pid)
            if obj:
                backend.addInputDataTable(obj)
                getLogger().info(f'{self._guiModule.className}:{self.tabName}. {obj} added to inputDataTables')

        self._guiModule.updateAll()
