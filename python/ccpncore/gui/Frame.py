import sys

from PySide import QtGui

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

