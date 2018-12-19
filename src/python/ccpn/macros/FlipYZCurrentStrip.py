"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:38 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

"""This macro creates a new spectrum display from the current strip with the Y and Z axes swapped"""

# determine the number of dimensions in the current strip.
nDim = len(current.strip.axisOrder)

# check if we have sufficient dimensions for the swap
if nDim < 3:
    print('Too few dimensions for YZ flip')

else:
    # create a list with X and Z axes swapped.
    axisOrder = [current.strip.axisOrder[0], current.strip.axisOrder[2], current.strip.axisOrder[1]]

    # add any remaining axes of the strip to the list
    if nDim > len(axisOrder):
        axisOrder.extend(current.strip.axisOrder[3:])

    # create a new spectrum display with the new axis order
    spectra = current.strip.spectra
    newDisplay = mainWindow.createSpectrumDisplay(spectra[0], axisOrder=axisOrder)
    for spectrum in spectra:
        newDisplay.displaySpectrum(spectrum)
