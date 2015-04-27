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

class AxisTextItem(pg.TextItem):

  def __init__(self, plotWidget, orientation, axisCode=None, units=None, mappedDim=None):

    self.plotWidget = plotWidget
    self.orientation = orientation
    self.axisCode = axisCode
    self.units = units
    self.mappedDim = mappedDim

    pg.TextItem.__init__(self, text=axisCode, color='w')
    if orientation == 'top':
      self.setPos(plotWidget.plotItem.vb.boundingRect().bottomLeft())
      self.anchor = pg.Point(0, 1)
    else:
      self.setPos(plotWidget.plotItem.vb.boundingRect().topRight())
      self.anchor = pg.Point(1, 0)
    plotWidget.scene().addItem(self)


  def setUnits(self, units):
    self.units = units

  def setAxisCode(self, axisCode):
    self.axisCode = str(axisCode)



