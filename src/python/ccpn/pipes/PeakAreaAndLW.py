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
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Calculate Peak Areas'

ExcludeRegions = 'excludeRegions'
ReferencePeakList = 'referencePeakList'
NoiseThreshold = 'noiseThreshold'
NegativePeaks =  'negativePeaks'
MinimalLineWidth =  'minimalLineWidth'

########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################




########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################




class CalculateAreaGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = PipeName

  def __init__(self, name=pipeName, parent=None, project=None,   **kw):
    super(CalculateAreaGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kw )
    self.parent = parent

    self.peakListLabel = Label(self.pipeFrame, 'Reference PeakList', grid=(0, 0))
    setattr(self, ReferencePeakList, PulldownList(self.pipeFrame, grid=(0, 1)))
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
  pipeName = PipeName

  _kwargs =       {
                    ReferencePeakList : 'peakList.pid',
                    ExcludeRegions: [[0.0, 0.0], [0.0, 0.0]],
                    NoiseThreshold: [0.0, 0.0],
                    NegativePeaks: False,
                    MinimalLineWidth: 0.01,
                   }


  def runPipe(self, spectra):
    '''
    :param data:
    :return:
    '''

    if NoiseThreshold in self.pipeline._kwargs:
      positiveNoiseThreshold = max(self.pipeline._kwargs[NoiseThreshold])
    else:
      positiveNoiseThreshold = max(self._kwargs[NoiseThreshold])

    if MinimalLineWidth in self.pipeline._kwargs:
      minimalLineWidth = self.pipeline._kwargs[MinimalLineWidth]
    else:
      minimalLineWidth = self._kwargs[MinimalLineWidth]

    for spectrum in spectra:
      referencePeakListPid = self._kwargs[ReferencePeakList]
      referencePeakList = self.project.getByPid(referencePeakListPid)

      if referencePeakList is not None:
          if referencePeakList.peaks:
            _addAreaValuesToPeaks(spectrum, referencePeakList, noiseThreshold=positiveNoiseThreshold, minimalLineWidth = minimalLineWidth)
          else:
            print('Error. No peaks to assign volume found. Pick the peaks first' )

    return spectra


CalculateAreaPipe.register() # Registers the pipe in the pipeline


