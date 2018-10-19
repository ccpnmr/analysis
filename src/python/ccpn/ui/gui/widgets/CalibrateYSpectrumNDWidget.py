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

from ccpn.ui.gui.widgets.CalibrateYSpectrum1DWidget import CalibrateY1DWidgets
from ccpn.core.lib.SpectrumLib import _calibrateYND
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier


class CalibrateYNDWidgets(CalibrateY1DWidgets):
    def __init__(self, parent=None, mainWindow=None, strip=None, **kw):
        super(CalibrateYNDWidgets, self).__init__(parent=parent, mainWindow=mainWindow, strip=strip, **kw)


    def _calibrateSpectra(self, fromPos, toPos):
        if self.mainWindow is not None:
            if self.strip is not None:
                for spectrumView in self.strip.spectrumViews:
                    if spectrumView.isVisible():
                        spectrum = spectrumView.spectrum
                        _calibrateYND(spectrum, fromPos, toPos)

                    spectrumView.buildContours = True

        if self.GLWidget:
            # spawn a redraw of the GL windows
            self.GLWidget._moveAxes((0.0, toPos-fromPos))
            self.GLSignals.emitPaintEvent()
