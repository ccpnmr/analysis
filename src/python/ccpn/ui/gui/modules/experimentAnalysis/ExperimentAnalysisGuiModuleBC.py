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
__dateModified__ = "$dateModified: 2022-05-27 10:42:33 +0100 (Fri, May 27, 2022) $"
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

######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiManagers import PanelHandler,\
    SettingsPanelHandler, IOHandler, BackendHandler
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiSettingsPanel as settingsPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBar import ToolBarPanel
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

    def __init__(self, mainWindow, name='Experiment Analysis', **kwds):
        super(ExperimentAnalysisGuiModuleBC, self)
        CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

        self.project = getProject()
        self.application = getApplication()
        self.current = getCurrent()

        ## link to the Non-Gui backend and its Settings
        self.backendHandler = BackendHandler(self)

        ## link to Gui Panels
        self.panelHandler = PanelHandler(self)
        self._addCommonPanels()

        ## link to Gui Setting-Panels
        self.settingsPanelHandler = SettingsPanelHandler(self)
        self._addCommonSettingsPanels()

        ## link to Core Notifiers (Project/Current)
        self.coreNotifiersHandler = CoreNotifiersHandler(guiModule=self)

        ## link to Core Notifiers (Project/Current)
        self.ioHandler = IOHandler(guiModule=self)

        ## the working dataTable which drives all Gui
        self._selectedDataTables = () # add comment on what will be, e.g.: Pids

        ## Startup with the first Data available
        if self.project:
            pass

    #################################################################
    #####################      Data       ###########################
    #################################################################

    ### Get the input/output dataTables via the backend.

    #################################################################
    #####################      Widgets    ###########################
    #################################################################

    def _addCommonPanels(self):
        """ Add the Gui Panels to the panelHandler.
        Each Panel is a stand-alone frame with information where about to be added on the general GUI."""
        self.panelHandler.addToolBar(ToolBarPanel(self))
        self.panelHandler.addPanel(TablePanel(self))
        self.panelHandler.addPanel(FitPlotPanel(self))
        self.panelHandler.addPanel(BarPlotPanel(self))

    def _addCommonSettingsPanels(self):
        """
        Add the Settings Panels to the Gui. To retrieve a Panel use/see the settingsPanelsManager.
        """
        self.settingsPanelHandler.append(settingsPanel.GuiCalculationPanel(self))
        self.settingsPanelHandler.append(settingsPanel.AppearancePanel(self))

    #####################################################################
    #####################  Widgets callbacks  ###########################
    #####################################################################

    def restoreWidgetsState(self, **widgetsState):
        # with self.blockWidgetSignals():
        super().restoreWidgetsState(**widgetsState)
        ## restore and apply filters correctly

    def _closeModule(self):
        ## de-register/close all notifiers
        self.coreNotifiersHandler.close()
        self.panelHandler.close()
        self.ioHandler.close()
        self.settingsPanelHandler.close()
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
    m = ExperimentAnalysisGuiModuleBC(mainWindow=None)
    moduleArea.addModule(m)
    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.show()
    app.start()
