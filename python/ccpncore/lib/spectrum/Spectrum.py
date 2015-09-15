"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

from ccpncore.util.typing import Sequence
from ccpncore.util import Path
from ccpncore.lib.spectrum.BlockData import determineBlockSizes
from ccpncore.memops.ApiError import ApiError
from ccpncore.api.ccp.nmr.Nmr import ExpDimRef


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

def axisCodeMatch(axisCode:str, refAxisCodes:Sequence)->str:
  """Get refAxisCode that best matches axisCode """
  for ii,indx in enumerate(_axisCodeMapIndices([axisCode], refAxisCodes)):
    if indx == 0:
      # We have a match
      return refAxisCodes[ii]
  else:
    return None

def axisCodeMapping(axisCodes:Sequence, refAxisCodes:Sequence)->dict:
  """get {axisCode:refAxisCode} mapping dictionary
  all axisCodes must match, or dictionary will be empty
  NB a series of single-letter axisCodes (e.g. 'N;, 'HCN') can be passed in as a string"""
  result = {}
  mapIndices =  _axisCodeMapIndices(axisCodes, refAxisCodes)
  if mapIndices:
    for ii, refAxisCode in enumerate(refAxisCodes):
      indx = mapIndices[ii]
      if indx is not None:
        result[axisCodes[indx]] = refAxisCodes
  #
  return result

#
def _axisCodeMapIndices(axisCodes:Sequence, refAxisCodes:Sequence)->list:
  """get mapping tuple so that axisCodes[result[ii]] matches refAxisCodes[ii]
  all axisCodes must match, but result can contain None if refAxisCodes is longer
  if axisCodes contain duplicates, youwill get one of possible matches"""

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

def dimensionTransferType(dataDims:Sequence)->str:
  """Get ExpTransferType connecting two dataDims - uses heuristics"""

  expDimRefs = [x.expDim.sortedExpDimRefs()[0] for x in dataDims]
  return _expDimRefTransferType(*expDimRefs)

def _expDimRefTransferType(expDimRef1:ExpDimRef, expDimRef2:ExpDimRef)->str:
  """Get ExpTransferType and isDirect boolean connecting two expDimRefs - uses heuristics"""

  # First try looking for one-bond axisCodes
  axisCode1 = expDimRef1.axisCode
  axisCode2 = expDimRef2.axisCode
  if len(axisCode1) > 1 and len(axisCode2) > 1:
    ss2 = axisCode2.upper()
    if axisCode1.upper() == ss2[1] + ss2[0] + ss2[2:]:
      if (axisCode1[0].isupper() and axisCode2[0].isupper() and
          axisCode1[1].islower() and axisCode2[1].islower()):
        # Hooray, we have a situation like 'Hn'/'Nh' or 'Hp1'/'Ph1'
        return ('onebond', True)

  # Still here - try with ExpPrototypes
  refExpDimRef1 = expDimRef1.refExpDimRef
  refExpDimRef2 = expDimRef2.refExpDimRef
  if None not in (refExpDimRef1, refExpDimRef2):
    for atomSite1 in refExpDimRef1.expMeasurement.atomSites:
      for atomSite2 in refExpDimRef2.expMeasurement.atomSites:
        ll = list(atomSite1.expTransfers.intersection(atomSite2.expTransfers))
        if len(ll) == 1:
          # We have an expTransfer that connects our expDimRefs
          return (ll[0].transferType, True)

  # Still here - try using expTransfer
  ll = list(expDimRef1.expTransfers.intersection(expDimRef2.expTransfers))
  if len(ll) == 1:
    return (ll[0].transferType, ll[0].isDirect)
  #
  return None

