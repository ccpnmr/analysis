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

from PyQt4 import QtGui

from ccpncore.gui.Base import Base

class Frame(QtGui.QFrame, Base):

  def __init__(self, parent=None, **kw):

    QtGui.QFrame.__init__(self, parent)
    Base.__init__(self, **kw)

if __name__ == '__main__':

  from ccpncore.gui.Application import TestApplication
  from ccpncore.gui.BasePopup import BasePopup

  class TestPopup(BasePopup):
    def body(self, parent):
      frame = Frame(parent=parent, bgColor=QtGui.QColor(255, 255, 0))

  app = TestApplication()
  popup = TestPopup(title='Test Frame')
  popup.resize(400, 400)
  app.start()

