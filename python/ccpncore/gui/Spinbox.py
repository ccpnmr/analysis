__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpncore.gui.Base import Base

class Spinbox(QtGui.QSpinBox, Base):

  def __init__(self, parent, **kw):

    QtGui.QSpinBox.__init__(self, parent)
    Base.__init__(self, **kw)
