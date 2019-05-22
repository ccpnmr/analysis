

from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.Base import Base

class DateTime(QtWidgets.QDateEdit, Base):

  def __init__(self, parent, **kwds):

    super().__init__(parent)
    Base._init(self, **kwds)
