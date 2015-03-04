__author__ = 'simon'

import pyqtgraph as pg

class Axis(pg.AxisItem):

   def __init__(self, parent, orientation, viewBox=None, axisCode=None, units=None, mappedDim=None, pen=None):

     self.parent = parent
     self.plotItem = self.parent.plotItem
     self.orientation = orientation
     pg.AxisItem.__init__(self, orientation=orientation, linkView=viewBox)
     self.axisCode = axisCode
     self.units = units
     self.mappedDim = mappedDim
     self.textItem = pg.TextItem(text=axisCode, color='w')
     if orientation == 'top':
       axis = self.plotItem.axes['bottom']['item']
       self.textItem.setPos(viewBox.boundingRect().bottomLeft())
       self.textItem.anchor = pg.Point(0, 1)
     else:
       axis = self.plotItem.axes['right']['item']
       self.textItem.setPos(viewBox.boundingRect().topRight())
       self.textItem.anchor = pg.Point(1, 0)
     self.parent.scene().addItem(self.textItem)
     axis.orientation = orientation
     axis.setPen(pg.functions.mkPen(pen))
     axis.show()



   def setUnits(self, units):
     self.setLabel(units=units)

   def setAxisCode(self, axisCode):
     self.axisCode = str(axisCode)



       # self.label.setPos(3,1)
       # self.parent.plotItem.addItem(self.label)
       # self.update()
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

