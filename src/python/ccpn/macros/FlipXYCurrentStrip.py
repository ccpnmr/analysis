"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification
#=========================================================================================
__author__ = ": rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:37 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

"""This macro creates a new spectrum display from the current strip with the X and Y axes swapped"""

# determine the number of dimensions in the current strip.
nDim = len(current.strip.axisOrder)

# check if we have sufficient dimensions for the swap
if nDim < 2:
  print('Too few dimensions for XY flip')

else:
  # create a list with X and Y axes swapped.
  axisOrder = [current.strip.axisOrder[1], current.strip.axisOrder[0]]

  # add any remaining axes of the strip to the list
  if nDim > len(axisOrder):
    axisOrder.extend(current.strip.axisOrder[2:])

  # create a new spectrum display with the new axis order
  spectra = current.strip.spectra
  newDisplay = mainWindow.createSpectrumDisplay(spectra[0], axisOrder=axisOrder)
  for spectrum in spectra:
    newDisplay.displaySpectrum(spectrum)
