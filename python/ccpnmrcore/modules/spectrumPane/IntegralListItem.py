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
