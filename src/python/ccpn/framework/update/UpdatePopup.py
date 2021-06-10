"""
Module Documentation Here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-06-10 14:59:40 +0100 (Thu, June 10, 2021) $"
__version__ = "$Revision: 3.0.4 $"
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
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.util.Update import UpdateAgent
from ccpn.ui.gui.widgets.Font import setWidgetFont, getFontHeight


REFRESHBUTTONTEXT = 'Refresh Updates Information'
DOWNLOADBUTTONTEXT = 'Download/Install Updates'
UPDATELICENCEKEYTEXT = 'Update LicenceKey'
# CLOSEBUTTONTEXT = 'Close'
CLOSEEXITBUTTONTEXT = 'Close and Exit'


class UpdatePopup(CcpnDialogMainWidget, UpdateAgent):
    def __init__(self, parent=None, mainWindow=None, title='Update CCPN code', **kwds):
        CcpnDialogMainWidget.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        # keep focus on this window
        self.setModal(True)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.preferences = mainWindow.application.preferences
        else:
            self.application = None
            self.project = None
            self.preferences = None

        version = QtCore.QCoreApplication.applicationVersion()
        UpdateAgent.__init__(self, version, dryRun=False,
                             showInfo=self._showInfo, showError=self._showError,
                             _updateProgressHandler=self._refreshQT)

        self.setWindowTitle(title)

        row = 0

        #label = Label(self, 'Server location:', grid=(row, 0))
        #label = Label(self, self.server, grid=(row, 1))
        #row += 1

        # align all widgets to the top
        self.mainWidget.getLayout().setAlignment(QtCore.Qt.AlignTop)

        label = Label(self.mainWidget, 'Installation location:', grid=(row, 0), gridSpan=(1, 2))
        label = Label(self.mainWidget, text=self.installLocation, grid=(row, 2))
        row += 1

        label = Label(self.mainWidget, 'Version:', grid=(row, 0), gridSpan=(1, 2))
        label = Label(self.mainWidget, text=version, grid=(row, 2))
        row += 1

        label = Label(self.mainWidget, 'Number of updates:', grid=(row, 0), gridSpan=(1, 2))
        self.updatesLabel = Label(self.mainWidget, text='TBD', grid=(row, 2))
        row += 1

        label = Label(self.mainWidget, 'Installing updates will require a restart of the program.', grid=(row, 0), gridSpan=(1, 3))
        row += 1

        self._updateButton = Button(self.mainWidget, text=UPDATELICENCEKEYTEXT, tipText='Update LicenceKey from the server',
                                    callback=self._doUpdate, icon='icons/Filetype-Docs-icon.png', grid=(row, 0))

        row += 1
        texts = (REFRESHBUTTONTEXT, DOWNLOADBUTTONTEXT, self.CLOSEBUTTONTEXT)
        callbacks = (self._resetClicked, self._install, self._accept)
        tipTexts = ('Refresh the updates information by querying server and comparing with what is installed locally',
                    'Install the updates from the server',
                    'Close update dialog')
        icons = ('icons/redo.png', 'icons/dialog-apply.png', 'icons/window-close.png')
        self.buttonList = ButtonList(self.mainWidget, texts=texts, tipTexts=tipTexts, callbacks=callbacks, icons=icons, grid=(row, 0), gridSpan=(1, 3),
                                     setMinimumWidth=False)

        # set some padding for the buttons
        _height = getFontHeight()
        for button in self.buttonList.buttons:
            button.setStyleSheet("padding-left: {}px; padding-right: {}px; padding-top: 0px; padding-bottom: 0px;".format(_height, _height))
        self._updateButton.setStyleSheet("padding-left: {}px; padding-right: {}px; padding-top: 0px; padding-bottom: 0px;".format(_height, _height))

        row += 1

        if self.preferences:
            checkAtStartup = CheckBoxCompoundWidget(self.mainWidget,
                                                    grid=(row, 0), hAlign='left', gridSpan=(1, 3),
                                                    # fixedWidths=(None, 30),
                                                    orientation='right',
                                                    labelText='Check for updates at startup',
                                                    checked=self.preferences.general.checkUpdatesAtStartup,
                                                    callback=self._checkAtStartupCallback)
            row += 1

        self.infoBox = TextEditor(self.mainWidget, grid=(row, 0), gridSpan=(1, 3))  # NOTE:ED - do not set valign here
        self.infoBox.setVisible(False)

        self.setFixedWidth(self.sizeHint().width())
        self._hideInfoBox()
        # self._showInfoBox()

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
        self._showInfoBox()
        self._handleUpdates()

        # # not very nice but refreshes the popup first
        # QtCore.QTimer.singleShot(0, self._handleUpdates)

    def _handleUpdates(self):
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

    def closeEvent(self, event) -> None:
        self.reject()

    def _showInfoBox(self):
        self.infoBox.show()
        _height = self.sizeHint().height()
        # self.setMinimumHeight(8 * getFontHeight())
        # self.setMaximumHeight(16 * getFontHeight())
        self.setMinimumHeight(_height)
        self.setMaximumHeight(_height * 2)
        self.resize(QtCore.QSize( self.width(), _height * 2))
        self._refreshQT()

    def _hideInfoBox(self):
        self.infoBox.hide()
        _height = self.sizeHint().height()
        # self.setFixedHeight(8 * getFontHeight())
        self.setFixedHeight(_height)
        self._refreshQT()

    def _showInfo(self, *args):
        for arg in args:
            self.infoBox.append(arg)

    def _showError(self, *args):
        self._showInfoBox()
        for arg in args:
            self.infoBox.append(arg)

    def _refreshQT(self):
        # force a refresh of the popup - makes the updating look a little cleaner
        self.repaint()
        QtWidgets.QApplication.processEvents()

    def _checkAtStartupCallback(self, value):
        if self.preferences:
            self.preferences.general.checkUpdatesAtStartup = value


if __name__ == '__main__':
    import sys
    import os


    qtApp = QtWidgets.QApplication(['Update'])

    QtCore.QCoreApplication.setApplicationName('Update')
    QtCore.QCoreApplication.setApplicationVersion('3.0.1')

    popup = UpdatePopup()
    popup.exec_()

    # os._exit(qtApp.exec_()) - not required with exec_
