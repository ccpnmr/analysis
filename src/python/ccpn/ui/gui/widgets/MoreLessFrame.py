"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-06-02 09:52:54 +0100 (Tue, June 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-27 16:32:49 +0000 (Wed, May 27, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui
from functools import partial
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import ActiveLabel, Label


class MoreLessFrame(Frame):
    """
    Widget that contains a button to expand/contract show more/less subframe containing more options
    """

    def __init__(self, parent, mainWindow=None, name=None, showMore=True, setLayout=None, **kwds):
        """Initialise the widget
        """
        super().__init__(parent=parent, setLayout=True, **kwds)
        self._parent = parent
        self.mainWindow = mainWindow
        self._name = name
        self._showMore = showMore
        self._callback = None

        self._minusIcon = Icon('icons/minus')
        self._plusIcon = Icon('icons/plus')

        row = 0
        self.openButton = ActiveLabel(self, mainWindow=self.mainWindow, grid=(row, 0))
        self.openButton.setFixedSize(18, 18)
        self.openButton.setPixmap(self._minusIcon.pixmap(18, 18))
        self.label = Label(self, text=name or '', grid=(row, 1))
        self.label.setFixedHeight(24)

        row += 1
        self.contentsWidget = Frame(self, setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 2))
        self.openButton.setSelectionCallback(self._toggleContents)

        self._showContents(showMore)
        self._lastSize = QtCore.QSize(self.sizeHint())

    def _showContents(self, visible):
        self.contentsWidget.setVisible(visible)
        if visible:
            self.openButton.setPixmap(self._minusIcon.pixmap(18, 18))
            # arbitrary large height
            self.setMaximumHeight(2000)
        else:
            self.openButton.setPixmap(self._plusIcon.pixmap(18, 18))
            self.setMaximumHeight(24)

        if self._callback:
            self._callback(self)

    def setCallback(self, callback):
        """Set a callback to the frame from the parent
        """
        self._callback = callback

    def _toggleContents(self):
        visible = not self.contentsWidget.isVisible()
        self._showContents(visible)

    @property
    def name(self):
        """Set/get the name of the more/less widget
        """
        return self.label.get()

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise TypeError('name {} must be a string'.format(value))

        self._name = value
        self.label.setText(value)

    # def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
    #     self._lastSize = QtCore.QSize(self.sizeHint())
    #     print('>>>RESIZEEVENT', self._lastSize)
    #     super(MoreLessFrame, self).resizeEvent(a0)
