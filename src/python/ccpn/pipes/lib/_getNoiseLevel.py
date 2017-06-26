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



import numpy as np
from ccpn.core.lib.SpectrumLib import _estimateNoiseLevel1D

def _getNoiseLevelForPipe(cls, spectrum, estimateNoiseThreshold_var, noiseThreshold_var):
  '''Gets the noise level from the pipeline if a previous pipe was set. Otherwise takes from Spectrum.noiseLevel if set.
  If even this is not set, it estimates
  cls.pipeline._kwargs[estimateNoiseThreshold_var] = True or False
  '''

  positiveNoiseThreshold = 0.0
  negativeNoiseThreshold = 0.0
  if estimateNoiseThreshold_var in cls.pipeline._kwargs:
    if cls.pipeline._kwargs[estimateNoiseThreshold_var]:
      if spectrum.noiseLevel is not None:
        positiveNoiseThreshold = spectrum.noiseLevel
        negativeNoiseThreshold = -spectrum.noiseLevel
        spectrum.noiseLevel = positiveNoiseThreshold
        return (negativeNoiseThreshold, positiveNoiseThreshold)
      else:
        positiveNoiseThreshold = _estimateNoiseLevel1D(np.array(spectrum.positions), np.array(spectrum.intensities))
        negativeNoiseThreshold = -positiveNoiseThreshold
        spectrum.noiseLevel = positiveNoiseThreshold
        return (negativeNoiseThreshold, positiveNoiseThreshold)
    else:
      if noiseThreshold_var in cls.pipeline._kwargs:
        positiveNoiseThreshold = max(cls.pipeline._kwargs[noiseThreshold_var])
        negativeNoiseThreshold = min(cls.pipeline._kwargs[noiseThreshold_var])
        spectrum.noiseLevel = positiveNoiseThreshold
        return (negativeNoiseThreshold, positiveNoiseThreshold)

  if spectrum.noiseLevel == 0.0 or None:
    positiveNoiseThreshold = _estimateNoiseLevel1D(np.array(spectrum.positions), np.array(spectrum.intensities))
    negativeNoiseThreshold = - positiveNoiseThreshold
    spectrum.noiseLevel = positiveNoiseThreshold
    return (negativeNoiseThreshold, positiveNoiseThreshold)
  return (negativeNoiseThreshold, positiveNoiseThreshold)