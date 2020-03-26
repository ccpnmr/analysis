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
__dateModified__ = "$dateModified: 2020-03-26 12:02:35 +0000 (Thu, March 26, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-03-26 11:44:06 +0000 (Thu, March 26, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject
from PyQt5.QtGui import QShowEvent, QHideEvent
from ccpn.ui.gui.guiSettings import BORDERNOFOCUS_COLOUR


class ScrollBarVisibilityWatcher(QObject):
    """
    Class to insert new widget into the corner of scroll areas
    """
    def __init__(self, widget, cornerWidget=None):
        """
        Initialise the widgets for the class
        """
        super().__init__()

        # setup the corner widget
        if not cornerWidget:
            cornerWidget = QtWidgets.QWidget()
            # add a small widget with the top/left borders defined
            cornerWidget.setStyleSheet('border-top: 1px solid %s;'
                                  'border-left: 1px solid %s;'
                                  'background: transparent;' % (BORDERNOFOCUS_COLOUR, BORDERNOFOCUS_COLOUR))

        self._cornerWidget = cornerWidget
        self._widget = widget

        # setup the event filters for the scroll bars
        horizontalScrollBar = self._getHorizontalScrollBar(widget)
        verticalScrollBar = self._getVerticalScrollBar(widget)
        horizontalScrollBar.installEventFilter(self)
        verticalScrollBar.installEventFilter(self)

        self.scrollBarChanged(horizontalScrollBar.isVisible(), verticalScrollBar.isVisible())

    def eventFilter(self, watched, event):
        """Event filter to be attached to the scroll bars
        """
        show = None
        if isinstance(event, QShowEvent):
            show = True
        elif isinstance(event, QHideEvent):
            show = False

        if show is not None:
            self._doScrollBarChange(show, watched)

        return super().eventFilter(watched, event)

    def _doScrollBarChange(self, show, watched):
        """Update the scroll bar corner widget state
        """
        horizontalScrollBar = self._getHorizontalScrollBar(self._widget)
        verticalScrollBar = self._getVerticalScrollBar(self._widget)
        if watched == horizontalScrollBar:
            horizontalVisible = show
            verticalVisible = verticalScrollBar is not None and verticalScrollBar.isVisible()
        elif watched == verticalScrollBar:
            horizontalVisible = horizontalScrollBar is not None and horizontalScrollBar.isVisible()
            verticalVisible = show
        else:
            raise Exception("scroll bar watcher received a object that wasn't watched %s" % repr(watched))
        self.scrollBarChanged(horizontalVisible, verticalVisible)

    @staticmethod
    def _getHorizontalScrollBar(watched):
        return watched.horizontalScrollBar()

    @staticmethod
    def _getVerticalScrollBar(watched):
        return watched.verticalScrollBar()

    def scrollBarChanged(self, horizontalVisible, verticalVisible):
        """Set the corner widget
        """
        if horizontalVisible and verticalVisible:
            self._widget.setCornerWidget(self._cornerWidget)
        else:
            self._widget.setCornerWidget(None)
