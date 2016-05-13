__author__ = 'simon'

from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu

class ListWidget(QtGui.QListWidget, Base):

  def __init__(self, parent, callback=None, rightMouseCallback=None, contextMenu=None, **kw):

    QtGui.QListWidget.__init__(self, parent)
    Base.__init__(self, **kw)

    self.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
    self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
    self.setAcceptDrops(False)
    self.contextMenu = contextMenu
    self.callback = callback
    self.rightMouseCallback = rightMouseCallback
    if callback is not None:
      self.itemClicked.connect(callback)

    self.contextMenuItem = 'Delete'

  def contextCallback(self, remove=True):
    self.rightMouseCallback()
    if remove:
      self.removeItem()


  def removeItem(self):
    self.takeItem(self.currentRow())


  def mousePressEvent(self, event):
    self._mouse_button = event.button()
    if event.button() == QtCore.Qt.RightButton and self.contextMenu:
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

  def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
      event.accept()
    else:
      super(ListWidget, self).dragEnterEvent(event)

  def dragMoveEvent(self, event):
    if event.mimeData().hasUrls():
      event.setDropAction(QtCore.Qt.CopyAction)
      event.accept()
    else:
      super(ListWidget, self).dragMoveEvent(event)

  def dropEvent(self, event):
    if event.mimeData().hasUrls():
      event.setDropAction(QtCore.Qt.CopyAction)
      event.accept()
      links = []
      for url in event.mimeData().urls():
        links.append(str(url.toLocalFile()))
      self.emit(QtCore.SIGNAL("dropped"), links)
    else:
      items = []
      event.setDropAction(QtCore.Qt.MoveAction)
      self.emit(QtCore.SIGNAL("dropped"), items)
      super(ListWidget, self).dropEvent(event)