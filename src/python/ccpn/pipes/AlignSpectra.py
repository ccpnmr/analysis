#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:38 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe , _getWidgetByAtt
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Label import Label

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from scipy import signal
import numpy as np
from ccpn.util.Logging import getLogger , _debug3


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

ReferenceSpectrum = 'Reference_Spectrum'
PipeName = 'AlignSpectra'
HeaderText = '-- Select Spectrum --'
########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################


def _getShift(ref_x, ref_y, target_y):
  '''
  :param ref_x: X array of the reference spectra (positions)
  :param ref_y: Y array of the reference spectra (intensities)
  :param target_y: Y array of the target spectra (intensities)
  :return: the shift needed to align the two spectra.
  To align the target spectrum to its reference: add the shift to the x array.
  E.g. target_y += shift
  '''
  return (np.argmax(signal.correlate(ref_y, target_y)) - len(target_y)) * np.mean(np.diff(ref_x))


def _alignSpectra(referenceSpectrum, spectra):

  alignedSpectra = []
  for sp in spectra:
    shift = _getShift(ref_x=referenceSpectrum.positions, ref_y=referenceSpectrum.intensities, target_y=sp.intensities)
    sp._positions = sp.positions
    sp._positions += shift
    alignedSpectra.append(sp)
  return alignedSpectra



########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class AlignSpectraGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = PipeName

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(AlignSpectraGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent
    self.spectrumLabel = Label(self.pipeFrame, ReferenceSpectrum,  grid=(0,0))
    setattr(self, ReferenceSpectrum, PulldownList(self.pipeFrame, headerText=HeaderText, headerIcon=self._warningIcon,  grid=(0,1)) )
    self._updateWidgets()

  def _updateWidgets(self):
    self._setDataReferenceSpectrum()


  def _setDataReferenceSpectrum(self):
    data = list(self.inputData)
    if len(data)>0:
      _getWidgetByAtt(self,ReferenceSpectrum).setData(texts=[sp.pid for sp in data], objects=data, headerText=HeaderText, headerIcon=self._warningIcon)
    else:
      _getWidgetByAtt(self, ReferenceSpectrum)._clear()



########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class AlignSpectra(SpectraPipe):

  guiPipe = AlignSpectraGuiPipe
  pipeName = PipeName

  _kwargs  =   {
               ReferenceSpectrum: 'spectrum.pid'
               }



  def runPipe(self, spectra):
    '''
    :param spectra: inputData
    :return: aligned spectra
    '''
    if self.project is not None:
      referenceSpectrumPid = self._kwargs[ReferenceSpectrum]
      referenceSpectrum = self.project.getByPid(referenceSpectrumPid)
      if referenceSpectrum is not None:
        spectra = [spectrum for spectrum in spectra if spectrum != referenceSpectrum]
        if spectra:
          return _alignSpectra(referenceSpectrum, spectra)

      else:
        getLogger().warning('Spectra not Aligned. Returned original spectra')
        return spectra

AlignSpectra.register() # Registers the pipe in the pipeline
