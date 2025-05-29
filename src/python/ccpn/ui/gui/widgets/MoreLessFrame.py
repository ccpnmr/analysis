"""
MoreLessFrame

A custom QFrame widget that can expand and contract to show/hide
additional options, typically used in user interfaces to manage
screen real estate.
"""
from __future__ import annotations


#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
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
__dateModified__ = "$dateModified: 2025-05-29 11:38:47 +0100 (Thu, May 29, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-05-27 16:32:49 +0000 (Wed, May 27, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.ui.gui.widgets.Frame import Frame, ScrollableFrame
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Label import ActiveLabel
from ccpn.ui.gui.widgets.Font import getFontHeight
from typing import Any, Callable


class MoreLessFrame(Frame):
    """
    A widget that contains a button to expand/contract a subframe, showing or
    hiding more options or content within the UI.

    This frame presents a label with an associated expand/collapse icon.
    Clicking the label or icon toggles the visibility of a `contentsFrame`
    which can be populated with additional widgets.
    """
    DEFAULTMARGINS: tuple[int, int, int, int] = (0, 2, 0, 0)  # l, t, r, b
    _contentsFrame: ScrollableFrame | Frame
    scrollArea: QtWidgets.QScrollArea | None

    def __init__(self, parent: QtWidgets.QWidget, name: str | None = None, showMore: bool = True,
                 scrollable: bool = False, closable: bool = False,
                 showBorder: bool = True, borderColour: QtGui.QColor | None = None,
                 frameMargins: tuple[int, int, int, int] = DEFAULTMARGINS, **kwds: Any):
        """Initialise the widget.

        :param parent: The parent widget of this frame.
        :type parent: PyQt5.QtWidgets.QWidget
        :param name: The text label to display on the frame's header.
        :type name: str | None
        :param showMore: If True, the contents-frame is initially visible (expanded).
                         If False, it's initially hidden (collapsed).
        :type showMore: bool
        :param scrollable: If True, the contents-frame will be a ScrollableFrame,
                           providing scrollbars if content exceeds visible area.
        :type scrollable: bool
        :param closable: If True, a close button will be displayed next to the label.
        :type closable: bool
        :param showBorder: If True, a custom border is drawn around the frame's header.
        :type showBorder: bool
        :param borderColour: The colour for the custom border. If None, uses palette's dark colour.
        :type borderColour: QtGui.QColor | None
        :param frameMargins: Margins for the frame's layout (left, top, right, bottom).
        :type frameMargins: tuple[int, int, int, int]
        :param kwds: Additional keyword arguments passed to the base Frame constructor.
        :type kwds: Any
        """
        # Pop 'setLayout' from kwds if present, as it's handled internally.
        kwds.pop('setLayout', None)
        super().__init__(parent=parent, setLayout=True, **kwds)

        self._name: str | None = name
        self._showMore: bool = showMore
        self._callback: Callable[[MoreLessFrame], None] | None = None
        self._showBorder: bool = showBorder
        self._borderColour: QtGui.QColor | None = borderColour
        self._closable: bool = closable

        # Icons for expand/collapse and close actions
        self._minusIcon: Icon = Icon('icons/minus-large')
        self._plusIcon: Icon = Icon('icons/plus-large')
        self._closeIcon: Icon = Icon('icons/reset-2')  # close-icon, to the right of text

        # Determine the width for the pix-maps based on current font height
        self.PIXMAPWIDTH: int = getFontHeight()

        # Setup child widgets and their layout
        self._setWidgets(frameMargins, kwds, name, scrollable)
        # Set initial visibility of the contents-frame
        self._showContents(showMore)
        # Store the initial size hint for potential future use (though not currently used)
        self._lastSize: QtCore.QSize = QtCore.QSize(self.sizeHint())

    def _setWidgets(self, _frameMargins: tuple[int, int, int, int], kwds: Any, name: str | None,
                    scrollable: bool):
        """Internal method to create and arrange the header widgets and contents frame.

        :param _frameMargins: Margins for the frame's layout. (Currently unused internally).
        :type _frameMargins: tuple[int, int, int, int]
        :param kwds: Keyword arguments, specifically checked for 'bold' status of the label.
        :type kwds: Any
        :param name: The text to be displayed on the header label.
        :type name: Optional[str]
        :param scrollable: If True, the contents-frame will be a ScrollableFrame.
        :type scrollable: bool
        """
        # what was I going to use frame-margins for :| - Comment from original code
        row: int = 0
        # Button for toggling expand/collapse state
        self._openButton: ActiveLabel = ActiveLabel(self, grid=(row, 0))
        self._openButton.setFixedSize(self.PIXMAPWIDTH + 3, self.PIXMAPWIDTH + 3)
        self._openButton.setPixmap(self._minusIcon.pixmap(self.PIXMAPWIDTH, self.PIXMAPWIDTH))

        # Text label for the frame's header
        bold: bool = kwds.get('bold', False)
        self._label: ActiveLabel = ActiveLabel(self, text=name or '', grid=(row, 1), bold=bold)
        # Fix label to the size of its text, allowing it to expand horizontally if needed
        self._label.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self._label.setMinimumWidth(50)

        # Optional close button
        if self._closable:
            self._closeButton: ActiveLabel = ActiveLabel(self, grid=(row, 2))
            self._closeButton.setFixedSize(self.PIXMAPWIDTH, self.PIXMAPWIDTH)
            self._closeButton.setPixmap(self._closeIcon.pixmap(self.PIXMAPWIDTH - 5, self.PIXMAPWIDTH - 5))
            # Connect the close button's clicked signal to the frame's close method
            self._closeButton.sigClicked.connect(self.close)  # noqa: pycharm can't see qt

        row += 1
        # Create the contents frame, either scrollable or standard
        if scrollable:
            # Add a frame with scroll-bars for its content
            self._contentsFrame = ScrollableFrame(self, setLayout=True, grid=(row, 0), gridSpan=(1, 4))
            self.scrollArea = self._contentsFrame.scrollArea
        else:
            # Add a standard frame for its content
            self._contentsFrame = Frame(self, setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 4))
            self.scrollArea = None

        # Connect click signals of the open button and label to the toggle method
        self._openButton.setSelectionCallback(self._toggleContents)
        self._label.setSelectionCallback(self._toggleContents)

    def _showContents(self, visible: bool):
        """Toggle visibility of the contents-widget and update the expand/collapse icon.
        Also adjusts the frame's maximum height to collapse/expand.

        :param visible: If True, the contents-frame becomes visible (expanded).
                        If False, it becomes hidden (collapsed).
        :type visible: bool
        """
        self._contentsFrame.setVisible(visible)
        if visible:
            self._openButton.setPixmap(self._minusIcon.pixmap(self.PIXMAPWIDTH, self.PIXMAPWIDTH))
            # Set the maximum height to a large arbitrary value to allow expansion
            self.setMaximumHeight(2000)
        else:
            self._openButton.setPixmap(self._plusIcon.pixmap(self.PIXMAPWIDTH, self.PIXMAPWIDTH))
            # Collapse the contents by setting maximum height to the current size-hint
            self.setMaximumHeight(self.sizeHint().height())

        # Call the external callback if set
        if self._callback:
            self._callback(self)

    def setCallback(self, callback: Callable[[MoreLessFrame], None]):
        """Set a callback function to be executed when the frame's contents visibility changes.

        :param callback: A callable that accepts one argument: the MoreLessFrame instance itself.
        :type callback: Callable[[MoreLessFrame], None]
        """
        self._callback = callback

    def _toggleContents(self):
        """Toggle visibility of the contents-frame.
        This method is connected to the click signals of the open button and label.
        """
        visible: bool = not self._contentsFrame.isVisible()
        self._showContents(visible)

    @property
    def contentsVisible(self) -> bool:
        """Return True if the contents-frame is currently visible.

        :returns: True if visible, False otherwise.
        :rtype: bool
        """
        return self._contentsFrame.isVisible()

    def setContentsVisible(self, state: bool):
        """Open/Close the frame by setting the visibility of its contents-frame.

        :param state: True to make contents visible (open), False to make them hidden (close).
        :type state: bool
        """
        self._showContents(state)

    @property
    def name(self) -> str | None:
        """Get the text name of the widget's header label.

        :returns: The text displayed on the header label.
        :rtype: Optional[str]
        """
        return self._label.get()

    @name.setter
    def name(self, value: str):
        """Set the text name of the widget's header label.

        :param value: The new text string for the header label.
        :type value: str
        :raises TypeError: If the provided value is not a string.
        """
        if not isinstance(value, str):
            raise TypeError(f'name {value} must be a string')
        self._name = value
        self._label.setText(value)

    @property
    def contentsFrame(self) -> Frame:
        """Get the internal contents frame where additional widgets should be added.

        :returns: The Frame (or ScrollableFrame) instance containing the toggleable content.
        :rtype: ccpn.ui.gui.widgets.Frame.Frame
        """
        return self._contentsFrame

    def paintEvent(self, ev: QtGui.QPaintEvent):
        """Paint the custom border around the header part of the frame.

        Qt automatically calls this method when the widget needs to be repainted.

        :param ev: The paint event object.
        :type ev: PyQt5.QtGui.QPaintEvent
        """
        if not self._showBorder:
            return

        p: QtGui.QPainter = QtGui.QPainter(self)
        # Adjust rectangle to draw correctly within widget bounds (shrink by 1 pixel)
        rgn: QtCore.QRect = self.rect().adjusted(0, 0, -1, -1)

        # Calculate dimensions for the header elements to determine border offset
        _size: QtCore.QSize = self._label.sizeHint()
        h: int = _size.height()
        w: int = (_size.width() +
                  self._openButton.sizeHint().width() +
                  (self._closeButton.sizeHint().width() if self._closable else 0))
        offset: int = w

        # offset so that the diagonals look correct for displays with devicePixelRatio > 1
        uOffset = QtCore.QPointF(0.75, 0.75)
        lOffset = QtCore.QPointF(0.25, 0.25)
        if h > 40:
            # if the height is greater than 40, then add a vertical section to the boundary;
            # otherwise, there can be an enormous diagonal
            tt = 15
            bb = h - tt + 3
            # Define points for the main border-lines
            points0: list[QtCore.QPointF] = [
                QtCore.QPointF(0, 1),  # Start top-left
                QtCore.QPointF(offset + 2, 1),  # To right of label (top line segment 1)
                QtCore.QPointF(offset + tt, tt - 1),  # Vertical between diagonals
                QtCore.QPointF(offset + tt, bb - 1),
                QtCore.QPointF(offset + 2 * tt - 3, h - 1),  # Extend to right edge (bottom line segment 1)
                QtCore.QPointF(rgn.width() + 1, h - 1),
                ]
            # Define points for diagonal lines
            points1: list[QtCore.QPointF] = [
                QtCore.QPointF(offset + 2, 1) + uOffset,  # Diagonal from top-right of label
                QtCore.QPointF(offset + tt, tt - 1) - lOffset,
                QtCore.QPointF(offset + tt, bb - 1) + uOffset,  # Diagonal to bottom-right of label
                QtCore.QPointF(offset + 2 * tt - 3, h - 1) - lOffset,
                ]
        else:
            # Define points for the main border-lines
            points0: list[QtCore.QPointF] = [
                QtCore.QPointF(0, 1),  # Start top-left
                QtCore.QPointF(offset + 2, 1),  # To right of label (top line segment 1)
                QtCore.QPointF(offset + h, h - 1),  # Extend to right edge (bottom line segment 1)
                QtCore.QPointF(rgn.width() + 1, h - 1),
                ]
            # Define points for diagonal lines
            points1: list[QtCore.QPointF] = [
                QtCore.QPointF(offset + 2, 1) + uOffset,
                QtCore.QPointF(offset + h, h - 1) - lOffset,
                ]

        # Set pen color for drawing the lines
        # Use user-defined colour or default to palette's dark color for theme consistency
        pen_color: QtGui.QColor = self._borderColour or self.palette().dark().color()
        p.setPen(QtGui.QPen(pen_color, 1.25))
        # Add a little smoothing for drawing diagonals
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)
        p.drawLines(*points1)  # Draw secondary lines
        p.setPen(QtGui.QPen(pen_color, 1))
        p.setRenderHint(QtGui.QPainter.Antialiasing, False)
        p.drawLines(*points0)  # Draw main border-lines
        p.end()

    def closeEvent(self, event: QtGui.QCloseEvent):
        """Clean-up resources and handle widget closing.

        Qt calls this method when the widget is about to be closed.

        :param event: The close event object.
        :type event: QtGui.QCloseEvent
        """
        from ccpn.ui.gui.lib.WidgetClosingLib import CloseHandler

        # Use a context manager for safe widget closing
        with CloseHandler(self):
            super().closeEvent(event)
