__author__ = 'simon1'

from PyQt4 import QtCore, QtGui
from pyqtgraph.dockarea.DockDrop import DockDrop
from pyqtgraph.dockarea.Dock import DockLabel, Dock
from ccpn.ui.gui.widgets.Font import Font
from ccpn.ui.gui.widgets.Button import Button

from functools import partial

Module = Dock
ModuleLabel = DockLabel

class CcpnModule(Module):

  includeSettingsWidget = False

  def __init__(self, name, logger=None, buttonParent=None, buttonGrid=None, **kw):
    super(CcpnModule, self).__init__(name, self)
    self.label.hide()
    self.label = CcpnModuleLabel(name.upper(), self)
    self.label.show()
    self.label.closeButton.clicked.connect(self._closeModule)
    self.label.fixedWidth = True
    self.autoOrientation = False
    self.mainWidget = QtGui.QWidget(self)
    self.addWidget(self.mainWidget, 0, 0)

    if self.includeSettingsWidget:
      self.settingsWidget = QtGui.QWidget(self)
      self.addWidget(self.settingsWidget, 1, 0)
      self.settingsWidget.hide()


      #
      # if buttonParent and buttonGrid:
      #   self.placeSettingsButton(buttonParent, buttonGrid)
      # else:
      #   print('cannot add settings button')



  def resizeEvent(self, event):
    self.setOrientation('vertical', force=True)
    self.resizeOverlay(self.size())

  def placeSettingsButton(self, buttonParent, buttonGrid):
    if self.includeSettingsWidget:
      settingsButton = Button(buttonParent, icon='icons/applications-system', grid=buttonGrid, hPolicy='fixed', toggle=True)
      settingsButton.toggled.connect(partial(self.toggleSettingsWidget, settingsButton))
      settingsButton.setChecked(False)


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


  def _closeModule(self):
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



