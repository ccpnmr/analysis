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

    for peak in peakList.peaks:
      self.peakItems[peak.pid] = PeakItem(self, peak)
      
class PeakItem(QtGui.QGraphicsItem):

  def __init__(self, peakListItem, peak):
    """ peakListItem is the QGraphicsItem parent
        peak is the CCPN object
    """

    QtGui.QGraphicsItem.__init__(self, peakListItem)
    
    self.peak = peak
    # print(self.peak)
    # TBD: symbol and annotation
    # self.peakSymbolItem = PeakSymbolItem(self, peak)
    self.peakAnnotationItem = PeakAnnotationItem(self.peak)  #(this in turn has peakTextItem, peakPointerItem)

class PeakSymbolItem(QtGui.QGraphicsItem):

  def __init__(self, peak):

    QtGui.QGraphicsItem(self, peak)

    self.peak = peak


class PeakAnnotationItem(QtGui.QGraphicsItem):

  def __init__(self, peak):
    peakHeight = peak._wrappedData.findFirstPeakIntensity(intensityType='height').value
    self.peak = peak
    self.peakTextItem = pg.TextItem(text=str("%.3f" % peak.position[0]), anchor=(-0.9,2.5), color='k')
    self.peakPointerItem =  pg.ArrowItem(pos=(peak.position[0],peakHeight), angle = -45, headLen=60, tipAngle=5)
    self.peakTextItem.setPos(peak.position[0],peakHeight)
    self.displayed = False




