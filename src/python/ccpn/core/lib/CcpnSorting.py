""" Ccpn-specific variant of functions for sorting and comparison."""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:31 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import re
from ccpn.util import Sorting


SPLITONDOTS = re.compile("([.])")

_keyCache = {}


#
def stringSortKey(key: str) -> tuple:
    """Sort key for strings.

    Usage: sorted(aList, key=stringSortKey) or aList.sort(key=stringSortKey)

    Custom CCPN version of stringSortKey that sorts Pids on their individual components.

    Advanced:

    Splits on embedded dots before further processing, and
    Returns an alternating tuple of (possibly empty) strings interspersed with (float,string) tuples,
    where the float is the converted value of the substring.
    First and last element are always strings.

    If the entire string evaluates to a float, the result is ('', '(floatVal, stringVal), '')

    Otherwise the numeric tuples are (intVal, subStringVal).
    Substrings recognised as integers are an optional series of ' ',
    an optional sign, and a series of digits - or REGEX '[ ]*[+-]?\d+'
    For this type the key tuple is extended by (0,''),
    # so that end-of-key sorts as 0 rather thn coming first.

    Example of sorting order
    ['', 'NaN', '-1', '-1A', '0.0', '1', '2', '15', '3.2e12', 'Inf',
    'Ahh', 'b',  'b2', 'b12', 'bb', 'ciao'] """

    keyEnd = ((0, ''), '')

    global _keyCache
    result = _keyCache.get(key)

    if result is None:
        tt = Sorting._floatStringKey(key)
        if tt:
            # Read as floating point number if possible
            result = (tt,)
        elif '.' in key:
            # Otherwise treat dot ('.') as a field separator
            ll = [Sorting._numericSplitString(x) for x in SPLITONDOTS.split(key) if x != '']
            # result = tuple(x if x[-1] else x + keyEnd for x in ll)
            result = tuple(x + keyEnd for x in ll)
        else:
            # Simple string
            result = Sorting._numericSplitString(key)
            # if len(result) > 1 and result[-1] == '':
            if len(result) > 1:
                # String ended with a numeric field. Add keyEnd so that this sorts as 0
                # against keys where the next field is also numeric
                result += keyEnd
            result = (result,)
        #
        _keyCache[key] = result
    #
    return result


def _ccpnOrderedKey(key):
    """Special case sorting key for CCPN - groups CCPN AbstractWrapperObjects together
    before sorting by class name"""

    # import here to avoid circular imports
    from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject

    cls = key.__class__

    ordering = 0
    if isinstance(key, AbstractWrapperObject):
        ordering = -1
    #
    return (ordering, cls.__name__, id(cls), key)


def universalSortKey(key):
    """Custom universalSortKey, used to sort a list of mixed-type Python objects.

    Usage: sorted(aList, key=universalSortKey) or aList.sort(key=universalSortKey)

    Uses the local stringSortKey variant for strings and
    CCPN WrapperObjects sorted together"""
    return Sorting.universalSortKey(key, _stringOrderingHook=stringSortKey,
                                    _orderedKeyHook=_ccpnOrderedKey)
