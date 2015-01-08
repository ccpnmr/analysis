"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from PySide import QtCore, QtGui

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
      self.integralTextItem = pg.TextItem(html=("%.1f&#x222b" % round(integral.volume*spectrum.ccpnSpectrum.integralFactor,2)),color='k')
      self.integralPointerItem = pg.LineSegmentROI([[integral.firstPoint,0],[integral.lastPoint,0]], pen='k')
      self.integralTextItem.setPos(float(self.position),-3)
