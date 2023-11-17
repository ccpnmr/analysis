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

import sys
from PyQt5 import QtGui, QtCore, QtWidgets
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.Colour import hexToRgb


class HLine(Widget):
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

    def __init__(self, parent=None, style=SOLID_LINE, colour=QtCore.Qt.black, height=10, lineWidth=2, divisor=3, **kwds):
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
        self.height = height
        self.divisor = divisor  #int(height / divisor)
        self.lineWidth = lineWidth

        # self.setMaximumHeight(10)
        self.setFixedHeight(height)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawLine(qp, self.style)
        qp.end()

    def drawLine(self, qp, style=None, colour=None):

        geomRect = self.geometry()
        geomHeight = geomRect.height() // self.divisor
        lineHeight = geomHeight + self.contentsMargins().top()
        left = 0
        right = geomRect.width()

        if style in self.styles:
            style = self.styles[style]
            try:
                pen = QtGui.QPen(self.colour, self.lineWidth, style)
            except:
                pen = QtGui.QPen(QtGui.QColor(*hexToRgb(self.colour)), self.lineWidth, style)

            qp.setPen(pen)
            qp.drawLine(left, lineHeight, right, lineHeight)


class LabeledHLine(Frame):
    """A class to make a Frame with an Hline - Label - Hline
    """

    def __init__(self, parent=None, height=30, text=None, bold=False, sides='both',
                 style=HLine.SOLID_LINE, colour=QtCore.Qt.black, lineWidth=2,
                 **kwds):
        """
        Draw a horizontal line and a label
        :param parent:
        :param height:
        :param text:
        :param bold:
        :param sides: either of 'both', 'left', 'right'
        :param style:
        :param colour:
        :param lineWidth:
        :param kwds:
        """
        if sides not in ['left', 'right', 'both']:
            raise RuntimeError('sides not defined correctly')
        self._sides = sides

        super(LabeledHLine, self).__init__(parent=parent, setLayout=True, showBorder=False, **kwds)
        height = height if height is not None else 30
        self.setFixedHeight(height)

        # the label with text
        self._line1 = HLine(parent=self, grid=(0, 0), style=style, colour=colour, lineWidth=lineWidth, height=height, divisor=2, hPolicy='expanding')
        self._label = Label(parent=self, grid=(0, 1), text=text, bold=bold, hPolicy='fixed')
        self._line2 = HLine(parent=self, grid=(0, 2), style=style, colour=colour, lineWidth=lineWidth, height=height, divisor=2, hPolicy='expanding')

        self._updateLines()

    @property
    def sides(self):
        return self._sides

    @sides.setter
    def sides(self, value):
        if value not in ['left', 'right', 'both']:
            raise RuntimeError('sides not defined correctly')
        self._sides = value

        self._updateLines()

    def _updateLines(self):
        if self._sides == 'left':
            self._line1.show()
            self._line2.hide()
        elif self._sides == 'right':
            self._line1.hide()
            self._line2.show()
        else:
            self._line1.show()
            self._line2.show()
        if not (txt := bool(self._label.get())):
            if self._sides == 'left':
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
        val = size.height()

        self._line1.setFixedHeight(val // 2)
        self._line2.setFixedHeight(val // 2)
        self.setFixedHeight(val)


def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = HLine()
    sys.exit(app.exec_())


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = CcpnDialog(windowTitle='Test HLine', setLayout=True)
    Label(parent=popup, grid=(0, 0), text='Just some text')
    line = HLine(parent=popup, grid=(1, 0), hPolicy='expanding', spacing=(0, 0))
    Label(parent=popup, grid=(2, 0), text='Just some text to separate')
    line2 = LabeledHLine(parent=popup, grid=(3, 0), text='a line with text')
    popup.show()
    popup.raise_()
    app.start()
