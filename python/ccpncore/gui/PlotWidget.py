__author__ = 'simon'

from PySide import QtGui
from ccpncore.gui.Base import Base
from ccpncore.gui import ViewBox

import pyqtgraph as pg

class PlotWidget(QtGui.QWidget, Base):

  def __init__(self, parent=None, **kw):

    QtGui.QWidget.__init__(self, parent)
    Base.__init__(self, **kw)
    layout = QtGui.QGridLayout()
    self.setLayout(layout)
    self.plotWidget = pg.PlotWidget(viewBox=ViewBox.ViewBox(), axes=None, enableMenu=True)
    self.layout().addWidget(self.plotWidget)