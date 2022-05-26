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
__dateModified__ = "$dateModified: 2022-05-26 12:06:36 +0100 (Thu, May 26, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import weakref
from collections import defaultdict
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import PanelPositions, TopFrame, BottomFrame,\
    LeftFrame, RightFrame
from ccpn.ui.gui.widgets.Tabs import Tabs
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Splitter import Splitter


class ExperimentAnalysisHandlerABC(object):
    """
    This object manages a dedicated part of a ExperimentAnalysis GuiModule instance e.g:
        - Backend   (ExperimentAnalysis base class)
        - Notifiers (core and current)
        - Settings  (Tab containing setting widgets)
        - Panels    (Frame containing tables, plotting etc)
        - Files     (I/O)

    Handlers are created internally when you create a ExperimentAnalysis GuiModule.
    You interact with them later, e.g. when you want to start the backend
    process or when you want to install/retrieve a panel.

    example:
        experimentAnalysis = ExperimentAnalysis()
        # use the backend manager to start the backend server
        experimentAnalysis.backend.start(...)
        experimentAnalysis.backend.calculate(...)
        # use the panels controller to install a panel
        experimentAnalysis.panels.install(MyPanel(name))
        panel = experimentAnalysis.panels.get(name)
        # etc

    """

    @property
    def guiModule(self):
        """
        Return a reference to the parent code edit widget.
        """
        return self._guiModule

    def __init__(self, guiModule, autoStart=True):
        """
        :param guiModule: The GuiModule instance to control
        :param autoStart: bool. True to start the handler processes.
        """
        self._guiModule = guiModule
        if autoStart:
            self.start()

    def start(self):
        pass

    def close(self):
        pass

####################################################################################
#########################      The Various Handlers        #########################
####################################################################################

class PanelHandler(ExperimentAnalysisHandlerABC):
    """
    Manages the list of Gui Panels and adds them to the GuiModule.
    """
    gridPositions = {
        TopFrame :   ((0, 0), (1, 2)), #grid and gridSpan
        LeftFrame:   ((1, 0), (1, 1)),
        RightFrame:  ((1, 1), (1, 1)),
        BottomFrame: ((2, 0), (2, 2)),
    }

    def __init__(self, guiModule):
        super(PanelHandler, self).__init__(guiModule)
        self._marginSizes = (0, 0, 0, 0)
        self.panels = defaultdict()
        self._panelsByFrame = {k:[] for k in PanelPositions}

    def start(self):
        """ Setup the four main Frames: Top/Bottom Left/Right """
        for frameName, gridDefs in self.gridPositions.items():
            grid, gridSpan = gridDefs
            setattr(self, frameName, Frame(self.guiModule.mainWidget, setLayout=True, grid=grid, gridSpan=gridSpan))
        self._setupSplitters()
        self.guiModule.mainWidget.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self._setupFrameGeometries()

    def append(self, panel):
        """
        Installs a panel in the proper frame of the MainWidget .
        :param panel: Panel to install
        :return: The installed panel
        """
        panel.onInstall()
        self._addToLayout(panel)
        return panel

    def _addToLayout(self, panel):
        frameAttr = panel._panelPositionData.description
        frame = getattr(self, frameAttr, None)
        if frame is not None:
            frame.getLayout().addWidget(panel)
            self._panelsByFrame[frameAttr].append(panel)
            self.panels.update({panel.panelName:panel})

    def clear(self):
        """
        Removes all panel from the Module.
        """
        pass

    def close(self):
        for name, panel in self.panels.items():
            panel.close()

    def getPanel(self, name):
        panel = self.panels.get(name)
        return panel

    def getFrame(self, name):
        frame = getattr(self, name)
        return frame

    ######## Private methods ######

    def _setupSplitters(self):
        """
        Create splitters and add frames to them. There are two splitters:
         - one "vertical" as it divides vertically the Top/Bottom frames,
         - one "horizontal" between the Left/Right frames .
        The Vertical is the primary splitter that contains the horizontal.
        The Vertical splitter is added to the mainWidget layout.
        (Line-ordering is crucial for the correct layout)
        """
        self._horizontalSplitter = Splitter()
        self._verticalSplitter = Splitter(horizontal=False)
        ## add frames to splitters
        self._horizontalSplitter.addWidget(self.getFrame(LeftFrame))
        self._horizontalSplitter.addWidget(self.getFrame(RightFrame))
        self._verticalSplitter.addWidget(self._horizontalSplitter) # Important: add horizontalSplitter to the Vertical!
        self._verticalSplitter.addWidget(self.getFrame(BottomFrame))
        ## add all to main Layout
        self.guiModule.mainWidget.getLayout().addWidget(self._verticalSplitter)

    def _setupFrameGeometries(self):
        for ff in PanelPositions:
            frame = self.getFrame(ff)
            frame.getLayout().setAlignment(QtCore.Qt.AlignTop)

    def __iter__(self):
        lst = []
        for name, panel in self.panels.items():
            lst.append(panel)
        return iter(lst)

    def __len__(self):
        lst = []
        for name, panel in self.panels.items():
            lst.append(panel)
        return len(lst)


class SettingsPanelHandler(ExperimentAnalysisHandlerABC):
    """
    Manages the list of Tab settings and adds them to the GuiModule settingsWidget.
    """
    def __init__(self, guiModule):
        super(SettingsPanelHandler, self).__init__(guiModule)
        self._marginSizes = (5, 5, 5, 5)
        self._panels = {}
        self.settingsWidget = self.guiModule.settingsWidget
        self.settingsWidget.setContentsMargins(*self._marginSizes)
        self.settingsTabWidget = Tabs(self.settingsWidget, setLayout=True, grid=(0, 0))

    def append(self, panel):
        # add tab to gui
        from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiSettingsPanel import GuiSettingPanel
        if not isinstance(panel, GuiSettingPanel):
            raise RuntimeError(f'{panel} is not of instance: {GuiSettingPanel}')
        self.settingsTabWidget.insertTab(panel.tabPosition, panel, panel.tabName)
        self._panels.update({panel.tabPosition:panel})

    def close(self):
        pass

class BackendHandler(ExperimentAnalysisHandlerABC):
    """
    Manages the no-Gui machinery of the GuiModule.
    This only for consistency. Not sure if adds an extra layer of complexity to get to data.
    """
    def start(self):
        pass
        # needs to start the backend engines and notifiers for settingsChanged
        # self.settingsChanged.register(self.updateAll)
        # self.settingsChanged.setSilentCallback(self._silentCallback)

    def close(self):
        pass
        ## close the settings-Changed notifiers etc

class IOHandler(ExperimentAnalysisHandlerABC):
    """
    Manages the I/O machinery of the GuiModule.
    """
    pass
