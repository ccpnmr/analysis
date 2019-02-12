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
__version__ = "$Revision: 3.0.b5 $"
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
    def __init__(self, parent=None, mainWindow=None, strip=None, **kwds):
        super().__init__(parent=parent, mainWindow=mainWindow, strip=strip, **kwds)

    def _calibrateSpectra(self, fromPos, toPos):
        if self.mainWindow is not None:
            if self.strip is not None:
                for spectrumView in self.strip.spectrumViews:
                    if spectrumView.isVisible():
                        spectrum = spectrumView.spectrum
                        _calibrateXND(spectrum, fromPos, toPos)
                        self.setOriginalPos(toPos)

                        spectrumView.buildContours = True

        if self.GLWidget:
            # spawn a redraw of the GL windows
            self.GLWidget._moveAxes((toPos-fromPos, 0.0))
            self.GLSignals.emitPaintEvent()
