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

def getAxisCodes(spectrum):
  """ Return axis codes for spectrum, using the isotopeCode if the axisCode not set
  """
  return DataSource.getAxisCodes(spectrum.apiDataSource)

def axisCodeMapIndices(axisCodes:Sequence, refAxisCodes:Sequence)->list:
  """get mapping tuple so that axisCodes[result[ii]] matches refAxisCodes[ii]
  all axisCodes must match, but result can contain None if refAxisCodes is longer"""

 # All axisCodes: ['Br', 'C', 'CA', 'CA1', 'CO', 'CO1', 'C1', 'C2', 'Ch', 'Ch1',
 # 'F', 'H', 'H1', 'H2', 'H3', 'H4', 'Hc', 'Hc1', 'Hcn', 'Hcn1', 'Hn', 'Hn1',
 # 'Jch', 'Jhh', 'Jhn', 'Jhp', 'MQcc', 'MQhh', 'MQhhhh', 'N', 'N1', 'Nh', 'Nh1',
 # 'P', 'delay']
  #
  # Replace Hcn with Hx?
  #
  # NB 'fidXyz' match other FID, then 'delay'
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
