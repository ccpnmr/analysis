import numpy

from ccpnmrcore.modules.spectrumPane.SpectrumItem import SpectrumItem

from PySide import QtCore, QtGui

from ccpn.lib import Spectrum as LibSpectrum  # TEMP (should be direct function call on spectrum object some day)


class Spectrum1dItem(SpectrumItem):

  # sigClicked = QtCore.Signal()


  def __init__(self, spectrumPane, spectrumVar, region=None, dimMapping=None):
    """ spectrumPane is the parent
        spectrumVar is the Spectrum name or object
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    self.spectrum = spectrumVar  # TEMP
    self.spectrumPane = spectrumPane
    self.spectralData = self.getSliceData()
    self.integrals = self.autoIntegration()
    # dimMapping = {} # this block of code TEMP
    # for i in range(len(self.spectrum.pointCount)):
    #   dimMapping[i] = i
    SpectrumItem.__init__(self, spectrumPane, spectrumVar, region)

  def autoIntegration(self):
    return LibSpectrum.automaticIntegration(self.spectrum, self.spectralData)


  def showPeaks(self, peakList):

    for peak in peakList.peaks:
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakTextItem.show()
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakPointerItem.show()
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.displayed = True
      self.peakListItems[peakList.pid].displayed = True

  def addPeaks(self, pane, peakList):

    for peak in peakList.peaks:
      pane.widget.addItem(self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakTextItem)
      pane.widget.addItem(self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakPointerItem)
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.displayed = True
      self.peakListItems[peakList.pid].displayed = True

  def addIntegrals(self, pane):
    for integralListItem in self.integralListItems:
      integralListItem.displayed = True
      for integral in integralListItem.integralItems:
        pane.widget.addItem(integral.integralTextItem)
        pane.widget.addItem(integral.integralPointerItem)
        integralListItem.displayed = True

  def showIntegrals(self):
    for integralListItem in self.integralListItems:
      integralListItem.displayed = True
      for integral in integralListItem.integralItems:
        integral.integralTextItem.show()
        integral.integralPointerItem.show()

  def hideIntegrals(self):
    for integralListItem in self.integralListItems:
      integralListItem.displayed = False
      for integral in integralListItem.integralItems:
        integral.integralTextItem.hide()
        integral.integralPointerItem.hide()

  def hidePeaks(self, peakList):

    for peak in peakList.peaks:
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakTextItem.hide()
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakPointerItem.hide()
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.displayed = True
      self.peakListItems[peakList.pid].displayed = False
  def getSliceData(self):

    spectrum = self.spectrum.ccpnSpectrum
    dataDimRef = spectrum.findFirstDataDim().findFirstDataDimRef()
    firstPoint = dataDimRef.pointToValue(0)
    pointCount = spectrum.findFirstDataDim().numPoints
    lastPoint = dataDimRef.pointToValue(pointCount)
    pointSpacing = (lastPoint-firstPoint)/pointCount
    position = numpy.array([firstPoint + n*pointSpacing for n in range(pointCount)],numpy.float32)
    sliceData = LibSpectrum.getSliceData(spectrum)
    scaledData = sliceData*spectrum.scale
    # spectrumData = numpy.array(position, scaledData, dtype=numpy.float32)
    # spectrumData = numpy.empty((2), dtype=numpy.float32)
    # position
    # spectrumData[1] = scaledData
    # #   spectrumData.append([x,y])
    spectrumData = numpy.array([position,scaledData], numpy.float32)
    # print(spectrumData)
    return numpy.array(spectrumData,numpy.float32)

