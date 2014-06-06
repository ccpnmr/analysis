import operator

from ccpnmrcore.modules.SpectrumPane import SpectrumPane

from ccpnmrcore.modules.spectrumPane.SpectrumNdItem import SpectrumNdItem

class SpectrumNdPane(SpectrumPane):

  ##### functions used externally #####

  # implements superclass function
  def addSpectrum(self, spectrumVar, region=None, dimMapping=None):
    
    spectrumItem = SpectrumNdItem(self, spectrumVar, region, dimMapping)

  ##### functions called from SpectrumScene #####
  
  # overrides superclass function
  def drawPre(self, painter, rect):

    # below gives rise to infinite loop, and there is no 'rank' attribute yet
    #spectrumItems = sorted(self.spectrumItems, key=operator.attrgetter('rank'), reverse=True)
    spectrumItems = self.spectrumItems
    
    for spectrumItem in spectrumItems:
      spectrumItem.drawContours(painter, rect)
    
    # note, peaks will be drawn automatically

  # overrides superclass function
  def drawPost(self, painter, rect):

    pass  # TBD: markers, etc.
