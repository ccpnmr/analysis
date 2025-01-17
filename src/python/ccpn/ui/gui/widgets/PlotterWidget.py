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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-02-21 19:34:43 +0000 (Tue, February 21, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from contextlib import contextmanager
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets import PlotterWidgetUtils as plotterUtils
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning

matplotlib.use('QtAgg') # this is very important!! If not set to an Agg variant, it keeps popping up previously closed windows.

class PlotterWidget(Widget):
    """
    This widget allows to plot several kinds of plots using the libraries of MatplotLib, Seaborn and Pandas.
    It includes:
        - Standard plots: Line, LineErrors, Scatter, Bars, hist, contour etc.
        - Distribution plots: univariate and bivariate(kde) distributions, Box&Whisker
        - Matrix plots: HeatMap and ClusterMap
        - Statistical plots: Regression, CrossCorrelation, AutoCorrelation, Coherence, CrossSpectralDensity
        - 3D (advance see examples)
        - images

    Usages:
    ================
    User-Macros. Stand-alone:
    --> use with a context manager. (it ensures always to show the figure at the end)
        Example:
            from ui.gui.widgets.PlotterWidget import plotter
            with plotter(xAxisTitle='X', yAxisTitle='Y', plotTitle='MyPlot') as plot:
                x, y = [1,2,3,], [10,20,30]
                plot.plotLine(x,y, label='myCurve')


    User-Macros/Development. Embedded in a popup:
    --> Inside a Ccpn Dialog. After calling the method plotX, always need to call the method "show".
        Example:
            from ui.gui.widgets.PlotterWidget import PlotterWidget
            y = [1,20,3,7]
            widget = PlotterWidget()
            widget.plotLine(y=y)
            widget.show(windowTitle='Test', size=(500, 500) ...)


    Development. Embedded inside a module: (Not fully tested!)
     --> use as a normal Base Widget (Give a layout parent, grid ... any other Base kwds)
            Example:
                y = [1,20,3,7]
                widget = PlotterWidget(myModule.mainWidget, grid=(0,0))
                widget.plotLine(y=y)
                ...

    See a series of example at the bottom of this file.
    For complex cases and general usages see matplotlib documentation:
        1) https://matplotlib.org/tutorials/introductory/pyplot.html#sphx-glr-tutorials-introductory-pyplot-py
        2) https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.html#module-matplotlib.pyplot


    """

    def __init__(self, **kwds):
        super().__init__(None, setLayout=True, **kwds)
        plotterUtils._setDefaultGlobalPlotPreferences(plt)
        self.pyplot = plt
        self._figure = self.pyplot.figure(clear=False) # figure has to be initiated here
        self.canvas = FigureCanvas(self._figure)
        self.toolbar = plotterUtils.PyPlotToolbar(parent=self, canvas=self.canvas,
                                     grid=(0, 0), gridSpan=(1, 2), hAlign='l', hPolicy='preferred')

        self.pyplot.show = self.show # overrides the original show method, open the CcpnDialog instead
        self.isClosed = False
        ### sets all plt attr to this widget to easy access them
        for att in dir(self.pyplot):
            setattr(self, att, getattr(self.pyplot, att))
        layout = self.getLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)


    @property
    def currentPlot(self):
        """
        get the current AxesSubplot instance
        """
        return self.gca()

    @property
    def currentFigure(self):
        return self.gcf()

    ###################################################
    ###############   Standard plots    ###############
    ###################################################

    def plotLine(self, x=None, y=None, colour='b', markerStyle=None, lineStyle='-',
                 linewidth=None, legendName=None, gid=None, **kwargs):
        """
        Plot data as a line using the native MatplotLib Module.
        --------------------------

        Parameters:
        ==========================
            :x, y:   array-like or scalar
                    The horizontal / vertical coordinates of the data points.
                    x values are optional and default to range(len(y)).
            :markerStyle: str, one of:
                                    '.' 	point marker;
                                    ',' 	pixel marker;
                                    'o' 	circle marker;
                                    'v' 	triangle_down marker;
                                    '^' 	triangle_up marker
            :lineStyle: str, one of:
                                    '-' 	solid line style;
                                    '--' 	dashed line style;
                                    '-.' 	dash-dot line style;
                                    ':' 	dotted line style
            :colour: str, one of:
                                    'b' 	blue;
                                    'g' 	green;
                                    'r' 	red;
                                    'c' 	cyan;
                                    'm' 	magenta;
                                    'y' 	yellow;
                                    'k' 	black;
                                    'w' 	white
            :gid:            str, line identifier
            :linewidth:      float, thickness of the line
            :legendName:     str, the name for the line that will go on the legend

        """
        if y is None:
            raise RuntimeError('Y value must be set.')
        if x is None:
            x = np.arange(len(y))
        kwargs.update({'linestyle':lineStyle, 'color': colour, 'marker': markerStyle,
                       'linewidth':linewidth, 'label':legendName, 'gid':gid,})
        self.currentPlot.plot(x,y, **kwargs)

    def plotLineWithErrors(self, x, y, yErr=None, xErr=None, fmt='', errColour=None, eLinewidth=None, capSize=None,
                           barsAbove=False, lowLims=False, upperLims=False, xLowLims=False, xUpLims=False, errorEvery=1,
                           capThick=None, *args, **kwargs):

        """
        Plot data as line and x/y errors.
        --------------------------

        For full documentation see:
            https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.errorbar.html#matplotlib.axes.Axes.errorbar
        """
        self.currentPlot.errorbar(x, y, yerr=yErr, xerr=xErr, fmt=fmt, ecolor=errColour, elinewidth=eLinewidth,
                             capsize=capSize, barsabove=barsAbove, lolims=lowLims, uplims=upperLims, xlolims=xLowLims,
                             xuplims=xUpLims, errorevery=errorEvery, capthick=capThick, *args, **kwargs)


    def plotHist(self, x, bins=None, range=None, density=False, weights=None,
                cumulative=False, bottom=None, histtype='bar', align='mid',
                orientation='vertical', rwidth=None, log=False, colour=None,
                label=None, stacked=False, normed=None, data=None, **kwargs):
        """
        Plot data as histogram using the native MatplotLib Module.

        --------------------------

        Parameters:
        ==========================

            :x: float or array-like
            :bins: int or sequence or str, default: 10.
                    If bins is an integer, it defines the number of equal-width bins in the range.
                    If bins is a sequence, it defines the bin edges.
                    If bins is a string, it is one of the binning strategies: One of
                    'auto', 'fd', 'doane', 'scott', 'stone', 'rice', 'sturges', or 'sqrt'.
            :density: bool, default: False. If True, draw and return a probability density
            :weights(n,) array-like or None, default: None. An array of weights, of the same shape as x.
                    Each value in x only contributes its associated weight towards the bin count (instead of 1).
                    If density is True, the weights are normalized, so that the integral of the
                    density over the range remains 1.

        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hist.html#matplotlib.pyplot.hist

        """

        self.currentPlot.hist(x, bins=bins, range=range, density=density, weights=weights,
                cumulative=cumulative, bottom=bottom, histtype=histtype, align=align,
                orientation=orientation, rwidth=rwidth, log=log, color=colour,
                label=label, stacked=stacked, normed=normed, data=data,**kwargs)

    def plotBar(self, values, heights, unitLabels=None, errors=None, thickness=0.8, colour=None, orientation='v', **kwargs):
        """
        Plot data as horizonatal bars using the native MatplotLib Module.
        --------------------------
         For full documentation see:
         https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.bar.html#matplotlib.pyplot.bar

        """

        if orientation in ['v', 'vertical', 'V', 'Vertical']:
            self.currentPlot.bar(x=values, height=heights, width=thickness, color=colour, yerr=errors, **kwargs)
            self.currentPlot.set_xticklabels(unitLabels)
            self.currentPlot.set_xticks(values)

        if orientation in ['h', 'H', 'Horizontal', 'horizontal']:
            self.currentPlot.barh(y=values, width=heights, height=thickness, color=colour, xerr=errors, **kwargs)
            self.currentPlot.set_yticklabels(unitLabels)
            self.currentPlot.set_yticks(values)

    def plotContour(self, x, y, heights, levels=None, colours=None, **kwargs):
        """
        Plot contours.
        --------------------------

        Parameters:
        ==========================

        Parameters:
            :heights: (M, N) array-like. The height values over which the contour is drawn.
            :x,y:  (x,y) array-like, optional. The coordinates of the values in heights. X and y must have the same shape.
            :levels: int or array-like, optional .Determines the number and positions of the contour lines / regions.
            :colours: color string or sequence of colors, optional. The colors of the levels, i.e. the lines for contour

        For more optional parameters see the original documentation in matplotlib.pyplot.contour.
        See _contourExample for x,y,heights demo data.
        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.contour.html#matplotlib.pyplot.contour

        """
        self.currentPlot.contour(x, y, heights, levels=levels, colors=colours, **kwargs)

    def plotScatter(self, x, y, shape=None, colours=None, marker=None, cmap=None, norm=None, vMin=None, vMax=None,
                    alpha=None, lineWidths=None, edgeColours=None, plotNonFinite=False, **kwargs):
        """
        Plot scatter plots.
        --------------------------

        Parameters:
        ==========================
            :x, y:   float or array-like, shape (n, ). The data positions.
            :shape:  float or array-like, shape (n, ), optional
            :colours:   array-like or list of colors or color, optional

        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.scatter.html#matplotlib.pyplot.scatter

        """
        self.currentPlot.scatter(x, y, s=shape, c=colours, marker=marker, cmap=cmap, norm=norm, vmin=vMin, vmax=vMax,
                            alpha=alpha, linewidths=lineWidths, edgecolors=edgeColours, plotnonfinite=plotNonFinite,
                            **kwargs)

    def plotPie(self, x, explode=None, labels=None, colours=None, autopct=None, pctDistance=0.6, shadow=False,
                labelDistance=1.1, startAngle=0, radius=1, counterClock=True, wedgeProps=None,
                textProps=None, centre=(0,0), frame=False, rotateLabels=False):
        """
        Plot a pie plot.
        --------------------------

        Parameters:
        ==========================
            :x:   array-like. The wedge sizes.
            :explode:  array-like, optional. A len(x) array which specifies the fraction of the radius with which to offset each wedge.
            :labels:   list, optional. A sequence of strings providing the labels for each wedge
            :colours:   array-like or list of colors or color, optional

        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.pie.html#matplotlib.pyplot.pie

        """

        self.currentPlot.pie(x, explode=explode, labels=labels, colors=colours, autopct=autopct, pctdistance=pctDistance,
                            shadow=shadow, labeldistance=labelDistance, startangle=startAngle, radius=radius,
                            counterclock=counterClock, wedgeprops=wedgeProps, textprops=textProps, center=centre,
                            frame=frame, rotatelabels=rotateLabels)

    def plotHexBin(self, *args, **kwargs):
        """
        Make a 2D hexagonal binning plot of points x, y.
        --------------------------

        Parameters:
        ==========================

        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.hexbin.html#matplotlib.pyplot.hexbin

        """
        self.currentPlot.hexbin(*args, **kwargs)

    ###################################################
    ############### Distribution plots  ###############
    ###################################################


    def plotDistribution(self, y, hist=True, kde=True, rug=False,
                         colour=None, orientation='h', legendName=None, **kwargs ):
        """
        Plot univariate distribution of data using the package Seaborn.
        --------------------------

        Parameters:
        ==========================
            :y:   Series, 1d-array, or list
            :hist: bool, True to add the (normed) histograms.
            :kde: bool, True to plot a gaussian kernel density estimate as a line.
            :rug: bool, True to draw a rugplot on the support axis.

        For full documentation see:
        https://seaborn.pydata.org/generated/seaborn.displot.html#seaborn.displot
        """
        import seaborn as sns

        #  Warning distplot will be deprecated at some point so use displot instead. Hence, ensure the same signature.
        distPlot = getattr(sns, 'distplot', None)
        vertical = True if orientation in ['v', 'V', 'Vertical', 'vertical'] else False
        if distPlot:
            kwargs.update({'a':y, 'hist':hist, 'kde':kde, 'rug':rug,
                           'color':colour, 'label':legendName, 'vertical': vertical,})
        else:
            distPlot = getattr(sns, 'displot', None)
            kwargs.update({'y':y, 'kde': kde, 'rug': rug, 'color': colour, 'label': legendName,})
        try:
            distPlot(**kwargs)
        except Exception as e:
            getLogger().warning("Cannot plot distribution. %s" %str(e))
            showWarning('Cannot plot distribution', str(e))


    def plotKDE(self, x, y, colour=None, orientation='h', legendName=None, **kwargs ):
        """
        Plot bivariate distribution of data using the package Seaborn.
        --------------------------

        Parameters:
        ==========================
            :x,y:   Series, 1d-array, or list

        For full documentation see:
        https://seaborn.pydata.org/generated/seaborn.kdeplot.html
        """
        import seaborn as sns

        vertical = True if orientation in ['v', 'V', 'Vertical', 'vertical'] else False
        kwargs.update({'data':x, 'data2':y, 'vertical': vertical, 'color': colour, 'label': legendName,})
        sns.kdeplot(**kwargs)

    def plotBoxAndWhisker(self, x,  notch=None, sym=None, vert=None, whis=None, positions=None, widths=None,
                          patchArtist=None, bootstrap=None, userMedians=None,
                          confIntervals=None, meanLine=None, showMeans=None,
                          showCaps=None, showBox=None, showFliers=None, boxProps=None,
                          labels=None, flierProps=None, medianProps=None, meanProps=None,
                          capProps=None, whiskerProps=None, manageTicks=True,
                          autoRange=False, zOrder=None, **kwargs):
        """
        Make a box and whisker plot.
        --------------------------

        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.boxplot.html#matplotlib.pyplot.boxplot
        """
        kwargs.update({'notch':notch, 'sym':sym, 'vert':vert, 'whis':whis,
                        'positions':positions, 'widths':widths, 'patch_artist':patchArtist,
                        'bootstrap':bootstrap, 'usermedians':userMedians,
                        'conf_intervals':confIntervals, 'meanline':meanLine,
                        'showmeans':showMeans, 'showcaps':showCaps, 'showbox':showBox,
                        'showfliers':showFliers, 'boxprops':boxProps, 'labels':labels,
                        'flierprops':flierProps, 'medianprops':medianProps,
                        'meanprops':meanProps, 'capprops':capProps,
                        'whiskerprops':whiskerProps, 'manage_ticks':manageTicks,
                        'autorange':autoRange, 'zorder':zOrder})

        
        self.currentPlot.boxplot(x, **kwargs)


    ###################################################
    ###############   Matrix plots      ###############
    ###################################################

    def plotHeatMap(self, data, *args, **kwargs ):
        """
        Plot a heatmap data using the package Seaborn.
        --------------------------

        Parameters:
        ==========================
            data:   2d-array

        For full documentation see:
        https://seaborn.pydata.org/generated/seaborn.heatmap.html

        """
        import seaborn as sns
        sns.heatmap(data, *args, **kwargs)

    def plotClusterMap(self, data, *args, **kwargs):
        """
        Plot a cluster map data using the package Seaborn.

        For full documentation see:
        https://seaborn.pydata.org/generated/seaborn.clustermap.html#seaborn.clustermap
        --------------------------

        Parameters:
        ==========================

            data:   2d-array
        """

        import seaborn as sns

        sns.clustermap(data, *args, **kwargs)


    ###################################################
    ###############  Statistical plots  ###############
    ###################################################

    def plotRegression(self, x, y, *args, **kwargs):
        """
        Plot data and a linear regression model fit using the package Seaborn.
        --------------------------

        For full documentation see:
        https://seaborn.pydata.org/generated/seaborn.regplot.html#seaborn.regplot

        """
        import seaborn as sns
        sns.regplot(x,y, *args, **kwargs)


    def plotResidualRegression(self, x, y, *args, **kwargs):
        """
        Plot the residuals of a linear regression using the package Seaborn.

        This function will regress y on x (possibly as a robust or polynomial regression)
         and then draw a scatterplot of the residuals. You can optionally fit a lowess
         smoother to the residual plot, which can help in determining if there is structure to the residuals.
        --------------------------

        For full documentation see:
        https://seaborn.pydata.org/generated/seaborn.residplot.html#seaborn.residplot
        """
        import seaborn as sns
        sns.residplot(x,y, *args, **kwargs)

    def plotCoherence(self, x, y, *args, **kwargs):
        """

        Plot the coherence between x and y.
        ---------------------------------

        Plot the coherence between x and y. Coherence is the normalized cross spectral density:
            Cxy = | Pxy| 2PxxPyy

        ---------------------------------

        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.cohere.html#matplotlib.pyplot.cohere

        """
        self.currentPlot.cohere(x, y, *args, **kwargs)

    def plotAutoCorrelation(self, x, *args, **kwargs):
        """
        Plot the autocorrelation of x.
        --------------------------

        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.acorr.html#matplotlib.pyplot.acorr

        """
        self.currentPlot.acorr(x, *args, **kwargs)

    def plotCrossCorrelation(self, x, y, *args, **kwargs):
        """
        Plot the cross correlation between x and y.
        --------------------------

        The correlation with lag k is defined as ∑𝑛𝑥[𝑛+𝑘]⋅𝑦∗[𝑛]
        where 𝑦∗ is the complex conjugate of 𝑦.

        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.xcorr.html#matplotlib.pyplot.xcorr

        """
        self.currentPlot.xcorr(x, y, *args, **kwargs)

    def plotCrossSpectralDensity(self, x, y, *args, **kwargs):
        """
        Plot the cross-spectral density.
        --------------------------

        The cross spectral density 𝑃𝑥𝑦 by Welch's average periodogram method.
        The vectors x and y are divided into NFFT length segments. Each segment is detrended by function detrend
        and windowed by function window. noverlap gives the length of the overlap between segments.
        The product of the direct FFTs of x and y are averaged over each segment to compute 𝑃𝑥𝑦,
        with a scaling to correct for power loss due to windowing.
        For full documentation see:
        https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.acorr.html#matplotlib.pyplot.acorr

        """
        self.currentPlot.csd(x, y, *args, **kwargs)


    def displayImage(self, imagePath:str=None, format=None, axis=False, *args, **kwds):
        """
        quick way to display images using the built-in methods from pyPlot
        --------------------------

        Parameters:
        :param image: str -- Path
        :param format: as imread
        :param axis: False doesn't display axis around the image.
        :param args: as imshow
        :param kwds: as imshow
        :return:
        """
        if imagePath:
            img = self.imread(imagePath, format)
            self.imshow(img, *args, **kwds)
            if not axis:
                self.axis('off')
            return img

    def show(self, windowTitle='CcpNmr Plot', size=(700, 700),
             xAxisTitle=None, yAxisTitle=None, plotTitle=None, showLegend=True, minimalMargins=False, dialogKwds=None):
        """

        Show the plot in a new popup window.
        --------------------------

        Parameters:
        ---------------------------------
        :windowTitle: str, title of the popup window
        :plotTitle: str, title of the plot (top-centre)
        :xAxisTitle: str, name of the x Axis label
        :yAxisTitle: str, name of the y Axis label
        :showLegend: bool, show the legend on the top-right corner of the plot
        :param dialogKwds: dict, CcpnDialog key arguments
        :return: opens a CcpnDialog with the plot

        See CcpnDialog for more arguments.

        """
        if self.isClosed:
            showWarning('Cannot show','Plot has been closed. Please create a new instance.')
            return

        dialogKwds = dialogKwds or {}
        if showLegend:
            if self._getCurrentLegendLabels():
                self.legend()
        if minimalMargins:
            self.tight_layout()
        self.xlabel(xAxisTitle)
        self.ylabel(yAxisTitle)
        self.title(plotTitle)
        super().show()
        # wrap all in a ccpn dialog popup
        # popup = CcpnDialog(setLayout=True, windowTitle=windowTitle, size=size, **dialogKwds)
        # popup.getLayout().addWidget(self)
        # popup.show()
        # popup.raise_()

    def updatePlot(self):
        self.canvas.draw_idle()

    def clear(self):
        self._figure.clear()

    def setBackgroundColour(self, colour):
        self.currentPlot.set_facecolor(colour)

    def _getCurrentLegendLabels(self):
        from matplotlib.legend import _get_legend_handles_labels
        objs, labels = _get_legend_handles_labels([self.currentPlot])
        return labels

    def close(self):
        self.clear()
        self.currentPlot.close()
        self.currentFigure.close()
        self.isClosed = True

    def __repr__(self):
        name = self.__class__.__name__
        if self.isClosed:
            return f'<{name}.closed>'
        return f'<{name}>'


@contextmanager
def plotter(xAxisTitle=None, yAxisTitle=None, plotTitle=None, showLegend=True,
            windowTitle=None, size=(700, 700), *args, **kwargs):
    """Wrap a Plotter and show the GUI dialog Window at the end.
    At the end of the "with" statement stream, the Plotter instance is automatically closed to avoid
    wrong state representations. The GUI window cannot be reopened after closing the Dialog.

    ===============
    usage:
        from ui.gui.widgets.PlotterWidget import plotter
        with plotter() as plot:
            x = [1,2,3,]
            y = [10,20,30]
            plot.plotLine(x,y, label='myCurve')
    ===============
    """
    plot = PlotterWidget()

    try:
        yield plot
    finally:
        plot.show(size=size, windowTitle=windowTitle,
                  xAxisTitle=xAxisTitle, yAxisTitle=yAxisTitle, plotTitle=plotTitle,
                  showLegend=showLegend, *args, **kwargs)
        # plot.close()

###################################################
###############      Examples       ###############
###################################################


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication

    app = TestApplication()

    def _plotterExample():
        with plotter() as plot:
            d = {'one': np.random.rand(5),
                 'two': np.random.rand(5)}
            df = pd.DataFrame(d)
            plot.plotLine(x=df.one, y=df.two)

    def _simplePlotExample():
        plt = PlotterWidget()
        x = np.arange(10)
        y = np.random.rand(len(x))
        plt.plotLine(x,y, legendName='my curve')
        plt.show(windowTitle='Simple plot', size=(500, 500))

    def _plotLineWithErrorsExample():
        plt = PlotterWidget()
        x = np.arange(100)
        y = np.random.rand(len(x))
        plt.plotLineWithErrors(x,y, xErr=x*0.01, yErr=y*0.06)
        plt.show(windowTitle='Simple plot', size=(500, 500))

    def _pandasPlotExample():
        d = {'x': np.random.rand(5),
             'y': np.random.rand(5)}
        df = pd.DataFrame(d)
        plt = PlotterWidget()
        plt.plotScatter(x=df.x, y=df.y,)
        plt.show(windowTitle='Pandas', size=(500, 500))

    def _imageExample():
        import os
        plt = PlotterWidget()
        path = os.getcwd()
        imgPath = (os.path.join(path, 'AboutCcpNmr.png'))
        plt.displayImage(imgPath)
        plt.show(windowTitle='Image', size=(500, 500))

    def _multiPlotExample():
        """
        Example copied from https://matplotlib.org
        """
        names = ['group_a', 'group_b', 'group_c']
        values = [1, 10, 100]
        plt = PlotterWidget()
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

        plt = PlotterWidget()
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
        plt = PlotterWidget()
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

    def _contourExample():
        import numpy as np

        # generate 101 x and y values between -10 and 10
        x = np.linspace(-10, 10, 101)
        y = np.linspace(-10, 10, 101)

        # make X and Y matrices representing x and y values of 2d plane
        X, Y = np.meshgrid(x, y)

        # compute z value of a point as a function of x and y (z = l2 distance form 0,0)
        Z = np.sqrt(X ** 2 + Y ** 2)

        plt = PlotterWidget()
        plt.plotContour(X, Y, Z, [1,4,7], ['r','g','b'])
        plt.show()

    def _3dCountourExample():
        import matplotlib.pyplot as plt
        from scipy.stats import multivariate_normal
        from mpl_toolkits.mplot3d import Axes3D  # <--- This is important for 3d plotting  :O

        x, y = np.mgrid[3:5:100j, 3:5:100j]
        xy = np.column_stack([x.flat, y.flat])
        mu = np.array([4.0, 4.0])
        sigma = np.array([0.1, 0.1])
        covariance = np.diag(sigma ** 2)
        z = multivariate_normal.pdf(xy, mean=mu, cov=covariance)
        z = z.reshape(x.shape)


        plt = PlotterWidget()
        fig = plt._figure
        ax = fig.gca(projection='3d')
        ax.plot_surface(x, y, z)
        plt.show()

    def _barExample(orientation='v'):
        import numpy as np

        # Example data
        people = ('Tom', 'Alex', 'Harry', 'Slim', 'Jim')
        x = np.arange(len(people))
        performance = 3 + 10 * np.random.rand(len(people))
        error = np.random.rand(len(people))
        #  plot
        plt = PlotterWidget()
        plt.plotBar(x, heights=performance, unitLabels=people, errors=error, orientation=orientation, label='myData1')
        plt.plotBar(x, heights=performance*0.6, unitLabels=people, errors=error, orientation=orientation, label='myData2')

        plt.show(plotTitle='Example', xAxisTitle='AX', yAxisTitle='ddd', )

    def _scatterExample():

        N = 50
        x = np.random.rand(N)
        y = np.random.rand(N)
        colors = np.random.rand(N)
        area = (30 * np.random.rand(N)) ** 2  # 0 to 15 point radii
        plt = PlotterWidget()
        plt.plotScatter(x, y, shape=area, colours=colors, alpha=0.7)
        plt.show(plotTitle='Scatter Example', xAxisTitle='size', yAxisTitle='size Y',)


    def _pieExample():

        # Pie chart, where the slices will be ordered and plotted counter-clockwise:
        labels = 'Frogs', 'Hogs', 'Dogs', 'Logs'
        sizes = np.array([15, 30, 45, 10])
        explode = (0, 0.1, 0, 0)  # only "explode" the 2nd slice (i.e. 'Hogs')

        plt = PlotterWidget()
        plt.plotPie(sizes, explode, labels=labels, autopct='%1.1f%%', shadow=True, startAngle=90)
        plt.show(plotTitle='Pie Example', )

    def _kdeExample():
        y = np.random.randn(100)
        x = np.arange(len(y))
        plot = PlotterWidget()
        plot.plotKDE(x, y, vertical=True, colour='red', legendName='kde 1')
        plot.show(windowTitle='KDE Example', size=(500, 500))

    def _distributionExample():
        y = np.random.randn(100)
        x = np.arange(len(y))
        plot = PlotterWidget()
        plot.plotDistribution(y, vertical=True, colour='red', legendName='test')
        plot.show(windowTitle='distribution Example', size=(500, 500))

    def _BoxAndWhiskerExample():
        y = np.random.randn(100)
        plot = PlotterWidget()
        plot.plotBoxAndWhisker([y,y*0.6])
        plot.show(windowTitle='distribution Example', size=(500, 500))

    def _heatMapExample():
        data = np.random.rand(10, 10)
        plot = PlotterWidget()
        plot.plotHeatMap(data)
        plot.show(windowTitle='heatmap Example', size=(500, 500))

    def _clusterMapExample():
        import seaborn as sns
        iris = sns.load_dataset("iris")
        species = iris.pop("species")
        plot = PlotterWidget()
        plot.plotClusterMap(iris)
        plot.show(windowTitle='ClusterMap Example', size=(500, 500))

    _contourExample()
    _3dCountourExample()
    _pieExample()
    _scatterExample()
    _barExample('h')
    _barExample('v')
    _3DExample()
    _3DsurfaceExample()
    # _imageExample()
    _multiPlotExample()
    _simplePlotExample()
    _plotLineWithErrorsExample()
    _BoxAndWhiskerExample()
    _heatMapExample()
    _clusterMapExample()
    _pandasPlotExample()
    _kdeExample()
    _distributionExample()

    # app.start()
