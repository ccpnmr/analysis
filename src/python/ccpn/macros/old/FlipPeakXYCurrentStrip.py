"""
Flip the axes of the peak list.
May be necessary due to incorrect importing of a Sparky Spectrum
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2024-11-21 18:22:24 +0100 (Thu, November 21, 2024) $"
__version__ = "$Revision: 3.2.10.GWV $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

"""This macro flips the peak list in the current strip with the X and Y axes swapped
"""
from ccpn.core.lib.ContextManagers import notificationSuspend

# determine the number of dimensions in the current strip.
nDim = len(current.strip.axisOrder)

# check if we have sufficient dimensions for the swap
if nDim < 2:
    print('Too few dimensions for XY flip of peakList')

else:
    # create a list with X and Y axes swapped.

    with notificationSuspend():
        try:
            for spec in current.strip.spectra:
                for peak in spec.peaks:

                    newPosition = [peak.position[1], peak.position[0]]

                    if nDim > 2:
                        newPosition = newPosition.extend(peak.position[2:])

                    peak.position = newPosition
        except:
            getLogger().warning('Error flipping peak list axes')

