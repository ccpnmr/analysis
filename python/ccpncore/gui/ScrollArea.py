__author__ = 'simon'

from PySide import QtGui, QtCore

from ccpncore.gui.Base import Base

class ScrollArea(QtGui.QScrollArea, Base):

  def __init__(self, parent, **kw):

    QtGui.QScrollArea.__init__(self, parent)

    Base.__init__(self, **kw)

