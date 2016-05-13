__author__ = 'simon1'

from PyQt4 import QtCore, QtGui

from pyqtgraph.dockarea.Dock import DockLabel, Dock

from ccpn.ui.gui.widgets.Font import Font
from ccpn.ui.gui.widgets.Button import Button

class CcpnDock(Dock):
  def __init__(self, name, **kw):
    super(CcpnDock, self).__init__(name, self)
    self.label.hide()
    self.label = CcpnDockLabel(name.upper(), self)
    self.label.show()
    self.label.closeButton.clicked.connect(self.closeDock)
    self.label.fixedWidth = True
    self.autoOrientation = False
    self.widget1 = QtGui.QWidget(self)
    self.widget2 = QtGui.QWidget(self)
    self.addWidget(self.widget1, 0, 0)
    self.addWidget(self.widget2, 1, 0)



  def resizeEvent(self, event):
    self.setOrientation('vertical', force=True)
    self.resizeOverlay(self.size())

  def closeDock(self):
    self.close()

class CcpnDockLabel(DockLabel):

    def __init__(self, *args):
      super(CcpnDockLabel, self).__init__(showCloseButton=True, *args)
      self.setFont(Font(size=12, semiBold=True))

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.pressPos = ev.pos()
            self.startedDrag = False
            ev.accept()



