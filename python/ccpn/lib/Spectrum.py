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


def automaticIntegration(spectrum, spectralData):

  return DataSource.automaticIntegration(spectrum.ccpnSpectrum, spectralData)


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


