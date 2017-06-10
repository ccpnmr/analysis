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


#### GUI IMPORTS
from ccpn.ui.gui.widgets.PipelineWidgets import GuiPipe
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Label import Label

#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from scipy import signal
import numpy as np
from ccpn.pipes.lib.AreaCalculation import _addAreaValuesToPeaks

########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################




########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################




class CalculateAreaGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = 'Calculate Peak Areas'

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(CalculateAreaGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent

    self.peakListLabel = Label(self.pipeFrame, 'Reference PeakList', grid=(0, 0))
    self.referencePeakList= PulldownList(self.pipeFrame, grid=(0, 1))
    self._updateWidgets()

  def _updateWidgets(self):
    self._setDataReferenceSpectrum()

  def _setDataReferenceSpectrum(self):
    data = list(self.inputData)
    if len(data) > 0:
      for spectrum in data:
        if spectrum is not None:
          if spectrum.peakLists:
            pls = spectrum.peakLists
            self.referencePeakList.setData(texts=[pl.pid for pl in pls], objects=pls)




########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class CalculateAreaPipe(SpectraPipe):

  guiPipe = CalculateAreaGuiPipe
  pipeName = guiPipe.pipeName

  _kwargs =       {'referencePeakList' : 'pid',
                   'excludeRegions': [[0.0, 0.0], [0.0, 0.0]],
                   'noiseRegions': [0.0, 0.0],
                   'negative': False,
                   'minimalLineWidth' : 0.01,
                   }


  def runPipe(self, spectra):
    '''
    :param data:
    :return:
    '''

    if 'noiseThreshold' in self.pipeline._kwargs:
      positiveNoiseThreshold = max(self.pipeline._kwargs['noiseThreshold'])
      negativeNoiseThreshold = min(self.pipeline._kwargs['noiseThreshold'])
    else:
      positiveNoiseThreshold = max(self._kwargs['noiseThreshold'])
      negativeNoiseThreshold = min(self._kwargs['noiseThreshold'])

    if 'minimalLineWidth' in self.pipeline._kwargs:
      minimalLineWidth = self.pipeline._kwargs['minimalLineWidth']
    else:
      minimalLineWidth = self._kwargs['minimalLineWidth']

    for spectrum in spectra:
      referencePeakListPid = self._kwargs['referencePeakList']
      referencePeakList = self.project.getByPid(referencePeakListPid)

      if referencePeakList is not None:
          if referencePeakList.peaks:
            _addAreaValuesToPeaks(spectrum, referencePeakList, noiseThreshold=positiveNoiseThreshold, minimalLineWidth = minimalLineWidth)
          else:
            print('Error. No peaks found.' )

    return spectra


CalculateAreaPipe.register() # Registers the pipe in the pipeline


