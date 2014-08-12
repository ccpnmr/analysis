from PySide import QtGui

from ccpncore.gui.Action import Action
from ccpncore.gui.Base import Base

class Menu(QtGui.QMenu, Base):
  def __init__(self, parent, isFloatWidget=False, **kw):
    QtGui.QMenu.__init__(self, parent)
    Base.__init__(self, isFloatWidget=isFloatWidget, **kw)
    self.isFloatWidget = isFloatWidget

  def addItem(self, text, shortcut=None, callback=None, checkable=False):
    self.addAction(Action(self.parent(), text, callback=callback, shortcut=shortcut,
                         checkable=checkable, isFloatWidget=self.isFloatWidget))