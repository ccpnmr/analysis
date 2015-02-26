"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
import numpy

# from ccpn.lib.wrapper import Spectrum as LibSpectrum  # TEMP (should be direct function call on spectrum object some day)

from ccpnmrcore.modules.GuiSpectrumView import GuiSpectrumView

from ccpncore.util.Colour import Colour

class GuiSpectrumView1d(GuiSpectrumView):

  # sigClicked = QtCore.Signal()


  #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None):
  def __init__(self):
    """ spectrumPane is the parent
        spectrum is the Spectrum name or object
        """
    """ old comment
        region is in units of parent, ordered by spectrum dimensions
        dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
        (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
    """
    #GuiSpectrumView.__init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping)
    GuiSpectrumView.__init__(self)

    colour = Colour('red').rgba()
    for strip in self.strips:
      strip.plot(self.getSliceData()[0],self.getSliceData()[1], pen=colour)
    # if spectralData is None:
    #   self.spectralData = self.getSliceData()
    # else:
    #   self.spectralData = spectralData
    self.setZValue(-1)



  def getSliceData(self):

    apiDataSource = self.apiDataSource
    dataDimRef = apiDataSource.findFirstDataDim().findFirstDataDimRef()
    firstPoint = dataDimRef.pointToValue(0)
    pointCount = apiDataSource.findFirstDataDim().numPoints
    lastPoint = dataDimRef.pointToValue(pointCount)
    pointSpacing = (lastPoint-firstPoint)/pointCount
    position = numpy.array([firstPoint + n*pointSpacing for n in range(pointCount)],numpy.float32)
    sliceData = apiDataSource.getSliceData()
    scaledData = sliceData*apiDataSource.scale
    spectrumData = numpy.array([position,scaledData], numpy.float32)
    return numpy.array(spectrumData,numpy.float32)


