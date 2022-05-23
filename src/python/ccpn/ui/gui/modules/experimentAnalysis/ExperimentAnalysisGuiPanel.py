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
__dateModified__ = "$dateModified: 2022-05-23 15:17:37 +0100 (Mon, May 23, 2022) $"
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
This module contains the GUI panel API.
"""


from ccpn.util.DataEnum import DataEnum
######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
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
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.FilteringPulldownList import FilteringPulldownList
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea


TopFrame = 'TopFrame'
LeftFrame = 'LeftFrame'
RightFrame = 'RightFrame'
BottomFrame = 'BottomFrame'

PanelPositions = [TopFrame, LeftFrame, RightFrame, BottomFrame]


class PanelPositionData(DataEnum):
    TOP = 0, TopFrame
    LEFT = 1, LeftFrame
    RIGHT = 2, RightFrame
    BOTTOM = 3, BottomFrame

class GuiPanel(Frame):
    """
    Base class for Gui panels.
    A panel is Frame containing a building block of the Experiment Analysis GUI, E.g.: the nmrResidue table
    """
    position = -1
    panelName = 'panelName'


    def __init__(self, guiModule, *args, **Framekwargs):

        Frame.__init__(self, setLayout=True, **Framekwargs)
        self._panelPositionData = PanelPositionData(self.position)

        self._guiModule = guiModule
        self.initWidgets()

    def initWidgets(self):
        pass

    def onInstall(self):
        pass

    def close(self):
        """ de-register anything left or close table etc"""
        pass



class ToolBarPanel(GuiPanel):

    position = 0
    panelName = 'ToolBar'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setMaximumHeight(100)


    def initWidgets(self):
        row = 0
        Label(self, 'Test Colour', grid=(row, 0))


class TablePanel(GuiPanel):

    position = 1
    panelName = 'TablePanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setMaximumHeight(100)

    def initWidgets(self):
        row = 0
        Label(self, 'Test TablePanel', grid=(row, 0))


class FitPlotPanel(GuiPanel):

    position = 2
    panelName = 'FitPlotPanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setMaximumHeight(100)

    def initWidgets(self):
        row = 0
        Label(self, 'FitPlotPanel', grid=(row, 0))


class BarPlotPanel(GuiPanel):

    position = 3
    panelName = 'BarPlotPanel'

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setMaximumHeight(100)

    def initWidgets(self):
        row = 0
        Label(self, 'PlotPanel', hAlign='c', grid=(row, 0))
