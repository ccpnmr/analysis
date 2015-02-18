
from PySide import QtGui

from ccpnmrcore.Base import Base as GuiBase

from pyqtgraph.dockarea import Dock

from PySide import QtCore, QtGui

QtCore.qInstallMsgHandler(lambda *args: None)

class GuiModule(QtGui.QWidget, GuiBase):

  def __init__(self):
    
    QtGui.QWidget.__init__(self)
    
    self.dockArea = self.window.dockArea
    # self.apiModule = apiModule
    
    self.dock = Dock(name=self._wrappedData.name, size=(1100,1300))
    self.dockArea.addDock(self.dock)
    
    GuiBase.__init__(self, self._project._appBase)
    