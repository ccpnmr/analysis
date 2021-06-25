#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2021-01-24 17:58:26 +0000 (Sun, January 24, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from contextlib import contextmanager
from collections import OrderedDict as od
import matplotlib
import os
from ccpn.ui.gui.guiSettings import getColourScheme, DARK
from ccpn.ui.gui.widgets.Widget import Widget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backend_tools import ToolBase, ToolToggleBase, ZoomPanBase, cursors, _views_positions
import matplotlib.backend_bases as backends
import matplotlib.backends.qt_editor.figureoptions as figureoptions
from matplotlib.backends.qt_editor.formsubplottool import UiSubplotTool
from matplotlib.backend_managers import ToolManager

import matplotlib.pyplot as plt
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Action import Action
from ccpn.ui.gui.widgets.ToolBar import ToolBar
from PyQt5 import QtWidgets, QtCore
import time
from ccpn.ui.gui.widgets import MessageDialog as md


# Background colour:
# Use style.available for all list
# print(plt.style.available)
if getColourScheme() == DARK:
    plt.style.use('dark_background')

# backend
matplotlib.rcParams['backend'] = 'Qt5Agg'


class PyPlotToolbar(ToolBar,  backends.NavigationToolbar2):
    """
    Re-implementation of Matplotlib ToolBar with CcpNmr widgets ands syntax.
    Matplotlib  backends for toolbars gave UserWarning as it was an experimental feature at the time of
    this implementation.
    Navigation Toolbar controls panning and zooming. Therefore re-implementations of those actions are done here.

    """

    message = QtCore.Signal(str)

    def __init__(self, parent, canvas, coordinates=True, *args, **kwargs):
        super().__init__(canvas)
        backends.NavigationToolbar2.__init__(self, canvas)

        self.canvas = canvas
        self.parent = parent
        self.coordinates = coordinates

        #  set panning the only active mode
        self._active = 'PAN'
        self._initConnections()
        # scrolling
        self.base_scale = 2.
        self.scrollthresh = .5  # .5 second scroll threshold
        self.lastscroll = time.time() - self.scrollthresh

    def _getToolBarDefs(self):
        """
        The menu action definitions
        """
        toolBarDefs = (
            ('MaximiseZoom', od((
                ('text', 'MaximiseZoom'),
                ('toolTip', 'Full zoom'),
                ('icon', Icon('icons/zoom-full.png')),
                ('callback', self.home),
                ('enabled', True)
                ))),
            ('UndoZoom', od((
                ('text', 'UndoZoom'),
                ('toolTip', 'Previous zoom'),
                ('icon', Icon('icons/zoom-undo.png')),
                ('callback', self.back),
                ('enabled', True)
                ))),
            ('RedoZoom', od((
                ('text', 'RedoZoom'),
                ('toolTip', 'Next zoom'),
                ('icon', Icon('icons/zoom-redo.png')),
                ('callback', self.forward),
                ('enabled', True)
                ))),
            (),

            ('settings', od((
                ('text', 'settings'),
                ('toolTip', 'settings'),
                ('icon', Icon('icons/settings_cog.png')),
                ('callback', self.showSettings),
                ('enabled', True)
                ))),
            ('SaveAs', od((
                        ('text', 'SaveAs'),
                        ('toolTip', 'Save image to disk'),
                        ('icon', Icon('icons/saveAs.png')),
                        ('callback', self.save_figure),
                        ('enabled', True)
                        ))),
            (),
            )
        return toolBarDefs

    def _init_toolbar(self):
        for v in self._getToolBarDefs():
            if len(v) == 2:
                if isinstance(v[1], od):
                    action = Action(self, **v[1])
                    action.setObjectName(v[0])
                    self.addAction(action)
            else:
                self.addSeparator()

    def save_figure(self, *args):
        filetypes = self.canvas.get_supported_filetypes_grouped()
        sorted_filetypes = sorted(filetypes.items())
        default_filetype = self.canvas.get_default_filetype()

        startpath = os.path.expanduser(
            matplotlib.rcParams['savefig.directory'])
        start = os.path.join(startpath, self.canvas.get_default_filename())
        filters = []
        selectedFilter = None
        for name, exts in sorted_filetypes:
            exts_list = " ".join(['*.%s' % ext for ext in exts])
            filter = '%s (%s)' % (name, exts_list)
            if default_filetype in exts:
                selectedFilter = filter
            filters.append(filter)
        filters = ';;'.join(filters)
        # TODO replace with CCPN dialog
        _getSaveFileName = QtWidgets.QFileDialog.getSaveFileName
        fname, filter = _getSaveFileName(self.canvas.parent(),
                                         "Choose a filename to save to",
                                         start, filters, selectedFilter)
        if fname:
            # Save dir for next time, unless empty str (i.e., use cwd).
            if startpath != "":
                matplotlib.rcParams['savefig.directory'] = (
                    os.path.dirname(fname))
            try:
                self.canvas.figure.savefig(fname)
            except Exception as e:
                md.showError('Error saving', e)

    def showSettings(self):
        from matplotlib.backends.backend_qt5 import SubplotToolQt
        # TODO replace with CCPN dialog
        dia = SubplotToolQt(self.canvas.figure, self.canvas.parent())
        dia.exec_()

    def _initConnections(self, *args):
        """
        Re-implemetation of panning/zooming to have a consistent behaviour with other Ccpn widgets.
        Disable the native "pan or zoom' mouse mode
        """

        if self._active:
            self._idPress = self.canvas.mpl_connect(
                    'button_press_event', self.press_pan)
            self._idRelease = self.canvas.mpl_connect(
                    'button_release_event', self.release_pan)
            self._idScroll = self.canvas.mpl_connect(
                    'scroll_event', self.scroll_event)
            # self.mode = 'pan/zoom'
            self.canvas.widgetlock(self)
        else:
            self.canvas.widgetlock.release(self)

        for a in self.canvas.figure.get_axes():
            a.set_navigate_mode(self._active)

    def scroll_event(self, event):
        if event.inaxes is None:
            return
        if event.button == 'up':
            # deal with zoom in
            scl = self.base_scale
        elif event.button == 'down':
            # deal with zoom out
            scl = 1 / self.base_scale
        else:
            # deal with something that should never happen
            scl = 1

        ax = event.inaxes
        ax._set_view_from_bbox([event.x, event.y, scl])

        # # If last scroll was done within the timing threshold, delete the
        # # previous view
        # if (time.time() - self.lastscroll) < self.scrollthresh:
        #     self.toolmanager.get_tool(_views_positions).back()
        self.canvas.draw_idle()  # force re-draw
        # self.lastscroll = time.time()
        # # self.toolmanager.get_tool(_views_positions).push_current()


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
        self.pyplot = plt
        self._figure = self.pyplot.figure(clear=False) # figure has to be initiated here
        self.canvas = FigureCanvas(self._figure)
        self.toolbar = PyPlotToolbar(parent=self, canvas=self.canvas,
                                     grid=(0, 0), gridSpan=(1, 2), hAlign='l', hPolicy='preferred')

        self.pyplot.show = self.show # overrides the original show method so to open the CcpnDialog
        for att in dir(self.pyplot): # sets all plt attr to this widget to easy access them
            setattr(self, att, getattr(self.pyplot, att))

        layout = self.getLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)


    def plotDataFrame(self, dataFrame, kind='line', *args, **kwds):
        """

        Make plots of a DataFrame.

        Parameters
        ----------
        dataFrame : Pandas DataFrame

        kind : str
            The kind of plot to produce:
            - 'line' : line plot (default)
            - 'bar' : vertical bar plot
            - 'barh' : horizontal bar plot
            - 'hist' : histogram
            - 'box' : boxplot
            - 'kde' : Kernel Density Estimation plot
            - 'density' : same as 'kde'
            - 'area' : area plot
            - 'pie' : pie plot
            - 'scatter' : scatter plot
            - 'hexbin' : hexbin plot.
        x : label or position, default None
            Only used if data is a DataFrame.
        y : label, position or list of label, positions, default None
            Allows plotting of one column versus another. Only used if data is a
            DataFrame.
        figsize : a tuple (width, height) in inches
        use_index : bool, default True
            Use index as ticks for x axis.
        title : str or list
            Title to use for the plot. If a string is passed, print the string
            at the top of the figure. If a list is passed and `subplots` is
            True, print each item in the list above the corresponding subplot.
        grid : bool, default None (matlab style default)
            Axis grid lines.
        legend : bool or {'reverse'}
            Place legend on axis subplots.
        style : list or dict
            The matplotlib line style per column.
        logx : bool or 'sym', default False
            Use log scaling or symlog scaling on x axis.
            .. versionchanged:: 0.25.0

        logy : bool or 'sym' default False
            Use log scaling or symlog scaling on y axis.
            .. versionchanged:: 0.25.0

        loglog : bool or 'sym', default False
            Use log scaling or symlog scaling on both x and y axes.
            .. versionchanged:: 0.25.0

        xticks : sequence
            Values to use for the xticks.
        yticks : sequence
            Values to use for the yticks.
        xlim : 2-tuple/list
        ylim : 2-tuple/list
        rot : int, default None
            Rotation for ticks (xticks for vertical, yticks for horizontal
            plots).
        fontsize : int, default None
            Font size for xticks and yticks.
        colormap : str or matplotlib colormap object, default None
            Colormap to select colors from. If string, load colormap with that
            name from matplotlib.
        colorbar : bool, optional
            If True, plot colorbar (only relevant for 'scatter' and 'hexbin'
            plots).
        position : float
            Specify relative alignments for bar plot layout.
            From 0 (left/bottom-end) to 1 (right/top-end). Default is 0.5
            (center).
        table : bool, Series or DataFrame, default False
            If True, draw a table using the data in the DataFrame and the data
            will be transposed to meet matplotlib's default layout.
            If a Series or DataFrame is passed, use passed data to draw a
            table.
        yerr : DataFrame, Series, array-like, dict and str
            See :ref:`Plotting with Error Bars <visualization.errorbars>` for
            detail.
        xerr : DataFrame, Series, array-like, dict and str
            Equivalent to yerr.
        mark_right : bool, default True
            When using a secondary_y axis, automatically mark the column
            labels with "(right)" in the legend.
        include_bool : bool, default is False
            If True, boolean values can be plotted.
        backend : str, default None
            Backend to use instead of the backend specified in the option
            ``plotting.backend``. For instance, 'matplotlib'. Alternatively, to
            specify the ``plotting.backend`` for the whole session, set
            ``pd.options.plotting.backend``.

            .. versionadded:: 1.0.0

        **kwargs
            Options to pass to matplotlib plotting method.

        Returns
        -------
        :class:`matplotlib.axes.Axes` or numpy.ndarray of them
            If the backend is not the default matplotlib one, the return value
            will be the object returned by the backend.

        Notes
        -----
        - See matplotlib documentation online for more on this subject
        - If `kind` = 'bar' or 'barh', you can specify relative alignments
          for bar plot layout by `position` keyword.
          From 0 (left/bottom-end) to 1 (right/top-end). Default is 0.5
          (center)
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

    def clear(self):
        self._figure.clear()

@contextmanager
def plotter(*args, **kwargs):
    """Wrap a pyplot and show the window at the end

    ===============
    usage:
        with plotter() as plot:
            x = [1,2,3,]
            y = [10,20,30]
            plot.plot(x,y)
    ===============
    """
    plot = PyPlotWidget(*args, **kwargs)


    try:
        yield plot
    finally:
        plot.show(*args, **kwargs)
        # plot.deleteLater()



if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    import numpy as np
    import pandas as pd
    app = TestApplication()

    with plotter() as plot:

        d = {'one': np.random.rand(5),
             'two': np.random.rand(5)}
        df = pd.DataFrame(d)
        plot.plotDataFrame(df, kind='line', x='two', y='one')
        # plot.hist([1,2,3,4])


    def _simplePlotExample():
        plt = PyPlotWidget()
        x = [1,2,3,4,5]
        y = [10,20,30,14,5]
        x1 = [1, 2, 3, 4, 5]
        y1 = [100, 200, 300, 140, 50]
        m = np.mean([y])
        m1 = np.mean([y1])
        ys = y/m
        y1s = y1/m1

        plt.plot(x,ys, x1,y1s,)
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
        imgPath = (os.path.join(path, 'AboutCcpNmr.png'))
        plt.displayImage(imgPath)
        plt.tight_layout()
        plt.show(windowTitle='Image', size=(500, 500))

    def _multiPlotExample():
        """
        Example copied from https://matplotlib.org
        """
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
    # _simplePlotExample()
    app.start()
