from PySide import QtGui, QtCore

from ccpncore.gui.Base import Base

class Action(QtGui.QAction, Base):
  def __init__(self, parent, text, callback=None, shortcut=None, **kw):
    text = self.translate(text)
    if shortcut:
      QtGui.QAction.__init__(self, text, parent, shortcut=QtGui.QKeySequence(", ".join(tuple(shortcut))), triggered=callback)
      QtGui.QAction.setShortcutContext(self, QtCore.Qt.ApplicationShortcut)
    else:
      QtGui.QAction.__init__(self, text, parent, triggered=callback)

    Base.__init__(self, **kw)
