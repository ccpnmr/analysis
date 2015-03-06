__author__ = 'simon'

from PySide import QtGui
from ccpncore.gui.Base import Base

class Widget(QtGui.QWidget, Base):

  def __init__(self, parent=None, **kw):

    QtGui.QWidget.__init__(self, parent)
    self.setAcceptDrops(True)
    Base.__init__(self, **kw)
    layout = QtGui.QGridLayout()
    self.setLayout(layout)

  def dropEvent(self, event):
    print('dropped')