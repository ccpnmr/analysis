__author__ = 'simon'

from PyQt4 import QtCore, QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Menu import Menu

class ListWidget(QtGui.QListWidget, Base):

  def __init__(self, parent, callback=None, rightMouseCallback=None, **kw):

    QtGui.QListWidget.__init__(self, parent)
    Base.__init__(self, **kw)
    self.callback = callback
    self.rightMouseCallback = rightMouseCallback
    if callback is not None:
      self.itemClicked.connect(callback)


  def contextCallback(self):
    self.removeItem()
    self.rightMouseCallback()

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
    if self.rightMouseCallback is None:
      contextMenu.addItem("Delete", callback=self.removeItem)
    else:
      contextMenu.addItem("Delete", callback=self.contextCallback)
    return contextMenu
