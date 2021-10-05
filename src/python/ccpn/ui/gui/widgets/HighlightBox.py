"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-10-05 17:38:46 +0100 (Tue, October 05, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-09-29 12:12:09 +0100 (Wed, September 29, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from typing import Union
from PyQt5 import QtGui, QtCore, QtWidgets
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Label import Label


class HighlightBox(Widget):
    """Widget to put a selection box around a span of cells in a grid layout
    """
    SOLID_LINE = 'SolidLine'
    DASH_LINE = 'DashLine'
    DASH_DOT_LINE = 'DashDotLine'
    DASH_DOT_DOT_LINE = 'DashDotDotLine'

    styles = {
        SOLID_LINE       : QtCore.Qt.SolidLine,
        DASH_LINE        : QtCore.Qt.DashLine,
        DASH_DOT_LINE    : QtCore.Qt.DashDotLine,
        DASH_DOT_DOT_LINE: QtCore.Qt.DashDotDotLine,
        }

    def __init__(self, parent=None, style: str = SOLID_LINE, colour: Union[str, QtGui.QColor] = QtCore.Qt.black, lineWidth: int = 2, showBorder=True, **kwds):
        """Initialise the widget
        :param style: Options:
                              'SolidLine';
                               'DashLine';
                               'DashDotLine';
                               'DashDotDotLine'
        """

        super().__init__(parent, **kwds)
        self._parent = parent

        if style not in self.styles:
            raise ValueError(f'HighlightBox.style must be one of {[val for val in self.styles.keys()]}')
        if not isinstance(colour, (str, QtGui.QColor)):
            raise ValueError(f'HighlightBox.colour must be of type str or QtGui.QColor')
        if not (isinstance(lineWidth, int) and lineWidth >= 0):
            raise ValueError(f'HighlightBox.lineWidth must be an int >= 0')
        if not isinstance(showBorder, bool):
            raise ValueError(f'HighlightBox.showBorder must be True/False')

        self.style = style
        self.colour = colour
        self.lineWidth = lineWidth
        self._showBorder = showBorder

        # don't intercept the mouse events
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)

    @property
    def showBorder(self):
        """Get the visible state of the border without hiding the widget
        """
        return self._showBorder

    @showBorder.setter
    def showBorder(self, value):
        self._showBorder = (True if value else False)
        self.update()

    def paintEvent(self, e):
        if self._showBorder:
            qp = QtGui.QPainter()

            # offset ensures that the border widths are uniform for different devicePixelRatios
            _offset = (1 + self.lineWidth) // 2
            rgn = self.rect().adjusted(_offset, _offset, -_offset, -_offset)

            # draw the border
            qp.begin(self)
            if self.style in self.styles:
                style = self.styles[self.style]
                try:
                    pen = QtGui.QPen(self.colour, self.lineWidth, style)
                except:
                    pen = QtGui.QPen(QtGui.QColor(self.colour), self.lineWidth, style)

                qp.setPen(pen)
                qp.drawRect(rgn)

            qp.end()


def main():
    app = QtWidgets.QApplication(sys.argv)
    HighlightBox()
    sys.exit(app.exec_())


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = CcpnDialog(windowTitle='Test HLine', setLayout=True)
    Label(parent=popup, grid=(0, 0), text='Just some text')
    HighlightBox(parent=popup, grid=(0, 0), hPolicy='expanding', vPolicy='expanding', spacing=(0, 0), )
    Label(parent=popup, grid=(2, 0), text='Just some text to separate')
    HighlightBox(parent=popup, grid=(2, 0), hPolicy='expanding', vPolicy='expanding', spacing=(0, 0),
                 colour='#8523e0', style=HighlightBox.DASH_DOT_DOT_LINE)
    popup.show()
    popup.raise_()
    app.start()
