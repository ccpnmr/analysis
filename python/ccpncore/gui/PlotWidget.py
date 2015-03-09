__author__ = 'simon'

from ccpncore.gui.Base import Base
from ccpncore.gui import ViewBox
from ccpnmrcore.DropBase import DropBase

import pyqtgraph as pg

class PlotWidget(DropBase, pg.PlotWidget, Base):

  def __init__(self, parent=None, appBase=None, dropCallback=None, **kw):


    pg.PlotWidget.__init__(self, parent=parent, viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True)
    Base.__init__(self, **kw)
    DropBase.__init__(self, appBase, dropCallback)

    self.plotItem.setAcceptDrops(True)
    self.plotItem.axes['left']['item'].hide()
    self.plotItem.axes['right']['item'].show()

    # # self.plotItem.axes['top']['item'].hide()
    # self.plotItem.axes['bottom']['item'].show()
    # self.plotItem.axes['right']['item'].show()



