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
__dateModified__ = "$dateModified: 2021-06-07 12:11:51 +0100 (Mon, June 07, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2021-03-26 15:58:06 +0000 (Fri, March 26, 2021) $"
#=========================================================================================
# Start of code
#=========================================================================================

import math
import time
from contextlib import contextmanager
from typing import Tuple

import numpy as np
from OpenGL import GL
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import pyqtSlot, Qt

from ccpn.util.Common import getAxisCodeMatchIndices
from ccpn.util.Constants import AXIS_FULLATOMNAME, AXIS_ACTIVEAXES, MOUSEDICTSTRIP, \
    AXIS_MATCHATOMTYPE, DOUBLEAXIS_MATCHATOMTYPE, DOUBLEAXIS_FULLATOMNAME, \
    DOUBLEAXIS_ACTIVEAXES
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.guiSettings import getColours, CCPNGLWIDGET_HEXBACKGROUND, CCPNGLWIDGET_BACKGROUND, \
    CCPNGLWIDGET_FOREGROUND, CCPNGLWIDGET_PICKCOLOUR, CCPNGLWIDGET_GRID, CCPNGLWIDGET_HIGHLIGHT, \
    CCPNGLWIDGET_LABELLING, CCPNGLWIDGET_PHASETRACE, CCPNGLWIDGET_ZOOMAREA, CCPNGLWIDGET_PICKAREA, \
    CCPNGLWIDGET_SELECTAREA, CCPNGLWIDGET_ZOOMLINE, CCPNGLWIDGET_MOUSEMOVELINE, CCPNGLWIDGET_HARDSHADE
from ccpn.ui.gui.lib.GuiStrip import STRIP_MINIMUMHEIGHT, STRIP_MINIMUMWIDTH, AxisMenu
from ccpn.ui.gui.lib.OpenGL import CcpnOpenGLDefs as GLDefs
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import ZOOMHISTORYSTORE, CURSOR_SOURCE_NONE, CURSOR_SOURCE_OTHER, ZOOMTIMERDELAY, CURSOR_SOURCE_SELF
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLRENDERMODE_REBUILD, GLRENDERMODE_DRAW, GLVertexArray
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import YAXISUNITS1D, PaintModes
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import GLString
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import GLGlobalData
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLNotifier import GLNotifier
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLViewports import GLViewports
from ccpn.ui.gui.lib.mouseEvents import rightMouse


class Gui1dWidgetAxis(QtWidgets.QOpenGLWidget):
    is1D = True
    AXIS_MARGINRIGHT = 80
    AXIS_MARGINBOTTOM = 25
    AXIS_LINE = 7
    AXIS_OFFSET = 3
    AXIS_INSIDE = False
    YAXISUSEEFORMAT = True
    INVERTXAXIS = True
    INVERTYAXIS = True
    AXISLOCKEDBUTTON = False
    AXISLOCKEDBUTTONALLSTRIPS = False
    SPECTRUMXZOOM = 1.0e1
    SPECTRUMYZOOM = 1.0e1
    SHOWSPECTRUMONPHASING = False
    XAXES = GLDefs.XAXISUNITS
    YAXES = YAXISUNITS1D
    AXIS_MOUSEYOFFSET = AXIS_MARGINBOTTOM + (0 if AXIS_INSIDE else AXIS_LINE)

    def __init__(self, parent, spectrumDisplay=None, mainWindow=None, antiAlias=4, drawRightAxis=False, drawBottomAxis=False,
                 fullHeightRightAxis=False, fullWidthBottomAxis=False):

        # add a flag so that scaling cannot be done until the gl attributes are initialised
        self.glReady = False

        super().__init__(parent)

        # GST add antiAliasing, no perceptible speed impact on my mac (intel iris graphics!)
        # samples = 4 is good enough but 8 also works well in terms of speed...
        try:
            fmt = QtGui.QSurfaceFormat()
            fmt.setSamples(antiAlias)
            self.setFormat(fmt)

            samples = self.format().samples()  # GST a use for the walrus
            if samples != antiAlias:
                getLogger().warning('hardware changed antialias level, expected %i got %i...' % (samples, antiAlias))
        except Exception as es:
            getLogger().warning('error during anti aliasing setup %s, anti aliasing disabled...' % str(es))

        # flag to display paintGL but keep an empty screen
        self._blankDisplay = False
        self.setAutoFillBackground(False)

        if not spectrumDisplay:  # don't initialise if nothing there
            return

        self.spectrumDisplay = spectrumDisplay

        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
        else:
            self.application = None
            self.project = None
            self.current = None

        self._preferences = self.application.preferences.general
        self.globalGL = None

        self.setMouseTracking(True)  # generate mouse events when button not pressed

        # always respond to mouse events
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        self._drawRightAxis = drawRightAxis
        self._drawBottomAxis = drawBottomAxis
        self._fullHeightRightAxis = fullHeightRightAxis
        self._fullWidthBottomAxis = fullWidthBottomAxis

        # initialise all attributes
        self._initialiseAll()

        # set a minimum size so that the strips resize nicely
        self.setMinimumSize(self.AXIS_MARGINRIGHT + 10, self.AXIS_MARGINBOTTOM + 10)
        # if drawRightAxis:
        #     self.setMinimumSize(self.AXIS_MARGINRIGHT + 10, STRIP_MINIMUMHEIGHT)
        # else:
        #     self.setMinimumSize(STRIP_MINIMUMWIDTH, self.AXIS_MARGINBOTTOM + 10)

        # initialise the pyqtsignal notifier
        self.GLSignals = GLNotifier(parent=self, strip=None)

        # # set the pyqtsignal responders
        # self.GLSignals.glXAxisChanged.connect(self._glXAxisChanged)
        # self.GLSignals.glYAxisChanged.connect(self._glYAxisChanged)
        # self.GLSignals.glAllAxesChanged.connect(self._glAllAxesChanged)
        # self.GLSignals.glMouseMoved.connect(self._glMouseMoved)
        # self.GLSignals.glEvent.connect(self._glEvent)
        self.GLSignals.glAxisLockChanged.connect(self._glAxisLockChanged)
        # self.GLSignals.glAxisUnitsChanged.connect(self._glAxisUnitsChanged)

        self.lastPixelRatio = None
        # self.setFixedWidth(self.AXIS_MARGINRIGHT+self.AXIS_LINE)

    @property
    def tilePosition(self) -> Tuple[int, int]:
        """Returns a tuple of the tile coordinates (from top-left)
        tilePosition = (x, y)
        """
        if self.spectrumDisplay.stripArrangement == 'Y':
            return self._tilePosition
        else:
            # return the flipped position
            return (self._tilePosition[1], self._tilePosition[0])

    @tilePosition.setter
    def tilePosition(self, value):
        """Setter for tilePosition
        tilePosition must be a tuple of int (x, y)
        """
        if not isinstance(value, tuple):
            raise ValueError('Expected a tuple for tilePosition')
        if len(value) != 2:
            raise ValueError('Tuple must be (x, y)')
        if any(type(vv) != int for vv in value):
            raise ValueError('Tuple must be of type int')

        self._tilePosition = value

    def setAxisType(self, dimension):
        """Set the current axis type for the axis widget
        0 = X Axis type, 1 = Y Axis type
        Only the required axis is drawn and the widget dimensions are fixed in the other axis
        """
        _axisList = (GLDefs.BOTTOMAXIS, GLDefs.RIGHTAXIS)

        if type(dimension) != int:
            raise TypeError('dimension must be an int')
        if not (0 <= dimension < 2):
            raise TypeError('dimension is out of range')

        self._axisType = _axisList[dimension]
        if dimension == 1:
            self.setFixedWidth(self.AXIS_MARGINRIGHT + (0 if self.AXIS_INSIDE else self.AXIS_LINE))
            self.setMinimumHeight(STRIP_MINIMUMHEIGHT)
        else:
            self.setFixedHeight(self.AXIS_MARGINBOTTOM + (0 if self.AXIS_INSIDE else self.AXIS_LINE))
            self.setMinimumWidth(STRIP_MINIMUMWIDTH)

    def getSmallFont(self, transparent=False):
        # GST tried this, it wrong sometimes, also sometimes its a float?
        scale = self.viewports.devicePixelRatio
        size = self.globalGL.glSmallFontSize

        _font = list(self.globalGL.fonts.values())[0].closestFont(size * scale)

        if not (0.9999 < scale < 1.0001):
            _font.charHeight = _font.height / scale
            _font.charWidth = _font.width / scale

        return _font

    def paintGL(self):
        """Handle the GL painting
        """
        if self._blankDisplay:
            return

        if self.spectrumDisplay.isDeleted:
            return

        # NOTE:ED - testing, remove later
        self._paintMode = PaintModes.PAINT_ALL

        if self._paintMode == PaintModes.PAINT_NONE:

            # do nothing
            pass

        elif (self._paintMode == PaintModes.PAINT_ALL) or self._leavingWidget:

            # check whether the visible spectra list needs updating
            if self._visibleSpectrumViewsChange:
                self._visibleSpectrumViewsChange = False
                self._updateVisibleSpectrumViews()

            # if there are no spectra then skip the paintGL event
            if not self._ordering:
                return

            with self.glBlocking():
                # simple profile of building all
                self._buildGL()
                self._paintGL()

            # make all following paint events into mouse only
            # so only paints a single frame from an update event
            self._paintMode = PaintModes.PAINT_MOUSEONLY
            self._paintLastFrame = True
            self._leavingWidget = False

        elif self._paintMode == PaintModes.PAINT_MOUSEONLY:
            self._paintLastFrame = False
            self._leavingWidget = False

            # only need to paint the mouse cursor
            self._paintGLMouseOnly()

    @contextmanager
    def glBlocking(self):
        try:
            # stop notifiers and logging interfering with paint event
            self.project.blankNotification()
            self.application._increaseNotificationBlocking()

            yield

        finally:
            # re-enable notifiers
            self.application._decreaseNotificationBlocking()
            self.project.unblankNotification()

    def _round_sig(self, x, sig=6, small_value=1.0e-9):
        try:
            return 0 if x == 0 else round(x, sig - int(math.floor(math.log10(max(abs(x), abs(small_value))))) - 1)
        except ValueError as es:
            return 0

    def between(self, val, l, r):
        return (l - val) * (r - val) <= 0

    def _floatFormat(self, f=0.0, prec=3):
        """return a float string, remove trailing zeros after decimal
        """
        return (('%.' + str(prec) + 'f') % f).rstrip('0').rstrip('.')

    def _intFormat(self, ii=0, prec=0):
        """return an integer string
        """
        return self._floatFormat(ii, 1)
        # return '%i' % ii

    def _eFormat(self, f=0.0, prec=4):
        """return an exponential with trailing zeroes removed
        """
        s = '%.*e' % (prec, f)
        if 'e' in s:
            mantissa, exp = s.split('e')
            mantissa = mantissa.rstrip('0')
            if mantissa.endswith('.'):
                mantissa += '0'
            exp = exp.lstrip('0+')
            if exp:
                if exp.startswith('-'):
                    return '%se%d' % (mantissa, int(exp))
                else:
                    return '%se+%d' % (mantissa, int(exp))
            else:
                return '%s' % mantissa

        else:
            return ''

    def _buildAxes(self, gridGLList, axisList=None, scaleGrid=None, r=0.0, g=0.0, b=0.0, transparency=256.0,
                   _includeDiagonal=False, _diagonalList=None, _includeAxis=True):
        """Build the grid
        """

        def getDigit(ll, order):
            ss = '{0:.1f}'.format(ll[3] / order)
            valLen = len(ss)
            return ss[valLen - 3]

        def getDigitLen(ll, order):
            ss = '{0:.1f}'.format(ll[3] / order)
            return len(ss)

        def check(ll):
            # check if a number ends in an even digit
            val = '%.0f' % (ll[3] / ll[4])
            valLen = len(val)
            if val[valLen - 1] in '02468':
                return True

        def valueToRatio(val, x0, x1):
            return (val - x0) / (x1 - x0)

        labelling = {'0': {}, '1': {}}
        axesChanged = False
        _minPow = None
        _minOrder = None
        _minSet = False
        _labelRestrictList = ('0123456789', '0258', '05', '0')

        # check if the width is too small to draw too many grid levels
        boundX = (self.w - self.AXIS_MARGINRIGHT) if self._drawRightAxis else self.w
        boundY = (self.h - self.AXIS_MOUSEYOFFSET) if self._drawBottomAxis else self.h
        scaleBounds = (boundX, boundY)

        if gridGLList.renderMode == GLRENDERMODE_REBUILD:

            # get the list of visible spectrumViews, or the first in the list
            visibleSpectrumViews = [specView for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
            thisSpecView = visibleSpectrumViews[0] if visibleSpectrumViews else self._ordering[0] if self._ordering and not self._ordering[
                0].isDeleted else None

            if thisSpecView:
                thisSpec = thisSpecView.spectrum

                # generate different axes depending on units - X Axis
                if self.XAXES[self._xUnits] == GLDefs.AXISUNITSPPM:
                    axisLimitL = self.axisL
                    axisLimitR = self.axisR
                    self.XMode = self._floatFormat

                elif self.XAXES[self._xUnits] == GLDefs.AXISUNITSHZ:
                    if self._ordering:

                        if self.is1D:
                            axisLimitL = self.axisL * thisSpec.spectrometerFrequencies[0]
                            axisLimitR = self.axisR * thisSpec.spectrometerFrequencies[0]

                        else:
                            # get the axis ordering from the spectrumDisplay and map to the strip
                            indices = self._spectrumSettings[thisSpecView][GLDefs.SPECTRUM_POINTINDEX]
                            axisLimitL = self.axisL * thisSpec.spectrometerFrequencies[indices[0]]
                            axisLimitR = self.axisR * thisSpec.spectrometerFrequencies[indices[0]]

                    else:
                        # error trap all spectra deleted
                        axisLimitL = self.axisL
                        axisLimitR = self.axisR
                    self.XMode = self._floatFormat

                else:
                    if self._ordering:

                        if self.is1D:
                            axisLimitL = thisSpec.mainSpectrumReferences[0].valueToPoint(self.axisL)
                            axisLimitR = thisSpec.mainSpectrumReferences[0].valueToPoint(self.axisR)

                        else:
                            # get the axis ordering from the spectrumDisplay and map to the strip
                            indices = self._spectrumSettings[thisSpecView][GLDefs.SPECTRUM_POINTINDEX]

                            # map to a point
                            axisLimitL = thisSpec.mainSpectrumReferences[indices[0]].valueToPoint(self.axisL)
                            axisLimitR = thisSpec.mainSpectrumReferences[indices[0]].valueToPoint(self.axisR)

                    else:
                        # error trap all spectra deleted
                        axisLimitL = self.axisL
                        axisLimitR = self.axisR
                    self.XMode = self._intFormat

                # generate different axes depending on units - Y Axis, always use first option for 1d
                if self.is1D:
                    axisLimitT = self.axisT
                    axisLimitB = self.axisB
                    self.YMode = self._eFormat  # '%.6g'

                elif self.YAXES[self._yUnits] == GLDefs.AXISUNITSPPM:
                    axisLimitT = self.axisT
                    axisLimitB = self.axisB
                    self.YMode = self._floatFormat  # '%.3f'

                elif self.YAXES[self._yUnits] == GLDefs.AXISUNITSHZ:
                    if self._ordering:

                        # get the axis ordering from the spectrumDisplay and map to the strip
                        indices = self._spectrumSettings[thisSpecView][GLDefs.SPECTRUM_POINTINDEX]
                        axisLimitT = self.axisT * thisSpec.spectrometerFrequencies[indices[1]]
                        axisLimitB = self.axisB * thisSpec.spectrometerFrequencies[indices[1]]

                    else:
                        # error trap all spectra deleted
                        axisLimitT = self.axisT
                        axisLimitB = self.axisB
                    self.YMode = self._floatFormat  # '%.3f'

                else:
                    if self._ordering:

                        # get the axis ordering from the spectrumDisplay and map to the strip
                        indices = self._spectrumSettings[thisSpecView][GLDefs.SPECTRUM_POINTINDEX]

                        # map to a point
                        axisLimitT = thisSpec.mainSpectrumReferences[indices[1]].valueToPoint(self.axisT)
                        axisLimitB = thisSpec.mainSpectrumReferences[indices[1]].valueToPoint(self.axisB)

                    else:
                        # error trap all spectra deleted
                        axisLimitT = self.axisT
                        axisLimitB = self.axisB
                    self.YMode = self._intFormat  # '%i'

                # ul = np.array([min(self.axisL, self.axisR), min(self.axisT, self.axisB)])
                # br = np.array([max(self.axisL, self.axisR), max(self.axisT, self.axisB)])

                minX = min(axisLimitL, axisLimitR)
                maxX = max(axisLimitL, axisLimitR)
                minY = min(axisLimitT, axisLimitB)
                maxY = max(axisLimitT, axisLimitB)
                ul = np.array([minX, minY])
                br = np.array([maxX, maxY])

                gridGLList.renderMode = GLRENDERMODE_DRAW
                axesChanged = True

                gridGLList.clearArrays()

                vertexList = ()
                indexList = ()
                colorList = ()

                index = 0
                for scaleOrder, i in enumerate(scaleGrid):  #  [2,1,0]:   ## Draw three different scales of grid
                    dist = br - ul
                    nlTarget = 10. ** i
                    _pow = np.log10(abs(dist / nlTarget)) + 0.5
                    d = 10. ** np.floor(_pow)

                    ul1 = np.floor(ul / d) * d
                    br1 = np.ceil(br / d) * d
                    dist = br1 - ul1
                    nl = (dist / d) + 0.5

                    _minPow = np.floor(_pow) if _minPow is None else np.minimum(_minPow, np.floor(_pow))
                    _minOrder = d if _minOrder is None else np.minimum(_minOrder, d)
                    for ax in axisList:  #   range(0,2):  ## Draw grid for both axes

                        c = 30.0 + (scaleOrder * 20)
                        bx = (ax + 1) % 2

                        for x in range(0, int(nl[ax])):
                            p1 = np.array([0., 0.])
                            p2 = np.array([0., 0.])
                            p1[ax] = ul1[ax] + x * d[ax]
                            p2[ax] = p1[ax]
                            p1[bx] = ul[bx]
                            p2[bx] = br[bx]
                            if p1[ax] < min(ul[ax], br[ax]) or p1[ax] > max(ul[ax], br[ax]):
                                continue

                            if i == 1:  # should be largest scale grid
                                d[0] = self._round_sig(d[0], sig=4)
                                d[1] = self._round_sig(d[1], sig=4)

                                if ax == 0:
                                    includeGrid = not (self.XMode == self._intFormat and d[0] < 1 and abs(p1[0] - int(p1[0])) > d[0] / 2.0)
                                else:
                                    includeGrid = not (self.YMode == self._intFormat and d[1] < 1 and abs(p1[1] - int(p1[1])) > d[1] / 2.0)

                                if includeGrid:
                                    if '%.5f' % p1[0] == '%.5f' % p2[0]:  # check whether a vertical line - x axis
                                        pp = self._round_sig(p1[0], sig=10)

                                        # xLabel = str(int(p1[0])) if d[0] >=1 else self.XMode % p1[0]
                                        labelling[str(ax)][pp] = ((i, ax, valueToRatio(p1[0], axisLimitL, axisLimitR),
                                                                   pp, d[0]))
                                    else:
                                        pp = self._round_sig(p1[1], sig=10)

                                        # num = int(p1[1]) if d[1] >=1 else self.XMode % p1[1]
                                        labelling[str(ax)][pp] = ((i, ax, valueToRatio(p1[1], axisLimitB, axisLimitT),
                                                                   pp, d[1]))

                                    # append the new points to the end of nparray, ignoring narrow grids
                                    if scaleBounds[ax] * (scaleOrder + 1) > 225:
                                        indexList += (index, index + 1)
                                        vertexList += (valueToRatio(p1[0], axisLimitL, axisLimitR),
                                                       valueToRatio(p1[1], axisLimitB, axisLimitT),
                                                       valueToRatio(p2[0], axisLimitL, axisLimitR),
                                                       valueToRatio(p2[1], axisLimitB, axisLimitT))

                                        alpha = min([1.0, c / transparency])
                                        colorList += (r, g, b, alpha, r, g, b, alpha)

                                        gridGLList.numVertices += 2
                                        index += 2

                # add the extra axis lines
                if _includeAxis:
                    for ax in axisList:

                        offset = GLDefs.AXISDRAWOFFSET if self.AXIS_INSIDE else (1 - GLDefs.AXISDRAWOFFSET)
                        if ax == 0:
                            # add the x axis line
                            indexList += (index, index + 1)
                            vertexList += (0.0, offset, 1.0, offset)
                            colorList += (r, g, b, 1.0, r, g, b, 1.0)
                            gridGLList.numVertices += 2
                            index += 2

                        elif ax == 1:
                            # add the y axis line
                            indexList += (index, index + 1)
                            vertexList += (1.0 - offset, 0.0, 1.0 - offset, 1.0)
                            colorList += (r, g, b, 1.0, r, g, b, 1.0)
                            gridGLList.numVertices += 2
                            index += 2

                # copy the arrays the the GLstore
                gridGLList.vertices = np.array(vertexList, dtype=np.float32)
                gridGLList.indices = np.array(indexList, dtype=np.uint32)
                gridGLList.colors = np.array(colorList, dtype=np.float32)

                # restrict the labelling to the maximum without overlap based on width
                # should be dependent on font size though
                _maxChars = 1
                for k, val in list(labelling['0'].items()):
                    _maxChars = max(_maxChars, getDigitLen(val, _minOrder[0]))
                _width = self.w / (7.0 * _maxChars)  # num of columns
                restrictList = 0
                ll = len(labelling['0'])
                while ll > _width and restrictList < 3:
                    ll /= 2
                    restrictList += 1
                for k, val in list(labelling['0'].items()):
                    if getDigit(val, _minOrder[0]) not in _labelRestrictList[restrictList]:
                        # remove the item
                        del labelling['0'][k]

                _height = self.h / 15.0  # num of rows
                restrictList = 0
                ll = len(labelling['1'])
                while ll > _height and restrictList < 3:
                    ll /= 2
                    restrictList += 1
                for k, val in list(labelling['1'].items()):
                    if getDigit(val, _minOrder[1]) not in _labelRestrictList[restrictList]:
                        # remove the item
                        del labelling['1'][k]

        return labelling, axesChanged

    def buildGrid(self):
        """Build the grids for the mainGrid and the bottom/right axes
        """
        # build the axes
        if self.highlighted:
            if self._axisType == GLDefs.RIGHTAXIS:
                self.axisLabelling, self.axesChanged = self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1, 0],
                                                                       r=self.highlightColour[0],
                                                                       g=self.highlightColour[1],
                                                                       b=self.highlightColour[2], transparency=32.0)
            else:  # self._axisType == GLDefs.BOTTOMAXIS:
                self.axisLabelling, self.axesChanged = self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1, 0],
                                                                       r=self.highlightColour[0],
                                                                       g=self.highlightColour[1],
                                                                       b=self.highlightColour[2], transparency=32.0)
        else:
            if self._axisType == GLDefs.RIGHTAXIS:
                self.axisLabelling, self.axesChanged = self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1, 0],
                                                                       r=self.foreground[0],
                                                                       g=self.foreground[1],
                                                                       b=self.foreground[2], transparency=32.0)
            else:  # self._axisType == GLDefs.BOTTOMAXIS:
                self.axisLabelling, self.axesChanged = self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1, 0],
                                                                       r=self.foreground[0],
                                                                       g=self.foreground[1],
                                                                       b=self.foreground[2], transparency=32.0)

        # buffer the lists to VBOs
        for gr in self.gridList[1:]:
            gr.defineIndexVBO()

    def drawGrid(self):
        # set to the mainView and draw the grid
        # self.buildGrid()

        GL.glEnable(GL.GL_BLEND)
        GL.glLineWidth(GLDefs.GLDEFAULTLINETHICKNESS * self.viewports.devicePixelRatio)

        # draw the axes tick marks (effectively the same grid in smaller viewport)
        if self._axesVisible:
            if self._drawRightAxis and self._axisType == GLDefs.RIGHTAXIS:
                # draw the grid marks for the right axis
                self.viewports.setViewport(self._currentRightAxisView)
                self.gridList[1].drawIndexVBO()

            if self._drawBottomAxis and self._axisType == GLDefs.BOTTOMAXIS:
                # draw the grid marks for the bottom axis
                self.viewports.setViewport(self._currentBottomAxisView)
                self.gridList[2].drawIndexVBO()

    @contextmanager
    def _disableGLAliasing(self):
        """Disable aliasing for the contained routines
        """
        try:
            GL.glDisable(GL.GL_MULTISAMPLE)
            yield
        finally:
            GL.glEnable(GL.GL_MULTISAMPLE)

    @contextmanager
    def _enableGLAliasing(self):
        """Enable aliasing for the contained routines
        """
        try:
            GL.glEnable(GL.GL_MULTISAMPLE)
            yield
        finally:
            GL.glDisable(GL.GL_MULTISAMPLE)

    def _buildSpectrumSetting(self, spectrumView, stackCount=0):
        # if spectrumView.spectrum.headerSize == 0:
        #     return

        self._spectrumSettings[spectrumView] = {}

        self._spectrumValues = spectrumView.getVisibleState()

        # set defaults for undefined spectra
        if not self._spectrumValues[0].pointCount:
            dx = -1.0 if self.INVERTXAXIS else -1.0
            fxMax, fxMin = 1.0, -1.0
            dxAF = fxMax - fxMin
            xScale = dx * dxAF

            dy = -1.0 if self.INVERTYAXIS else -1.0
            fyMax, fyMin = 1.0, -1.0
            dyAF = fyMax - fyMin
            yScale = dy * dyAF
            # xAliasingIndex = (0, 0)
            # yAliasingIndex = (0, 0)
            # xFoldingMode = yFoldingMode = None

            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fxMax - fxMin))
            self._maxXRange = max(self._maxXRange, (fxMax - fxMin))
            self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * (fyMax - fyMin))
            self._maxYRange = max(self._maxYRange, (fyMax - fyMin))

        else:

            # get the bounding box of the spectra
            dx = -1.0 if self.INVERTXAXIS else -1.0  # self.sign(self.axisR - self.axisL)
            fxMax, fxMin = self._spectrumValues[0].maxSpectrumFrequency, self._spectrumValues[0].minSpectrumFrequency
            # xAliasingIndex = self._spectrumValues[0].aliasingIndex
            # xFoldingMode = self._spectrumValues[0].foldingMode

            # check tolerances
            if not self._widthsChangedEnough((fxMax, 0.0), (fxMin, 0.0), tol=1e-10):
                fxMax, fxMin = 1.0, -1.0

            dxAF = fxMax - fxMin
            xScale = dx * dxAF / self._spectrumValues[0].pointCount

            dy = -1.0 if self.INVERTYAXIS else -1.0  # dy = self.sign(self.axisT - self.axisB)

            if spectrumView.spectrum.intensities is not None and spectrumView.spectrum.intensities.size != 0:
                fyMax = float(np.max(spectrumView.spectrum.intensities))
                fyMin = float(np.min(spectrumView.spectrum.intensities))
            else:
                fyMax, fyMin = 0.0, 0.0
            # yAliasingIndex = (0, 0)
            # yFoldingMode = None

            # check tolerances
            if not self._widthsChangedEnough((fyMax, 0.0), (fyMin, 0.0), tol=1e-10):
                fyMax, fyMin = 1.0, -1.0

            dyAF = fyMax - fyMin
            yScale = dy * dyAF / 1.0

            # set to 1D limits to twice the width of the spectrum and the intensity limit
            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fxMax - fxMin) / max(self._spectrumValues[0].pointCount, self.SPECTRUMXZOOM))
            self._maxXRange = max(self._maxXRange, (fxMax - fxMin))
            # self._minYRange = min(self._minYRange, 3.0 * (fyMax - fyMin) / self.SPECTRUMYZOOM)
            self._minYRange = min(self._minYRange, self._intensityLimit)
            self._maxYRange = max(self._maxYRange, (fyMax - fyMin))

            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIX] = np.zeros((16,), dtype=np.float32)

            # if self._stackingMode:
            stX = stackCount * self._stackingValue[0]
            stY = stackCount * self._stackingValue[1]
            # stackCount += 1
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIX][0:16] = [1.0, 0.0, 0.0, 0.0,
                                                                                         0.0, 1.0, 0.0, 0.0,
                                                                                         0.0, 0.0, 1.0, 0.0,
                                                                                         stX, stY, 0.0, 1.0]
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIXOFFSET] = np.array((stX, stY), dtype=np.float32)

        self._rangeXDefined = True
        self._rangeYDefined = True

        # create modelview matrix for the spectrum to be drawn
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX] = np.zeros((16,), dtype=np.float32)

        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX][0:16] = [xScale, 0.0, 0.0, 0.0,
                                                                              0.0, yScale, 0.0, 0.0,
                                                                              0.0, 0.0, 1.0, 0.0,
                                                                              fxMax, fyMax, 0.0, 1.0]
        # setup information for the horizontal/vertical traces
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_XLIMITS] = (fxMin, fxMax)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_YLIMITS] = (fyMin, fyMax)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_AF] = (dxAF, dyAF)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_SCALE] = (xScale, yScale)
        # self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_SPINNINGRATE] = spectrumView.spectrum.spinningRate
        # self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_ALIASINGINDEX] = (xAliasingIndex, yAliasingIndex)
        # self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_FOLDINGMODE] = (xFoldingMode, yFoldingMode)

        indices = getAxisCodeMatchIndices(self.spectrumDisplay.axisCodes, spectrumView.spectrum.axisCodes)
        # only need the axes for this spectrum
        indices = indices[:spectrumView.spectrum.dimensionCount]
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX] = indices
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = None
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_REGIONBOUNDS] = (self._spectrumValues[0].regionBounds, 0)

        self._maxX = max(self._maxX, fxMax)
        self._minX = min(self._minX, fxMin)
        self._maxY = max(self._maxY, fyMax)
        self._minY = min(self._minY, fyMin)

        self._buildAxisCodesWithWildCards()

    def buildSpectra(self):
        if self.spectrumDisplay.isDeleted:
            return

        # self._spectrumSettings = {}
        rebuildFlag = False
        for spectrumView in self._ordering:  # strip.spectrumViews:
            if spectrumView.isDeleted:
                continue

            self._buildSpectrumSetting(spectrumView=spectrumView)
            rebuildFlag = True

    def _buildGL(self):
        """Separate the building of the display from the paint event; not sure that this is required
        """
        # only call if the axes have changed
        # self._updateAxes = True

        # if abs(self.axisL - self.axisR) < 1e-9 or abs(self.axisT - self.axisB) < 1e-9:
        #     return

        if self._updateAxes:
            self.buildGrid()
            self._updateAxes = False

        self.buildSpectra()

    def _paintGLMouseOnly(self):
        """paintGL event - paint only the mouse in Xor mode
        """
        # No mouse cursor
        pass

    def _paintGL(self):
        w = self.w
        h = self.h

        if self._updateBackgroundColour:
            self._updateBackgroundColour = False
            self.setBackgroundColour(self.background, silent=True)

        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glEnable(GL.GL_MULTISAMPLE)

        currentShader = self.globalGL._shaderProgram1.makeCurrent()

        # start with the grid mapped to (0..1, 0..1) to remove zoom errors here
        currentShader.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0.0, 1.0, -1.0, 1.0)
        currentShader.setPMatrix(self._uPMatrix)

        with self._disableGLAliasing():
            # draw the grid components
            self.drawGrid()

        currentShader = self.globalGL._shaderProgramTex.makeCurrent()

        self._axisScale[0:4] = [self.pixelX, self.pixelY, 1.0, 1.0]
        currentShader.setAxisScale(self._axisScale)

        # draw the text to the screen
        self.enableTexture()
        self.enableTextClientState()
        self._setViewPortFontScale()

        # make the overlay/axis solid
        currentShader.setBlendEnabled(False)
        self.drawAxisLabels()
        currentShader.setBlendEnabled(True)

        self.disableTextClientState()
        self.disableTexture()

    def _initialiseAll(self):
        """Initialise all attributes for the display
        """
        # if self.glReady: return

        self.w = self.width()
        self.h = self.height()

        self._threads = {}
        self._threadUpdate = False

        self.lastPos = QtCore.QPoint()
        self._mouseX = 0
        self._mouseY = 0
        self._mouseStart = (0.0, 0.0)
        self._mouseEnd = (0.0, 0.0)

        self.pixelX = 1.0
        self.pixelY = 1.0
        self.deltaX = 1.0
        self.deltaY = 1.0
        self.symbolX = 1.0
        self.symbolY = 1.0

        self.peakWidthPixels = 16

        # set initial axis limits - should be changed by strip.display..
        self.axisL = -1.0
        self.axisR = 1.0
        self.axisT = 1.0
        self.axisB = -1.0
        self.storedZooms = []
        self._currentZoom = 0
        self._zoomHistory = [None] * ZOOMHISTORYSTORE
        self._zoomHistoryCurrent = 0
        self._zoomHistoryHead = 0
        self._zoomTimerLast = time.time()

        self.base = None
        self.spectrumValues = []

        self.highlighted = False
        self._drawSelectionBox = False
        self._drawMouseMoveLine = False
        self._drawDeltaOffset = False
        self._selectionMode = 0
        self._startCoordinate = None
        self._endCoordinate = None
        self.cursorSource = CURSOR_SOURCE_NONE  # can be CURSOR_SOURCE_NONE / CURSOR_SOURCE_SELF / CURSOR_SOURCE_OTHER
        self.cursorCoordinate = np.zeros((4,), dtype=np.float32)
        self.doubleCursorCoordinate = np.zeros((4,), dtype=np.float32)

        self._shift = False
        self._command = False
        self._key = ''
        self._isSHIFT = ''
        self._isCTRL = ''
        self._isALT = ''
        self._isMETA = ''

        self._lastClick = None
        self._mousePressed = False
        self._draggingLabel = False

        self.buildMarks = True
        self._marksList = None
        self._infiniteLines = []
        self._regionList = None
        self._orderedAxes = None
        self._axisOrder = None
        self._axisCodes = None
        self._refreshMouse = False
        self._successiveClicks = None  # GWV: Store successive click events for zooming; None means first click not set
        self._dottedCursorCoordinate = None
        self._dottedCursorVisible = None
        self._spectrumBordersVisible = True

        self.gridList = []
        self._gridVisible = True  #self._preferences.showGrid
        self._crosshairVisible = True  #self._preferences.showCrosshair
        self._doubleCrosshairVisible = True  #self._preferences.showDoubleCrosshair
        self._sideBandsVisible = True

        self.diagonalGLList = None
        self.diagonalSideBandsGLList = None
        self.boundingBoxes = None
        self._updateAxes = True
        self.axesChanged = False
        self.axisLabelling = {'0': [], '1': []}

        self._axesVisible = True
        self._aspectRatioMode = 0
        self._aspectRatios = {}

        self._fixedAspectX = 1.0
        self._fixedAspectY = 1.0

        self._showSpectraOnPhasing = False
        self._xUnits = 0
        self._yUnits = 0
        self.modeDecimal = [False, False]

        # here for completeness, although they should be updated in rescale
        self._currentView = None
        self._currentRightAxisView = GLDefs.RIGHTAXIS
        self._currentRightAxisBarView = GLDefs.RIGHTAXISBAR
        self._currentBottomAxisView = GLDefs.BOTTOMAXIS
        self._currentBottomAxisBarView = GLDefs.BOTTOMAXISBAR

        self._oldStripIDLabel = None
        self.stripIDString = None
        self._spectrumSettings = {}
        self._newStripID = False

        self._setColourScheme()

        self._updateHTrace = False
        self._updateVTrace = False
        self._lastTracePoint = {}  # [-1, -1]
        self.showActivePhaseTrace = True

        self._applyXLimit = True  #.zoomXLimitApply
        self._applyYLimit = True  #self._preferences.zoomYLimitApply
        self._intensityLimit = True  #self._preferences.intensityLimit

        self._GLIntegralLists = {}
        self._GLIntegralLabels = {}

        self._marksAxisCodes = []

        self._regions = []
        self._infiniteLines = []
        self._buildTextFlag = True

        self._buildMouse = True
        self._mouseCoords = [-1.0, -1.0]
        self.mouseString = None
        # self.diffMouseString = None
        self._symbolLabelling = 0
        self._symbolType = 0
        self._symbolSize = 0
        self._symbolThickness = 0
        self._aliasEnabled = True
        self._aliasShade = 0.0
        self._aliasLabelsEnabled = True
        self._contourThickness = 0

        self._contourList = {}
        self._hTraces = {}
        self._vTraces = {}
        self._staticHTraces = []
        self._staticVTraces = []
        self._currentTraces = []
        self._axisXLabelling = []
        self._axisYLabelling = []
        self._axisScaleLabelling = []
        self._axisType = GLDefs.BOTTOMAXIS

        self._stackingValue = (0.0, 0.0)
        self._stackingMode = False
        self._hTraceVisible = False
        self._vTraceVisible = False
        self.w = 0
        self.h = 0

        self._uPMatrix = np.zeros((16,), dtype=np.float32)
        self._uMVMatrix = np.zeros((16,), dtype=np.float32)
        self._uVMatrix = np.zeros((16,), dtype=np.float32)
        self._dataMatrix = np.zeros((16,), dtype=np.float32)
        self._aMatrix = np.zeros((16,), dtype=np.float32)
        self._IMatrix = np.zeros((16,), dtype=np.float32)
        self._IMatrix[0:16] = [1.0, 0.0, 0.0, 0.0,
                               0.0, 1.0, 0.0, 0.0,
                               0.0, 0.0, 1.0, 0.0,
                               0.0, 0.0, 0.0, 1.0]

        self.vInv = None
        self.mouseTransform = None

        self._useTexture = np.zeros((1,), dtype=np.int)
        self._axisScale = np.zeros((4,), dtype=np.float32)
        self._background = np.zeros((4,), dtype=np.float32)
        self._parameterList = np.zeros((4,), dtype=np.int32)
        # self._view = np.zeros((4,), dtype=np.float32)
        self._updateBackgroundColour = True

        # get information from the parent class (strip)
        # self.orderedAxes = self.spectrumDisplay.orderedAxes
        self.axisOrder = self.spectrumDisplay.axisOrder
        self.axisCodes = self.spectrumDisplay.axisCodes

        self._dragRegions = set()

        self.resetRangeLimits()

        self._ordering = []
        self._visibleOrdering = []
        self._firstVisible = None
        self.visiblePlaneList = {}
        self.visiblePlaneListPointValues = {}
        self.visiblePlaneDimIndices = {}
        self._visibleSpectrumViewsChange = False
        self._matchingIsotopeCodes = False

        self._menuActive = False

    def _setColourScheme(self):
        """Update colours from colourScheme
        """
        self.colours = getColours()
        self.hexBackground = self.colours[CCPNGLWIDGET_HEXBACKGROUND]
        self.background = self.colours[CCPNGLWIDGET_BACKGROUND]
        self.foreground = self.colours[CCPNGLWIDGET_FOREGROUND]
        self.mousePickColour = self.colours[CCPNGLWIDGET_PICKCOLOUR]
        self.gridColour = self.colours[CCPNGLWIDGET_GRID]
        self.highlightColour = self.colours[CCPNGLWIDGET_HIGHLIGHT]
        self._labellingColour = self.colours[CCPNGLWIDGET_LABELLING]
        self._phasingTraceColour = self.colours[CCPNGLWIDGET_PHASETRACE]

        self.zoomAreaColour = self.colours[CCPNGLWIDGET_ZOOMAREA]
        self.pickAreaColour = self.colours[CCPNGLWIDGET_PICKAREA]
        self.selectAreaColour = self.colours[CCPNGLWIDGET_SELECTAREA]
        self.zoomLineColour = self.colours[CCPNGLWIDGET_ZOOMLINE]
        self.mouseMoveLineColour = self.colours[CCPNGLWIDGET_MOUSEMOVELINE]

        self.zoomAreaColourHard = (*self.colours[CCPNGLWIDGET_ZOOMAREA][0:3], CCPNGLWIDGET_HARDSHADE)
        self.pickAreaColourHard = (*self.colours[CCPNGLWIDGET_PICKAREA][0:3], CCPNGLWIDGET_HARDSHADE)
        self.selectAreaColourHard = (*self.colours[CCPNGLWIDGET_SELECTAREA][0:3], CCPNGLWIDGET_HARDSHADE)

    def resetRangeLimits(self, allLimits=True):
        # reset zoom limits for the display
        self._minXRange, self._maxXRange = GLDefs.RANGELIMITS
        self._minYRange, self._maxYRange = GLDefs.RANGELIMITS
        self._maxX, self._minX = GLDefs.AXISLIMITS
        self._maxY, self._minY = GLDefs.AXISLIMITS
        if allLimits:
            self._rangeXDefined = False
            self._rangeYDefined = False
            self._minXReached = False
            self._minYReached = False
            self._maxXReached = False
            self._maxYReached = False

            self._minReached = False
            self._maxReached = False

    @pyqtSlot(dict)
    def _glXAxisChanged(self, aDict):
        if self._aspectRatioMode:
            self._glAllAxesChanged(aDict)
            return

        if self.spectrumDisplay.isDeleted:
            return

        sDisplay = aDict[GLNotifier.GLSPECTRUMDISPLAY]
        source = aDict[GLNotifier.GLSOURCE]

        if source != self and sDisplay == self.spectrumDisplay:

            # match only the scale for the X axis
            axisL = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLLEFTAXISVALUE]
            axisR = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLRIGHTAXISVALUE]
            row = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPROW]
            col = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPCOLUMN]

            if any(val is None for val in (axisL, axisR, row, col)):
                return

            tilePos = self.tilePosition

            if self._widthsChangedEnough([axisL, self.axisL], [axisR, self.axisR]):
                if self.spectrumDisplay.stripArrangement == 'Y':
                    if tilePos[1] == col:
                        self.axisL = axisL
                        self.axisR = axisR
                    else:
                        diff = (axisR - axisL) / 2.0
                        mid = (self.axisR + self.axisL) / 2.0
                        self.axisL = mid - diff
                        self.axisR = mid + diff

                elif self.spectrumDisplay.stripArrangement == 'X':
                    if tilePos[0] == row:
                        self.axisL = axisL
                        self.axisR = axisR
                    else:
                        diff = (axisR - axisL) / 2.0
                        mid = (self.axisR + self.axisL) / 2.0
                        self.axisL = mid - diff
                        self.axisR = mid + diff
                else:
                    raise
                self._rescaleXAxis()
                # self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glAxisLockChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        try:
            self._parentStrip = self.spectrumDisplay.strips[0]
        except:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:
            self._aspectRatioMode = aDict[GLNotifier.GLVALUES][0]

            if self._aspectRatioMode:

                # check which is the primary axis and update the opposite axis - similar to wheelEvent
                if self.spectrumDisplay.stripArrangement == 'Y':

                    # strips are arranged in a row
                    self._scaleToYAxis()

                elif self.spectrumDisplay.stripArrangement == 'X':

                    # strips are arranged in a column
                    self._scaleToXAxis()

                elif self.spectrumDisplay.stripArrangement == 'T':

                    # NOTE:ED - Tiled plots not fully implemented yet
                    getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

                else:
                    getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

            else:
                # paint to update lock button colours
                self.update()

    @pyqtSlot(dict)
    def _glAxisUnitsChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        # update the list of visible spectra
        self._updateVisibleSpectrumViews()

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # read values from dataDict and set units
            if aDict[GLNotifier.GLVALUES]:  # and aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]:

                self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]
                if GLDefs.AXISASPECTRATIOMODE in aDict[GLNotifier.GLVALUES]:
                    aRM = aDict[GLNotifier.GLVALUES][GLDefs.AXISASPECTRATIOMODE]

                    if self._aspectRatioMode != aRM:
                        self._aspectRatioMode = aRM

                        changeDict = {GLNotifier.GLSOURCE         : None,
                                      GLNotifier.GLSPECTRUMDISPLAY: self.spectrumDisplay,
                                      GLNotifier.GLVALUES         : (aRM,)
                                      }
                        self._glAxisLockChanged(changeDict)

                    if GLDefs.AXISASPECTRATIOS in aDict[GLNotifier.GLVALUES]:
                        self._aspectRatios.update(aDict[GLNotifier.GLVALUES][GLDefs.AXISASPECTRATIOS])
                        if aRM == 2:
                            self._rescaleAllZoom(rescale=True)

            # spawn rebuild event for the grid
            self._updateAxes = True
            if self.gridList:
                for gr in self.gridList:
                    gr.renderMode = GLRENDERMODE_REBUILD
            self.update()

    def _widthsChangedEnough(self, r1, r2, tol=1e-5):
        if len(r1) != len(r2):
            raise ValueError('WidthsChanged must be the same length')

        for ii in zip(r1, r2):
            if abs(ii[0] - ii[1]) > tol:
                return True

    @pyqtSlot(dict)
    def _glYAxisChanged(self, aDict):
        if self._aspectRatioMode:
            self._glAllAxesChanged(aDict)
            return

        if self.spectrumDisplay.isDeleted:
            return

        sDisplay = aDict[GLNotifier.GLSPECTRUMDISPLAY]
        source = aDict[GLNotifier.GLSOURCE]

        if source != self and sDisplay == self.spectrumDisplay:

            # match the Y axis
            axisB = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLBOTTOMAXISVALUE]
            axisT = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLTOPAXISVALUE]
            row = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPROW]
            col = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPCOLUMN]

            if any(val is None for val in (axisB, axisT, row, col)):
                return

            tilePos = self.tilePosition

            if self._widthsChangedEnough([axisB, self.axisB], [axisT, self.axisT]):
                if self.spectrumDisplay.stripArrangement == 'Y':
                    if tilePos[0] == row:
                        self.axisB = axisB
                        self.axisT = axisT
                    else:
                        diff = (axisT - axisB) / 2.0
                        mid = (self.axisT + self.axisB) / 2.0
                        self.axisB = mid - diff
                        self.axisT = mid + diff

                elif self.spectrumDisplay.stripArrangement == 'X':
                    if tilePos[1] == col:
                        self.axisB = axisB
                        self.axisT = axisT
                    else:
                        diff = (axisT - axisB) / 2.0
                        mid = (self.axisT + self.axisB) / 2.0
                        self.axisB = mid - diff
                        self.axisT = mid + diff
                else:
                    raise

                self._rescaleYAxis()
                # self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glAllAxesChanged(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        sDisplay = aDict[GLNotifier.GLSPECTRUMDISPLAY]
        source = aDict[GLNotifier.GLSOURCE]

        if source != self and sDisplay == self.spectrumDisplay:

            # match the values for the Y axis, and scale for the X axis
            axisB = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLBOTTOMAXISVALUE]
            axisT = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLTOPAXISVALUE]
            axisL = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLLEFTAXISVALUE]
            axisR = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLRIGHTAXISVALUE]
            row = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPROW]
            col = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLSTRIPCOLUMN]

            if any(val is None for val in (axisB, axisT, axisL, axisR, row, col)):
                return

            tilePos = self.tilePosition

            if self._widthsChangedEnough([axisB, self.axisB], [axisT, self.axisT]) and \
                    self._widthsChangedEnough([axisL, self.axisL], [axisR, self.axisR]):

                # # do the matching row and column only unless _useLockedAspect or self._useDefaultAspect are set
                # if not (tilePos[0] == row or tilePos[1] == col) and \
                #         not (self._useLockedAspect or self._useDefaultAspect):
                #     return

                if self.spectrumDisplay.stripArrangement == 'Y':

                    # strips are arranged in a row
                    if tilePos[1] == col:
                        self.axisL = axisL
                        self.axisR = axisR
                    elif self._aspectRatioMode:
                        diff = (axisR - axisL) / 2.0
                        mid = (self.axisR + self.axisL) / 2.0
                        self.axisL = mid - diff
                        self.axisR = mid + diff

                    if tilePos[0] == row:
                        self.axisB = axisB
                        self.axisT = axisT
                    elif self._aspectRatioMode:
                        diff = (axisT - axisB) / 2.0
                        mid = (self.axisT + self.axisB) / 2.0
                        self.axisB = mid - diff
                        self.axisT = mid + diff

                elif self.spectrumDisplay.stripArrangement == 'X':

                    # strips are arranged in a column
                    if tilePos[1] == col:
                        self.axisB = axisB
                        self.axisT = axisT
                    elif self._aspectRatioMode:
                        diff = (axisT - axisB) / 2.0
                        mid = (self.axisT + self.axisB) / 2.0
                        self.axisB = mid - diff
                        self.axisT = mid + diff

                    if tilePos[0] == row:
                        self.axisL = axisL
                        self.axisR = axisR
                    elif self._aspectRatioMode:
                        diff = (axisR - axisL) / 2.0
                        mid = (self.axisR + self.axisL) / 2.0
                        self.axisL = mid - diff
                        self.axisR = mid + diff

                elif self.spectrumDisplay.stripArrangement == 'T':

                    # NOTE:ED - Tiled plots not fully implemented yet
                    pass

                else:
                    # currently ignore - warnings will be logged elsewhere
                    pass

                self._rescaleAllAxes()
                # self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glMouseMoved(self, aDict):
        if self.spectrumDisplay.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self:
            # self.cursorCoordinate = aDict[GLMOUSECOORDS]
            # self.update()

            mouseMovedDict = aDict[GLNotifier.GLMOUSEMOVEDDICT]

            if self._crosshairVisible:  # or self._updateVTrace or self._updateHTrace:

                exactMatch = (self._preferences.matchAxisCode == AXIS_FULLATOMNAME)
                indices = getAxisCodeMatchIndices(self.spectrumDisplay.axisCodes[:2], mouseMovedDict[AXIS_ACTIVEAXES], exactMatch=exactMatch)

                for n in range(2):
                    if indices[n] is not None:

                        axis = mouseMovedDict[AXIS_ACTIVEAXES][indices[n]]
                        self.cursorSource = CURSOR_SOURCE_OTHER
                        self.cursorCoordinate[n] = mouseMovedDict[AXIS_FULLATOMNAME][axis]

                        # coordinates have already been flipped
                        self.doubleCursorCoordinate[1 - n] = self.cursorCoordinate[n]

                    else:
                        self.cursorSource = CURSOR_SOURCE_OTHER
                        self.cursorCoordinate[n] = None
                        self.doubleCursorCoordinate[1 - n] = None

                # self.current.cursorPosition = (self.cursorCoordinate[0], self.cursorCoordinate[1])

                # only need to redraw if we can see the cursor
                # if self._updateVTrace or self._updateHTrace:
                #   self.updateTraces()

                # self._renderCursorOnly()

                # force a redraw to only paint the cursor
                # self._paintMode = PaintModes.PAINT_MOUSEONLY
                # self.update(mode=PaintModes.PAINT_ALL)
                self.update(mode=PaintModes.PAINT_MOUSEONLY)

    def update(self, mode=PaintModes.PAINT_ALL):
        """Update the glWidget with the correct refresh mode
        """
        self._paintMode = mode
        super().update()

    @pyqtSlot(dict)
    def _glEvent(self, aDict):
        """Process events from the application/popups and other strips
        :param aDict - dictionary containing event flags:
        """
        if self.spectrumDisplay.isDeleted:
            return

        if not self.globalGL:
            return

        if aDict:
            if aDict[GLNotifier.GLSOURCE] != self:

                # check the params for actions and update the display
                triggers = aDict[GLNotifier.GLTRIGGERS]
                targets = aDict[GLNotifier.GLTARGETS]

                if triggers or targets:

                    if GLNotifier.GLRESCALE in triggers:
                        self._rescaleXAxis(update=False)

                    if GLNotifier.GLPREFERENCES in triggers:
                        self._preferencesUpdate()
                        self._rescaleXAxis(update=False)

        # repaint
        self.update()

    def initializeGL(self):
        # GLversionFunctions = self.context().versionFunctions()
        # GLversionFunctions.initializeOpenGLFunctions()
        # self._GLVersion = GLversionFunctions.glGetString(GL.GL_VERSION)

        # initialise a common to all OpenGL windows
        self.globalGL = GLGlobalData(parent=self, mainWindow=self.mainWindow)  #, strip=None, spectrumDisplay=self.spectrumDisplay)

        # initialise the arrays for the grid and axes
        self.gridList = []
        for li in range(3):
            self.gridList.append(GLVertexArray(numLists=1,
                                               renderMode=GLRENDERMODE_REBUILD,
                                               blendMode=False,
                                               drawMode=GL.GL_LINES,
                                               dimension=2,
                                               GLContext=self))

        self.viewports = GLViewports()
        self._initialiseViewPorts()

        # This is the correct blend function to ignore stray surface blending functions
        GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA, GL.GL_ONE, GL.GL_ONE)

        self._setColourScheme()
        self.setBackgroundColour(self.background, silent=True)
        # _shader = self.globalGL._shaderProgramTex
        # _shader.setBlendEnabled(0)
        # _shader.setAlpha(1.0)

        self.updateVisibleSpectrumViews()
        self.initialiseAxes()
        self._attachParentStrip()

        # set the painting mode
        self._paintMode = PaintModes.PAINT_ALL
        self._paintLastFrame = True
        self._leavingWidget = False

        # check that the screen device pixel ratio is correct
        self.refreshDevicePixelRatio()

        # set the pyqtsignal responders
        self.GLSignals.glXAxisChanged.connect(self._glXAxisChanged)
        self.GLSignals.glYAxisChanged.connect(self._glYAxisChanged)
        self.GLSignals.glAllAxesChanged.connect(self._glAllAxesChanged)
        self.GLSignals.glMouseMoved.connect(self._glMouseMoved)
        self.GLSignals.glEvent.connect(self._glEvent)
        # self.GLSignals.glAxisLockChanged.connect(self._glAxisLockChanged)
        self.GLSignals.glAxisUnitsChanged.connect(self._glAxisUnitsChanged)

        self.glReady = True

    def _attachParentStrip(self):
        self._parentStrip.stripResized.connect(self._parentResize)

    def _parentResize(self, size):
        return
        if self._axisType == GLDefs.BOTTOMAXIS:
            # axis widget is an X widget so grab connected width
            self.setMaximumWidth(size[0])

        else:
            # axis widget is a Y widget so grab connected height
            self.setMaximumHeight(size[1])

    # def _clearGLCursorQueue(self):
    #     for glBuf in self._glCursorQueue:
    #         glBuf.clearArrays()
    #     self._glCursorHead = 0
    #     self._glCursorTail = (self._glCursorHead - 1) % self._numBuffers
    #
    # def _advanceGLCursor(self):
    #     """Advance the pointers for the cursor glLists
    #     """
    #     self._glCursorHead = (self._glCursorHead + 1) % self._numBuffers
    #     self._glCursorTail = (self._glCursorHead - 1) % self._numBuffers

    def initialiseAxes(self, strip=None):
        """setup the correct axis range and padding
        """

        # need to get the matching strip at the correct tilePosition
        tilePos = self._tilePosition

        if tilePos[1] == -1:
            # this should be the axes to the right of a row

            if self.spectrumDisplay.stripArrangement == 'Y':
                stripList = self.spectrumDisplay.stripRow(tilePos[0])
            else:
                stripList = self.spectrumDisplay.stripColumn(tilePos[0])

        elif tilePos[0] == -1:
            # this should be the axis at the bottom of a column

            if self.spectrumDisplay.stripArrangement == 'Y':
                stripList = self.spectrumDisplay.stripColumn(tilePos[1])
            else:
                stripList = self.spectrumDisplay.stripRow(tilePos[1])
        else:
            raise ValueError('Badly defined axisWidget position')

        if not stripList:
            getLogger().warning('Error initialising axis widget, no strips found')

        self._orderedAxes = stripList[0].axes
        self._axisCodes = stripList[0].axisCodes
        self._axisOrder = stripList[0].axisOrder

        # use this to link to the parent height/width
        self._parentStrip = stripList[0]

        axis = self._orderedAxes[0]
        if self.INVERTXAXIS:
            self.axisL = max(axis.region[0], axis.region[1])
            self.axisR = min(axis.region[0], axis.region[1])
        else:
            self.axisL = min(axis.region[0], axis.region[1])
            self.axisR = max(axis.region[0], axis.region[1])

        axis = self._orderedAxes[1]
        if self.INVERTYAXIS:
            self.axisB = max(axis.region[0], axis.region[1])
            self.axisT = min(axis.region[0], axis.region[1])
        else:
            self.axisB = min(axis.region[0], axis.region[1])
            self.axisT = max(axis.region[0], axis.region[1])
        self.update()

    def _initialiseViewPorts(self):
        """Initialise all the viewports for the widget
        """
        self.viewports.clearViewports()

        # define the main viewports
        if self.AXIS_INSIDE:
            self.viewports.addViewport(GLDefs.MAINVIEW, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                       (-self.AXIS_MARGINRIGHT, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

            self.viewports.addViewport(GLDefs.MAINVIEWFULLWIDTH, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                       (0, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

            self.viewports.addViewport(GLDefs.MAINVIEWFULLHEIGHT, self, (0, 'a'), (0, 'a'),
                                       (-self.AXIS_MARGINRIGHT, 'w'), (0, 'h'))
        else:
            self.viewports.addViewport(GLDefs.MAINVIEW, self, (0, 'a'), (self.AXIS_MARGINBOTTOM + self.AXIS_LINE, 'a'),
                                       (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'), (-(self.AXIS_MARGINBOTTOM + self.AXIS_LINE), 'h'))

            self.viewports.addViewport(GLDefs.MAINVIEWFULLWIDTH, self, (0, 'a'), (self.AXIS_MARGINBOTTOM + self.AXIS_LINE, 'a'),
                                       (0, 'w'), (-(self.AXIS_MARGINBOTTOM + self.AXIS_LINE), 'h'))

            self.viewports.addViewport(GLDefs.MAINVIEWFULLHEIGHT, self, (0, 'a'), (0, 'a'),
                                       (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'), (0, 'h'))

        # define the viewports for the right axis bar
        if self.AXIS_INSIDE:
            self.viewports.addViewport(GLDefs.RIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                       (self.AXIS_MARGINBOTTOM, 'a'),
                                       (self.AXIS_LINE, 'a'), (-self.AXIS_MARGINBOTTOM, 'h'))
            self.viewports.addViewport(GLDefs.RIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'),
                                       (self.AXIS_MARGINBOTTOM, 'a'),
                                       (0, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

        else:
            self.viewports.addViewport(GLDefs.RIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                       (self.AXIS_MARGINBOTTOM + self.AXIS_LINE, 'a'),
                                       (self.AXIS_LINE, 'a'), (-(self.AXIS_MARGINBOTTOM + self.AXIS_LINE), 'h'))

            self.viewports.addViewport(GLDefs.RIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'),
                                       (self.AXIS_MARGINBOTTOM + self.AXIS_LINE, 'a'),
                                       (0, 'w'), (-(self.AXIS_MARGINBOTTOM + self.AXIS_LINE), 'h'))

        self.viewports.addViewport(GLDefs.FULLRIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                   (0, 'a'),
                                   (self.AXIS_LINE, 'a'), (0, 'h'))

        self.viewports.addViewport(GLDefs.FULLRIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'), (0, 'a'),
                                   (0, 'w'), (0, 'h'))

        # define the viewports for the bottom axis bar
        if self.AXIS_INSIDE:
            self.viewports.addViewport(GLDefs.BOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                       (-self.AXIS_MARGINRIGHT, 'w'), (self.AXIS_LINE, 'a'))

            self.viewports.addViewport(GLDefs.BOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                       (-self.AXIS_MARGINRIGHT, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))
        else:
            self.viewports.addViewport(GLDefs.BOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                       (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'), (self.AXIS_LINE, 'a'))

            self.viewports.addViewport(GLDefs.BOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                       (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        self.viewports.addViewport(GLDefs.FULLBOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (0, 'w'), (self.AXIS_LINE, 'a'))

        self.viewports.addViewport(GLDefs.FULLBOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                   (0, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        # define the full viewport
        self.viewports.addViewport(GLDefs.FULLVIEW, self, (0, 'a'), (0, 'a'), (0, 'w'), (0, 'h'))

        # define the remaining corner
        self.viewports.addViewport(GLDefs.AXISCORNER, self, (-self.AXIS_MARGINRIGHT, 'w'), (0, 'a'), (0, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        # define an empty view (for printing mainly)
        self.viewports.addViewport(GLDefs.BLANKVIEW, self, (0, 'a'), (0, 'a'), (0, 'a'), (0, 'a'))

    def refreshDevicePixelRatio(self):
        """refresh the devicePixelRatio for the viewports
        """
        newPixelRatio = self.devicePixelRatioF()
        if newPixelRatio != self.lastPixelRatio:
            self.lastPixelRatio = newPixelRatio
            if hasattr(self, GLDefs.VIEWPORTSATTRIB):
                self.viewports.devicePixelRatio = newPixelRatio
            self.update()

    def _preferencesUpdate(self):
        """update GL values after the preferences have changed
        """
        self._preferences = self.application.preferences.general
        self._setColourScheme()

        # set the new limits
        self._applyXLimit = self._preferences.zoomXLimitApply
        self._applyYLimit = self._preferences.zoomYLimitApply
        self._intensityLimit = self._preferences.intensityLimit

        # set the flag to update the background in the paint event
        self._updateBackgroundColour = True

    def setBackgroundColour(self, col, silent=False):
        """
        set all background colours in the shaders
        :param col - vec4, 4 element list e.g.: [0.05, 0.05, 0.05, 1.0], very dark gray
        """
        GL.glClearColor(*col)
        self.background = np.array(col, dtype=np.float32)

        self.globalGL._shaderProgramTex.makeCurrent()
        self.globalGL._shaderProgramTex.setBackground(self.background)
        self.globalGL._shaderProgramAlias.makeCurrent()
        self.globalGL._shaderProgramAlias.setBackground(self.background)
        self.globalGL._shaderProgramTexAlias.makeCurrent()
        self.globalGL._shaderProgramTexAlias.setBackground(self.background)
        if not silent:
            self.update()

    def enableTextClientState(self):
        _attribArrayIndex = 1
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glEnableVertexAttribArray(_attribArrayIndex)

    def disableTextClientState(self):
        _attribArrayIndex = 1
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableVertexAttribArray(_attribArrayIndex)

    def _setViewPortFontScale(self):
        # set the scale for drawing the overlay text correctly
        self._axisScale[0:4] = [self.deltaX, self.deltaY, 1.0, 1.0]
        self.globalGL._shaderProgramTex.setAxisScale(self._axisScale)
        self.globalGL._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0, 1.0, -1.0, 1.0)
        self.globalGL._shaderProgramTex.setPTexMatrix(self._uPMatrix)

    def buildAxisLabels(self, refresh=False):
        # build axes labelling
        if refresh or self.axesChanged:

            self._axisXLabelling = []
            self._axisScaleLabelling = []

            if self.highlighted:
                labelColour = self.highlightColour
            else:
                labelColour = self.foreground

            smallFont = self.getSmallFont()

            if self._drawBottomAxis and self._axisType == GLDefs.BOTTOMAXIS:
                # create the X axis labelling
                for axLabel in self.axisLabelling['0'].values():
                    axisX = axLabel[2]
                    axisXLabel = axLabel[3]

                    axisXText = self._intFormat(axisXLabel) if axLabel[4] >= 1 else self.XMode(axisXLabel)

                    self._axisXLabelling.append(GLString(text=axisXText,
                                                         font=smallFont,
                                                         x=axisX - (0.4 * smallFont.charWidth * self.deltaX * len(
                                                                 axisXText)),
                                                         y=self.AXIS_MARGINBOTTOM - GLDefs.TITLEYOFFSET * smallFont.charHeight,

                                                         colour=labelColour, GLContext=self,
                                                         obj=None))

                # append the axisCode
                self._axisXLabelling.append(GLString(text=self._visibleOrderingAxisCodes[0] if self._visibleOrderingAxisCodes else '*',
                                                     font=smallFont,
                                                     x=GLDefs.AXISTEXTXOFFSET * self.deltaX,
                                                     y=self.AXIS_MARGINBOTTOM - GLDefs.TITLEYOFFSET * smallFont.charHeight,
                                                     colour=labelColour, GLContext=self,
                                                     obj=None))
                # and the axis dimensions
                xUnitsLabels = self.XAXES[self._xUnits]
                self._axisXLabelling.append(GLString(text=xUnitsLabels,
                                                     font=smallFont,
                                                     x=1.0 - (self.deltaX * len(xUnitsLabels) * smallFont.charWidth),
                                                     y=self.AXIS_MARGINBOTTOM - GLDefs.TITLEYOFFSET * smallFont.charHeight,
                                                     colour=labelColour, GLContext=self,
                                                     obj=None))

            self._axisYLabelling = []

            if self._drawRightAxis and self._axisType == GLDefs.RIGHTAXIS:
                # create the Y axis labelling
                for xx, ayLabel in enumerate(self.axisLabelling['1'].values()):
                    axisY = ayLabel[2]
                    axisYLabel = ayLabel[3]

                    if self.YAXISUSEEFORMAT:
                        axisYText = self.YMode(axisYLabel)
                    else:
                        axisYText = self._intFormat(axisYLabel) if ayLabel[4] >= 1 else self.YMode(axisYLabel)

                    self._axisYLabelling.append(GLString(text=axisYText,
                                                         font=smallFont,
                                                         x=self.AXIS_OFFSET,
                                                         y=axisY - (GLDefs.AXISTEXTYOFFSET * self.deltaY),
                                                         colour=labelColour, GLContext=self,
                                                         obj=None))

                # append the axisCode
                self._axisYLabelling.append(GLString(text=self._visibleOrderingAxisCodes[1] if self._visibleOrderingAxisCodes and len(self._visibleOrderingAxisCodes) > 1 else '*',
                                                     font=smallFont,
                                                     x=self.AXIS_OFFSET,
                                                     y=1.0 - (GLDefs.TITLEYOFFSET * smallFont.charHeight * self.deltaY),
                                                     colour=labelColour, GLContext=self,
                                                     obj=None))
                # and the axis dimensions
                yUnitsLabels = self.YAXES[self._yUnits]
                self._axisYLabelling.append(GLString(text=yUnitsLabels,
                                                     font=smallFont,
                                                     x=self.AXIS_OFFSET,
                                                     y=1.0 * self.deltaY,
                                                     colour=labelColour, GLContext=self,
                                                     obj=None))

    def drawAxisLabels(self):
        # draw axes labelling

        if self._axesVisible:
            self.buildAxisLabels()

            if self._drawBottomAxis and self._drawRightAxis:
                # NOTE:ED - this case should never occur
                return

            if self._drawBottomAxis and self._axisType == GLDefs.BOTTOMAXIS:
                # put the axis labels into the bottom bar
                self.viewports.setViewport(self._currentBottomAxisBarView)

                # self._axisScale[0:4] = [self.pixelX, 1.0, 1.0, 1.0]
                self._axisScale[0:4] = [self.deltaX, 1.0, 1.0, 1.0]

                self.globalGL._shaderProgramTex.setAxisScale(self._axisScale)
                self.globalGL._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0,
                                                                  self.AXIS_MARGINBOTTOM, -1.0, 1.0)
                self.globalGL._shaderProgramTex.setPTexMatrix(self._uPMatrix)

                for lb in self._axisXLabelling:
                    lb.drawTextArrayVBO()

            if self._drawRightAxis and self._axisType == GLDefs.RIGHTAXIS:
                # put the axis labels into the right bar
                self.viewports.setViewport(self._currentRightAxisBarView)

                # self._axisScale[0:4] = [1.0, self.pixelY, 1.0, 1.0]
                self._axisScale[0:4] = [1.0, self.deltaY, 1.0, 1.0]

                self.globalGL._shaderProgramTex.setAxisScale(self._axisScale)
                self.globalGL._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0, self.AXIS_MARGINRIGHT,
                                                                  0.0, 1.0, -1.0, 1.0)
                self.globalGL._shaderProgramTex.setPTexMatrix(self._uPMatrix)

                for lb in self._axisYLabelling:
                    lb.drawTextArrayVBO()

    def enableTexture(self):
        GL.glEnable(GL.GL_BLEND)
        # GL.glEnable(GL.GL_TEXTURE_2D)
        # GL.glBindTexture(GL.GL_TEXTURE_2D, smallFont.textureId)

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.getSmallFont()._parent.textureId)
        # GL.glActiveTexture(GL.GL_TEXTURE1)
        # GL.glBindTexture(GL.GL_TEXTURE_2D, self.getSmallFont(transparent=True).textureId)

        # # specific blend function for text overlay
        # GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_DST_COLOR, GL.GL_ONE, GL.GL_ONE)

    def disableTexture(self):
        GL.glDisable(GL.GL_BLEND)

        # # reset blend function
        # GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA, GL.GL_ONE, GL.GL_ONE)

    def _testAxisLimits(self, setLimits=False):
        xRange = abs(self.axisL - self.axisR) / 3.0
        yRange = abs(self.axisT - self.axisB) / 3.0
        self._minXReached = False
        self._minYReached = False
        self._maxXReached = False
        self._maxYReached = False

        if xRange < self._minXRange and self._rangeXDefined and self._applyXLimit:
            if setLimits:
                xMid = (self.axisR + self.axisL) / 2.0
                self.axisL = xMid - self._minXRange * self.sign(self.pixelX)
                self.axisR = xMid + self._minXRange * self.sign(self.pixelX)
            self._minXReached = True

        if yRange < self._minYRange and self._rangeYDefined and self._applyYLimit:
            if setLimits:
                yMid = (self.axisT + self.axisB) / 2.0
                self.axisT = yMid + self._minYRange * self.sign(self.pixelY)
                self.axisB = yMid - self._minYRange * self.sign(self.pixelY)
            self._minYReached = True

        if xRange > self._maxXRange and self._rangeXDefined and self._applyXLimit:
            if setLimits:
                xMid = (self.axisR + self.axisL) / 2.0
                self.axisL = xMid - self._maxXRange * self.sign(self.pixelX)
                self.axisR = xMid + self._maxXRange * self.sign(self.pixelX)
            self._maxXReached = True

        if yRange > self._maxYRange and self._rangeYDefined and self._applyYLimit:
            if setLimits:
                yMid = (self.axisT + self.axisB) / 2.0
                self.axisT = yMid + self._maxYRange * self.sign(self.pixelY)
                self.axisB = yMid - self._maxYRange * self.sign(self.pixelY)
            self._maxYReached = True

        self._minReached = self._minXReached or self._minYReached
        self._maxReached = self._maxXReached or self._maxYReached

    def _rescaleAllZoom(self, rescale=True):
        """Reset the zoomto fit the spectra, including aspect checking
        """
        _useFirstDefault = getattr(self.spectrumDisplay, '_useFirstDefault', False)
        if (self._aspectRatioMode or _useFirstDefault):

            # check which is the primary axis and update the opposite axis - similar to wheelEvent
            if self.spectrumDisplay.stripArrangement == 'Y':

                # strips are arranged in a row
                self._scaleToYAxis(rescale=rescale)

            elif self.spectrumDisplay.stripArrangement == 'X':

                # strips are arranged in a column
                self._scaleToXAxis(rescale=rescale)

            elif self.spectrumDisplay.stripArrangement == 'T':

                # NOTE:ED - Tiled plots not fully implemented yet
                getLogger().warning('Tiled plots not implemented for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

            else:
                getLogger().warning('Strip direction is not defined for spectrumDisplay: %s' % str(self.spectrumDisplay.pid))

        self.rescale()

        # put stuff in here that will change on a resize
        self._updateAxes = True
        for gr in self.gridList:
            gr.renderMode = GLRENDERMODE_REBUILD
        # self._GLPeaks.rescale()
        # self._GLMultiplets.rescale()

        # self._clearAndUpdate(clearKeys=True)
        self.update()

    def _rescaleAllAxes(self, mouseMoveOnly=False, update=True):
        self._testAxisLimits()
        self.rescale()

        # spawn rebuild event for the grid
        self._updateAxes = True
        for gr in self.gridList:
            gr.renderMode = GLRENDERMODE_REBUILD
        if update:
            self.update()

    def _rescaleXAxis(self, update=True):
        self._testAxisLimits()
        self.rescale(rescaleStaticHTraces=False)

        # spawn rebuild event for the grid
        self._updateAxes = True
        if self.gridList:
            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD

        if update:
            self.update()

    def _rescaleYAxis(self, update=True):
        self._testAxisLimits()
        self.rescale(rescaleStaticVTraces=False)

        # spawn rebuild event for the grid
        self._updateAxes = True
        if self.gridList:
            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD

        if update:
            self.update()

    def _storeZoomHistory(self):
        """Store the current axis state to the zoom history
        """
        currentAxis = (self.axisL, self.axisR, self.axisB, self.axisT)

        # store the current value if current zoom has not been set
        if self._zoomHistory[self._zoomHistoryHead] is None:
            self._zoomHistory[self._zoomHistoryHead] = currentAxis

        if self._widthsChangedEnough(currentAxis, self._zoomHistory[self._zoomHistoryHead], tol=1e-8):

            for stored in self.storedZooms:
                if not self._widthsChangedEnough(currentAxis, self._zoomHistory[self._zoomHistoryHead], tol=1e-8):
                    break
            else:
                currentTime = time.time()
                if currentTime - self._zoomTimerLast < ZOOMTIMERDELAY:

                    # still on the current zoom item - write new value
                    self._zoomHistory[self._zoomHistoryHead] = currentAxis

                else:

                    # increment the head of the zoom history
                    self._zoomHistoryHead = (self._zoomHistoryHead + 1) % len(self._zoomHistory)
                    self._zoomHistory[self._zoomHistoryHead] = currentAxis
                    self._zoomHistoryCurrent = self._zoomHistoryHead

                # reset the timer so you have to wait another 5 seconds
                self._zoomTimerLast = currentTime

    def getCurrentCursorCoordinate(self):

        if self.cursorSource == None or self.cursorSource == 'self':
            currentPos = self.mapFromGlobal(QtGui.QCursor.pos())

            # calculate mouse coordinate within the mainView
            _mouseX = currentPos.x()
            if not self._fullHeightRightAxis:
                _mouseY = self.height() - currentPos.y() - self.AXIS_MOUSEYOFFSET
                _top = self.height() - self.AXIS_MOUSEYOFFSET
            else:
                _mouseY = self.height() - currentPos.y()
                _top = self.height()

            # translate from screen (0..w, 0..h) to NDC (-1..1, -1..1) to axes (axisL, axisR, axisT, axisB)
            result = self.mouseTransform.dot([_mouseX, _mouseY, 0.0, 1.0])

            # print('updated current pos GLWidget:', currentPos, self.height(), self.AXIS_MOUSEYOFFSET, result[:2])

        else:
            result = self.cursorCoordinate

        return result

    def redrawAxes(self):
        """Redraw the axes when switching strip arrangement
        """
        if self.glReady:
            self._rescaleAllZoom(False)

    def mousePressEvent(self, ev):

        try:
            _row = self.spectrumDisplay.stripRow(0)
            self.current.strip = _row[-1]
        except:
            return

        mx = ev.pos().x()
        if self._drawBottomAxis:
            my = self.height() - ev.pos().y() - self.AXIS_MOUSEYOFFSET
        else:
            my = self.height() - ev.pos().y()
        self._mouseStart = (mx, my)

    def mouseReleaseEvent(self, ev):

        # if no self.current then strip is not defined correctly
        if not getattr(self.current, 'mouseMovedDict', None):
            return

        mx = ev.pos().x()
        if self._drawBottomAxis:
            my = self.height() - ev.pos().y() - self.AXIS_MOUSEYOFFSET
        else:
            my = self.height() - ev.pos().y()
        self._mouseEnd = (mx, my)

        # add a 2-pixel tolerance to the click event - in case of a small wiggle on coordinates
        if not self._widthsChangedEnough(self._mouseStart, self._mouseEnd, tol=2):
            # perform click action
            self._mouseClickEvent(ev)

    def _mouseClickEvent(self, event: QtGui.QMouseEvent, axis=None):
        """handle the mouse click event
        """
        if rightMouse(event) and axis is None:
            # right click on canvas, not the axes

            try:
                _row = self.spectrumDisplay.stripRow(0)
                strip = _row[-1]
            except:
                return

            event.accept()
            mouseInAxis = self._axisType

            strip.contextMenuMode = AxisMenu
            menu = strip._contextMenus.get(strip.contextMenuMode)

            # create a dynamic menu based on the available axisCodes
            menu.clear()
            strip._addItemsToMarkAxesMenuAxesView(mouseInAxis, menu)
            strip._addItemsToCopyAxisFromMenuesAxes(mouseInAxis, menu, self.is1D)

            if menu is not None:
                strip.viewStripMenu = menu
            else:
                strip.viewStripMenu = self._getCanvasContextMenu()

            strip._raiseContextMenu(event)

        self.update()

    def _mouseInAxis(self, mousePos):
        h = self.h
        w = self.w

        # find the correct viewport
        if (self._drawRightAxis and self._drawBottomAxis):
            mw = [0, self.AXIS_MARGINBOTTOM, w - self.AXIS_MARGINRIGHT, h - 1]
            ba = [0, 0, w - self.AXIS_MARGINRIGHT, self.AXIS_MARGINBOTTOM - 1]
            ra = [w - self.AXIS_MARGINRIGHT, self.AXIS_MARGINBOTTOM, w, h]

        elif (self._drawBottomAxis):
            mw = [0, self.AXIS_MARGINBOTTOM, w, h - 1]
            ba = [0, 0, w, self.AXIS_MARGINBOTTOM - 1]
            ra = [w, self.AXIS_MARGINBOTTOM, w, h]

        elif (self._drawRightAxis):
            mw = [0, 0, w - self.AXIS_MARGINRIGHT, h - 1]
            ba = [0, 0, w - self.AXIS_MARGINRIGHT, 0]
            ra = [w - self.AXIS_MARGINRIGHT, 0, w, h]

        else:  # no axes visible
            mw = [0, 0, w, h]
            ba = [0, 0, w, 0]
            ra = [w, 0, w, h]

        mx = mousePos.x()
        my = self.height() - mousePos.y()

        if self.between(mx, mw[0], mw[2]) and self.between(my, mw[1], mw[3]):

            # if in the mainView
            return GLDefs.MAINVIEW

        elif self.between(mx, ba[0], ba[2]) and self.between(my, ba[1], ba[3]):

            # in the bottomAxisBar, so zoom in the X axis
            return GLDefs.BOTTOMAXIS

        elif self.between(mx, ra[0], ra[2]) and self.between(my, ra[1], ra[3]):

            # in the rightAxisBar, so zoom in the Y axis
            return GLDefs.RIGHTAXIS

        else:

            # must be in the corner
            return GLDefs.AXISCORNER

    def mouseMoveEvent(self, event):

        self.cursorSource = CURSOR_SOURCE_SELF

        if self.spectrumDisplay.isDeleted:
            return
        if not self._ordering:  # strip.spectrumViews:
            return
        if self._draggingLabel:
            return

        if abs(self.axisL - self.axisR) < 1.0e-6 or abs(self.axisT - self.axisB) < 1.0e-6:
            return

        # reset on the first mouseMove - frees the locked/default axis
        setattr(self.spectrumDisplay, '_useFirstDefault', False)

        currentPos = self.mapFromGlobal(QtGui.QCursor.pos())

        dx = currentPos.x() - self.lastPos.x()
        dy = currentPos.y() - self.lastPos.y()
        self.lastPos = currentPos
        cursorCoordinate = self.getCurrentCursorCoordinate()

        try:
            mouseMovedDict = self.current.mouseMovedDict
        except:
            # initialise a new mouse moved dict
            mouseMovedDict = {MOUSEDICTSTRIP          : None,
                              AXIS_MATCHATOMTYPE      : {},
                              AXIS_FULLATOMNAME       : {},
                              AXIS_ACTIVEAXES         : (),
                              DOUBLEAXIS_MATCHATOMTYPE: {},
                              DOUBLEAXIS_FULLATOMNAME : {},
                              DOUBLEAXIS_ACTIVEAXES   : ()
                              }

        xPos = yPos = 0
        activeOther = []
        activeX = activeY = '<None>'

        for n, axisCode in enumerate(self.spectrumDisplay.axisCodes):
            if n == 0:
                xPos = pos = cursorCoordinate[0]
                activeX = axisCode  #[0]

                # double cursor
                dPos = cursorCoordinate[1]
            elif n == 1:
                yPos = pos = cursorCoordinate[1]
                activeY = axisCode  #[0]

                # double cursor
                dPos = cursorCoordinate[0]

            else:
                dPos = pos = self._orderedAxes[n].position if (n in self._orderedAxes and
                                                               not self._orderedAxes[n].isDeleted) else 0
                # dPos = pos = self.spectrumDisplay.axes[n].position  # if n in self._orderedAxes else 0

                activeOther.append(axisCode)  #[0])

            # populate the mouse moved dict
            mouseMovedDict[AXIS_MATCHATOMTYPE][axisCode[0]] = pos
            mouseMovedDict[AXIS_FULLATOMNAME][axisCode] = pos
            mouseMovedDict[DOUBLEAXIS_MATCHATOMTYPE][axisCode[0]] = dPos
            mouseMovedDict[DOUBLEAXIS_FULLATOMNAME][axisCode] = dPos

        mouseMovedDict[AXIS_ACTIVEAXES] = (activeX, activeY) + tuple(activeOther)  # changed to full axisCodes
        mouseMovedDict[DOUBLEAXIS_ACTIVEAXES] = (activeY, activeX) + tuple(activeOther)

        self.current.cursorPosition = (xPos, yPos)
        self.current.mouseMovedDict = mouseMovedDict

        if int(event.buttons() & (Qt.LeftButton | Qt.RightButton)):
            # Main mouse drag event - handle moving the axes with the mouse

            # only change if moving in the correct axis bar
            if self._drawBottomAxis:
                self.axisL -= dx * self.pixelX
                self.axisR -= dx * self.pixelX
            if self._drawRightAxis:
                self.axisT += dy * self.pixelY
                self.axisB += dy * self.pixelY

            tilePos = self.tilePosition
            self.GLSignals._emitAllAxesChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                               axisB=self.axisB, axisT=self.axisT,
                                               axisL=self.axisL, axisR=self.axisR,
                                               row=tilePos[0], column=tilePos[1])
            # self._selectionMode = 0
            self._rescaleAllAxes(mouseMoveOnly=True)
            # self._storeZoomHistory()

        if not int(event.buttons()):
            self.GLSignals._emitMouseMoved(source=self, coords=cursorCoordinate, mouseMovedDict=mouseMovedDict, mainWindow=self.mainWindow)

        self.update()

    def _resizeGL(self, w, h):
        self.w = w
        self.h = h

        self._rescaleAllZoom(False)

    def sign(self, x):
        return 1.0 if x >= 0 else -1.0

    def _scaleToXAxis(self, rescale=True):

        _useFirstDefault = getattr(self.spectrumDisplay, '_useFirstDefault', False)
        if (self._aspectRatioMode or _useFirstDefault):  # and self._axisType != GLDefs.BOTTOMAXIS:
            mby = 0.5 * (self.axisT + self.axisB)

            # if self._useDefaultAspect or _useFirstDefault:
            if (self._aspectRatioMode == 2) or _useFirstDefault:
                ax0 = self._getValidAspectRatio(self.spectrumDisplay.axisCodes[0])
                ax1 = self._getValidAspectRatio(self.spectrumDisplay.axisCodes[1])
            else:
                try:
                    ax0, ax1 = self.spectrumDisplay._stripAddMode
                except Exception as es:
                    # just let stripAddMode fail for axis widget
                    ax0 = self.pixelX
                    ax1 = self.pixelY

            width, height = self._parentStrip.mainViewSize()

            ratio = (height / width) * 0.5 * abs((self.axisL - self.axisR) * ax1 / ax0)
            self.axisB = mby + ratio * self.sign(self.axisB - mby)
            self.axisT = mby - ratio * self.sign(mby - self.axisT)

        if rescale:
            self._rescaleAllAxes()

    def _scaleToYAxis(self, rescale=True):

        _useFirstDefault = getattr(self.spectrumDisplay, '_useFirstDefault', False)
        if (self._aspectRatioMode or _useFirstDefault):  # and self._axisType != GLDefs.RIGHTAXIS:
            mbx = 0.5 * (self.axisR + self.axisL)

            # if self._useDefaultAspect or _useFirstDefault:
            if (self._aspectRatioMode == 2) or _useFirstDefault:
                ax0 = self._getValidAspectRatio(self.spectrumDisplay.axisCodes[0])
                ax1 = self._getValidAspectRatio(self.spectrumDisplay.axisCodes[1])
            else:
                try:
                    ax0, ax1 = self.spectrumDisplay._stripAddMode
                except Exception as es:
                    # just let stripAddMode fail for axis widget
                    ax0 = self.pixelX
                    ax1 = self.pixelY

            width, height = self._parentStrip.mainViewSize()

            ratio = (width / height) * 0.5 * abs((self.axisT - self.axisB) * ax0 / ax1)
            self.axisL = mbx + ratio * self.sign(self.axisL - mbx)
            self.axisR = mbx - ratio * self.sign(mbx - self.axisR)

        if rescale:
            self._rescaleAllAxes()

    def _getValidAspectRatio(self, axisCode):
        if self.spectrumDisplay and self.spectrumDisplay.strips and len(self.spectrumDisplay.strips) > 0:
            strip = self.spectrumDisplay.strips[0]
            if not (strip.isDeleted or strip._flaggedForDelete):
                ratios = strip._CcpnGLWidget._aspectRatios

                va = [ax for ax in ratios.keys() if ax.upper()[0] == axisCode.upper()[0]]
                if va and len(va) > 0:
                    return ratios[va[0]]
        return 1.0

    def resizeGL(self, w, h):
        # must be set here to catch the change of screen
        self.refreshDevicePixelRatio()
        self._resizeGL(w, h)
        if self._aspectRatioMode == 0:
            ratios = None
            if self.spectrumDisplay and self.spectrumDisplay.strips and len(self.spectrumDisplay.strips) > 0:
                strip = self.spectrumDisplay.strips[0]
                if not (strip.isDeleted or strip._flaggedForDelete):
                    ratios = strip._CcpnGLWidget._lockedAspectRatios
            self.GLSignals._emitXAxisChanged(source=self, strip=None,
                                             aspectRatios=ratios)

    def rescale(self, rescaleOverlayText=True, rescaleMarksRulers=True,
                rescaleIntegralLists=True, rescaleRegions=True,
                rescaleSpectra=True, rescaleStaticHTraces=True,
                rescaleStaticVTraces=True, rescaleSpectrumLabels=True,
                rescaleLegend=True):
        """Change to axes of the view, axis visibility, scale and rebuild matrices when necessary
        to improve display speed
        """
        try:
            self._parentStrip = self.spectrumDisplay.orderedStrips[0]
        except:
            return

        if self._parentStrip.isDeleted or not self.globalGL:
            return

        if not self.viewports:
            return

        # use the updated size
        w = self.w
        h = self.h

        currentShader = self.globalGL._shaderProgram1.makeCurrent()

        # set projection to axis coordinates
        currentShader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB,
                                        self.axisT, -1.0, 1.0)
        currentShader.setPMatrix(self._uPMatrix)

        # needs to be offset from (0,0) for mouse scaling
        if self._drawRightAxis and self._drawBottomAxis:

            raise ValueError('Bad axis state - can only have either right axis or bottom axis')

        elif self._drawRightAxis and not self._drawBottomAxis:

            if self._fullHeightRightAxis:
                self._currentRightAxisView = GLDefs.FULLRIGHTAXIS
                self._currentRightAxisBarView = GLDefs.FULLRIGHTAXISBAR
            else:
                self._currentRightAxisView = GLDefs.RIGHTAXIS
                self._currentRightAxisBarView = GLDefs.RIGHTAXISBAR

        elif not self._drawRightAxis and self._drawBottomAxis:

            if self._fullWidthBottomAxis:
                self._currentBottomAxisView = GLDefs.FULLBOTTOMAXIS
                self._currentBottomAxisBarView = GLDefs.FULLBOTTOMAXISBAR
            else:
                self._currentBottomAxisView = GLDefs.BOTTOMAXIS
                self._currentBottomAxisBarView = GLDefs.BOTTOMAXISBAR

        else:
            # do nothing
            pass

        # get the dimensions of the main view for the current strip
        vpwidth, vpheight = self._parentStrip.mainViewSize()
        currentShader.setViewportMatrix(self._uVMatrix, 0, vpwidth, 0, vpheight,
                                        -1.0, 1.0)

        self.pixelX = (self.axisR - self.axisL) / vpwidth
        self.pixelY = (self.axisT - self.axisB) / vpheight
        self.deltaX = 1.0 / vpwidth
        self.deltaY = 1.0 / vpheight

        # self._dataMatrix[0:16] = [self.axisL, self.axisR, self.axisT, self.axisB,
        #                           self.pixelX, self.pixelY, w, h,
        #                           0.2, 1.0, 0.4, 1.0,
        #                           0.3, 0.1, 1.0, 1.0]
        # currentShader.setGLUniformMatrix4fv('dataMatrix', 1, GL.GL_FALSE, self._dataMatrix)
        currentShader.setMVMatrix(self._IMatrix)

        # map mouse coordinates to world coordinates - only needs to change on resize, move soon
        currentShader.setViewportMatrix(self._aMatrix, self.axisL, self.axisR, self.axisB,
                                        self.axisT, -1.0, 1.0)

        # calculate the screen to axes transform
        self.vInv = np.linalg.inv(self._uVMatrix.reshape((4, 4)))
        self.mouseTransform = np.matmul(self._aMatrix.reshape((4, 4)), self.vInv)

        # NOTE:ED - raising numpy runtimewarnings as errors
        # with np.errstate(all='raise'):
        #     try:
        #         self.mouseTransform = np.matmul(self._aMatrix.reshape((4, 4)), self.vInv)
        #     except Exception as es:
        #         # catch runtime error and set to identity
        #         print('>>> RuntimeWarning', str(es))
        #         self.mouseTransform = self._IMatrix

        self.modelViewMatrix = (GL.GLdouble * 16)()
        self.projectionMatrix = (GL.GLdouble * 16)()
        self.viewport = (GL.GLint * 4)()

        # change to the text shader
        currentShader = self.globalGL._shaderProgramTex.makeCurrent()

        currentShader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB, self.axisT, -1.0, 1.0)
        currentShader.setPTexMatrix(self._uPMatrix)

        self._axisScale[0:4] = [self.pixelX, self.pixelY, 1.0, 1.0]
        # self._view[0:4] = [w - self.AXIS_MARGINRIGHT, h - self.AXIS_MOUSEYOFFSET, 1.0, 1.0]
        # self._view[0:4] = [vpwidth, vpheight, 1.0, 1.0]

        # self._axisScale[0:4] = [1.0/(self.axisR-self.axisL), 1.0/(self.axisT-self.axisB), 1.0, 1.0]
        currentShader.setAxisScale(self._axisScale)
        # currentShader.setGLUniform4fv('viewport', 1, self._view)

    def _updateVisibleSpectrumViews(self):
        """Update the list of visible spectrumViews when change occurs
        """

        # make the list of ordered spectrumViews
        self._ordering = []
        if self.spectrumDisplay and self.spectrumDisplay.strips and len(self.spectrumDisplay.strips) > 0:
            strip = self.spectrumDisplay.strips[0]
            if not (strip.isDeleted or strip._flaggedForDelete):
                self._ordering = self.spectrumDisplay.orderedSpectrumViews(strip.spectrumViews)

        self._ordering = [specView for specView in self._ordering]

        for specView in tuple(self._spectrumSettings.keys()):
            if specView not in self._ordering:
                # print('>>>_updateVisibleSpectrumViews delete', specView, id(specView))
                # print('>>>', [id(spec) for spec in self._ordering])
                del self._spectrumSettings[specView]

        # make a list of the visible and not-deleted spectrumViews
        # visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
        visibleSpectrumViews = [specView for specView in self._ordering if not specView.isDeleted and specView.isVisible()]

        self._visibleOrdering = visibleSpectrumViews

        # set the first visible, or the first in the ordered list
        self._firstVisible = visibleSpectrumViews[0] if visibleSpectrumViews else self._ordering[0] if self._ordering and not self._ordering[
            0].isDeleted else None

    def updateVisibleSpectrumViews(self):
        self._visibleSpectrumViewsChange = True
        self.update()

    def wheelEvent(self, event):
        # def between(val, l, r):
        #   return (l-val)*(r-val) <= 0

        if self.spectrumDisplay and not self._ordering:  # strip.spectrumViews:
            event.accept()
            return

        # check the movement of the wheel first
        numPixels = event.pixelDelta()
        numDegrees = event.angleDelta()
        zoomCentre = self._preferences.zoomCentreType

        zoomScale = 0.0
        scrollDirection = 0
        if numPixels:

            # always seems to be numPixels - check with Linux
            # the Shift key automatically returns the x-axis
            scrollDirection = numPixels.x() if self._isSHIFT else numPixels.y()
            zoomScale = 8.0

            # stop the very sensitive movements
            if abs(scrollDirection) < 1:
                event.ignore()
                return

        elif numDegrees:

            # this may work when using Linux
            scrollDirection = (numDegrees.x() / 4) if self._isSHIFT else (numDegrees.y() / 4)
            zoomScale = 8.0

            # stop the very sensitive movements
            if abs(scrollDirection) < 1:
                event.ignore()
                return

        else:
            event.ignore()
            return

        # if self._isSHIFT or self._isCTRL:
        #
        #     # process wheel with buttons here
        #     # transfer event to the correct widget for changing the plane OR raising base contour level...
        #
        #     if self._isSHIFT:
        #         # raise/lower base contour level - should be strip I think
        #         if scrollDirection > 0:
        #             self.strip.spectrumDisplay.raiseContourBase()
        #         else:
        #             self.strip.spectrumDisplay.lowerContourBase()
        #
        #     elif self._isCTRL:
        #         # scroll through planes
        #         pT = self.strip.planeAxisBars if hasattr(self.strip, 'planeAxisBars') else None
        #         activePlaneAxis = self.strip.activePlaneAxis
        #         if pT and activePlaneAxis is not None and (activePlaneAxis - 2) < len(pT):
        #             # pass the event to the correct double spinbox
        #             pT[activePlaneAxis - 2].scrollPpmPosition(event)
        #
        #     event.accept()
        #     return

        # test whether the limits have been reached in either axis
        if (scrollDirection > 0 and self._minReached and self._aspectRatioMode) or \
                (scrollDirection < 0 and self._maxReached and self._aspectRatioMode):
            event.accept()
            return

        zoomIn = (100.0 + zoomScale) / 100.0
        zoomOut = 100.0 / (100.0 + zoomScale)

        h = self.h
        w = self.w

        # find the correct viewport
        if (self._drawRightAxis and self._drawBottomAxis):
            # ba = self.viewports.getViewportFromWH(GLDefs.BOTTOMAXISBAR, w, h)
            # ra = self.viewports.getViewportFromWH(GLDefs.RIGHTAXISBAR, w, h)
            ba = self.viewports.getViewportFromWH(self._currentBottomAxisBarView, w, h)
            ra = self.viewports.getViewportFromWH(self._currentRightAxisBarView, w, h)

        elif (self._drawBottomAxis):
            # ba = self.viewports.getViewportFromWH(GLDefs.FULLBOTTOMAXISBAR, w, h)
            ba = self.viewports.getViewportFromWH(self._currentBottomAxisBarView, w, h)
            ra = (0, 0, 0, 0)

        elif (self._drawRightAxis):
            ba = (0, 0, 0, 0)
            # ra = self.viewports.getViewportFromWH(GLDefs.FULLRIGHTAXISBAR, w, h)
            ra = self.viewports.getViewportFromWH(self._currentRightAxisBarView, w, h)

        else:  # no axes visible
            ba = (0, 0, 0, 0)
            ra = (0, 0, 0, 0)

        mx = event.pos().x()
        my = self.height() - event.pos().y()

        tilePos = self.tilePosition

        if self.between(mx, ba[0], ba[0] + ba[2]) and self.between(my, ba[1], ba[1] + ba[3]):

            # in the bottomAxisBar, so zoom in the X axis

            # check the X limits
            if (scrollDirection > 0 and self._minXReached) or (scrollDirection < 0 and self._maxXReached):
                event.accept()
                return

            if zoomCentre == 0:  # centre on mouse
                mb = (mx - ba[0]) / (ba[2] - ba[0])
            else:  # centre on the screen
                mb = 0.5

            mbx = self.axisL + mb * (self.axisR - self.axisL)

            if scrollDirection < 0:
                self.axisL = mbx + zoomIn * (self.axisL - mbx)
                self.axisR = mbx - zoomIn * (mbx - self.axisR)
            else:
                self.axisL = mbx + zoomOut * (self.axisL - mbx)
                self.axisR = mbx - zoomOut * (mbx - self.axisR)

            if not self._aspectRatioMode:
                # ratios = None
                # if self.spectrumDisplay and self.spectrumDisplay.strips and len(self.spectrumDisplay.strips) > 0:
                #     strip = self.spectrumDisplay.strips[0]
                #     if not (strip.isDeleted or strip._flaggedForDelete):
                #         ratios = strip._CcpnGLWidget._lockedAspectRatios
                try:
                    ratios = self.spectrumDisplay.strips[0]._CcpnGLWidget._lockedAspectRatios
                except:
                    ratios = None

                self.GLSignals._emitXAxisChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                                 axisB=self.axisB, axisT=self.axisT,
                                                 axisL=self.axisL, axisR=self.axisR,
                                                 row=tilePos[0], column=tilePos[1],
                                                 aspectRatios=ratios)

                self._rescaleXAxis()
                # self._storeZoomHistory()

            else:
                self._scaleToXAxis()

                self.GLSignals._emitAllAxesChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                                   axisB=self.axisB, axisT=self.axisT,
                                                   axisL=self.axisL, axisR=self.axisR,
                                                   row=tilePos[0], column=tilePos[1])

                # self._storeZoomHistory()

        elif self.between(mx, ra[0], ra[0] + ra[2]) and self.between(my, ra[1], ra[1] + ra[3]):

            # in the rightAxisBar, so zoom in the Y axis

            # check the Y limits
            if (scrollDirection > 0 and self._minYReached) or (scrollDirection < 0 and self._maxYReached):
                event.accept()
                return

            if zoomCentre == 0:  # centre on mouse
                mb = (my - ra[1]) / (ra[3] - ra[1])
            else:  # centre on the screen
                mb = 0.5

            mby = self.axisB + mb * (self.axisT - self.axisB)

            if scrollDirection < 0:
                self.axisB = mby + zoomIn * (self.axisB - mby)
                self.axisT = mby - zoomIn * (mby - self.axisT)
            else:
                self.axisB = mby + zoomOut * (self.axisB - mby)
                self.axisT = mby - zoomOut * (mby - self.axisT)

            if not self._aspectRatioMode:
                # ratios = None
                # if self.spectrumDisplay and self.spectrumDisplay.strips and len(self.spectrumDisplay.strips) > 0:
                #     strip = self.spectrumDisplay.strips[0]
                #     if not (strip.isDeleted or strip._flaggedForDelete):
                #         ratios = strip._CcpnGLWidget._lockedAspectRatios
                try:
                    ratios = self.spectrumDisplay.strips[0]._CcpnGLWidget._lockedAspectRatios
                except:
                    ratios = None

                self.GLSignals._emitYAxisChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                                 axisB=self.axisB, axisT=self.axisT,
                                                 axisL=self.axisL, axisR=self.axisR,
                                                 row=tilePos[0], column=tilePos[1],
                                                 aspectRatios=ratios)

                self._rescaleYAxis()
                # self._storeZoomHistory()

            else:
                self._scaleToYAxis()

                self.GLSignals._emitAllAxesChanged(source=self, strip=None, spectrumDisplay=self.spectrumDisplay,
                                                   axisB=self.axisB, axisT=self.axisT,
                                                   axisL=self.axisL, axisR=self.axisR,
                                                   row=tilePos[0], column=tilePos[1])

                # self._storeZoomHistory()

        event.accept()

    def highlightCurrentStrip(self, current):
        if current:
            self.highlighted = True

            self._updateAxes = True
            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD

        else:
            self.highlighted = False

            self._updateAxes = True
            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD

        self.update()

    def _buildSingleWildCard(self, _axisCodes):
        """Buld the axisCode appending wildcard as required
        """
        _code = ''
        if _axisCodes:
            _maxLen = max(len(ax) for ax in _axisCodes)
            _chs = [a for a in zip(*_axisCodes)]
            for ch in _chs:
                chSet = set(ch)
                if len(chSet) == 1:
                    _code += ch[0]
                else:
                    _code += '*'
                    break
            else:
                if len(_code) < _maxLen:
                    _code += '*'
        _code = _code or '*'

        return _code

    def _buildAxisCodesWithWildCards(self):
        """Build the visible axis codes from the visible spectra appending wildcard as required
        """
        _visibleSpec = [(specView, self._spectrumSettings[specView]) for specView in self._ordering
                        if not specView.isDeleted and specView.isVisible() and
                        specView in self._spectrumSettings]
        _firstVisible = ((self._ordering[0], self._spectrumSettings[self._ordering[0]]),) if self._ordering and not self._ordering[0].isDeleted and self._ordering[0] in self._spectrumSettings else ()
        self._visibleOrderingDict = _visibleSpec or _firstVisible

        # quick fix to take the set of matching letters from the spectrum axisCodes - append a '*' to denote trailing differences
        if self.spectrumDisplay.is1D:
            # get the x-axis codes for 1d
            _axisCodes = [spec.spectrum.axisCodes[0] for spec, settings in self._visibleOrderingDict]
            _axisWildCards = (self._buildSingleWildCard(_axisCodes),
                              self.axisCodes[1] or '*')
        else:
            dim = len(self.spectrumDisplay.axisCodes)
            _axisWildCards = []
            for axis in range(dim):
                # get the correct x-axis mapped axis codes for Nd
                _axisCodes = []
                for spec, settings in self._visibleOrderingDict:
                    try:
                        _axisCodes.append(spec.spectrum.axisCodes[settings[GLDefs.SPECTRUM_POINTINDEX][axis]])
                    except Exception as es:
                        # can skip for now
                        pass
                _code = self._buildSingleWildCard(_axisCodes)
                _axisWildCards.append(_code)

        self._visibleOrderingAxisCodes = _axisWildCards


class GuiNdWidgetAxis(Gui1dWidgetAxis):
    """Testing a widget that only contains a right axis
    """
    is1D = False
    AXIS_MARGINRIGHT = 50
    AXIS_MARGINBOTTOM = 25
    AXIS_LINE = 7
    AXIS_OFFSET = 3
    AXIS_INSIDE = False
    YAXISUSEEFORMAT = False
    INVERTXAXIS = True
    INVERTYAXIS = True
    AXISLOCKEDBUTTON = True
    AXISLOCKEDBUTTONALLSTRIPS = True
    SPECTRUMXZOOM = 1.0e1
    SPECTRUMYZOOM = 1.0e1
    SHOWSPECTRUMONPHASING = True
    XAXES = GLDefs.XAXISUNITS
    YAXES = GLDefs.YAXISUNITS
    AXIS_MOUSEYOFFSET = AXIS_MARGINBOTTOM + (0 if AXIS_INSIDE else AXIS_LINE)

    def _buildSpectrumSetting(self, spectrumView, stackCount=0):
        # if spectrumView.spectrum.headerSize == 0:
        #     return

        self._spectrumSettings[spectrumView] = {}

        self._spectrumValues = spectrumView.getVisibleState()

        # set defaults for undefined spectra
        if not self._spectrumValues[0].pointCount:
            dx = -1.0 if self.INVERTXAXIS else -1.0
            fxMax, fxMin = 1.0, -1.0
            dxAF = fxMax - fxMin
            xScale = dx * dxAF

            dy = -1.0 if self.INVERTYAXIS else -1.0
            fyMax, fyMin = 1.0, -1.0
            dyAF = fyMax - fyMin
            yScale = dy * dyAF
            # xAliasingIndex = (0, 0)
            # yAliasingIndex = (0, 0)
            # xFoldingMode = yFoldingMode = None

            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fxMax - fxMin))
            self._maxXRange = max(self._maxXRange, (fxMax - fxMin))
            self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * (fyMax - fyMin))
            self._maxYRange = max(self._maxYRange, (fyMax - fyMin))

        else:

            # get the bounding box of the spectra
            dx = -1.0 if self.INVERTXAXIS else -1.0  # self.sign(self.axisR - self.axisL)
            fxMax, fxMin = self._spectrumValues[0].maxSpectrumFrequency, self._spectrumValues[0].minSpectrumFrequency
            # xAliasingIndex = self._spectrumValues[0].aliasingIndex
            # xFoldingMode = self._spectrumValues[0].foldingMode

            # check tolerances
            if not self._widthsChangedEnough((fxMax, 0.0), (fxMin, 0.0), tol=1e-10):
                fxMax, fxMin = 1.0, -1.0

            dxAF = fxMax - fxMin
            xScale = dx * dxAF / self._spectrumValues[0].pointCount

            dy = -1.0 if self.INVERTYAXIS else -1.0  # self.sign(self.axisT - self.axisB)
            fyMax, fyMin = self._spectrumValues[1].maxSpectrumFrequency, self._spectrumValues[1].minSpectrumFrequency
            # yAliasingIndex = self._spectrumValues[1].aliasingIndex
            # yFoldingMode = self._spectrumValues[1].foldingMode

            # check tolerances
            if not self._widthsChangedEnough((fyMax, 0.0), (fyMin, 0.0), tol=1e-10):
                fyMax, fyMin = 1.0, -1.0

            dyAF = fyMax - fyMin
            yScale = dy * dyAF / self._spectrumValues[1].pointCount

            # set to nD limits to twice the width of the spectrum and a few data points
            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fxMax - fxMin) / self._spectrumValues[0].pointCount)
            self._maxXRange = max(self._maxXRange, (fxMax - fxMin))
            self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * (fyMax - fyMin) / self._spectrumValues[1].pointCount)
            self._maxYRange = max(self._maxYRange, (fyMax - fyMin))

        self._rangeXDefined = True
        self._rangeYDefined = True

        # create modelview matrix for the spectrum to be drawn
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX] = np.zeros((16,), dtype=np.float32)

        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX][0:16] = [xScale, 0.0, 0.0, 0.0,
                                                                              0.0, yScale, 0.0, 0.0,
                                                                              0.0, 0.0, 1.0, 0.0,
                                                                              fxMax, fyMax, 0.0, 1.0]
        # setup information for the horizontal/vertical traces
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_XLIMITS] = (fxMin, fxMax)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_YLIMITS] = (fyMin, fyMax)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_AF] = (dxAF, dyAF)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_SCALE] = (xScale, yScale)
        # self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_SPINNINGRATE] = spectrumView.spectrum.spinningRate
        # self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_ALIASINGINDEX] = (xAliasingIndex, yAliasingIndex)
        # self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_FOLDINGMODE] = (xFoldingMode, yFoldingMode)

        indices = getAxisCodeMatchIndices(self.spectrumDisplay.axisCodes, spectrumView.spectrum.axisCodes)
        # only need the axes for this spectrum
        indices = indices[:spectrumView.spectrum.dimensionCount]
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX] = indices
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_REGIONBOUNDS] = (self._spectrumValues[0].regionBounds, self._spectrumValues[1].regionBounds)

        # if len(self._spectrumValues) > 2:
        #     # store a list for the extra dimensions - should only be one per spectrumDisplay really
        #     # needed so that the planeDepth is calculated correctly for visible spectra
        #     vPP = ()
        #     for dim in range(2, len(self._spectrumValues)):
        #         specVal = self._spectrumValues[dim]
        #         vPP = vPP + (specVal.valuePerPoint,)
        #
        #     self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = vPP
        #
        # else:
        #     self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = None

        self._maxX = max(self._maxX, fxMax)
        self._minX = min(self._minX, fxMin)
        self._maxY = max(self._maxY, fyMax)
        self._minY = min(self._minY, fyMin)

        self._buildAxisCodesWithWildCards()