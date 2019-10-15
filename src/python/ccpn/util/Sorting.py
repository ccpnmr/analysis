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
__dateModified__ = "$dateModified: 2017-07-07 16:32:59 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

# Functions for sorting and comparison.

# NBNB TBD 1) Add SMALLEST and LARGEST sorting sentinels

# NBNB TBD 2) Support circular data structures by making circular keys for them


import math
import re
from collections import OrderedDict
from numbers import Real
from ccpn.util import Constants


NUMERICSPLIT = re.compile("([ ]*[+-]?\d+)")

sortOrder = [
    'None',
    'bool',
    'NaN',
    'Real',
    'str',
    'dict',
    'list',
    'tuple',
    'ordered',
    'unordered'
    ]
_sortOrderDict = dict((tt[1], tt[0]) for tt in enumerate(sortOrder))


def _orderedKey(key):
    """Key for ordered objects, whose __lt__ function returns a Boolean.
    Sorts by class name, then class id, then uses teh object's internal comparison function
    Can be overridden for custom grouping and keys"""
    cls = key.__class__
    ordering = 0
    #
    return (ordering, cls.__name__, id(cls), key)


def _unorderedKey(key):
    """Default key for unordered object that has no more sensible key
    Uses class name, then class id, then __name__ and len() ( where available), then defaults to id()"""
    cls = key.__class__
    ordering = 0
    name = key.__name__ if hasattr(key, '__name__') else ''
    length = len(key) if hasattr(cls, '__len__') else 0
    key = (ordering, cls.__name__, id(cls), name, length, id(key))
    #
    return key


def stringSortKey(key):
    """Sort key for strings.

    If the entire string evaluates to a float, the result is ('', '(floatVal, stringVal), '')

    Otherwise returns _numericSplitString(key)

    Example of sorting order:
    ['', 'NaN', '-1', '-1A', '0.0', '1', '2', '15', '3.2e12', 'Inf',
    'Ahh', 'b',  'b2', 'b12', 'bb', 'ciao'] """

    return _floatStringKey(key) or _numericSplitString(key)


def _numericSplitString(key):
    """
    Returns an alternating tuple of (possibly empty) strings interspersed with (float,string) tuples,
    where the float is the converted value of the substring.
    First and last element are always strings.

    The numeric tuples are (intVal, subStringVal).
    Substrings recognised as integers are an optional series of ' ',
    an optional sign, and a series of digits - or REGEX '[ ]*[+-]?\d+'"""
    matches = list(NUMERICSPLIT.split(key))
    for ii in range(1, len(matches), 2):
        matches[ii] = (int(matches[ii]), matches[ii])
    #
    return tuple(matches)


def _floatStringKey(key: str) -> tuple:
    """Get key if string evaluates to a float, empty tuple otherwise"""
    try:
        # first strings that evaluate to floats
        floatkey = float(key)
        if math.isnan(floatkey):
            # Put NaN before -Infinity
            return ('', (Constants.NEGINFINITY, ''), '')
        else:
            return ('', (floatkey, key), '')

    except ValueError:
        # String did not evaluate to float - return empty tuple
        return ()


def universalSortKey(key, _stringOrderingHook=None, _orderedKeyHook=_orderedKey,
                     _unorderedKeyHook=_unorderedKey):
    """Sort mixed types by type, then value or id. Should work for all object types.

    This function serves to sort mixed and unpredictable types,
    e.g. for sorting rows in a mixed-type (or any-type) table,
    for processing unordered input in semi-reproducible order,
    or for preliminary hacking about with mixed-type data.
    Dicts, lists, and tuples are sorted by content, recursively.
    Circular references are treated by waiting for the RunTimeError
    after infinite recursion, and then treating the objects as unorderable.

    Sorting order of types is giving in the sortOrder list. Booleans are treated as a separate class.
    Otherwise all real numbers are compared by value, with NaN treated as small than -Infinity.
    Objects with types that are not treated explicitly ('ordered' and 'unordered') are sorted first
    by class name and class id. 'Ordered' objects are sorted by their internal comparison method,
    'unordered' objects by __name__, length, and id (where each is defined).

    The ordering keys for strings, orderable types (that support a __lt__ method),
    and unorderable types (that do not) can be modified by the optional hook parameters.

    The function identifies objects whose __lt__ function does not return a Boolean (e.g.
    numpy.ndarray) as unorderable. set and frozenset are special-cased as unorderable. The function
    may give unstable sorting results for objects whose __lt__ function returns a Boolean
    but does not define an ordering (as for sets), but it will sort these correctly by class."""

    params = {
        '_stringOrderingHook': _stringOrderingHook,
        '_orderedKeyHook'    : _orderedKeyHook,
        '_unorderedKeyHook'  : _unorderedKeyHook,
        }

    if key is None:
        category = 'None'

    elif isinstance(key, bool):
        category = 'bool'

    elif isinstance(key, Real):
        if math.isnan(key):
            category = 'NaN'
            key = None
        else:
            category = 'Real'

    elif isinstance(key, str):
        category = 'str'
        if _stringOrderingHook is not None:
            key = _stringOrderingHook(key)

    elif isinstance(key, dict):
        # Not identical to the Python 2 behaviour
        # Compares by keys, then by values. Unordered dicts are sorted first.
        try:
            items = list((universalSortKey(tt[0], **params),
                          universalSortKey(tt[1], **params)) for tt in key.items())
            if not isinstance(key, OrderedDict):
                items.sort()
            # key = tuple(tt[0] for tt in items), tuple(tt[1] for tt in items))
            key = tuple(tuple(x) for x in zip(items))
            category = 'dict'
        except RuntimeError:
            # Should be RecursionError from version 3.5 onwards
            # We have infinite recursion - default to generic object key
            category = 'unordered'
            key = _unorderedKeyHook(key)

    elif isinstance(key, list):
        try:
            key = tuple(universalSortKey(x, **params) for x in key)
            category = 'list'
        except RuntimeError:
            # Should be RecursionError from version 3.5
            # We have infinite recursion - default to generic object key
            category = 'unordered'
            key = _unorderedKeyHook(key)

    elif isinstance(key, tuple):
        try:
            key = tuple(universalSortKey(x, **params) for x in key)
            category = 'tuple'
        except RuntimeError:
            # Should be RecursionError from version 3.5 onwards
            # We have infinite recursion - default to generic object key
            # This should never happen for tuples, but better be safe.
            category = 'unordered'
            key = _unorderedKey(key)

    else:

        # Check for orderable types
        if hasattr(key, '__lt__'):
            try:
                # This should filter out most objects that abuse the comparison operators, like numpy,
                # pandas, SQL Alchemy, or sets.
                # Regrettably there is no way to know that a comparison operator that returns a Boolean
                # actually implements an ordering relation.
                isOrderable = (((key == key) is True) and ((key > key) is False)
                               and not isinstance(key, (set, frozenset)))
            except:
                isOrderable = False
        else:
            isOrderable = False

        cls = key.__class__
        if isOrderable:
            category = 'ordered'
            key = _orderedKeyHook(key)

        else:
            category = 'unordered'
            key = _unorderedKey(key)
    #
    return (_sortOrderDict[category], key)


def universalNaturalSortKey(key):
    """Universal sort key, using stringSortKey for strings"""
    return universalSortKey(key, _stringOrderingHook=stringSortKey)
