"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:50 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-07-04 09:28:16 +0000 (Tue, July 04, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning


class StructurePopup(CcpnDialog):
    """
    Open a small popup to allow changing the label of a StructureEnsemble
    """

    def __init__(self, parent=None, mainWindow=None, title='StructureEnsembles', structureEnsemble=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.structure = structureEnsemble
        self.structureLabel = Label(self, "Structure Name: " + self.structure.pid, grid=(0, 0))
        self.structureText = LineEdit(self, self.structure.name, grid=(0, 1))
        ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(1, 1))

    def _okButton(self):
        """
        When ok button pressed: update StructureEnsemble and exit
        """
        newName = self.structureText.text()
        try:
            if str(newName) != self.structure.name:
                self.structure.rename(newName)
            self.accept()

        except Exception as es:
            showWarning(self.windowTitle(), str(es))
            if self.application._isInDebugMode:
                raise es
