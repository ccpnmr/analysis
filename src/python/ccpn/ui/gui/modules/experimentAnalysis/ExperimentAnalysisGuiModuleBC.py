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
__dateModified__ = "$dateModified: 2022-08-18 13:02:02 +0100 (Thu, August 18, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

######## core imports ########
from ccpn.framework.Application import getApplication, getCurrent, getProject
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisNotifierHandler import CoreNotifiersHandler
from ccpn.framework.lib.experimentAnalysis.SeriesAnalysisABC import SeriesAnalysisABC
from ccpn.util.Logging import getLogger
from PyQt5.QtCore import pyqtSignal

######## gui/ui imports ########
from PyQt5 import QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiManagers import PanelHandler,\
    SettingsPanelHandler, IOHandler, ExtensionsHandler
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiNamespaces as guiNameSpaces
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiSettingsPanel as settingsPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBar import ToolBarPanel, PanelUpdateState
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiTable import TablePanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisBarPlotPanel import BarPlotPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisFitPlotPanel import FitPlotPanel


#####################################################################
#######################  The main GUI Module ########################
#####################################################################

class ExperimentAnalysisGuiModuleBC(CcpnModule):
    includeSettingsWidget = True
    maxSettingsState = 2
    settingsPosition = 'left'
    className = 'ExperimentAnalysis'
    _includeInLastSeen = False
    settingsChanged = pyqtSignal(dict)

    def __init__(self, mainWindow, name='Experiment Analysis', backendHandler=None, **kwds):
        super(ExperimentAnalysisGuiModuleBC, self)
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        self.project = getProject()
        self.application = getApplication()
        self.current = getCurrent()

        ## link to the Non-Gui backend
        self.backendHandler = backendHandler or SeriesAnalysisABC()

        ## link to Gui Setting-Panels. Needs to be before the GuiPanels
        self.settingsPanelHandler = SettingsPanelHandler(self)
        self.addSettingsPanels()

        ## link to Gui Panels
        self.panelHandler = PanelHandler(self)
        self.addPanels()

        ## link to Core Notifiers (Project/Current)
        self.coreNotifiersHandler = CoreNotifiersHandler(guiModule=self)

        ## link to Input/output. (NYI)
        self.ioHandler = IOHandler(guiModule=self)

        ## link to user extestions - external programs. (NYI)
        self.extensionsHandler = ExtensionsHandler(guiModule=self)

    #################################################################
    #####################      Data       ###########################
    #################################################################

    ### Get the input/output dataTables via the backendHandler.
    @property
    def inputDataTables(self) -> list:
        return self.backendHandler.inputDataTables

    @property
    def outputDataTables(self) -> list:
        return self.backendHandler.getOutputDataTables()

    #################################################################
    #####################      Widgets    ###########################
    #################################################################

    def addPanels(self):
        """ Add the Gui Panels to the panelHandler.
        Each Panel is a stand-alone frame with information where about to be added on the general GUI.
        Override in Subclasses"""
        self._addCommonPanels()

    def addSettingsPanels(self):
        """
        Add the Settings Panels to the Gui. To retrieve a Panel use/see the settingsPanelsManager.
        Override in Subclasses
        """
        self._addCommonSettingsPanels()

    def _addCommonPanels(self):
        """ Add the Common Gui Panels to the panelHandler."""
        self.panelHandler.addToolBar(ToolBarPanel(self))
        self.panelHandler.addPanel(TablePanel(self))
        self.panelHandler.addPanel(FitPlotPanel(self))
        self.panelHandler.addPanel(BarPlotPanel(self))

    def _addCommonSettingsPanels(self):
        """
        Add the Common Settings Panels to the settingsPanelsManager.
        """
        self.settingsPanelHandler.append(settingsPanel.GuiInputDataPanel(self))
        self.settingsPanelHandler.append(settingsPanel.AppearancePanel(self))

    #####################################################################
    #####################  Widgets callbacks  ###########################
    #####################################################################

    def updateAll(self):
        """ Update all Gui panels"""
        getLogger().info(f'Updating All ...')
        backend = self.backendHandler
        if backend._needsRefitting:
            if self.inputDataTables:
                backend.fitInputData()
        getLogger().info(f'{self.className}: Updating all Gui Panels...')
        settingsDict = self.settingsPanelHandler.getAllSettings()
        for panelName, panel in self.panelHandler.panels.items():
            panel.updatePanel(**{guiNameSpaces.SETTINGS: settingsDict})

        #set update done.
        toolbar = self.panelHandler.getToolBarPanel()
        if toolbar:
            toolbar.setUpdateState(PanelUpdateState.DONE)

    def restoreWidgetsState(self, **widgetsState):
        # with self.blockWidgetSignals():
        super().restoreWidgetsState(**widgetsState)
        ## restore and apply filters correctly

    def _closeModule(self):
        ## de-register/close all notifiers
        self.coreNotifiersHandler.close()
        self.panelHandler.close()
        self.extensionsHandler.close()
        self.settingsPanelHandler.close()
        super()._closeModule()
