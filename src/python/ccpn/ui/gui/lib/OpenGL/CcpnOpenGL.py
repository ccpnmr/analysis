"""
By Functionality:

Zoom and pan:
    Left-drag:                          pans the spectrum.

    shift-left-drag:                    draws a zooming box and zooms the viewing window.
    shift-middle-drag:                  draws a zooming box and zooms the viewing window.
    shift-right-drag:                   draws a zooming box and zooms the viewing window.
    Two successive shift-right-clicks:  define zoombox
    control-right click:                reset the zoom

Peaks:
    Left-click:                         select peak near cursor in a spectrum display, deselecting others
    Control(Cmd)-left-click:            (de)select peak near cursor in a spectrum display, adding/removing to selection.
    Control(Cmd)-left-drag:             selects peaks in an area specified by the dragged region.
    Middle-drag:                        Moves a selected peak.
    Control(Cmd)-Shift-Left-click:      picks a peak at the cursor position, adding to selection
    Control(Cmd)-shift-left-drag:       picks peaks in an area specified by the dragged region.

Others:
    Right-click:                        raises the context menu.


By Mouse button:

    Left-click:                         select peak near cursor in a spectrum display, deselecting others
    Control(Cmd)-left-click:            (de)select peak near cursor in a spectrum display, adding/removing to selection.
    Control(Cmd)-Shift-Left-click:      picks a peak at the cursor position, adding to selection

    Left-drag:                          pans the spectrum.
    shift-left-drag:                    draws a zooming box and zooms the viewing window.
    Control(Cmd)-left-drag:             selects peaks in an area specified by the dragged region.
    Control(Cmd)-shift-left-drag:       picks peaks in an area specified by the dragged region.


    shift-middle-drag:                  draws a zooming box and zooms the viewing window.

    Right-click:                        raises the context menu.
    control-right click:                reset the zoom
    Two successive shift-right-clicks:  define zoombox

    shift-right-drag:                   draws a zooming box and zooms the viewing window.
"""
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2018-12-20 16:43:53 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
import math
import json
import re
import time
import numpy as np
from functools import partial
# from threading import Thread
# from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPoint, QSize, Qt, pyqtSlot
from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from ccpn.util.Logging import getLogger
from pyqtgraph import functions as fn
from ccpn.core.PeakList import PeakList
from ccpn.core.Integral import Integral
# from ccpn.core.IntegralList import IntegralList
from ccpn.ui.gui.lib.mouseEvents import getCurrentMouseMode
from ccpn.ui.gui.lib.GuiStrip import DefaultMenu, PeakMenu, IntegralMenu, \
    MultipletMenu, PhasingMenu

from ccpn.core.lib.Cache import cached

# from ccpn.util.Colour import getAutoColourRgbRatio
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_BACKGROUND, CCPNGLWIDGET_FOREGROUND, CCPNGLWIDGET_PICKCOLOUR, \
    CCPNGLWIDGET_GRID, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_INTEGRALSHADE, \
    CCPNGLWIDGET_LABELLING, CCPNGLWIDGET_PHASETRACE, getColours, \
    CCPNGLWIDGET_HEXBACKGROUND, CCPNGLWIDGET_ZOOMAREA, CCPNGLWIDGET_PICKAREA, \
    CCPNGLWIDGET_SELECTAREA, CCPNGLWIDGET_ZOOMLINE, CCPNGLWIDGET_MOUSEMOVELINE, \
    CCPNGLWIDGET_HARDSHADE
# from ccpn.ui.gui.lib.GuiPeakListView import _getScreenPeakAnnotation, _getPeakAnnotation  # temp until I rewrite
import ccpn.util.Phasing as Phasing
from ccpn.ui.gui.lib.mouseEvents import \
    leftMouse, shiftLeftMouse, controlLeftMouse, controlShiftLeftMouse, controlShiftRightMouse, \
    middleMouse, shiftMiddleMouse, rightMouse, shiftRightMouse, controlRightMouse, PICK


# from ccpn.core.lib.Notifiers import Notifier

try:
    # used to test whether all the arrays are defined correctly
    # os.environ.update({'PYOPENGL_ERROR_ON_COPY': 'true'})

    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)

from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLNotifier import GLNotifier
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import GLGlobalData
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import GLString
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLRENDERMODE_IGNORE, GLRENDERMODE_DRAW, \
    GLRENDERMODE_RESCALE, GLRENDERMODE_REBUILD, \
    GLREFRESHMODE_NEVER, GLREFRESHMODE_ALWAYS, \
    GLREFRESHMODE_REBUILD, GLVertexArray, \
    GLSymbolArray, GLLabelArray
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLViewports import GLViewports
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLWidgets import GLExternalRegion, \
    GLRegion, REGION_COLOURS, GLInfiniteLine
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLLabelling import GLpeakNdLabelling, GLpeak1dLabelling, \
    GLintegral1dLabelling, GLintegralNdLabelling, \
    GLmultiplet1dLabelling, GLmultipletNdLabelling
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLExport import GLExporter
import ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs as GLDefs
# from ccpn.util.Common import makeIterableList
from typing import Tuple
from ccpn.util.Constants import AXIS_FULLATOMNAME, AXIS_MATCHATOMTYPE, AXIS_ACTIVEAXES
from ccpn.ui.gui.guiSettings import textFont, getColours, STRIPHEADER_BACKGROUND, \
    STRIPHEADER_FOREGROUND, GUINMRRESIDUE

from ccpn.ui.gui.widgets.DropBase import DropBase
from ccpn.ui.gui.lib.mouseEvents import getMouseEventDict
from ccpn.core.lib.ContextManagers import undoBlock
from ccpn.util.decorators import profile


UNITS_PPM = 'ppm'
UNITS_HZ = 'Hz'
UNITS_POINT = 'point'
UNITS = [UNITS_PPM, UNITS_HZ, UNITS_POINT]
SINGLECLICK = 'click'
DOUBLECLICK = 'doubleClick'

ZOOMTIMERDELAY = 2
ZOOMMAXSTORE = 1
ZOOMHISTORYSTORE = 10

removeTrailingZero = re.compile(r'^(\d*[\d.]*?)\.?0*$')


class CcpnGLWidget(QOpenGLWidget):
    """Widget to handle all visible spectra/peaks/integrals/multiplets
    """
    AXIS_MARGINRIGHT = 50
    AXIS_MARGINBOTTOM = 25
    AXIS_LINE = 7
    AXIS_OFFSET = 3
    YAXISUSEEFORMAT = False
    INVERTXAXIS = True
    INVERTYAXIS = True
    AXISLOCKEDBUTTON = True
    SPECTRUMXZOOM = 1.0e1
    SPECTRUMYZOOM = 1.0e1
    SHOWSPECTRUMONPHASING = True
    XAXES = GLDefs.XAXISUNITS
    YAXES = GLDefs.YAXISUNITS

    def __init__(self, strip=None, mainWindow=None, stripIDLabel=None):
        # TODO:ED add documentation

        super().__init__(strip)

        # flag to display paintGL but keep an empty screen
        self._blankDisplay = False

        if not strip:  # don't initialise if nothing there
            return

        self.strip = strip
        self.spectrumDisplay = strip.spectrumDisplay

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

        # add a flag so that scaling cannot be done until the gl attributes are initialised
        self.glReady = False

        self.stripIDLabel = stripIDLabel if stripIDLabel else ''

        self.setMouseTracking(True)  # generate mouse events when button not pressed

        # always respond to mouse events
        self.setFocusPolicy(Qt.StrongFocus)

        # initialise all attributes
        self._initialiseAll()

        # set a minimum size so that the strips resize nicely
        self.setMinimumSize(self.AXIS_MARGINRIGHT + 10, self.AXIS_MARGINBOTTOM + 10)

        # set the pyqtsignal responders
        self.GLSignals = GLNotifier(parent=self, strip=strip)
        self.GLSignals.glXAxisChanged.connect(self._glXAxisChanged)
        self.GLSignals.glYAxisChanged.connect(self._glYAxisChanged)
        self.GLSignals.glAllAxesChanged.connect(self._glAllAxesChanged)
        self.GLSignals.glMouseMoved.connect(self._glMouseMoved)
        self.GLSignals.glEvent.connect(self._glEvent)
        self.GLSignals.glAxisLockChanged.connect(self._glAxisLockChanged)
        self.GLSignals.glAxisUnitsChanged.connect(self._glAxisUnitsChanged)

    def _initialiseAll(self):
        """Initialise all attributes for the display
        """
        # if self.glReady: return

        self.w = self.width()
        self.h = self.height()

        self._threads = {}
        self._threadUpdate = False

        self.lastPos = QPoint()
        self._mouseX = 0
        self._mouseY = 0
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
        self.cursorCoordinate = np.zeros((4,), dtype=np.float32)

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

        self.gridList = []
        self._gridVisible = self._preferences.showGrid
        self._crosshairVisible = self._preferences.showCrosshair
        self._axesVisible = True
        self._axisLocked = False
        self._showSpectraOnPhasing = False
        self._xUnits = 0
        self._yUnits = 0

        self._drawRightAxis = True
        self._drawBottomAxis = True
        self.modeDecimal = [False, False]

        # here for completeness, although they should be updated in rescale
        self._currentView = GLDefs.MAINVIEW
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

        self._applyXLimit = self._preferences.zoomXLimitApply
        self._applyYLimit = self._preferences.zoomYLimitApply
        self._intensityLimit = self._preferences.intensityLimit

        self._GLIntegralLists = {}
        self._GLIntegralLabels = {}

        self._marksAxisCodes = []
        self._regions = []
        self._infiniteLines = []
        self._buildTextFlag = True

        # define a new class holding the entire peaklist symbols and labelling
        if self.is1D:
            self._GLPeaks = GLpeak1dLabelling(parent=self, strip=self.strip,
                                              name='peaks', resizeGL=True)
            self._GLIntegrals = GLintegral1dLabelling(parent=self, strip=self.strip,
                                                      name='integrals', resizeGL=True)
            self._GLMultiplets = GLmultiplet1dLabelling(parent=self, strip=self.strip,
                                                        name='multiplets', resizeGL=True)
        else:
            self._GLPeaks = GLpeakNdLabelling(parent=self, strip=self.strip,
                                              name='peaks', resizeGL=True)
            self._GLIntegrals = GLintegralNdLabelling(parent=self, strip=self.strip,
                                                      name='integrals', resizeGL=True)
            self._GLMultiplets = GLmultipletNdLabelling(parent=self, strip=self.strip,
                                                        name='multiplets', resizeGL=True)

        self._buildMouse = True
        self._mouseCoords = [-1.0, -1.0]
        self.mouseString = None
        self.diffMouseString = None
        self.peakLabelling = 0

        self._contourList = {}

        self._hTraces = {}
        self._vTraces = {}
        self._staticHTraces = []
        self._staticVTraces = []
        self._currentTraces = []

        self._stackingValue = 0.0
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
        self._view = np.zeros((4,), dtype=np.float32)
        self.cursorCoordinate = np.zeros((4,), dtype=np.float32)

        # get information from the parent class (strip)
        self.orderedAxes = self.strip.orderedAxes
        self.axisOrder = self.strip.axisOrder
        self.axisCodes = self.strip.axisCodes

        self._dragRegions = set()

        self.resetRangeLimits()

        self._ordering = []
        self._firstVisible = None
        self.visiblePlaneList = {}
        self._visibleSpectrumViewsChange = False

        self._glClientIndex = 0
        self.glReady = True

    def close(self):
        self.GLSignals.glXAxisChanged.disconnect()
        self.GLSignals.glYAxisChanged.disconnect()
        self.GLSignals.glAllAxesChanged.disconnect()
        self.GLSignals.glMouseMoved.disconnect()
        self.GLSignals.glEvent.disconnect()
        self.GLSignals.glAxisLockChanged.disconnect()
        self.GLSignals.glAxisUnitsChanged.disconnect()

    def threadUpdate(self):
        self.update()

    def rescale(self, rescaleOverlayText=True, rescaleMarksRulers=True,
                rescaleIntegralLists=True, rescaleRegions=True,
                rescaleSpectra=True, rescaleStaticHTraces=True,
                rescaleStaticVTraces=True):
        """Change to axes of the view, axis visibility, scale and rebuild matrices when necessary
        to improve display speed
        """
        if self.strip.isDeleted or not self.globalGL:
            return

        # use the updated size
        w = self.w
        h = self.h

        currentShader = self.globalGL._shaderProgram1.makeCurrent()

        # set projection to axis coordinates
        currentShader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB,
                                        self.axisT, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)

        # needs to be offset from (0,0) for mouse scaling
        if self._drawRightAxis and self._drawBottomAxis:

            self._currentView = GLDefs.MAINVIEW
            self._currentRightAxisView = GLDefs.RIGHTAXIS
            self._currentRightAxisBarView = GLDefs.RIGHTAXISBAR
            self._currentBottomAxisView = GLDefs.BOTTOMAXIS
            self._currentBottomAxisBarView = GLDefs.BOTTOMAXISBAR

            currentShader.setViewportMatrix(self._uVMatrix, 0, w - self.AXIS_MARGINRIGHT, 0, h - self.AXIS_MARGINBOTTOM,
                                            -1.0, 1.0)
            self.pixelX = (self.axisR - self.axisL) / (w - self.AXIS_MARGINRIGHT)
            self.pixelY = (self.axisT - self.axisB) / (h - self.AXIS_MARGINBOTTOM)
            self.deltaX = 1.0 / (w - self.AXIS_MARGINRIGHT)
            self.deltaY = 1.0 / (h - self.AXIS_MARGINBOTTOM)

        elif self._drawRightAxis and not self._drawBottomAxis:

            self._currentView = GLDefs.MAINVIEWFULLHEIGHT
            self._currentRightAxisView = GLDefs.FULLRIGHTAXIS
            self._currentRightAxisBarView = GLDefs.FULLRIGHTAXISBAR

            currentShader.setViewportMatrix(self._uVMatrix, 0, w - self.AXIS_MARGINRIGHT, 0, h, -1.0, 1.0)
            self.pixelX = (self.axisR - self.axisL) / (w - self.AXIS_MARGINRIGHT)
            self.pixelY = (self.axisT - self.axisB) / h
            self.deltaX = 1.0 / (w - self.AXIS_MARGINRIGHT)
            self.deltaY = 1.0 / h

        elif not self._drawRightAxis and self._drawBottomAxis:

            self._currentView = GLDefs.MAINVIEWFULLWIDTH
            self._currentBottomAxisView = GLDefs.FULLBOTTOMAXIS
            self._currentBottomAxisBarView = GLDefs.FULLBOTTOMAXISBAR

            currentShader.setViewportMatrix(self._uVMatrix, 0, w, 0, h - self.AXIS_MARGINBOTTOM, -1.0, 1.0)
            self.pixelX = (self.axisR - self.axisL) / w
            self.pixelY = (self.axisT - self.axisB) / (h - self.AXIS_MARGINBOTTOM)
            self.deltaX = 1.0 / w
            self.deltaY = 1.0 / (h - self.AXIS_MARGINBOTTOM)

        else:

            self._currentView = GLDefs.FULLVIEW

            currentShader.setViewportMatrix(self._uVMatrix, 0, w, 0, h, -1.0, 1.0)
            self.pixelX = (self.axisR - self.axisL) / w
            self.pixelY = (self.axisT - self.axisB) / h
            self.deltaX = 1.0 / w
            self.deltaY = 1.0 / h

        self.symbolX = abs(self.strip.symbolSize * self.pixelX)
        self.symbolY = abs(self.strip.symbolSize * self.pixelY)

        self._dataMatrix[0:16] = [self.axisL, self.axisR, self.axisT, self.axisB,
                                  self.pixelX, self.pixelY, w, h,
                                  0.2, 1.0, 0.4, 1.0,
                                  0.3, 0.1, 1.0, 1.0]
        currentShader.setGLUniformMatrix4fv('dataMatrix', 1, GL.GL_FALSE, self._dataMatrix)
        currentShader.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._IMatrix)

        # map mouse coordinates to world coordinates - only needs to change on resize, move soon
        currentShader.setViewportMatrix(self._aMatrix, self.axisL, self.axisR, self.axisB,
                                        self.axisT, -1.0, 1.0)

        # calculate the screen to axes transform
        self.vInv = np.linalg.inv(self._uVMatrix.reshape((4, 4)))
        self.mouseTransform = np.matmul(self._aMatrix.reshape((4, 4)), self.vInv)

        self.modelViewMatrix = (GL.GLdouble * 16)()
        self.projectionMatrix = (GL.GLdouble * 16)()
        self.viewport = (GL.GLint * 4)()

        # change to the text shader
        currentShader = self.globalGL._shaderProgramTex.makeCurrent()

        currentShader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB, self.axisT, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, self._uPMatrix)

        self._axisScale[0:4] = [self.pixelX, self.pixelY, 1.0, 1.0]
        self._view[0:4] = [w - self.AXIS_MARGINRIGHT, h - self.AXIS_MARGINBOTTOM, 1.0, 1.0]

        # self._axisScale[0:4] = [1.0/(self.axisR-self.axisL), 1.0/(self.axisT-self.axisB), 1.0, 1.0]
        currentShader.setGLUniform4fv('axisScale', 1, self._axisScale)
        currentShader.setGLUniform4fv('viewport', 1, self._view)

        if rescaleOverlayText:
            self._rescaleOverlayText()

        if rescaleMarksRulers:
            self.rescaleMarksRulers()

        if rescaleIntegralLists:
            self._GLIntegrals.rescaleIntegralLists()
            self._GLIntegrals.rescale()

        if rescaleRegions:
            self._rescaleRegions()

        if rescaleSpectra:
            self.rescaleSpectra()

        if rescaleStaticHTraces:
            self.rescaleStaticHTraces()

        if rescaleStaticVTraces:
            self.rescaleStaticVTraces()

    def setStackingValue(self, val):
        self._stackingValue = val

    def setStackingMode(self, value):
        self._stackingMode = value
        self.rescaleSpectra()
        self.update()

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

    def rescaleSpectra(self):
        if self.strip.isDeleted:
            return
        self.updateVisibleSpectrumViews()
        # rescale the matrices for each spectrumView
        # stackCount = 0
        self.resetRangeLimits(allLimits=False)

        for stackCount, spectrumView in enumerate(self._ordering):  # _ordering:                             # strip.spectrumViews:  #.orderedSpectrumViews():
            # self._spectrumSettings[spectrumView] = {}

            if spectrumView.isDeleted:
                self._spectrumSettings[spectrumView] = {}
                continue

            self._buildSpectrumSetting(spectrumView=spectrumView, stackCount=stackCount)
            # if self._stackingMode:
            #     stackCount += 1

    def _setRegion(self, region, value):
        self.strip.project._undo.increaseBlocking()
        if region:
            region.region = value
        self.strip.project._undo.decreaseBlocking()

    def autoRange(self):
        self._updateVisibleSpectrumViews()
        for spectrumView in self._ordering:  # strip.spectrumViews:  #.orderedSpectrumViews():
            if spectrumView.isDeleted:
                self._spectrumSettings[spectrumView] = {}
                continue

            self._buildSpectrumSetting(spectrumView)

            axis = self._orderedAxes[0]
            # axis.region = (float(self._minX), float(self._maxX))
            self._setRegion(axis, (float(self._minX), float(self._maxX)))

            if self.INVERTXAXIS:
                self.axisL = max(axis.region[0], axis.region[1])
                self.axisR = min(axis.region[0], axis.region[1])
            else:
                self.axisL = min(axis.region[0], axis.region[1])
                self.axisR = max(axis.region[0], axis.region[1])

            axis = self._orderedAxes[1]
            # axis.region = (float(self._minY), float(self._maxY))
            self._setRegion(axis, (float(self._minY), float(self._maxY)))

            if self.INVERTYAXIS:
                self.axisB = max(axis.region[0], axis.region[1])
                self.axisT = min(axis.region[0], axis.region[1])
            else:
                self.axisB = min(axis.region[0], axis.region[1])
                self.axisT = max(axis.region[0], axis.region[1])

    def _buildSpectrumSetting(self, spectrumView, stackCount=0):
        # if spectrumView.spectrum.headerSize == 0:
        #     return

        self._spectrumSettings[spectrumView] = {}

        self._spectrumValues = spectrumView._getValues()

        # set defaults for undefined spectra
        if not self._spectrumValues[0].totalPointCount:
            dx = -1.0 if self.INVERTXAXIS else -1.0
            fx0, fx1 = 1.0, -1.0
            dxAF = fx0 - fx1
            xScale = dx * dxAF

            dy = -1.0 if self.INVERTYAXIS else -1.0
            fy0, fy1 = 1.0, -1.0
            dyAF = fy0 - fy1
            yScale = dy * dyAF

            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fx0 - fx1))
            self._maxXRange = max(self._maxXRange, (fx0 - fx1))
            self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * (fy0 - fy1))
            self._maxYRange = max(self._maxYRange, (fy0 - fy1))

        else:

            # get the bounding box of the spectra
            dx = -1.0 if self.INVERTXAXIS else -1.0  # self.sign(self.axisR - self.axisL)
            fx0, fx1 = self._spectrumValues[0].maxAliasedFrequency, self._spectrumValues[0].minAliasedFrequency

            # check tolerances
            if not self._widthsChangedEnough((fx0, 0.0), (fx1, 0.0), tol=1e-10):
                fx0, fx1 = 1.0, -1.0

            dxAF = fx0 - fx1
            xScale = dx * dxAF / self._spectrumValues[0].totalPointCount

            if spectrumView.spectrum.dimensionCount > 1:
                dy = -1.0 if self.INVERTYAXIS else -1.0  # self.sign(self.axisT - self.axisB)
                fy0, fy1 = self._spectrumValues[1].maxAliasedFrequency, self._spectrumValues[1].minAliasedFrequency

                # check tolerances
                if not self._widthsChangedEnough((fy0, 0.0), (fy1, 0.0), tol=1e-10):
                    fy0, fy1 = 1.0, -1.0

                dyAF = fy0 - fy1
                yScale = dy * dyAF / self._spectrumValues[1].totalPointCount

                # set to nD limits to twice the width of the spectrum and a few data points
                self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fx0 - fx1) / self._spectrumValues[0].totalPointCount)
                self._maxXRange = max(self._maxXRange, (fx0 - fx1))
                self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * (fy0 - fy1) / self._spectrumValues[1].totalPointCount)
                self._maxYRange = max(self._maxYRange, (fy0 - fy1))

            else:
                dy = -1.0 if self.INVERTYAXIS else -1.0  # dy = self.sign(self.axisT - self.axisB)

                if spectrumView.spectrum.intensities is not None and spectrumView.spectrum.intensities.size != 0:
                    fy0, fy1 = np.max(spectrumView.spectrum.intensities), np.min(spectrumView.spectrum.intensities)
                else:
                    fy0, fy1 = 0.0, 0.0

                # check tolerances
                if not self._widthsChangedEnough((fy0, 0.0), (fy1, 0.0), tol=1e-10):
                    fy0, fy1 = 1.0, -1.0

                dyAF = fy0 - fy1
                yScale = dy * dyAF / 1.0

                # set to 1D limits to twice the width of the spectrum and the intensity limit
                self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * (fx0 - fx1) / max(self._spectrumValues[0].totalPointCount, self.SPECTRUMXZOOM))
                self._maxXRange = max(self._maxXRange, (fx0 - fx1))
                # self._minYRange = min(self._minYRange, 3.0 * (fy0 - fy1) / self.SPECTRUMYZOOM)
                self._minYRange = min(self._minYRange, self._intensityLimit)
                self._maxYRange = max(self._maxYRange, (fy0 - fy1))

                self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIX] = np.zeros((16,), dtype=np.float32)

                # if self._stackingMode:
                st = stackCount * self._stackingValue
                # stackCount += 1
                self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIX][0:16] = [1.0, 0.0, 0.0, 0.0,
                                                                                             0.0, 1.0, 0.0, 0.0,
                                                                                             0.0, 0.0, 1.0, 0.0,
                                                                                             0.0, st, 0.0, 1.0]
                # else:
                #     self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_STACKEDMATRIX][0:16] = [1.0, 0.0, 0.0, 0.0,
                #                                                                                  0.0, 1.0, 0.0, 0.0,
                #                                                                                  0.0, 0.0, 1.0, 0.0,
                #                                                                                  0.0, 0.0, 0.0, 1.0]

        self._rangeXDefined = True
        self._rangeYDefined = True

        # create modelview matrix for the spectrum to be drawn
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX] = np.zeros((16,), dtype=np.float32)

        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX][0:16] = [xScale, 0.0, 0.0, 0.0,
                                                                              0.0, yScale, 0.0, 0.0,
                                                                              0.0, 0.0, 1.0, 0.0,
                                                                              fx0, fy0, 0.0, 1.0]
        # setup information for the horizontal/vertical traces
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXXALIAS] = fx0
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINXALIAS] = fx1
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXYALIAS] = fy0
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINYALIAS] = fy1
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DXAF] = dxAF
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DYAF] = dyAF
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_XSCALE] = xScale
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_YSCALE] = yScale

        if spectrumView.spectrum.dimensionCount > 1:
            # get the ordering of the strip axisCodes in the spectrum
            try:
                indices = spectrumView.spectrum.getByAxisCodes('indices', self.strip.axisCodes,
                                                               exactMatch=(self._preferences.matchAxisCode == 1))
            except Exception as es:

                # spectrum possibly no compatible here, may be 2d overlaid onto Nd
                indices = spectrumView.spectrum.getByAxisCodes('indices', self.strip.axisCodes[0:2],
                                                               exactMatch=(self._preferences.matchAxisCode == 1))
        else:
            indices = (0,)  # spectrumView.spectrum.getByAxisCodes('indices', self.strip.axisCodes)

        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX] = indices

        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_YSCALE] = yScale

        if len(self._spectrumValues) > 2:
            specVal = self._spectrumValues[2]
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = specVal.valuePerPoint
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DATADIM] = specVal.dataDim

            if hasattr(specVal.dataDim, 'primaryDataDimRef'):
                ddr = specVal.dataDim.primaryDataDimRef
                valueToPoint = ddr and ddr.valueToPoint
            else:
                valueToPoint = specVal.dataDim.valueToPoint

            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUETOPOINT] = valueToPoint
        else:
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = None
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DATADIM] = None
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUETOPOINT] = None

        self._maxX = max(self._maxX, fx0)
        self._minX = min(self._minX, fx1)
        self._maxY = max(self._maxY, fy0)
        self._minY = min(self._minY, fy1)

    def refreshDevicePixelRatio(self):
        """refresh the devicePixelRatio for the viewports
        """
        # control for changing screens has now been moved to mainWindow so only one signal is needed
        self.viewports._devicePixelRatio = self.devicePixelRatio()
        self.update()

    def _getValidAspectRatio(self, axisCode):
        va = [ax for ax in self._preferences.aspectRatios.keys() if ax.upper()[0] == axisCode.upper()[0]]
        return self._preferences.aspectRatios[va[0]]

    def resizeGL(self, w, h):
        # must be set here to catch the change of screen
        self.refreshDevicePixelRatio()

        self.w = w
        self.h = h

        if self._axisLocked:
            ax0 = self._getValidAspectRatio(self._axisCodes[0])
            ax1 = self._getValidAspectRatio(self._axisCodes[1])

            if (self.h / self.w) > 1:
                mby = 0.5 * (self.axisT + self.axisB)

                ratio = (self.h / self.w) * 0.5 * abs(self.axisL - self.axisR) * ax1 / ax0
                self.axisB = mby + ratio * self.sign(self.axisB - mby)
                self.axisT = mby - ratio * self.sign(mby - self.axisT)
            else:
                mbx = 0.5 * (self.axisR + self.axisL)

                ratio = (self.w / self.h) * 0.5 * abs(self.axisT - self.axisB) * ax0 / ax1
                self.axisL = mbx + ratio * self.sign(self.axisL - mbx)
                self.axisR = mbx - ratio * self.sign(mbx - self.axisR)

        self.rescale()

        # put stuff in here that will change on a resize
        for li in self.gridList:
            li.renderMode = GLRENDERMODE_REBUILD
        self._GLPeaks.rescale()
        self._GLMultiplets.rescale()

        self.update()

    def viewRange(self):
        return ((self.axisL, self.axisR),
                (self.axisT, self.axisB))

    def wheelEvent(self, event):
        # def between(val, l, r):
        #   return (l-val)*(r-val) <= 0

        if self.strip and not self._ordering:  # strip.spectrumViews:
            event.accept()
            return

        numPixels = event.pixelDelta()
        numDegrees = event.angleDelta()
        zoomCentre = self._preferences.zoomCentreType

        zoomScale = 0.0
        if numPixels:

            # always seems to be numPixels - check with Linux
            scrollDirection = numPixels.y()
            zoomScale = 8.0

            # stop the very sensitive movements
            if abs(scrollDirection) < 1:
                event.ignore()
                return

        elif numDegrees:

            # this may work when using Linux
            scrollDirection = numDegrees.y() / 4
            zoomScale = 8.0

            # stop the very sensitive movements
            if abs(scrollDirection) < 1:
                event.ignore()
                return

        else:
            event.ignore()
            return

        # test whether the limits have been reached in either axis
        if (scrollDirection > 0 and self._minReached and self._axisLocked) or \
                (scrollDirection < 0 and self._maxReached and self._axisLocked):
            event.accept()
            return

        zoomIn = (100.0 + zoomScale) / 100.0
        zoomOut = 100.0 / (100.0 + zoomScale)

        h = self.h
        w = self.w

        # find the correct viewport
        mw = [0, self.AXIS_MARGINBOTTOM, w - self.AXIS_MARGINRIGHT, h - 1]
        ba = [0, 0, w - self.AXIS_MARGINRIGHT, self.AXIS_MARGINBOTTOM - 1]
        ra = [w - self.AXIS_MARGINRIGHT, self.AXIS_MARGINBOTTOM, w, h]

        mx = event.pos().x()
        my = self.height() - event.pos().y()

        if self.between(mx, mw[0], mw[2]) and self.between(my, mw[1], mw[3]):

            # if in the mainView

            if (scrollDirection > 0 and self._minReached) or \
                    (scrollDirection < 0 and self._maxReached):
                event.accept()
                return

            if zoomCentre == 0:  # centre on mouse
                mb0 = (mx - mw[0]) / (mw[2] - mw[0])
                mb1 = (my - mw[1]) / (mw[3] - mw[1])
            else:  # centre on the screen
                mb0 = 0.5
                mb1 = 0.5

            mbx = self.axisL + mb0 * (self.axisR - self.axisL)
            mby = self.axisB + mb1 * (self.axisT - self.axisB)

            if scrollDirection < 0:
                self.axisL = mbx + zoomIn * (self.axisL - mbx)
                self.axisR = mbx - zoomIn * (mbx - self.axisR)
                self.axisB = mby + zoomIn * (self.axisB - mby)
                self.axisT = mby - zoomIn * (mby - self.axisT)
            else:
                self.axisL = mbx + zoomOut * (self.axisL - mbx)
                self.axisR = mbx - zoomOut * (mbx - self.axisR)
                self.axisB = mby + zoomOut * (self.axisB - mby)
                self.axisT = mby - zoomOut * (mby - self.axisT)

            self.GLSignals._emitAllAxesChanged(source=self, strip=self.strip,
                                               axisB=self.axisB, axisT=self.axisT,
                                               axisL=self.axisL, axisR=self.axisR)

            self._rescaleAllAxes()
            self._storeZoomHistory()

        elif self.between(mx, ba[0], ba[2]) and self.between(my, ba[1], ba[3]):

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

            if not self._axisLocked:
                self.GLSignals._emitXAxisChanged(source=self, strip=self.strip,
                                                 axisB=self.axisB, axisT=self.axisT,
                                                 axisL=self.axisL, axisR=self.axisR)

                self._rescaleXAxis()
                self._storeZoomHistory()

            else:
                mby = 0.5 * (self.axisT + self.axisB)

                ax0 = self._getValidAspectRatio(self._axisCodes[0])
                ax1 = self._getValidAspectRatio(self._axisCodes[1])

                ratio = (self.h / self.w) * 0.5 * abs(self.axisL - self.axisR) * ax1 / ax0
                self.axisB = mby + ratio * self.sign(self.axisB - mby)
                self.axisT = mby - ratio * self.sign(mby - self.axisT)

                self.GLSignals._emitAllAxesChanged(source=self, strip=self.strip,
                                                   axisB=self.axisB, axisT=self.axisT,
                                                   axisL=self.axisL, axisR=self.axisR)

                self._rescaleAllAxes()
                self._storeZoomHistory()

        elif self.between(mx, ra[0], ra[2]) and self.between(my, ra[1], ra[3]):

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

            if not self._axisLocked:
                self.GLSignals._emitYAxisChanged(source=self, strip=self.strip,
                                                 axisB=self.axisB, axisT=self.axisT,
                                                 axisL=self.axisL, axisR=self.axisR)

                self._rescaleYAxis()
                self._storeZoomHistory()

            else:
                mbx = 0.5 * (self.axisR + self.axisL)

                ax0 = self._getValidAspectRatio(self._axisCodes[0])
                ax1 = self._getValidAspectRatio(self._axisCodes[1])

                ratio = (self.w / self.h) * 0.5 * abs(self.axisT - self.axisB) * ax0 / ax1
                self.axisL = mbx + ratio * self.sign(self.axisL - mbx)
                self.axisR = mbx - ratio * self.sign(mbx - self.axisR)

                self.GLSignals._emitAllAxesChanged(source=self, strip=self.strip,
                                                   axisB=self.axisB, axisT=self.axisT,
                                                   axisL=self.axisL, axisR=self.axisR)

                self._rescaleAllAxes()
                self._storeZoomHistory()

        event.accept()

    def _scaleToYAxis(self):
        if self._axisLocked:
            mbx = 0.5 * (self.axisR + self.axisL)

            ax0 = self._getValidAspectRatio(self._axisCodes[0])
            ax1 = self._getValidAspectRatio(self._axisCodes[1])

            ratio = (self.w / self.h) * 0.5 * abs(self.axisT - self.axisB) * ax0 / ax1
            self.axisL = mbx + ratio * self.sign(self.axisL - mbx)
            self.axisR = mbx - ratio * self.sign(mbx - self.axisR)

            # self.GLSignals._emitAllAxesChanged(source=self, strip=self.strip,
            #                                    axisB=self.axisB, axisT=self.axisT,
            #                                    axisL=self.axisL, axisR=self.axisR)

        self._rescaleAllAxes()

    def _rescaleXAxis(self, update=True):
        self._testAxisLimits()
        self.rescale(rescaleStaticHTraces=False)

        # spawn rebuild event for the grid
        if self.gridList:
            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD
            # self.gridList[0].renderMode = GLRENDERMODE_REBUILD
            # self.gridList[2].renderMode = GLRENDERMODE_REBUILD

        # ratios have changed so rescale the peak/multiplet symbols
        self._GLPeaks.rescale()
        self._GLMultiplets.rescale()

        self._rescaleOverlayText()

        if update:
            self.update()

        # self.project._startCommandEchoBlock('_rescaleXAxis', quiet=True)
        try:
            # self._orderedAxes[0].region = (self.axisL, self.axisR)
            self._setRegion(self._orderedAxes[0], (self.axisL, self.axisR))
        except:
            getLogger().debug('error setting viewing window X-range')
        # finally:
        #     self.project._endCommandEchoBlock()

    def _rescaleYAxis(self, update=True):
        self._testAxisLimits()
        self.rescale(rescaleStaticVTraces=False)

        # spawn rebuild event for the grid
        if self.gridList:
            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD
            # self.gridList[0].renderMode = GLRENDERMODE_REBUILD
            # self.gridList[1].renderMode = GLRENDERMODE_REBUILD

        # ratios have changed so rescale the peak/multiplet symbols
        self._GLPeaks.rescale()
        self._GLMultiplets.rescale()

        self._rescaleOverlayText()

        if update:
            self.update()

        # self.project._startCommandEchoBlock('_rescaleYAxis', quiet=True)
        try:
            # self._orderedAxes[1].region = (self.axisT, self.axisB)
            self._setRegion(self._orderedAxes[1], (self.axisT, self.axisB))

        except Exception as es:
            getLogger().debug('error setting viewing window Y-range')
        # finally:
        #     self.project._endCommandEchoBlock()

    def _rebuildMarks(self, update=True):
        self.rescale(rescaleStaticHTraces=False, rescaleStaticVTraces=False)

        # spawn rebuild event for the grid
        for li in self.gridList:
            li.renderMode = GLRENDERMODE_REBUILD
        self._marksList.renderMode = GLRENDERMODE_REBUILD

        self._rescaleOverlayText()

        if update:
            self.update()

    def _testAxisLimits(self, setLimits=False):
        xRange = abs(self.axisL - self.axisR) / 2.0
        yRange = abs(self.axisT - self.axisB) / 2.0
        self._minXReached = False
        self._minYReached = False
        self._maxXReached = False
        self._maxYReached = False

        if xRange < self._minXRange and self._rangeXDefined and self._applyXLimit:
            if setLimits:
                xMid = (self.axisR + self.axisL) / 2.0
                self.axisL = xMid - self._minXRange * np.sign(self.pixelX)
                self.axisR = xMid + self._minXRange * np.sign(self.pixelX)
            self._minXReached = True

        if yRange < self._minYRange and self._rangeYDefined and self._applyYLimit:
            if setLimits:
                yMid = (self.axisT + self.axisB) / 2.0
                self.axisT = yMid + self._minYRange * np.sign(self.pixelY)
                self.axisB = yMid - self._minYRange * np.sign(self.pixelY)
            self._minYReached = True

        if xRange > self._maxXRange and self._rangeXDefined and self._applyXLimit:
            if setLimits:
                xMid = (self.axisR + self.axisL) / 2.0
                self.axisL = xMid - self._maxXRange * np.sign(self.pixelX)
                self.axisR = xMid + self._maxXRange * np.sign(self.pixelX)
            self._maxXReached = True

        if yRange > self._maxYRange and self._rangeYDefined and self._applyYLimit:
            if setLimits:
                yMid = (self.axisT + self.axisB) / 2.0
                self.axisT = yMid + self._maxYRange * np.sign(self.pixelY)
                self.axisB = yMid - self._maxYRange * np.sign(self.pixelY)
            self._maxYReached = True

        self._minReached = self._minXReached or self._minYReached
        self._maxReached = self._maxXReached or self._maxYReached

    def _rescaleAllAxes(self, update=True):
        self._testAxisLimits()
        self.rescale(rescaleStaticHTraces=True, rescaleStaticVTraces=True)

        # spawn rebuild event for the grid
        for li in self.gridList:
            li.renderMode = GLRENDERMODE_REBUILD

        # if self._axisLocked:
        # ratios have changed so rescale the peak/multiplet symbols
        self._GLPeaks.rescale()
        self._GLMultiplets.rescale()

        self._rescaleOverlayText()

        if update:
            self.update()

        try:
            # self._orderedAxes[0].region = (self.axisL, self.axisR)
            # self._orderedAxes[1].region = (self.axisT, self.axisB)

            self._setRegion(self._orderedAxes[0], (self.axisL, self.axisR))
            self._setRegion(self._orderedAxes[1], (self.axisT, self.axisB))

        except Exception as es:
            getLogger().debug('error setting viewing window XY-range')

    def eventFilter(self, obj, event):
        self._key = '_'
        if type(event) == QtGui.QKeyEvent and event.key() == Qt.Key_A:
            self._key = 'A'
            event.accept()
            return True
        return super().eventFilter(obj, event)

    def _panSpectrum(self, event, movePercent=20):
        """Implements Arrows up,down, left, right to pan the spectrum """
        # percentage of the view to set as single step

        if type(event) == QtGui.QKeyEvent:
            moveFactor = movePercent / 100.0
            dx = (self.axisR - self.axisL) / 2.0
            dy = (self.axisT - self.axisB) / 2.0

            key = event.key()

            if key == QtCore.Qt.Key_Left:
                self.axisL -= moveFactor * dx
                self.axisR -= moveFactor * dx

            elif key == QtCore.Qt.Key_Up:
                self.axisT += moveFactor * dy
                self.axisB += moveFactor * dy

            elif key == QtCore.Qt.Key_Right:
                self.axisL += moveFactor * dx
                self.axisR += moveFactor * dx

            elif key == QtCore.Qt.Key_Down:
                self.axisT -= moveFactor * dy
                self.axisB -= moveFactor * dy

            elif key == QtCore.Qt.Key_Plus or key == QtCore.Qt.Key_Equal:  # Plus:
                self._testAxisLimits()
                if self._minReached:
                    return

                self.zoomIn()

            elif key == QtCore.Qt.Key_Minus:
                self._testAxisLimits()
                if self._maxReached:
                    return

                self.zoomOut()

            else:
                # not a movement key
                return

            self.GLSignals._emitAllAxesChanged(source=self, strip=self.strip,
                                               axisB=self.axisB, axisT=self.axisT,
                                               axisL=self.axisL, axisR=self.axisR)

            # self._testAxisLimits(setLimits=True)
            self._rescaleAllAxes()
            self._storeZoomHistory()

    def _moveAxes(self, delta=(0.0, 0.0)):
        """Implements Arrows up,down, left, right to pan the spectrum """
        # percentage of the view to set as single step

        self.axisL += delta[0]
        self.axisR += delta[0]
        self.axisT += delta[1]
        self.axisB += delta[1]

        self.GLSignals._emitAllAxesChanged(source=self, strip=self.strip,
                                           axisB=self.axisB, axisT=self.axisT,
                                           axisL=self.axisL, axisR=self.axisR)
        self._rescaleAllAxes()

    def _movePeakFromKeys(self, event):

        if len(self.current.peaks) < 1:
            return

        moveFactor = 5
        moveDict = {
            QtCore.Qt.Key_Left : (-self.pixelX * moveFactor, 0),
            QtCore.Qt.Key_Right: (self.pixelX * moveFactor, 0),
            QtCore.Qt.Key_Up   : (0, self.pixelX * moveFactor),
            QtCore.Qt.Key_Down : (0, -self.pixelX * moveFactor)
            }

        if type(event) == QtGui.QKeyEvent:
            if event.key() in moveDict:

                with undoBlock():
                    for peak in self.current.peaks:
                        self._movePeak(peak, moveDict.get(event.key()))

    def _singleKeyAction(self, event):
        """
        :return: Actions for single key press. If current peaks, moves the peaks when using
        directional arrow otherwise pans the spectrum.
        """
        # if not self.current.peak:
        if not self._isSHIFT:
            self._panSpectrum(event)

        if self._isSHIFT:
            self._movePeakFromKeys(event)

    def initialiseAxes(self, strip=None):
        """
    setup the correct axis range and padding
    """
        self.orderedAxes = strip.axes
        self._axisCodes = strip.axisCodes
        self._axisOrder = strip.axisOrder

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

    def zoom(self, xRegion: Tuple[float, float], yRegion: Tuple[float, float]):
        """Zooms strip to the specified region
        """
        if self.INVERTXAXIS:
            self.axisL = max(xRegion[0], xRegion[1])
            self.axisR = min(xRegion[0], xRegion[1])
        else:
            self.axisL = min(xRegion[0], xRegion[1])
            self.axisR = max(xRegion[0], xRegion[1])

        if self.INVERTYAXIS:
            self.axisB = max(yRegion[0], yRegion[1])
            self.axisT = min(yRegion[0], yRegion[1])
        else:
            self.axisB = min(yRegion[0], yRegion[1])
            self.axisT = max(yRegion[0], yRegion[1])
        self._rescaleAllAxes()

    def zoomX(self, x1: float, x2: float):
        """Zooms x axis of strip to the specified region
        """
        if self.INVERTXAXIS:
            self.axisL = max(x1, x2)
            self.axisR = min(x1, x2)
        else:
            self.axisL = min(x1, x2)
            self.axisR = max(x1, x2)
        self._rescaleXAxis()

    def zoomY(self, y1: float, y2: float):
        """Zooms y axis of strip to the specified region
        """
        if self.INVERTYAXIS:
            self.axisB = max(y1, y2)
            self.axisT = min(y1, y2)
        else:
            self.axisB = min(y1, y2)
            self.axisT = max(y1, y2)
        self._rescaleYAxis()

    def resetXZoom(self):
        self._resetAxisRange(xAxis=True, yAxis=False)
        self._rescaleXAxis()

    def resetYZoom(self):
        self._resetAxisRange(xAxis=False, yAxis=True)
        self._rescaleYAxis()

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

    def previousZoom(self):
        """Move to the previous stored zoom
        """
        previousZoomPtr = (self._zoomHistoryCurrent - 1) % len(self._zoomHistory)

        if self._zoomHistoryHead != previousZoomPtr and self._zoomHistory[previousZoomPtr] is not None:
            self._zoomHistoryCurrent = previousZoomPtr

        restoredZooms = self._zoomHistory[self._zoomHistoryCurrent]
        self.axisL, self.axisR, self.axisB, self.axisT = restoredZooms[0], restoredZooms[1], restoredZooms[2], \
                                                         restoredZooms[3]

        # use this because it rescales all the symbols
        self._rescaleXAxis()

    def nextZoom(self):
        """Move to the next stored zoom
        """
        if self._zoomHistoryHead != self._zoomHistoryCurrent:
            self._zoomHistoryCurrent = (self._zoomHistoryCurrent + 1) % len(self._zoomHistory)

        restoredZooms = self._zoomHistory[self._zoomHistoryCurrent]
        self.axisL, self.axisR, self.axisB, self.axisT = restoredZooms[0], restoredZooms[1], restoredZooms[2], \
                                                         restoredZooms[3]

        # use this because it rescales all the symbols
        self._rescaleXAxis()

    def storeZoom(self):
        """Store the current axis values to the zoom stack
        Sets this to the top of the stack, removing everything after
        """
        if self._currentZoom < ZOOMMAXSTORE:
            self._currentZoom += 1
        self.storedZooms = self.storedZooms[:self._currentZoom - 1]
        self.storedZooms.append((self.axisL, self.axisR, self.axisB, self.axisT))

    def restoreZoom(self):
        """Restore zoom to the last stored zoom
        """
        if self.storedZooms:
            # restoredZooms = self.storedZooms.pop()

            # get the top of the stack
            self._currentZoom = len(self.storedZooms)
            restoredZooms = self.storedZooms[self._currentZoom - 1]
            self.axisL, self.axisR, self.axisB, self.axisT = restoredZooms[0], restoredZooms[1], restoredZooms[2], \
                                                             restoredZooms[3]
        else:
            self._resetAxisRange()

        self._zoomHistoryCurrent = self._zoomHistoryHead

        # use this because it rescales all the symbols
        self._rescaleXAxis()

    # def previousZoom(self):
    #     """Move to the previous stored zoom
    #     """
    #     if self._currentZoom > 1:
    #         self._currentZoom -= 1
    #     restoredZooms = self.storedZooms[self._currentZoom - 1]
    #     self.axisL, self.axisR, self.axisB, self.axisT = restoredZooms[0], restoredZooms[1], restoredZooms[2], \
    #                                                      restoredZooms[3]
    #
    #     # use this because it rescales all the symbols
    #     self._rescaleXAxis()
    #
    # def nextZoom(self):
    #     """Move to the next stored zoom
    #     """
    #     if self._currentZoom < len(self.storedZooms):
    #         self._currentZoom += 1
    #     restoredZooms = self.storedZooms[self._currentZoom - 1]
    #     self.axisL, self.axisR, self.axisB, self.axisT = restoredZooms[0], restoredZooms[1], restoredZooms[2], \
    #                                                      restoredZooms[3]
    #
    #     # use this because it rescales all the symbols
    #     self._rescaleXAxis()

    def resetZoom(self):
        self._resetAxisRange()
        self._rescaleAllAxes()

    def zoomIn(self):
        zoomPercent = -self._preferences.zoomPercent / 100.0
        dx = (self.axisR - self.axisL) / 2.0
        dy = (self.axisT - self.axisB) / 2.0
        self.axisL -= zoomPercent * dx
        self.axisR += zoomPercent * dx
        self.axisT += zoomPercent * dy
        self.axisB -= zoomPercent * dy

        self._rescaleAllAxes()

    def zoomOut(self):
        zoomPercent = self._preferences.zoomPercent / 100.0
        dx = (self.axisR - self.axisL) / 2.0
        dy = (self.axisT - self.axisB) / 2.0
        self.axisL -= zoomPercent * dx
        self.axisR += zoomPercent * dx
        self.axisT += zoomPercent * dy
        self.axisB -= zoomPercent * dy

        self._rescaleAllAxes()

    def _resetAxisRange(self, xAxis=True, yAxis=True):
        """
        reset the axes to the limits of the spectra in this view
        """
        # set a default empty axisRange
        axisLimits = []

        # iterate over spectrumViews
        for spectrumView in self._ordering:  # strip.spectrumViews:
            if spectrumView.isDeleted:
                continue

            if not axisLimits:
                axisLimits = [self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXXALIAS],
                              self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINXALIAS],
                              self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXYALIAS],
                              self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINYALIAS]]
            else:
                axisLimits[0] = max(axisLimits[0], self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXXALIAS])
                axisLimits[1] = min(axisLimits[1], self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINXALIAS])
                axisLimits[2] = max(axisLimits[2], self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXYALIAS])
                axisLimits[3] = min(axisLimits[3], self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINYALIAS])

        if axisLimits:
            if xAxis:
                if self.INVERTXAXIS:
                    self.axisL, self.axisR = axisLimits[0:2]
                else:
                    self.axisR, self.axisL = axisLimits[0:2]

            if yAxis:
                if self.INVERTYAXIS:
                    self.axisB, self.axisT = axisLimits[2:4]
                else:
                    self.axisT, self.axisB = axisLimits[2:4]

    def initializeGL(self):
        # GLversionFunctions = self.context().versionFunctions()
        # GLversionFunctions.initializeOpenGLFunctions()
        # self._GLVersion = GLversionFunctions.glGetString(GL.GL_VERSION)

        # initialise a common to all OpenGL windows
        self.globalGL = GLGlobalData(parent=self, strip=self.strip)
        self._glClientIndex = self.globalGL.getNextClientIndex()

        # initialise the arrays for the grid and axes
        self.gridList = []
        for li in range(3):
            self.gridList.append(GLVertexArray(numLists=1,
                                               renderMode=GLRENDERMODE_REBUILD,
                                               blendMode=False,
                                               drawMode=GL.GL_LINES,
                                               dimension=2,
                                               GLContext=self))

        self._externalRegions = GLExternalRegion(project=self.project, GLContext=self, spectrumView=None,
                                                 integralListView=None)

        self._selectionBox = GLVertexArray(numLists=1,
                                           renderMode=GLRENDERMODE_REBUILD,
                                           blendMode=True,
                                           drawMode=GL.GL_QUADS,
                                           dimension=3,
                                           GLContext=self)
        self._selectionOutline = GLVertexArray(numLists=1,
                                               renderMode=GLRENDERMODE_REBUILD,
                                               blendMode=True,
                                               drawMode=GL.GL_LINES,
                                               dimension=3,
                                               GLContext=self)
        self._marksList = GLVertexArray(numLists=1,
                                        renderMode=GLRENDERMODE_REBUILD,
                                        blendMode=False,
                                        drawMode=GL.GL_LINES,
                                        dimension=2,
                                        GLContext=self)
        self._regionList = GLVertexArray(numLists=1,
                                         renderMode=GLRENDERMODE_REBUILD,
                                         blendMode=True,
                                         drawMode=GL.GL_QUADS,
                                         dimension=2,
                                         GLContext=self)

        self._testSpectrum = GLVertexArray(numLists=1,
                                           renderMode=GLRENDERMODE_REBUILD,
                                           blendMode=True,
                                           drawMode=GL.GL_TRIANGLES,
                                           dimension=4,
                                           GLContext=self)

        self.viewports = GLViewports()

        # define the main viewports
        self.viewports.addViewport(GLDefs.MAINVIEW, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (-self.AXIS_MARGINRIGHT, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

        self.viewports.addViewport(GLDefs.MAINVIEWFULLWIDTH, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (0, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

        self.viewports.addViewport(GLDefs.MAINVIEWFULLHEIGHT, self, (0, 'a'), (0, 'a'),
                                   (-self.AXIS_MARGINRIGHT, 'w'), (0, 'h'))

        # define the viewports for the right axis bar
        self.viewports.addViewport(GLDefs.RIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                   (self.AXIS_MARGINBOTTOM, 'a'),
                                   (self.AXIS_LINE, 'a'), (-self.AXIS_MARGINBOTTOM, 'h'))

        self.viewports.addViewport(GLDefs.RIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'),
                                   (self.AXIS_MARGINBOTTOM, 'a'),
                                   (0, 'w'), (-self.AXIS_MARGINBOTTOM, 'h'))

        self.viewports.addViewport(GLDefs.FULLRIGHTAXIS, self, (-(self.AXIS_MARGINRIGHT + self.AXIS_LINE), 'w'),
                                   (0, 'a'),
                                   (self.AXIS_LINE, 'a'), (0, 'h'))

        self.viewports.addViewport(GLDefs.FULLRIGHTAXISBAR, self, (-self.AXIS_MARGINRIGHT, 'w'), (0, 'a'),
                                   (0, 'w'), (0, 'h'))

        # define the viewports for the bottom axis bar
        self.viewports.addViewport(GLDefs.BOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (-self.AXIS_MARGINRIGHT, 'w'), (self.AXIS_LINE, 'a'))

        self.viewports.addViewport(GLDefs.BOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                   (-self.AXIS_MARGINRIGHT, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        self.viewports.addViewport(GLDefs.FULLBOTTOMAXIS, self, (0, 'a'), (self.AXIS_MARGINBOTTOM, 'a'),
                                   (0, 'w'), (self.AXIS_LINE, 'a'))

        self.viewports.addViewport(GLDefs.FULLBOTTOMAXISBAR, self, (0, 'a'), (0, 'a'),
                                   (0, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        # define the full viewport
        self.viewports.addViewport(GLDefs.FULLVIEW, self, (0, 'a'), (0, 'a'), (0, 'w'), (0, 'h'))

        # # define the remaining corner
        # self.viewports.addViewport(GLDefs.AXISCORNER, self, (-self.AXIS_MARGINRIGHT, 'w'), (0, 'a'), (0, 'w'), (self.AXIS_MARGINBOTTOM, 'a'))

        # set strings for the overlay text
        self._lockStringFalse = GLString(text='Lock', font=self.globalGL.glSmallFont, x=0, y=0,
                                         color=(0.5, 0.5, 0.5, 1.0), GLContext=self)
        self._lockStringTrue = GLString(text='Lock', font=self.globalGL.glSmallFont, x=0, y=0,
                                        color=self.highlightColour, GLContext=self)

        self.stripIDString = GLString(text='', font=self.globalGL.glSmallFont, x=0, y=0, GLContext=self, obj=None)

        # This is the correct blend function to ignore stray surface blending functions
        GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA, GL.GL_ONE, GL.GL_ONE)
        self.setBackgroundColour(self.background)
        self.globalGL._shaderProgramTex.setBlendEnabled(0)

        if self.strip:
            self.updateVisibleSpectrumViews()

            self.initialiseAxes(self.strip)
            self.initialiseTraces()

        # check that the screen device pixel ratio is correct
        self.refreshDevicePixelRatio()

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

    def _preferencesUpdate(self):
        """update GL values after the preferences have changed
        """
        self._setColourScheme()

        # change the colour of the selected 'Lock' string
        self._lockStringTrue = GLString(text='Lock', font=self.globalGL.glSmallFont, x=0, y=0,
                                        color=self.highlightColour, GLContext=self)

        # set the new limits
        self._applyXLimit = self._preferences.zoomXLimitApply
        self._applyYLimit = self._preferences.zoomYLimitApply
        self._intensityLimit = self._preferences.intensityLimit

        self.setBackgroundColour(self.background)

    def setBackgroundColour(self, col, silent=False):
        """
        set all background colours in the shaders
        :param col - vec4, 4 element list e.g.: [0.05, 0.05, 0.05, 1.0], very dark gray
        """
        self.makeCurrent()
        GL.glClearColor(*col)
        self.background = np.array(col, dtype=np.float32)

        self.globalGL._shaderProgram1.makeCurrent()
        self.globalGL._shaderProgram1.setBackground(self.background)
        self.globalGL._shaderProgramTex.makeCurrent()
        self.globalGL._shaderProgramTex.setBackground(self.background)
        if not silent:
            self.update()
        self.doneCurrent()

        # self.doneCurrent()
        # self.update()

    def mapMouseToAxis(self, pnt):
        if isinstance(pnt, QPoint):
            mx = pnt.x()
            if self._drawBottomAxis:
                my = self.height() - pnt.y() - self.AXIS_MARGINBOTTOM
            else:
                my = self.height() - pnt.y()

            # vect = self.vInv.dot([mx, my, 0.0, 1.0])
            # return tuple(self._aMatrix.reshape((4, 4)).dot(vect)[:2])

            return tuple(self.mouseTransform.dot([mx, my, 0.0, 1.0])[:2])
        else:
            return None

    def _toggleAxisLocked(self):
        """Toggle the axis locked button
        """
        self._axisLocked = not self._axisLocked
        self.GLSignals._emitAxisLockChanged(source=self, strip=self.strip, lock=self._axisLocked)

    def mousePressInCornerButtons(self, mx, my):
        """Check if the mouse has been pressed in the lock button
        """
        if self.AXISLOCKEDBUTTON:
            buttons = ((14, 6, 14, 6, self._toggleAxisLocked),)
            for button in buttons:
                minDiff = abs(mx - button[0])
                maxDiff = abs(my - button[1])

                if (minDiff < button[2]) and (maxDiff < button[3]):
                    button[4]()

    def mousePressInLabel(self, mx, my, ty):
        """Check if the mouse has been pressed in the stripIDlabel
        """
        buttons = (((GLDefs.TITLEXOFFSET + 0.5 * len(self.stripIDLabel)) * self.globalGL.glSmallFont.width,
                    ty - ((GLDefs.TITLEYOFFSET - 0.5) * self.globalGL.glSmallFont.height),
                    0.5 * len(self.stripIDLabel) * self.globalGL.glSmallFont.width,
                    0.4 * self.globalGL.glSmallFont.height),)

        for button in buttons:
            minDiff = abs(mx - button[0])
            maxDiff = abs(my - button[1])

            if (minDiff < button[2]) and (maxDiff < button[3]):
                return True

    def _dragStrip(self, mouseDict):  #, event: QtGui.QMouseEvent):
        """
        Re-implementation of the mouse press event to enable a NmrResidue label to be dragged as a json object
        containing its id and a modifier key to encode the direction to drop the strip.
        """
        # event.accept()
        mimeData = QtCore.QMimeData()
        # create the dataDict
        dataDict = {DropBase.PIDS: [self.strip.pid]}
        # connectDir = self._connectDir if hasattr(self, STRIPLABEL_CONNECTDIR) else STRIPLABEL_CONNECTNONE
        # dataDict[STRIPLABEL_CONNECTDIR] = connectDir

        # update the dataDict with all mouseEvents﻿{"controlRightMouse": false, "text": "NR:@-.@27.", "leftMouse": true, "controlShiftMiddleMouse": false, "middleMouse": false, "controlMiddleMouse": false, "controlShiftLeftMouse": false, "controlShiftRightMouse": false, "shiftMiddleMouse": false, "_connectDir": "isRight", "controlLeftMouse": false, "rightMouse": false, "shiftLeftMouse": false, "shiftRightMouse": false}
        dataDict.update(mouseDict)
        # convert into json
        itemData = json.dumps(dataDict)

        # ejb - added so that itemData works with PyQt5
        tempData = QtCore.QByteArray()
        stream = QtCore.QDataStream(tempData, QtCore.QIODevice.WriteOnly)
        stream.writeQString(self.stripIDLabel)
        mimeData.setData(DropBase.JSONDATA, tempData)

        # mimeData.setData(DropBase.JSONDATA, self.text())
        mimeData.setText(itemData)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)

        # create a new temporary label the the dragged pixmap
        # fixes labels that are very big with small text
        dragLabel = QtWidgets.QLabel()
        dragLabel.setText(self.stripIDLabel)
        dragLabel.setFont(textFont)
        dragLabel.setStyleSheet('color : %s' % (getColours()[GUINMRRESIDUE]))

        # set the pixmap
        pixmap = dragLabel.grab()

        # make the label slightly transparent
        painter = QtGui.QPainter(pixmap)
        painter.setCompositionMode(painter.CompositionMode_DestinationIn)
        painter.fillRect(pixmap.rect(), QtGui.QColor(0, 0, 0, 240))
        painter.end()
        drag.setPixmap(pixmap)

        # drag.setHotSpot(event.pos())
        drag.setHotSpot(QtCore.QPoint(dragLabel.width() // 2, dragLabel.height() // 2))

        # drag.targetChanged.connect(self._targetChanged)
        drag.exec_(QtCore.Qt.CopyAction)

    def mousePressIn1DArea(self, regions):
        for region in regions:
            if region._objectView and not region._objectView.isVisible():
                continue

            if isinstance(region._object, Integral):
                # if not self._widthsChangedEnough((region.values[0], 0.0),
                #                                  (self.cursorCoordinate[0], 0.0),
                #                                  tol=abs(3*self.pixelX)):
                #   self._dragRegions.add((region, 'v', 0))     # line 0 of v-region
                #
                # elif not self._widthsChangedEnough((region.values[1], 0.0),
                #                                   (self.cursorCoordinate[0], 0.0),
                #                                   tol=abs(3*self.pixelX)):
                #   self._dragRegions.add((region, 'v', 1))     # line 1 of v-region
                #
                # else:
                #   mid = (region.values[0]+region.values[1])/2.0
                #   delta = abs(region.values[0]-region.values[1])/2.0
                #   if not self._widthsChangedEnough((mid, 0.0),
                #                                    (self.cursorCoordinate[0], 0.0),
                #                                    tol=delta):
                #     self._dragRegions.add((region, 'v', 3))   # both lines of v-region

                thisRegion = region._object._1Dregions
                if thisRegion:
                    mid = np.median(thisRegion[1])
                    delta = (np.max(thisRegion[1]) - np.min(thisRegion[1])) / 2.0
                    inX = self._widthsChangedEnough((mid, 0.0),
                                                    (self.cursorCoordinate[0], 0.0),
                                                    tol=delta)

                    mx = np.max([thisRegion[0], np.max(thisRegion[2])])
                    mn = np.min([thisRegion[0], np.min(thisRegion[2])])
                    mid = (mx + mn) / 2.0
                    delta = (mx - mn) / 2.0
                    inY = self._widthsChangedEnough((0.0, mid),
                                                    (0.0, self.cursorCoordinate[1]),
                                                    tol=delta)
                    if not inX and not inY:
                        self._dragRegions.add((region, 'v', 3))

        return self._dragRegions

    def mousePressInRegion(self, regions):
        for region in regions:
            if region._objectView and not region._objectView.isVisible():
                continue

            if region.visible and region.movable:
                if region.orientation == 'h':
                    if not self._widthsChangedEnough((0.0, region.values[0]),
                                                     (0.0, self.cursorCoordinate[1]),
                                                     tol=abs(3 * self.pixelY)):
                        self._dragRegions.add((region, 'h', 0))  # line 0 of h-region
                        # break

                    elif not self._widthsChangedEnough((0.0, region.values[1]),
                                                       (0.0, self.cursorCoordinate[1]),
                                                       tol=abs(3 * self.pixelY)):
                        self._dragRegions.add((region, 'h', 1))  # line 1 of h-region
                        # break
                    else:
                        mid = (region.values[0] + region.values[1]) / 2.0
                        delta = abs(region.values[0] - region.values[1]) / 2.0
                        if not self._widthsChangedEnough((0.0, mid),
                                                         (0.0, self.cursorCoordinate[1]),
                                                         tol=delta):
                            self._dragRegions.add((region, 'h', 3))  # both lines of h-region
                            # break

                elif region.orientation == 'v':
                    if not self._widthsChangedEnough((region.values[0], 0.0),
                                                     (self.cursorCoordinate[0], 0.0),
                                                     tol=abs(3 * self.pixelX)):
                        self._dragRegions.add((region, 'v', 0))  # line 0 of v-region
                        # break

                    elif not self._widthsChangedEnough((region.values[1], 0.0),
                                                       (self.cursorCoordinate[0], 0.0),
                                                       tol=abs(3 * self.pixelX)):
                        self._dragRegions.add((region, 'v', 1))  # line 1 of v-region
                        # break
                    else:
                        mid = (region.values[0] + region.values[1]) / 2.0
                        delta = abs(region.values[0] - region.values[1]) / 2.0
                        if not self._widthsChangedEnough((mid, 0.0),
                                                         (self.cursorCoordinate[0], 0.0),
                                                         tol=delta):
                            self._dragRegions.add((region, 'v', 3))  # both lines of v-region
                            # break

        return self._dragRegions

    def mousePressInfiniteLine(self, regions):
        for region in regions:
            if region._objectView and not region._objectView.isVisible():
                continue

            if region.visible and region.movable:
                if region.orientation == 'h':
                    if not self._widthsChangedEnough((0.0, region.values),
                                                     (0.0, self.cursorCoordinate[1]),
                                                     tol=abs(3 * self.pixelY)):
                        self._dragRegions.add((region, 'h', 4))  # line 0 of h-region

                elif region.orientation == 'v':
                    if not self._widthsChangedEnough((region.values, 0.0),
                                                     (self.cursorCoordinate[0], 0.0),
                                                     tol=abs(3 * self.pixelX)):
                        self._dragRegions.add((region, 'v', 4))  # line 0 of v-region

        return self._dragRegions

    def mousePressInIntegralLists(self):
        """Check whether the mouse has been pressed in an integral
        """
        # for reg in self._GLIntegralLists.values():
        for reg in self._GLIntegrals._GLSymbols.values():
            if not reg.integralListView.isVisible() or \
                    not reg.spectrumView.isVisible():
                continue

            integralPressed = self.mousePressInRegion(reg._regions)
            # if integralPressed:
            #   break

    def _mousePressedEvent(self, ev):
        """Handle mouse press event for single click and beginning of mouse drag event
        when dragging strip label
        """
        if not self._lastClick:
            self._lastClick = SINGLECLICK

        if self._lastClick == SINGLECLICK:
            self._draggingLabel = True
            mouseDict = getMouseEventDict(ev)

            # set up a singleshot event, but a bit quicker than the normal interval (which seems a little long)
            QtCore.QTimer.singleShot(QtWidgets.QApplication.instance().doubleClickInterval() // 2,
                                     partial(self._handleMouseClicked, mouseDict, ev))

        elif self._lastClick == DOUBLECLICK:

            # reset the doubleClick history
            self._lastClick = None
            self._mousePressed = False
            self._draggingLabel = False

    def _handleMouseClicked(self, mouseDict, ev):
        """handle a single mouse event, but ignore double click events for dragging strip label
        """
        if self._lastClick == SINGLECLICK and self._mousePressed:
            self._dragStrip(mouseDict)

        # reset the doubleClick history
        self._lastClick = None
        self._mousePressed = False
        self._draggingLabel = False

    def mousePressEvent(self, ev):
        self._mousePressed = True
        self.lastPos = ev.pos()

        mx = ev.pos().x()
        if self._drawBottomAxis:
            my = self.height() - ev.pos().y() - self.AXIS_MARGINBOTTOM
            top = self.height() - self.AXIS_MARGINBOTTOM
        else:
            my = self.height() - ev.pos().y()
            top = self.height()
        self._mouseStart = (mx, my)

        # vect = self.vInv.dot([mx, my, 0.0, 1.0])
        # self._startCoordinate = self._aMatrix.reshape((4, 4)).dot(vect)

        self._startCoordinate = self.mouseTransform.dot([mx, my, 0.0, 1.0])

        self._endCoordinate = self._startCoordinate
        # self._drawSelectionBox = True

        # if not self.mousePressInRegion(self._externalRegions._regions):
        #   self.mousePressInIntegralLists()

        if self.mousePressInLabel(mx, my, top):
            # self._dragStrip(ev)
            self._mousePressedEvent(ev)

        else:
            # check if the corner buttons have been pressed
            self.mousePressInCornerButtons(mx, my)

            # check for dragging of infinite lines, region boundaries, integrals
            self.mousePressInfiniteLine(self._infiniteLines)

            while len(self._dragRegions) > 1:
                self._dragRegions.pop()

            if not self._dragRegions:
                if not self.mousePressInRegion(self._externalRegions._regions):
                    self.mousePressInIntegralLists()

        self.current.strip = self.strip
        self.update()

    def mouseDoubleClickEvent(self, ev):
        self._lastClick = DOUBLECLICK

    def mouseReleaseEvent(self, ev):

        self._mousePressed = False
        self._draggingLabel = False

        self._clearAndUpdate()

        mx = ev.pos().x()
        if self._drawBottomAxis:
            my = self.height() - ev.pos().y() - self.AXIS_MARGINBOTTOM
        else:
            my = self.height() - ev.pos().y()
        self._mouseEnd = (mx, my)

        # add a 2-pixel tolerance to the click event - in case of a small wiggle on coordinates
        if not self._widthsChangedEnough(self._mouseStart, self._mouseEnd, tol=2):

            # perform click action
            self._mouseClickEvent(ev)

        else:
            # if self._selectionMode != 0:

            # end of drag event - perform action
            self._mouseDragEvent(ev)

    def _checkKeys(self, ev):
        keyMod = QApplication.keyboardModifiers()
        key = ev.key()

        if keyMod == Qt.ShiftModifier or key == QtCore.Qt.Key_Shift:
            self._isSHIFT = 'S'
            self.shift = True
        if keyMod == Qt.ControlModifier:
            self._isCTRL = 'C'
        if keyMod == Qt.AltModifier:
            self._isALT = 'A'
        if keyMod == Qt.MetaModifier:
            self._isMETA = 'M'

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        self._key = event.key()
        self._checkKeys(event)
        self._singleKeyAction(event)

    def _clearAfterRelease(self, ev):
        key = ev.key()
        if key == QtCore.Qt.Key_Shift:
            self._isSHIFT = ''

    def _clearKeys(self):
        self._key = ''
        # self._isSHIFT = ''
        self._isCTRL = ''
        self._isALT = ''
        self._isMETA = ''

    def _clearAndUpdate(self, clearKeys=False):
        if clearKeys:
            self._clearKeys()
        self._drawSelectionBox = False
        self._drawDeltaOffset = False
        self._drawMouseMoveLine = False
        self._dragRegions = set()
        self.update()

    def keyReleaseEvent(self, ev: QtGui.QKeyEvent):
        super().keyReleaseEvent(ev)
        self._clearAndUpdate(clearKeys=True)
        self._clearAfterRelease(ev)

    def enterEvent(self, ev: QtCore.QEvent):
        super().enterEvent(ev)
        self._clearAndUpdate()

    def focusInEvent(self, ev: QtGui.QFocusEvent):
        super().focusInEvent(ev)
        self._clearAndUpdate()

    def focusOutEvent(self, ev: QtGui.QFocusEvent):
        super().focusOutEvent(ev)
        self._clearAndUpdate()

    def leaveEvent(self, ev: QtCore.QEvent):
        super().leaveEvent(ev)
        self._clearAndUpdate()

    def mouseMoveEvent(self, event):
        if self.strip.isDeleted:
            return
        if not self._ordering:  # strip.spectrumViews:
            return
        if self._draggingLabel:
            return

        if abs(self.axisL - self.axisR) < 1.0e-6 or abs(self.axisT - self.axisB) < 1.0e-6:
            return

        self.setFocus()
        dx = event.pos().x() - self.lastPos.x()
        dy = event.pos().y() - self.lastPos.y()
        self.lastPos = event.pos()

        # calculate mouse coordinate within the mainView
        self._mouseX = event.pos().x()
        if self._drawBottomAxis:
            self._mouseY = self.height() - event.pos().y() - self.AXIS_MARGINBOTTOM
            self._top = self.height() - self.AXIS_MARGINBOTTOM
        else:
            self._mouseY = self.height() - event.pos().y()
            self._top = self.height()

        # translate from screen (0..w, 0..h) to NDC (-1..1, -1..1) to axes (axisL, axisR, axisT, axisB)
        self.cursorCoordinate = self.mouseTransform.dot([self._mouseX, self._mouseY, 0.0, 1.0])

        try:
            mouseMovedDict = self.current.mouseMovedDict
        except:
            # initialise a new mouse moved dict
            mouseMovedDict = {'strip'           : self.strip,
                              AXIS_MATCHATOMTYPE: {},
                              AXIS_FULLATOMNAME : {}}  #     dict(strip=self.strip)   #strip)

        xPos = yPos = 0
        activeOther = []
        for n, axisCode in enumerate(self._axisCodes):
            if n == 0:
                xPos = pos = self.cursorCoordinate[0]
                activeX = axisCode[0]
            elif n == 1:
                yPos = pos = self.cursorCoordinate[1]
                activeY = axisCode[0]
            else:
                pos = self._orderedAxes[n].position  # if n in self._orderedAxes else 0
                activeOther.append(axisCode[0])

            # populate the mouse moved dict
            mouseMovedDict[AXIS_MATCHATOMTYPE][axisCode[0]] = pos
            mouseMovedDict[AXIS_FULLATOMNAME][axisCode] = pos

        mouseMovedDict[AXIS_ACTIVEAXES] = (activeX, activeY) + tuple(activeOther)

        self.current.cursorPosition = (xPos, yPos)
        self.current.mouseMovedDict = mouseMovedDict

        if event.buttons() & (Qt.LeftButton | Qt.RightButton):
            # do the complicated keypresses first
            # other keys are: Key_Alt, Key_Meta, and _isALT, _isMETA

            if (self._key == Qt.Key_Control and self._isSHIFT == 'S') or \
                    (self._key == Qt.Key_Shift and self._isCTRL) == 'C':

                self._endCoordinate = self.cursorCoordinate  #[event.pos().x(), self.height() - event.pos().y()]
                self._selectionMode = 3
                self._drawSelectionBox = True
                self._drawDeltaOffset = True

            elif (self._key == Qt.Key_Shift) and (event.buttons() & Qt.LeftButton):

                self._endCoordinate = self.cursorCoordinate  #[event.pos().x(), self.height() - event.pos().y()]
                self._selectionMode = 1
                self._drawSelectionBox = True
                self._drawDeltaOffset = True

            elif (self._key == Qt.Key_Control) and (event.buttons() & Qt.LeftButton):

                self._endCoordinate = self.cursorCoordinate  #[event.pos().x(), self.height() - event.pos().y()]
                self._selectionMode = 2
                self._drawSelectionBox = True
                self._drawDeltaOffset = True

            else:

                if self._dragRegions:
                    for reg in self._dragRegions:
                        values = reg[0].values
                        if reg[1] == 'v':

                            if reg[2] == 3:

                                # moving the mouse in a region
                                values[0] += dx * self.pixelX
                                values[1] += dx * self.pixelX
                            elif reg[2] == 4:

                                # moving an infinite line
                                values += dx * self.pixelX
                            else:

                                # moving one edge of a region
                                values[reg[2]] += dx * self.pixelX

                        elif reg[1] == 'h':

                            if reg[2] == 3:

                                # moving the mouse in a region
                                values[0] -= dy * self.pixelY
                                values[1] -= dy * self.pixelY
                            elif reg[2] == 4:

                                # moving an infinite line
                                values -= dy * self.pixelY
                            else:

                                # moving one edge of a region
                                values[reg[2]] -= dy * self.pixelY

                        reg[0].values = values

                        # # NOTE:ED check moving of _baseline
                        # if hasattr(reg[0], '_integralArea'):
                        #     # reg[0].renderMode = GLRENDERMODE_REBUILD
                        #     reg[0]._rebuildIntegral()
                else:

                    # Main mouse drag event - handle moving the axes with the mouse
                    self.axisL -= dx * self.pixelX
                    self.axisR -= dx * self.pixelX
                    self.axisT += dy * self.pixelY
                    self.axisB += dy * self.pixelY
                    self.GLSignals._emitAllAxesChanged(source=self, strip=self.strip,
                                                       axisB=self.axisB, axisT=self.axisT,
                                                       axisL=self.axisL, axisR=self.axisR)
                    self._selectionMode = 0
                    self._rescaleAllAxes()
                    self._storeZoomHistory()

        elif event.buttons() & Qt.MiddleButton:
            if self._isSHIFT == '' and self._isCTRL == '' and self._isALT == '' and self._isMETA == '':
                # drag a peak
                self._endCoordinate = self.cursorCoordinate
                self._drawMouseMoveLine = True
                self._drawDeltaOffset = True

        self.GLSignals._emitMouseMoved(source=self, coords=self.cursorCoordinate, mouseMovedDict=mouseMovedDict)

        # spawn rebuild/paint of traces
        if self._updateHTrace or self._updateVTrace:
            self.updateTraces()

        self.update()

    def sign(self, x):
        return 1.0 if x >= 0 else -1.0

    def _rescaleOverlayText(self):
        if self.stripIDString:
            vertices = self.stripIDString.numVertices

            # offsets = [self.axisL + (GLDefs.TITLEXOFFSET * self.globalGL.glSmallFont.width * self.pixelX),
            #            self.axisT - (GLDefs.TITLEYOFFSET * self.globalGL.glSmallFont.height * self.pixelY)]
            offsets = [GLDefs.TITLEXOFFSET * self.globalGL.glSmallFont.width * self.deltaX,
                       1.0 - (GLDefs.TITLEYOFFSET * self.globalGL.glSmallFont.height * self.deltaY)]

            for pp in range(0, 2 * vertices, 2):
                self.stripIDString.attribs[pp:pp + 2] = offsets

            self.stripIDString.updateTextArrayVBOAttribs(enableVBO=True)

    def _updateHighlightedIntegrals(self, spectrumView, integralListView):
        drawList = self._GLIntegralLists[integralListView]
        drawList._rebuild()

    def _processPeakNotifier(self, data):
        self._updateVisibleSpectrumViews()
        self._GLPeaks._processNotifier(data)

        self._clearKeys()
        self.update()

    def _processIntegralNotifier(self, data):
        self._updateVisibleSpectrumViews()
        self._GLIntegrals._processNotifier(data)

        self._clearKeys()
        self.update()

    def _processMultipletNotifier(self, data):
        self._updateVisibleSpectrumViews()
        self._GLMultiplets._processNotifier(data)

        self._clearKeys()
        self.update()

    def _round_sig(self, x, sig=6, small_value=1.0e-9):
        return 0 if x == 0 else round(x, sig - int(math.floor(math.log10(max(abs(x), abs(small_value))))) - 1)

    def between(self, val, l, r):
        return (l - val) * (r - val) <= 0

    def _setViewPortFontScale(self):
        # set the scale for drawing the overlay text correctly
        self._axisScale[0:4] = [self.deltaX, self.deltaY, 1.0, 1.0]
        self.globalGL._shaderProgramTex.setGLUniform4fv('axisScale', 1, self._axisScale)
        self.globalGL._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0, 1.0, -1.0, 1.0)
        self.globalGL._shaderProgramTex.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, self._uPMatrix)

    def updateVisibleSpectrumViews(self):
        self._visibleSpectrumViewsChange = True
        self.update()

    # def _updateVisibleSpectrumViews(self):
    #     """Update the list of visible spectrumViews when change occurs
    #     """
    #
    #     # make the list of ordered spectrumViews
    #     self._ordering = self.spectrumDisplay.orderedSpectrumViews(self.strip.spectrumViews)
    #     for specView in tuple(self._spectrumSettings.keys()):
    #         if specView not in self._ordering:
    #             del self._spectrumSettings[specView]
    #
    #     # make a list of the visible and not-deleted spectrumViews
    #     visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
    #     visibleSpectrumViews = [specView for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
    #
    #     # set the first visible, or the first in the ordered list
    #     self._firstVisible = visibleSpectrumViews[0] if visibleSpectrumViews else self._ordering[0] if self._ordering and not self._ordering[0].isDeleted else None
    #     self.visiblePlaneList = {}
    #     for visibleSpecView in self._ordering:
    #         self.visiblePlaneList[visibleSpecView] = visibleSpecView._getVisiblePlaneList(self._firstVisible)
    #
    #     # update the labelling lists
    #     self._GLPeaks.setListViews(self._ordering)
    #     self._GLIntegrals.setListViews(self._ordering)
    #     self._GLMultiplets.setListViews(self._ordering)

    # @profile
    def paintGL(self):
        w = self.w
        h = self.h
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        currentShader = self.globalGL._shaderProgram1.makeCurrent()

        if self._blankDisplay:
            return

        if self.strip.isDeleted:
            return

        # check whether the visible spectra list needs updating
        if self._visibleSpectrumViewsChange:
            self._visibleSpectrumViewsChange = False
            self._updateVisibleSpectrumViews()

        # if there are no spectra then skip the paintGL event
        if not self._ordering:
            return

        # stop notifiers interfering with paint event
        self.project.blankNotification()

        # self._ordering = self.spectrumDisplay.orderedSpectrumViews(self._ordering:                             # strip.spectrumViews)
        # self._GLPeaks.setListViews(self._ordering)
        # self._GLIntegrals.setListViews(self._ordering)
        # self._GLMultiplets.setListViews(self._ordering)

        # start with the grid mapped to (0..1, 0..1) to remove zoom errors here
        currentShader.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0.0, 1.0, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)

        # draw the grid components
        self.drawGrid()

        # set the scale to the axis limits, needs addressing correctly, possibly same as grid
        currentShader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB,
                                        self.axisT, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)
        currentShader.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._IMatrix)

        # draw the spectra, need to reset the viewport
        self.viewports.setViewport(self._currentView)
        self.drawSpectra()

        if not self._stackingMode:
            self._GLPeaks.drawSymbols(self._spectrumSettings)
            self._GLMultiplets.drawSymbols(self._spectrumSettings)
            self._GLIntegrals.drawSymbols(self._spectrumSettings)

            self.drawMarksRulers()
            self.drawRegions()

        # change to the text shader
        currentShader = self.globalGL._shaderProgramTex.makeCurrent()

        currentShader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB, self.axisT, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, self._uPMatrix)

        self._axisScale[0:4] = [self.pixelX, self.pixelY, 1.0, 1.0]
        currentShader.setGLUniform4fv('axisScale', 1, self._axisScale)

        self.enableTexture()

        if not self._stackingMode:
            self.enableTextClientState()

            self._GLPeaks.drawLabels(self._spectrumSettings)
            self._GLMultiplets.drawLabels(self._spectrumSettings)
            self._GLIntegrals.drawLabels(self._spectrumSettings)
            self.drawMarksAxisCodes()

            self.disableTextClientState()

        currentShader = self.globalGL._shaderProgram1.makeCurrent()

        self.drawTraces()
        currentShader.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._IMatrix)

        self.drawInfiniteLines()

        currentShader.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0.0, 1.0, -1.0, 1.0)
        currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uPMatrix)

        self.drawSelectionBox()
        self.drawMouseMoveLine()

        if self._successiveClicks:
            self.drawDottedCursor()

        self.drawCursors()

        currentShader = self.globalGL._shaderProgramTex.makeCurrent()
        self.enableTextClientState()
        self._setViewPortFontScale()

        # if self._crosshairVisible:
        self.drawMouseCoords()

        # make the overlay/axis solid
        currentShader.setBlendEnabled(0)
        self.drawOverlayText()
        self.drawAxisLabels()
        currentShader.setBlendEnabled(1)

        self.disableTextClientState()
        self.disableTexture()

        # use the current viewport matrix to display the last bit of the axes
        currentShader = self.globalGL._shaderProgram1.makeCurrent()
        currentShader.setProjectionAxes(self._uVMatrix, 0, w - self.AXIS_MARGINRIGHT, -1, h - self.AXIS_MARGINBOTTOM,
                                        -1.0, 1.0)

        self.viewports.setViewport(self._currentView)

        # why are these labelled the other way round?
        currentShader.setGLUniformMatrix4fv('pMatrix', 1, GL.GL_FALSE, self._uVMatrix)
        currentShader.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._IMatrix)

        # cheat for the moment to draw the axes (if visible)
        if self.highlighted:
            colour = self.highlightColour
        else:
            colour = self.foreground

        GL.glDisable(GL.GL_BLEND)
        GL.glColor4f(*colour)
        GL.glBegin(GL.GL_LINES)

        if self._drawBottomAxis:
            GL.glVertex2d(0, 0)
            GL.glVertex2d(w - self.AXIS_MARGINRIGHT, 0)

        if self._drawRightAxis:
            GL.glVertex2d(w - self.AXIS_MARGINRIGHT, 0)
            GL.glVertex2d(w - self.AXIS_MARGINRIGHT, h - self.AXIS_MARGINBOTTOM)

        GL.glEnd()

        # re-enable notifiers
        self.project.unblankNotification()

    def enableTexture(self):
        GL.glEnable(GL.GL_BLEND)
        # GL.glEnable(GL.GL_TEXTURE_2D)
        # GL.glBindTexture(GL.GL_TEXTURE_2D, self.globalGL.glSmallFont.textureId)

        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.globalGL.glSmallFont.textureId)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.globalGL.glSmallTransparentFont.textureId)

        # # specific blend function for text overlay
        # GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_DST_COLOR, GL.GL_ONE, GL.GL_ONE)

    def disableTexture(self):
        GL.glDisable(GL.GL_BLEND)

        # # reset blend function
        # GL.glBlendFuncSeparate(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA, GL.GL_ONE, GL.GL_ONE)

    def buildAllContours(self):
        for spectrumView in self._ordering:  # strip.spectrumViews:
            if not spectrumView.isDeleted:
                spectrumView.buildContours = True

    def buildSpectra(self):
        if self.strip.isDeleted:
            return

        # self._spectrumSettings = {}
        rebuildFlag = False
        for spectrumView in self._ordering:  # strip.spectrumViews:
            if spectrumView.isDeleted:
                continue

            if spectrumView.buildContours or spectrumView.buildContoursOnly:

                # flag the peaks for rebuilding
                if not spectrumView.buildContoursOnly:
                    for peakListView in spectrumView.peakListViews:
                        peakListView.buildSymbols = True
                        peakListView.buildLabels = True
                    for integralListView in spectrumView.integralListViews:
                        integralListView.buildSymbols = True
                        integralListView.buildLabels = True
                    for multipletListView in spectrumView.multipletListViews:
                        multipletListView.buildSymbols = True
                        multipletListView.buildLabels = True

                spectrumView.buildContours = False
                spectrumView.buildContoursOnly = False

                # rebuild the contours
                if spectrumView not in self._contourList.keys():
                    self._contourList[spectrumView] = GLVertexArray(numLists=1,
                                                                    renderMode=GLRENDERMODE_DRAW,
                                                                    blendMode=False,
                                                                    drawMode=GL.GL_LINES,
                                                                    dimension=2,
                                                                    GLContext=self)
                spectrumView._buildGLContours(self._contourList[spectrumView])

                self._buildSpectrumSetting(spectrumView=spectrumView)
                rebuildFlag = True

                # define the VBOs to pass to the graphics card
                self._contourList[spectrumView].defineIndexVBO(enableVBO=True)

        # rebuild the traces as the spectrum/plane may have changed
        if rebuildFlag:
            self.rebuildTraces()

    def enableTextClientState(self):
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glEnableClientState(GL.GL_COLOR_ARRAY)
        GL.glEnableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glEnableVertexAttribArray(self._glClientIndex)

    def disableTextClientState(self):
        GL.glDisableClientState(GL.GL_TEXTURE_COORD_ARRAY)
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        GL.glDisableVertexAttribArray(self._glClientIndex)

    def drawSpectra(self):
        if self.strip.isDeleted:
            return

        currentShader = self.globalGL._shaderProgram1

        self.buildSpectra()

        # use the _devicePixelRatio for retina displays
        GL.glLineWidth(self.strip._contourThickness * self.viewports._devicePixelRatio)
        GL.glDisable(GL.GL_BLEND)

        for spectrumView in self._ordering:  #self._ordering:                             # strip.spectrumViews:       #.orderedSpectrumViews():

            if spectrumView.isDeleted:
                continue

            if spectrumView.isVisible():

                if spectrumView.spectrum.dimensionCount > 1:
                    if spectrumView in self._spectrumSettings.keys():
                        # set correct transform when drawing this contour

                        currentShader.setGLUniformMatrix4fv('mvMatrix',
                                                            1, GL.GL_FALSE,
                                                            self._spectrumSettings[spectrumView][
                                                                GLDefs.SPECTRUM_MATRIX])

                        # draw the spectrum - call the existing glCallList
                        # spectrumView._paintContoursNoClip()

                        # self._contourList[spectrumView].drawIndexArray()
                        self._contourList[spectrumView].drawIndexVBO(enableVBO=True)
                else:

                    # only draw the traces for the spectra that are visible
                    specTraces = [trace.spectrumView for trace in self._staticHTraces]

                    if spectrumView in self._contourList.keys() and \
                            (spectrumView not in specTraces or self.showSpectraOnPhasing):

                        if self._stackingMode:
                            # use the stacking matrix to offset the 1D spectra
                            try:
                                currentShader.setGLUniformMatrix4fv('mvMatrix',
                                                                    1, GL.GL_FALSE,
                                                                    self._spectrumSettings[spectrumView][
                                                                        GLDefs.SPECTRUM_STACKEDMATRIX])
                            except Exception as es:
                                pass

                        # self._contourList[spectrumView].drawVertexColor()
                        self._contourList[spectrumView].drawVertexColorVBO(enableVBO=True)
                    else:
                        pass

                # if self._testSpectrum.renderMode == GLRENDERMODE_REBUILD:
                #   self._testSpectrum.renderMode = GLRENDERMODE_DRAW
                #
                #   self._makeSpectrumArray(spectrumView, self._testSpectrum)

        # set transform back to identity - ensures only the pMatrix is applied
        currentShader.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._IMatrix)

        # draw the bounding boxes
        GL.glEnable(GL.GL_BLEND)
        if self._preferences.showSpectrumBorder:
            for spectrumView in self._ordering:  #self._ordering:                             # strip.spectrumViews:

                if spectrumView.isDeleted:
                    continue

                if spectrumView.isVisible() and spectrumView.spectrum.dimensionCount > 1 and spectrumView in self._spectrumSettings.keys():
                    specSettings = self._spectrumSettings[spectrumView]

                    fx0 = specSettings[GLDefs.SPECTRUM_MAXXALIAS]
                    fx1 = specSettings[GLDefs.SPECTRUM_MINXALIAS]
                    fy0 = specSettings[GLDefs.SPECTRUM_MAXYALIAS]
                    fy1 = specSettings[GLDefs.SPECTRUM_MINYALIAS]

                    # fx0, fx1 = self._spectrumValues[0].maxAliasedFrequency, self._spectrumValues[0].minAliasedFrequency
                    #
                    # self._spectrumValues = spectrumView._getValues()
                    #
                    # spectrumReferences = spectrumView.spectrum.spectrumReferences
                    #
                    # # get the bounding box of the spectra
                    # fx0, fx1 = self._spectrumValues[0].maxAliasedFrequency, self._spectrumValues[0].minAliasedFrequency
                    #
                    # # totalPointCountX = spectrumView.spectrum.totalPointCounts[0]
                    # # fx0, fx1 = spectrumReferences[0].pointToValue(1), spectrumReferences[0].pointToValue(totalPointCountX)
                    # # fx0, fx1 = max(fx0, fx1), min(fx0, fx1)
                    #
                    # # if spectrumView.spectrum.dimensionCount > 1:
                    # fy0, fy1 = self._spectrumValues[1].maxAliasedFrequency, self._spectrumValues[1].minAliasedFrequency
                    #
                    # # totalPointCountY = spectrumView.spectrum.totalPointCounts[1]
                    # # fy0, fy1 = spectrumReferences[1].pointToValue(1), spectrumReferences[1].pointToValue(totalPointCountY)
                    # # fy0, fy1 = max(fy0, fy1), min(fy0, fy1)

                    GL.glColor4f(*spectrumView.posColour[0:3], 0.5)

                    # else:
                    #     fy0, fy1 = np.max(spectrumView.spectrum.intensities), np.min(spectrumView.spectrum.intensities)
                    #
                    #     colour = spectrumView.sliceColour
                    #     colR = int(colour.strip('# ')[0:2], 16) / 255.0
                    #     colG = int(colour.strip('# ')[2:4], 16) / 255.0
                    #     colB = int(colour.strip('# ')[4:6], 16) / 255.0
                    #
                    #     GL.glColor4f(colR, colG, colB, 0.5)

                    GL.glBegin(GL.GL_LINE_LOOP)
                    GL.glVertex2d(fx0, fy0)
                    GL.glVertex2d(fx0, fy1)
                    GL.glVertex2d(fx1, fy1)
                    GL.glVertex2d(fx1, fy0)
                    GL.glEnd()

        # reset lineWidth
        GL.glLineWidth(1.0)

    def buildGrid(self):
        self.axisLabelling, self.labelsChanged = self._buildAxes(self.gridList[0], axisList=[0, 1],
                                                                 scaleGrid=[1, 0],
                                                                 r=self.foreground[0],
                                                                 g=self.foreground[1],
                                                                 b=self.foreground[2],
                                                                 transparency=300.0)

        if self.highlighted:
            self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1, 0], r=self.highlightColour[0],
                            g=self.highlightColour[1],
                            b=self.highlightColour[2], transparency=32.0)
            self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1, 0], r=self.highlightColour[0],
                            g=self.highlightColour[1],
                            b=self.highlightColour[2], transparency=32.0)
        else:
            self._buildAxes(self.gridList[1], axisList=[1], scaleGrid=[1, 0], r=self.foreground[0],
                            g=self.foreground[1],
                            b=self.foreground[2], transparency=32.0)
            self._buildAxes(self.gridList[2], axisList=[0], scaleGrid=[1, 0], r=self.foreground[0],
                            g=self.foreground[1],
                            b=self.foreground[2], transparency=32.0)

        # buffer the lists to VBOs
        for gr in self.gridList:
            gr.defineIndexVBO(enableVBO=True)

    def drawGrid(self):
        # set to the mainView and draw the grid
        self.buildGrid()

        GL.glEnable(GL.GL_BLEND)

        if self._gridVisible:
            self.viewports.setViewport(self._currentView)
            self.gridList[0].drawIndexVBO(enableVBO=True)

        if self._axesVisible:
            if self._drawRightAxis:
                # draw the grid marks for the right axis
                self.viewports.setViewport(self._currentRightAxisView)
                self.gridList[1].drawIndexVBO(enableVBO=True)

            if self._drawBottomAxis:
                # draw the grid marks for the bottom axis
                self.viewports.setViewport(self._currentBottomAxisView)
                self.gridList[2].drawIndexVBO(enableVBO=True)

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

    def buildAxisLabels(self, refresh=False):
        # build axes labelling
        if refresh or self.labelsChanged:

            self._axisXLabelling = []
            self._axisScaleLabelling = []

            if self.highlighted:
                labelColour = self.highlightColour
            else:
                labelColour = self.foreground

            if self._drawBottomAxis:
                # create the X axis labelling
                for axLabel in self.axisLabelling['0']:
                    axisX = axLabel[2]
                    axisXLabel = axLabel[3]

                    # axisXText = str(int(axisXLabel)) if axLabel[4] >= 1 else str(axisXLabel)
                    axisXText = self._intFormat(axisXLabel) if axLabel[4] >= 1 else self.XMode(axisXLabel)

                    self._axisXLabelling.append(GLString(text=axisXText,
                                                         font=self.globalGL.glSmallFont,
                                                         x=axisX - (0.4 * self.globalGL.glSmallFont.width * self.deltaX * len(
                                                                 axisXText)),
                                                         y=self.AXIS_MARGINBOTTOM - GLDefs.TITLEYOFFSET * self.globalGL.glSmallFont.height,

                                                         color=labelColour, GLContext=self,
                                                         obj=None))

                # append the axisCode
                self._axisXLabelling.append(GLString(text=self.axisCodes[0],
                                                     font=self.globalGL.glSmallFont,
                                                     x=GLDefs.AXISTEXTXOFFSET * self.deltaX,
                                                     y=self.AXIS_MARGINBOTTOM - GLDefs.TITLEYOFFSET * self.globalGL.glSmallFont.height,
                                                     color=labelColour, GLContext=self,
                                                     obj=None))
                # and the axis dimensions
                xUnitsLabels = self.XAXES[self._xUnits]
                self._axisXLabelling.append(GLString(text=xUnitsLabels,
                                                     font=self.globalGL.glSmallFont,
                                                     x=1.0 - (self.deltaX * len(xUnitsLabels) * self.globalGL.glSmallFont.width),
                                                     y=self.AXIS_MARGINBOTTOM - GLDefs.TITLEYOFFSET * self.globalGL.glSmallFont.height,
                                                     color=labelColour, GLContext=self,
                                                     obj=None))

            self._axisYLabelling = []

            if self._drawRightAxis:
                # create the Y axis labelling
                for xx, ayLabel in enumerate(self.axisLabelling['1']):
                    axisY = ayLabel[2]
                    axisYLabel = ayLabel[3]

                    if self.YAXISUSEEFORMAT:
                        axisYText = self.YMode(axisYLabel)
                    else:
                        # axisYText = str(int(axisYLabel)) if ayLabel[4] >= 1 else str(axisYLabel)
                        axisYText = self._intFormat(axisYLabel) if ayLabel[4] >= 1 else self.YMode(axisYLabel)

                    self._axisYLabelling.append(GLString(text=axisYText,
                                                         font=self.globalGL.glSmallFont,
                                                         x=self.AXIS_OFFSET,
                                                         # y=axisY - (GLDefs.AXISTEXTYOFFSET * self.pixelY),
                                                         y=axisY - (GLDefs.AXISTEXTYOFFSET * self.deltaY),
                                                         color=labelColour, GLContext=self,
                                                         obj=None))

                # append the axisCode
                self._axisYLabelling.append(GLString(text=self.axisCodes[1],
                                                     font=self.globalGL.glSmallFont,
                                                     x=self.AXIS_OFFSET,
                                                     # y=self.axisT - (GLDefs.TITLEYOFFSET * self.globalGL.glSmallFont.height * self.pixelY),
                                                     y=1.0 - (GLDefs.TITLEYOFFSET * self.globalGL.glSmallFont.height * self.deltaY),
                                                     color=labelColour, GLContext=self,
                                                     obj=None))
                # and the axis dimensions
                yUnitsLabels = self.YAXES[self._yUnits]
                self._axisYLabelling.append(GLString(text=yUnitsLabels,
                                                     font=self.globalGL.glSmallFont,
                                                     x=self.AXIS_OFFSET,
                                                     y=1.0 * self.deltaY,
                                                     color=labelColour, GLContext=self,
                                                     obj=None))

    def drawAxisLabels(self):
        # draw axes labelling

        if self._axesVisible:
            self.buildAxisLabels()

            if self._drawBottomAxis:
                # put the axis labels into the bottom bar
                self.viewports.setViewport(self._currentBottomAxisBarView)

                # self._axisScale[0:4] = [self.pixelX, 1.0, 1.0, 1.0]
                self._axisScale[0:4] = [self.deltaX, 1.0, 1.0, 1.0]

                self.globalGL._shaderProgramTex.setGLUniform4fv('axisScale', 1, self._axisScale)
                self.globalGL._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0.0, 1.0, 0,
                                                                  self.AXIS_MARGINBOTTOM, -1.0, 1.0)
                self.globalGL._shaderProgramTex.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, self._uPMatrix)

                for lb in self._axisXLabelling:
                    lb.drawTextArrayVBO(enableVBO=True)

            if self._drawRightAxis:
                # put the axis labels into the right bar
                self.viewports.setViewport(self._currentRightAxisBarView)

                # self._axisScale[0:4] = [1.0, self.pixelY, 1.0, 1.0]
                self._axisScale[0:4] = [1.0, self.deltaY, 1.0, 1.0]

                self.globalGL._shaderProgramTex.setGLUniform4fv('axisScale', 1, self._axisScale)
                self.globalGL._shaderProgramTex.setProjectionAxes(self._uPMatrix, 0, self.AXIS_MARGINRIGHT,
                                                                  0.0, 1.0, -1.0, 1.0)
                self.globalGL._shaderProgramTex.setGLUniformMatrix4fv('pTexMatrix', 1, GL.GL_FALSE, self._uPMatrix)

                for lb in self._axisYLabelling:
                    lb.drawTextArrayVBO(enableVBO=True)

    def removeInfiniteLine(self, line):
        if line in self._infiniteLines:
            self._infiniteLines.remove(line)
        self.update()

    def addInfiniteLine(self, values=None, axisCode=None, orientation=None,
                        brush=None, colour='blue',
                        movable=True, visible=True, bounds=None,
                        obj=None, lineStyle='dashed', lineWidth=1.0):

        if colour in REGION_COLOURS.keys():
            if colour == 'highlight':
                brush = self.highlightColour
            else:
                brush = REGION_COLOURS[colour]

        if orientation == 'h':
            axisCode = self._axisCodes[1]
        elif orientation == 'v':
            axisCode = self._axisCodes[0]
        else:
            if axisCode:
                axisIndex = None
                for ps, psCode in enumerate(self._axisCodes[0:2]):
                    if self._preferences.matchAxisCode == 0:  # default - match atom type

                        if axisCode[0] == psCode[0]:
                            axisIndex = ps
                    elif self._preferences.matchAxisCode == 1:  # match full code
                        if axisCode == psCode:
                            axisIndex = ps

                    if axisIndex == 0:
                        orientation = 'v'
                    elif axisIndex == 1:
                        orientation = 'h'

                if not axisIndex:
                    getLogger().warning('Axis code %s not found in current strip' % axisCode)
                    return None
            else:
                axisCode = self._axisCodes[0]
                orientation = 'v'

        newInfiniteLine = GLInfiniteLine(self.strip, self._regionList,
                                         values=values,
                                         axisCode=axisCode,
                                         orientation=orientation,
                                         brush=brush,
                                         colour=colour,
                                         movable=movable,
                                         visible=visible,
                                         bounds=bounds,
                                         obj=obj,
                                         lineStyle=lineStyle,
                                         lineWidth=lineWidth)
        self._infiniteLines.append(newInfiniteLine)

        self.update()
        return newInfiniteLine

    def removeExternalRegion(self, region):
        pass
        self._externalRegions._removeRegion(region)
        self._externalRegions.renderMode = GLRENDERMODE_REBUILD
        # if self._dragRegions[0] == region:
        #   self._dragRegions = set()
        for reg in self._dragRegions:
            if reg[0] == region:
                self._dragRegions.remove(reg)
                break

        self.update()

    def addExternalRegion(self, values=None, axisCode=None, orientation=None,
                          brush=None, colour='blue',
                          movable=True, visible=True, bounds=None,
                          obj=None, **kwds):

        newRegion = self._externalRegions._addRegion(values=values, axisCode=axisCode, orientation=orientation,
                                                     brush=brush, colour=colour,
                                                     movable=movable, visible=visible, bounds=bounds,
                                                     obj=obj, **kwds)

        self._externalRegions.renderMode = GLRENDERMODE_REBUILD
        self.update()

        return newRegion

    def addRegion(self, values=None, axisCode=None, orientation=None,
                  brush=None, colour='blue',
                  movable=True, visible=True, bounds=None,
                  obj=None):

        if colour in REGION_COLOURS.keys():
            brush = REGION_COLOURS[colour]

        if orientation == 'h':
            axisCode = self._axisCodes[1]
        elif orientation == 'v':
            axisCode = self._axisCodes[0]
        else:
            if axisCode:
                axisIndex = None
                for ps, psCode in enumerate(self._axisCodes[0:2]):
                    if self._preferences.matchAxisCode == 0:  # default - match atom type

                        if axisCode[0] == psCode[0]:
                            axisIndex = ps
                    elif self._preferences.matchAxisCode == 1:  # match full code
                        if axisCode == psCode:
                            axisIndex = ps

                    if axisIndex == 0:
                        orientation = 'v'
                    elif axisIndex == 1:
                        orientation = 'h'

                if not axisIndex:
                    getLogger().warning('Axis code %s not found in current strip' % axisCode)
                    return None
            else:
                axisCode = self._axisCodes[0]
                orientation = 'v'

        newRegion = GLRegion(self.strip, self._regionList,
                             values=values,
                             axisCode=axisCode,
                             orientation=orientation,
                             brush=brush,
                             colour=colour,
                             movable=movable,
                             visible=visible,
                             bounds=bounds,
                             obj=obj)
        self._regions.append(newRegion)

        self._regionList.renderMode = GLRENDERMODE_REBUILD
        self.update()
        return newRegion

    def buildRegions(self):

        drawList = self._externalRegions
        if drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode
            drawList._rebuild()

            drawList.defineIndexVBO(enableVBO=True)

        elif drawList.renderMode == GLRENDERMODE_RESCALE:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode
            drawList._resize()

            drawList.defineIndexVBO(enableVBO=True)

    def buildMarksRulers(self):
        drawList = self._marksList

        if drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode
            drawList.refreshMode = GLREFRESHMODE_REBUILD
            drawList.clearArrays()

            # clear the attached strings
            self._marksAxisCodes = []

            # build the marks VBO
            index = 0
            for mark in self.project.marks:

                for rr in mark.rulerData:

                    axisIndex = 2
                    for ps, psCode in enumerate(self.axisOrder[0:2]):
                        if self._preferences.matchAxisCode == 0:  # default - match atom type
                            if rr.axisCode[0] == psCode[0]:
                                axisIndex = ps
                        elif self._preferences.matchAxisCode == 1:  # match full code
                            if rr.axisCode == psCode:
                                axisIndex = ps

                    if axisIndex < 2:

                        # NOTE:ED check axis units - assume 'ppm' for the minute
                        if axisIndex == 0:
                            # vertical ruler
                            pos = x0 = x1 = rr.position
                            y0 = self.axisT
                            y1 = self.axisB
                            textX = pos + (3.0 * self.pixelX)
                            textY = self.axisB + (3.0 * self.pixelY)
                        else:
                            # horizontal ruler
                            pos = y0 = y1 = rr.position
                            x0 = self.axisL
                            x1 = self.axisR
                            textX = self.axisL + (3.0 * self.pixelX)
                            textY = pos + (3.0 * self.pixelY)

                        colour = mark.colour
                        colR = int(colour.strip('# ')[0:2], 16) / 255.0
                        colG = int(colour.strip('# ')[2:4], 16) / 255.0
                        colB = int(colour.strip('# ')[4:6], 16) / 255.0

                        drawList.indices = np.append(drawList.indices, np.array((index, index + 1), dtype=np.uint32))
                        drawList.vertices = np.append(drawList.vertices, np.array((x0, y0, x1, y1), dtype=np.float32))
                        drawList.colors = np.append(drawList.colors, np.array((colR, colG, colB, 1.0) * 2, dtype=np.float32))
                        drawList.attribs = np.append(drawList.attribs, (axisIndex, pos, axisIndex, pos))

                        # build the string and add the extra axis code
                        label = rr.label if rr.label else rr.axisCode

                        newMarkString = GLString(text=label,
                                                 font=self.globalGL.glSmallFont,
                                                 x=textX,
                                                 y=textY,
                                                 color=(colR, colG, colB, 1.0),
                                                 GLContext=self,
                                                 obj=None)
                        # this is in the attribs
                        newMarkString.axisIndex = axisIndex
                        newMarkString.axisPosition = pos
                        self._marksAxisCodes.append(newMarkString)

                        index += 2
                        drawList.numVertices += 2

            drawList.defineIndexVBO(enableVBO=True)

        elif drawList.renderMode == GLRENDERMODE_RESCALE:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            drawList.defineIndexVBO(enableVBO=True)

    def drawMarksRulers(self):
        if self.strip.isDeleted:
            return

        if self.buildMarks:
            self._marksList.renderMode = GLRENDERMODE_REBUILD
            self.buildMarks = False

        self.buildMarksRulers()
        self._marksList.drawIndexVBO(enableVBO=True)

    def drawRegions(self):
        if self.strip.isDeleted:
            return

        self.buildRegions()
        self._externalRegions.drawIndexVBO(enableVBO=True)

    def drawMarksAxisCodes(self):
        if self.strip.isDeleted:
            return

        # strings are generated when the marksRulers are modified
        for mark in self._marksAxisCodes:
            mark.drawTextArrayVBO(enableVBO=True)

    def _scaleAxisToRatio(self, values):
        return [((values[0] - self.axisL) / (self.axisR - self.axisL)) if values[0] is not None else None,
                ((values[1] - self.axisB) / (self.axisT - self.axisB)) if values[1] is not None else None]

    def drawCursors(self):
        # draw the cursors
        # need to change to VBOs

        if self._crosshairVisible:  # and (not self._updateHTrace or not self._updateVTrace):
            GL.glBegin(GL.GL_LINES)

            # map the cursor to the ratio coordinates
            newCoords = self._scaleAxisToRatio(self.cursorCoordinate[0:2])

            if getCurrentMouseMode() == PICK and self.underMouse():
                GL.glColor4f(*self.mousePickColour)

                # x = self.pixelX * 8
                # y = self.pixelY * 8
                # GL.glVertex2d(self.cursorCoordinate[0] - x, self.cursorCoordinate[1] - y)
                # GL.glVertex2d(self.cursorCoordinate[0] + x, self.cursorCoordinate[1] - y)
                # GL.glVertex2d(self.cursorCoordinate[0] + x, self.cursorCoordinate[1] - y)
                # GL.glVertex2d(self.cursorCoordinate[0] + x, self.cursorCoordinate[1] + y)
                # GL.glVertex2d(self.cursorCoordinate[0] + x, self.cursorCoordinate[1] + y)
                # GL.glVertex2d(self.cursorCoordinate[0] - x, self.cursorCoordinate[1] + y)
                # GL.glVertex2d(self.cursorCoordinate[0] - x, self.cursorCoordinate[1] + y)
                # GL.glVertex2d(self.cursorCoordinate[0] - x, self.cursorCoordinate[1] - y)

                x = self.deltaX * 8
                y = self.deltaY * 8
                GL.glVertex2d(newCoords[0] - x, newCoords[1] - y)
                GL.glVertex2d(newCoords[0] + x, newCoords[1] - y)
                GL.glVertex2d(newCoords[0] + x, newCoords[1] - y)
                GL.glVertex2d(newCoords[0] + x, newCoords[1] + y)
                GL.glVertex2d(newCoords[0] + x, newCoords[1] + y)
                GL.glVertex2d(newCoords[0] - x, newCoords[1] + y)
                GL.glVertex2d(newCoords[0] - x, newCoords[1] + y)
                GL.glVertex2d(newCoords[0] - x, newCoords[1] - y)

            else:
                GL.glColor4f(*self.foreground)

            # # if not self._updateVTrace:
            # GL.glVertex2d(self.cursorCoordinate[0], self.axisT)
            # GL.glVertex2d(self.cursorCoordinate[0], self.axisB)
            # # if not self._updateHTrace:
            # GL.glVertex2d(self.axisL, self.cursorCoordinate[1])
            # GL.glVertex2d(self.axisR, self.cursorCoordinate[1])

            phasingFrame = self.spectrumDisplay.phasingFrame
            if not phasingFrame.isVisible():
                if not self._updateVTrace and newCoords[0] is not None:
                    GL.glVertex2d(newCoords[0], 1.0)
                    GL.glVertex2d(newCoords[0], 0.0)
                if not self._updateHTrace and newCoords[1] is not None:
                    GL.glVertex2d(0.0, newCoords[1])
                    GL.glVertex2d(1.0, newCoords[1])

            GL.glEnd()

    def drawDottedCursor(self):
        # draw the cursors
        # need to change to VBOs

        GL.glColor4f(*self.zoomLineColour)
        GL.glLineStipple(1, 0xF0F0)
        GL.glEnable(GL.GL_LINE_STIPPLE)

        succClick = self._scaleAxisToRatio(self._successiveClicks[0:2])

        GL.glBegin(GL.GL_LINES)
        GL.glVertex2d(succClick[0], 1.0)
        GL.glVertex2d(succClick[0], 0.0)
        GL.glVertex2d(0.0, succClick[1])
        GL.glVertex2d(1.0, succClick[1])
        GL.glEnd()

        GL.glDisable(GL.GL_LINE_STIPPLE)

    def setInfiniteLineColour(self, infLine, colour):
        for reg in self._infiniteLines:
            if reg == infLine:
                colR = int(colour.strip('# ')[0:2], 16) / 255.0
                colG = int(colour.strip('# ')[2:4], 16) / 255.0
                colB = int(colour.strip('# ')[4:6], 16) / 255.0
                reg.brush = (colR, colG, colB, 1.0)

    def drawInfiniteLines(self):
        # draw the simulated infinite lines - using deprecated GL :)

        GL.glDisable(GL.GL_BLEND)
        GL.glEnable(GL.GL_LINE_STIPPLE)
        for infLine in self._infiniteLines:

            if infLine.visible:
                GL.glColor4f(*infLine.brush)
                GL.glLineStipple(1, GLDefs.GLLINE_STYLES[infLine.lineStyle])

                # GL.glBegin(GL.GL_LINES)
                # if infLine.orientation == 'h':
                #     GL.glVertex2d(self.axisL, infLine.values[0])
                #     GL.glVertex2d(self.axisR, infLine.values[0])
                # else:
                #     GL.glVertex2d(infLine.values[0], self.axisT)
                #     GL.glVertex2d(infLine.values[0], self.axisB)

                GL.glLineWidth(infLine.lineWidth)
                GL.glBegin(GL.GL_LINES)
                if infLine.orientation == 'h':
                    GL.glVertex2d(self.axisL, infLine.values)
                    GL.glVertex2d(self.axisR, infLine.values)
                else:
                    GL.glVertex2d(infLine.values, self.axisT)
                    GL.glVertex2d(infLine.values, self.axisB)

                GL.glEnd()

        GL.glDisable(GL.GL_LINE_STIPPLE)
        GL.glLineWidth(1.0)

    def setStripID(self, name):
        self.stripIDLabel = name
        self._newStripID = True

    def drawOverlayText(self, refresh=False):
        """Draw extra information to the screen
        """
        # cheat for the moment
        if self._newStripID or self.stripIDString.renderMode == GLRENDERMODE_REBUILD:
            self.stripIDString.renderMode = GLRENDERMODE_DRAW
            self._newStripID = False

            if self.highlighted:
                colour = self.highlightColour
            else:
                colour = self.foreground

            self.stripIDString = GLString(text=self.stripIDLabel,
                                          font=self.globalGL.glSmallFont,
                                          # x=self.axisL + (GLDefs.TITLEXOFFSET * self.globalGL.glSmallFont.width * self.pixelX),
                                          # y=self.axisT - (GLDefs.TITLEYOFFSET * self.globalGL.glSmallFont.height * self.pixelY),
                                          x=GLDefs.TITLEXOFFSET * self.globalGL.glSmallFont.width * self.deltaX,
                                          y=1.0 - (GLDefs.TITLEYOFFSET * self.globalGL.glSmallFont.height * self.deltaY),
                                          color=colour, GLContext=self,
                                          obj=None, blendMode=False)

            self._oldStripIDLabel = self.stripIDLabel

        # draw the strip ID to the screen
        self.stripIDString.drawTextArrayVBO(enableVBO=True)

        if self.AXISLOCKEDBUTTON:
            if self._axisLocked:
                # self._lockStringTrue.setStringOffset((self.axisL, self.axisB))
                self._lockStringTrue.drawTextArrayVBO(enableVBO=True)
            else:
                # self._lockStringFalse.setStringOffset((self.axisL, self.axisB))
                self._lockStringFalse.drawTextArrayVBO(enableVBO=True)

    def _rescaleRegions(self):
        self._externalRegions._rescale()

        # return
        #
        # vertices = self._regionList.numVertices
        #
        # if vertices:
        #     for pp in range(0, 2 * vertices, 8):
        #         axisIndex = int(self._regionList.attribs[pp])
        #         axis0 = self._regionList.attribs[pp + 1]
        #         axis1 = self._regionList.attribs[pp + 3]
        #
        #         # [x0, y0, x0, y1, x1, y1, x1, y0])
        #
        #         if axisIndex == 0:
        #             offsets = [axis0, self.axisT + self.pixelY, axis0, self.axisB - self.pixelY,
        #                        axis1, self.axisB - self.pixelY, axis1, self.axisT + self.pixelY]
        #         else:
        #             offsets = [self.axisL - self.pixelX, axis0, self.axisL - self.pixelX, axis1,
        #                        self.axisR + self.pixelX, axis1, self.axisR + self.pixelX, axis0]
        #
        #         self._regionList.vertices[pp:pp + 8] = offsets

    def _rescaleMarksRulers(self):
        vertices = self._marksList.numVertices

        if vertices:
            for pp in range(0, 2 * vertices, 4):
                axisIndex = int(self._marksList.attribs[pp])
                axisPosition = self._marksList.attribs[pp + 1]

                if axisIndex == 0:
                    offsets = [axisPosition, self.axisT,
                               axisPosition, self.axisB]
                else:
                    offsets = [self.axisL, axisPosition,
                               self.axisR, axisPosition]
                self._marksList.vertices[pp:pp + 4] = offsets

            self._marksList.defineIndexVBO(enableVBO=True)

    def _rescaleMarksAxisCode(self, mark):
        vertices = mark.numVertices

        # mark.attribs[0][0] = axisIndex
        # mark.attribs[0][1] = axisPosition
        if vertices:
            if mark.axisIndex == 0:
                offsets = [mark.axisPosition + (GLDefs.MARKTEXTXOFFSET * self.pixelX),
                           self.axisB + (GLDefs.MARKTEXTYOFFSET * self.pixelY)]
            else:
                offsets = [self.axisL + (GLDefs.MARKTEXTXOFFSET * self.pixelX),
                           mark.axisPosition + (GLDefs.MARKTEXTYOFFSET * self.pixelY)]

            for pp in range(0, 2 * vertices, 2):
                mark.attribs[pp:pp + 2] = offsets

            # redefine the mark's VBOs
            mark.updateTextArrayVBOAttribs(enableVBO=True)

    def rescaleMarksRulers(self):
        """rescale the marks
        """
        self._rescaleMarksRulers()
        for mark in self._marksAxisCodes:
            self._rescaleMarksAxisCode(mark)

    def setRightAxisVisible(self, axisVisible=True):
        """Set the visibility of the right axis
        """
        self._drawRightAxis = axisVisible
        self.rescale(rescaleStaticHTraces=False)
        self.update()

    def setBottomAxisVisible(self, axisVisible=True):
        """Set the visibility of the bottom axis
        """
        self._drawBottomAxis = axisVisible
        self.rescale(rescaleStaticVTraces=False)
        self.update()

    def setAxesVisible(self, rightAxisVisible=True, bottomAxisVisible=False):
        """Set the visibility of the axes
        """
        self._drawRightAxis = rightAxisVisible
        self._drawBottomAxis = bottomAxisVisible
        self.rescale()
        self.update()

    @property
    def axesVisible(self):
        return self._axesVisible

    @axesVisible.setter
    def axesVisible(self, visible):
        self._axesVisible = visible
        self.update()

    def toggleAxes(self):
        self._axesVisible = not self._axesVisible
        self.update()

    @property
    def gridVisible(self):
        return self._gridVisible

    @gridVisible.setter
    def gridVisible(self, visible):
        self._gridVisible = visible
        self.update()

    def toggleGrid(self):
        self._gridVisible = not self._gridVisible
        self.update()

    @property
    def crosshairVisible(self):
        return self._crosshairVisible

    @crosshairVisible.setter
    def crosshairVisible(self, visible):
        self._crosshairVisible = visible
        self.update()

    def toggleCrosshair(self):
        self._crosshairVisible = not self._crosshairVisible
        self.update()

    @property
    def showSpectraOnPhasing(self):
        return self._showSpectraOnPhasing

    @showSpectraOnPhasing.setter
    def showSpectraOnPhasing(self, visible):
        self._showSpectraOnPhasing = visible
        self.update()

    def toggleShowSpectraOnPhasing(self):
        self._showSpectraOnPhasing = not self._showSpectraOnPhasing
        self.update()

    @property
    def axisOrder(self):
        return self._axisOrder

    @axisOrder.setter
    def axisOrder(self, axisOrder):
        self._axisOrder = axisOrder

    @property
    def axisCodes(self):
        return self._axisCodes

    @axisCodes.setter
    def axisCodes(self, axisCodes):
        self._axisCodes = axisCodes

    @property
    def xUnits(self):
        return self._xUnits

    @xUnits.setter
    def xUnits(self, xUnits):
        self._xUnits = xUnits
        self._rescaleAllAxes()

    @property
    def yUnits(self):
        return self._yUnits

    @yUnits.setter
    def yUnits(self, yUnits):
        self._yUnits = yUnits
        self._rescaleAllAxes()

    @property
    def axisLocked(self):
        return self._axisLocked

    @axisLocked.setter
    def axisLocked(self, axisLocked):
        self._axisLocked = axisLocked
        self._rescaleAllAxes()

    @property
    def orderedAxes(self):
        return self._orderedAxes

    @orderedAxes.setter
    def orderedAxes(self, axes):
        self._orderedAxes = axes

        try:
            if self._orderedAxes[1] and self._orderedAxes[1].code == 'intensity':
                self.mouseFormat = " %s: %.3f\n %s: %.6g"
                self.diffMouseFormat = " d%s: %.3f\n d%s: %.6g"
            else:
                self.mouseFormat = " %s: %.3f\n %s: %.3f"
                self.diffMouseFormat = " d%s: %.3f\n d%s: %.3f"
        except:
            self.mouseFormat = " %s: %.3f  %s: %.4g"
            self.diffMouseFormat = " d%s: %.3f  d%s: %.4g"

    @property
    def updateHTrace(self):
        return self._updateHTrace

    @updateHTrace.setter
    def updateHTrace(self, visible):
        self._updateHTrace = visible

    @property
    def updateVTrace(self):
        return self._updateVTrace

    @updateVTrace.setter
    def updateVTrace(self, visible):
        self._updateVTrace = visible

    def buildMouseCoords(self, refresh=False):

        def valueToRatio(val, x0, x1):
            return (val - x0) / (x1 - x0)

        if refresh or self._widthsChangedEnough(self.cursorCoordinate[:2], self._mouseCoords[:2], tol=1e-8):

            if not self._drawDeltaOffset:
                self._startCoordinate = self.cursorCoordinate

            # get the list of visible spectra, or the first in the list
            visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
            thisSpec = visibleSpectra[0] if visibleSpectra else self._ordering[0].spectrum if self._ordering and not self._ordering[0].isDeleted else None

            if thisSpec:

                # generate different axes depending on units - X Axis
                if self.XAXES[self._xUnits] == GLDefs.AXISUNITSPPM:
                    cursorX = self.cursorCoordinate[0]
                    startX = self._startCoordinate[0]
                    # XMode = '%.3f'

                elif self.XAXES[self._xUnits] == GLDefs.AXISUNITSHZ:
                    if self._ordering:

                        # thisSpec = self._ordering[0].spectrum

                        if self.is1D:
                            cursorX = self.cursorCoordinate[0] * thisSpec.spectrometerFrequencies[0]
                            startX = self._startCoordinate[0] * thisSpec.spectrometerFrequencies[0]

                        else:
                            # get the axis ordering from the spectrumDisplay and map to the strip
                            stripAxisCodes = self.strip.axisCodes
                            try:
                                indices = thisSpec.getByAxisCodes('indices', stripAxisCodes)
                            except Exception as es:
                                indices = thisSpec.getByAxisCodes('indices', stripAxisCodes[0:2])

                            cursorX = self.cursorCoordinate[0] * thisSpec.spectrometerFrequencies[indices[0]]
                            startX = self._startCoordinate[0] * thisSpec.spectrometerFrequencies[indices[0]]

                    else:
                        # error trap all spectra deleted
                        cursorX = self.cursorCoordinate[0]
                        startX = self._startCoordinate[0]
                    # XMode = '%.3f'

                else:
                    if self._ordering:

                        # visibleSpectra = [specView.spectrum for specView in self._ordering if specView.isVisible()]
                        # thisSpec = visibleSpectra[0] if visibleSpectra else self._ordering[0].spectrum

                        if self.is1D:
                            cursorX = thisSpec.mainSpectrumReferences[0].valueToPoint(self.cursorCoordinate[0])
                            startX = thisSpec.mainSpectrumReferences[0].valueToPoint(self._startCoordinate[0])

                        else:
                            # get the axis ordering from the spectrumDisplay and map to the strip
                            stripAxisCodes = self.strip.axisCodes
                            try:
                                indices = thisSpec.getByAxisCodes('indices', stripAxisCodes)
                            except Exception as es:
                                indices = thisSpec.getByAxisCodes('indices', stripAxisCodes[0:2])

                            # map to a point
                            cursorX = thisSpec.mainSpectrumReferences[indices[0]].valueToPoint(self.cursorCoordinate[0])
                            startX = thisSpec.mainSpectrumReferences[indices[0]].valueToPoint(self._startCoordinate[0])

                    else:
                        # error trap all spectra deleted
                        cursorX = self.cursorCoordinate[0]
                        startX = self._startCoordinate[0]

                    # if self.modeDecimal[0]:
                    #     cursorX = int(cursorX)
                    #     startX = int(startX)
                    # XMode = '%i'

                # generate different axes depending on units - Y Axis, always use first option for 1d
                if self.is1D:
                    cursorY = self.cursorCoordinate[1]
                    startY = self._startCoordinate[1]
                    # YMode = '%.6g'

                elif self.YAXES[self._yUnits] == GLDefs.AXISUNITSPPM:
                    cursorY = self.cursorCoordinate[1]
                    startY = self._startCoordinate[1]
                    # YMode = '%.3f'

                elif self.YAXES[self._yUnits] == GLDefs.AXISUNITSHZ:
                    if self._ordering:

                        # thisSpec = self._ordering[0].spectrum

                        # get the axis ordering from the spectrumDisplay and map to the strip
                        stripAxisCodes = self.strip.axisCodes
                        try:
                            indices = thisSpec.getByAxisCodes('indices', stripAxisCodes)
                        except Exception as es:
                            indices = thisSpec.getByAxisCodes('indices', stripAxisCodes[0:2])

                        cursorY = self.cursorCoordinate[1] * thisSpec.spectrometerFrequencies[indices[1]]
                        startY = self._startCoordinate[1] * thisSpec.spectrometerFrequencies[indices[1]]

                    else:
                        # error trap all spectra deleted
                        cursorY = self.cursorCoordinate[1]
                        startY = self._startCoordinate[1]
                    # YMode = '%.3f'

                else:
                    if self._ordering:

                        # visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
                        # thisSpec = visibleSpectra[0] if visibleSpectra else self._ordering[0].spectrum if self._ordering and not self._ordering[0].isDeleted

                        # get the axis ordering from the spectrumDisplay and map to the strip
                        stripAxisCodes = self.strip.axisCodes
                        try:
                            indices = thisSpec.getByAxisCodes('indices', stripAxisCodes)
                        except Exception as es:
                            indices = thisSpec.getByAxisCodes('indices', stripAxisCodes[0:2])

                        # map to a point
                        cursorY = thisSpec.mainSpectrumReferences[indices[1]].valueToPoint(self.cursorCoordinate[1])
                        startY = thisSpec.mainSpectrumReferences[indices[1]].valueToPoint(self._startCoordinate[1])

                    else:
                        # error trap all spectra deleted
                        cursorY = self.cursorCoordinate[1]
                        startY = self._startCoordinate[1]

                # if self.modeDecimal[1]:
                #     cursorY = int(cursorY)
                #     startY = int(startY)
                # YMode = '%i'

            else:

                # no visible spectra
                return

            # newCoords = self.mouseFormat % (self._axisOrder[0], cursorX,
            #                                 self._axisOrder[1], cursorY)
            newCoords = ' %s: %s\n %s: %s' % (self._axisOrder[0], self.XMode(cursorX),
                                              self._axisOrder[1], self.YMode(cursorY))

            self.mouseString = GLString(text=newCoords,
                                        font=self.globalGL.glSmallFont,
                                        x=valueToRatio(self.cursorCoordinate[0], self.axisL, self.axisR),
                                        y=valueToRatio(self.cursorCoordinate[1], self.axisB, self.axisT),
                                        color=self.foreground, GLContext=self,
                                        obj=None)
            self._mouseCoords = (self.cursorCoordinate[0], self.cursorCoordinate[1])

            if self._drawDeltaOffset:
                # diffCoords = self.diffMouseFormat % (self._axisOrder[0], (cursorX - startX),
                #                                      self._axisOrder[1], (cursorY - startY))
                diffCoords = ' d%s: %s\n d%s: %s' % (self._axisOrder[0], self.XMode(cursorX - startX),
                                                     self._axisOrder[1], self.YMode(cursorY - startY))

                self.diffMouseString = GLString(text=diffCoords,
                                                font=self.globalGL.glSmallFont,
                                                x=valueToRatio(self.cursorCoordinate[0], self.axisL, self.axisR),
                                                y=valueToRatio(self.cursorCoordinate[1], self.axisB, self.axisT) - (
                                                        self.globalGL.glSmallFont.height * 2.0 * self.deltaY),
                                                color=self.foreground, GLContext=self,
                                                obj=None)

    def drawMouseCoords(self):
        if self.underMouse():  # and self.mouseString:
            self.buildMouseCoords()
            # draw the mouse coordinates to the screen
            self.mouseString.drawTextArrayVBO(enableVBO=True)
            if self._drawDeltaOffset and self.diffMouseString:
                self.diffMouseString.drawTextArrayVBO(enableVBO=True)

    def drawSelectionBox(self):
        # should really use the proper VBOs for this
        if self._drawSelectionBox:
            GL.glEnable(GL.GL_BLEND)

            self._dragStart = self._scaleAxisToRatio(self._startCoordinate[0:2])
            self._dragEnd = self._scaleAxisToRatio(self._endCoordinate[0:2])

            if self._selectionMode == 1:  # yellow
                GL.glColor4f(*self.zoomAreaColour)
            elif self._selectionMode == 2:  # purple
                GL.glColor4f(*self.selectAreaColour)
            elif self._selectionMode == 3:  # cyan
                GL.glColor4f(*self.pickAreaColour)

            GL.glBegin(GL.GL_QUADS)
            GL.glVertex2d(self._dragStart[0], self._dragStart[1])
            GL.glVertex2d(self._dragEnd[0], self._dragStart[1])
            GL.glVertex2d(self._dragEnd[0], self._dragEnd[1])
            GL.glVertex2d(self._dragStart[0], self._dragEnd[1])
            GL.glEnd()

            if self._selectionMode == 1:  # yellow
                GL.glColor4f(*self.zoomAreaColourHard)
            elif self._selectionMode == 2:  # purple
                GL.glColor4f(*self.selectAreaColourHard)
            elif self._selectionMode == 3:  # cyan
                GL.glColor4f(*self.pickAreaColourHard)

            GL.glBegin(GL.GL_LINE_STRIP)
            GL.glVertex2d(self._dragStart[0], self._dragStart[1])
            GL.glVertex2d(self._dragEnd[0], self._dragStart[1])
            GL.glVertex2d(self._dragEnd[0], self._dragEnd[1])
            GL.glVertex2d(self._dragStart[0], self._dragEnd[1])
            GL.glVertex2d(self._dragStart[0], self._dragStart[1])
            GL.glEnd()
            GL.glDisable(GL.GL_BLEND)

    def drawMouseMoveLine(self):
        """Draw the line for the middleMouse dragging of peaks
        """
        if self._drawMouseMoveLine:
            GL.glColor4f(*self.mouseMoveLineColour)
            GL.glBegin(GL.GL_LINES)

            startCoord = self._scaleAxisToRatio(self._startCoordinate[0:2])
            cursCoord = self._scaleAxisToRatio(self.cursorCoordinate[0:2])

            GL.glVertex2d(startCoord[0], startCoord[1])
            GL.glVertex2d(cursCoord[0], cursCoord[1])
            GL.glEnd()

    def _getSliceData(self, spectrumView, points, sliceDim):
        """Get the slice along sliceDim, using spectrumView to get to spectrum
        Separate routine to allow for caching,
        uses Spectrum._getSliceDataFromPlane for efficient extraction of slices

        points as integer list, with points[sliceDim-1] set to 1, as this allows
        the cached _getSliceFromPlane to work best

        return sliceData numpy array
        """
        axisCodes = [a.code for a in spectrumView.strip.axes][0:2]
        planeDims = spectrumView.spectrum.getByAxisCodes('dimensions', axisCodes)
        pointInt = [1 + int(pnt + 0.5) for pnt in points]
        pointInt[sliceDim - 1] = 1  # To improve caching; points, dimensions are 1-based

        # print('>>>_getSliceData', pointInt, points)
        data = np.array(spectrumView.spectrum._getSliceDataFromPlane(pointInt,
                                                                     xDim=planeDims[0], yDim=planeDims[1], sliceDim=sliceDim))
        return data

    def _newStaticHTraceData(self, spectrumView, tracesDict,
                             point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel, position,
                             ph0=None, ph1=None, pivot=None):

        try:
            data = self._getSliceData(spectrumView=spectrumView, points=point, sliceDim=xDataDim.dim)

            # preData = data
            # if ph0 is not None and ph1 is not None and pivot is not None:
            #     preData = Phasing.phaseRealData(data, ph0, ph1, pivot)

            x = np.array(
                    [xDataDim.primaryDataDimRef.pointToValue(p + 1) for p in range(xMinFrequency, xMaxFrequency + 1)])
            # y = positionPixel[1] + spectrumView._traceScale * (self.axisT - self.axisB) * \
            #     np.array([preData[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency + 1)])

            colour = spectrumView._getColour(self.SPECTRUMPOSCOLOUR, '#aaaaaa')
            colR = int(colour.strip('# ')[0:2], 16) / 255.0
            colG = int(colour.strip('# ')[2:4], 16) / 255.0
            colB = int(colour.strip('# ')[4:6], 16) / 255.0

            hSpectrum = GLVertexArray(numLists=1,
                                      renderMode=GLRENDERMODE_RESCALE,
                                      blendMode=False,
                                      drawMode=GL.GL_LINE_STRIP,
                                      dimension=2,
                                      GLContext=self)
            tracesDict.append(hSpectrum)

            # add extra vertices to give a horizontal line across the trace
            xLen = x.size
            x = np.append(x, (x[xLen - 1], x[0]))
            # y = np.append(y, (positionPixel[1], positionPixel[1]))

            numVertices = len(x)
            # hSpectrum = tracesDict[-1]
            hSpectrum.indices = numVertices
            hSpectrum.numVertices = numVertices
            hSpectrum.indices = np.arange(numVertices, dtype=np.uint32)
            hSpectrum.vertices = np.empty(hSpectrum.numVertices * 2, dtype=np.float32)
            hSpectrum.vertices[::2] = x
            # hSpectrum.vertices[1::2] = y
            hSpectrum.colors = np.array(self._phasingTraceColour * numVertices, dtype=np.float32)

            # change to colour of the last 2 points to the spectrum colour
            colLen = hSpectrum.colors.size
            hSpectrum.colors[colLen - 8:colLen] = (colR, colG, colB, 1.0, colR, colG, colB, 1.0)

            # store the pre-phase data
            hSpectrum.data = data
            hSpectrum.values = (spectrumView, point, xDataDim,
                                xMinFrequency, xMaxFrequency,
                                xNumPoints, positionPixel, position)
            hSpectrum.spectrumView = spectrumView

        except Exception as es:
            tracesDict = []

    def _newStaticVTraceData(self, spectrumView, tracesDict,
                             point, yDataDim, yMinFrequency, yMaxFrequency, yNumPoints, positionPixel, position,
                             ph0=None, ph1=None, pivot=None):

        try:
            data = self._getSliceData(spectrumView=spectrumView, points=point, sliceDim=yDataDim.dim)

            # preData = data
            # if ph0 is not None and ph1 is not None and pivot is not None:
            #     preData = Phasing.phaseRealData(data, ph0, ph1, pivot)

            y = np.array(
                    [yDataDim.primaryDataDimRef.pointToValue(p + 1) for p in range(yMinFrequency, yMaxFrequency + 1)])
            # x = positionPixel[0] + spectrumView._traceScale * (self.axisL - self.axisR) * \
            #     np.array([preData[p % yNumPoints] for p in range(yMinFrequency, yMaxFrequency + 1)])

            colour = spectrumView._getColour(self.SPECTRUMPOSCOLOUR, '#aaaaaa')
            colR = int(colour.strip('# ')[0:2], 16) / 255.0
            colG = int(colour.strip('# ')[2:4], 16) / 255.0
            colB = int(colour.strip('# ')[4:6], 16) / 255.0

            vSpectrum = GLVertexArray(numLists=1,
                                      renderMode=GLRENDERMODE_RESCALE,
                                      blendMode=False,
                                      drawMode=GL.GL_LINE_STRIP,
                                      dimension=2,
                                      GLContext=self)
            tracesDict.append(vSpectrum)

            # add extra vertices to give a horizontal line across the trace
            yLen = y.size
            y = np.append(y, (y[yLen - 1], y[0]))
            # x = np.append(x, (positionPixel[0], positionPixel[0]))

            numVertices = len(y)
            # vSpectrum = tracesDict[-1]
            vSpectrum.indices = numVertices
            vSpectrum.numVertices = numVertices
            vSpectrum.indices = np.arange(numVertices, dtype=np.uint32)
            vSpectrum.vertices = np.empty(vSpectrum.numVertices * 2, dtype=np.float32)
            # vSpectrum.vertices[::2] = x
            vSpectrum.vertices[1::2] = y
            vSpectrum.colors = np.array(self._phasingTraceColour * numVertices, dtype=np.float32)

            # change to colour of the last 2 points to the spectrum colour
            colLen = vSpectrum.colors.size
            vSpectrum.colors[colLen - 8:colLen] = (colR, colG, colB, 1.0, colR, colG, colB, 1.0)

            # store the pre-phase data
            vSpectrum.data = data
            vSpectrum.values = (spectrumView, point, yDataDim,
                                yMinFrequency, yMaxFrequency,
                                yNumPoints, positionPixel, position)
            vSpectrum.spectrumView = spectrumView

        except Exception as es:
            tracesDict = []

    def _updateHTraceData(self, spectrumView, tracesDict,
                          point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, positionPixel,
                          ph0=None, ph1=None, pivot=None):

        try:
            data = self._getSliceData(spectrumView=spectrumView, points=point, sliceDim=xDataDim.dim)

            if ph0 is not None and ph1 is not None and pivot is not None:
                data = Phasing.phaseRealData(data, ph0, ph1, pivot)

            dataY = np.array([data[p % xNumPoints] for p in range(xMinFrequency, xMaxFrequency + 1)])
            x = np.array(
                    [xDataDim.primaryDataDimRef.pointToValue(p + 1) for p in range(xMinFrequency, xMaxFrequency + 1)])
            y = positionPixel[1] + spectrumView._traceScale * (self.axisT - self.axisB) * dataY

            # print('>>>', positionPixel)
            col1 = getattr(spectrumView.spectrum,
                           self.SPECTRUMPOSCOLOUR)  #spectrumView._getColour('sliceColour', '#aaaaaa')
            if self.is1D:
                col2 = col1
            else:
                col2 = getattr(spectrumView.spectrum,
                               self.SPECTRUMNEGCOLOUR)  #spectrumView._getColour('sliceColour', '#aaaaaa')
            colR = int(col1.strip('# ')[0:2], 16) / 255.0
            colG = int(col1.strip('# ')[2:4], 16) / 255.0
            colB = int(col1.strip('# ')[4:6], 16) / 255.0

            # fade the trace to the negative colour
            # colRn = int(col2.strip('# ')[0:2], 16) / 255.0
            # colGn = int(col2.strip('# ')[2:4], 16) / 255.0
            # colBn = int(col2.strip('# ')[4:6], 16) / 255.0

            if spectrumView not in tracesDict.keys():
                tracesDict[spectrumView] = GLVertexArray(numLists=1,
                                                         renderMode=GLRENDERMODE_REBUILD,
                                                         blendMode=False,
                                                         drawMode=GL.GL_LINE_STRIP,
                                                         dimension=2,
                                                         GLContext=self)

            # add extra vertices to give a horizontal line across the trace
            xLen = x.size
            x = np.append(x, (x[xLen - 1], x[0]))
            y = np.append(y, (positionPixel[1], positionPixel[1]))

            numVertices = len(x)
            hSpectrum = tracesDict[spectrumView]
            hSpectrum.indices = numVertices
            hSpectrum.numVertices = numVertices
            hSpectrum.indices = np.arange(numVertices, dtype=np.uint32)
            hSpectrum.vertices = np.empty(numVertices * 2, dtype=np.float32)
            hSpectrum.vertices[::2] = x
            hSpectrum.vertices[1::2] = y
            hSpectrum.colors = np.array([colR, colG, colB, 1.0] * numVertices, dtype=np.float32)
            # hSpectrum.colors[dataY < 0] = [colRn, colGn, colBn, 1.0]

            # push to VBO

        except Exception as es:
            tracesDict[spectrumView].clearArrays()

    def _updateVTraceData(self, spectrumView, tracesDict,
                          point, yDataDim, yMinFrequency, yMaxFrequency, yNumPoints, positionPixel,
                          ph0=None, ph1=None, pivot=None):

        try:
            data = self._getSliceData(spectrumView=spectrumView, points=point, sliceDim=yDataDim.dim)

            if ph0 is not None and ph1 is not None and pivot is not None:
                data = Phasing.phaseRealData(data, ph0, ph1, pivot)

            dataX = np.array([data[p % yNumPoints] for p in range(yMinFrequency, yMaxFrequency + 1)])
            y = np.array(
                    [yDataDim.primaryDataDimRef.pointToValue(p + 1) for p in range(yMinFrequency, yMaxFrequency + 1)])
            x = positionPixel[0] + spectrumView._traceScale * (self.axisL - self.axisR) * dataX

            col1 = getattr(spectrumView.spectrum,
                           self.SPECTRUMPOSCOLOUR)  #spectrumView._getColour('sliceColour', '#aaaaaa')
            if self.is1D:
                col2 = col1
            else:
                col2 = getattr(spectrumView.spectrum,
                               self.SPECTRUMNEGCOLOUR)  #spectrumView._getColour('sliceColour', '#aaaaaa')
            colR = int(col1.strip('# ')[0:2], 16) / 255.0
            colG = int(col1.strip('# ')[2:4], 16) / 255.0
            colB = int(col1.strip('# ')[4:6], 16) / 255.0

            # fade the trace to the negative colour
            # colRn = int(col2.strip('# ')[0:2], 16) / 255.0
            # colGn = int(col2.strip('# ')[2:4], 16) / 255.0
            # colBn = int(col2.strip('# ')[4:6], 16) / 255.0

            if spectrumView not in tracesDict.keys():
                tracesDict[spectrumView] = GLVertexArray(numLists=1,
                                                         renderMode=GLRENDERMODE_REBUILD,
                                                         blendMode=False,
                                                         drawMode=GL.GL_LINE_STRIP,
                                                         dimension=2,
                                                         GLContext=self)

            # add extra vertices to give a vertical line across the trace
            yLen = y.size
            y = np.append(y, (y[yLen - 1], y[0]))
            x = np.append(x, (positionPixel[0], positionPixel[0]))

            numVertices = len(x)
            vSpectrum = tracesDict[spectrumView]
            vSpectrum.indices = numVertices
            vSpectrum.numVertices = numVertices
            vSpectrum.indices = np.arange(numVertices, dtype=np.uint32)
            vSpectrum.vertices = np.zeros(numVertices * 2, dtype=np.float32)
            vSpectrum.vertices[::2] = x
            vSpectrum.vertices[1::2] = y
            vSpectrum.colors = np.array([colR, colG, colB, 1.0] * numVertices, dtype=np.float32)
            # vSpectrum.colors[dataX < 0] = [colRn, colGn, colBn, 1.0]

        except Exception as es:
            tracesDict[spectrumView].clearArrays()

    def _tracesNeedUpdating(self, spectrumView=None):
        """Check if traces need updating on _lastTracePoint, use spectrumView to see
        if cursor has moved sufficiently far to warrant an update of the traces
        """
        _tmp, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, \
        yDataDim, yMinFrequency, yMaxFrequency, yNumPoints \
            = spectrumView._getTraceParams(self.cursorCoordinate)

        if spectrumView not in self._lastTracePoint:
            numDim = len(spectrumView.strip.axes)
            self._lastTracePoint[spectrumView] = [-1] * numDim

        lastTrace = self._lastTracePoint[spectrumView]

        point = [int(p + 0.5) for p in point]

        # get the correct ordering for horizontal/vertical
        axisCodes = [a.code for a in spectrumView.strip.axes]  # [0:2]
        planeDims = spectrumView.spectrum.getByAxisCodes('indices', axisCodes)

        if point[planeDims[0]] >= xNumPoints or point[planeDims[1]] >= yNumPoints:
            # Extra check whether the new point is out of range if numLimits
            return False

        if self._updateHTrace and not self._updateVTrace and point[planeDims[1]] == lastTrace[planeDims[1]]:
            # Only HTrace, an y-point has not changed
            return False
        elif not self._updateHTrace and self._updateVTrace and point[planeDims[0]] == lastTrace[planeDims[0]]:
            # Only VTrace and x-point has not changed
            return False
        elif self._updateHTrace and self._updateVTrace and point[planeDims[0]] == lastTrace[planeDims[0]] \
                and point[planeDims[1]] == lastTrace[planeDims[1]]:
            # both HTrace and Vtrace, both x-point an y-point have not changed
            return False
        # We need to update; save this point as the last point
        self._lastTracePoint[spectrumView] = point
        return True

    def updateTraces(self):
        if self.strip.isDeleted:
            return

        position = [self.cursorCoordinate[0], self.cursorCoordinate[1]]  #list(cursorPosition)
        for axis in self._orderedAxes[2:]:
            position.append(axis.position)

        positionPixel = (self.cursorCoordinate[0], self.cursorCoordinate[1])

        for spectrumView in self._ordering:  # strip.spectrumViews:
            if spectrumView.isDeleted:
                continue

            if self._tracesNeedUpdating(spectrumView):

                phasingFrame = self.spectrumDisplay.phasingFrame
                if phasingFrame.isVisible():
                    ph0 = phasingFrame.slider0.value()
                    ph1 = phasingFrame.slider1.value()
                    pivotPpm = phasingFrame.pivotEntry.get()
                    direction = phasingFrame.getDirection()
                    # dataDim = self._apiStripSpectrumView.spectrumView.orderedDataDims[direction]
                    # pivot = dataDim.primaryDataDimRef.valueToPoint(pivotPpm)
                    axisIndex = spectrumView._displayOrderSpectrumDimensionIndices[direction]
                    pivot = spectrumView.spectrum.mainSpectrumReferences[axisIndex].valueToPoint(pivotPpm)
                else:
                    # ph0 = ph1 = direction = 0
                    # pivot = 1
                    direction = 0
                    ph0 = ph1 = pivot = None

                inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, \
                yDataDim, yMinFrequency, yMaxFrequency, yNumPoints \
                    = spectrumView._getTraceParams(position)

                # intPositionPixel = [spectrumView.spectrum.mainSpectrumReferences[ax].pointToValue(pp) for ax, pp in enumerate(self._lastTracePoint[:2])]
                ref = spectrumView.spectrum.mainSpectrumReferences

                # get the correct axis ordering for the refDims
                axisCodes = [a.code for a in spectrumView.strip.axes]  # [0:2]
                planeDims = spectrumView.spectrum.getByAxisCodes('indices', axisCodes)

                # rounds the wrong way when point values are adjusted from negative
                intPositionPixel = [ref[planeDims[ax]].pointToValue(int(ref[planeDims[ax]].valueToPoint(pp) + 0.5)) for ax, pp in enumerate(positionPixel)]

                if direction == 0:
                    if self._updateHTrace:
                        self._updateHTraceData(spectrumView, self._hTraces, point, xDataDim, xMinFrequency, xMaxFrequency,
                                               xNumPoints, intPositionPixel, ph0, ph1, pivot)
                    if self._updateVTrace:
                        self._updateVTraceData(spectrumView, self._vTraces, point, yDataDim, yMinFrequency, yMaxFrequency,
                                               yNumPoints, intPositionPixel)
                else:
                    if self._updateHTrace:
                        self._updateHTraceData(spectrumView, self._hTraces, point, xDataDim, xMinFrequency, xMaxFrequency,
                                               xNumPoints, intPositionPixel)
                    if self._updateVTrace:
                        self._updateVTraceData(spectrumView, self._vTraces, point, yDataDim, yMinFrequency, yMaxFrequency,
                                               yNumPoints, intPositionPixel, ph0, ph1, pivot)

    def newTrace(self, position=None):
        position = position if position else [self.cursorCoordinate[0], self.cursorCoordinate[1]]  #list(cursorPosition)

        # add to the list of traces
        self._currentTraces.append(position)

        for axis in self._orderedAxes[2:]:
            position.append(axis.position)

        positionPixel = position  #(self.cursorCoordinate[0], self.cursorCoordinate[1])

        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            # only add phasing trace for the visible spectra
            if spectrumView.isVisible():

                phasingFrame = self.spectrumDisplay.phasingFrame

                ph0 = phasingFrame.slider0.value()
                ph1 = phasingFrame.slider1.value()
                pivotPpm = phasingFrame.pivotEntry.get()
                direction = phasingFrame.getDirection()
                # dataDim = self._apiStripSpectrumView.spectrumView.orderedDataDims[direction]
                # pivot = dataDim.primaryDataDimRef.(pivotPpm)
                axisIndex = spectrumView._displayOrderSpectrumDimensionIndices[direction]
                ref = spectrumView.spectrum.mainSpectrumReferences
                pivot = ref[axisIndex].valueToPoint(pivotPpm)

                if self.is1D:
                    inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints = spectrumView._getTraceParams(
                            position)
                    self._newStatic1DTraceData(spectrumView, self._staticHTraces, point, xDataDim, xMinFrequency,
                                               xMaxFrequency,
                                               xNumPoints, positionPixel, position, ph0, ph1, pivot)
                else:
                    inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xNumPoints, yDataDim, yMinFrequency, yMaxFrequency, yNumPoints \
                        = spectrumView._getTraceParams(position)

                    # get the correct axis ordering for the refDims
                    axisCodes = [a.code for a in spectrumView.strip.axes]  # [0:2]
                    planeDims = spectrumView.spectrum.getByAxisCodes('indices', axisCodes)

                    # rounds the wrong way when point values are adjusted from negative
                    intPositionPixel = [ref[planeDims[ax]].pointToValue(int(ref[planeDims[ax]].valueToPoint(pp) + 0.5)) for ax, pp in enumerate(positionPixel)]

                    if direction == 0:
                        self._newStaticHTraceData(spectrumView, self._staticHTraces, point, xDataDim, xMinFrequency,
                                                  xMaxFrequency, xNumPoints, intPositionPixel, position, ph0, ph1, pivot)
                    else:
                        self._newStaticVTraceData(spectrumView, self._staticVTraces, point, yDataDim, yMinFrequency,
                                                  yMaxFrequency, yNumPoints, intPositionPixel, position, ph0, ph1, pivot)

    def clearStaticTraces(self):
        self._staticVTraces = []
        self._staticHTraces = []
        self._currentTraces = []
        self.update()

    def rescaleStaticTraces(self):
        for hTrace in self._staticHTraces:
            hTrace.renderMode = GLRENDERMODE_RESCALE

        for vTrace in self._staticVTraces:
            vTrace.renderMode = GLRENDERMODE_RESCALE

        self.update()

    def rescaleStaticHTraces(self):
        for hTrace in self._staticHTraces:
            hTrace.renderMode = GLRENDERMODE_RESCALE

    def rescaleStaticVTraces(self):
        for vTrace in self._staticVTraces:
            vTrace.renderMode = GLRENDERMODE_RESCALE

    def rebuildTraces(self):
        traces = self._currentTraces
        self.clearStaticTraces()
        for trace in traces:
            self.newTrace(trace[:2])

    def buildStaticTraces(self):

        phasingFrame = self.spectrumDisplay.phasingFrame
        if phasingFrame.isVisible():
            ph0 = phasingFrame.slider0.value()
            ph1 = phasingFrame.slider1.value()
            pivotPpm = phasingFrame.pivotEntry.get()
            direction = phasingFrame.getDirection()
            # dataDim = self._apiStripSpectrumView.spectrumView.orderedDataDims[direction]
            # pivot = dataDim.primaryDataDimRef.valueToPoint(pivotPpm)

            deleteHList = []
            for hTrace in self._staticHTraces:
                if hTrace.spectrumView and hTrace.spectrumView.isDeleted:
                    deleteHList.append(hTrace)
                    continue

                if hTrace.renderMode == GLRENDERMODE_RESCALE:
                    hTrace.renderMode = GLRENDERMODE_DRAW

                    # print('>>>buildStaticTraces hTraces')
                    # [spectrumView._traceScale, point, yDataDim,
                    # yMinFrequency, yMaxFrequency,
                    # yNumPoints, positionPixel]

                    values = hTrace.values
                    axisIndex = values[0]._displayOrderSpectrumDimensionIndices[direction]
                    pivot = values[0].spectrum.mainSpectrumReferences[axisIndex].valueToPoint(pivotPpm)
                    positionPixel = values[6]

                    preData = Phasing.phaseRealData(hTrace.data, ph0, ph1, pivot)

                    if self.is1D:
                        hTrace.vertices[1::2] = preData
                    else:
                        y = values[6][1] + values[0]._traceScale * (self.axisT - self.axisB) * \
                            np.array([preData[p % values[5]] for p in range(values[3], values[4] + 1)])

                        y = np.append(y, (positionPixel[1], positionPixel[1]))
                        hTrace.vertices[1::2] = y

                    # build the VBOs here
                    hTrace.defineVertexColorVBO(enableVBO=True)

            for dd in deleteHList:
                self._staticHTraces.remove(dd)

            deleteVList = []
            for vTrace in self._staticVTraces:
                if vTrace.spectrumView and vTrace.spectrumView.isDeleted:
                    deleteVList.append(vTrace)
                    continue

                if vTrace.renderMode == GLRENDERMODE_RESCALE:
                    vTrace.renderMode = GLRENDERMODE_DRAW

                    # print('>>>buildStaticTraces vTraces')

                    values = vTrace.values
                    axisIndex = values[0]._displayOrderSpectrumDimensionIndices[direction]
                    pivot = values[0].spectrum.mainSpectrumReferences[axisIndex].valueToPoint(pivotPpm)
                    positionPixel = values[6]

                    preData = Phasing.phaseRealData(vTrace.data, ph0, ph1, pivot)

                    x = values[6][0] + values[0]._traceScale * (self.axisL - self.axisR) * \
                        np.array([preData[p % values[5]] for p in range(values[3], values[4] + 1)])

                    x = np.append(x, (positionPixel[0], positionPixel[0]))
                    vTrace.vertices[::2] = x

                    # build the VBOs here
                    vTrace.defineVertexColorVBO(enableVBO=True)

            for dd in deleteVList:
                self._staticVTraces.remove(dd)

    def drawTraces(self):
        if self.strip.isDeleted:
            return

        phasingFrame = self.spectrumDisplay.phasingFrame
        if phasingFrame.isVisible():

            self.buildStaticTraces()

            for hTrace in self._staticHTraces:
                if hTrace.spectrumView and not hTrace.spectrumView.isDeleted and hTrace.spectrumView.isVisible():
                    # hTrace.drawVertexColor()

                    if self._stackingMode:
                        # use the stacking matrix to offset the 1D spectra
                        self.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
                                                                            1, GL.GL_FALSE,
                                                                            self._spectrumSettings[hTrace.spectrumView][
                                                                                GLDefs.SPECTRUM_STACKEDMATRIX])
                    hTrace.drawVertexColorVBO(enableVBO=True)

            for vTrace in self._staticVTraces:
                if vTrace.spectrumView and not vTrace.spectrumView.isDeleted and vTrace.spectrumView.isVisible():
                    # vTrace.drawVertexColor()

                    if self._stackingMode:
                        # use the stacking matrix to offset the 1D spectra
                        self.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
                                                                            1, GL.GL_FALSE,
                                                                            self._spectrumSettings[vTrace.spectrumView][
                                                                                GLDefs.SPECTRUM_STACKEDMATRIX])
                    vTrace.drawVertexColorVBO(enableVBO=True)

        # only paint if mouse is in the window
        if self.underMouse():
            # self.updateTraces()

            # spawn rebuild/paint of traces
            # if self._updateHTrace or self._updateVTrace:
            #   self.updateTraces()

            deleteHList = []
            if self._updateHTrace and (self.showActivePhaseTrace or not phasingFrame.isVisible()):
                for hTrace in self._hTraces.keys():
                    trace = self._hTraces[hTrace]
                    if hTrace and hTrace.isDeleted:
                        deleteHList.append(hTrace)
                        continue

                    if hTrace and not hTrace.isDeleted and hTrace.isVisible():
                        # trace.drawVertexColor()
                        trace.drawVertexColorVBO(enableVBO=False)

            for dd in deleteHList:
                del self._hTraces[dd]

            deleteVList = []
            if self._updateVTrace and (self.showActivePhaseTrace or not phasingFrame.isVisible()):
                for vTrace in self._vTraces.keys():
                    trace = self._vTraces[vTrace]
                    if vTrace and vTrace.isDeleted:
                        deleteVList.append(vTrace)
                        continue

                    if vTrace and not vTrace.isDeleted and vTrace.isVisible():
                        # trace.drawVertexColor()
                        trace.drawVertexColorVBO(enableVBO=False)

            for dd in deleteVList:
                del self._vTraces[dd]

    def initialiseTraces(self):
        # set up the arrays and dimension for showing the horizontal/vertical traces
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            self._spectrumSettings[spectrumView] = {}

            self._spectrumValues = spectrumView._getValues(dimensionCount=2)

            # get the bounding box of the spectra
            dx = self.sign(self.axisR - self.axisL)
            fx0, fx1 = self._spectrumValues[0].maxAliasedFrequency, self._spectrumValues[0].minAliasedFrequency

            # check tolerances
            if not self._widthsChangedEnough((fx0, 0.0), (fx1, 0.0), tol=1e-10):
                fx0, fx1 = 1.0, -1.0

            dxAF = fx0 - fx1
            xScale = dx * dxAF / self._spectrumValues[0].totalPointCount

            if spectrumView.spectrum.dimensionCount > 1:
                dy = self.sign(self.axisT - self.axisB)
                fy0, fy1 = self._spectrumValues[1].maxAliasedFrequency, self._spectrumValues[1].minAliasedFrequency

                # check tolerances
                if not self._widthsChangedEnough((fy0, 0.0), (fy1, 0.0), tol=1e-10):
                    fy0, fy1 = 1.0, -1.0

                dyAF = fy0 - fy1
                yScale = dy * dyAF / self._spectrumValues[1].totalPointCount
            else:
                dy = self.sign(self.axisT - self.axisB)
                if spectrumView.spectrum.intensities is not None and spectrumView.spectrum.intensities.size != 0:
                    fy0, fy1 = np.max(spectrumView.spectrum.intensities), np.min(spectrumView.spectrum.intensities)
                else:
                    fy0, fy1 = 0.0, 0.0

                # check tolerances
                if not self._widthsChangedEnough((fy0, 0.0), (fy1, 0.0), tol=1e-10):
                    fy0, fy1 = 1.0, -1.0

                dyAF = fy0 - fy1
                yScale = dy * dyAF / 1.0

            # create modelview matrix for the spectrum to be drawn
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX] = np.zeros((16,), dtype=np.float32)

            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MATRIX][0:16] = [xScale, 0.0, 0.0, 0.0,
                                                                                  0.0, yScale, 0.0, 0.0,
                                                                                  0.0, 0.0, 1.0, 0.0,
                                                                                  fx0, fy0, 0.0, 1.0]
            # setup information for the horizontal/vertical traces
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXXALIAS] = fx0
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINXALIAS] = fx1
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MAXYALIAS] = fy0
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_MINYALIAS] = fy1
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DXAF] = dxAF
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_DYAF] = dyAF
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_XSCALE] = xScale
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_YSCALE] = yScale

    def _makeSpectrumArray(self, spectrumView, drawList):
        drawList.renderMode = GLRENDERMODE_DRAW
        spectrum = spectrumView.spectrum
        drawList.clearArrays()

        for position, dataArray in spectrumView._getPlaneData():
            ma = np.amax(dataArray)
            mi = np.amin(dataArray)
            # min(  abs(  fract(P.z * gsize) - 0.5), 0.2);
            # newData = np.clip(np.absolute(np.remainder((50.0*dataArray/ma), 1.0)-0.5), 0.2, 50.0)
            dataScale = 15.0
            newData = dataScale * dataArray / ma
            npX = dataArray.shape[0]
            npY = dataArray.shape[1]

            indexing = (npX - 1) * (npY - 1)
            elements = npX * npY
            drawList.indices = np.zeros(int(indexing * 6), dtype=np.uint32)
            drawList.vertices = np.zeros(int(elements * 4), dtype=np.float32)
            drawList.colors = np.zeros(int(elements * 4), dtype=np.float32)

            ii = 0
            for y0 in range(0, npY):
                for x0 in range(0, npX):
                    vertex = [y0, x0, newData[x0, y0], 0.5 + newData[x0, y0] / (2.0 * dataScale)]
                    color = [0.5, 0.5, 0.5, 1.0]
                    drawList.vertices[ii * 4:ii * 4 + 4] = vertex
                    drawList.colors[ii * 4:ii * 4 + 4] = color
                    ii += 1
            drawList.numVertices = elements

            ii = 0
            for y0 in range(0, npY - 1):
                for x0 in range(0, npX - 1):
                    corner = x0 + (y0 * npX)
                    indices = [corner, corner + 1, corner + npX,
                               corner + 1, corner + npX, corner + 1 + npX]
                    drawList.indices[ii * 6:ii * 6 + 6] = indices
                    ii += 1
            break

    def sizeHint(self):
        return QSize(self.w, self.h)

    def set3DProjection(self):
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GL.glOrtho(-0.5, +0.5, +0.5, -0.5, 4.0, 15.0)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadIdentity()

    def setClearColor(self, c):
        GL.glClearColor(c.redF(), c.greenF(), c.blueF(), c.alphaF())

    def setColor(self, c):
        GL.glColor4f(c.redF(), c.greenF(), c.blueF(), c.alphaF())

    def highlightCurrentStrip(self, current):
        if current:
            self.highlighted = True

            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD
            # self.buildGrid()
            # self.buildAxisLabels()

            if self.stripIDString:
                self.stripIDString.renderMode = GLRENDERMODE_REBUILD
            # self.drawOverlayText(refresh=True)

            # set axes colour
            # set stripIDStringcolour
            # set to self.highLightColour
        else:
            self.highlighted = False

            for gr in self.gridList:
                gr.renderMode = GLRENDERMODE_REBUILD
            # self.buildGrid()
            # self.buildAxisLabels()

            if self.stripIDString:
                self.stripIDString.renderMode = GLRENDERMODE_REBUILD
            # self.drawOverlayText(refresh=True)

            # set axes colour
            # set stripIDStringcolour
            # set to self.foreground

        self.update()

    def _buildAxes(self, gridGLList, axisList=None, scaleGrid=None, r=0.0, g=0.0, b=0.0, transparency=256.0):
        """Build the grid
        """

        def check(ll):
            # check if a number ends in an even digit
            val = '%.0f' % (ll[3] / ll[4])
            valLen = len(val)
            if val[valLen - 1] in '02468':
                return True

        def valueToRatio(val, x0, x1):
            return (val - x0) / (x1 - x0)

        labelling = {'0': [], '1': []}
        labelsChanged = False

        # check if the width is too small to draw too many grid levels
        boundX = (self.w - self.AXIS_MARGINRIGHT) if self._drawRightAxis else self.w
        boundY = (self.h - self.AXIS_MARGINBOTTOM) if self._drawBottomAxis else self.h
        scaleBounds = (boundX, boundY)

        if gridGLList.renderMode == GLRENDERMODE_REBUILD:

            # get the list of visible spectra, or the first in the list
            visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
            thisSpec = visibleSpectra[0] if visibleSpectra else self._ordering[0].spectrum if self._ordering and not self._ordering[0].isDeleted else None

            if thisSpec:
                # generate different axes depending on units - X Axis
                if self.XAXES[self._xUnits] == GLDefs.AXISUNITSPPM:
                    axisLimitL = self.axisL
                    axisLimitR = self.axisR
                    self.XMode = self._floatFormat

                elif self.XAXES[self._xUnits] == GLDefs.AXISUNITSHZ:
                    if self._ordering:

                        # thisSpec = self._ordering[0].spectrum

                        if self.is1D:
                            axisLimitL = self.axisL * thisSpec.spectrometerFrequencies[0]
                            axisLimitR = self.axisR * thisSpec.spectrometerFrequencies[0]

                        else:
                            # get the axis ordering from the spectrumDisplay and map to the strip
                            stripAxisCodes = self.strip.axisCodes
                            try:
                                indices = thisSpec.getByAxisCodes('indices', stripAxisCodes)
                            except Exception as es:
                                indices = thisSpec.getByAxisCodes('indices', stripAxisCodes[0:2])

                            axisLimitL = self.axisL * thisSpec.spectrometerFrequencies[indices[0]]
                            axisLimitR = self.axisR * thisSpec.spectrometerFrequencies[indices[0]]

                    else:
                        # error trap all spectra deleted
                        axisLimitL = self.axisL
                        axisLimitR = self.axisR
                    self.XMode = self._floatFormat

                else:
                    if self._ordering:

                        # visibleSpectra = [specView.spectrum for specView in self._ordering if specView.isVisible()]
                        # thisSpec = visibleSpectra[0] if visibleSpectra else self._ordering[0].spectrum

                        if self.is1D:
                            axisLimitL = thisSpec.mainSpectrumReferences[0].valueToPoint(self.axisL)
                            axisLimitR = thisSpec.mainSpectrumReferences[0].valueToPoint(self.axisR)

                        else:
                            # get the axis ordering from the spectrumDisplay and map to the strip
                            stripAxisCodes = self.strip.axisCodes
                            try:
                                indices = thisSpec.getByAxisCodes('indices', stripAxisCodes)
                            except Exception as es:
                                indices = thisSpec.getByAxisCodes('indices', stripAxisCodes[0:2])

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

                        # thisSpec = self._ordering[0].spectrum

                        # get the axis ordering from the spectrumDisplay and map to the strip
                        stripAxisCodes = self.strip.axisCodes
                        try:
                            indices = thisSpec.getByAxisCodes('indices', stripAxisCodes)
                        except Exception as es:
                            indices = thisSpec.getByAxisCodes('indices', stripAxisCodes[0:2])

                        axisLimitT = self.axisT * thisSpec.spectrometerFrequencies[indices[1]]
                        axisLimitB = self.axisB * thisSpec.spectrometerFrequencies[indices[1]]

                    else:
                        # error trap all spectra deleted
                        axisLimitT = self.axisT
                        axisLimitB = self.axisB
                    self.YMode = self._floatFormat  # '%.3f'

                else:
                    if self._ordering:

                        # visibleSpectra = [specView.spectrum for specView in self._ordering if specView.isVisible()]
                        # thisSpec = visibleSpectra[0] if visibleSpectra else self._ordering[0].spectrum

                        # get the axis ordering from the spectrumDisplay and map to the strip
                        stripAxisCodes = self.strip.axisCodes
                        try:
                            indices = thisSpec.getByAxisCodes('indices', stripAxisCodes)
                        except Exception as es:
                            indices = thisSpec.getByAxisCodes('indices', stripAxisCodes[0:2])

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
                labelsChanged = True

                gridGLList.clearArrays()

                vertexList = ()
                indexList = ()
                colorList = ()

                index = 0
                for scaleOrder, i in enumerate(scaleGrid):  #  [2,1,0]:   ## Draw three different scales of grid
                    dist = br - ul
                    nlTarget = 10. ** i
                    d = 10. ** np.floor(np.log10(abs(dist / nlTarget)) + 0.5)

                    ul1 = np.floor(ul / d) * d
                    br1 = np.ceil(br / d) * d
                    dist = br1 - ul1
                    nl = (dist / d) + 0.5

                    for ax in axisList:  #   range(0,2):  ## Draw grid for both axes

                        # skip grid lines for point grids - not sure this is working
                        if d[0] < 0.1 and ax == 0 and self.XMode == self._intFormat:
                            continue
                        if d[1] < 0.1 and ax == 1 and self.YMode == self._intFormat:
                            continue

                        # # ignore narrow grids
                        # if self.w * (scaleOrder+1) < 250 or self.h * (scaleOrder+1) < 250:
                        #     continue
                        #
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

                                if '%.5f' % p1[0] == '%.5f' % p2[0]:  # check whether a vertical line - x axis

                                    # xLabel = str(int(p1[0])) if d[0] >=1 else self.XMode % p1[0]
                                    labelling[str(ax)].append((i, ax, valueToRatio(p1[0], axisLimitL, axisLimitR),
                                                               p1[0], d[0]))
                                else:
                                    # num = int(p1[1]) if d[1] >=1 else self.XMode % p1[1]
                                    labelling[str(ax)].append((i, ax, valueToRatio(p1[1], axisLimitB, axisLimitT),
                                                               p1[1], d[1]))

                            # append the new points to the end of nparray, ignoring narrow grids
                            if scaleBounds[ax] * (scaleOrder + 1) > 225:
                                indexList += (index, index + 1)
                                vertexList += (valueToRatio(p1[0], axisLimitL, axisLimitR),
                                               valueToRatio(p1[1], axisLimitB, axisLimitT),
                                               valueToRatio(p2[0], axisLimitL, axisLimitR),
                                               valueToRatio(p2[1], axisLimitB, axisLimitT))

                                alpha = min([1.0, c / transparency])
                                # gridGLList.colors = np.append(gridGLList.colors, (r, g, b, alpha, r, g, b, alpha))
                                colorList += (r, g, b, alpha, r, g, b, alpha)

                                gridGLList.numVertices += 2
                                index += 2

                # copy the arrays the the GLstore
                gridGLList.vertices = np.array(vertexList, dtype=np.float32)
                gridGLList.indices = np.array(indexList, dtype=np.uint32)
                gridGLList.colors = np.array(colorList, dtype=np.float32)

                # restrict the labelling to the maximum without overlap based on width
                # should be dependent on font size though
                while len(labelling['0']) > (self.w / 60.0):
                    #restrict X axis labelling
                    lStrings = labelling['0']
                    if check(lStrings[0]):
                        labelling['0'] = lStrings[0::2]  # [ls for ls in lStrings if check(ls)]
                    else:
                        labelling['0'] = lStrings[1::2]  # [ls for ls in lStrings if check(ls)]

                # # clean up strings if in _intFormat
                # if self.XMode == self._intFormat:
                #     for ll in labelling['0'][::-1]:
                #         if round(ll[3], 5) != int(ll[3]):
                #             # remove the item
                #             labelling['0'].remove(ll)

                while len(labelling['1']) > (self.h / 20.0):
                    #restrict Y axis labelling
                    lStrings = labelling['1']
                    if check(lStrings[0]):
                        labelling['1'] = lStrings[0::2]  # [ls for ls in lStrings if check(ls)]
                    else:
                        labelling['1'] = lStrings[1::2]  # [ls for ls in lStrings if check(ls)]

                # # clean up strings if in _intFormat
                # if self.YMode == self._intFormat:
                #     for ll in labelling['1'][::-1]:
                #         if round(ll[3], 5) != int(ll[3]):
                #             # remove the item
                #             labelling['1'].remove(ll)

        return labelling, labelsChanged

    def _widthsChangedEnough(self, r1, r2, tol=1e-5):
        # r1 = sorted(r1)
        # r2 = sorted(r2)
        # minDiff = abs(r1[0] - r2[0])
        # maxDiff = abs(r1[1] - r2[1])
        # return (minDiff > tol) or (maxDiff > tol)

        if len(r1) != len(r2):
            raise ValueError('WidthsChanged must be the same length')

        for ii in zip(r1, r2):
            if abs(ii[0] - ii[1]) > tol:
                return True

    @pyqtSlot(dict)
    def _glXAxisChanged(self, aDict):
        if self.strip.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # match only the scale for the X axis
            axisL = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLLEFTAXISVALUE]
            axisR = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLRIGHTAXISVALUE]

            if self._widthsChangedEnough([axisL, self.axisL], [axisR, self.axisR]):
                diff = (axisR - axisL) / 2.0
                mid = (self.axisR + self.axisL) / 2.0
                self.axisL = mid - diff
                self.axisR = mid + diff
                self._rescaleXAxis()
                self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glAxisLockChanged(self, aDict):
        if self.strip.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:
            self._axisLocked = aDict[GLNotifier.GLVALUES]
            self.update()

    @pyqtSlot(dict)
    def _glAxisUnitsChanged(self, aDict):
        if self.strip.isDeleted:
            return

        # update the list of visible spectra
        self._updateVisibleSpectrumViews()

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # read values from dataDict and set units
            if aDict[GLNotifier.GLVALUES]:
                self._xUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISXUNITS]
                self._yUnits = aDict[GLNotifier.GLVALUES][GLDefs.AXISYUNITS]
                self._axisLocked = aDict[GLNotifier.GLVALUES][GLDefs.AXISLOCKASPECTRATIO]
            self._rescaleAllAxes()

    def setAxisPosition(self, axisCode, position, update=True):
        # if not self.glReady: return

        stripAxisIndex = self.axisCodes.index(axisCode)

        if stripAxisIndex == 0:
            diff = (self.axisR - self.axisL) / 2.0
            self.axisL = position - diff
            self.axisR = position + diff

            self._rescaleXAxis(update=update)

        elif stripAxisIndex == 1:
            diff = (self.axisT - self.axisB) / 2.0
            self.axisB = position - diff
            self.axisT = position + diff

            self._rescaleYAxis(update=update)

    def setAxisWidth(self, axisCode, width, update=True):
        # if not self.glReady: return

        stripAxisIndex = self.axisCodes.index(axisCode)

        if stripAxisIndex == 0:
            diff = np.sign(self.axisR - self.axisL) * abs(width) / 2.0
            mid = (self.axisR + self.axisL) / 2.0
            self.axisL = mid - diff
            self.axisR = mid + diff

            self._rescaleXAxis(update=update)

        elif stripAxisIndex == 1:
            diff = np.sign(self.axisT - self.axisB) * abs(width) / 2.0
            mid = (self.axisT + self.axisB) / 2.0
            self.axisB = mid - diff
            self.axisT = mid + diff

            self._rescaleYAxis(update=update)

    def setAxisRange(self, axisCode, range, update=True):
        # if not self.glReady: return

        stripAxisIndex = self.axisCodes.index(axisCode)

        if stripAxisIndex == 0:
            if self.INVERTXAXIS:
                self.axisL = max(range)
                self.axisR = min(range)
            else:
                self.axisL = min(range)
                self.axisR = max(range)

            self._rescaleXAxis(update=update)

        elif stripAxisIndex == 1:
            if self.INVERTXAXIS:
                self.axisB = max(range)
                self.axisT = min(range)
            else:
                self.axisB = min(range)
                self.axisT = max(range)

            self._rescaleYAxis(update=update)

    @pyqtSlot(dict)
    def _glYAxisChanged(self, aDict):
        if self.strip.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # match the Y axis
            axisB = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLBOTTOMAXISVALUE]
            axisT = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLTOPAXISVALUE]

            if self._widthsChangedEnough([axisB, self.axisB], [axisT, self.axisT]):
                self.axisB = axisB
                self.axisT = axisT
                self._rescaleYAxis()
                self._storeZoomHistory()

    @pyqtSlot(dict)
    def _glAllAxesChanged(self, aDict):
        if self.strip.isDeleted:
            return

        sDisplay = aDict[GLNotifier.GLSPECTRUMDISPLAY]
        source = aDict[GLNotifier.GLSOURCE]

        if source != self and aDict[GLNotifier.GLSPECTRUMDISPLAY] == self.spectrumDisplay:

            # match the values for the Y axis, and scale for the X axis
            axisB = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLBOTTOMAXISVALUE]
            axisT = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLTOPAXISVALUE]
            axisL = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLLEFTAXISVALUE]
            axisR = aDict[GLNotifier.GLAXISVALUES][GLNotifier.GLRIGHTAXISVALUE]

            if self._widthsChangedEnough([axisB, self.axisB], [axisT, self.axisT]) and \
                    self._widthsChangedEnough([axisL, self.axisL], [axisR, self.axisR]):

                if self.spectrumDisplay.stripDirection == 'Y':

                    # strips are arranged in a row
                    diff = (axisR - axisL) / 2.0
                    mid = (self.axisR + self.axisL) / 2.0
                    self.axisL = mid - diff
                    self.axisR = mid + diff
                    self.axisB = axisB
                    self.axisT = axisT

                elif self.spectrumDisplay.stripDirection == 'X':

                    # strips are arranged in a column
                    diff = (axisT - axisB) / 2.0
                    mid = (self.axisT + self.axisB) / 2.0
                    self.axisB = mid - diff
                    self.axisT = mid + diff
                    self.axisL = axisL
                    self.axisR = axisR

                else:
                    # currently ignore - warnings will be logged elsewhere
                    pass

                self._rescaleAllAxes()
                self._storeZoomHistory()


    @pyqtSlot(dict)
    def _glMouseMoved(self, aDict):
        if self.strip.isDeleted:
            return

        if aDict[GLNotifier.GLSOURCE] != self:
            # self.cursorCoordinate = aDict[GLMOUSECOORDS]
            # self.update()

            mouseMovedDict = aDict[GLNotifier.GLMOUSEMOVEDDICT]

            if self._crosshairVisible:  # or self._updateVTrace or self._updateHTrace:

                if self._preferences.matchAxisCode == AXIS_MATCHATOMTYPE:
                    for n, axis in enumerate(self._axisOrder[:2]):
                        for ax in mouseMovedDict[AXIS_MATCHATOMTYPE].keys():
                            if ax and axis and ax[0] == axis[0] and axis[0] in mouseMovedDict[AXIS_ACTIVEAXES]:
                                self.cursorCoordinate[n] = mouseMovedDict[AXIS_MATCHATOMTYPE][ax]
                                break
                        else:
                            self.cursorCoordinate[n] = None

                elif self._preferences.matchAxisCode == AXIS_FULLATOMNAME:
                    for n, axis in enumerate(self._axisOrder[:2]):
                        for ax in mouseMovedDict[AXIS_FULLATOMNAME].keys():
                            if axis in mouseMovedDict[AXIS_FULLATOMNAME].keys():
                                self.cursorCoordinate[n] = mouseMovedDict[AXIS_FULLATOMNAME][axis]
                                break
                        else:
                            self.cursorCoordinate[n] = None

                self.current.cursorPosition = (self.cursorCoordinate[0], self.cursorCoordinate[1])

                # only need to redraw if we can see the cursor
                # if self._updateVTrace or self._updateHTrace:
                #   self.updateTraces()
                self.update()

    @pyqtSlot(dict)
    def _glEvent(self, aDict):
        """
    process events from the application/popups and other strips
    :param aDict - dictionary containing event flags:
    """
        if self.strip.isDeleted:
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
                        self.stripIDString.renderMode = GLRENDERMODE_REBUILD

                    if GLNotifier.GLPEAKLISTS in triggers:
                        for spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            for peakListView in spectrumView.peakListViews:
                                for peakList in targets:
                                    if peakList == peakListView.peakList:
                                        peakListView.buildSymbols = True
                        # self.buildPeakLists()

                    if GLNotifier.GLPEAKLISTLABELS in triggers:
                        for spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            for peakListView in spectrumView.peakListViews:
                                for peakList in targets:
                                    if peakList == peakListView.peakList:
                                        peakListView.buildLabels = True
                        # self.buildPeakListLabels()

                    if GLNotifier.GLMARKS in triggers:
                        self.buildMarks = True

                    if GLNotifier.GLHIGHLIGHTPEAKS in triggers:
                        self._GLPeaks.updateHighlightSymbols()

                    if GLNotifier.GLHIGHLIGHTMULTIPLETS in triggers:
                        self._GLMultiplets.updateHighlightSymbols()

                    if GLNotifier.GLHIGHLIGHTINTEGRALS in triggers:
                        self._GLIntegrals.updateHighlightSymbols()

                    if GLNotifier.GLALLCONTOURS in triggers:
                        self.buildAllContours()

                    if GLNotifier.GLALLPEAKS in triggers:
                        self._GLPeaks.updateAllSymbols()

                    if GLNotifier.GLALLMULTIPLETS in triggers:
                        self._GLMultiplets.updateAllSymbols()

                    if GLNotifier.GLANY in targets:
                        self._rescaleXAxis(update=False)

                    if GLNotifier.GLPEAKNOTIFY in targets:
                        self._GLPeaks.updateHighlightSymbols()

                    if GLNotifier.GLINTEGRALLISTS in triggers:

                        for spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            for integralListView in spectrumView.integralListViews:

                                if integralListView in self._GLIntegralLists.keys():
                                    integralListView.buildSymbols = True

                    if GLNotifier.GLINTEGRALLISTLABELS in triggers:

                        for spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            for integralListView in spectrumView.integralListViews:

                                if integralListView in self._GLIntegralLists.keys():
                                    integralListView.buildLabels = True

                    if GLNotifier.GLMULTIPLETLISTS in triggers:
                        for spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            for multipletListView in spectrumView.multipletListViews:
                                for multipletList in targets:
                                    if multipletList == multipletListView.multipletList:
                                        multipletListView.buildSymbols = True
                        # self.buildMultipletLists()

                    if GLNotifier.GLMULTIPLETLISTLABELS in triggers:
                        for spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            for multipletListView in spectrumView.multipletListViews:
                                for multipletList in targets:
                                    if multipletList == multipletListView.multipletList:
                                        multipletListView.buildLabels = True
                            # self.buildMultipletListLabels()

                        # for ils in self._GLIntegralLists.values():
                        #   if ils.integralListView.peakList in targets:
                        #     # ils.renderMode = GLRENDERMODE_REBUILD
                        #     ils.integralListView.buildPeakLists = True

                        # self._processPeakNotifier(targets)

                    if GLNotifier.GLCLEARPHASING in triggers:
                        if self.spectrumDisplay == aDict[GLNotifier.GLSPECTRUMDISPLAY]:
                            self.clearStaticTraces()

                    if GLNotifier.GLADD1DPHASING in triggers:
                        if self.spectrumDisplay == aDict[GLNotifier.GLSPECTRUMDISPLAY]:
                            self.clearStaticTraces()
                            self.newTrace()

        # repaint
        self.update()

    def _resetBoxes(self):
        """Reset/Hide the boxes
        """
        self._successiveClicks = None

    def _selectPeak(self, xPosition, yPosition):
        """(de-)Select first peak near cursor xPosition, yPosition
        if peak already was selected, de-select it
        """
        peaks = set(self.current.peaks)
        newPeaks = self._mouseInPeak(xPosition, yPosition)

        self.current.peaks = list(peaks ^ set(newPeaks))  # symmetric difference

    def _selectIntegral(self, xPosition, yPosition):
        """(de-)Select first integral near cursor xPosition, yPosition
        if integral already was selected, de-select it
        """
        integrals = set(self.current.integrals)
        newIntegrals = self._mouseInIntegral(xPosition, yPosition)

        self.current.integrals = list(integrals ^ set(newIntegrals))  # symmetric difference

    def _selectMultiplet(self, xPosition, yPosition):
        """(de-)Select first multiplet near cursor xPosition, yPosition
        if multiplet already was selected, de-select it
        """
        multiplets = set(self.current.multiplets)
        newMultiplets = self._mouseInMultiplet(xPosition, yPosition)

        self.current.multiplets = list(multiplets ^ set(newMultiplets))  # symmetric difference

    def _pickAtMousePosition(self, event):
        """pick the peaks at the mouse position
        """
        event.accept()
        self._resetBoxes()

        mousePosition = (self.cursorCoordinate[0], self.cursorCoordinate[1])
        position = [mousePosition[0], mousePosition[1]]
        for orderedAxis in self._orderedAxes[2:]:
            position.append(orderedAxis.position)

        newPeaks, peakLists = self.strip.peakPickPosition(position)

    def _clearIntegralRegions(self):
        """Clear the integral regions
        """
        self._regions = []
        self._regionList.renderMode = GLRENDERMODE_REBUILD
        self._dragRegions = set()
        self.update()

    def _mouseClickEvent(self, event: QtGui.QMouseEvent, axis=None):
        """handle the mouse click event
        """
        # self.current.strip = self.strip
        xPosition = self.cursorCoordinate[0]  # self.mapSceneToView(event.pos()).x()
        yPosition = self.cursorCoordinate[1]  # self.mapSceneToView(event.pos()).y()
        self.current.positions = [xPosition, yPosition]

        # This is the correct future style for cursorPosition handling
        self.current.cursorPosition = (xPosition, yPosition)

        if getCurrentMouseMode() == PICK:
            self._pickAtMousePosition(event)

        if controlShiftLeftMouse(event) or controlShiftRightMouse(event):
            # Control-Shift-left-click: pick peak
            self._pickAtMousePosition(event)

        elif controlLeftMouse(event):
            # Control-left-click; (de-)select peak and add/remove to selection
            event.accept()
            self._resetBoxes()
            self._selectMultiplet(xPosition, yPosition)
            self._selectPeak(xPosition, yPosition)
            self._selectIntegral(xPosition, yPosition)

        elif leftMouse(event):
            # Left-click; select peak/integral/multiplet, deselecting others
            event.accept()
            self._resetBoxes()
            self.current.clearPeaks()
            self.current.clearIntegrals()
            self.current.clearMultiplets()

            self._selectMultiplet(xPosition, yPosition)
            self._selectPeak(xPosition, yPosition)
            self._selectIntegral(xPosition, yPosition)

        elif shiftRightMouse(event):
            # Two successive shift-right-clicks: define zoombox
            event.accept()
            if self._successiveClicks is None:
                self._resetBoxes()
                self._successiveClicks = (self.cursorCoordinate[0], self.cursorCoordinate[1])
            else:

                if self._widthsChangedEnough((self.cursorCoordinate[0], self.cursorCoordinate[1]),
                                             (self._successiveClicks[0], self._successiveClicks[1]),
                                             3 * max(abs(self.pixelX),
                                                     abs(self.pixelY))):

                    if self.INVERTXAXIS:
                        self.axisL = max(self._startCoordinate[0], self._successiveClicks[0])
                        self.axisR = min(self._startCoordinate[0], self._successiveClicks[0])
                    else:
                        self.axisL = min(self._startCoordinate[0], self._successiveClicks[0])
                        self.axisR = max(self._startCoordinate[0], self._successiveClicks[0])

                    if self.INVERTYAXIS:
                        self.axisB = max(self._startCoordinate[1], self._successiveClicks[1])
                        self.axisT = min(self._startCoordinate[1], self._successiveClicks[1])
                    else:
                        self.axisB = min(self._startCoordinate[1], self._successiveClicks[1])
                        self.axisT = max(self._startCoordinate[1], self._successiveClicks[1])

                    self._testAxisLimits(setLimits=True)
                    self._rescaleXAxis()

                self._resetBoxes()
                self._successiveClicks = None

        elif rightMouse(event) and axis is None:
            # right click on canvas, not the axes
            strip = self.strip
            menu = None
            event.accept()
            self._resetBoxes()

            # Search if the event is in a range of a selected peak.
            peaks = list(self.current.peaks)
            strip._addItemsToNavigateToCursorPosMenu()
            strip._addItemsToMarkInCursorPosMenu()

            from ccpn.ui.gui.lib.GuiStripContextMenus import _hidePeaksSingleActionItems, _enableAllItems

            ii = strip._contextMenus.get(PeakMenu)
            if len(peaks) > 1:
                _hidePeaksSingleActionItems(strip, ii)
            else:
                _enableAllItems(ii)

            # will only work for self.current.peak
            strip._addItemsToNavigateToPeakMenu()
            strip._addItemsToMarkInPeakMenu()

            # check other menu items before raising menues
            strip._checkMenuItems()

            # set the correct rightMouseMenu for the clicked object (must be selected)
            if self._mouseInPeak(xPosition, yPosition, firstOnly=True):
                strip.contextMenuMode = PeakMenu
                menu = strip._contextMenus.get(strip.contextMenuMode)

            elif self._mouseInIntegral(xPosition, yPosition, firstOnly=True):
                strip.contextMenuMode = IntegralMenu
                menu = strip._contextMenus.get(strip.contextMenuMode)

            elif self._mouseInMultiplet(xPosition, yPosition, firstOnly=True):
                strip.contextMenuMode = MultipletMenu
                menu = strip._contextMenus.get(strip.contextMenuMode)

            if menu is not None:
                strip.viewStripMenu = menu
            else:
                strip.viewStripMenu = self._getCanvasContextMenu()
            strip._raiseContextMenu(event)


        elif controlRightMouse(event) and axis is None:
            # control-right-mouse click: reset the zoom
            event.accept()
            self._resetBoxes()
            self._resetAxisRange()
            self._rescaleXAxis(update=True)

        else:
            # reset and hide all for all other clicks
            self._resetBoxes()
            event.ignore()

        self.update()

    def _getCanvasContextMenu(self):
        """Give a needed menu based on strip mode
        """
        strip = self.strip
        menu = strip._contextMenus.get(DefaultMenu)

        # set the checkboxes to the correct settings
        strip.toolbarAction.setChecked(strip.spectrumDisplay.spectrumUtilToolBar.isVisible())
        strip.crosshairAction.setChecked(self._crosshairVisible)
        strip.gridAction.setChecked(self._gridVisible)
        if hasattr(strip, 'lastAxisOnlyCheckBox'):
            strip.lastAxisOnlyCheckBox.setChecked(strip.spectrumDisplay.lastAxisOnly)

        if strip._isPhasingOn:
            menu = strip._contextMenus.get(PhasingMenu)

        return menu

    def _setContextMenu(self, menu):
        """Set a needed menu based on strip mode
        """
        self.strip.viewStripMenu = menu

    def _selectPeaksInRegion(self, xPositions, yPositions, zPositions):
        currentPeaks = set(self.current.peaks)

        peaks = set()
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            for peakListView in spectrumView.peakListViews:
                if not peakListView.isVisible() or not spectrumView.isVisible():
                    continue

                peakList = peakListView.peakList
                if not isinstance(peakList, PeakList):  # it could be an IntegralList
                    continue

                if len(spectrumView.spectrum.axisCodes) == 1:

                    y0 = self._startCoordinate[1]
                    y1 = self._endCoordinate[1]
                    y0, y1 = min(y0, y1), max(y0, y1)
                    xAxis = 0

                    for peak in peakList.peaks:
                        height = peak.height  # * scale # TBD: is the scale already taken into account in peak.height???
                        if xPositions[0] < float(peak.position[xAxis]) < xPositions[1] and y0 < height < y1:
                            peaks.add(peak)

                else:
                    spectrumIndices = spectrumView._displayOrderSpectrumDimensionIndices
                    xAxis = spectrumIndices[0]
                    yAxis = spectrumIndices[1]

                    for peak in peakList.peaks:
                        if (xPositions[0] < float(peak.position[xAxis]) < xPositions[1]
                                and yPositions[0] < float(peak.position[yAxis]) < yPositions[1]):
                            if len(peak.axisCodes) > 2 and zPositions is not None:
                                zAxis = spectrumIndices[2]

                                # within the XY bounds so check whether inPlane
                                _isInPlane, _isInFlankingPlane, planeIndex, fade = self._GLPeaks.objIsInVisiblePlanes(spectrumView, peak)

                                # if zPositions[0] < float(peak.position[zAxis]) < zPositions[1]:
                                if _isInPlane:
                                    peaks.add(peak)
                            else:
                                peaks.add(peak)

        self.current.peaks = list(currentPeaks | peaks)

    def _selectMultipletsInRegion(self, xPositions, yPositions, zPositions):
        currentMultiplets = set(self.current.multiplets)

        multiplets = set()
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            for multipletListView in spectrumView.multipletListViews:
                if not multipletListView.isVisible() or not spectrumView.isVisible():
                    continue

                multipletList = multipletListView.multipletList

                if len(spectrumView.spectrum.axisCodes) == 1:

                    y0 = self._startCoordinate[1]
                    y1 = self._endCoordinate[1]
                    y0, y1 = min(y0, y1), max(y0, y1)
                    xAxis = 0

                    for multiplet in multipletList.multiplets:
                        if not multiplet.position:
                            continue

                        height = multiplet.height  # * scale # TBD: is the scale already taken into account in multiplet.height???
                        if xPositions[0] < float(multiplet.position[xAxis]) < xPositions[1] and y0 < height < y1:
                            multiplets.add(multiplet)

                else:
                    spectrumIndices = spectrumView._displayOrderSpectrumDimensionIndices
                    xAxis = spectrumIndices[0]
                    yAxis = spectrumIndices[1]

                    for multiplet in multipletList.multiplets:
                        if not multiplet.position:
                            continue

                        if (xPositions[0] < float(multiplet.position[xAxis]) < xPositions[1]
                                and yPositions[0] < float(multiplet.position[yAxis]) < yPositions[1]):
                            if len(multiplet.axisCodes) > 2 and zPositions is not None:
                                zAxis = spectrumIndices[2]

                                # within the XY bounds so check whether inPlane
                                _isInPlane, _isInFlankingPlane, planeIndex, fade = self._GLPeaks.objIsInVisiblePlanes(spectrumView, multiplet)

                                # if zPositions[0] < float(multiplet.position[zAxis]) < zPositions[1]:
                                if _isInPlane:
                                    multiplets.add(multiplet)
                            else:
                                multiplets.add(multiplet)

        self.current.multiplets = list(currentMultiplets | multiplets)

    def _mouseDragEvent(self, event: QtGui.QMouseEvent, axis=None):
        if controlShiftLeftMouse(event) or controlShiftRightMouse(event):
            # Control(Cmd)+shift+left drag: Peak-picking
            event.accept()

            self._resetBoxes()
            selectedRegion = [[round(self._startCoordinate[0], 3), round(self._endCoordinate[0], 3)],
                              [round(self._startCoordinate[1], 3), round(self._endCoordinate[1], 3)]]

            for n in self._orderedAxes[2:]:
                selectedRegion.append((n.region[0], n.region[1]))

            peaks = self.strip.peakPickRegion(selectedRegion)
            self.current.peaks = peaks

        elif controlLeftMouse(event):
            # Control(Cmd)+left drag: selects peaks - purple box
            event.accept()

            self._resetBoxes()
            xPositions = sorted([self._startCoordinate[0], self._endCoordinate[0]])
            yPositions = sorted([self._startCoordinate[1], self._endCoordinate[1]])

            if len(self._orderedAxes) > 2:
                zPositions = self._orderedAxes[2].region
            else:
                zPositions = None

            self._selectMultipletsInRegion(xPositions, yPositions, zPositions)
            self._selectPeaksInRegion(xPositions, yPositions, zPositions)

        elif middleMouse(event):
            # middle drag: moves a selected peak
            event.accept()

            peaks = list(self.current.peaks)
            if not peaks:
                return

            deltaPosition = [self.cursorCoordinate[0] - self._startCoordinate[0],
                             self.cursorCoordinate[1] - self._startCoordinate[1]]
            for peak in peaks:
                peak.startPosition = peak.position

            with undoBlock():
                for peak in peaks:
                    self._movePeak(peak, deltaPosition)

            self.current.peaks = peaks

        elif shiftLeftMouse(event):
            # zoom into the region - yellow box
            if self.INVERTXAXIS:
                self.axisL = max(self._startCoordinate[0], self._endCoordinate[0])
                self.axisR = min(self._startCoordinate[0], self._endCoordinate[0])
            else:
                self.axisL = min(self._startCoordinate[0], self._endCoordinate[0])
                self.axisR = max(self._startCoordinate[0], self._endCoordinate[0])

            if self.INVERTYAXIS:
                self.axisB = max(self._startCoordinate[1], self._endCoordinate[1])
                self.axisT = min(self._startCoordinate[1], self._endCoordinate[1])
            else:
                self.axisB = min(self._startCoordinate[1], self._endCoordinate[1])
                self.axisT = max(self._startCoordinate[1], self._endCoordinate[1])

            self._testAxisLimits(setLimits=True)
            self._resetBoxes()

            # this also rescales the peaks
            self._rescaleXAxis()

        elif shiftMiddleMouse(event) or shiftRightMouse(event):
            pass

        else:
            event.ignore()

        self.update()

    def _movePeak(self, peak, deltaPosition):
        # oldPosition = peak.position
        # orderedAxes = peak.orderedAxes

        # get the correct coordinates based on the axisCodes
        p0 = list(peak.position)  # [0.0] * 2            #len(self.axisOrder)
        axisCount = 0
        for ps, psCode in enumerate(self.axisOrder[:2]):  # display x, y
            for pp, ppCode in enumerate(peak.axisCodes):

                # if self._preferences.matchAxisCode == 0:  # default - match atom type, first letter
                if ppCode[0] == psCode[0]:
                    p0[pp] += deltaPosition[ps]
                    axisCount += 1

        if self.is1D:
            peak.height = peak.height + deltaPosition[1]
        peak.position = p0

    def exportToPDF(self, filename='default.pdf', params=None):
        return GLExporter(self, self.strip, filename, params)

    def exportToSVG(self, filename='default.svg', params=None):
        return GLExporter(self, self.strip, filename, params)

    def cohenSutherlandClip(self, x0, y0, x1, y1):
        """Implement Cohen-Sutherland clipping
        :param x0, y0 - co-ordinates of first point:
        :param x1, y1 - co-ordinates of second point:
        :return None if not clipped else (xs, ys, xe, ye) - start, end of clipped line
        """
        INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

        xMin = min([self.axisL, self.axisR])
        xMax = max([self.axisL, self.axisR])
        yMin = min([self.axisB, self.axisT])
        yMax = max([self.axisB, self.axisT])

        def computeCode(x, y):
            """calculate region that point lies in
            :param x, y - point:
            :return code:
            """
            code = INSIDE
            if x < xMin:  # to the left of rectangle
                code |= LEFT
            elif x > xMax:  # to the right of rectangle
                code |= RIGHT
            if y < yMin:  # below the rectangle
                code |= BOTTOM
            elif y > yMax:  # above the rectangle
                code |= TOP
            return code

        code1 = computeCode(x0, y0)
        code2 = computeCode(x1, y1)
        accept = False

        while not accept:

            # If both endpoints lie within rectangle
            if code1 == 0 and code2 == 0:
                accept = True

            # If both endpoints are outside rectangle
            elif (code1 & code2) != 0:
                return None

            # Some segment lies within the rectangle
            else:

                # Line Needs clipping
                # At least one of the points is outside,
                # select it
                x = 1.0
                y = 1.0
                if code1 != 0:
                    code_out = code1
                else:
                    code_out = code2

                # Find intersection point
                # using formulas y = y0 + slope * (x - x0),
                # x = x0 + (1 / slope) * (y - y0)
                if code_out & TOP:

                    # point is above the clip rectangle
                    x = x0 + (x1 - x0) * \
                        (yMax - y0) / (y1 - y0)
                    y = yMax

                elif code_out & BOTTOM:

                    # point is below the clip rectangle
                    x = x0 + (x1 - x0) * \
                        (yMin - y0) / (y1 - y0)
                    y = yMin

                elif code_out & RIGHT:

                    # point is to the right of the clip rectangle
                    y = y0 + (y1 - y0) * \
                        (xMax - x0) / (x1 - x0)
                    x = xMax

                elif code_out & LEFT:

                    # point is to the left of the clip rectangle
                    y = y0 + (y1 - y0) * \
                        (xMin - x0) / (x1 - x0)
                    x = xMin

                # Now intersection point x,y is found
                # We replace point outside clipping rectangle
                # by intersection point
                if code_out == code1:
                    x0 = x
                    y0 = y
                    code1 = computeCode(x0, y0)

                else:
                    x1 = x
                    y1 = y
                    code2 = computeCode(x1, y1)

        return [x0, y0, x1, y1]

    def pointVisible(self, lineList, x=0.0, y=0.0, width=0.0, height=0.0):
        """return true if the line has visible endpoints
        """
        if (self.between(lineList[0], self.axisL, self.axisR) and
                (self.between(lineList[1], self.axisT, self.axisB))):
            lineList[0] = x + width * (lineList[0] - self.axisL) / (self.axisR - self.axisL)
            lineList[1] = y + height * (lineList[1] - self.axisB) / (self.axisT - self.axisB)
            return True

    def lineVisible(self, lineList, x=0.0, y=0.0, width=0.0, height=0.0, checkIntegral=False):
        """return the list of visible lines
        """
        newLine = [[lineList[ll], lineList[ll + 1]] for ll in range(0, len(lineList), 2)]
        if len(newLine) > 2:
            newList = self.clipPoly(newLine)
        elif len(newLine) == 2:
            newList = self.clipLine(newLine)

        try:
            for pp in range(0, len(newList), 2):
                newList[pp] = x + width * (newList[pp] - self.axisL) / (self.axisR - self.axisL)
                newList[pp + 1] = y + height * (newList[pp + 1] - self.axisB) / (self.axisT - self.axisB)
        except Exception as es:
            pass

        return newList

    def clipPoly(self, subjectPolygon):
        """Apply Sutherland-Hodgman algorithm for clipping polygons
        """
        if self.INVERTXAXIS != self.INVERTYAXIS:
            clipPolygon = [[self.axisL, self.axisB],
                           [self.axisL, self.axisT],
                           [self.axisR, self.axisT],
                           [self.axisR, self.axisB]]
        else:
            clipPolygon = [[self.axisL, self.axisB],
                           [self.axisR, self.axisB],
                           [self.axisR, self.axisT],
                           [self.axisL, self.axisT]]

        def inside(p):
            return (cp2[0] - cp1[0]) * (p[1] - cp1[1]) > (cp2[1] - cp1[1]) * (p[0] - cp1[0])

        def computeIntersection():
            dc = [cp1[0] - cp2[0], cp1[1] - cp2[1]]
            dp = [s[0] - e[0], s[1] - e[1]]
            n1 = cp1[0] * cp2[1] - cp1[1] * cp2[0]
            n2 = s[0] * e[1] - s[1] * e[0]
            n3 = 1.0 / (dc[0] * dp[1] - dc[1] * dp[0])
            return [(n1 * dp[0] - n2 * dc[0]) * n3, (n1 * dp[1] - n2 * dc[1]) * n3]

        outputList = subjectPolygon
        cLen = len(clipPolygon)
        cp1 = clipPolygon[cLen - 1]

        for clipVertex in clipPolygon:
            cp2 = clipVertex
            inputList = outputList
            outputList = []
            if not inputList:
                break

            ilLen = len(inputList)
            s = inputList[ilLen - 1]

            for subjectVertex in inputList:
                e = subjectVertex
                if inside(e):
                    if not inside(s):
                        outputList.append(computeIntersection())
                    outputList.append(e)
                elif inside(s):
                    outputList.append(computeIntersection())
                s = e
            cp1 = cp2
        return [pp for ol in outputList for pp in ol]

    def clipLine(self, subjectPolygon):
        """Apply Sutherland-Hodgman algorithm for clipping polygons"""

        if self.INVERTXAXIS != self.INVERTYAXIS:
            clipPolygon = [[self.axisL, self.axisB],
                           [self.axisL, self.axisT],
                           [self.axisR, self.axisT],
                           [self.axisR, self.axisB]]
        else:
            clipPolygon = [[self.axisL, self.axisB],
                           [self.axisR, self.axisB],
                           [self.axisR, self.axisT],
                           [self.axisL, self.axisT]]

        def inside(p):
            return (cp2[0] - cp1[0]) * (p[1] - cp1[1]) > (cp2[1] - cp1[1]) * (p[0] - cp1[0])

        def computeIntersection():
            dc = [cp1[0] - cp2[0], cp1[1] - cp2[1]]
            dp = [s[0] - e[0], s[1] - e[1]]
            n1 = cp1[0] * cp2[1] - cp1[1] * cp2[0]
            n2 = s[0] * e[1] - s[1] * e[0]
            n3 = 1.0 / (dc[0] * dp[1] - dc[1] * dp[0])
            return [(n1 * dp[0] - n2 * dc[0]) * n3, (n1 * dp[1] - n2 * dc[1]) * n3]

        outputList = subjectPolygon
        cLen = len(clipPolygon)
        cp1 = clipPolygon[cLen - 1]

        for clipVertex in clipPolygon:
            cp2 = clipVertex
            inputList = outputList
            outputList = []
            if not inputList:
                break

            ilLen = len(inputList)
            s = inputList[ilLen - 1]
            e = inputList[0]
            if inside(e):
                outputList.append(e)
                if inside(s):
                    outputList.append(s)
                else:
                    outputList.append(computeIntersection())
            elif inside(s):
                outputList.append(s)
                outputList.append(computeIntersection())
            cp1 = cp2
        return [pp for ol in outputList for pp in ol]

    def lineFit(self, lineList, x=0.0, y=0.0, width=0.0, height=0.0, checkIntegral=False):
        for pp in range(0, len(lineList), 2):
            if (self.between(lineList[pp], self.axisL, self.axisR) and
                    (self.between(lineList[pp + 1], self.axisT, self.axisB) or checkIntegral)):
                fit = True
                break
        else:
            fit = False

        for pp in range(0, len(lineList), 2):
            lineList[pp] = x + width * (lineList[pp] - self.axisL) / (self.axisR - self.axisL)
            lineList[pp + 1] = y + height * (lineList[pp + 1] - self.axisB) / (self.axisT - self.axisB)
        return fit


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# need to use the class below to make everything more generic
GLOptions = {
    'opaque'     : {
        GL.GL_DEPTH_TEST: True,
        GL.GL_BLEND     : False,
        GL.GL_ALPHA_TEST: False,
        GL.GL_CULL_FACE : False,
        },
    'translucent': {
        GL.GL_DEPTH_TEST: True,
        GL.GL_BLEND     : True,
        GL.GL_ALPHA_TEST: False,
        GL.GL_CULL_FACE : False,
        'glBlendFunc'   : (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA),
        },
    'additive'   : {
        GL.GL_DEPTH_TEST: False,
        GL.GL_BLEND     : True,
        GL.GL_ALPHA_TEST: False,
        GL.GL_CULL_FACE : False,
        'glBlendFunc'   : (GL.GL_SRC_ALPHA, GL.GL_ONE),
        },
    }


class CcpnTransform3D(QtGui.QMatrix4x4):
    """
  Extension of QMatrix4x4 with some helpful methods added.
  """

    def __init__(self, *args):
        QtGui.QMatrix4x4.__init__(self, *args)

    def matrix(self, nd=3):
        if nd == 3:
            return np.array(self.copyDataTo()).reshape(4, 4)
        elif nd == 2:
            m = np.array(self.copyDataTo()).reshape(4, 4)
            m[2] = m[3]
            m[:, 2] = m[:, 3]
            return m[:3, :3]
        else:
            raise Exception("Argument 'nd' must be 2 or 3")

    def map(self, obj):
        """
    Extends QMatrix4x4.map() to allow mapping (3, ...) arrays of coordinates
    """
        if isinstance(obj, np.ndarray) and obj.ndim >= 2 and obj.shape[0] in (2, 3):
            return fn.transformCoordinates(self, obj)
        else:
            return QtGui.QMatrix4x4.map(self, obj)

    def inverted(self):
        inv, b = QtGui.QMatrix4x4.inverted(self)
        return CcpnTransform3D(inv), b


class CcpnGLItem():
    _nextId = 0

    def __init__(self, parentItem=None):
        self._id = CcpnGLItem._nextId
        CcpnGLItem._nextId += 1

        self.strip = None
        self._view = None
        self._children = set()
        self._transform = CcpnTransform3D()
        self._visible = True
        # self.setParentItem(parentItem)
        # self.setDepthValue(0)
        self._glOpts = {}


vertex_data = np.array([0.75, 0.75, 0.0,
                        0.75, -0.75, 0.0,
                        -0.75, -0.75, 0.0], dtype=np.float32)

color_data = np.array([1, 0, 0,
                       0, 1, 0,
                       0, 0, 1], dtype=np.float32)
