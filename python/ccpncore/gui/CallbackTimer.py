from PySide import QtCore

class CallbackTimer(QtCore.QTimer):
  
  def __init__(self, callback):
    
    QtCore.QTimer.__init__(self)
    self.setSingleShot(True)
    self.connect(self, QtCore.SIGNAL('timeout()'), callback)
    
if __name__ == '__main__':

  from ccpncore.gui.Application import TestApplication
  from ccpncore.gui.Button import Button
  from ccpncore.gui.MainWindow import MainWindow

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

    