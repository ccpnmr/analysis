"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:43 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Frame import Frame

class MainWindow(QtGui.QMainWindow, Base):

  def __init__(self, parent=None, title='', location=None, hide=False, **kw):

    QtGui.QMainWindow.__init__(self, parent)
    Base.__init__(self, **kw)

    self.mainFrame = Frame(self)
    self.setCentralWidget(self.mainFrame)
    self.mainFrame.setAccessibleName('MainWindow Frame')

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

  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.Button import Button

  def callback():
    print('callback')

  app = TestApplication()
  
  window = MainWindow(title='Test MainWindow')
  button = Button(window.mainFrame, text='hit me', callback=callback)
  button = Button(window.mainFrame, text='quit', callback=app.quit)
  
  app.start()

