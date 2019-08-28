"""
Module Documentation Here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:20 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:40 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
#from ccpn.ui.gui.widgets.Table import ObjectTable, Column

# from ccpn.framework.update.UpdateAgent import UpdateAgent
from ccpn.util.Update import UpdateAgent


class UpdatePopup(CcpnDialog, UpdateAgent):
    def __init__(self, parent=None, mainWindow=None, title='Update CCPN code', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        # keep focus on this window
        self.setModal(True)

        self.mainWindow = mainWindow

        version = QtCore.QCoreApplication.applicationVersion()
        UpdateAgent.__init__(self, version)

        self.setWindowTitle(title)

        row = 0

        #label = Label(self, 'Server location:', grid=(row, 0))
        #label = Label(self, self.server, grid=(row, 1))
        #row += 1

        label = Label(self, 'Installation location:', grid=(row, 0))
        label = Label(self, text=self.installLocation, grid=(row, 1))
        row += 1

        label = Label(self, 'Version:', grid=(row, 0))
        label = Label(self, text=version, grid=(row, 1))
        row += 1

        label = Label(self, 'Number of updates:', grid=(row, 0))
        self.updatesLabel = Label(self, text='TBD', grid=(row, 1))
        row += 1

        label = Label(self, 'Installing updates will require a restart of the program.', grid=(row, 0))
        row += 1

        texts = ('Refresh Updates Information', 'Download and Install Updates', 'Update Licence', 'Close')
        callbacks = (self.resetFromServer, self._install, self._doUpdate, self._accept)
        tipTexts = ('Refresh the updates information by querying server and comparing with what is installed locally',
                    'Install the updates from the server',
                    'Update Licence from the server',
                    'Close update dialog')
        icons = ('icons/null.png', 'icons/dialog-apply.png', 'icons/dialog-apply.png', 'icons/window-close.png')
        self.buttonList = ButtonList(self, texts=texts, tipTexts=tipTexts, callbacks=callbacks, icons=icons, grid=(row, 0), gridSpan=(1, 2))
        row += 1

        self.setFixedSize(750, 150)

        # initialise the popup
        self.resetFromServer()
        self._numUpdatesInstalled = 0
        self.buttonList.getButton('Update Licence').setEnabled(self._check())

    def _install(self):
        """The update button has been clicked. Install updates and flag that files have been changed
        """
        updateFilesInstalled = self.installUpdates()
        if updateFilesInstalled:
            self._numUpdatesInstalled += len(updateFilesInstalled)
            self.buttonList.buttons[2].setText('Close and Exit')

    def _closeProgram(self):
        """Call the mainWindow close function giving user option to save, then close program
        """
        self.accept()

    def _accept(self):
        """Close button has been clicked, close if files have been updated or close dialog
        """
        if self._numUpdatesInstalled:
            self._closeProgram()
        else:
            self.accept()

    def _doUpdate(self):
        self._resetMd5()
        self.buttonList.getButton('Update Licence').setEnabled(False)

    def reject(self):
        """Dialog-frame close button has been clicked, close if files have been updated or close dialog
        """
        if self._numUpdatesInstalled:
            self._closeProgram()
        else:
            super(UpdatePopup, self).reject()

    def resetFromServer(self):
        """Get current number of updates from the server
        """
        UpdateAgent.resetFromServer(self)
        self.updatesLabel.set('%d' % len(self.updateFiles))


if __name__ == '__main__':
    import sys


    qtApp = QtWidgets.QApplication(['Update'])

    QtCore.QCoreApplication.setApplicationName('Update')
    QtCore.QCoreApplication.setApplicationVersion('3.0')

    popup = UpdatePopup()
    popup.raise_()
    popup.show()

    sys.exit(qtApp.exec_())
