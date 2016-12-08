__author__ = 'simon1'

from PyQt4 import QtCore, QtGui

from pyqtgraph.dockarea.Dock import DockLabel, Dock

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.guiSettings import moduleLabelFont

class CcpnDock(Dock):
  def __init__(self, name, **kw):
    super(CcpnDock, self).__init__(name, self)
    self.label.hide()
    self.label = CcpnDockLabel(name.upper(), self)
    self.label.show()
    self.label.closeButton.clicked.connect(self.closeModule)
    self.label.fixedWidth = True
    self.autoOrientation = False
    self.mainWidget = QtGui.QWidget(self)
    self.settingsWidget = QtGui.QWidget(self)
    self.addWidget(self.mainWidget, 0, 0)
    self.addWidget(self.settingsWidget, 1, 0)

  def resizeEvent(self, event):
    self.setOrientation('vertical', force=True)
    self.resizeOverlay(self.size())

  def closeDock(self):
    self.close()

class CcpnDockLabel(DockLabel):

    def __init__(self, *args):
      super(CcpnDockLabel, self).__init__(showCloseButton=True, *args)
      self.setFont(moduleLabelFont)

    def mousePressEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton:
            self.pressPos = ev.pos()
            self.startedDrag = False
            ev.accept()



