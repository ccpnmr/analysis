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
__dateModified__ = "$dateModified: 2022-06-01 16:20:00 +0100 (Wed, June 01, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2022-05-20 12:59:02 +0100 (Fri, May 20, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
from ccpn.ui.gui.modules.experimentAnalysis.ExperimentAnalysisGuiPanel import GuiPanel
######## gui/ui imports ########
from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets.Label import Label, DividerLabel
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Button import Button

FilterButton = 'filterButton'
UpdateButton = 'updateButton'
ShowStructureButton = 'showStructureButton'
Callback = 'Callback'

class ToolBarPanel(GuiPanel):
    """
    A GuiPanel containing the ToolBar Widgets for the Experimental Analysis Module
    """

    position = 0
    panelName = 'ToolBar'

    toolButtons = {}

    def __init__(self, guiModule, *args, **Framekwargs):
        GuiPanel.__init__(self, guiModule, *args , **Framekwargs)
        self.setMaximumHeight(100)

    def initWidgets(self):

        toolButtonsDefs = {
            FilterButton: {
                'text': '',
                'icon': 'icons/filter',
                'tipText': 'Apply filters as defined in settings',
                'toggle': True,
                'callback': f'_{FilterButton}{Callback}',  # the exact name as the function def
                'objectName': FilterButton,
            },

            UpdateButton: {
                'text': '',
                'icon': 'icons/update',
                'tipText': 'Update all data and GUI',
                'toggle': None,
                'callback': f'_{UpdateButton}{Callback}',
                'objectName': UpdateButton,
            },
            ShowStructureButton: {
                'text': '',
                'icon': 'icons/showStructure',
                'tipText': 'Show on Molecular Viewer',
                'toggle': None,
                'callback': f'_{ShowStructureButton}{Callback}',
                'objectName': UpdateButton,
            }}

        colPos = 0
        for i, buttonName in enumerate(toolButtonsDefs, start=1):
            colPos+=i
            callbackAtt = toolButtonsDefs.get(buttonName).pop('callback')
            button = Button(self, **toolButtonsDefs.get(buttonName), grid=(0, colPos))
            callback = getattr(self, callbackAtt or '', None)
            button.setCallback(callback)
            button.setMaximumHeight(25)
            button.setMaximumWidth(25)
            setattr(self, buttonName, button)
            self.toolButtons.update({buttonName:button})

        self.getLayout().setAlignment(QtCore.Qt.AlignLeft)

    def getButton(self, name):
        return self.toolButtons.get(name)

    def _filterButtonCallback(self):
        getLogger().warn('Not implemented. Clicked _filterButtonCallback')

    def _updateButtonCallback(self):
        getLogger().warn('Not implemented. Clicked _updateButtonCallback')

    def _showStructureButtonCallback(self):
        getLogger().warn('Not implemented. Clicked _showStructureButtonCallback')

