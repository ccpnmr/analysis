from PySide import QtGui

from ccpncore.gui.Base import Base

class Action(QtGui.QAction, Base):
  def __init__(self, parent, text, callback=None, shortcut=None, **kw):
    if shortcut:
      QtGui.QAction.__init__(self, text, parent, shortcut=QtGui.QKeySequence(", ".join(tuple(shortcut))), triggered=callback)
    else:
      QtGui.QAction.__init__(self, text, parent, triggered=callback)

    Base.__init__(self, **kw)
