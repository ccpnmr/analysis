__author__ = 'simon'

from PyQt4 import QtCore, QtGui

from ccpncore.gui.Base import Base
from ccpncore.gui.Menu import Menu

class ListWidget(QtGui.QListWidget, Base):

  def __init__(self, parent, **kw):

    QtGui.QListWidget.__init__(self, parent)
    # removeItemShortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete), self, self.removeItem)
    Base.__init__(self, **kw)
    # self.setStyleSheet( """QListWidget {background-color: #000021;
    #          color: #f7ffff;
    # }""")

    # QtGui.QAction("New", self, triggered=self.newProject))
    # removeItemAction = QtGui.QAction('removeItem', self, triggered=self.removeItem, shortcut=QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete)))

    # QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete), self, self.removeItem)

  def removeItem(self):
    self.takeItem(self.currentRow())

  def mousePressEvent(self, event):
    if event.button() == QtCore.Qt.RightButton:
      event.accept()
      self.raiseContextMenu(event)
    else:
      event.accept()
      event.acceptProposedAction()


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

