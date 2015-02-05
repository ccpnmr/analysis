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


  #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None):
  def __init__(self, guiSpectrumDisplay, apiSpectrumView):
    """ spectrumPane is the parent
        spectrum is the Spectrum name or object
        """
    """ old comment
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    #GuiSpectrumView.__init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping)
    GuiSpectrumView.__init__(self, guiSpectrumDisplay, apiSpectrumView)
    
    # if spectralData is None:
    #   self.spectralData = self.getSliceData()
    # else:
    #   self.spectralData = spectralData
    self.setZValue(-1)


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


