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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:46 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.0 $"
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


class HLine(Widget):

    SOLID_LINE = 'SolidLine'
    DASH_LINE = 'DashLine'
    DASH_DOT_LINE = 'DashDotLine'
    DASH_DOT_DOT_LINE = 'DashDotDotLine'

    styles = {
            SOLID_LINE     : QtCore.Qt.SolidLine,
            DASH_LINE      : QtCore.Qt.DashLine,
            DASH_DOT_LINE  : QtCore.Qt.DashDotLine,
            DASH_DOT_DOT_LINE: QtCore.Qt.DashDotDotLine,
            }

    def __init__(self, parent=None, style=SOLID_LINE, colour=QtCore.Qt.black, height=10, lineWidth=2, divisor = 3, **kwds):
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
        self.divisor = divisor #int(height / divisor)
        self.lineWidth=lineWidth

        # self.setMaximumHeight(10)
        self.setFixedHeight(height)

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawLine(qp, self.style)
        qp.end()

    def drawLine(self, qp, style=None, colour=None):

        # geomRect = self.geometry().marginsRemoved(self.contentsMargins())
        geomRect = self.geometry()
        geomHeight = int(geomRect.height() / self.divisor + 0.5)
        lineHeight = geomHeight + self.contentsMargins().top()
        left = geomRect.left()
        right =geomRect.right()

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

    def __init__(self, parent=None, height=30, text=None, bold=False,
                                    style=HLine.SOLID_LINE, colour=QtCore.Qt.black, lineWidth=2, **kwds):

        super(LabeledHLine, self).__init__(parent=parent, setLayout=True, showBorder=False, **kwds)
        self.setMinimumHeight(height)

        # first line
        self._line1 = Frame(parent=self, grid=(0, 0), setLayout=True, showBorder=False, hPolicy='expanding')
        HLine(self._line1, grid=(0,0), style=style, colour=colour, lineWidth=lineWidth, height=height, divisor=2)
        # the label with text
        self._label = Label(parent=self, grid=(0, 1), text=text, bold=bold, hAlign='centre')
        # the second line
        self._line2 = Frame(parent=self, grid=(0, 2), setLayout=True, showBorder=False, hPolicy='expanding')
        HLine(self._line2, grid=(0,0), style=style, colour=colour, lineWidth=lineWidth, height=height, divisor=2)

def main():
    app = QtWidgets.QApplication(sys.argv)
    ex = HLine()
    sys.exit(app.exec_())


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog
    from ccpn.ui.gui.widgets.Slider import SliderSpinBox


    app = TestApplication()
    popup = CcpnDialog(windowTitle='Test HLine', setLayout=True)
    Label(parent=popup, grid=(0,0), text='Just some text')
    line = HLine(parent=popup, grid=(1, 0), hPolicy='expanding', spacing=(0,0))
    Label(parent=popup, grid=(2,0), text='Just some text to separate')
    line2 = LabeledHLine(parent=popup, grid=(3,0), text='a line with text')
    popup.show()
    popup.raise_()
    app.start()
