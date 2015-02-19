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
import os
import itertools
from collections.abc import Sequence

from ccpncore.util import Path
from ccpncore.lib.spectrum.BlockData import determineBlockSizes
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
                        headerSize:int=0, blockHeaderSize:int=0, nByte=4, fileType=None,
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
                 blockHeaderSize=blockHeaderSize, nByte=nByte, fileType=fileType,
                 **additionalParameters)

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
def axisCodeMapIndices(axisCodes:Sequence, refAxisCodes:Sequence)->list:
  """get mapping tuple so that axisCodes[result[ii]] matches refAxisCodes[ii]
  all axisCodes must match, but result can contain None if refAxisCodes is longer"""

 # All known axisCodes: ['Br', 'C', 'CA', 'CA1', 'CO', 'CO1', 'C1', 'C2', 'Ch', 'Ch1',
 # 'F', 'H', 'H1', 'H2', 'H3', 'H4', 'Hc', 'Hc1', 'Hcn', 'Hcn1', 'Hn', 'Hn1',
 # 'Jch', 'Jhh', 'Jhn', 'Jhp', 'MQcc', 'MQhh', 'MQhhhh', 'N', 'N1', 'Nh', 'Nh1',
 # 'P', 'delay']
  #
  # 'J' matches 'Jx...'

  lenDifference = len(refAxisCodes) - len(axisCodes)
  if lenDifference < 0 :
    return None

  # Set up match matrix
  matches = []
  for code in axisCodes:
    matches.append([_compareAxisCodes(code, x) for x in refAxisCodes])

  # find best mapping
  maxScore = sum(len(x) for x in axisCodes)
  bestscore = -1
  result = None
  values = list(range(len(axisCodes))) + [None] * lenDifference
  for permutation in itertools.permutations(values):
    score = 0
    for ii, jj in enumerate(permutation):
      if jj is not None:
        score += matches[jj][ii]
    if score > bestscore:
      bestscore = score
      result = permutation
    if score >= maxScore:
      # it cannot get any higher
      break
  #
  return result

def _compareAxisCodes(code:str, code2:str, mismatch:int=-999999) -> int:
  """Score code, code2 for matching. Score is length of common prefix, or 'mismatch' if None"""

  if not code or not code2 or code[0] != code2[0]:
    score = mismatch
  elif code == code2:
    score = len(code)
  elif  code[0].islower():
    # 'fidX...' 'delay', etc. must match exactly
    score = mismatch
  elif code.startswith('MQ'):
    # 'MQxy...' must match exactly
    score = mismatch
  elif len(code) == 1 or code[1].isdigit() or len(code2) == 1 or code2[1].isdigit():
    # Match against a single upper-case letter on one side. Always OK
    score = 1
  else:
    # Partial match of two strings with at least two significant chars each
    score = len(os.path.commonprefix((code, code2))) or mismatch
    if score == 1:
      # Only first letter matches, second does not
      if ((code.startswith('Hn') and code2.startswith('Hcn')) or
            (code.startswith('Hcn') and code2.startswith('Hn'))):
        # Hn must matches Hcn
        score = 2
      else:
        # except as above we need at least two char match
        score = mismatch
    elif code.startswith('J') and score == 2:
      # 'Jab' matches 'J' or 'Jab...', but NOT 'Ja...'
      score = mismatch
  #
  return score

def doAxisCodesMatch(axisCodes:Sequence, refAxisCodes:Sequence)->bool:
  """Return True if axisCodes match refAxisCodes else False"""
  if len(axisCodes) != len(refAxisCodes):
    return False

  for ii, code in enumerate(axisCodes):
    if _compareAxisCodes(code, refAxisCodes[ii]) < 1:
      return False
  #
  return True