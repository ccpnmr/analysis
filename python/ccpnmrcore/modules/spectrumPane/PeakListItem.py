from PySide import QtCore, QtGui

class PeakListItem(QtGui.QGraphicsItem):

  def __init__(self, spectrumItem, peakList):
    """ spectrumItem is the QGraphicsItem parent
        peakList is the CCPN object
    """
    
    QtGui.QGraphicsItem.__init__(self, spectrumItem)
    
    self.peakList = peakList
    self.peakItems = {}  # CCPN peak -> Qt peakItem
    
    for peak in peakList.peaks:
      self.peakItems[peak] = PeakItem(peak)
      
class PeakItem(QtGui.QGraphicsItem):

  def __init__(self, peakListItem, peak):
    """ peakListItem is the QGraphicsItem parent
        peak is the CCPN object
    """

    QtGui.QGraphicsItem.__init__(self, peakListItem)
    
    self.peak = peak
    # TBD: symbol and annotation
    # self.peakSymbolItem = PeakSymbolItem(self, peak)
    # self.peakAnnotationItem = PeakAnnotationItem(self, peak)  (this in turn has peakTextItem, peakPointerItem)
