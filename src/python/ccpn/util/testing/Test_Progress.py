"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
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
__dateModified__ = "$dateModified: 2022-12-15 15:59:34 +0000 (Thu, December 15, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-05-31 10:16:51 +0100 (Tue, May 31, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from time import sleep
from ccpn.ui.gui.widgets.Application import newTestApplication
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.lib.ContextManagers import progressHandler, busyHandler
from ccpn.framework.Application import getApplication
from ccpn.util.Logging import getLogger


gui = True
error = True


def showTestProgressDialog():
    """Show a test dialog for a few seconds
    """
    start, end = 97, 225

    with progressHandler(minimum=start, maximum=end, steps=20, autoClose=False,
                         raiseErrors=True) as progress:

        progress.setText('counting')  # forces a repaint
        # set extra progress-dialog settings here

        for cc in range(start, end + 1):
            progress.checkCancelled()  # will raise ProgressCancelled exception if pressed
            progress.setValue(cc)  # update the progress-bar if matches step-size

            if error and cc == 198:
                # test generating a cancel event
                progress.cancel()

            # wait for fraction of a second
            sleep(0.03)

    getLogger().info(f'cancelled: {progress.cancelled}')
    getLogger().info(f'error: {progress.error}')


def showTestBusyDialog():
    """Show a test dialog for a few seconds
    """
    start, end = 97, 225

    with busyHandler(minimum=start, maximum=end, steps=20, autoClose=False,
                     raiseErrors=True) as progress:

        progress.setText('counting')  # forces a repaint
        # set extra progress-dialog settings here

        for cc in range(start, end + 1):
            progress.checkCancelled()  # will raise ProgressCancelled exception if pressed
            progress.setValue(cc)  # update the progress-bar if matches step-size

            if error and cc == 198:
                # test generating a cancel event
                progress.cancel()

            # wait for fraction of a second
            sleep(0.03)

    getLogger().info(f'cancelled: {progress.cancelled}')
    getLogger().info(f'error: {progress.error}')


def main():
    # create a new test application
    _app = newTestApplication(interface='Gui' if gui else 'NoUi')
    app = getApplication()

    if app.hasGui:
        # show a waiting popup otherwise the progress may finish before you see it
        app.ui.mainWindow.show()
        showWarning('progress bar', 'Waiting...')

    # show progress dialog
    showTestProgressDialog()
    if gui:
        showTestBusyDialog()

    getLogger().info('end Test_Progress')


if __name__ == '__main__':
    main()
