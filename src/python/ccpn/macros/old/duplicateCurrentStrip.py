"""
This macro duplicates the spectrum display from the current strip
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-01-13 17:30:49 +0000 (Thu, January 13, 2022) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
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
    newDisplay = mainWindow.newSpectrumDisplay(spectra[0], axisOrder=axisOrder)
    for spectrum in spectra:
        newDisplay.displaySpectrum(spectrum)
