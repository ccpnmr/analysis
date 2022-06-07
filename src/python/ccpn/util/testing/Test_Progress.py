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
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-06-07 19:13:35 +0100 (Tue, June 07, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-05-31 10:16:51 +0100 (Tue, May 31, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import tqdm
from time import sleep
from ccpn.ui.gui.widgets.Application import newTestApplication
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.core.lib.ContextManagers import progressManager
from ccpn.framework.Application import getApplication


def showTestProgressDialog():
    """Show a test dialog for a few seconds
    """
    start, end = 40, 99
    with progressManager(minimum=start, maximum=end, delay=2000) as progress:

        # set extra progress-dialog settings here
        progress.setText('counting')

        try:
            for cc in range(start, end):
                if progress.wasCanceled():
                    break

                # wait for 1/10 seconds
                sleep(0.1)

                # update the progress-bar and the text
                progress.setValue(cc)
                progress.setText(f'counting {cc}%')

            progress.finalise()
            # progress.setValue(end)
            # progress.close()

        except Exception as es:
            print(f'{es}')
        else:
            print(f'okay')

        finally:
            # set closing conditions here
            pass


def main():
    gui = True

    # create a new test application
    _app = newTestApplication(interface='Gui' if gui else 'NoUi')
    app = getApplication()

    if app.hasGui:
        app.ui.mainWindow.show()
        showWarning('progress bar', 'Waiting...')

    # show progress dialog
    showTestProgressDialog()


if __name__ == '__main__':
    main()
