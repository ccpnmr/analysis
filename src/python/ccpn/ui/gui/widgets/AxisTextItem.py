"""Module Documentation here

"""
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
__author__ = "$Author: CCPN $"
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:05 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"

#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import pyqtgraph as pg

class AxisTextItem(pg.TextItem):

  def __init__(self, plotWidget, orientation, axisCode=None, units=None, mappedDim=None):

    self.plotWidget = plotWidget
    self.orientation = orientation
    self.axisCode = axisCode
    self.units = units
    self.mappedDim = mappedDim
    if plotWidget._appBase.colourScheme == 'dark':
      colour = '#f7ffff'
    else:
      colour = '#080000'
    pg.TextItem.__init__(self, text=axisCode, color=colour)
    if orientation == 'top':
      self.setPos(plotWidget.plotItem.vb.boundingRect().bottomLeft())
      self.anchor = pg.Point(0, 1)
    else:
      self.setPos(plotWidget.plotItem.vb.boundingRect().topRight())
      self.anchor = pg.Point(1, 0)
    plotWidget.scene().addItem(self)


  def _setUnits(self, units):
    self.units = units

  def _setAxisCode(self, axisCode):
    self.axisCode = str(axisCode)



