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



