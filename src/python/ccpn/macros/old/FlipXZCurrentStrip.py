"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Geerten Vuister $"
__dateModified__ = "$dateModified: 2022-01-11 12:34:42 +0000 (Tue, January 11, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

"""This macro creates a new spectrum display from the current strip with the X and Z axes swapped"""

# determine the number of dimensions in the current strip.
nDim = len(current.strip.axisOrder)

# check if we have sufficient dimensions for the swap
if nDim < 3:
    print('Too few dimensions for XZ flip')
else:
    # create a list with X and Z axes swapped.
    axisOrder = [current.strip.axisOrder[2], current.strip.axisOrder[1], current.strip.axisOrder[0]]

    # add any remaining axes of the strip to the list
    if nDim > len(axisOrder):
        axisOrder.extend(current.strip.axisOrder[3:])

    # create a new spectrum display with the new axis order
    spectra = current.strip.spectra
    newDisplay = ui.mainWindow.newSpectrumDisplay(spectra[0], axisOrder=axisOrder)
    for spectrum in spectra[1:]:
        newDisplay.displaySpectrum(spectrum)
