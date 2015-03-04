__author__ = 'simon'

from ccpncore.gui import ViewBox
from ccpncore.gui.Widget import Widget

import pyqtgraph as pg

class PlotWidget(Widget):

  def __init__(self, parent=None, **kw):

    Widget.__init__(self, parent, **kw)
    self.plotWidget = pg.PlotWidget(viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True)
    self.layout().addWidget(self.plotWidget)
    self.plotWidget.plotItem.axes['left']['item'].hide()
    self.plotWidget.plotItem.axes['right']['item'].show()