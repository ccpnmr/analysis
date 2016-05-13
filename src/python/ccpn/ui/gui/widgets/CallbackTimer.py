"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtCore

class CallbackTimer(QtCore.QTimer):
  
  def __init__(self, callback):
    
    QtCore.QTimer.__init__(self)
    self.setSingleShot(True)
    self.connect(self, QtCore.SIGNAL('timeout()'), callback)
    
if __name__ == '__main__':

  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.Button import Button
  from ccpn.ui.gui.widgets.MainWindow import MainWindow

  def callbackFunc():

    print('callbackFunc()')

  timer = CallbackTimer(callbackFunc)
  
  def startTimer():
    
    if not timer.isActive():
      print('start timer')
      timer.start()
    
  app = TestApplication()

  window = MainWindow()
  frame = window.mainFrame

  button = Button(frame, text='Start timer', callback=startTimer, grid=(0,0))
  button = Button(frame, text='Quit', callback=app.quit, grid=(1,0))

  window.show()

  app.start()

    