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
__dateModified__ = "$dateModified: 2022-05-20 18:40:05 +0100 (Fri, May 20, 2022) $"
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
import pandas as pd
import numpy as np
from functools import partial
from ccpn.util.Logging import getLogger
from ccpn.core.Peak import Peak
from ccpn.core.Substance import Substance
from ccpn.core.Spectrum import Spectrum
from ccpn.core.DataTable import DataTable
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.lib.ContextManagers import notificationEchoBlocking
from ccpn.util.Common import percentage
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisNotifierHandler import _NotifierHandler

######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Label import Label, DividerLabel
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.CompoundWidgets import ListCompoundWidget, ScientificSpinBoxCompoundWidget
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons, EditableRadioButtons
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.GuiTable import _selectRowsOnTable
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.widgets.ScatterPlotWidget import ScatterPlot, _ItemBC, ScatterSymbolsDict
from ccpn.ui.gui.widgets.MessageDialog import showWarning, _stoppableProgressBar, progressManager
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiManagers import PanelsManager, SettingsPanelManager
import ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiSettingsPanel as settingsPanel


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

        if self.mainWindow:
            self._notifierHandler = _NotifierHandler(guiModule=self)

        ## link to the Non-Gui backend
        # self._backend = SeriesAnalysisABC()
        # self._backend.settingsChanged.register(self.updateAll)
        # self._backend.settingsChanged.setSilentCallback(self._silentCallback)

        ## settings on PeakChange queue
        self._updateSilent = True
        self.updatesOnPeakChanged = False
        self._peaksChangedQueue = set() # temp store any peaks that have been changed but not refreshed on GUI

        ## the working dataTable which drives all
        self._dataTable = None

        ## link to gui Panels
        self._initLayout()
        self.panelsManager = PanelsManager(self)
        self.settingsPanelsManager = SettingsPanelManager(self)
        self._initPanels()
        self._initSettingsPanel()

        ## Startup with the first Data available
        if self.project:
            self._updateDataSetPulldown()

    #################################################################
    #####################      Data       ###########################
    #################################################################


    #################################################################
    #####################      Widgets    ###########################
    #################################################################

    def _initLayout(self):
        # Splitters are created automatically between two panels. Splitters are nasty!
        # if a panel is flagged as top and one as bottom, then a horizontal splitter is created.
        pass


    def _initPanels(self):
        pass

    def _initSettingsPanel(self):
        """
        Add the Settings Panels to the Gui. To retrieve a Panel use/see the settingsPanelsManager.
        """
        self.settingsPanelsManager.append(settingsPanel.GuiCalculationPanel(self))
        self.settingsPanelsManager.append(settingsPanel.AppearancePanel(self))

    #####################################################################
    #####################  Widgets callbacks  ###########################
    #####################################################################


    def restoreWidgetsState(self, **widgetsState):
        self._updateSilent = True
        # with self.blockWidgetSignals():
        super().restoreWidgetsState(**widgetsState)
        self._updateSilent = False
        ## restore and apply filters correctly


    def _closeModule(self):
        ## de-register all notifiers
        _NotifierHandler._unRegisterNotifiers()
        ## close tables
        # pass
        ## deregistr settingsChanged notifiers
        # self.module -> .settingsChanged.deregister()
        super()._closeModule()


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
