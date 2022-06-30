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
__dateModified__ = "$dateModified: 2022-06-30 14:25:23 +0100 (Thu, June 30, 2022) $"
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
from ccpn.framework.lib.experimentAnalysis.ChemicalShiftMappingAnalysisBC import ChemicalShiftMappingAnalysisBC
from ccpn.util.Logging import getLogger

######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiManagers import PanelHandler,\
    SettingsPanelHandler, IOHandler
from ccpn.ui.gui.widgets.MessageDialog import showWarning
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiSettingsPanel as settingsPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBar import ToolBarPanel
from ccpn.ui.gui.modules.experimentAnalysis.CSMGuiTable import CSMTablePanel
from ccpn.ui.gui.modules.experimentAnalysis.CSMBarPlotPanel import CSMBarPlotPanel
from ccpn.ui.gui.modules.experimentAnalysis.CSMFitPlotPanel import CSMFitPlotPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiModuleBC import ExperimentAnalysisGuiModuleBC

#####################################################################
#######################  The main GUI Module ########################
#####################################################################

class ChemicalShiftMappingGuiModule(ExperimentAnalysisGuiModuleBC):

    className = 'ChemicalShiftMapping'

    def __init__(self, mainWindow, name='Chemical Shift Mapping (Beta)', **kwds):
        super(ExperimentAnalysisGuiModuleBC, self)
        ExperimentAnalysisGuiModuleBC.__init__(self, mainWindow=mainWindow, name=name)

        ## link to the Non-Gui backend and its Settings
        self.backendHandler = ChemicalShiftMappingAnalysisBC()

        ## Startup with the first Data available
        if self.project:
            pass


    #################################################################
    #####################      Widgets    ###########################
    #################################################################

    def addPanels(self):
        """ Add the Gui Panels to the panelHandler.
        Each Panel is a stand-alone frame with information where about to be added on the general GUI.
        Override in Subclasses"""
        self.panelHandler.addToolBar(ToolBarPanel(self))
        self.panelHandler.addPanel(CSMTablePanel(self))
        self.panelHandler.addPanel(CSMFitPlotPanel(self))
        self.panelHandler.addPanel(CSMBarPlotPanel(self))

    def addSettingsPanels(self):
        """
        Add the Settings Panels to the Gui. To retrieve a Panel use/see the settingsPanelsManager.
        """
        self.settingsPanelHandler.append(settingsPanel.CSMGuiInputDataPanel(self))
        self.settingsPanelHandler.append(settingsPanel.CSMCalculationPanel(self))
        self.settingsPanelHandler.append(settingsPanel.CSMGuiFittingPanel(self))
        self.settingsPanelHandler.append(settingsPanel.AppearancePanel(self))


    #####################################################################
    #####################  Widgets callbacks  ###########################
    #####################################################################

    def updateAll(self):
        """ Update all Gui panels"""
        if not self.outputDataTables:

            if self.inputDataTables:
                self.backendHandler.fitInputData()
                getLogger().warn('Requested an update before fitting data. Fitting available InputData ')
            else:
                showWarning('InputData','Add/create an Input DataTable from Settings')
        super(ChemicalShiftMappingGuiModule, self).updateAll()


    def restoreWidgetsState(self, **widgetsState):
        # with self.blockWidgetSignals():
        super().restoreWidgetsState(**widgetsState)
        ## restore and apply filters correctly

    def _closeModule(self):
        ## de-register/close all notifiers
        super()._closeModule()





#################################
######    Testing GUI   #########
#################################
if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
    app = TestApplication()
    win = QtWidgets.QMainWindow()
    moduleArea = CcpnModuleArea(mainWindow=None, )
    m = ChemicalShiftMappingGuiModule(mainWindow=None)
    moduleArea.addModule(m)
    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.show()
    app.start()
