"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.CalibrateXSpectrum1DWidget import CalibrateX1DWidgets
from ccpn.core.lib.SpectrumLib import _calibrateXND


class CalibrateXNDWidgets(CalibrateX1DWidgets):
    def __init__(self, parent=None, mainWindow=None, strip=None, **kw):
        super(CalibrateXNDWidgets, self).__init__(parent=parent, mainWindow=mainWindow, strip=strip, **kw)

    def _calibrateSpectra(self, fromPos, toPos):
        if self.mainWindow is not None:
            if self.strip is not None:
                for spectrumView in self.strip.spectrumViews:
                    if spectrumView.isVisible():
                        spectrum = spectrumView.spectrum
                        _calibrateXND(spectrum, fromPos, toPos)

                    spectrumView.buildContours = True

        if self.GLWidget:
            # spawn a redraw of the GL windows
            self.GLSignals.emitPaintEvent()
