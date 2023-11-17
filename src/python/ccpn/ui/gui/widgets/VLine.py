#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2023-11-17 17:43:50 +0000 (Fri, November 17, 2023) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-04-07 10:28:42 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtCore
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Label import VerticalLabel
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
        self.width = width
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
        geomWidth = geomRect.width() // self.divisor
        lineWidth = geomWidth + self.contentsMargins().left()
        top = 0
        bottom = geomRect.height()

        if style in self.styles:
            style = self.styles[style]
            try:
                pen = QtGui.QPen(self.colour, self.lineWidth, style)
            except:
                pen = QtGui.QPen(QtGui.QColor(*hexToRgb(self.colour)), self.lineWidth, style)

            qp.setPen(pen)
            qp.drawLine(lineWidth, top, lineWidth, bottom)


class LabeledVLine(Frame):
    """A class to make a Frame with a VLine - Label - VLine
    """

    def __init__(self, parent=None, width=30, text=None, bold=False, sides='both',
                 style=VLine.SOLID_LINE, colour=QtCore.Qt.black, lineWidth=2,
                 **kwds):
        """
        Draw a horizontal line and a label
        :param parent:
        :param width:
        :param text:
        :param bold:
        :param sides: either of 'both', 'top', 'bottom'
        :param style:
        :param colour:
        :param lineWidth:
        :param kwds:
        """
        if sides not in ['top', 'bottom', 'both']:
            raise RuntimeError('sides not defined correctly')
        self._sides = sides

        super().__init__(parent=parent, setLayout=True, showBorder=False, **kwds)
        width = width if width is not None else 30
        self.setFixedWidth(width)

        # the label with text
        self._line1 = VLine(parent=self, grid=(2, 0), style=style, colour=colour, lineWidth=lineWidth, width=width, divisor=2, vPolicy='expanding')
        self._label = VerticalLabel(parent=self, grid=(1, 0), text=text, bold=bold, orientation='vertical', vPolicy='fixed')
        self._line2 = VLine(parent=self, grid=(0, 0), style=style, colour=colour, lineWidth=lineWidth, width=width, divisor=2, vPolicy='expanding')

        self._updateLines()

    @property
    def sides(self):
        return self._sides

    @sides.setter
    def sides(self, value):
        if value not in ['top', 'bottom', 'both']:
            raise RuntimeError('sides not defined correctly')
        self._sides = value

        self._updateLines()

    def _updateLines(self):
        if self._sides == 'bottom':
            self._line1.show()
            self._line2.hide()
        elif self._sides == 'top':
            self._line1.hide()
            self._line2.show()
        else:
            self._line1.show()
            self._line2.show()
        if not (txt := bool(self._label.get())):
            if self._sides == 'bottom':
                self._line2.hide()
            else:
                self._line1.hide()

        self._label.setVisible(txt)

    def setText(self, text):
        """Set the text of the widget"""
        self._label.setText(text)
        self._updateLines()

    def _fixToSizeHint(self):
        size = self.sizeHint()
        val = size.width()

        self._line1.setFixedWidth(val // 2)
        self._line2.setFixedWidth(val // 2)
        self.setFixedWidth(val)


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
