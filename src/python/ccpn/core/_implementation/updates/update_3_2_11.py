"""
update 3.2.11 to 3.3.0 routines
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

from ccpn.core.lib.CcpNmrProperties import CcpNmrBoolProperty

#=========================================================================================
# Start of code
#=========================================================================================
#
# from ccpn.core.lib.ContextManagers import undoStack
from ccpn.core.lib.forceAttribute import forceSetattr

OLD_NMRCHAINCODE = "@-"

def _updateOldDefaultNmrChain(nmrChain):
    """Update the old default nmrChain name to the new default one
    Set the default chain serial to 0
    """
    # NB all updates executed with inactivity
    from ccpn.core.NmrChain import DEFAULT_NMRCHAINCODE

    _serials = [nc.serial for nc in nmrChain.project.nmrChains]
    if 0 not in _serials:
        nmrChain._resetSerial(0)

    if nmrChain.name == OLD_NMRCHAINCODE:
        nmrChain._rename(DEFAULT_NMRCHAINCODE)
