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
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.popups.Dialog import CcpnDialog  # ejb
from ccpn.ui.gui.widgets.MessageDialog import showWarning


class NmrChainPopup(CcpnDialog):

    def __init__(self, parent=None, mainWindow=None, nmrChain=None, **kwds):
        """
        Initialise the widget
        """
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle='Edit NmrChain', **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        self.nmrChain = nmrChain
        self.nmrChainLabel = Label(self, "Name ", grid=(0, 0))
        self.nmrChainText = LineEdit(self, nmrChain.shortName, grid=(0, 1))
        buttonList = ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(1, 1))

    def _okButton(self):
        newName = self.nmrChainText.text()
        try:
            if str(newName) != self.nmrChain.shortName:
                self.nmrChain.rename(newName)  # currently okay for undo as only does one thing
            self.accept()

        except Exception as es:
            showWarning(self.windowTitle(), str(es))
            if self.application._isInDebugMode:
                raise es
