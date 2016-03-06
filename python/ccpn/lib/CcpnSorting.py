
#=========================================================================================
# Ccpn-specific variant of functions for sorting and comparison.
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
import re
from ccpncore.util import  Sorting
SPLITONDOTS = re.compile("([.])")

_keyCache = {}

#
def stringSortKey(key:str) -> tuple:
  """Sort key for strings.

  Custom CCPN version of stringSortKey that splits on embedded dots before further processing

  Returns an alternating tuple of (possibly empty) strings interspersed with (float,string) tuples,
  where the float is the converted value of the substring.
  First and last element are always strings.

  If the entire string evaluates to a float, the result is ('', '(floatVal, stringVal), '')
  Otherwise the numeric tuples are (intVal, subStringVal).
  Substrings recognised as integers are an optional series of ' ',
  an optional sign, and a series of digits - or REGEX '[ ]*[+-]?\d+'

  Example of sorting order
  ['', 'NaN', '-1', '-1A', '0.0', '1', '2', '15', '3.2e12', 'Inf',
  'Ahh', 'b',  'b2', 'b12', 'bb', 'ciao'] """

  global _keyCache
  result = _keyCache.get(key)

  if result is None:
    tt = Sorting._floatStringKey(key)
    if tt:
      # Read as floating point numbr if possible
      result = (tt,)
    elif '.'  in key:
      # Otherwise treat dot ('.') as a field separator
      ll = [x for x in SPLITONDOTS.split(key) if x != '']
      result =  tuple(Sorting._numericSplitString(x) for x in  ll)
    else:
      # Simple string
      result = (Sorting._numericSplitString(key),)
    #
    _keyCache[key] = result
  #
  return result


def _ccpnOrderedKey(key):
  """Special case sorting key for CCPN - groups CCPN AbstractWrapperObjects together
  before sorting by class name"""

  # import here to avoid circular imports
  from ccpn import AbstractWrapperObject

  cls = key.__class__

  ordering = 0
  if isinstance(key, AbstractWrapperObject):
    ordering = -1
  #
  return (ordering, cls.__name__, id(cls), key)


def universalSortKey(key):
  """Custom universalSortKey with local stringSortKey variant for strings and
  CCPN WrapperObjects sorted together"""
  return Sorting.universalSortKey(key, _stringOrderingHook=stringSortKey,
                                  _orderedKeyHook=_ccpnOrderedKey)