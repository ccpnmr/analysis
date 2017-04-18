
from ccpn.ui.gui.modules.GuiModule import GuiModule
from pyqtgraph.dockarea import Dock
import pyqtgraph as pg
import numpy as np

class DataPlottingModule(Dock): # DropBase needs to be first, else the drop events are not processed

  def __init__(self, moduleArea):


    Dock.__init__(self, name='Data Plotting', size=(1100,1300))

    self.plotWidget = pg.PlotWidget()
    moduleArea.addModule(self)

    self.addWidget(self.plotWidget)
    x = np.array([0, 2, 4, 6, 8, 10])
    y = np.array([1500, 500, 200, 100, 50, 10])
    self.plotWidget.plot(x, y, pen=(255, 0, 0), symbol='t', symbolPen=None, symbolSize=10, symbolBrush=(255, 0, 0))
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:03 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
