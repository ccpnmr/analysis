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

class PeakListItem(QtGui.QGraphicsItem):

  def __init__(self, spectrumItem, peakList):
    """ spectrumItem is the QGraphicsItem parent
        peakList is the CCPN object
    """
    
    QtGui.QGraphicsItem.__init__(self, spectrumItem)
    
    self.peakList = peakList
    self.peakItems = {}  # CCPN peak -> Qt peakItem
    self.displayed = False
    self.symbolColour = None
    self.symbolStyle = None
    self.isSymbolDisplayed = False
    self.textColour = None
    self.isTextDisplayed = False

    for peak in peakList.peaks:
      self.peakItems[peak.pid] = PeakItem(self, peak)


  def createPeakItems(self):
    for peak in self.peakList.peaks:
      print(peak, peak.pid)
      self.peakItems[peak.pid] = PeakItem(self, peak)
      
class PeakItem(QtGui.QGraphicsItem):

  def __init__(self, peakListItem, peak):
    """ peakListItem is the QGraphicsItem parent
        peak is the CCPN object
    """

    QtGui.QGraphicsItem.__init__(self, peakListItem)
    
    self.peak = peak
    # TBD: symbol and annotation
    # self.peakSymbolItem = PeakSymbolItem(self, peak)

    self.peakAnnotationItem = PeakAnnotationItem(self.peak)  #(this in turn has peakTextItem, peakPointerItem)

class PeakSymbolItem(QtGui.QGraphicsItem):

  def __init__(self, peak):

    QtGui.QGraphicsItem(self, peak)

    self.peak = peak


class PeakAnnotationItem(QtGui.QGraphicsItem):

  def __init__(self, peak):
    self.textOffset = None
    if peak.height is not None:
      peakHeight = peak.height
    else:
      peakHeight = peak._wrappedData.findFirstPeakIntensity(intensityType='height').value
    self.peak = peak
    self.peakTextItem = pg.TextItem(text=str("%.3f" % peak.position[0]), anchor=(-0.9,2.5), color='k')
    self.peakPointerItem =  pg.ArrowItem(pos=(peak.position[0],peakHeight), angle = -45, headLen=60, tipAngle=5)
    self.peakTextItem.setPos(peak.position[0],peakHeight)
    self.displayed = False




