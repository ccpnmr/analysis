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

"""
This module contains the GUI panel API.
"""

from ccpn.util.DataEnum import DataEnum
from ccpn.ui.gui.widgets.Frame import Frame

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

        self.guiModule = guiModule
        self.initWidgets()

    def initWidgets(self):
        pass

    def onInstall(self):
        pass

    def close(self):
        """ de-register anything left or close table etc"""
        pass