__author__ = 'simon'

from PyQt4 import QtCore, QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Menu import Menu

class ListWidget(QtGui.QListWidget, Base):

  def __init__(self, parent, callback=None, **kw):

    QtGui.QListWidget.__init__(self, parent)
    Base.__init__(self, **kw)
    self.callback = None

    self.itemClicked.connect(callback)


  def removeItem(self):
    self.takeItem(self.currentRow())


  def mousePressEvent(self, event):
    self._mouse_button = event.button()
    if event.button() == QtCore.Qt.RightButton:
      self.raiseContextMenu(event)
    elif event.button() == QtCore.Qt.LeftButton:
      if self.itemAt(event.pos()) is None:
        self.clearSelection()
      else:
        super(ListWidget, self).mousePressEvent(event)

  def raiseContextMenu(self, event):
    """
    Raise the context menu
    """
    menu = self.getContextMenu()
    menu.popup(event.globalPos())

  def getContextMenu(self):
    contextMenu = Menu('', self, isFloatWidget=True)
    contextMenu.addItem("Delete", callback=self.removeItem)
    return contextMenu
