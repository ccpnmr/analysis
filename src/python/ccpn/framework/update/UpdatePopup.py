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
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:40 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.util.Update import UpdateAgent

REFRESHBUTTONTEXT = 'Refresh Updates Information'
DOWNLOADBUTTONTEXT = 'Download and Install Updates'
UPDATELICENCEKEYTEXT = 'Update LicenceKey'
# CLOSEBUTTONTEXT = 'Close'
CLOSEEXITBUTTONTEXT = 'Close and Exit'


class UpdatePopup(CcpnDialog, UpdateAgent):
    def __init__(self, parent=None, mainWindow=None, title='Update CCPN code', **kwds):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        # keep focus on this window
        self.setModal(True)

        self.mainWindow = mainWindow

        version = QtCore.QCoreApplication.applicationVersion()
        UpdateAgent.__init__(self, version, dryRun=False)

        self.setWindowTitle(title)

        row = 0

        #label = Label(self, 'Server location:', grid=(row, 0))
        #label = Label(self, self.server, grid=(row, 1))
        #row += 1

        label = Label(self, 'Installation location:', grid=(row, 0), gridSpan=(1,2))
        label = Label(self, text=self.installLocation, grid=(row, 2))
        row += 1

        label = Label(self, 'Version:', grid=(row, 0), gridSpan=(1,2))
        label = Label(self, text=version, grid=(row, 2))
        row += 1

        label = Label(self, 'Number of updates:', grid=(row, 0), gridSpan=(1,2))
        self.updatesLabel = Label(self, text='TBD', grid=(row, 2))
        row += 1

        label = Label(self, 'Installing updates will require a restart of the program.', grid=(row, 0), gridSpan=(1,3))
        row += 1

        self._updateButton = Button(self, text=UPDATELICENCEKEYTEXT, tipText='Update LicenceKey from the server',
                                        callback=self._doUpdate, icon='icons/Filetype-Docs-icon.png', grid=(row, 0))

        row += 1
        texts = (REFRESHBUTTONTEXT, DOWNLOADBUTTONTEXT, self.CLOSEBUTTONTEXT)
        callbacks = (self._resetClicked, self._install, self._accept)
        tipTexts = ('Refresh the updates information by querying server and comparing with what is installed locally',
                    'Install the updates from the server',
                    'Close update dialog')
        icons = ('icons/redo.png', 'icons/dialog-apply.png', 'icons/window-close.png')
        self.buttonList = ButtonList(self, texts=texts, tipTexts=tipTexts, callbacks=callbacks, icons=icons, grid=(row, 0), gridSpan=(1, 3))
        row += 1

        self.setFixedSize(750, 150)

        # initialise the popup
        self.resetFromServer()
        self._numUpdatesInstalled = 0
        self._updateButton.setEnabled(self._check())

        self._downloadButton = self.buttonList.getButton(DOWNLOADBUTTONTEXT)
        self._downloadButton.setEnabled(True if (self.updateFiles and len(self.updateFiles) > 0) else False)

    def _resetClicked(self):
        """Reset button clicked,update the count and reset the download button
        """
        self.resetFromServer()
        self._downloadButton.setEnabled(True if (self.updateFiles and len(self.updateFiles) > 0) else False)

    def _install(self):
        """The update button has been clicked. Install updates and flag that files have been changed
        """
        updateFilesInstalled = self.installUpdates()
        if updateFilesInstalled:
            self._numUpdatesInstalled += len(updateFilesInstalled)
            self.buttonList.getButton(self.CLOSEBUTTONTEXT).setText(CLOSEEXITBUTTONTEXT)

        self._downloadButton.setEnabled(True if (self.updateFiles and len(self.updateFiles) > 0) else False)

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
        self._updateButton.setEnabled(False)

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
    QtCore.QCoreApplication.setApplicationVersion('3.0.0')

    popup = UpdatePopup()
    popup.raise_()
    popup.show()

    sys.exit(qtApp.exec_())
