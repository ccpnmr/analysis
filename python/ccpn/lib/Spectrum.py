from ccpncore.lib.ccp.nmr.Nmr import DataSource

def getPlaneData(spectrum, position=None, xDim=0, yDim=1):

  # TBD: below should instead say (but this is not implemented yet)
  # return spectrum.ccpnSpectrum.getPlaneData(position=position, xDim=xDim, yDim=yDim)
  return DataSource.getPlaneData(spectrum.ccpnSpectrum, position=position, xDim=xDim, yDim=yDim)
  
def getSliceData(spectrum, position=None, sliceDim=0):

  # TBD: below should instead say (but this is not implemented yet)
  # return spectrum.ccpnSpectrum.getSliceData(position=position, xDim=xDim, yDim=yDim)
  return DataSource.getSliceData(spectrum, position=position, sliceDim=sliceDim)


def automaticIntegration(spectrum, xDim=0):

  return DataSource.automaticIntegration(spectrum, xDim=xDim)



