"""Module Documentation here
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-05-18 09:27:23 +0100 (Wed, 18 May 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license "
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: tjragan $"
__date__ = "$Date: 2016-05-18 09:27:23 +0100 (Wed, 18 May 2016) $"
__version__ = "$Revision: 9353 $"

#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore

from ccpn.util import Path

class SplashScreen(QtGui.QSplashScreen):

  def __init__(self, dummy=None, wait=1):

    splashImagePath = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                                                        'ccpnmr-splash-screen.jpg')
    #print(splashImagePath)
    pixmap = QtGui.QPixmap(splashImagePath)
    #super(QtGui.QSplashScreen, self).__init__(pixmap, QtCore.Qt.WindowStaysOnTopHint)
    QtGui.QSplashScreen.__init__(self, pixmap, QtCore.Qt.WindowStaysOnTopHint)

    self.show()

    # dummy window; to have something going
    if dummy:
      self.w = QtGui.QWidget()
      self.w.resize(dummy[0],dummy[1])
      self.w.show()

    self.wait = wait

  def info(self, text):
    self.showMessage(text, color=QtCore.Qt.white, alignment = QtCore.Qt.AlignBottom)

  def close(self):
    import time
    time.sleep(self.wait)
    if hasattr(self,'w'):
        self.w.close()
    super(QtGui.QSplashScreen, self).close()

