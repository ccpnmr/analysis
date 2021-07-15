"""
This module defines the code for creating the credits
"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2018"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: geertenv $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

authors = ('Ed Brooksbank', 'Joanna Fox', 'Victoria A Higman', 'Luca Mureddu', 'Eliza Płoskoń',
           'Timothy J Ragan', 'Gary S Thompson', 'Brian O Smith', 'Geerten W Vuister')


def _strList(inlist: list, maxlen: int = 80) -> list:

    outstr = ''
    # skip = False  # print commas and ampersand
    lencount = maxlen

    nameList = sorted(inlist, key=lambda name: name.split()[-1])

    outList = []

    for cName in nameList[:-1]:
        skip = False
        if len(outstr + cName) > lencount and cName not in nameList[-2:]:
            outstr += cName + ', '
            outList.append(outstr)
            lencount += maxlen
            skip = True
            outstr = ''
        elif cName not in nameList[-2:]:
            outstr += cName + ', '
        else:
            outstr += cName

    if len(nameList) == 1:
        outstr = nameList[0]
    else:
        outstr = outstr + ' & ' + nameList[-1]

    if outstr:
        outList.append(outstr)

    return outList


def printCreditsText(fp, programName, version):
    """Initial text to terminal """
    from ccpn.framework.PathsAndUrls import ccpnLicenceUrl

    lines = []  # ejb
    lines.append("%s, version: %s" % (programName, version))
    lines.append("")
    # lines.append("%s" % __copyright__[0:__copyright__.index('-')] + '- 2016')
    lines.append("%s" % __copyright__)
    lines.append("")
    lines.append("CCPN licence. See %s. Not to be distributed without prior consent!" % ccpnLicenceUrl)
    lines.append("")

    try:
        prefix = "Active Developers:   "
        if isinstance(authors, str):
            lines.append("%s%s" % (prefix, authors))
        elif isinstance(authors, (list, tuple)):
            authorList = _strList(authors, maxlen=60)
            lines.append("%s%s" % (prefix, authorList[0]))
            for crLine in authorList[1:]:
                lines.append("%s%s" % (' ' * len(prefix), crLine))
    except:
        pass

    lines.append("")
    try:
        if isinstance(__reference__, str):
            lines.append("Please cite:  %s" % __reference__)
        else:
            if isinstance(__reference__, tuple):
                lines.append("Please cite:  %s" % __reference__[0])
                for refLine in __reference__[1:]:
                    lines.append("              %s" % refLine)
    except:
        pass

    lines.append("")
    lines.append("DISCLAIMER:   This program is offered 'as-is'. Under no circumstances will the authors, CCPN,")
    lines.append("              the Department of Molecular and Cell Biology, or the University of Leicester be")
    lines.append("              liable of any damage, loss of data, loss of revenue or any other undesired")
    lines.append("              consequences originating from the usage of this software.")

    # print with aligning '|'s
    maxlen = max(map(len, lines))
    fp.write('%s\n' % ('=' * (maxlen + 8)))
    for line in lines:
        fp.write('|   %s ' % line + ' ' * (maxlen - len(line)) + '  |\n')
    fp.write('%s\n' % ('=' * (maxlen + 8)))