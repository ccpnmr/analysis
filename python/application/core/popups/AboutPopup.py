"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'
import os
from ccpncore.util import Path
from PyQt4 import QtGui
from ccpncore.gui.Base import Base
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Label import Label


class AboutPopup(QtGui.QDialog, Base):
  def __init__(self, parent=None, **kw):
    super(AboutPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    splashPng = os.path.join(Path.getPythonDirectory(), 'ccpncore', 'gui', 'ccpnmr-splash-screen.jpg')
    splashPix = QtGui.QPixmap(splashPng)
    self.setFixedSize(671, 659)
    self.label = Label(self, grid=(0, 0), gridSpan=(10, 12))
    self.label.setPixmap(splashPix)
    self.buttonList = ButtonList(self, ['OK'], [self.accept], grid=(9, 10), gridSpan=(1, 1))