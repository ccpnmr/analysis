"""
This macro duplicates the spectrum display from the current strip
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
__author__ = ": $rhfogh $"
__date__ = ": 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = ": 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.Logging import getLogger
logger = getLogger()

# check if we have sufficient dimensions for the swap
if current.strip is None:
  logger.warning('duplicateStrip: current.strip is undefined')

else:
  # create a new spectrum display
  axisOrder = current.strip.axisOrder
  spectra = current.strip.spectra
  newDisplay = mainWindow.createSpectrumDisplay(spectra[0], axisOrder=axisOrder)
  for spectrum in spectra:
    newDisplay.displaySpectrum(spectrum)
