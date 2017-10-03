
from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.widgets.Base import Base

class GroupBox(QtWidgets.QGroupBox, Base):

  def __init__(self, parent=None, border=None, **kw):

    QtWidgets.QGroupBox.__init__(self, parent)
    Base.__init__(self, setLayout=True, **kw)   # ejb

    if border:
      self.setObjectName("borderedGroupBox")
