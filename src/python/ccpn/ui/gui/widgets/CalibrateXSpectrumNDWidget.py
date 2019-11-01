"""
Module Documentation here
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2018-12-20 15:53:21 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.CalibrateXSpectrum1DWidget import CalibrateX1DWidgets
from ccpn.core.lib.SpectrumLib import _calibrateXND


class CalibrateXNDWidgets(CalibrateX1DWidgets):

    CLOSELABEL = 'Close'

    def _calibrateSpectra(self, spectra, fromPos, toPos):

        for specView, spectrum in spectra:
            _calibrateXND(spectrum, self.strip, fromPos, toPos)

            if specView and not specView.isDeleted:
                specView.buildContours = True

        self.setOriginalPos(toPos)
        if self.mainWindow and self.strip and self.GLWidget:
            # spawn a redraw of the GL windows
            self.GLWidget._moveAxes((toPos - fromPos, 0.0))
            self.GLSignals.emitPaintEvent()
