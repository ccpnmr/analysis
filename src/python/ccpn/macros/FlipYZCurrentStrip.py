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
nDim = len(current.strip.axisOrder)
if nDim < 3:
  print('Too few dimensions for XZ flip')

else:

  axisOrder = [current.strip.axisOrder[0], current.strip.axisOrder[2], current.strip.axisOrder[1]]

  if nDim > len(axisOrder):
    axisOrder = axisOrder + list(current.strip.axisOrder[3:])

  spectra = current.strip.spectra
  newDisplay = application.createSpectrumDisplay(spectra[0], axisOrder=axisOrder)
  for spectrum in spectra:
    newDisplay.displaySpectrum(spectrum)