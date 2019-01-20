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
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank$"
__date__ = "$Date: 9/05/2017 $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.core.lib import Undo
from ccpn.ui.gui.widgets.MessageDialog import showWarning


class NotesPopup(CcpnDialog):
    """
    Open a small popup to allow changing the name of a Note
    """

    def __init__(self, parent=None, mainWindow=None, note=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='Edit Note', **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.note = note

        self.noteLabel = Label(self, "Name ", grid=(0, 0))
        self.noteText = LineEdit(self, self.note.name, grid=(0, 1))
        ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(1, 1))

    def _okButton(self):
        """
        When ok button pressed: update Note and exit
        """
        #TODO:ED doesn't need _startCommandEchoBlock yet
        newName = self.noteText.text()
        if str(newName) != self.note.name:
            try:
                self.note.rename(newName)  # rename covers the undo event
                self.accept()

            except Exception as es:
                showWarning('Notes', str(es))
                if self.application._isInDebugMode:
                    raise es
        else:
            self.accept()  # no change so accept and exit
