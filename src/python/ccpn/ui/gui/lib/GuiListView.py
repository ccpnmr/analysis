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
__dateModified__ = "$dateModified: 2018-12-20 15:53:11 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.b5 $"
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

    def boundingRect(self):
        return NULL_RECT

    def paint(self, *args):
        pass

    def setVisible(self, visible):
        super().setVisible(visible)

        # change visibility list for the strip
        self.spectrumView.strip._updateVisibility()

        # repaint all displays - this is called for each spectrumView in the spectrumDisplay
        # all are attached to the same click
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()
