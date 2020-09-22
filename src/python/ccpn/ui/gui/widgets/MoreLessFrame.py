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
__dateModified__ = "$dateModified: 2020-09-22 09:33:24 +0100 (Tue, September 22, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-27 16:32:49 +0000 (Wed, May 27, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import ActiveLabel, Label
from ccpn.ui.gui.guiSettings import getColours, BORDERNOFOCUS
from ccpn.ui.gui.widgets.Font import getFontHeight


class MoreLessFrame(Frame):
    """
    Widget that contains a button to expand/contract show more/less subframe containing more options
    """
    DEFAULTMARGINS = (0, 2, 0, 0)  # l, t, r, b

    def __init__(self, parent, mainWindow=None, name=None, showMore=True, setLayout=None,
                 showBorder=True, borderColour=None, _frameMargins=DEFAULTMARGINS, **kwds):
        """Initialise the widget
        """
        super().__init__(parent=parent, setLayout=True, **kwds)
        self._parent = parent
        self.mainWindow = mainWindow
        self._name = name
        self._showMore = showMore
        self._callback = None
        self._showBorder = showBorder
        self._borderColour = borderColour or QtGui.QColor(getColours()[BORDERNOFOCUS])

        self._minusIcon = Icon('icons/minus')
        self._plusIcon = Icon('icons/plus')

        self.PIXMAPWIDTH = getFontHeight()

        row = 0
        self._openButton = ActiveLabel(self, mainWindow=self.mainWindow, grid=(row, 0))
        self._openButton.setFixedSize(self.PIXMAPWIDTH, self.PIXMAPWIDTH)
        self._openButton.setPixmap(self._minusIcon.pixmap(self.PIXMAPWIDTH, self.PIXMAPWIDTH))
        self._label = Label(self, text=name or '', grid=(row, 1))
        self._labelHeight = self._label.sizeHint().height()
        self._label.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        # self._label.setFixedHeight(self._labelHeight)

        row += 1
        self._contentsFrame = Frame(self, setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 2))
        self._openButton.setSelectionCallback(self._toggleContents)

        self.setContentsMargins(*_frameMargins)
        self._showContents(showMore)
        self._lastSize = QtCore.QSize(self.sizeHint())

    def _showContents(self, visible):
        """Toggle visibility of the contents widget
        """
        self._contentsFrame.setVisible(visible)
        if visible:
            self._openButton.setPixmap(self._minusIcon.pixmap(self.PIXMAPWIDTH, self.PIXMAPWIDTH))
            # arbitrary large height
            self.setMaximumHeight(2000)
        else:
            self._openButton.setPixmap(self._plusIcon.pixmap(self.PIXMAPWIDTH, self.PIXMAPWIDTH))
            self.setMaximumHeight(self.sizeHint().height())

        if self._callback:
            self._callback(self)

    def setCallback(self, callback):
        """Set a callback to the frame from the parent
        """
        self._callback = callback

    def _toggleContents(self):
        """Toggle visibility of the contents
        """
        visible = not self._contentsFrame.isVisible()
        self._showContents(visible)

    @property
    def name(self):
        """Set/get the name of the widget
        """
        return self._label.get()

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise TypeError('name {} must be a string'.format(value))

        self._name = value
        self._label.setText(value)

    @property
    def contentsFrame(self):
        """Get the contents frame
        """
        return self._contentsFrame

    def paintEvent(self, ev):
        """Paint the top border
        """
        if not self._showBorder:
            return

        # create a painter over the widget - shrink by 1 pixel to draw correctly
        p = QtGui.QPainter(self)
        rgn = self.rect()
        rgn = QtCore.QRect(rgn.x(), rgn.y(), rgn.width() - 1, rgn.height() - 1)

        # get the size of the box to draw in and define the point list
        _size = self._label.sizeHint()
        h, w = _size.height(), _size.width() + self._openButton.sizeHint().width()
        offset = w
        points = [QtCore.QPoint(0, 1),
                  QtCore.QPoint(offset + 2, 1),
                  QtCore.QPoint(offset + 2, 1),
                  QtCore.QPoint(offset + h, h - 1),
                  QtCore.QPoint(offset + h + 1, h - 1),
                  QtCore.QPoint(rgn.width() + 1, h - 1), ]

        # draw the border
        p.setPen(QtGui.QPen(self._borderColour, 1))
        p.drawLines(*points)
        p.end()
