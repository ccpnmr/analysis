"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-09-20 12:22:13 +0100 (Mon, September 20, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-06-28 18:11:16 +0100 (Mon, June 28, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================
import itertools
from collections import OrderedDict


def _matchSingleAxisCodeLength(code1, code2):
    """return a score based on the mismatch in length
    """
    lenDiff = abs(len(code1) - len(code2))

    return (100 + 800 // (lenDiff + 1))


def _matchSingleAxisCode(code1: str = None, code2: str = None, exactMatch: bool = False, allowLowercase=True, mismatch=0) -> int:
    """number of matching characters
    code1, code2 = strings
    e.g. 'Hn1', 'H1'

    Compare single axis codes

    Must always be upper case first letter

    more matching letters = higher code
    difference in length reduces match

    'Jab' matches 'J' or 'Jab...', but NOT 'Ja...'      ie, 1 or 3 or more letter match

    MQ gets no match - only with other MQ axis codes

    Hn* always matches Hcn*

    :param code1: first axis code to compare
    :param code2: second axis code to compare
    :param exactMatch: only allow exact matches, True/False
    :return: score based on the match
    """
    if mismatch > 0:
        raise ValueError('mismatch cannot be greater than 0')

    # undefined codes
    if not code1 or not code2 or (code1[0].islower() and code2[0].islower() and not allowLowercase):
        return mismatch

    # if exactMatch is True then only test for exact match
    if exactMatch:
        return 1100 if (code1 == code2) else 0

    ms = [a for a in zip(code1, code2)]  # zips to the shortest string
    ss = 0

    # add extra tests from v2.4
    if (code1.startswith('MQ') and not code2.startswith('MQ')) or (code2.startswith('MQ') and not code1.startswith('MQ')):
        return mismatch
    # char followed by digit already accounted for

    # get count of matching characters - more characters -> higher score
    for a, b in ms:
        if a != b:
            break
        ss += 1

    # another v2.4 test
    if ss:
        if ((code1.startswith('Hn') and code2.startswith('Hcn')) or
                (code1.startswith('Hcn') and code2.startswith('Hn'))):
            # Hn must always match Hcn, give it a high score
            ss += 500

        if code1.startswith('J'):
            if ss == 2:  # must be a 1, or (3 or more) letter match
                return mismatch

        ss += _matchSingleAxisCodeLength(code1, code2)
    return (1000 + ss) if ss else mismatch


def _axisCodeMapIndices(axisCodes, refAxisCodes, checkBoundAtoms=True, allMatches=False, exactMatch=False):
    """get mapping tuple so that axisCodes[result[ii]] matches refAxisCodes[ii]
    all axisCodes must match, but result can contain None if refAxisCodes is longer
    if axisCodes contain duplicates, you will get one of possible matches
    """
    # CCPNINTERNAL - used in multiple places to map display order and spectrum order

    mismatch = -1000
    lenDifference = len(refAxisCodes) - len(axisCodes)

    # get the individual scores for the matching axisCodes
    matches = []
    for code in axisCodes:
        matches.append([_matchSingleAxisCode(code, x, exactMatch=exactMatch, mismatch=mismatch) for x in refAxisCodes])

    values = list(range(len(axisCodes))) + [None] * lenDifference
    _results = []
    for perm in itertools.permutations(values):
        perm = list(perm)
        score = 0
        for ii, jj in enumerate(perm):
            if jj is not None and ii < len(refAxisCodes):
                _score = matches[jj][ii]
                if _score <= 0:
                    perm[ii] = None
                score += _score
        if score > 0:
            _results.append((score, tuple(perm)))

    if _results:
        if checkBoundAtoms:
            # bound atoms matching - make a dict of matching atoms in axisCodes and refAxisCodes
            boundCodeDicts = []
            for tryCodes in axisCodes, refAxisCodes:
                boundCodes = {}
                boundCodeDicts.append(boundCodes)
                for ii, code in enumerate(tryCodes):
                    if len(code) > 1:
                        for jj in range(ii + 1, len(tryCodes)):
                            code2 = tryCodes[jj]
                            if len(code2) > 1:
                                # purely matching by checking the upper/lowerCase characters in the string
                                if (code[0].isupper() and code[0].lower() == code2[1] and
                                        code2[0].isupper() and code2[0].lower() == code[1] and
                                        code[2:] == code2[2:]):
                                    # Matches pair of bound atoms - e.g. match Hc - Ch, or Hc1 - Ch1
                                    boundCodes[tryCodes.index(code)] = tryCodes.index(code2)
                                    boundCodes[tryCodes.index(code2)] = tryCodes.index(code)

            if boundCodeDicts[0] and boundCodeDicts[1]:
                # bound pairs on both sides - check for matching pairs
                _bounds = []
                for score, perm in _results:
                    for idx1, idx2 in boundCodeDicts[1].items():
                        target = perm[idx1]
                        if target is not None and target == boundCodeDicts[0].get(perm[idx2]):
                            # if there is a match then increase the score
                            score *= 2
                            break
                    _bounds.append((score, perm))
                _results = _bounds

        _results = sorted(_results, reverse=True, key=lambda val: val[0])
        if allMatches:
            return tuple(res[1] for res in _results if res)
        else:
            return _results and _results[0] and _results[0][1]


def getAxisCodeMatch(axisCodes, refAxisCodes, exactMatch=False, allMatches=False, checkBoundAtoms=False) -> OrderedDict:
    """Return an OrderedDict containing the mapping from the refAxisCodes to axisCodes

    There may be multiple matches, or None for each axis code.

    Set allMatches to True to return all, or False for only the best match in each case

    e.g. for unique axis codes:

        getAxisCodeMatch(('Hn', 'Nh', 'C'), ('Nh', 'Hn'), allMatches=False)

        ->  { 'Hn':   'Hn'
              'Nh':   'Nh'
              'C' :   None
            }

        getAxisCodeMatch(('Hn', 'Nh', 'C'), ('Nh', 'Hn'), allMatches=True)

        ->  { 'Hn':   ('Hn',)
              'Nh':   ('Nh',)
              'C' :   ()
            }

    for similar repeated axis codes, possibly from matching isotopeCodes:

        getAxisCodeMatch(('Nh', 'H'), ('H', 'H1', 'N'), allMatches=False)

        ->  { 'Nh':   'N'
              'H' :   'H'
            }

        getAxisCodeMatch(('Nh', 'H'), ('H', 'H1', 'N'), allMatches=True)

        ->  { 'Nh':   ('N',)
              'H' :   ('H', 'H1')       <- in this case the first match is always the highest
            }
    """

    _found = OrderedDict()
    _matches = _axisCodeMapIndices(axisCodes, refAxisCodes, checkBoundAtoms=checkBoundAtoms, allMatches=allMatches, exactMatch=exactMatch)
    if allMatches:
        for _match in _matches or ():
            for ii, ind in enumerate(_match):
                if ind is not None and ii < len(refAxisCodes):
                    if axisCodes[ind] in _found:
                        if refAxisCodes[ii] not in _found[axisCodes[ind]]:
                            _found[axisCodes[ind]] += (refAxisCodes[ii],)
                    else:
                        _found[axisCodes[ind]] = (refAxisCodes[ii],)
        return OrderedDict([(axis, _found.get(axis) or ()) for axis in axisCodes])

    elif _matches:
        # _matches is a single item
        for ii, ind in enumerate(_matches):
            if ind is not None and ii < len(refAxisCodes):
                _found[axisCodes[ind]] = refAxisCodes[ii]
        return OrderedDict([(axis, _found.get(axis)) for axis in axisCodes])


def getAxisCodeMatchIndices(axisCodes, refAxisCodes, exactMatch=False, allMatches=False, checkBoundAtoms=False):
    """Return a tuple containing the indices for each axis code in axisCodes in refAxisCodes

    Only the best match is returned for each code, elements not found in refAxisCodes will be marked as 'None'

    e.g. for unique axis codes:

        indices = getAxisCodeMatchIndices(('Hn', 'Nh', 'C'), ('Nh', 'Hn'))

        ->  (1, 0, None)

                i.e axisCodes[0] = 'Hn' which maps to refAxisCodes[indices[0]] = 'Hn'

    for similar repeated axis codes, possibly from matching isotopeCodes:

        getAxisCodeMatchIndices(('Nh', 'H'), ('H', 'H1', 'N'))

        ->  (2, 0)

    """

    _found = OrderedDict()
    _matches = _axisCodeMapIndices(axisCodes, refAxisCodes, checkBoundAtoms=checkBoundAtoms, allMatches=allMatches, exactMatch=exactMatch)
    if allMatches:
        for _match in _matches or ():
            for ii, ind in enumerate(_match):
                if ind is not None and ii < len(refAxisCodes):
                    if axisCodes[ind] in _found:
                        if ii not in _found[axisCodes[ind]]:
                            _found[axisCodes[ind]] += (ii,)
                    else:
                        _found[axisCodes[ind]] = (ii,)
        return tuple(_found.get(axis) or () for axis in axisCodes)

    elif _matches:
        # _matches is a single item
        for ii, ind in enumerate(_matches):
            if ind is not None and ii < len(refAxisCodes):
                _found[axisCodes[ind]] = ii
        return tuple(_found.get(axis) for axis in axisCodes)

    return ()


def axisCodeMatch(axisCode, refAxisCodes):
    """Get refAxisCode that best matches axisCode """
    for ii, indx in enumerate(_axisCodeMapIndices([axisCode], refAxisCodes)):
        if indx == 0:
            # We have a match
            return refAxisCodes[ii]
    else:
        return None


def doAxisCodesMatch(axisCodes, refAxisCodes):
    """Return True if axisCodes match refAxisCodes else False"""
    if len(axisCodes) != len(refAxisCodes):
        return False

    for code1, code2 in zip(axisCodes, refAxisCodes):
        if not _matchSingleAxisCode(code1, code2):
            return False

    return True
