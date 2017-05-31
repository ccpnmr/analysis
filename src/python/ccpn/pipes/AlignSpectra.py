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


from ccpn.framework.lib.Pipe import Pipe
from ccpn.pipes.guiPipes.GuiAlignSpectra import GuiAlignSpectra

class AlignSpectra(Pipe):

  guiPipe = GuiAlignSpectra
  pipeName = GuiAlignSpectra.pipeName



  def runPipe(self, params):
    '''
    :param data:
    :return:
    '''

    from ccpn.AnalysisScreen.lib.spectralProcessing.align import alignment
    if self.project is not None:

      referenceSpectrumPid = params['referenceSpectrum']
      referenceSpectrum = self.project.getByPid(referenceSpectrumPid)
      if referenceSpectrum is not None:
        spectra = [spectrum for spectrum in self.inputData if spectrum != referenceSpectrum]

        print(referenceSpectrum)
        print(spectra)
        if spectra:
          alignment._alignSpectra(referenceSpectrum, spectra)

          print('finished',)





AlignSpectra.register()

