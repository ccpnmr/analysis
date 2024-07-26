"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-07-24 18:05:24 +0100 (Wed, July 24, 2024) $"
__version__ = "$Revision: 3.2.5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtWidgets


NULL_RECT = QtCore.QRectF()


class GuiListViewABC(QtWidgets.QGraphicsItem):
    """Base class for gui<Type>ListView objects
    """

    def __init__(self):
        """Initialise instance.
        """
        QtWidgets.QGraphicsItem.__init__(self)

        self.application = self.spectrumView.application
        self.setFlag(QtWidgets.QGraphicsItem.ItemHasNoContents, True)

        # flags to initiate updates to the GL windows
        self.buildSymbols = True
        self.buildLabels = True
        self.buildArrows = True

        self._pixelSize = None
        self._parent.strip.pixelSizeChanged.connect(self._updatePixelSize)

    def boundingRect(self):
        return NULL_RECT

    def paint(self, *args):
        pass

    def setVisible(self, visible):
        super().setVisible(visible)

        self.isDisplayed = visible

        # print(f'    setVisible {self}')
        #
        self.isDisplayed = visible

        # change visibility list for the strip
        self.spectrumView.strip._updateVisibility()

        self._notifyChange()

    # # just use the same behaviour for the minute
    # setDisplayed = setVisible

    def setDisplayed(self, visible):
        # super().setVisible(visible)

        # print(f'    setDisplayed {self}')
        #
        self.isDisplayed = visible

        # change visibility list for the strip
        self.spectrumView.strip._updateVisibility()

        self._notifyChange()

    def _notifyChange(self):
        # repaint all displays - this is called for each spectrumView in the spectrumDisplay
        # all are attached to the same click
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()

    @property
    def pixelSize(self):
        """Return the pixel size for the view in ppm.
        """
        return self._pixelSize

    def _updatePixelSize(self, strip, value: tuple):
        """Update the pixel size from the strip signal.
        """
        self._pixelSize = value
