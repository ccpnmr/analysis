__author__ = 'simon1'

from PyQt4 import QtCore, QtGui
from pyqtgraph.dockarea.DockDrop import DockDrop
from pyqtgraph.dockarea.Dock import DockLabel, Dock
from ccpn.ui.gui.widgets.Font import Font
from ccpn.ui.gui.widgets.Button import Button

Module = Dock
ModuleLabel = DockLabel

class CcpnModule(Module):

  includeSettingsWidget = False

  def __init__(self, name, logger=None, **kw):
    super(CcpnModule, self).__init__(name, self)
    self.label.hide()
    self.label = CcpnModuleLabel(name.upper(), self)
    self.label.show()
    self.label.closeButton.clicked.connect(self.closeModule)
    self.label.fixedWidth = True
    self.autoOrientation = False
    self.mainWidget = QtGui.QWidget(self)
    self.settingsWidget = QtGui.QWidget(self)
    self.addWidget(self.mainWidget, 0, 0)
    self.addWidget(self.settingsWidget, 1, 0)
    if not self.includeSettingsWidget:
      self.settingsWidget.hide()



  def resizeEvent(self, event):
    self.setOrientation('vertical', force=True)
    self.resizeOverlay(self.size())


  def toggleSettingsWidget(self, button=None):
    """
    Toggles display of settings widget in module.
    """
    if self.includeSettingsWidget:
      if button.isChecked():
        self.settingsWidget.show()
      else:
        self.settingsWidget.hide()
    else:
      print('Settings widget inclusion is false, please set includeSettingsWidget boolean to True at class level ')

  def closeModule(self):
    self.close()

  def dropEvent(self, *args):
    source = args[0].source()

    if hasattr(source, 'implements') and source.implements('dock'):
      DockDrop.dropEvent(self, *args)
    else:
      args[0].ignore()
      return

class CcpnModuleLabel(ModuleLabel):
  def __init__(self, *args):
    super(CcpnModuleLabel, self).__init__(showCloseButton=True, *args)
    self.setFont(Font(size=12, semiBold=True))

  def mousePressEvent(self, ev):
    if ev.button() == QtCore.Qt.LeftButton:
      self.pressPos = ev.pos()
      self.startedDrag = False
      ev.accept()



