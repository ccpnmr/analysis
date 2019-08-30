"""Module Documentation here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:56 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: tjragan $"
__date__ = "$Date: 2016-05-18 09:27:23 +0100 (Wed, 18 May 2016) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from PyQt5 import QtGui, QtWidgets, QtCore
from ccpn.util import Path


class SplashScreen(QtWidgets.QSplashScreen):

    def __init__(self, dummy=None, wait=1):

        splashImagePath = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                                       'splash-screen.png')
        #print(splashImagePath)
        pixmap = QtGui.QPixmap(splashImagePath)
        #super(QtGui.QSplashScreen, self).__init__(pixmap, QtCore.Qt.WindowStaysOnTopHint)
        QtWidgets.QSplashScreen.__init__(self, pixmap, QtCore.Qt.WindowStaysOnTopHint)

        self.show()

        # dummy window; to have something going
        if dummy:
            self.w = QtWidgets.QWidget()
            self.w.resize(dummy[0], dummy[1])
            self.w.show()

        self.wait = wait

    #
    # def info(self, text):
    #   self.showMessage(text, color=QtCore.Qt.white, alignment = QtCore.Qt.AlignBottom)

    def close(self):
        import time

        time.sleep(self.wait)
        if hasattr(self, 'w'):
            self.w.close()
        super(QtWidgets.QSplashScreen, self).close()
