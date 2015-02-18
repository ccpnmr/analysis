
from PySide import QtGui

from ccpnmrcore.Base import Base as GuiBase

from pyqtgraph.dockarea import Dock

from PySide import QtCore

QtCore.qInstallMsgHandler(lambda *args: None)

class GuiModule(Dock, GuiBase):

  def __init__(self):
    
    window = self.window

    self.dockArea = window.dockArea
    # self.apiModule = apiModule
    
    Dock.__init__(self, name=self._wrappedData.name, size=(1100,1300))
    self.dockArea.addDock(self)
    
    GuiBase.__init__(self, self._project._appBase)
