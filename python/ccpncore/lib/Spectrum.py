import os
from collections.abc import Sequence

from ccpncore.util import Path
from ccpncore.lib.BlockData import determineBlockSizes
from ccpncore.memops.ApiError import ApiError

def createExperiment(nmrProject:object, name:str, numDim:int, sf:Sequence,
                     isotopeCodes:Sequence, isAcquisition:Sequence=None, **additionalParameters):
  """Create Experiment object ExpDim, and one ExpDimRef per ExpDim.
  Additional parameters to Experiment object are passed in additionalParameters"""

  experiment = nmrProject.newExperiment(name=name, numDim=numDim, **additionalParameters)

  if isAcquisition is None:
    isAcquisition = (False,) * numDim

  for n, expDim in enumerate(experiment.sortedExpDims()):
    expDim.isAcquisition = isAcquisition[n]
    ic = isotopeCodes[n]
    if ic:
      if isinstance(ic, str):
        ic = (ic,)
      expDim.newExpDimRef(sf=sf[n], unit='ppm', isotopeCodes=ic)

  return experiment

def createDataSource(experiment:object, name:str, numPoints:Sequence, sw:Sequence,
                     refppm:Sequence, refpt:Sequence, dataStore:object=None,
                     scale:float=1.0, details:str=None, numPointsOrig:Sequence=None,
                     pointOffset:Sequence=None, isComplex:Sequence=None,
                     **additionalParameters) -> object:
  """Create a processed DataSource, with FreqDataDims, and one DataDimRef for each DataDim.
  NB Assumes that number and order of dimensions match the Experiment.
  Parameter names generally follow CCPN data model names. dataStore is a BlockedBinaryMatrix object
  Sequence type parameters are one per dimension.
  Additional  parameters for the DataSource are passed in additionalParameters"""

  numDim = len(numPoints)

  if numDim != experiment.numDim:
    raise ApiError('numDim = %d != %d = experiment.numDim' % (numDim, experiment.numDim))

  spectrum = experiment.newDataSource(name=name, dataStore=dataStore, scale=scale, details=details,
                                      numDim=numDim, dataType='processed', **additionalParameters)
 
  # NBNB TBD This is not a CCPN attribute. Removed. Put back if you need it after all,
  # spectrum.writeable = writeable

  if not numPointsOrig:
    numPointsOrig = numPoints

  if not pointOffset:
    pointOffset = (0,) * numDim

  if not isComplex:
    isComplex = (False,) * numDim


  for n , expDim in enumerate(experiment.sortedExpDims()):
    freqDataDim = spectrum.newFreqDataDim(dim=n+1, numPoints=numPoints[n],
                             isComplex=isComplex[n], numPointsOrig=numPointsOrig[n],
                             pointOffset=pointOffset[n],
                             valuePerPoint=sw[n]/float(numPoints[n]), expDim=expDim)
    expDimRef = (expDim.findFirstExpDimRef(measurementType='Shift') or expDim.findFirstExpDimRef())
    if expDimRef:
      freqDataDim.newDataDimRef(refPoint=refpt[n], refValue=refppm[n], expDimRef=expDimRef)

  return spectrum

def createBlockedMatrix(dataUrl:object, path:str, numPoints:Sequence, blockSizes:Sequence=None,
                        isBigEndian:bool=True, numberType:str='float', isComplex:bool=None,
                        headerSize:int=0, blockHeaderSize:int=0, nByte=4,
                       **additionalParameters) -> object:
  """Create BlockedBinaryMatrix object. Explicit parameters are the most important,
  additional parameters to BlockedBinaryMatrix are passed in additionalParameters"""
  path = Path.normalisePath(path)

  if os.path.isabs(path):
    urlpath = Path.normalisePath(dataUrl.url.path, makeAbsolute=True)
    if not path.startswith(urlpath):
      raise ApiError('path = %s, does not start with dataUrl path = %s' % (path, urlpath))
    if path == urlpath:
      raise ApiError('path = %s, same as dataUrl path but should be longer' % path)

    # TBD: below is a bit dangerous but should work (+1 is to remove '/')
    path = path[len(urlpath)+1:]

  if not blockSizes:
    blockSizes = determineBlockSizes(numPoints)

  if not isComplex:
    isComplex = len(numPoints) * [False]

  dataLocationStore = dataUrl.dataLocationStore

  matrix = dataLocationStore.newBlockedBinaryMatrix(dataUrl=dataUrl, path=path,
                 numPoints=numPoints, blockSizes=blockSizes, isBigEndian=isBigEndian,
                 numberType=numberType, isComplex=isComplex, headerSize=headerSize,
                 blockHeaderSize=blockHeaderSize, nByte=nByte, **additionalParameters)

  return matrix
  
# if __name__ == '__main__':
#
#   from ccpncore.api.memops.Implementation import MemopsRoot
#   from ccpncore.api.memops.Implementation import Url
#
#   r = MemopsRoot()
#   n = r.newNmrProject(name='testNmrProject')
#   e = createExperiment(n, name='testExpt', numDim=2, sf=(800, 150), isotopeCodes=('H', 'C'))
#   numPoints = (512, 256)
#   d = r.newDataLocationStore(name='testDLS')
#   u = d.newDataUrl(name='testDataUrl', url=Url(path='/my/test/path'))
#   m = createBlockedMatrix(u, 'test.spc', numPoints)
#   s = createDataSource(e, name='testSpectrum', numPoints=numPoints, sw=(8000, 2000),
#                      refppm=(5, 50), refpt = (256, 128), dataStore=m)
#
