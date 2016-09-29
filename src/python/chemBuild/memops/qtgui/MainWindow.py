import sys

from PyQt4 import QtGui

from memops.qtgui.Frame import Frame

class MainWindow(QtGui.QMainWindow):

  def __init__(self, parent=None, title='', location=None, hide=False,  **kw):

    QtGui.QMainWindow.__init__(self, parent)

    self.mainFrame = Frame(self)
    self.setCentralWidget(self.mainFrame)

    self.title = title
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

  from .Application import Application
  from .Button import Button

  def callback():
    print('callback')

  app = Application()
  window = MainWindow(title='Test MainWindow')
  button = Button(window.mainFrame, text='hit me', callback=callback)
  app.start()

