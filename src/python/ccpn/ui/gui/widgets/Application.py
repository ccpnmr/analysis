"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:51 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from PyQt4 import QtGui, Qt
# from ccpn.ui.gui.guiSettings import monaco12


class Application(QtGui.QApplication):

  def __init__(self, applicationName, applicationVersion, organizationName='CCPN', organizationDomain='ccpn.ac.uk'):

    # QtGui.QApplication.setFont(monaco12)
    QtGui.QApplication.__init__(self, [applicationName,])

    self.setApplicationVersion(applicationVersion)
    self.setOrganizationName(organizationName)
    self.setOrganizationDomain(organizationDomain)

  #   Qt.QObject.connect(self, Qt.SIGNAL("focusChanged(QWidget *, QWidget *)"), self.changedFocusSlot)
  #
  # def changedFocusSlot(old, now):
  #   if (now == None and QtGui.QApplication.activeWindow() != None):
  #     # QtGui.QApplication.activeWindow().setFocus()
  #     old.activeWindow().clearFocus()
  #     old.activeWindow().setFocus()


  def start(self):
    self.exec_()

class TestApplication(Application):
  
  def __init__(self):
    Application.__init__(self, 'testApplication', '1.0')
    
if __name__ == '__main__':

  app = TestApplication()
  w = QtGui.QWidget()
  w.resize(250, 150)
  w.move(300, 300)
  w.setWindowTitle('testApplication')
  w.show()

  app.start()
