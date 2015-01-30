
from PySide import QtGui

from ccpnmrcore.Base import Base as GuiBase

from pyqtgraph.dockarea import Dock

from PySide import QtCore

QtCore.qInstallMsgHandler(lambda *args: None)

class GuiModule(Dock, GuiBase):

  def __init__(self, dockArea, apiModule):
    
    self.dockArea = dockArea
    self.apiModule = apiModule
    
    Dock.__init__(self, name=apiModule.name, size=(1100,1300))
    dockArea.addDock(self)
    
    GuiBase.__init__(self, dockArea.guiWindow.appBase)
