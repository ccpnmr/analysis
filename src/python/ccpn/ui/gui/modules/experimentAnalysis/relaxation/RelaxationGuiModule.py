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
__dateModified__ = "$dateModified: 2022-08-18 18:08:36 +0100 (Thu, August 18, 2022) $"
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
from ccpn.framework.lib.experimentAnalysis.RelaxationAnalysisBC import RelaxationAnalysisBC
from ccpn.util.Logging import getLogger
######## gui/ui imports ########
from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBar import ToolBarPanel
from ccpn.ui.gui.modules.experimentAnalysis.relaxation.RelaxationBarPlotPanel import RelaxationBarPlotPanel
from ccpn.ui.gui.modules.experimentAnalysis.relaxation.RelaxationFitPlotPanel import RelaxationFitPlotPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiTable import TablePanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiModuleBC import ExperimentAnalysisGuiModuleBC
import ccpn.ui.gui.modules.experimentAnalysis.relaxation.RelaxationSettingsPanel as settingsPanel

#####################################################################
#######################  The main GUI Module ########################
#####################################################################

class RelaxationGuiModule(ExperimentAnalysisGuiModuleBC):

    className = 'Relaxation'

    def __init__(self, mainWindow, name='Relaxation (Alpha)', **kwds):
        super(ExperimentAnalysisGuiModuleBC, self)

        ## link to the Non-Gui backend and its Settings
        backendHandler = RelaxationAnalysisBC()
        ExperimentAnalysisGuiModuleBC.__init__(self, mainWindow=mainWindow, name=name, backendHandler=backendHandler)

    #################################################################
    #####################      Widgets    ###########################
    #################################################################

    def addPanels(self):
        """ Add the Gui Panels to the panelHandler.
        Each Panel is a stand-alone frame with information where about to be added on the general GUI.
        Override in Subclasses"""
        self.panelHandler.addToolBar(ToolBarPanel(self))
        self.panelHandler.addPanel(TablePanel(self))
        self.panelHandler.addPanel(RelaxationFitPlotPanel(self))
        self.panelHandler.addPanel(RelaxationBarPlotPanel(self))

    def addSettingsPanels(self):
        """
        Add the Settings Panels to the Gui. To retrieve a Panel use/see the settingsPanelsManager.
        """
        self.settingsPanelHandler.append(settingsPanel.RelaxationGuiInputDataPanel(self))
        self.settingsPanelHandler.append(settingsPanel.RelaxationCalculationPanel(self))
        self.settingsPanelHandler.append(settingsPanel.RelaxationFittingPanel(self))
        self.settingsPanelHandler.append(settingsPanel.RelaxationAppearancePanel(self))



#################################
######    Testing GUI   #########
#################################
if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.widgets.CcpnModuleArea import CcpnModuleArea
    app = TestApplication()
    win = QtWidgets.QMainWindow()
    moduleArea = CcpnModuleArea(mainWindow=None, )
    m = RelaxationGuiModule(mainWindow=None)
    moduleArea.addModule(m)
    win.setCentralWidget(moduleArea)
    win.resize(1000, 500)
    win.show()
    app.start()
