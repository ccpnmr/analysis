from PySide import QtGui

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

