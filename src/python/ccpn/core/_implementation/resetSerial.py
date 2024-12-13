"""
resetSerial function
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               )
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y"
                )
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-12-13 12:42:05 +0000 (Fri, December 13, 2024) $"
__version__ = "$Revision: 3.3.0.develop $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2021-01-13 10:28:41 +0000 (Wed, Jan 13, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.Application import getApplication, getProject


def resetSerial(apiObject, newSerial):
    """ADVANCED Reset serial of object to newSerial, resetting parent link
    and the nextSerial of the parent.

    Raises ValueError for objects that do not have a serial
    (or, more precisely, where the _wrappedData does not have a serial).
    """

    # NB, needed both from V2 NefIo and V3

    if not hasattr(apiObject, 'serial'):
        raise ValueError("Cannot reset serial, %s does not have a 'serial' attribute"
                         % apiObject)
    downlink = apiObject.__class__._metaclass.parentRole.otherRole.name

    parentDict = apiObject.parent.__dict__
    downdict = parentDict[downlink]
    oldSerial = apiObject.serial
    serialDict = parentDict['_serialDict']

    if newSerial == oldSerial:
        return

    elif newSerial in downdict:
        # newSerial is in use;
        # get the identifier of the v3 object to report the error

        project = getProject()
        v3obj = None
        if project and apiObject in project._data2Obj:
            v3obj = project._data2Obj[apiObject]
        raise ValueError("Cannot reset serial to %s - value already in use (%s)" % (newSerial, v3obj or apiObject))

    else:
        maxSerial = serialDict[downlink]
        apiObject.__dict__['serial'] = newSerial
        downdict[newSerial] = apiObject
        del downdict[oldSerial]
        if newSerial > maxSerial:
            serialDict[downlink] = newSerial
        elif oldSerial == maxSerial:
            serialDict[downlink] = max(downdict)
