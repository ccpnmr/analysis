"""Miscellaneous common utilities

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
import itertools
from typing import Sequence

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
"""Common utilities

NB Must conform to Python 2.1. Imported in ObjectDomain.
"""

import datetime
import os
import random
import sys
import typing
# import collections
import string
# from functools import total_ordering

from ccpn.util import Path, Constants
from ccpnmodel.ccpncore.lib import Constants as coreLibConstants

# Max value used for random integer. Set to be expressible as a signed 32-bit integer.
maxRandomInt =  2000000000

WHITESPACE_AND_NULL =  {'\x00', '\t', '\n', '\r', '\x0b', '\x0c'}

# valid characters for file names
# NB string.ascii_letters and string.digits are not compatible
# with Python 2.1 (used in ObjectDomain)
defaultFileNameChar = '_'
separatorFileNameChar = '+'
validFileNamePartChars = ('abcdefghijklmnopqrstuvwxyz'
                          'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                          + defaultFileNameChar)
validCcpnFileNameChars  = validFileNamePartChars + '-.' + separatorFileNameChar

# # Not used - Rasmus 20/2/2017
# Sentinel = collections.namedtuple('Sentinel', ['value'])



def convertStringToFileName(fileNameString, validChars=validCcpnFileNameChars,
                            defaultChar=defaultFileNameChar):

  ll = [x for x in fileNameString]
  for ii,char in enumerate(ll):
    if char not in validChars:
      ll[ii] = defaultChar
  #
  return ''.join(ll)

def getCcpFileString(fileNameString):
  """
  Changes an input string to the one used for a component of file names.
  """

  return convertStringToFileName(fileNameString, validFileNamePartChars,
                                   defaultFileNameChar)

def incrementName(name:str) -> str:
  """Add '_1' to name or change suffix '_n' to '_(n+1) """
  ll = name.rsplit('_',1)
  if len(ll) == 2:
    try:
      ll[1] = str(int(ll[1]) + 1)
      return '_'.join(ll)

    except ValueError:
      pass

  return name + '_1'


def recursiveImport(dirname, modname=None, ignoreModules=None, force=False):
  """ recursively import all .py files
  (not starting with '__' and not containing internal '.' in their name)
  from directory dirname and all its subdirectories, provided they
  contain '__init__.py'
  Serves to check that files compile without error

  modname is the module name (dot-separated) corresponding to the directory
  dirName.
  If modname is None, dirname must be on the pythonPath

  Note that there are potential problems if the files we want are not
  the ones encountered first on the pythonPath
  """

  listdir = os.listdir(dirname)
  try:
    listdir.remove('__init__.py')
  except ValueError:
    if not force:
      return

  files = []

  if ignoreModules is None:
    ignoreModules = []

  if modname is None:
    prefix = ''
  else:
    prefix = modname + '.'

  listdir2 = []
  for name in listdir:
    head,ext = os.path.splitext(name)
    if (prefix + head) in ignoreModules:
      pass
    elif ext == '.py' and head.find('.') == -1:
      files.append(head)
    else:
      listdir2.append(name)

  # import directory and underlying directories
  if modname:
    # Note that files is never empty, so module is lowest level not toplevel
    for ff in files:
      try:
        __import__(modname, {}, {}, [ff])
      except:
        # We want log output, not an Exception in all cases here
        from ccpn.util.Logging import getLogger
        getLogger().warning("Import failed for %s.%s" % (modname,ff))

  for name in listdir2:
    newdirname = Path.joinPath(dirname,name)
    if os.path.isdir(newdirname) and name.find('.') == -1:
      recursiveImport(newdirname, prefix + name,ignoreModules)


def isWindowsOS():

  return sys.platform[:3].lower() == 'win'


def parseSequenceCode(value):
  """split sequence code into (seqCode,seqInsertCode, offset) tuple"""

  # sequenceCodePattern = re.compile('(\d+)?(.*?)(\+\d+|\-\d+)?$')

  tt = coreLibConstants.sequenceCodePattern.match(value.strip()).groups()

  if tt[0] is None and not tt[1]:
    # special case: entire string matches offset modifier and is misread
    return None, tt[2], None
  else:
    return (
      tt[0] and int(tt[0]),      # None or an integer
      tt[1],                     # Text string, possibly empty
      tt[2] and int(tt[2]),      # None or an integer
    )

def splitIntFromChars(value:str):
  """convert a string with a leading integer optionally followed by characters
  into an (integer,string) tuple"""

  value = value.strip()

  for ii in reversed(range(1,len(value)+1)):
    try:
      number = int(value[:ii])
      chars = value[ii:]
      break
    except ValueError:
      continue
  else:
    number = None
    chars = value

  return number,chars

def dictionaryProduct(dict1:dict, dict2:dict) -> dict:
  """multiply input {a:x}, {b:y} to result {(a,b):x*y} dictionary"""
  result = {}
  for key1,val1 in dict1.items():
    for key2,val2 in dict2.items():
      result[(key1,key2)] = val1 * val2
  #
  return result

def uniquify(sequence:typing.Sequence) -> list:
  """Get list of unique elements in sequence, in order of first appearance"""
  seen = set()
  seen_add = seen.add
  return [x for x in sequence if x not in seen and not seen_add(x)]

def isClose(a:float, b:float, relTolerance:float=1e-05, absTolerance=1e-08) -> bool:
  """Are a and b identical within reasonable floating point tolerance?
  Uses sum of relative (relTolerance) and absolute (absTolerance) difference

  Inspired by numpy.isclose()"""
  return (abs(a - b) <= (absTolerance + relTolerance * abs(b)))

# # No longer used - Rasmus 20/2/2017
# def flattenIfNumpy(data, shape=None):
#   """If data are Numpy, convert to flat array
#   If shape is given, check that numpy fits shape, and flat sequence fits total number of elements"""
#
#   if hasattr(data, 'flat'):
#     # Numpy array
#     if shape and data.shape != tuple(shape):
#       raise ValueError("Shape of array data is %s, should be %s" % (data.shape, shape))
#     data = data.flat
#
#   elif shape:
#       elementCount = 1
#       for x in shape:
#         elementCount *= x
#       if len(data) != elementCount:
#         raise ValueError("Number of elements in data sequence is %s, should be %s"
#                          % (len(data), elementCount))
#   #
#   return data

def stringToIdentifier(value:str) -> str:
  """Convert string to identifier, replacing non-alphanumeric values by underscore"""
  if value.isidentifier():
    return value
  else:
    return ''.join(x if x.isalnum() else '_' for x in value)

def getTimeStamp() -> str:
  """Get iso-formtted timestamp"""
  return datetime.datetime.today().isoformat()

def getUuid(programName, timeStamp=None):
  """Get UUid following the NEF convention"""
  if timeStamp is None:
    timeStamp = getTimeStamp()
  return '%s-%s-%s' % (programName, timeStamp, random.randint(0, maxRandomInt))


def name2IsotopeCode(name:str=None) -> str:
  """Get standard isotope code matching atom name or axisCode string

  """
  if not name:
    return None

  result = Constants.DEFAULT_ISOTOPE_DICT.get(name[0])
  if result is None:
    if name[0].isdigit():
      ss = name.title()
      for key in Constants.isotopeRecords:
        if ss.startswith(key):
          if name[:len(key)].isupper():
            result = key
          break
    else:
      result = Constants.DEFAULT_ISOTOPE_DICT.get(name[:2])
  #
  return result


def isotopeCode2Nucleus(isotopeCode:str=None):
  if not isotopeCode:
    return None

  record = Constants.isotopeRecords.get(isotopeCode)
  if record is None:
    return None
  else:
    return record.symbol.upper()

  # for tag,val in sorted(Constants.DEFAULT_ISOTOPE_DICT.items()):
  #   if val == isotopeCode:
  #     return tag
  # else:
  #   return None


def name2ElementSymbol(name:str) -> str:
  """Get standard element symbol matching name or axisCode

  NB, the first letter takes precedence, so e.g. 'CD' returns 'C' (carbon)
  rather than 'CD' (Cadmium)"""

  # NB, We deliberately do NOT use 'value in Constants.DEFAULT_ISOTOPE_DICT'
  # We want to avoid elements that are in the dict but have value None.
  if not name:
    return None
  elif Constants.DEFAULT_ISOTOPE_DICT.get(name[0]) is not None:
    return name[0]
  elif Constants.DEFAULT_ISOTOPE_DICT.get(name[:2]) is not None:
    return name[:2]
  elif name[0].isdigit():
    ss = name.title()
    for key,record in Constants.isotopeRecords.items():
      if ss.startswith(key):
        if name[:len(key)].isupper():
          return record.symbol.upper()
        break
  #
  return None

  # for tag in reversed(sorted(Constants.DEFAULT_ISOTOPE_DICT)):
  #   # Reversed looping guarantees that the longer of two matches will be chosen
  #   if name.startswith(tag):
  #     result = tag
  #     break
  # else:
  #   result = None
  # #
  # return result


def checkIsotope(text:str) -> str:
  """Convert isotope specifier string to most probable isotope code - defaulting to '1H'

  This function is intended for external format isotope specifications, *not* for
  axisCodes or atom names, hence the difference to name2ElementSymbol.
  """
  defaultIsotope = '1H'
  name = text.strip().upper()

  if not name:
    return defaultIsotope

  if name in Constants.isotopeRecords:
    # Superfluous but should speed things up
    return name

  for isotopeCode in Constants.isotopeRecords:
    # NB checking this first means that e.g. 'H13C' returns '13C' rather than '1H'
    if isotopeCode.upper() in name:
      return isotopeCode

  # NB order of checking means that e.g. 'CA' returns Calcium rather than Carbon
  result =  (Constants.DEFAULT_ISOTOPE_DICT.get(name[:2])
             or Constants.DEFAULT_ISOTOPE_DICT.get(name[0]))

  if result is None:
    if name == 'D':
      # special case
      result  = '2H'
    else:
      result = defaultIsotope
  #
  return result


def axisCodeMatch(axisCode:str, refAxisCodes:Sequence[str])->str:
  """Get refAxisCode that best matches axisCode """
  for ii,indx in enumerate(_axisCodeMapIndices([axisCode], refAxisCodes)):
    if indx == 0:
      # We have a match
      return refAxisCodes[ii]
  else:
    return None


def axisCodeMapping(axisCodes:Sequence[str], refAxisCodes:Sequence[str])->dict:
  """get {axisCode:refAxisCode} mapping dictionary
  all axisCodes must match, or dictionary will be empty
  NB a series of single-letter axisCodes (e.g. 'N', 'HCN') can be passed in as a string"""
  result = {}
  mapIndices =  _axisCodeMapIndices(axisCodes, refAxisCodes)
  if mapIndices:
    for ii, refAxisCode in enumerate(refAxisCodes):
      indx = mapIndices[ii]
      if indx is not None:
        result[axisCodes[indx]] = refAxisCode
  #
  return result

def reorder(values:typing.Sequence, axisCodes:typing.Sequence[str],
            refAxisCodes:typing.Sequence[str]) -> list:
  """reorder values in axisCode order to refAxisCode order, by matching axisCodes

  NB, the result will be the length of refAxisCodes, with additional Nones inserted
  if this is longer than the values.

  NB if there are multiple matches possible, one is chosen by heuristics"""
  if len(values) != len(axisCodes):
    raise ValueError("Length mismatch between %s and %s" % (values, axisCodes))
  remapping = _axisCodeMapIndices(axisCodes, refAxisCodes)
  result = list(values[x] for x in remapping)
  #
  return result


def _axisCodeMapIndices(axisCodes:Sequence[str], refAxisCodes:Sequence[str])->list:
  """get mapping tuple so that axisCodes[result[ii]] matches refAxisCodes[ii]
  all axisCodes must match, but result can contain None if refAxisCodes is longer
  if axisCodes contain duplicates, you will get one of possible matches"""

  #CCPNINTERNAL - used in multiple places to map display order and spectrum order


  lenDifference = len(refAxisCodes) - len(axisCodes)
  if lenDifference < 0 :
    return None

  # Set up match matrix
  matches = []
  for code in axisCodes:
    matches.append([axisCodesCompare(code, x, mismatch=-999999) for x in refAxisCodes])

  # find best mapping
  maxScore = sum(len(x) for x in axisCodes)
  bestscore = -1
  results = None
  values = list(range(len(axisCodes))) + [None] * lenDifference
  for permutation in itertools.permutations(values):
    score = 0
    for ii, jj in enumerate(permutation):
      if jj is not None:
        score += matches[jj][ii]
    if score > bestscore:
      bestscore = score
      results = [permutation]
    elif score == maxScore:
      # it cannot get any higher
      results.append(permutation)
  #
  if results:
    # Pick the first of the equally good matches as the default answer
    result = results[0]
    if len(results) > 1:
      # Multiple matches - try to select on pairs of bound atoms
      # NB we do not need to be rigorous as this is only used to resolve ambiguity
      # NB this is necessary to do a correct match of e.g. Hc, Ch, H to Hc, Hc1, Ch1
      boundCodeDicts = []
      for tryCodes in axisCodes, refAxisCodes:
        boundCodes = {}
        boundCodeDicts.append(boundCodes)
        for ii, code in enumerate(tryCodes):
          if len(code) > 1:
            for jj in range(ii+1, len(tryCodes)):
              code2 = tryCodes[jj]
              if len(code2) > 1:
                if (code[0].isupper() and code[0].lower() == code2[1] and
                    code2[0].isupper() and code2[0].lower() == code[1] and
                    code[2:] == code2[2:]):
                  # Matches pair of bound atoms - e.g. Hc1, Ch1
                  boundCodes[tryCodes.index(code)] = tryCodes.index(code2)
                  boundCodes[tryCodes.index(code2)] = tryCodes.index(code)

      if boundCodeDicts[0] and boundCodeDicts[1]:
        # bound pairs on both sides - check for matching pairs
        bestscore = -1
        for permutation in results:
          score = 0
          for idx1, idx2 in boundCodeDicts[1].items():
            target = permutation[idx1]
            if target is not None and target ==  boundCodeDicts[0].get(permutation[idx2]):
              score += 1
          if score > bestscore:
            bestscore = score
            result = permutation
  else:
    result = None
  #
  return result


def axisCodesCompare(code:str, code2:str, mismatch:int=0) -> int:
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


def doAxisCodesMatch(axisCodes:Sequence[str], refAxisCodes:Sequence[str])->bool:
  """Return True if axisCodes match refAxisCodes else False"""
  if len(axisCodes) != len(refAxisCodes):
    return False

  for ii, code in enumerate(axisCodes):
    if not axisCodesCompare(code, refAxisCodes[ii]):
      return False
  #
  return True


def stringifier(*fields, floatFormat:str=None) -> typing.Callable[[object], str]:
  """Get stringifier function, that will format an object x according to

  <str(x): field1=x.field1, field2=x.field2, ...>

  All floating point values encountered will be formatted according to floatFormat"""
  if floatFormat is None:
    # use default formatter, avoiding continuous creation of new ones
    localFormatter = stdLocalFormatter
  else:
    localFormatter = LocalFormatter(overrideFloatFormat=floatFormat)

  fieldFormats = []
  for field in fields:
    # String will be 'field1={_obj.field1}
    fieldFormats.append('{0}={{_obj.{0}!r}}'.format(field))

  formatString = '<{_obj.pid!s}| ' + ', '.join(fieldFormats) + '>'

  def formatter(x):
    return localFormatter.format(format_string=formatString, _obj=x)

  return formatter


class LocalFormatter(string.Formatter):
  """Overrides the string formatter to change the float formatting"""
  def __init__(self, overrideFloatFormat:str='.6g'):
    super().__init__()
    self.overrideFloatFormat = overrideFloatFormat

  def convert_field(self, value, conversion):
    # do any conversion on the resulting object
    # NB, conversion parameter is not used

    if hasattr(value, 'pid'):
      return str(value)
    elif isinstance(value, float):
      return format(value, self.overrideFloatFormat)
    elif type(value) == tuple:
      # Deliberate. We do NOT want to catch tuple subtypes here
      end = ',)' if len(value) == 1 else ')'
      return '(' + ', '.join(self.convert_field(x, 'r') for x in value) + end
    elif type(value) == list:
      # Deliberate. We do NOT want to catch list subtypes here
      return '[' + ', '.join(self.convert_field(x, 'r') for x in value) + ']'
    elif conversion is None:
        return value
    elif conversion == 's':
        return str(value)
    elif conversion == 'r':
        return repr(value)
    elif conversion == 'a':
        return ascii(value)
    raise ValueError("Unknown conversion specifier {0!s}".format(conversion))

stdLocalFormatter = LocalFormatter()