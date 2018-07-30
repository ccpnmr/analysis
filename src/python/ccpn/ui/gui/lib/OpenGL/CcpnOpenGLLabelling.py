"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
                 "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import math
from threading import Thread
# from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets
# from PyQt5.QtCore import QPoint, QSize, Qt, pyqtSlot
# from PyQt5.QtWidgets import QApplication, QOpenGLWidget
from ccpn.util.Logging import getLogger
import numpy as np
# from pyqtgraph import functions as fn
# from ccpn.core.PeakList import PeakList
# from ccpn.core.IntegralList import IntegralList
# from ccpn.ui.gui.lib.mouseEvents import getCurrentMouseMode
# from ccpn.ui.gui.lib.GuiStrip import DefaultMenu, PeakMenu, MultipletMenu, PhasingMenu

from ccpn.util.Colour import getAutoColourRgbRatio
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_BACKGROUND, CCPNGLWIDGET_FOREGROUND, CCPNGLWIDGET_PICKCOLOUR, \
    CCPNGLWIDGET_GRID, CCPNGLWIDGET_HIGHLIGHT, CCPNGLWIDGET_INTEGRALSHADE, \
    CCPNGLWIDGET_LABELLING, CCPNGLWIDGET_PHASETRACE, getColours
from ccpn.ui.gui.lib.GuiPeakListView import _getScreenPeakAnnotation, _getPeakAnnotation
# import ccpn.util.Phasing as Phasing
# from ccpn.ui.gui.lib.mouseEvents import \
#     leftMouse, shiftLeftMouse, controlLeftMouse, controlShiftLeftMouse, \
#     middleMouse, shiftMiddleMouse, rightMouse, shiftRightMouse, controlRightMouse, PICK
from ccpn.core.lib.Notifiers import Notifier
# from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLNotifier import GLNotifier
# from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import GLGlobalData
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import GLString
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLRENDERMODE_IGNORE, GLRENDERMODE_DRAW, \
    GLRENDERMODE_RESCALE, GLRENDERMODE_REBUILD, \
    GLREFRESHMODE_NEVER, GLREFRESHMODE_ALWAYS, \
    GLREFRESHMODE_REBUILD, GLVertexArray, \
    GLPeakLabelsArray, GLPeakListArray
# from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLViewports import GLViewports
# from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLWidgets import GLIntegralRegion, GLExternalRegion, \
#     GLRegion, REGION_COLOURS
# from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLExport import GLExporter
import ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs as GLDefs
# from ccpn.util.Common import makeIterableList
# from ccpn.util.Constants import AXIS_FULLATOMNAME, AXIS_MATCHATOMTYPE


try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)


class GLLabelling():
    """Class to handle symbol and symbol labelling
    """
    def __init__(self, parent=None, strip=None, name=None, resizeGL=False,
                 symbolDict=None, labelDict=None, objectList=None):
        self._GLParent = parent
        self.strip = strip
        self.name = name
        self.resizeGL = resizeGL
        # self.globalGL = parent.globalGL
        # self.symbolDict = symbolDict
        # self.labelict = labelDict
        self.objectList = objectList
        self._threads = {}
        self._threadupdate = False
        self.current = self.strip.current

        self._GLSymbolItems = {}        #symbolDict
        self._GLSymbolLabels = {}       #labelDict

    def _isSelected(self, peak):
        """return True if the obj in the defined object list
        """
        if self.current.peaks:
            return peak in self.current.peaks

    def rescale(self):
        if self.resizeGL:
            for pp in self._GLSymbolItems.values():
                pp.renderMode = GLRENDERMODE_RESCALE

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Handle notifiers
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _deletePeakListItem(self, peak):
        pls = peak.peakList
        if pls:
            spectrum = pls.spectrum

            for peakListView in pls.peakListViews:
                if peakListView in self._GLSymbolItems.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self.strip.spectrumViews:
                            self._removePeakListItem(spectrumView, peakListView, peak)
                            self._updateHighlightedSymbols(spectrumView, peakListView)

    def _createPeakListItem(self, peak):
        pls = peak.peakList
        if pls:
            spectrum = pls.spectrum

            for peakListView in pls.peakListViews:
                if peakListView in self._GLSymbolItems.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self.strip.spectrumViews:
                            self._appendPeakListItem(spectrumView, peakListView, peak)
                            self._updateHighlightedSymbols(spectrumView, peakListView)

    def _changePeakListLabel(self, peak):
        self._deletePeakListLabel(peak)
        self._createPeakListLabel(peak)

    def _changePeakListItem(self, peak):
        pls = peak.peakList
        if pls:
            spectrum = pls.spectrum

            for peakListView in pls.peakListViews:
                if peakListView in self._GLSymbolLabels.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self.strip.spectrumViews:
                            self._removePeakListItem(spectrumView, peakListView, peak)
                            self._appendPeakListItem(spectrumView, peakListView, peak)
                            self._updateHighlightedSymbols(spectrumView, peakListView)

    def _deletePeakListLabel(self, peak):
        for pll in self._GLSymbolLabels.keys():
            drawList = self._GLSymbolLabels[pll]

            for drawStr in drawList.stringList:
                if drawStr.object == peak:
                    drawList.stringList.remove(drawStr)
                    break

    def _createPeakListLabel(self, peak):
        pls = peak.peakList
        if pls:
            spectrum = pls.spectrum

            for peakListView in pls.peakListViews:
                if peakListView in self._GLSymbolLabels.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self.strip.spectrumViews:
                            drawList = self._GLSymbolLabels[peakListView]
                            self._appendPeakListLabel(spectrumView, peakListView, drawList.stringList, peak)
                            self._rescalePeakListLabels(spectrumView, peakListView, drawList)

    def _processNotifier(self, data):
        """process notifiers
        """
        triggers = data[Notifier.TRIGGER]
        peak = data[Notifier.OBJECT]

        if Notifier.DELETE in triggers:
            self._deletePeakListItem(peak)
            self._deletePeakListLabel(peak)

        if Notifier.CREATE in triggers:
            self._createPeakListItem(peak)
            self._createPeakListLabel(peak)

        if Notifier.CHANGE in triggers:
            self._changePeakListItem(peak)
            self._changePeakListLabel(peak)

    def _appendPeakListLabel(self, spectrumView, peakListView, stringList, peak):
        # get the correct coordinates based on the axisCodes

        spectrum = spectrumView.spectrum
        spectrumFrequency = spectrum.spectrometerFrequencies
        pls = peakListView.peakList

        symbolWidth = self.strip.peakSymbolSize / 2.0

        p0 = [0.0] * 2  # len(self.axisOrder)
        lineWidths = [None] * 2  # len(self.axisOrder)
        frequency = [0.0] * 2  # len(self.axisOrder)
        axisCount = 0
        for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
            for pp, ppCode in enumerate(peak.axisCodes):

                if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                    if ppCode[0] == psCode[0]:
                        p0[ps] = peak.position[pp]
                        lineWidths[ps] = peak.lineWidths[pp]
                        frequency[ps] = spectrumFrequency[pp]
                        axisCount += 1

                elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                    if ppCode == psCode:
                        p0[ps] = peak.position[pp]
                        lineWidths[ps] = peak.lineWidths[pp]
                        frequency[ps] = spectrumFrequency[pp]
                        axisCount += 1

        if lineWidths[0] and lineWidths[1]:
            # draw 24 connected segments
            r = 0.5 * lineWidths[0] / frequency[0]
            w = 0.5 * lineWidths[1] / frequency[1]
        else:
            r = symbolWidth
            w = symbolWidth

        if axisCount == 2:
            # TODO:ED display the required peaks
            strip = spectrumView.strip
            _isInPlane = strip.peakIsInPlane(peak)
            if not _isInPlane:
                _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
                fade = GLDefs.FADE_FACTOR
            else:
                _isInFlankingPlane = None
                fade = 1.0

            if not _isInPlane and not _isInFlankingPlane:
                return

            if self._isSelected(peak):
                listCol = self._GLParent.highlightColour[:3]
            else:
                listCol = getAutoColourRgbRatio(pls.textColour, pls.spectrum, self._GLParent.SPECTRUMPOSCOLOUR,
                                                getColours()[CCPNGLWIDGET_FOREGROUND])

            if self.strip.peakLabelling == 0:
                text = _getScreenPeakAnnotation(peak, useShortCode=True)
            elif self.strip.peakLabelling == 1:
                text = _getScreenPeakAnnotation(peak, useShortCode=False)
            else:
                text = _getPeakAnnotation(peak)  # original 'pid'

            # TODO:ED check axisCodes and ordering
            stringList.append(GLString(text=text,
                                       font=self._GLParent.globalGL.glSmallFont if _isInPlane else self._GLParent.globalGL.glSmallTransparentFont,
                                       x=p0[0], y=p0[1],
                                       ox=r, oy=w,
                                       # x=self._screenZero[0], y=self._screenZero[1]
                                       color=(*listCol, fade), GLContext=self._GLParent,
                                       obj=peak))

    def _removePeakListItem(self, spectrumView, peakListView, delPeak):
        symbolType = self.strip.peakSymbolType

        drawList = self._GLSymbolItems[peakListView]

        index = 0
        indexOffset = 0
        numPoints = 0

        pp = 0
        while (pp < len(drawList.pids)):
            # check whether the peaks still exists
            peak = drawList.pids[pp]

            if peak == delPeak:
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                if symbolType != 0:
                    numPoints = 2 * numPoints + 5

                # _isInPlane = drawList.pids[pp + 3]
                # _isInFlankingPlane = drawList.pids[pp + 4]
                # _isSelected = drawList.pids[pp + 5]
                indexStart = drawList.pids[pp + 6]
                indexEnd = drawList.pids[pp + 7]
                indexOffset = indexEnd - indexStart

                drawList.indices = np.delete(drawList.indices, np.s_[indexStart:indexEnd])
                drawList.vertices = np.delete(drawList.vertices, np.s_[2 * offset:2 * (offset + numPoints)])
                drawList.attribs = np.delete(drawList.attribs, np.s_[2 * offset:2 * (offset + numPoints)])
                drawList.colors = np.delete(drawList.colors, np.s_[4 * offset:4 * (offset + numPoints)])
                drawList.pids = np.delete(drawList.pids, np.s_[pp:pp + GLDefs.LENPID])
                drawList.numVertices -= numPoints
                break
            else:
                pp += GLDefs.LENPID

        # clean up the rest of the list
        while (pp < len(drawList.pids)):
            drawList.pids[pp + 1] -= numPoints
            drawList.pids[pp + 6] -= indexOffset
            drawList.pids[pp + 7] -= indexOffset
            pp += GLDefs.LENPID

    def _appendPeakListItem(self, spectrumView, peakListView, peak):
        spectrum = spectrumView.spectrum
        drawList = self._GLSymbolItems[peakListView]

        # find the correct scale to draw square pixels
        # don't forget to change when the axes change

        symbolType = self.strip.peakSymbolType
        symbolWidth = self.strip.peakSymbolSize / 2.0
        lineThickness = self.strip.peakSymbolThickness / 2.0

        x = abs(self._GLParent.pixelX)
        y = abs(self._GLParent.pixelY)
        # fix the aspect ratio of the cross to match the screen
        minIndex = 0 if x <= y else 1
        # pos = [symbolWidth, symbolWidth * y / x]
        # w = r = pos[minIndex]

        if x <= y:
            r = symbolWidth
            w = symbolWidth * y / x
        else:
            w = symbolWidth
            r = symbolWidth * x / y

        if symbolType == 0:  # a cross

            # change the ratio on resize
            drawList.refreshMode = GLREFRESHMODE_REBUILD
            drawList.drawMode = GL.GL_LINES
            drawList.fillMode = None

        elif symbolType == 1:  # draw an ellipse at lineWidth

            # fix the size to the axes
            drawList.refreshMode = GLREFRESHMODE_NEVER
            drawList.drawMode = GL.GL_LINES
            drawList.fillMode = None

        elif symbolType == 2:  # draw a filled ellipse at lineWidth

            # fix the size to the axes
            drawList.refreshMode = GLREFRESHMODE_NEVER
            drawList.drawMode = GL.GL_TRIANGLES
            drawList.fillMode = GL.GL_FILL

        # build the peaks VBO
        index = 0
        indexPtr = len(drawList.indices)

        # for pls in spectrum.peakLists:

        pls = peakListView.peakList
        spectrumFrequency = spectrum.spectrometerFrequencies

        strip = spectrumView.strip
        _isInPlane = strip.peakIsInPlane(peak)
        if not _isInPlane:
            _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
            fade = GLDefs.FADE_FACTOR
        else:
            _isInFlankingPlane = None
            fade = 1.0

        # ignore if not visible
        if not _isInPlane and not _isInFlankingPlane:
            return

        if self._isSelected(peak):
            listCol = self._GLParent.highlightColour[:3]
        else:
            listCol = getAutoColourRgbRatio(pls.textColour, pls.spectrum, self._GLParent.SPECTRUMPOSCOLOUR,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])

        # get the correct coordinates based on the axisCodes
        p0 = [0.0] * 2  # len(self.axisOrder)
        lineWidths = [None] * 2  # len(self.axisOrder)
        frequency = [0.0] * 2  # len(self.axisOrder)
        axisCount = 0
        for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
            for pp, ppCode in enumerate(peak.axisCodes):

                if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                    if ppCode[0] == psCode[0]:
                        p0[ps] = peak.position[pp]
                        lineWidths[ps] = peak.lineWidths[pp]
                        frequency[ps] = spectrumFrequency[pp]
                        axisCount += 1

                elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                    if ppCode == psCode:
                        p0[ps] = peak.position[pp]
                        lineWidths[ps] = peak.lineWidths[pp]
                        frequency[ps] = spectrumFrequency[pp]
                        axisCount += 1

        if axisCount != 2:
            getLogger().debug('Bad peak.axisCodes: %s - %s' % (peak.pid, peak.axisCodes))
        else:
            if symbolType == 0:

                # draw a cross
                # keep the cross square at 0.1ppm

                _isSelected = False
                # unselected
                if _isInPlane or _isInFlankingPlane:
                    drawList.indices = np.append(drawList.indices, [index, index + 1, index + 2, index + 3])

                    if self._isSelected(peak):
                        # if hasattr(peak, '_isSelected') and peak._isSelected:
                        _isSelected = True
                        drawList.indices = np.append(drawList.indices, [index, index + 2, index + 2, index + 1,
                                                                        index, index + 3, index + 3, index + 1])

                drawList.vertices = np.append(drawList.vertices, [p0[0] - r, p0[1] - w,
                                                                  p0[0] + r, p0[1] + w,
                                                                  p0[0] + r, p0[1] - w,
                                                                  p0[0] - r, p0[1] + w])
                drawList.colors = np.append(drawList.colors, [*listCol, fade] * 4)
                drawList.attribs = np.append(drawList.attribs, [p0[0], p0[1],
                                                                p0[0], p0[1],
                                                                p0[0], p0[1],
                                                                p0[0], p0[1]])

                # keep a pointer to the peak
                drawList.pids = np.append(drawList.pids, [peak, drawList.numVertices, 4,
                                                          _isInPlane, _isInFlankingPlane, _isSelected,
                                                          indexPtr, len(drawList.indices)])

                index += 4
                drawList.numVertices += 4

            elif symbolType == 1:  # draw an ellipse at lineWidth

                if lineWidths[0] and lineWidths[1]:
                    # draw 24 connected segments
                    r = 0.5 * lineWidths[0] / frequency[0]
                    w = 0.5 * lineWidths[1] / frequency[1]
                    numPoints = 24
                    angPlus = 2 * np.pi
                    skip = 1
                else:
                    # draw 12 disconnected segments (dotted)
                    # r = symbolWidth
                    # w = symbolWidth
                    numPoints = 12
                    angPlus = 1.0 * np.pi
                    skip = 2

                np2 = 2 * numPoints
                ang = list(range(numPoints))
                _isSelected = False

                if _isInPlane or _isInFlankingPlane:
                    drawList.indices = np.append(drawList.indices,
                                                 [[index + (2 * an), index + (2 * an) + 1] for an in ang])

                    if self._isSelected(peak):
                        _isSelected = True
                        drawList.indices = np.append(drawList.indices, [index + np2, index + np2 + 2,
                                                                        index + np2 + 2, index + np2 + 1,
                                                                        index + np2, index + np2 + 3,
                                                                        index + np2 + 3, index + np2 + 1])

                # draw an ellipse at lineWidth
                drawList.vertices = np.append(drawList.vertices, [[p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                   p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                   p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                                   p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints)]
                                                                  for an in ang])
                drawList.vertices = np.append(drawList.vertices, [p0[0] - r, p0[1] - w,
                                                                  p0[0] + r, p0[1] + w,
                                                                  p0[0] + r, p0[1] - w,
                                                                  p0[0] - r, p0[1] + w,
                                                                  p0[0], p0[1]])

                drawList.colors = np.append(drawList.colors, [*listCol, fade] * (np2 + 5))
                drawList.attribs = np.append(drawList.attribs, [p0[0], p0[1]] * (np2 + 5))
                drawList.offsets = np.append(drawList.offsets, [p0[0], p0[1]] * (np2 + 5))
                drawList.lineWidths = (r, w)

                # keep a pointer to the peak
                drawList.pids = np.append(drawList.pids, [peak, drawList.numVertices, numPoints,
                                                          _isInPlane, _isInFlankingPlane, _isSelected,
                                                          indexPtr, len(drawList.indices)])

                index += np2 + 5
                drawList.numVertices += np2 + 5

            elif symbolType == 2:  # draw a filled ellipse at lineWidth

                if lineWidths[0] and lineWidths[1]:
                    # draw 24 connected segments
                    r = 0.5 * lineWidths[0] / frequency[0]
                    w = 0.5 * lineWidths[1] / frequency[1]
                    numPoints = 24
                    angPlus = 2 * np.pi
                    skip = 1
                else:
                    # draw 12 disconnected segments (dotted)
                    # r = symbolWidth
                    # w = symbolWidth
                    numPoints = 12
                    angPlus = 1.0 * np.pi
                    skip = 2

                np2 = 2 * numPoints
                ang = list(range(numPoints))
                _isSelected = False

                if _isInPlane or _isInFlankingPlane:
                    drawList.indices = np.append(drawList.indices,
                                                 [[index + (2 * an), index + (2 * an) + 1, index + np2 + 4] for an in
                                                  ang])

                # draw an ellipse at lineWidth
                drawList.vertices = np.append(drawList.vertices, [[p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                   p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                   p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                                   p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints)]
                                                                  for an in ang])
                drawList.vertices = np.append(drawList.vertices, [p0[0] - r, p0[1] - w,
                                                                  p0[0] + r, p0[1] + w,
                                                                  p0[0] + r, p0[1] - w,
                                                                  p0[0] - r, p0[1] + w,
                                                                  p0[0], p0[1]])

                drawList.colors = np.append(drawList.colors, [*listCol, fade] * (np2 + 5))
                drawList.attribs = np.append(drawList.attribs, [p0[0], p0[1]] * (np2 + 5))
                drawList.offsets = np.append(drawList.offsets, [p0[0], p0[1]] * (np2 + 5))
                drawList.lineWidths = (r, w)

                # keep a pointer to the peak
                drawList.pids = np.append(drawList.pids, [peak, drawList.numVertices, numPoints,
                                                          _isInPlane, _isInFlankingPlane, _isSelected,
                                                          indexPtr, len(drawList.indices)])

                index += np2 + 5
                drawList.numVertices += np2 + 5

    def _updateHighlightedLabels(self, spectrumView, peakListView):
        drawList = self._GLSymbolLabels[peakListView]
        strip = self.strip

        pls = peakListView.peakList
        listCol = getAutoColourRgbRatio(pls.textColour, pls.spectrum, self._GLParent.SPECTRUMPOSCOLOUR,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])

        for drawStr in drawList.stringList:

            peak = drawStr.object

            if peak and not peak.isDeleted:
                # _isSelected = False
                _isInPlane = strip.peakIsInPlane(peak)
                if not _isInPlane:
                    _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
                    fade = GLDefs.FADE_FACTOR
                else:
                    _isInFlankingPlane = None
                    fade = 1.0

                if _isInPlane or _isInFlankingPlane:

                    if self._isSelected(peak):
                        drawStr.setColour((*self._GLParent.highlightColour[:3], fade))
                    else:
                        drawStr.setColour((*listCol, fade))

    def updateHighlightSymbols(self):
        """Respond to an update highlight notifier and update the highlighted symbols/labels
        """
        for spectrumView in self.strip.spectrumViews:
            for peakListView in spectrumView.peakListViews:

                if peakListView in self._GLSymbolItems.keys():
                    self._updateHighlightedSymbols(spectrumView, peakListView)
                    self._updateHighlightedLabels(spectrumView, peakListView)

    def updateAllSymbols(self):
        """Respond to update all notifier
        """
        for spectrumView in self.strip.spectrumViews:
            for peakListView in spectrumView.peakListViews:

                if peakListView in self._GLSymbolItems.keys():
                    peakListView.buildPeakLists = True
                    peakListView.buildPeakListLabels = True

    def _updateHighlightedSymbols(self, spectrumView, peakListView):
        """update the highlighted symbols
        """
        spectrum = spectrumView.spectrum
        strip = self.strip

        symbolType = strip.peakSymbolType
        symbolWidth = strip.peakSymbolSize / 2.0
        lineThickness = strip.peakSymbolThickness / 2.0

        drawList = self._GLSymbolItems[peakListView]
        drawList.indices = np.empty(0, dtype=np.uint)

        index = 0
        indexPtr = 0

        pls = peakListView.peakList
        listCol = getAutoColourRgbRatio(pls.symbolColour, pls.spectrum, self._GLParent.SPECTRUMPOSCOLOUR,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])

        if symbolType == 0:
            # for peak in pls.peaks:
            for pp in range(0, len(drawList.pids), GLDefs.LENPID):

                # check whether the peaks still exists
                peak = drawList.pids[pp]
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                if not peak.isDeleted:
                    _isSelected = False
                    _isInPlane = strip.peakIsInPlane(peak)
                    if not _isInPlane:
                        _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
                        fade = GLDefs.FADE_FACTOR
                    else:
                        _isInFlankingPlane = None
                        fade = 1.0

                    if _isInPlane or _isInFlankingPlane:
                        if self._isSelected(peak):
                            _isSelected = True
                            cols = self._GLParent.highlightColour[:3]
                            drawList.indices = np.append(drawList.indices,
                                                         np.array([index, index + 1, index + 2, index + 3,
                                                                   index, index + 2, index + 2, index + 1,
                                                                   index, index + 3, index + 3, index + 1],
                                                                  dtype=np.uint))
                        else:
                            cols = listCol

                            drawList.indices = np.append(drawList.indices,
                                                         np.array([index, index + 1, index + 2, index + 3],
                                                                  dtype=np.uint))
                        drawList.colors[offset * 4:(offset + numPoints) * 4] = [*cols, fade] * numPoints

                    # list MAY contain out of plane peaks
                    drawList.pids[pp + 3:pp + 8] = [_isInPlane, _isInFlankingPlane, _isSelected,
                                                    indexPtr, len(drawList.indices)]
                    indexPtr = len(drawList.indices)

                index += numPoints

        elif symbolType == 1:

            # for peak in pls.peaks:
            for pp in range(0, len(drawList.pids), GLDefs.LENPID):

                # check whether the peaks still exists
                peak = drawList.pids[pp]
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]
                np2 = 2 * numPoints

                if not peak.isDeleted:
                    ang = list(range(numPoints))

                    _isSelected = False
                    _isInPlane = strip.peakIsInPlane(peak)
                    if not _isInPlane:
                        _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
                        fade = GLDefs.FADE_FACTOR
                    else:
                        _isInFlankingPlane = None
                        fade = 1.0

                    if _isInPlane or _isInFlankingPlane:
                        drawList.indices = np.append(drawList.indices,
                                                     [[index + (2 * an), index + (2 * an) + 1] for an in ang])
                        if self._isSelected(peak):
                            _isSelected = True
                            cols = self._GLParent.highlightColour[:3]
                            drawList.indices = np.append(drawList.indices, [index + np2, index + np2 + 2,
                                                                            index + np2 + 2, index + np2 + 1,
                                                                            index + np2, index + np2 + 3,
                                                                            index + np2 + 3, index + np2 + 1])
                        else:
                            cols = listCol

                        drawList.colors[offset * 4:(offset + np2 + 5) * 4] = [*cols, fade] * (np2 + 5)

                    drawList.pids[pp + 3:pp + 8] = [_isInPlane, _isInFlankingPlane, _isSelected,
                                                    indexPtr, len(drawList.indices)]
                    indexPtr = len(drawList.indices)

                index += np2 + 5

        elif symbolType == 2:

            # for peak in pls.peaks:
            for pp in range(0, len(drawList.pids), GLDefs.LENPID):

                # check whether the peaks still exists
                peak = drawList.pids[pp]
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]
                np2 = 2 * numPoints

                if not peak.isDeleted:
                    ang = list(range(numPoints))

                    _isSelected = False
                    _isInPlane = strip.peakIsInPlane(peak)
                    if not _isInPlane:
                        _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
                        fade = GLDefs.FADE_FACTOR
                    else:
                        _isInFlankingPlane = None
                        fade = 1.0

                    if _isInPlane or _isInFlankingPlane:
                        drawList.indices = np.append(drawList.indices,
                                                     [[index + (2 * an), index + (2 * an) + 1, index + np2 + 4] for an
                                                      in ang])
                        if self._isSelected(peak):
                            _isSelected = True
                            cols = self._GLParent.highlightColour[:3]
                        else:
                            cols = listCol

                        drawList.colors[offset * 4:(offset + np2 + 5) * 4] = [*cols, fade] * (np2 + 5)

                    drawList.pids[pp + 3:pp + 8] = [_isInPlane, _isInFlankingPlane, _isSelected,
                                                    indexPtr, len(drawList.indices)]
                    indexPtr = len(drawList.indices)

                index += np2 + 5

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Rescaling
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _rescalePeakList(self, spectrumView, peakListView):
        """rescale symbols when the screen dimensions change
        """
        drawList = self._GLSymbolItems[peakListView]

        # if drawList.refreshMode == GLREFRESHMODE_REBUILD:

        symbolType = self.strip.peakSymbolType
        symbolWidth = self.strip.peakSymbolSize / 2.0
        x = abs(self._GLParent.pixelX)
        y = abs(self._GLParent.pixelY)

        # fix the aspect ratio of the cross to match the screen
        minIndex = 0 if x <= y else 1
        # pos = [symbolWidth, symbolWidth * y / x]
        # w = r = pos[minIndex]

        if x <= y:
            r = symbolWidth
            w = symbolWidth * y / x
        else:
            w = symbolWidth
            r = symbolWidth * x / y

        if symbolType == 0:  # a cross
            # drawList.clearVertices()
            # drawList.vertices.copy(drawList.attribs)
            offsets = np.array([-r, -w, +r, +w, +r, -w, -r, +w], np.float32)
            for pp in range(0, 2 * drawList.numVertices, 8):
                drawList.vertices[pp:pp + 8] = drawList.attribs[pp:pp + 8] + offsets

        elif symbolType == 1:  # an ellipse
            numPoints = 12
            angPlus = 1.0 * np.pi
            skip = 2

            np2 = 2 * numPoints
            ang = list(range(numPoints))

            offsets = np.empty(56)
            for an in ang:
                offsets[4 * an:4 * an + 4] = [- r * math.sin(skip * an * angPlus / numPoints),
                                              - w * math.cos(skip * an * angPlus / numPoints),
                                              - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                              - w * math.cos((skip * an + 1) * angPlus / numPoints)]
                offsets[48:56] = [-r, -w, +r, +w, +r, -w, -r, +w]

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):
                if drawList.pids[pp + 2] == 12:
                    index = 2 * drawList.pids[pp + 1]
                    drawList.vertices[index:index + 56] = drawList.attribs[index:index + 56] + offsets

        elif symbolType == 2:  # filled ellipse
            numPoints = 12
            angPlus = 1.0 * np.pi
            skip = 2

            np2 = 2 * numPoints
            ang = list(range(numPoints))

            offsets = np.empty(48)
            for an in ang:
                offsets[4 * an:4 * an + 4] = [- r * math.sin(skip * an * angPlus / numPoints),
                                              - w * math.cos(skip * an * angPlus / numPoints),
                                              - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                              - w * math.cos((skip * an + 1) * angPlus / numPoints)]

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):
                if drawList.pids[pp + 2] == 12:
                    index = 2 * drawList.pids[pp + 1]
                    drawList.vertices[index:index + 48] = drawList.attribs[index:index + 48] + offsets

    def _rescalePeakListLabels(self, spectrumView=None, peakListView=None, drawList=None):
        # drawList = self._GLSymbolLabels[peakListView]
        # strip = self._parent

        # pls = peakListView.peakList
        symbolType = self.strip.peakSymbolType
        symbolWidth = self.strip.peakSymbolSize / 2.0
        x = abs(self._GLParent.pixelX)
        y = abs(self._GLParent.pixelY)

        if symbolType == 0:  # a cross
            # fix the aspect ratio of the cross to match the screen
            # minIndex = 0 if x <= y else 1
            # pos = [symbolWidth, symbolWidth * y / x]

            if x <= y:
                r = symbolWidth
                w = symbolWidth * y / x
            else:
                w = symbolWidth
                r = symbolWidth * x / y

            for drawStr in drawList.stringList:
                drawStr.setStringOffset((r * np.sign(self._GLParent.pixelX), w * np.sign(self._GLParent.pixelY)))

        elif symbolType == 1:
            for drawStr in drawList.stringList:
                r, w = 0.7 * drawStr.lineWidths[0], 0.7 * drawStr.lineWidths[1]
                drawStr.setStringOffset((r * np.sign(self._GLParent.pixelX), w * np.sign(self._GLParent.pixelY)))

        elif symbolType == 2:
            for drawStr in drawList.stringList:
                r, w = 0.7 * drawStr.lineWidths[0], 0.7 * drawStr.lineWidths[1]
                drawStr.setStringOffset((r * np.sign(self._GLParent.pixelX), w * np.sign(self._GLParent.pixelY)))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Building
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _buildSymbols(self, spectrumView, peakListView):
        spectrum = spectrumView.spectrum

        if peakListView not in self._GLSymbolItems:
            self._GLSymbolItems[peakListView] = GLPeakListArray(GLContext=self,
                                                              spectrumView=spectrumView,
                                                              peakListView=peakListView)

        drawList = self._GLSymbolItems[peakListView]

        if drawList.renderMode == GLRENDERMODE_RESCALE:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode
            self._rescalePeakList(spectrumView=spectrumView, peakListView=peakListView)
            self._rescalePeakListLabels(spectrumView=spectrumView,
                                        peakListView=peakListView,
                                        drawList=self._GLSymbolLabels[peakListView])

        elif drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            drawList.clearArrays()

            # find the correct scale to draw square pixels
            # don't forget to change when the axes change

            symbolType = self.strip.peakSymbolType
            symbolWidth = self.strip.peakSymbolSize / 2.0

            x = abs(self._GLParent.pixelX)
            y = abs(self._GLParent.pixelY)
            if x <= y:
                r = symbolWidth
                w = symbolWidth * y / x
            else:
                w = symbolWidth
                r = symbolWidth * x / y

            if symbolType == 0:  # a cross

                # change the ratio on resize
                drawList.refreshMode = GLREFRESHMODE_REBUILD
                drawList.drawMode = GL.GL_LINES
                drawList.fillMode = None

            elif symbolType == 1:  # draw an ellipse at lineWidth

                # fix the size to the axes
                drawList.refreshMode = GLREFRESHMODE_NEVER
                drawList.drawMode = GL.GL_LINES
                drawList.fillMode = None

            elif symbolType == 2:  # draw a filled ellipse at lineWidth

                # fix the size to the axes
                drawList.refreshMode = GLREFRESHMODE_NEVER
                drawList.drawMode = GL.GL_TRIANGLES
                drawList.fillMode = GL.GL_FILL

            # build the peaks VBO
            index = 0
            indexPtr = 0

            pls = peakListView.peakList
            listCol = getAutoColourRgbRatio(pls.symbolColour, pls.spectrum, self._GLParent.SPECTRUMPOSCOLOUR,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])

            spectrumFrequency = spectrum.spectrometerFrequencies

            for peak in pls.peaks:

                # TODO:ED display the required peaks - possibly build all then draw selected later
                strip = spectrumView.strip
                _isInPlane = strip.peakIsInPlane(peak)
                if not _isInPlane:
                    _isInFlankingPlane = strip.peakIsInFlankingPlane(peak)
                    fade = GLDefs.FADE_FACTOR
                else:
                    _isInFlankingPlane = None
                    fade = 1.0

                if not _isInPlane and not _isInFlankingPlane:
                    continue

                if self._isSelected(peak):
                    cols = self._GLParent.highlightColour[:3]
                else:
                    cols = listCol

                # get the correct coordinates based on the axisCodes
                p0 = [0.0] * 2  #len(self.axisOrder)
                lineWidths = [None] * 2  #len(self.axisOrder)
                frequency = [0.0] * 2  #len(self.axisOrder)
                axisCount = 0
                for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
                    for pp, ppCode in enumerate(peak.axisCodes):

                        if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                            if ppCode[0] == psCode[0]:
                                p0[ps] = peak.position[pp]
                                lineWidths[ps] = peak.lineWidths[pp]
                                frequency[ps] = spectrumFrequency[pp]
                                axisCount += 1

                        elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                            if ppCode == psCode:
                                p0[ps] = peak.position[pp]
                                lineWidths[ps] = peak.lineWidths[pp]
                                frequency[ps] = spectrumFrequency[pp]
                                axisCount += 1

                if axisCount != 2:
                    getLogger().debug('Bad peak.axisCodes: %s - %s' % (peak.pid, peak.axisCodes))
                else:
                    if symbolType == 0:

                        # draw a cross
                        # keep the cross square at 0.1ppm

                        _isSelected = False
                        # unselected
                        if _isInPlane or _isInFlankingPlane:
                            if self._isSelected(peak):
                                _isSelected = True
                                drawList.indices = np.append(drawList.indices, [index, index + 1, index + 2, index + 3,
                                                                                index, index + 2, index + 2, index + 1,
                                                                                index, index + 3, index + 3, index + 1])
                            else:
                                drawList.indices = np.append(drawList.indices, [index, index + 1, index + 2, index + 3])

                        drawList.vertices = np.append(drawList.vertices, [p0[0] - r, p0[1] - w,
                                                                          p0[0] + r, p0[1] + w,
                                                                          p0[0] + r, p0[1] - w,
                                                                          p0[0] - r, p0[1] + w])
                        drawList.colors = np.append(drawList.colors, [*cols, fade] * GLDefs.LENCOLORS)
                        drawList.attribs = np.append(drawList.attribs, [p0[0], p0[1],
                                                                        p0[0], p0[1],
                                                                        p0[0], p0[1],
                                                                        p0[0], p0[1]])

                        # keep a pointer to the peak
                        drawList.pids = np.append(drawList.pids, [peak, index, 4,
                                                                  _isInPlane, _isInFlankingPlane, _isSelected,
                                                                  indexPtr, len(drawList.indices)])
                        indexPtr = len(drawList.indices)

                        index += 4
                        drawList.numVertices += 4

                    elif symbolType == 1:  # draw an ellipse at lineWidth

                        if lineWidths[0] and lineWidths[1]:
                            # draw 24 connected segments
                            r = 0.5 * lineWidths[0] / frequency[0]
                            w = 0.5 * lineWidths[1] / frequency[1]
                            numPoints = 24
                            angPlus = 2 * np.pi
                            skip = 1
                        else:
                            # draw 12 disconnected segments (dotted)
                            # r = symbolWidth
                            # w = symbolWidth
                            numPoints = 12
                            angPlus = 1.0 * np.pi
                            skip = 2

                        np2 = 2 * numPoints
                        ang = list(range(numPoints))
                        _isSelected = False

                        if _isInPlane or _isInFlankingPlane:
                            drawList.indices = np.append(drawList.indices,
                                                         [[index + (2 * an), index + (2 * an) + 1] for an in ang])
                            if self._isSelected(peak):
                                _isSelected = True
                                drawList.indices = np.append(drawList.indices, [index + np2, index + np2 + 2,
                                                                                index + np2 + 2, index + np2 + 1,
                                                                                index + np2, index + np2 + 3,
                                                                                index + np2 + 3, index + np2 + 1])

                        # draw an ellipse at lineWidth
                        drawList.vertices = np.append(drawList.vertices,
                                                      [[p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                        p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                        p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                        p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints)] for
                                                       an in ang])
                        drawList.vertices = np.append(drawList.vertices, [p0[0] - r, p0[1] - w,
                                                                          p0[0] + r, p0[1] + w,
                                                                          p0[0] + r, p0[1] - w,
                                                                          p0[0] - r, p0[1] + w,
                                                                          p0[0], p0[1]])

                        drawList.colors = np.append(drawList.colors, [*cols, fade] * (np2 + 5))
                        drawList.attribs = np.append(drawList.attribs, [p0[0], p0[1]] * (np2 + 5))
                        drawList.offsets = np.append(drawList.offsets, [p0[0], p0[1]] * (np2 + 5))
                        drawList.lineWidths = (r, w)

                        # keep a pointer to the peak
                        drawList.pids = np.append(drawList.pids, [peak, index, numPoints,
                                                                  _isInPlane, _isInFlankingPlane, _isSelected,
                                                                  indexPtr, len(drawList.indices)])
                        indexPtr = len(drawList.indices)

                        index += np2 + 5
                        drawList.numVertices += np2 + 5

                    elif symbolType == 2:  # draw a filled ellipse at lineWidth

                        if lineWidths[0] and lineWidths[1]:
                            # draw 24 connected segments
                            r = 0.5 * lineWidths[0] / frequency[0]
                            w = 0.5 * lineWidths[1] / frequency[1]
                            numPoints = 24
                            angPlus = 2 * np.pi
                            skip = 1
                        else:
                            # draw 12 disconnected segments (dotted)
                            # r = symbolWidth
                            # w = symbolWidth
                            numPoints = 12
                            angPlus = 1.0 * np.pi
                            skip = 2

                        np2 = 2 * numPoints
                        ang = list(range(numPoints))
                        _isSelected = False

                        if _isInPlane or _isInFlankingPlane:
                            drawList.indices = np.append(drawList.indices,
                                                         [[index + (2 * an), index + (2 * an) + 1, index + np2 + 4] for
                                                          an in ang])

                        # draw an ellipse at lineWidth
                        drawList.vertices = np.append(drawList.vertices,
                                                      [[p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                        p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                        p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                        p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints)] for
                                                       an in ang])
                        drawList.vertices = np.append(drawList.vertices, [p0[0] - r, p0[1] - w,
                                                                          p0[0] + r, p0[1] + w,
                                                                          p0[0] + r, p0[1] - w,
                                                                          p0[0] - r, p0[1] + w,
                                                                          p0[0], p0[1]])

                        drawList.colors = np.append(drawList.colors, [*cols, fade] * (np2 + 5))
                        drawList.attribs = np.append(drawList.attribs, [p0[0], p0[1]] * (np2 + 5))
                        drawList.offsets = np.append(drawList.offsets, [p0[0], p0[1]] * (np2 + 5))
                        drawList.lineWidths = (r, w)

                        # keep a pointer to the peak
                        drawList.pids = np.append(drawList.pids, [peak, index, numPoints,
                                                                  _isInPlane, _isInFlankingPlane, _isSelected,
                                                                  indexPtr, len(drawList.indices)])
                        indexPtr = len(drawList.indices)

                        index += np2 + 5
                        drawList.numVertices += np2 + 5

    def buildSymbols(self):
        if self.strip.isDeleted:
            return

        # list through the valid peakListViews attached to the strip - including undeleted
        for spectrumView in self.strip.spectrumViews:
            for peakListView in spectrumView.peakListViews:

                if peakListView in self._GLSymbolItems.keys():
                    if self._GLSymbolItems[peakListView].renderMode == GLRENDERMODE_RESCALE:
                        self._buildSymbols(spectrumView, peakListView)

                if peakListView.buildPeakLists:
                    peakListView.buildPeakLists = False

                    # set the interior flags for rebuilding the GLdisplay
                    if peakListView in self._GLSymbolItems.keys():
                        self._GLSymbolItems[peakListView].renderMode = GLRENDERMODE_REBUILD

                    self._buildSymbols(spectrumView, peakListView)

    def _buildLabels(self, spectrumView, peakListView):
        # spectrum = spectrumView.spectrum

        if peakListView not in self._GLSymbolLabels.keys():
            self._GLSymbolLabels[peakListView] = GLPeakLabelsArray(GLContext=self,
                                                                     spectrumView=spectrumView,
                                                                     peakListView=peakListView)

        drawList = self._GLSymbolLabels[peakListView]
        if drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            # drawList.clearArrays()
            drawList.stringList = []

            # if spectrumView in self._threads:
            #   self._threads[spectrumView].terminate()

            buildQueue = (spectrumView, peakListView, drawList, self._GLParent)
            buildPeaks = Thread(name=str(self.strip.pid + spectrumView.pid),
                                target=self._threadBuildLabels,
                                args=buildQueue)
            # self._threads[spectrumView] = buildPeaks
            buildPeaks.start()
            return

            drawList.clearArrays()
            drawList.stringList = []

            # symbolWidth = self._parent.peakSymbolSize / 2.0

            pls = peakListView.peakList
            # spectrumFrequency = spectrum.spectrometerFrequencies

            for peak in pls.peaks:
                self._appendPeakListLabel(spectrumView, peakListView, drawList.stringList, peak)

        elif drawList.renderMode == GLRENDERMODE_RESCALE:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode
            self._rescalePeakListLabels(spectrumView, peakListView, drawList)

    def buildLabels(self):
        if self.strip.isDeleted:
            return

        _buildList = []
        for spectrumView in self.strip.spectrumViews:
            for peakListView in spectrumView.peakListViews:

                if peakListView in self._GLSymbolLabels.keys():
                    if self._GLSymbolLabels[peakListView].renderMode == GLRENDERMODE_RESCALE:
                        self._rescalePeakListLabels(spectrumView, peakListView, self._GLSymbolLabels[peakListView])

                if peakListView.buildPeakListLabels:
                    peakListView.buildPeakListLabels = False

                    if peakListView in self._GLSymbolLabels.keys():
                        self._GLSymbolLabels[peakListView].renderMode = GLRENDERMODE_REBUILD

                    # self._buildPeakListLabels(spectrumView, peakListView)
                    _buildList.append([spectrumView, peakListView])

        if _buildList:
            self._buildAllLabels(_buildList)
            # self._rescalePeakListLabels(spectrumView, peakListView, self._GLPeakListLabels[peakListView])

    def _buildAllLabels(self, viewList):
        for ii, view in enumerate(viewList):
            spectrumView = view[0]
            peakListView = view[1]
            if peakListView not in self._GLSymbolLabels.keys():
                self._GLSymbolLabels[peakListView] = GLPeakLabelsArray(GLContext=self,
                                                                         spectrumView=spectrumView,
                                                                         peakListView=peakListView)
                drawList = self._GLSymbolLabels[peakListView]
                drawList.stringList = []

        # if self._parent in self._threads:
        #   print('>>>here')
        #   # if self._threads[self._parent]._pool[0].is_alive():
        #   if self._threads[self._parent].is_alive():
        #     print('  >>>kill')
        #     # self._threads[self._parent].terminate()
        #     # self._threads[self._parent].join()
        #
        # for a process:
        # if not p.is_alive(): continue
        # os.kill(p.pid, signal.SIGKILL)
        # buildQueue = Queue()
        buildQueue = (viewList, self._GLParent, self._GLSymbolLabels)
        buildPeaks = Thread(name=str(self.strip.pid),
                            target=self._threadBuildAllLabels,
                            args=buildQueue)
        # buildPeaks.daemon = True

        # buildPeaks = pool.ThreadPool(processes=1)
        self._threads[self.strip] = buildPeaks

        # buildPeaks.apply_async(self._threadBuildAllPeakListLabels,
        #                         args=(viewList, self))

        buildPeaks.start()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Threads
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _threadBuildLabels(self, spectrumView, peakListView, drawList, glStrip):
        tempList = []
        pls = peakListView.peakList

        for peak in pls.peaks:
            self._appendPeakListLabel(spectrumView, peakListView, tempList, peak)

        # self._rescalePeakListLabels(spectrumView, peakListView, drawList)
        drawList.stringList = tempList
        drawList.renderMode = GLRENDERMODE_RESCALE
        glStrip.GLSignals.emitPaintEvent(source=glStrip)

    def _threadBuildAllLabels(self, viewList, glStrip, _outList):
        # def _threadBuildAllPeakListLabels(self, threadQueue):#viewList, glStrip, _outList):
        #   print ([obj for obj in threadQueue])
        #   viewList = threadQueue[0]
        #   glStrip = threadQueue[1]
        #   _outList = threadQueue[2]
        #   stringList = threadQueue[3]

        for ii, view in enumerate(viewList):
            spectrumView = view[0]
            peakListView = view[1]
            self._threadBuildLabels(spectrumView, peakListView,
                                            _outList[peakListView],
                                            glStrip)

        glStrip.GLSignals.emitPaintEvent(source=glStrip)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Drawing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def drawSymbols(self):
        """Draw the symbols to the screen
        """
        if self.strip.isDeleted:
            return

        self.buildSymbols()

        lineThickness = self.strip.peakSymbolThickness
        GL.glLineWidth(lineThickness)

        # loop through the attached peakListViews to the strip
        for spectrumView in self._GLParent._ordering:  #self._parent.spectrumViews:
            for peakListView in spectrumView.peakListViews:
                if spectrumView.isVisible() and peakListView.isVisible():

                    if peakListView in self._GLSymbolItems.keys():
                        self._GLSymbolItems[peakListView].drawIndexArray()

        GL.glLineWidth(1.0)

    def drawLabels(self):
        """Draw the labelling to the screen
        """
        if self.strip.isDeleted:
            return

        self.buildLabels()

        # loop through the attached peakListViews to the strip
        for spectrumView in self._GLParent._ordering:  #self._parent.spectrumViews:
            for peakListView in spectrumView.peakListViews:
                if spectrumView.isVisible() and peakListView.isVisible():

                    if peakListView in self._GLSymbolLabels.keys():

                        for drawString in self._GLSymbolLabels[peakListView].stringList:
                            drawString.drawTextArray()
