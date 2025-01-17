"""
Flip the axes of the peak list.
May be necessary due to incorrect importing of a Sparky Spectrum
"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:38 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

"""This macro flips the peak list in the current strip with the X and Y axes swapped"""

# determine the number of dimensions in the current strip.
nDim = len(current.strip.axisOrder)

# check if we have sufficient dimensions for the swap
if nDim < 2:
    print('Too few dimensions for XY flip of peakList')

else:
    # create a list with X and Y axes swapped.

    project.suspendNotification()
    try:
        for spec in current.strip.spectra:
            for peak in spec.peaks:

                newPosition = [peak.position[1], peak.position[0]]

                if nDim > 2:
                    newPosition = newPosition.extend(peak.position[2:])

                peak.position = newPosition
    except:
        getLogger().warning('Error flipping peak list axes')

    finally:
        project.resumeNotification()
