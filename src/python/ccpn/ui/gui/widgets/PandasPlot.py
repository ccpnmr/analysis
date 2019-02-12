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
__dateModified__ = "$dateModified: 2017-07-07 16:32:54 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


from ccpn.ui.gui.widgets.Widget import Widget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt


class PandasPlot(Widget):
    """
    takes a dataframe and plot it using matplotlib
    See example below for usage.
    """

    def __init__(self, parent=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)
        self._parent = parent
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)

        layout = self.getLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def plotDataFrame(self, dataFrame, kind='line', *args, **kwds):
        """
        plots one plot at a time in position 111 on self.figure
        :param dataFrame: a pandas dataframe with plot-able items  (floats and ints)
        :param kind:  - 'line' : line plot (default)
                      - 'bar' : vertical bar plot
                      - 'barh' : horizontal bar plot
                      - 'hist' : histogram
                      - 'box' : boxplot
                      - 'kde' : Kernel Density Estimation plot
                      - 'density' : same as 'kde'
                      - 'area' : area plot
                      - 'pie' : pie plot
                      - 'scatter'
        :param args:
        :param kwds: Give any parameters as matplotlib eg. x,y color, linewidth, markersize etc
        :return: matplotlib axes obj
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        plot = dataFrame.plot(kind=kind, ax=ax, *args, **kwds)
        self.canvas.draw()
        return plot

    def show(self, *args, **kwds):
        """

        :param args: as CcpnDialog
        :param kwds: CcpnDialog
        :return: opens a CcpnDialog with the plot
        """
        from ccpn.ui.gui.popups.Dialog import CcpnDialog

        popup = CcpnDialog(setLayout=True, *args, **kwds)
        popup.getLayout().addWidget(self)
        popup.show()
        popup.raise_()


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    import numpy as np
    import pandas as pd


    app = TestApplication()

    colors = ("red", "green", "yellow", "pink", "purple")

    d = {'one': np.random.rand(5),
         'two': np.random.rand(5)}
    df = pd.DataFrame(d)

    widget = PandasPlot()
    widget.plotDataFrame(dataFrame=df, )
    widget.show(windowTitle='PCA', size=(500, 500))

    app.start()
