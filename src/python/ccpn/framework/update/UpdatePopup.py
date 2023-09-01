"""
Module Documentation Here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-09-01 11:44:04 +0100 (Fri, September 01, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:40 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets
import contextlib

# don't remove this import
import ccpn.core
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.popups.Dialog import CcpnDialogMainWidget
from ccpn.ui.gui.widgets.Font import getFontHeight
from ccpn.util.Update import UpdateAgent
from ccpn.framework.Version import applicationVersion


REFRESHBUTTONTEXT = 'Refresh Updates Information'
DOWNLOADBUTTONTEXT = 'Download/Install Updates'
UPDATELICENCEKEYTEXT = 'Update LicenceKey'
CLOSEEXITBUTTONTEXT = 'Close and Exit'


class UpdatePopup(CcpnDialogMainWidget):
    def __init__(self, parent=None, mainWindow=None, title='Update CCPN code', **kwds):
        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        # keep focus on this window
        self.setModal(True)

        # Derive application, project, and current from mainWindow
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.preferences = mainWindow.application.preferences
        else:
            self.application = self.project = self.preferences = None

        version = applicationVersion
        self._updatePopupAgent = UpdateAgent(version, dryRun=False,
                                             showInfo=self._showInfo, showError=self._showError,
                                             _updateProgressHandler=self._refreshQT)

        self.setWindowTitle(title)
        self._setWidgets(version)

        self.setFixedWidth(self.sizeHint().width())
        self._hideInfoBox()
        # self._showInfoBox()

        # initialise the popup
        self._updatesInstalled = False
        self._updateCount = 0
        self._updateVersion = None
        self.resetFromServer()

        self._updateButton.setEnabled(self._updatePopupAgent._check())
        self._downloadButton = self.buttonList.getButton(DOWNLOADBUTTONTEXT)
        self._downloadButton.setEnabled(self._updateCount > 0)

        # initialise the buttons and dialog size
        self.setDefaultButton(None)
        self._postInit()

    def _setWidgets(self, version):
        """Set the widgets.
        """
        row = 0
        #label = Label(self, 'Server location:', grid=(row, 0))
        #label = Label(self, self.server, grid=(row, 1))
        #row += 1
        # align all widgets to the top
        self.mainWidget.getLayout().setAlignment(QtCore.Qt.AlignTop)
        label = Label(self.mainWidget, 'Installation location:', grid=(row, 0), gridSpan=(1, 2))
        label = Label(self.mainWidget, text=self._updatePopupAgent.installLocation, grid=(row, 2))
        row += 1
        label = Label(self.mainWidget, 'Version:', grid=(row, 0), gridSpan=(1, 2))
        self.versionLabel = Label(self.mainWidget, text='TBD', grid=(row, 2))
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
        _style = f'QPushButton {{padding-left: {_height}px; padding-right: {_height}px; padding-top: 1px; padding-bottom: 1px;}}'
        for button in self.buttonList.buttons:
            button.setStyleSheet(_style)
        self._updateButton.setStyleSheet(_style)
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

        # why does this not resize correctly in self.mainWidget?
        self.infoBox = TextEditor(self.mainWidget, grid=(row, 0), gridSpan=(1, 3))  # NOTE:ED - do not set valign here
        self.infoBox.setVisible(False)
        self.infoBox.setEnabled(True)
        self.infoBox.setReadOnly(True)

        # why???
        self.mainWidget.setMaximumSize(QtCore.QSize(3000, 3000))

    def _resetClicked(self):
        """Reset button clicked,update the count and reset the download button
        """
        self.resetFromServer()
        self._downloadButton.setEnabled(self._updateCount > 0)

    def _install(self):
        """The update button has been clicked. Install updates and flag that files have been changed
        """
        self._showInfoBox()
        self._handleUpdates()

        # # not very nice but refreshes the popup first
        # QtCore.QTimer.singleShot(0, self._handleUpdates)

    def _handleUpdates(self):

        from ccpn.framework.PathsAndUrls import ccpnBinPath, ccpnBatchPath
        from ccpn.util.Common import isWindowsOS
        from subprocess import PIPE, Popen, STDOUT, CalledProcessError
        from ccpn.util.Update import FAIL_UNEXPECTED

        exitCode = 0
        if isWindowsOS():
            from os import startfile

            startfile(ccpnBatchPath / 'update')

        else:
            # start a process and continuously read the stdout to the textbox
            process = Popen([ccpnBinPath / 'update'], stdout=PIPE, stderr=STDOUT, text=True, bufsize=1, universal_newlines=True)
            for line in process.stdout:
                self._showInfo(line)
            exitCode = process.wait()
            # if exitCode >= FAIL_UNEXPECTED:
            #     CalledProcessError(exitCode, process.args)

        self._updatesInstalled = True
        self.buttonList.getButton(self.CLOSEBUTTONTEXT).setText(CLOSEEXITBUTTONTEXT)
        self._downloadButton.setEnabled(bool(exitCode != 0))

        self.resetFromServer()

        # resize due to change in button text
        QtCore.QTimer.singleShot(0, self._checkWidth)

    def _checkWidth(self):
        """Resize to account for the slighty wider buttons.
        """
        _width = self.sizeHint().width() + 100  # still not sure why I need to add constant here :|
        self.setFixedWidth(_width)

    def _closeProgram(self):
        """Call the mainWindow close function giving user option to save, then close program
        """
        self.accept()

    def _accept(self):
        """Close button has been clicked, close if files have been updated or close dialog
        """
        if self._updatesInstalled:
            self._closeProgram()
        else:
            self.accept()

    def _doUpdate(self):
        self._resetMd5()
        self._updateButton.setEnabled(False)

    def reject(self):
        """Dialog-frame close button has been clicked, close if files have been updated or close dialog
        """
        if self._updatesInstalled:
            self._closeProgram()
        else:
            super(UpdatePopup, self).reject()

    def _runProcess(self, command, text=False):
        """Run a system process and return any stdout/stderr.
        """
        if not isinstance(command, list) and all(isinstance(val, str) for val in command):
            raise TypeError(f'Invalid command structure - {command}')

        from subprocess import PIPE, Popen
        from ccpn.framework.PathsAndUrls import ccpnBinPath, ccpnBatchPath
        from ccpn.util.Common import isWindowsOS

        if isWindowsOS():
            from os import startfile

        else:
            query = Popen(command, stdout=PIPE, stderr=PIPE, text=text, bufsize=1)
            status, error = query.communicate()
            if query.poll() == 0:
                with contextlib.suppress(Exception):
                    return status

    def resetFromServer(self):
        """Get current number of updates from the server
        """
        from subprocess import PIPE, Popen
        from ccpn.framework.PathsAndUrls import ccpnBinPath, ccpnBatchPath
        from ccpn.util.Common import isWindowsOS

        count = 0
        version = '-'
        if isWindowsOS():
            from os import startfile

            # startfile(ccpnBatchPath / 'update', '--count')

        else:
            if (response := self._runProcess([ccpnBinPath / 'update', '--count', '--version'], text=True)) is not None:
                count, version = [val.strip() for val in response.split(',')]

        self._updateCount = int(count)
        self.updatesLabel.set(f'{count}')
        self.versionLabel.set(f'{version}')

        self._updatePopupAgent.resetFromServer()

    def closeEvent(self, event) -> None:
        self.reject()

    def _showInfoBox(self):
        self.infoBox.show()
        _width = self.sizeHint().width()
        _height = self.sizeHint().height()
        # self.setMinimumHeight(8 * getFontHeight())
        # self.setMaximumHeight(16 * getFontHeight())
        self.setMinimumHeight(_height)
        self.setMaximumHeight(int(_height * 2.5))
        self.resize(QtCore.QSize(_width, int(_height * 2.5)))
        self._refreshQT()

    def _hideInfoBox(self):
        self.infoBox.hide()
        _height = self.sizeHint().height()
        # self.setFixedHeight(8 * getFontHeight())
        self.setFixedHeight(_height)
        self._refreshQT()

    def _showInfo(self, *args):
        self._showInfoBox()
        for arg in args:
            if arg:
                txt = f'<span style="color:#101010;" >{arg}</span>'
                self.infoBox.append(txt)

    def _showError(self, *args):
        self._showInfoBox()
        for arg in args:
            if arg:
                txt = f'<span style="color:#ff1008;" >{arg}</span>'
                self.infoBox.append(txt)

    def _refreshQT(self):
        # force a refresh of the popup - makes the updating look a little cleaner
        self.repaint()
        QtWidgets.QApplication.processEvents()

    def _checkAtStartupCallback(self, value):
        if self.preferences:
            self.preferences.general.checkUpdatesAtStartup = value


def main():
    # QApplication must be persistent until end of main
    qtApp = QtWidgets.QApplication(['Update'])

    QtCore.QCoreApplication.setApplicationName('Update')
    QtCore.QCoreApplication.setApplicationVersion('3.0.1')

    popup = UpdatePopup()
    popup.exec_()


if __name__ == '__main__':
    main()
