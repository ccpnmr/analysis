"""
forceAttributes routines to bypass __egtitem__ and __setitem__
Use with extreme care!
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
__dateModified__ = "$dateModified: 2024-12-05 17:31:17 +0000 (Thu, December 05, 2024) $"
__version__ = "$Revision: 3.3.0.develop $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: geertenv $"
__date__ = "$Date: 2024-12-04 9:42:30 +0100 (Wed, December 4, 2024) $"
#=========================================================================================
# Start of code
#=========================================================================================
#


def forceSetattr(obj, attributeName: str, value):
    """Force setting of attributeName of obj to value;
    bypasses __setitem__
    :param obj: the object to set the attribute to
    :param attributeName: the attribute name to get
    :param value: the value to set
    """
    obj.__dict__[attributeName] = value


def forceGetattr(obj, attributeName: str):
    """Force getting of attributeName from obj;
    bypasses __getitem__
    :param obj: the object to get the attribute from
    :param attributeName: the attribute name to get
    :raises AttributeError: if attributeName is not found
    """
    if attributeName not in obj.__dict__:
        raise AttributeError(f'{obj} does not have attribute {attributeName!r}')

    value = obj.__dict__[attributeName]
    return value


