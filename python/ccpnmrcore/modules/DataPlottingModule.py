__author__ = 'simon'

from ccpnmrcore.modules.GuiModule import GuiModule
from pyqtgraph.dockarea import Dock
import pyqtgraph as pg
import numpy as np

class DataPlottingModule(Dock): # DropBase needs to be first, else the drop events are not processed

  def __init__(self, dockArea):


    Dock.__init__(self, name='Data Plotting', size=(1100,1300))

    self.plotWidget = pg.PlotWidget()
    dockArea.addDock(self)

    self.addWidget(self.plotWidget)
    x = np.array([0, 2, 4, 6, 8, 10])
    y = np.array([1500, 500, 200, 100, 50, 10])
    self.plotWidget.plot(x, y, pen=(255, 0, 0), symbol='t', symbolPen=None, symbolSize=10, symbolBrush=(255, 0, 0))