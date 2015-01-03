
from PySide import QtGui

from ccpnmrcore import Base as GuiBase

from pyqtgraph.dockarea import Dock

class GuiModule(Dock, GuiBase):

  def __init__(self, dockArea, module):
    Dock.__init__(self)
    dockArea.addDock(self)
    self.module = module
