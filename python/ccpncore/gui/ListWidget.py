__author__ = 'simon'

from PyQt4 import QtCore, QtGui

from ccpncore.gui.Base import Base

class ListWidget(QtGui.QListWidget, Base):

  def __init__(self, parent, **kw):

    QtGui.QListWidget.__init__(self)
    # removeItemShortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete), self, self.removeItem)
    Base.__init__(self, **kw)
    # self.setStyleSheet( """QListWidget {background-color: #000021;
    #          color: #f7ffff;
    # }""")

    # QtGui.QAction("New", self, triggered=self.newProject))
    # removeItemAction = QtGui.QAction('removeItem', self, triggered=self.removeItem, shortcut=QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete)))

    # QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Delete), self, self.removeItem)

  def removeItem(self):

    item = self.takeItem(self.currentRow())
    item = None
