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
