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
__dateModified__ = "$dateModified: 2022-05-26 12:38:12 +0100 (Thu, May 26, 2022) $"
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
This module contains the GUI Settings panels.
"""


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



class GuiSettingPanel(Frame):
    """
    Base class for GuiSettingPanel.
    A panel is Frame which will create a tab in the Gui Module settings
    """

    tabPosition = -1
    tabName = 'tab'

    def __init__(self, guiModule,  *args, **Framekwargs):
        Frame.__init__(self, setLayout=True, **Framekwargs)
        self._guiModule = guiModule
        self.getLayout().setAlignment(QtCore.Qt.AlignTop)
        self.initWidgets()

    def initWidgets(self):
        pass



class GuiCalculationPanel(GuiSettingPanel):

    tabPosition = 0
    tabName = 'Calculation'

    def initWidgets(self):
        row = 0
        self.calculationModeLabel = Label(self, 'Test Mode', grid=(row, 0))
        texts = ['A', 'B', 'C']
        objectNames = ['calculationMode_' + x for x in texts]
        self.calculationModeOptions = EditableRadioButtons(self, selectedInd=0, texts=texts,
                                                           direction='v',
                                                           callback=None,
                                                           objectName='calculationMode',
                                                           objectNames=objectNames,
                                                           grid=(row, 1))

class AppearancePanel(GuiSettingPanel):

    tabPosition = 1
    tabName = 'Appearance'

    def initWidgets(self):
        row = 0
        Label(self, 'Test Colour', grid=(row, 0))
        EditableRadioButtons(self, selectedInd=0, texts=['A','B','C',],
                                                           direction='v',
                                                           callback=None,
                                                           objectName='TestColour',
                                                           grid=(row, 1))
