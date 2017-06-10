"""
Get the regions between two peak Limits and fill the area under the curve.

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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pyqtgraph as pg
from ccpn.ui.gui.widgets.PlotWidget import PlotWidget


'''
WARNING:
This  file is Under development. 
DO NOT USE !!




def _getIntegralRegions(integralList):
  # return: array of points. Each array represent the integral shape

  spectrum = integralList.spectrum
  limitsPairs = [integral.limits for integral in integralList.integrals]
  x, y = np.array(spectrum.positions), np.array(spectrum.intensities)

  integralRegions = []
  for i in limitsPairs:
    index01 = np.where((x <= i[0]) & (x >= i[1]))
    y_region = y[index01]
    x_region = x[index01]
    integralRegions.append((x_region, y_region))
  return integralRegions


def _getFillRegions(regions, intersectingLine, brush):
  # Create curveItems and fill the area below till the intersectingLine
  base = pg.PlotCurveItem(intersectingLine)
  fills = []
  for region in regions:
    curve = pg.PlotCurveItem(region)
    fills.append(pg.FillBetweenItem(curve, base, brush=brush))
  return fills

def _addIntegralRegionsToPlot(plotWidget, fillRegions):
  for fillRegion in fillRegions:
    if isinstance(plotWidget, PlotWidget):
      plotWidget.addItem(fillRegion)

def _removeIntegralRegionsFromPlot(plotWidget, fillRegions):
  for fillRegion in fillRegions:
    if isinstance(plotWidget, PlotWidget):
      plotWidget.removeItem(fillRegion)

'''