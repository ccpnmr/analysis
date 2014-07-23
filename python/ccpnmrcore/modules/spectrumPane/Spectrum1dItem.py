import numpy

from ccpnmrcore.modules.spectrumPane.SpectrumItem import SpectrumItem

from PySide import QtCore, QtGui

from ccpn.lib import Spectrum as LibSpectrum  # TEMP (should be direct function call on spectrum object some day)



class Spectrum1dItem:

  # sigClicked = QtCore.Signal()


  def __init__(self, parent, spectrumVar, region=None, dimMapping=None):
    """ spectrumPane is the parent
        spectrumVar is the Spectrum name or object
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    self.spectrum = spectrumVar  # TEMP
    self.spectralData = self.getSliceData()
    self.integrals = self.autoIntegration()
    self.peakMarkings = []
    self.integralMarkings = []
    # dimMapping = {} # this block of code TEMP
    # for i in range(len(self.spectrum.pointCount)):
    #   dimMapping[i] = i
    # SpectrumItem.__init__(self, parent, spectrumVar, region, dimMapping)

  def autoIntegration(self):
    return LibSpectrum.automaticIntegration(self.spectrum, self.spectralData)


  def showPeaks(self):

    for marking in self.peakMarkings:
      marking.show()

  def showIntegrals(self):

    for marking in self.integralMarkings:
      marking.show()

  def hidePeaks(self):

    for marking in self.peakMarkings:
      marking.hide()

  def hideIntegrals(self):

    for marking in self.integralMarkings:
      marking.hide()

  def getSliceData(self):

    spectrum = self.spectrum.ccpnSpectrum
    dataDimRef = spectrum.findFirstDataDim().findFirstDataDimRef()
    firstPoint = dataDimRef.pointToValue(0)
    pointCount = spectrum.findFirstDataDim().numPoints
    lastPoint = dataDimRef.pointToValue(pointCount-1)
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

