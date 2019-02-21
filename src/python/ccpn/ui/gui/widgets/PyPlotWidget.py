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
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import matplotlib
from ccpn.ui.gui.widgets.Widget import Widget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

matplotlib.rcParams['backend'] = 'Qt5Agg'
# """
# This is not the best way to set the backend.
# But the quickest way to change if something goes wrong in some machine
# valid strings are: ['Qt4Agg', 'template', 'GTK3Cairo', 'ps', 'GTKAgg',
#                     'GTKCairo', 'Qt5Agg', 'WebAgg', 'WXAgg', 'nbAgg',
#                     'cairo', 'WXCairo', 'TkCairo', 'GTK3Agg', 'svg',
#                     'GTK', 'pgf', 'pdf', 'MacOSX', 'gdk', 'WX',
#                     'Qt4Cairo', 'agg', 'TkAgg', 'Qt5Cairo']
# """

class PyPlotWidget(Widget):
    """
    This widget wraps all calls from pyplot, e.g. plot,pie,hist,bar,fill etc.
    It plots 1D, nD, images, call the methods as normal pyplot.

    To use inside a module:
     --> use as a normal Base Widget (Give a layout parent, grid ... any other Base kwds)
            Example:
                x = [1,20,3,7]
                widget = PyPlotWidget(myModule.mainWidget, grid=(0,0))
                widget.plot(x)


    To use as popup:
    --> after init, use the show() method with any CcpnDialog Base kwds
            Example:
                x = [1,20,3,7]
                widget = PyPlotWidget()
                widget.plot(x)
                widget.show(windowTitle='Test', size=(500, 500))

    It contains a special method to plot directly from a dataframe.
    See examples below for usage.

    common:
            'plot',
            'pie',
            'pcolormesh',
            'hist',
            'streamplot',
            'bar',
            'scatter',
            'fill',
            'semilogx',
            'semilogy',
            'loglog',
            'polar'

    For more example and complex usages see matplotlib documentation.
    https://matplotlib.org/tutorials/introductory/pyplot.html#sphx-glr-tutorials-introductory-pyplot-py

    Possible errors:
        - backend: set one of the valid backend. E.g. matplotlib.rcParams['backend'] = 'Qt5Agg'
        - plot.figure() shows just a white background. Use plot._figure instead.
    """

    def __init__(self, parent=None, **kwds):
        super().__init__(parent, setLayout=True, **kwds)
        self._parent = parent
        self._figure = plt.figure() # as to be init here
        self.canvas = FigureCanvas(self._figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.pyplot = plt
        self.pyplot.show = self.show # override the original show method so to open the CcpnDialog
        for att in dir(self.pyplot): # set all plt attr to this widget to easy access them
            setattr(self, att, getattr(self.pyplot, att))

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
        self._figure.clear()
        ax = self._figure.add_subplot(111)
        plot = dataFrame.plot(kind=kind, ax=ax, *args, **kwds)
        self.canvas.draw()
        return plot

    def displayImage(self, image:str=None, format=None, axis=False, *args, **kwds):
        """
        quick way to display images using the built-in methods from pyPlot
        :param image: str -- Path
        :param format: as imread
        :param axis: False doesn't display axis around the image.
        :param args: as imshow
        :param kwds: as imshow
        :return:
        """
        if image:
            img = self.imread(image, format)
            self.imshow(img, *args, **kwds)
            if not axis:
                self.axis('off')
            return img

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


    def _simplePlotExample():
        plt = PyPlotWidget()
        x = [1,2,3,4,5]
        plt.plot(x)
        plt.ylabel('some numbers')
        plt.show(windowTitle='Simple plot', size=(500, 500))

    def _pandasPlotExample():
        d = {'one': np.random.rand(5),
             'two': np.random.rand(5)}
        df = pd.DataFrame(d)
        plt = PyPlotWidget()
        plt.plotDataFrame(dataFrame=df, )
        plt.show(windowTitle='Pandas', size=(500, 500))

    def _imageExample():
        import os
        plt = PyPlotWidget()
        path = os.getcwd()
        imgPath = (os.path.join(path, 'About_CcpNmr.png'))
        plt.displayImage(imgPath)
        plt.tight_layout()
        plt.show(windowTitle='Image', size=(500, 500))

    def _multiPlotExample():
        '''
        Example copied from https://matplotlib.org
        '''
        names = ['group_a', 'group_b', 'group_c']
        values = [1, 10, 100]
        plt = PyPlotWidget()
        plt.figure(1, figsize=(9, 3))
        plt.subplot(131)
        plt.bar(names, values)
        plt.subplot(132)
        plt.scatter(names, values)
        plt.subplot(133)
        plt.plot(names, values)
        plt.suptitle('Categorical Plotting')
        plt.show(windowTitle='Multi Plot Example', size=(1000, 500))

    def _3DExample():
        '''
        Example copied from https://matplotlib.org
        note plt._figure instead of  plt.figure()
        '''
        from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 unused import
        import numpy as np

        plt = PyPlotWidget()
        np.random.seed(19680801)
        fig = plt._figure # figure was already created
        ax = fig.add_subplot(111, projection='3d')
        colors = ['r', 'g', 'b', 'y']
        yticks = [3, 2, 1, 0]
        for c, k in zip(colors, yticks):
            # Generate the random data for the y=k 'layer'.
            xs = np.arange(20)
            ys = np.random.rand(20)
            cs = [c] * len(xs)
            cs[0] = 'c'
            ax.bar(xs, ys, zs=k, zdir='y', color=cs, alpha=0.8)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.set_yticks(yticks)

        plt.show(windowTitle='Multi Plot Example', size=(1000, 500))

    def _3DsurfaceExample():
        '''
        Example from https://matplotlib.org/mpl_toolkits/mplot3d/tutorial.html
        note plt._figure instead of  plt.figure()
        '''
        from mpl_toolkits.mplot3d import Axes3D
        from matplotlib import cm
        from matplotlib.ticker import LinearLocator, FormatStrFormatter
        import numpy as np
        plt = PyPlotWidget()
        fig = plt._figure
        ax = fig.gca(projection='3d')
        X = np.arange(-5, 5, 0.25)
        Y = np.arange(-5, 5, 0.25)
        X, Y = np.meshgrid(X, Y)
        R = np.sqrt(X**2 + Y**2)
        Z = np.sin(R)
        surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                               linewidth=0, antialiased=False)
        ax.set_zlim(-1.01, 1.01)
        ax.zaxis.set_major_locator(LinearLocator(10))
        ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))
        fig.colorbar(surf, shrink=0.5, aspect=5)
        plt.show(windowTitle='Surface Example', size=(1000, 500))

    # _imageExample()
    # _multiPlotExample()
    _3DsurfaceExample()
    app.start()
