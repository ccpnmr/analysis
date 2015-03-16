"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
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

