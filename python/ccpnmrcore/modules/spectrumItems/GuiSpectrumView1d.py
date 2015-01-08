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
import numpy

from ccpnmrcore.modules.spectrumItems.GuiSpectrumView import GuiSpectrumView

from PySide import QtCore, QtGui
from numpy import argwhere
from scipy.ndimage import maximum_filter
from ccpn._wrapper._Peak import Peak as Peak

from ccpn.lib import Spectrum as LibSpectrum  # TEMP (should be direct function call on spectrum object some day)
from ccpnmrcore.modules.spectrumPane.IntegralListItem import IntegralListItem

class GuiSpectrumView1d(GuiSpectrumView):

  # sigClicked = QtCore.Signal()


  def __init__(self, guiSpectrumDisplay1d, spectrum, spectralData = None, dimMapping=None):
    """ spectrumPane is the parent
        spectrum is the Spectrum name or object
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    GuiSpectrumView.__init__(self, guiSpectrumDisplay1d, spectrum, dimMapping)
    
    if spectralData is None:
      self.spectralData = self.getSliceData()
    else:
      self.spectralData = spectralData
    self.setZValue(-1)


  def autoIntegration(self):
    return LibSpectrum.automaticIntegration(self.spectrum, self.spectralData)

  def estimateNoise(self):
    return LibSpectrum.estimateNoise(self.spectrum)

  def showPeaks(self, peakList):

    for peak in peakList.peaks:
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakTextItem.show()
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakPointerItem.show()
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.displayed = True
      self.peakListItems[peakList.pid].displayed = True

  def addPeaks(self, pane, peakList):

    for peak in peakList.peaks:
      pane.addItem(self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakTextItem)
      pane.addItem(self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.peakPointerItem)
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.displayed = True
      self.peakListItems[peakList.pid].displayed = True

  def findPeaks(self, size=3, mode='wrap'):

   if self.spectrum.peakLists is None:
     peakList = self.spectrum.newPeakList
     print(peakList)
   else:
     peakList = self.spectrum.peakLists[0]
   print('#######',peakList.pid)
   peaks = []
   data = self.spectralData
   threshold = self.estimateNoise()*10
   if (data.size == 0) or (data.max() < threshold):
    return peaks
   boolsVal = data[1] > threshold
   maxFilter = maximum_filter(data[1], size=size, mode=mode)

   boolsMax = data[1] == maxFilter

   boolsPeak = boolsVal & boolsMax
   indices = argwhere(boolsPeak) # True positional indices
   for position in indices:
     peakPosition = [float(data[0][position])]
     print('position', peakPosition)
     height = data[1][position]
     peaks.append([peakPosition,height])
     peakList.newPeak(height=float(height), position=peakPosition)
   print(self.peakListItems[peakList.pid])#.createPeakItems()

   return peakList


  def addIntegrals(self, pane):
    for integralListItem in self.integralListItems:
      integralListItem.displayed = True
      for integral in integralListItem.integralItems:
        pane.addItem(integral.integralTextItem)
        pane.addItem(integral.integralPointerItem)
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
      self.peakListItems[peakList.pid].peakItems[peak.pid].peakAnnotationItem.displayed = False
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
    spectrumData = numpy.array([position,scaledData], numpy.float32)
    return numpy.array(spectrumData,numpy.float32)


