"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
import collections

from ccpncore.lib.ccp.nmr.Nmr import DataSource

def getPlaneData(spectrum:object, position:collections.abc.Sequence=None, xDim:int=0, yDim:int=1):

  # TBD: below should instead say (but this is not implemented yet)
  # return spectrum.ccpnSpectrum.getPlaneData(position=position, xDim=xDim, yDim=yDim)
  return DataSource.getPlaneData(spectrum.ccpnSpectrum, position=position, xDim=xDim, yDim=yDim)
  
def getSliceData(spectrum:object, position:collections.abc.Sequence=None, sliceDim:int=0):

  # TBD: below should instead say (but this is not implemented yet)
  # return spectrum.ccpnSpectrum.getSliceData(position=position, xDim=xDim, yDim=yDim)
  return DataSource.getSliceData(spectrum, position=position, sliceDim=sliceDim)

def getRegionData(spectrum:object, startPoint:collections.abc.Sequence, endPoint:collections.abc.Sequence):
  
  return DataSource.getRegionData(spectrum, startPoint, endPoint)

def automaticIntegration(spectrum, spectralData):

  return DataSource.automaticIntegration(spectrum, spectralData)


def estimateNoise(spectrum):
  return DataSource.estimateNoise(spectrum.ccpnSpectrum)

def getDimPointFromValue(spectrum, dimension, value):
  """ Convert from value (e.g. ppm) to point (counting from 0) for an arbitrary
      number of values in a given dimension (counting from 0).  If value is a
      number then return a number, otherwise return a list.
  """
  return DataSource.getDimPointFromValue(spectrum.ccpnSpectrum, dimension, value)
    
def getDimValueFromPoint(spectrum, dimension, point):
  """ Convert from point (counting from 0) to value (e.g. ppm) for an arbitrary
      number of points in a given dimension (counting from 0).  If point is a
      number then return a number, otherwise return a list.
  """
  return DataSource.getDimValueFromPoint(spectrum.ccpnSpectrum, dimension, point)

def getAxisCodes(spectrum):
  """ Return axis codes for spectrum, using the isotopeCode if the axisCode not set
  """
  return DataSource.getAxisCodes(spectrum.ccpnSpectrum)
