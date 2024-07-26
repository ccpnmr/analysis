"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-07-04 18:52:00 +0100 (Thu, July 04, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-05-31 10:16:51 +0100 (Tue, May 31, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from time import sleep
from PyQt5 import QtCore
from functools import partial

# don't remove import
import ccpn.core
from ccpn.ui.gui.widgets.Application import newTestApplication
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.lib.ContextManagers import progressHandler, busyHandler
from ccpn.util.Logging import getLogger


gui = False
error = True


def showTestProgressDialog(parent=None):
    """Show a test dialog for a few seconds
    """
    start, end = 97, 225

    with progressHandler(parent, text='progress counting',
                         minimum=start, maximum=end, steps=20,
                         raiseErrors=False) as progress:
        # set extra progress-dialog settings here
        for cc in range(start, end + 1):
            progress.checkCancel()  # will raise StopIteration exception if pressed
            progress.setValue(cc)  # update the progress-bar if matches step-size
            if error and cc == 135:
                # test generating a cancel event
                progress.cancel()
            # wait for fraction of a second
            sleep(0.01)

    getLogger().info(f'progress cancelled: {progress.cancelled} {cc}')
    getLogger().info(f'progress error: {progress.error}')


def showTestBusyDialog(parent=None):
    """Show a test dialog for a few seconds
    """
    start, end = 97, 225

    with busyHandler(parent, text='counting',
                     minimum=start, maximum=end, steps=20,
                     raiseErrors=False) as progress:
        # set extra progress-dialog settings here
        for cc in range(start, end + 1):
            progress.checkCancel()  # will raise StopIteration exception if pressed
            progress.setValue(cc)  # update the progress-bar if matches step-size
            if error and cc == 143:
                # test generating an error event
                raise ValueError('Error here')
            # wait for fraction of a second
            sleep(0.01)

    getLogger().info(f'busy cancelled: {progress.cancelled}')
    getLogger().info(f'busy error: {progress.error}')


def showTestProgressDialogNoStop(parent=None):
    """Show a test dialog for a few seconds
    """
    start, end = 100, 345

    with progressHandler(parent, text='progress2 counting',
                         minimum=start, maximum=end, steps=100,
                         raiseErrors=True) as progress:
        # set extra progress-dialog settings here
        for cc in range(start, end + 1):
            progress.checkCancel()  # will raise StopIteration exception if pressed
            progress.setValue(cc)  # update the progress-bar if matches step-size
            # wait for fraction of a second
            sleep(0.01)

    getLogger().info(f'progress2 cancelled: {progress.cancelled} {cc}')
    getLogger().info(f'progress2 error: {progress.error}')


def _initTest(qtApp):
    app = qtApp._framework
    if app.hasGui:
        # show a waiting popup otherwise the progress may finish before you see it
        app.ui.mainWindow.show()
        showWarning('progress bar', 'Waiting...',
                    parent=app.ui.mainWindow if app.hasGui else None)
    # show progress dialog
    showTestProgressDialog()
    showTestProgressDialogNoStop()
    if gui:
        showTestBusyDialog()
        # shutdown the app - hard shutdown as _closeWindow contains os._exit(0) :|
        # there is an issue somewhere with newTestApplication - not found yet :(
        QtCore.QTimer.singleShot(0, qtApp.closeAllWindows)
    else:
        QtCore.QTimer.singleShot(0, qtApp.quit)
    getLogger().info('end _initTest')


def main():
    # create a new test application
    qtApp = newTestApplication(interface='Gui' if gui else 'NoUi')
    # wait for a couple of seconds before showing popup
    QtCore.QTimer.singleShot(2000, partial(_initTest, qtApp))
    qtApp.start()
    # NEVER GETS HERE -_closeWindow calls os._exit(0)


if __name__ == '__main__':
    main()
