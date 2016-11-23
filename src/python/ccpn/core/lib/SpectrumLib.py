"""SPectrum-related functions and utiliities

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
import collections

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca G Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

# import typing
from ccpn.core.Project import Project
from ccpnmodel.ccpncore.lib.spectrum.NmrExpPrototype import getExpClassificationDict

MagnetisationTransferTuple = collections.namedtuple('MagnetisationTransferTuple',
  ['dimension1', 'dimension2', 'transferType', 'isIndirect']
)

def getExperimentClassifications(project:Project) -> dict:
  """
  Get a dictionary of dictionaries of dimensionCount:sortedNuclei:ExperimentClassification named tuples.
  """
  return getExpClassificationDict(project._wrappedData)


