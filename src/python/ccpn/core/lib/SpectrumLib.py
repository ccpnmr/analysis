"""SPectrum-related functions and utiliities

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
import collections

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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:34 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
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


def _estimateNoiseLevel1D(x, y, factor=3):
  '''
  :param x,y:  spectrum.positions, spectrum.intensities
  :param factor: optional. Increase factor to increase the STD and therefore the noise level threshold
  :return: float of estimated noise threshold
  '''

  data = np.array([x, y])
  dataStd = np.std(data)
  data = np.array(data, np.float32)
  data = data.clip(-dataStd, dataStd)
  value = factor * np.std(data)
  return value