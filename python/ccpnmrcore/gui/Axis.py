__author__ = 'simon'

from pyqtgraph import AxisItem as AxisItem
from pyqtgraph import LabelItem as LabelItem

from PySide import QtCore

from ccpncore.gui import ViewBox

class Axis(AxisItem):

   def __init__(self, parent, orientation, axisCode=None, units=None, mappedDim=None):
     self.parent = parent
     self.orientation = orientation
     AxisItem.__init__(self, orientation=orientation, linkView=ViewBox.ViewBox())
     self.axisCode = axisCode
     self.units = units
     self.mappedDim = mappedDim

   def setUnits(self, units):
     self.setLabel(units=units)

   def setAxisCode(self, axisCode):
     self.axisCode = str(axisCode)
     # self.label.setPos(-15,-15)
     # self.parent.plotItem.setLabel(self.orientation,self.axisCode)
     if self.orientation == 'bottom':
       # self.parent.plotItem.removeItem(self.label)


       self.label.setPos(3,1)
       self.parent.plotItem.addItem(self.label)
       self.update()
       # self.parent.plotItem.labels['bottom'].setPos(3,1)
     # print(self.orientation,self.label.pos())

     # p = QtCore.QPointF(0, 0)
     # br = self.label.boundingRect()
     # if self.orientation == 'top':
     #   p.setX(int(self.size().width()) - br.width())
     # self.addItem(label,(0,0))
     #
     # self.setLabel(text=axisCode)
     # self.showLabel(True)

