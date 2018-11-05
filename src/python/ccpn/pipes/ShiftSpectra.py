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
__version__ = "$Revision: 3.0.b3 $"
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
from ccpn.ui.gui.widgets.DoubleSpinbox import ScientificDoubleSpinBox
from ccpn.ui.gui.widgets.GLLinearRegionsPlot import GLTargetButtonSpinBoxes


#### NON GUI IMPORTS
from ccpn.framework.lib.Pipe import SpectraPipe
from scipy import signal
import numpy as np
from scipy import stats
from ccpn.util.Logging import getLogger , _debug3


########################################################################################################################
###   Attributes:
###   Used in setting the dictionary keys on _kwargs either in GuiPipe and Pipe
########################################################################################################################

PipeName = 'Shift Spectra'
Shift = 'Shift'
DefaultShift = 0.01
########################################################################################################################
##########################################      ALGORITHM       ########################################################
########################################################################################################################



def addShiftToSpectra(spectra, shift):
  alignedSpectra=[]
  for sp in spectra:
    if shift is not None:
      sp.positions += float(shift)
      alignedSpectra.append(sp)
  return alignedSpectra

########################################################################################################################
##########################################     GUI PIPE    #############################################################
########################################################################################################################


class ShiftSpectraGuiPipe(GuiPipe):

  preferredPipe = True
  pipeName = PipeName

  def __init__(self, name=pipeName, parent=None, project=None,   **kwds):
    super(ShiftSpectraGuiPipe, self)
    GuiPipe.__init__(self, parent=parent, name=name, project=project, **kwds)
    self.parent = parent


    # factor
    self.factorLabel = Label(self.pipeFrame, Shift, grid=(0, 0))
    setattr(self, Shift, ScientificDoubleSpinBox(self.pipeFrame, value=DefaultShift,
                                                 max = 1e20,min=0.01, grid=(0, 1)))




########################################################################################################################
##########################################       PIPE      #############################################################
########################################################################################################################




class ShiftSpectra(SpectraPipe):
  """
  Add a shift value to all the spectra in the pipeline
  """

  guiPipe = ShiftSpectraGuiPipe
  pipeName = PipeName

  _kwargs  =   {
                Shift  :DefaultShift,
               }



  def runPipe(self, spectra):
    '''
    :param spectra: inputData
    :return: aligned spectra
    '''
    shift = self._kwargs[Shift]

    if self.project is not None:
      if spectra:
        return addShiftToSpectra(spectra, shift)
      else:
        getLogger().warning('Spectra not Aligned. Returned original spectra')
        return spectra


ShiftSpectra.register() # Registers the pipe in the pipeline
