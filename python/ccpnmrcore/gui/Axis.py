__author__ = 'simon'

from pyqtgraph import AxisItem as AxisItem

class Axis(AxisItem):

   def __init__(self, parent, orientation, axisCode=None, units=None, mappedDim=None):
     self.parent = parent
     self.orientation = orientation
     AxisItem.__init__(self, orientation=orientation)
     self.axisCode = axisCode
     self.units = units
     self.mappedDim = mappedDim

   def setUnits(self, units):
     self.setLabel(units=units)

   def setAxisCode(self, axisCode):
     self.axisCode = str(axisCode)

     self.parent.plotItem.setLabel(self.orientation,self.axisCode)
     #
     # self.setLabel(text=axisCode)
     # self.showLabel(True)


