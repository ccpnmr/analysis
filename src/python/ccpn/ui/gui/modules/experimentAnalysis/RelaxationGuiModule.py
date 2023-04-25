#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-04-25 17:41:51 +0100 (Tue, April 25, 2023) $"
__version__ = "$Revision: 3.1.1 $"
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
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
from ccpn.util.Logging import getLogger
######## gui/ui imports ########
from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisToolBars import ToolBarPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisBarPlotPanel import BarPlotPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisFitPlotPanel import FitPlotPanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiTable import TablePanel
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiModuleBC import ExperimentAnalysisGuiModuleBC
import ccpn.ui.gui.modules.experimentAnalysis.RelaxationSettingsPanel as settingsPanel

#####################################################################
#######################  The main GUI Module ########################
#####################################################################

class RelaxationGuiModule(ExperimentAnalysisGuiModuleBC):

    className = 'Relaxation'
    analysisType = sv.RelaxationAnalysis

    def __init__(self, mainWindow, name='Relaxation (Alpha)', **kwds):
        super(ExperimentAnalysisGuiModuleBC, self)

        ## link to the Non-Gui backend and its Settings
        backendHandler = RelaxationAnalysisBC()
        ExperimentAnalysisGuiModuleBC.__init__(self, mainWindow=mainWindow, name=name, backendHandler=backendHandler)

    #################################################################
    #####################      Widgets    ###########################
    #################################################################

    def addPanels(self):
        """ Add the Gui Panels to the panelHandler."""
        super().addPanels()

    def addSettingsPanels(self):
        """
        Add the Settings Panels to the Gui. To retrieve a Panel use/see the settingsPanelsManager.
        """
        self.settingsPanelHandler.append(settingsPanel.RelaxationGuiInputDataPanel(self))
        self.settingsPanelHandler.append(settingsPanel.RelaxationCalculationPanel(self))
        self.settingsPanelHandler.append(settingsPanel.RelaxationFittingPanel(self))
        self.settingsPanelHandler.append(settingsPanel.RelaxationAppearancePanel(self))

