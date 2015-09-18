"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

from ccpnmrcore.modules.GuiSpectrumView import GuiSpectrumView

from ccpncore.util.Colour import spectrumColours

class GuiSpectrumView1d(GuiSpectrumView):


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

    # if self.spectrum.sliceColour is None:
    #   self.spectrum.sliceColour = list(spectrumColours.keys())[0]

    self.data = self._apiDataSource.get1dSpectrumData()

    # for strip in self.strips:
    if self.spectrum.sliceColour is None:
      if len(self.strip.spectrumViews) < 12:
        self.spectrum.sliceColour = list(spectrumColours.keys())[len(self.strip.spectrumViews)-1]
      else:
        self.spectrum.sliceColour = list(spectrumColours.keys())[(len(self.strip.spectrumViews) % 12)-1]

    self.plot = self.strip.plotWidget.plot(self.data[0], self.data[1], pen=self.spectrum.sliceColour)
    self.plot.curve.setClickable(True)
    self.plot.sigClicked.connect(self.clicked)
    for peakList in self.spectrum.peakLists:
      self.strip.showPeaks(peakList)

  def updatePhasing(self, ph0, ph1):
    pass
    
  def clicked(self):
    print(self.plot)
    

  def getSliceData(self, spectrum=None):

    if spectrum is None:
      apiDataSource = self._apiDataSource
    else:
      apiDataSource = spectrum._apiDataSource
    return apiDataSource.get1dSpectrumData()

  def update(self):
    self.plot.curve.setData(self.data[0], self.data[1])

