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

"""
This module contains the GUI panel API.
"""


from PyQt5 import QtCore, QtWidgets
from ccpn.util.DataEnum import DataEnum
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame

Top = 'Top'
Left = 'Left'
Right = 'Right'
Bottom = 'Bottom'
TopLeft = 'TopLeft'
TopRight = 'TopRight'
BottomLeft = 'BottomLeft'
BottomRight = 'BottomRight'

PanelPositions = [Top, TopLeft, Left, BottomLeft, Right, TopRight, BottomRight, Bottom]
_panelPositionsAttr = [f'_{s[0].lower() + s[1:]}' for s in PanelPositions]


class PanelPosition(DataEnum):
    TOP = 0, Top
    LEFT = 1, Left
    RIGHT = 2, Right
    BOTTOM = 3, Bottom
    TOPLEFT = 4, TopLeft
    TOPRIGHT = 5, TopRight
    BOTTOMLEFT = 6, BottomLeft
    BOTTOMRIGHT = 7, BottomRight

class GuiPanel(Frame):
    """
    Base class for Gui panels.
    A panel is Frame containing a building block of the Experiment Analysis GUI, E.g.: the nmrResidue table
    """
    PanelPosition = PanelPosition
    position = -1

    @property
    def scrollable(self):
        """
        :return: bool
        """
        return self._scrollable

    @scrollable.setter
    def scrollable(self, value):
        self._scrollable = value
        #set the scroll area

    def __init__(self, guiModule, scrollable=False, *args, **Framekwargs):

        Frame.__init__(self, setLayout=True, **Framekwargs)
        self.order_in_zone = -1
        self._scrollable = False
        self._guiModule = guiModule
        self.scrollable = scrollable

    def onInstall(self):
        pass

