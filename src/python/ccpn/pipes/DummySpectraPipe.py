#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.framework.lib.Pipe import SpectraPipe
from ccpn.pipes.guiPipes.CreateDummySpectraGuiPipe import CreateDummySpectraGuiPipe

class createDummySpectraPipe(SpectraPipe):

  guiPipe = CreateDummySpectraGuiPipe
  pipeName = guiPipe.pipeName


  def runPipe(self, spectra, ):
    '''
    :param data:
    :return: it copies the input data as dummy spectra. Dummy spectra can be then modified.
    '''
    for i in dir(self):
       print(i)


    if self.project is not None:
      newDummySpectra = []
      for spectrum in self.inputData:

        dummySpectrum = self.project.createDummySpectrum(('H',), spectrum.name)
        dummySpectrum._positions = spectrum._positions
        dummySpectrum._intensities = spectrum._intensities
        dummySpectrum.pointCounts = spectrum.pointCounts
        newDummySpectra.append(dummySpectrum)

      return newDummySpectra



createDummySpectraPipe.register()

