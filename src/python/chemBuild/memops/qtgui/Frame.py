import sys

from PyQt5 import QtGui, QtWidgets

from .Base import Base

class Frame(QtWidgets.QFrame, Base):

  def __init__(self, parent=None, **kw):

    QtWidgets.QFrame.__init__(self, parent)
    Base.__init__(self, parent, **kw)

if __name__ == '__main__':

  from .Application import Application
  from .BasePopup import BasePopup

  app = Application()
  popup = BasePopup(title='Test Frame')
  popup.resize(400, 400)
  frame = Frame(parent=popup)
  app.start()

