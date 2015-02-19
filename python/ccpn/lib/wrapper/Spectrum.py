"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
import collections
import itertools
import os
Sequence = collections.abc.Sequence

from ccpncore.lib.ccp.nmr.Nmr import DataSource

# NBNB TBD Surely we do not need one-line wrappers around API-level utilities
# If the utility is needed here and not in the API, should we not move the code here?

# NBNB TBD parameters need renaming to distinguish api and wrapper objects

def getPlaneData(spectrum:object, position:Sequence=None, xDim:int=0, yDim:int=1):

  # TBD: below should instead say (but this is not implemented yet)
  # return spectrum.apiDataSource.getPlaneData(position=position, xDim=xDim, yDim=yDim)
  return DataSource.getPlaneData(spectrum.apiDataSource, position=position, xDim=xDim, yDim=yDim)
  
def getSliceData(spectrum:object, position:collections.abc.Sequence=None, sliceDim:int=0):

  # TBD: below should instead say (but this is not implemented yet)
  # return spectrum.apiDataSource.getSliceData(position=position, xDim=xDim, yDim=yDim)
  return DataSource.getSliceData(spectrum, position=position, sliceDim=sliceDim)

def getRegionData(spectrum:object, startPoint:collections.abc.Sequence, endPoint:collections.abc.Sequence):
  
  return DataSource.getRegionData(spectrum, startPoint, endPoint)

def automaticIntegration(spectrum, spectralData):

  return DataSource.automaticIntegration(spectrum, spectralData)


def estimateNoise(spectrum):
  return DataSource.estimateNoise(spectrum.apiDataSource)

def getDimPointFromValue(spectrum, dimension, value):
  """ Convert from value (e.g. ppm) to point (counting from 0) for an arbitrary
      number of values in a given dimension (counting from 0).  If value is a
      number then return a number, otherwise return a list.
  """
  return DataSource.getDimPointFromValue(spectrum.apiDataSource, dimension, value)
    
def getDimValueFromPoint(spectrum, dimension, point):
  """ Convert from point (counting from 0) to value (e.g. ppm) for an arbitrary
      number of points in a given dimension (counting from 0).  If point is a
      number then return a number, otherwise return a list.
  """
  return DataSource.getDimValueFromPoint(spectrum.apiDataSource, dimension, point)


