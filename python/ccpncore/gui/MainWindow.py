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
from ccpncore.gui.Frame import Frame

class MainWindow(QtGui.QMainWindow, Base):

  def __init__(self, parent=None, title='', location=None, hide=False, **kw):

    QtGui.QMainWindow.__init__(self, parent)
    Base.__init__(self, **kw)

    self.mainFrame = Frame(self)
    self.setCentralWidget(self.mainFrame)

    self.setWindowTitle(title)

    if location:
      self.move(*location)

    if hide:
      self.hide()
    else:
      self.show()
      self.raise_()

  def setSize(self, w, h):
  
    self.setGeometry(self.x(), self.y(), w, h)

if __name__ == '__main__':

  from ccpncore.gui.Application import TestApplication
  from ccpncore.gui.Button import Button

  def callback():
    print('callback')

  app = TestApplication()
  
  window = MainWindow(title='Test MainWindow')
  button = Button(window.mainFrame, text='hit me', callback=callback)
  button = Button(window.mainFrame, text='quit', callback=app.quit)
  
  app.start()

