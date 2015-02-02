from PySide import QtGui, QtCore

from pyqtgraph.dockarea import Dock

from ccpn import Spectrum

from ccpncore.gui.Label import Label

from ccpnmrcore.gui.Frame import Frame as GuiFrame
from ccpnmrcore.DropBase import DropBase

class GuiBlankDisplay(DropBase, Dock): # DropBase needs to be first, else the drop events are not processed

  def __init__(self, dockArea):
    
    self.dockArea = dockArea
    
    Dock.__init__(self, name='BlankDisplay', size=(1100,1300))
    dockArea.addDock(self)
    
    DropBase.__init__(self, dockArea.guiWindow.appBase, self.dropCallback)
    
    self.label = Label(self, text='Drag Spectrum Here', grid=(0, 0))

  def dropCallback(self, dropObject):
    
    if isinstance(dropObject, Spectrum):
      self.dockArea.guiWindow.displayFirstSpectrum(dropObject)
