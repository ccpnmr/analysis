#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-02-28 17:35:34 +0000 (Mon, February 28, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.Colour import hexToRgb


class VLine(Widget):
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

    def __init__(self, parent=None, style=SOLID_LINE, colour=QtCore.Qt.black, width=10, lineWidth=2, divisor=3, **kwds):
        """
        :param style: Options:
                              'SolidLine';
                               'DashLine';
                               'DashDotLine';
                               'DashDotDotLine'
        """

        super().__init__(parent, **kwds)
        self._parent = parent
        self.style = style
        self.colour = colour
        self.height = width
        self.divisor = divisor  #int(height / divisor)
        self.lineWidth = lineWidth

        self.setFixedWidth(width)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawLine(qp, self.style)
        qp.end()

    def drawLine(self, qp, style=None, colour=None):

        geomRect = self.geometry()
        geomWidth = int(geomRect.width() / self.divisor + 0.5)
        lineWidth = geomWidth + self.contentsMargins().right()
        top = geomRect.top()
        bottom = geomRect.bottom()

        if style in self.styles:
            style = self.styles[style]
            try:
                pen = QtGui.QPen(self.colour, self.lineWidth, style)
            except:
                pen = QtGui.QPen(QtGui.QColor(*hexToRgb(self.colour)), self.lineWidth, style)

            qp.setPen(pen)
            qp.drawLine(lineWidth, top, lineWidth, bottom)


# class LabeledVLine(Frame):
#     """A class to make a Frame with a Vline - Label - Vline
#     """
#
#     def __init__(self, parent=None, height=30, text=None, bold=False,
#                  style=VLine.SOLID_LINE, colour=QtCore.Qt.black, lineWidth=2, **kwds):
#         super(LabeledVLine, self).__init__(parent=parent, setLayout=True, showBorder=False, **kwds)
#         self.setFixedWidth(height)
#
#         # first line
#         self._line1 = Frame(parent=self, grid=(0, 0), setLayout=True, showBorder=False, hPolicy='expanding')
#         VLine(self._line1, grid=(0, 0), style=style, colour=colour, lineWidth=lineWidth, height=height, divisor=2)
#         # the label with text
#         self._label = Label(parent=self, grid=(0, 1), text=text, bold=bold, hAlign='centre')
#         # the second line
#         self._line2 = Frame(parent=self, grid=(0, 2), setLayout=True, showBorder=False, hPolicy='expanding')
#         VLine(self._line2, grid=(0, 0), style=style, colour=colour, lineWidth=lineWidth, height=height, divisor=2)
#
#     def setText(self, text):
#         """Set the text of the widget"""
#         self._label.setText(text)


def main():
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from ccpn.ui.gui.widgets.Slider import SliderSpinBox

    app = TestApplication()
    popup = CcpnDialog(windowTitle='Test slider', setLayout=True)
    slider = SliderSpinBox(parent=popup, startVal=0, endVal=100, value=5, grid=(0, 0))
    line = VLine(parent=popup, grid=(0, 1), gridSpan=(3, 1))
    slider2 = SliderSpinBox(parent=popup, startVal=0, endVal=100, value=5, grid=(2, 0))
    popup.show()
    popup.raise_()
    app.start()


if __name__ == '__main__':
    main()
