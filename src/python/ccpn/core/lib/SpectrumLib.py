"""SPectrum-related functions and utiliities

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
import collections

__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:32 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================

__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import typing
from ccpn.core.Project import Project
from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import getExpClassificationDict
import numpy as np

MagnetisationTransferTuple = collections.namedtuple('MagnetisationTransferTuple',
  ['dimension1', 'dimension2', 'transferType', 'isIndirect']
)

def getExperimentClassifications(project:Project) -> dict:
  """
  Get a dictionary of dictionaries of dimensionCount:sortedNuclei:ExperimentClassification named tuples.
  """
  return getExpClassificationDict(project._wrappedData)


# def _estimateNoiseLevel1D(x, y, factor=3):
#   '''
#   :param x,y:  spectrum.positions, spectrum.intensities
#   :param factor: optional. Increase factor to increase the STD and therefore the noise level threshold
#   :return: float of estimated noise threshold
#   '''
#
#   data = np.array([x, y])
#   dataStd = np.std(data)
#   data = np.array(data, np.float32)
#   data = data.clip(-dataStd, dataStd)
#   value = factor * np.std(data)
#   return value


def _estimateNoiseLevel1D(y, factor=0.5):
  '''
  Estimates the noise threshold based on the max intensity of the first portion of the spectrum where
  only noise is present. To increase the threshold value: increase the factor.
  return:  float of estimated noise threshold
  '''
  if y is not None:
    return max(y[:int(len(y)/20)]) * factor
  else:
    return 0


def _calibrateX1D(spectrum, currentPosition, newPosition):
  shift = newPosition - currentPosition
  spectrum.positions = spectrum.positions+shift

def _calibrateY1D(spectrum, currentPosition, newPosition):
  shift = newPosition - currentPosition
  spectrum.intensities = spectrum.intensities+shift