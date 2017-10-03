

from PyQt5 import QtGui, QtWidgets, QtCore

from ccpn.ui.gui.widgets.Base import Base

class DateTime(QtGui.QDateEdit, Base):

  def __init__(self, parent, **kw):

    QtGui.QDateEdit.__init__(self, parent)

    Base.__init__(self, **kw)
