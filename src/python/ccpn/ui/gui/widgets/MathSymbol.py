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

