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
__dateModified__ = "$dateModified: 2021-06-29 13:31:41 +0100 (Tue, June 29, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2020-07-07 12:36:16 +0100 (Tue, July 7, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtCore import Qt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Base import Base

class MathTextWidget(Widget):


    def __init__(self, parent=None, mathText='', textColour=None, textSize=12, bold=False,
                 margins=[0, 0, 0, 0], **kwds):
        super().__init__(parent)
        Base._init(self, **kwds)

        l=QVBoxLayout(self)
        l.setContentsMargins(*margins)

        r,g,b,a=self.palette().base().color().getRgbF()

        self._figure=Figure(edgecolor=(r,g,b), facecolor=(r,g,b))
        self._canvas=FigureCanvas(self._figure)
        l.addWidget(self._canvas)
        self._figure.clear()
        text=self._figure.suptitle(
            mathText,
            x=0.0,
            y=1.0,
            horizontalalignment='left',
            verticalalignment='top',
            size=QtGui.QFont().pointSize()*2
        )
        self._canvas.draw()

        (x0,y0),(x1,y1)=text.get_window_extent().get_points()
        w=x1-x0; h=y1-y0

        self._figure.set_size_inches(w/80, h/80)
        self.setFixedSize(w,h)




if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog

    app = TestApplication()

    mathText = r'$X_k = \frac{V2-V1}{V1}}$'

    popup = CcpnDialog(windowTitle='Test PulldownList', setLayout=True)
    w = MathTextWidget(popup, mathText)

    popup.show()
    popup.raise_()
    app.start()

