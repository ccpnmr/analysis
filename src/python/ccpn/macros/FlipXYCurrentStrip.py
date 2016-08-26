"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - : 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
               "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                 " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = ": rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

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
