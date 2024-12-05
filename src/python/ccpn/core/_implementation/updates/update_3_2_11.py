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
#=========================================================================================
# Start of code
#=========================================================================================
#
from ccpn.core.lib.ContextManagers import undoBlock

def _updateNmrChain_to_3_3_0(nmrChain):
    """Update the old default nmrChain name
    """
    from ccpn.core.NmrChain import DEFAULT_NMRCHAINCODE
    if nmrChain.name == "@-":
        with undoBlock():
            nmrChain._rename(DEFAULT_NMRCHAINCODE)
            for _nr in nmrChain.nmrResidues:
                _nr.rename()
