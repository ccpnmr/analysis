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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:41 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"

__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
from PyQt4 import QtCore, QtGui

import pyqtgraph as pg

class IntegralListItem(QtGui.QGraphicsItem):

  def __init__(self, spectrum):
    """ spectrumItem is the QGraphicsItem parent
        peakList is the CCPN object
    """

    QtGui.QGraphicsItem.__init__(self, spectrum)
    self.integralItems = []
    for integral in spectrum.integrals:
      self.integralItems.append(IntegralItem(spectrum, integral))
    self.displayed = False


class IntegralItem(QtGui.QGraphicsItem):

  def __init__(self, spectrum, integral):


      self.position = (integral.lastPoint+integral.firstPoint)/2
      self.integralTextItem = pg.TextItem(html=("%.1f&#x222b" % round(integral.volume*spectrum._apiDataSource.integralFactor,2)),color='k')
      self.integralPointerItem = pg.LineSegmentROI([[integral.firstPoint,0],[integral.lastPoint,0]], pen='k')
      self.integralTextItem.setPos(float(self.position),-3)
