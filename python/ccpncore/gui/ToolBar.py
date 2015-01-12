__author__ = 'simon'


from ccpncore.gui.Base import Base

from PySide import QtGui

class ToolBar(QtGui.QToolBar, Base):

  def __init__(self, parent, **kw):
    QtGui.QToolBar.__init__(self, parent)
    Base.__init__(self, **kw)
