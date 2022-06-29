
#=========================================================================================
# General CCPN Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ =   ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ =   ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")

#=========================================================================================
# Macro Created by: Vicky Higman
#=========================================================================================
__author__ = "$Author: Ccpn $"
__date__ = "$Date: 2021-05-20 12:34:46 +0100 (Thu, May 20, 2021) $"
__version__ = "$Revision: 3.1.0 $"
__Title__ = "remove Unused Nmr Atoms"
__Category__ = "Assignment,"
__tags__ = ("NmrAtoms", )
__Description__ = """ This macro will remove all unused NmrAtoms from your project, i.e."""
"""all NmrAtoms which are not used in any peak assignments."""

#=========================================================================================
# Start of code
#=========================================================================================

for nc in project.nmrChains:
    for nr in list(nc.nmrResidues):
        for na in list(nr.nmrAtoms):
            if not na.assignedPeaks:
                na.delete()
# If you want to remove unused NmrResidues at the same time include this code
# as well (remove the # at the start of the line):
#        if not nr.nmrAtoms:
#            nr.delete()



# If you wanted a macro to remove the NmrAtoms in a specific NmrChain,
# use this code instead, making sure to enter the correct NmrChain PID in the
# first line.
#
# nc = get('NC:@-')
# for nr in nc.nmrResidues:
#     for na in list(nr.nmrAtoms):
#         if not na.assignedPeaks:
#             na.delete()



