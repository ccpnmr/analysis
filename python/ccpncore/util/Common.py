"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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
"""Common utilities

NB Must conform to Python 2.1. Imported in ObjectDomain.
"""

import os
import sys
import json
import itertools
import numpy
from numbers import Real
from collections import abc as collectionClasses
from functools import total_ordering

from ccpncore.util import Path
from ccpncore.lib import Constants as coreLibConstants
from ccpncore.memops.metamodel import Constants as metaConstants

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

apiTopModule = 'ccpncore.api'


@total_ordering
class __MinType(object):
    def __le__(self, other):
        return True

    def __eq__(self, other):
        return (self is other)

__smallest = __MinType()



def getClassFromFullName(qualifiedName):
  """ Get Api class from fully qualified (dot-separated) name
  """
  pathList = qualifiedName.split('.')
  mod = __import__('.'.join([apiTopModule] + pathList[:-1]),{},{},[pathList[-1]])
  return getattr(mod,pathList[-1])


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
        from ccpncore.util.Logging import getLogger
        getLogger().warning("Import failed for %s.%s" % (modname,ff))

  for name in listdir2:
    newdirname = Path.joinPath(dirname,name)
    if os.path.isdir(newdirname) and name.find('.') == -1:
      recursiveImport(newdirname, prefix + name,ignoreModules)


def getConfigParameter(name):
  """get configuration parameter, from reading configuration file
  """

  file = Path.joinPath(Path.getTopDirectory(),metaConstants.configFilePath)
  dd = json.load(open(file))
  return dd[
    'configuration'].get(name)


def isWindowsOS():

  return sys.platform[:3].lower() == 'win'


def parseSequenceCode(value):
  """split sequence code into (seqCode,seqInsertCode, offset) tuple"""

  # sequenceCodePattern = re.compile('(\d+)?(.*?)(\+\d+|\-\d+)?$')

  tt = coreLibConstants.sequenceCodePattern.match(value.strip()).groups()

  if not tt[0] and not tt[1]:
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

def universalSortKey(key):
  """"Universal sort key function. Works in nested sequences"""
  smallest = float('-inf')
  if key is None:
    # First None
    return ('',)

  elif isinstance(key, bool):
    # Then bools
    return (chr(1), key)

  elif isinstance(key, Real):
    # Then real numbers
    return (chr(2), key)

  elif isinstance(key,str):
    # Then strings - strings starting with 'real values' are last, sorted by the real value
    for ii in range(len(key)-1, 0, -1):
      try:
        val = float(key[:ii])
        break
      except:
        pass
    else:
      val = smallest
    #
    return (chr(3), val, key)

  elif isinstance(key, numpy.ndarray):
    # Numpy special case, as 1) it might be as sequence, 2) it has __lt__ but does not compare
    return (key.__class__.__name__, key.size(), repr(key))

  elif isinstance(key, bytes) or isinstance(key, bytearray):
    return (key.__class__.__name__, key)

  elif isinstance(key, collectionClasses.Sequence):
    # NBNB TBD FIXME
    # This will BREAK for nested sequences
    return (key.__class__.__name__, [universalSortKey(x) for x in key])

  else:
    if hasattr(key, '__len__'):
      val = len(key)
    else:
      val = smallest

    if not hasattr(key, '__lt__'):
      key = repr(key)

    return (key.__class__.__name__, val, key)

# NBNB TBD consider 1) updrading sorting to sort internal ints by number,
# 2) upgrading to universal sort key

def numericStringSortKey(key):
  """
  Returns customized sort key
  1) Works on single values or sequences
  2) sorts None as smallest value of whatever type.
  3) string fields that start with numeric values sort by that value
  E.g. '11a', '+1.1e1zz' or '11.0' sort as numeric 11.0
  """
  number = 0.0
  if isinstance(key,str):
    for ii in range(1,len(key)+1):
      try:
        number = float(key[:ii])
      except:
        pass
    #
    return [number, key]

  elif key is None:
    return [number, __smallest]

  elif isinstance(key, collectionClasses.Sequence):
    return list(itertools.chain(numericStringSortKey(x) for x in key))

  else:
    return [number, key]


# def integerStringSortKey(key):
#   """return sort key so that strings starting with an integer sort as if by integer
#
#   params:: key  either sequence or single string"""
#
#   if isinstance(key, str):
#     vv = key.lstrip()
#     ll = []
#     for char in vv:
#       if char.isdigit():
#         ll.append(char)
#       else:
#         break
#     if ll :
#       return '%30s' % ''.join(ll) + vv[len(ll):]
#     else:
#       return key
#
#   else:
#     result = list(key)
#
#     for ii,val in enumerate(result):
#       if isinstance(val, str):
#         vv = val.lstrip()
#         ll = []
#         for char in vv:
#           if char.isdigit():
#             ll.append(char)
#           else:
#             break
#         if ll :
#           result[ii] = '%30s' % ''.join(ll) + vv[len(ll):]
#
#     return result

def dictionaryProduct(dict1:dict, dict2:dict) -> dict:
  """multiply input {a:x}, {b:y} to result {(a,b):x*y} dictionary"""
  result = {}
  for key1,val1 in dict1.items():
    for key2,val2 in dict2.items():
      result[(key1,key2)] = val1 * val2
  #
  return result

def uniquify(sequence:collectionClasses.Sequence) -> list:
  """Get list of unique elements in sequence, in order of first appearance"""
  seen = set()
  seen_add = seen.add
  return [x for x in sequence if x not in seen and not seen_add(x)]

def isClose(a:float, b:float, relTolerance:float=1e-05, absTolerance=1e-08) -> bool:
  """Are a and b identical within reasonable floating point tolerance?
  Uses sum of relative (relTolerance) and absolute (absTolerance) difference

  Inspired by numpy.isclose()"""
  return (abs(a - b) <= (absTolerance + relTolerance * abs(b)))

def flattenIfNumpy(data, shape=None):
  """If data are Numpy, convert to flat array
  If shape is given, check that numpy fits shape, and flat sequence fits total number of elements"""

  if hasattr(data, 'flat'):
    # Numpy array
    if shape and data.shape != tuple(shape):
      raise ValueError("Shape of array data is %s, should be %s" % (data.shape, shape))
    data = data.flat

  elif shape:
      elementCount = 1
      for x in shape:
        elementCount *= x
      if len(data) != elementCount:
        raise ValueError("Number of elements in data sequence is %s, should be %s"
                         % (len(data), elementCount))
  #
  return data

def _resetParentLink(apiObject, downLink:str, tag:str, value):
  """Change single-attribute key of apiObject with property name tag to value

  downLink is the name of the link from parent to obj"""

  parent = apiObject.parent
  siblings = getattr(parent, downLink)
  if any(x for x in siblings if x is not apiObject and getattr(x, tag) == value):
    raise ValueError("Cannot rename %s - pre-existing object with key %s:%s"
        % apiObject, tag, value)

  oldKey = getattr(apiObject, tag)
  root = apiObject.root
  root.__dict__['override'] = True

  # Set up for undo
  undo = root._undo
  if undo is not None:
    undo.increaseBlocking()

  try:
    parentDict = parent.__dict__[downLink]
    del parentDict[oldKey]
    setattr(apiObject, tag, value)
    parentDict[value] = apiObject

  finally:
    # reset override and set isModified
    root.__dict__['override'] = False
    apiObject.topObject.__dict__['isModified'] = True
    if undo is not None:
      undo.decreaseBlocking()

  if undo is not None:
    undo.newItem(_resetParentLink, _resetParentLink, undoArgs=(apiObject, downLink, tag, oldKey),
                 redoArgs=(apiObject, downLink, tag, value))

  # call notifiers:
