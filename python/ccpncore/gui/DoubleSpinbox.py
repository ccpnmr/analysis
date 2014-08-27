__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpncore.gui.Base import Base

class DoubleSpinbox(QtGui.QDoubleSpinBox, Base):

  def __init__(self, parent, **kw):

    QtGui.QDoubleSpinBox.__init__(self, parent)
    Base.__init__(self, **kw)
