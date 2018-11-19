"""
Classes to handle drawing of symbols and symbol labelling to the openGL window
Currently this is peaks and multiplets
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
__version__ = "$Revision: 3.0.b4 $"
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
import time
from threading import Thread
import multiprocessing as mp
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
    CCPNGLWIDGET_LABELLING, CCPNGLWIDGET_PHASETRACE, CCPNGLWIDGET_MULTIPLETLINK, getColours
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
    GLSymbolArray, GLLabelArray
# from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLViewports import GLViewports
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLWidgets import GLIntegralRegion, GLExternalRegion, \
    GLRegion, REGION_COLOURS
# from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLExport import GLExporter
import ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs as GLDefs

from ccpn.util.Common import makeIterableList
from ccpn.core.lib.Cache import cached


# from ccpn.util.Constants import AXIS_FULLATOMNAME, AXIS_MATCHATOMTYPE


try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)

POINTCOLOURS = 4
OBJ_ISINPLANE = 0
OBJ_ISINFLANKINGPLANE = 1
OBJ_LINEWIDTHS = 2
OBJ_SPECTRALFREQUENCIES = 3
OBJ_OTHER = 4
OBJ_STORELEN = 5


_totalTime = 0.0
_timeCount = 0
_numTimes = 12


class GLLabelling():
    """Base class to handle symbol and symbol labelling
    """

    def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
        """Initialise the class
        """
        self._GLParent = parent
        self.strip = strip
        self.name = name
        self.resizeGL = resizeGL
        self._threads = {}
        self._threadupdate = False
        self.current = self.strip.current if self.strip else None
        self._objectStore = {}

        self._GLSymbols = {}
        self._GLLabels = {}

        self.autoColour = self._GLParent.SPECTRUMPOSCOLOUR

    def rescale(self):
        if self.resizeGL:
            for pp in self._GLSymbols.values():
                pp.renderMode = GLRENDERMODE_RESCALE


class GLpeakListMethods():
    """Class of methods common to 1d and Nd peaks
    This is added to the Peak Classes below and doesn't require an __init__
    """

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # List handlers
    #   The routines that have to be changed when accessing different named
    #   lists.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _isSelected(self, peak):
        """return True if the obj in the defined object list
        """
        if self.current.peaks:
            return peak in self.current.peaks

    def objects(self, obj):
        """return the peaks attached to the object
        """
        return obj.peaks

    def objectList(self, obj):
        """return the peakList attached to the peak
        """
        return obj.peakList

    def listViews(self, peakList):
        """Return the peakListViews attached to the peakList
        """
        return peakList.peakListViews

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # List specific routines
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def getLabelling(self, obj, labelType):
        """Get the object label based on the current labelling method
        For peaks, this is constructed from the pids of the attached nmrAtoms
        """
        if labelType == 0:
            # return the short code form
            text = _getScreenPeakAnnotation(obj, useShortCode=True)
        elif labelType == 1:
            # return the long form
            text = _getScreenPeakAnnotation(obj, useShortCode=False)
        else:
            # return the original pid
            text = _getPeakAnnotation(obj)

        return text

    def objIsInVisiblePlanes(self, spectrumView, peak):
        """Return whether in plane or adjacent
        """
        displayIndices = spectrumView._displayOrderSpectrumDimensionIndices

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:
                # If no axis matches the index may be None
                zPosition = peak.position[displayIndex]
                if not zPosition:
                    return False, False, 1.0
                zPlaneSize = 0.
                orderedAxes = spectrumView.strip.orderedAxes[2:]
                zRegion = orderedAxes[ii].region
                if not(zPosition < zRegion[0] - zPlaneSize or zPosition > zRegion[1] + zPlaneSize):
                    return True, False, 1.0

                zWidth = orderedAxes[ii].width
                if zRegion[0] - zWidth < zPosition < zRegion[0] or zRegion[1] < zPosition < zRegion[1] + zWidth:
                    return False, True, GLDefs.FADE_FACTOR

        return False, False, 1.0

    def objIsInPlane(self, strip, peak) -> bool:
        """is peak in currently displayed planes for strip?"""

        spectrumView = strip.findSpectrumView(peak.peakList.spectrum)
        if spectrumView is None:
            return False
        displayIndices = spectrumView._displayOrderSpectrumDimensionIndices
        orderedAxes = strip.orderedAxes[2:]

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:
                # If no axis matches the index may be None
                zPosition = peak.position[displayIndex]
                if not zPosition:
                    return False
                zPlaneSize = 0.
                zRegion = orderedAxes[ii].region
                if zPosition < zRegion[0] - zPlaneSize or zPosition > zRegion[1] + zPlaneSize:
                    return False

        return True

    def objIsInFlankingPlane(self, strip, peak) -> bool:
        """is peak in planes flanking currently displayed planes for strip?"""

        spectrumView = strip.findSpectrumView(peak.peakList.spectrum)
        if spectrumView is None:
            return False
        displayIndices = spectrumView._displayOrderSpectrumDimensionIndices
        orderedAxes = strip.orderedAxes[2:]

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:
                # If no axis matches the index may be None
                zPosition = peak.position[displayIndex]
                if not zPosition:
                    return False
                zRegion = orderedAxes[ii].region
                zWidth = orderedAxes[ii].width
                if zRegion[0] - zWidth < zPosition < zRegion[0] or zRegion[1] < zPosition < zRegion[1] + zWidth:
                    return True

        return False

    def extraIndicesCount(self, obj):
        """Calculate how many indices to add
        """
        return 0

    def appendExtraIndices(self, drawList, index, obj):
        """Add extra indices to the index list
        """
        return 0

    def extraVerticesCount(self, obj):
        """Calculate how many vertices to add
        """
        return 0

    def appendExtraVertices(self, drawList, obj, p0, colour, fade):
        """Add extra vertices to the vertex list
        """
        return 0


def _fillNdLabel(self, spectrumView, objListView, obj):
    self._fillLabel(self, spectrumView, objListView, obj)


class GLpeakNdLabelling(GLLabelling, GLpeakListMethods):
    """Class to handle symbol and symbol labelling for Nd displays
    """

    def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
        """Initialise the class
        """
        super(GLpeakNdLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Handle notifiers
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _deleteSymbol(self, obj):
        pls = self.objectList(obj)
        if pls:
            spectrum = pls.spectrum

            for objListView in self.listViews(pls):
                if objListView in self._GLSymbols.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self.strip.spectrumViews:
                            self._removeSymbol(spectrumView, objListView, obj)
                            self._updateHighlightedSymbols(spectrumView, objListView)

    def _createSymbol(self, obj):
        pls = self.objectList(obj)
        if pls:
            spectrum = pls.spectrum

            for objListView in self.listViews(pls):
                if objListView in self._GLSymbols.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self.strip.spectrumViews:
                            self._appendSymbol(spectrumView, objListView, obj)
                            self._updateHighlightedSymbols(spectrumView, objListView)

    def _changeLabel(self, obj):
        self._deleteLabel(obj)
        self._createLabel(obj)

    def _changeSymbol(self, obj):
        pls = self.objectList(obj)
        if pls:
            spectrum = pls.spectrum

            for objListView in self.listViews(pls):
                if objListView in self._GLSymbols.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self.strip.spectrumViews:
                            self._removeSymbol(spectrumView, objListView, obj)
                            self._appendSymbol(spectrumView, objListView, obj)
                            self._updateHighlightedSymbols(spectrumView, objListView)

    def _deleteLabel(self, obj):
        for pll in self._GLLabels.keys():
            drawList = self._GLLabels[pll]

            for drawStr in drawList.stringList:
                if drawStr.object == obj:
                    drawList.stringList.remove(drawStr)
                    break

    def _createLabel(self, obj):
        pls = self.objectList(obj)
        if pls:
            spectrum = pls.spectrum

            for objListView in self.listViews(pls):
                if objListView in self._GLLabels.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self.strip.spectrumViews:
                            drawList = self._GLLabels[objListView]
                            self._appendLabel(spectrumView, objListView, drawList.stringList, obj)
                            self._rescaleLabels(spectrumView, objListView, drawList)

    def _processNotifier(self, data):
        """Process notifiers
        """
        triggers = data[Notifier.TRIGGER]
        obj = data[Notifier.OBJECT]

        if Notifier.DELETE in triggers:
            self._deleteSymbol(obj)
            self._deleteLabel(obj)

        if Notifier.CREATE in triggers:
            self._createSymbol(obj)
            self._createLabel(obj)

        if Notifier.CHANGE in triggers:
            self._changeSymbol(obj)
            self._changeLabel(obj)

    def _appendLabel(self, spectrumView, objListView, stringList, obj):
        """Append a new label to the end of the list
        """
        if not obj.position:
            return

        spectrum = spectrumView.spectrum
        spectrumFrequency = spectrum.spectrometerFrequencies
        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        symbolWidth = self.strip.symbolSize / 2.0

        p0 = [0.0] * 2  # len(self.axisOrder)
        lineWidths = [None] * 2  # len(self.axisOrder)
        frequency = [0.0] * 2  # len(self.axisOrder)
        axisCount = 0
        for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
            for pp, ppCode in enumerate(obj.axisCodes):

                if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                    if ppCode[0] == psCode[0]:
                        p0[ps] = obj.position[pp]
                        lineWidths[ps] = obj.lineWidths[pp]
                        frequency[ps] = spectrumFrequency[pp]
                        axisCount += 1

                elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                    if ppCode == psCode:
                        p0[ps] = obj.position[pp]
                        lineWidths[ps] = obj.lineWidths[pp]
                        frequency[ps] = spectrumFrequency[pp]
                        axisCount += 1

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if lineWidths[0] and lineWidths[1]:
            # draw 24 connected segments
            r = 0.5 * lineWidths[0] / frequency[0]
            w = 0.5 * lineWidths[1] / frequency[1]
        else:
            r = symbolWidth
            w = symbolWidth

        if axisCount == 2:

            # get visible/plane status
            _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

            # skip if not visible
            if not _isInPlane and not _isInFlankingPlane:
                return

            if self._isSelected(obj):
                listCol = self._GLParent.highlightColour[:3]
            else:
                listCol = getAutoColourRgbRatio(pls.textColour, pls.spectrum,
                                                self.autoColour,
                                                getColours()[CCPNGLWIDGET_FOREGROUND])

            text = self.getLabelling(obj, self.strip.peakLabelling)

            stringList.append(GLString(text=text,
                                       font=self._GLParent.globalGL.glSmallFont if _isInPlane else self._GLParent.globalGL.glSmallTransparentFont,
                                       x=p0[0], y=p0[1],
                                       ox=r, oy=w,
                                       # x=self._screenZero[0], y=self._screenZero[1]
                                       color=(*listCol, fade),
                                       GLContext=self._GLParent,
                                       obj=obj, clearArrays=False))

    def _fillLabels(self, spectrumView, objListView, pls, objectList):
        """Append all labels to the new list
        """
        spectrum = spectrumView.spectrum
        spectrumFrequency = spectrum.spectrometerFrequencies
        # pls = peakListView.peakList
        # pls = self.objectList(objListView)
        # obj = spectrumView.project.getByPid(objPid) if isinstance(objPid, str) else objPid

        # use the first object for referencing
        obj = objectList(pls)[0]

        symbolWidth = self.strip.symbolSize / 2.0

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        p0 = (obj.position[pIndex[0]], obj.position[pIndex[1]])
        lineWidths = (obj.lineWidths[pIndex[0]], obj.lineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])

        p0 = [0.0] * 2  # len(self.axisOrder)
        lineWidths = [None] * 2  # len(self.axisOrder)
        frequency = [0.0] * 2  # len(self.axisOrder)
        axisCount = 0
        for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
            for pp, ppCode in enumerate(obj.axisCodes):

                if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                    if ppCode[0] == psCode[0]:
                        p0[ps] = obj.position[pp]
                        lineWidths[ps] = obj.lineWidths[pp]
                        frequency[ps] = spectrumFrequency[pp]
                        axisCount += 1

                elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                    if ppCode == psCode:
                        p0[ps] = obj.position[pp]
                        lineWidths[ps] = obj.lineWidths[pp]
                        frequency[ps] = spectrumFrequency[pp]
                        axisCount += 1

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if lineWidths[0] and lineWidths[1]:
            # draw 24 connected segments
            r = 0.5 * lineWidths[0] / frequency[0]
            w = 0.5 * lineWidths[1] / frequency[1]
        else:
            r = symbolWidth
            w = symbolWidth

        # if axisCount == 2:
        if pIndex:

            # get visible/plane status
            _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

            # skip if not visible
            if not _isInPlane and not _isInFlankingPlane:
                return

            if self._isSelected(obj):
                listCol = self._GLParent.highlightColour[:3]
            else:
                listCol = getAutoColourRgbRatio(pls.textColour, pls.spectrum,
                                                self.autoColour,
                                                getColours()[CCPNGLWIDGET_FOREGROUND])

            text = self.getLabelling(obj, self.strip.peakLabelling)

            return GLString(text=text,
                            font=self._GLParent.globalGL.glSmallFont if _isInPlane else self._GLParent.globalGL.glSmallTransparentFont,
                            x=p0[0], y=p0[1],
                            ox=r, oy=w,
                            color=(*listCol, fade),
                            GLContext=self._GLParent,
                            obj=obj, clearArrays=False)

    def _removeSymbol(self, spectrumView, objListView, delObj):
        """Remove a symbol from the list
        """
        symbolType = self.strip.symbolType

        drawList = self._GLSymbols[objListView]

        index = 0
        indexOffset = 0
        numPoints = 0

        pp = 0
        while (pp < len(drawList.pids)):
            # check whether the peaks still exists
            obj = drawList.pids[pp]

            if obj == delObj:
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                if symbolType != 0:
                    numPoints = 2 * numPoints + 5

                # _isInPlane = drawList.pids[pp + 3]
                # _isInFlankingPlane = drawList.pids[pp + 4]
                # _selected = drawList.pids[pp + 5]
                indexStart = drawList.pids[pp + 6]
                indexEnd = drawList.pids[pp + 7]
                indexOffset = indexEnd - indexStart

                drawList.indices = np.delete(drawList.indices, np.s_[indexStart:indexEnd])
                drawList.vertices = np.delete(drawList.vertices, np.s_[2 * offset:2 * (offset + numPoints)])
                drawList.attribs = np.delete(drawList.attribs, np.s_[2 * offset:2 * (offset + numPoints)])
                drawList.offsets = np.delete(drawList.offsets, np.s_[2 * offset:2 * (offset + numPoints)])
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

    def _insertSymbolItem(self, strip, obj, listCol, indexList, r, w,
                          spectrumFrequency, symbolType, drawList, spectrumView,
                          buildIndex):
        """insert a single symbol to the end of the symbol list
        """

        tk = time.time()
        times = [('_', tk)]

        index = indexList[0]
        indexPtr = indexList[1]
        objNum = buildIndex[0]
        vertexPtr = buildIndex[1]

        times.append(('_col:', time.time()))

        # get visible/plane status
        _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

        # skip if not visible
        if not _isInPlane and not _isInFlankingPlane:
            return

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            cols = listCol

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]

        times.append(('_sym:', time.time()))

        p0 = (obj.position[pIndex[0]], obj.position[pIndex[1]])
        lineWidths = (obj.lineWidths[pIndex[0]], obj.lineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])

        times.append(('_p0:', time.time()))

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if not pIndex:
            # if axisCount != 2:
            getLogger().debug('Bad axisCodes: %s - %s' % (obj.pid, obj.axisCodes))
        else:
            if symbolType == 0:

                # draw a cross
                # keep the cross square at 0.1ppm

                _selected = False
                # unselected
                if _isInPlane or _isInFlankingPlane:
                    if self._isSelected(obj):
                        _selected = True
                        drawList.indices[indexPtr:indexPtr + 12] = (index, index + 1, index + 2, index + 3,
                                                                    index, index + 2, index + 2, index + 1,
                                                                    index, index + 3, index + 3, index + 1)
                        iCount = 12
                    else:
                        try:
                            drawList.indices[indexPtr:indexPtr + 4] = (index, index + 1, index + 2, index + 3)
                            iCount = 4

                        except Exception as es:
                            pass

                times.append(('_ind:', time.time()))

                # add extra indices for the peak
                extraIndices = self.appendExtraIndices(drawList, index + 4, obj)

                drawList.vertices[vertexPtr:vertexPtr + 8] = (p0[0] - r, p0[1] - w,
                                                              p0[0] + r, p0[1] + w,
                                                              p0[0] + r, p0[1] - w,
                                                              p0[0] - r, p0[1] + w)
                drawList.colors[2 * vertexPtr:2 * vertexPtr + 16] = (*cols, fade) * GLDefs.LENCOLORS
                drawList.attribs[vertexPtr:vertexPtr + 8] = (p0[0], p0[1],
                                                             p0[0], p0[1],
                                                             p0[0], p0[1],
                                                             p0[0], p0[1])

                # add extra vertices for the multiplet
                extraVertices = self.appendExtraVertices(drawList, obj, p0, (*cols, fade), fade)

                try:
                    # keep a pointer to the obj
                    drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (4 + extraVertices),
                                                                    _isInPlane, _isInFlankingPlane, _selected,
                                                                    indexPtr, len(drawList.indices))
                except Exception as es:
                    pass

                times.append(('_pids:', time.time()))

                indexList[0] += (4 + extraIndices)
                indexList[1] += iCount  # len(drawList.indices)
                drawList.numVertices += (4 + extraVertices)
                buildIndex[0] += GLDefs.LENPID
                buildIndex[1] += (2 * (4 + extraVertices))

            elif symbolType == 1:  # draw an ellipse at lineWidth

                if lineWidths[0] and lineWidths[1]:
                    # draw 24 connected segments
                    r = 0.5 * lineWidths[0] / frequency[0]
                    w = 0.5 * lineWidths[1] / frequency[1]
                    numPoints = 24
                    angPlus = 2.0 * np.pi
                    skip = 1
                else:
                    # draw 12 disconnected segments (dotted)
                    # r = symbolWidth
                    # w = symbolWidth
                    numPoints = 12
                    angPlus = np.pi
                    skip = 2

                np2 = 2 * numPoints
                ang = list(range(numPoints))
                _selected = False

                if _isInPlane or _isInFlankingPlane:
                    drawList.indices[indexPtr:indexPtr + np2] = tuple((index + (2 * an), index + (2 * an) + 1) for an in ang)

                    if self._isSelected(obj):
                        _selected = True
                        drawList.indices[indexPtr + np2:indexPtr + np2 + 8] = (index + np2, index + np2 + 2,
                                                                               index + np2 + 2, index + np2 + 1,
                                                                               index + np2, index + np2 + 3,
                                                                               index + np2 + 3, index + np2 + 1)

                # add extra indices for the multiplet
                extraIndices = 0  #self.appendExtraIndices(drawList, index + np2, obj)

                # draw an ellipse at lineWidth
                drawList.vertices[vertexPtr:vertexPtr + 2 * np2] = np.append(drawList.vertices, tuple((p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                                                       p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                                                       p0[0] - r * math.sin(
                                                                                                           (skip * an + 1) * angPlus / numPoints),
                                                                                                       p0[1] - w * math.cos(
                                                                                                           (skip * an + 1) * angPlus / numPoints))
                                                                                                      for an in ang))
                drawList.vertices[vertexPtr + 2 * np2:vertexPtr + 2 * np2 + 10] = (p0[0] - r, p0[1] - w,
                                                                                   p0[0] + r, p0[1] + w,
                                                                                   p0[0] + r, p0[1] - w,
                                                                                   p0[0] - r, p0[1] + w,
                                                                                   p0[0], p0[1])

                drawList.colors[2 * vertexPtr:2 * vertexPtr + 4 * np2 + 20] = (*cols, fade) * (np2 + 5)
                drawList.attribs[vertexPtr + 2 * np2:vertexPtr + 2 * np2 + 10] = (p0[0], p0[1]) * (np2 + 5)
                drawList.offsets[vertexPtr + 2 * np2:vertexPtr + 2 * np2 + 10] = (p0[0], p0[1]) * (np2 + 5)
                drawList.lineWidths = (r, w)

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (numPoints + extraVertices),
                                                                _isInPlane, _isInFlankingPlane, _selected,
                                                                indexPtr, len(drawList.indices))

                indexList[0] += ((np2 + 5) + extraIndices)
                indexList[1] = len(drawList.indices)
                drawList.numVertices += ((np2 + 5) + extraVertices)
                buildIndex[0] += GLDefs.LENPID
                buildIndex[1] += (2 * ((np2 + 5) + extraVertices))

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
                _selected = False

                if _isInPlane or _isInFlankingPlane:
                    drawList.indices[indexPtr:indexPtr + 3 * numPoints] = tuple((index + (2 * an), index + (2 * an) + 1, index + np2 + 4) for an in ang)

                # add extra indices for the multiplet
                extraIndices = 0  #self.appendExtraIndices(drawList, index + np2 + 4, obj)

                # draw an ellipse at lineWidth
                drawList.vertices[vertexPtr:vertexPtr + 2 * np2] = tuple((p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                          p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                          p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                                          p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints))
                                                                         for an in ang)
                drawList.vertices[vertexPtr + 2 * np2:vertexPtr + 2 * np2 + 10] = (p0[0] - r, p0[1] - w,
                                                                                   p0[0] + r, p0[1] + w,
                                                                                   p0[0] + r, p0[1] - w,
                                                                                   p0[0] - r, p0[1] + w,
                                                                                   p0[0], p0[1])

                drawList.colors[2 * vertexPtr:2 * vertexPtr + 4 * np2 + 20] = (*cols, fade) * (np2 + 5)
                drawList.attribs[vertexPtr + 2 * np2:vertexPtr + 2 * np2 + 10] = (p0[0], p0[1]) * (np2 + 5)
                drawList.offsets[vertexPtr + 2 * np2:vertexPtr + 2 * np2 + 10] = (p0[0], p0[1]) * (np2 + 5)
                drawList.lineWidths = (r, w)

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (numPoints + extraVertices),
                                                                _isInPlane, _isInFlankingPlane, _selected,
                                                                indexPtr, len(drawList.indices))
                # indexPtr = len(drawList.indices)

                indexList[0] += ((np2 + 5) + extraIndices)
                indexList[1] = len(drawList.indices)
                drawList.numVertices += ((np2 + 5) + extraVertices)
                buildIndex[0] += GLDefs.LENPID
                buildIndex[1] += (2 * ((np2 + 5) + extraVertices))

        times.append(('_sym:', time.time()))
        print(', '.join([str(t[0] + str(t[1] - tk)) for t in times]))

    def _appendSymbolItem(self, strip, obj, listCol, indexList, r, w,
                          spectrumFrequency, symbolType, drawList, spectrumView):
        """append a single symbol to the end of the symbol list
        """
        index = indexList[0]
        indexPtr = indexList[1]

        # get visible/plane status
        _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

        # skip if not visible
        if not _isInPlane and not _isInFlankingPlane:
            return

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            cols = listCol

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]

        p0 = (obj.position[pIndex[0]], obj.position[pIndex[1]])
        lineWidths = (obj.lineWidths[pIndex[0]], obj.lineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if not pIndex:
            # if axisCount != 2:
            getLogger().debug('Bad axisCodes: %s - %s' % (obj.pid, obj.axisCodes))
        else:
            if symbolType == 0:

                # draw a cross
                # keep the cross square at 0.1ppm

                _selected = False
                # unselected
                if _isInPlane or _isInFlankingPlane:
                    if self._isSelected(obj):
                        _selected = True
                        drawList.indices = np.append(drawList.indices, (index, index + 1, index + 2, index + 3,
                                                                        index, index + 2, index + 2, index + 1,
                                                                        index, index + 3, index + 3, index + 1))
                    else:
                        drawList.indices = np.append(drawList.indices, (index, index + 1, index + 2, index + 3))

                # add extra indices for the multiplet
                extraIndices = self.appendExtraIndices(drawList, index + 4, obj)

                drawList.vertices = np.append(drawList.vertices, (p0[0] - r, p0[1] - w,
                                                                  p0[0] + r, p0[1] + w,
                                                                  p0[0] + r, p0[1] - w,
                                                                  p0[0] - r, p0[1] + w))
                drawList.colors = np.append(drawList.colors, (*cols, fade) * GLDefs.LENCOLORS)
                drawList.attribs = np.append(drawList.attribs, (p0[0], p0[1],
                                                                p0[0], p0[1],
                                                                p0[0], p0[1],
                                                                p0[0], p0[1]))

                # add extra vertices for the multiplet
                extraVertices = self.appendExtraVertices(drawList, obj, p0, (*cols, fade), fade)

                # keep a pointer to the obj
                drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (4 + extraVertices),
                                                          _isInPlane, _isInFlankingPlane, _selected,
                                                          indexPtr, len(drawList.indices)))
                # indexPtr = len(drawList.indices)

                indexList[0] += (4 + extraIndices)
                indexList[1] = len(drawList.indices)
                drawList.numVertices += (4 + extraVertices)

            elif symbolType == 1:  # draw an ellipse at lineWidth

                if lineWidths[0] and lineWidths[1]:
                    # draw 24 connected segments
                    r = 0.5 * lineWidths[0] / frequency[0]
                    w = 0.5 * lineWidths[1] / frequency[1]
                    numPoints = 24
                    angPlus = 2.0 * np.pi
                    skip = 1
                else:
                    # draw 12 disconnected segments (dotted)
                    # r = symbolWidth
                    # w = symbolWidth
                    numPoints = 12
                    angPlus = np.pi
                    skip = 2

                np2 = 2 * numPoints
                ang = list(range(numPoints))
                _selected = False

                if _isInPlane or _isInFlankingPlane:
                    drawList.indices = np.append(drawList.indices, tuple((index + (2 * an), index + (2 * an) + 1) for an in ang))

                    if self._isSelected(obj):
                        _selected = True
                        drawList.indices = np.append(drawList.indices, (index + np2, index + np2 + 2,
                                                                        index + np2 + 2, index + np2 + 1,
                                                                        index + np2, index + np2 + 3,
                                                                        index + np2 + 3, index + np2 + 1))

                # add extra indices for the multiplet
                extraIndices = 0  #self.appendExtraIndices(drawList, index + np2, obj)

                # draw an ellipse at lineWidth
                drawList.vertices = np.append(drawList.vertices, tuple((p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                        p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                        p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                                        p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints))
                                                                       for an in ang))
                drawList.vertices = np.append(drawList.vertices, (p0[0] - r, p0[1] - w,
                                                                  p0[0] + r, p0[1] + w,
                                                                  p0[0] + r, p0[1] - w,
                                                                  p0[0] - r, p0[1] + w,
                                                                  p0[0], p0[1]))

                drawList.colors = np.append(drawList.colors, (*cols, fade) * (np2 + 5))
                drawList.attribs = np.append(drawList.attribs, (p0[0], p0[1]) * (np2 + 5))
                drawList.offsets = np.append(drawList.offsets, (p0[0], p0[1]) * (np2 + 5))
                drawList.lineWidths = (r, w)

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (numPoints + extraVertices),
                                                          _isInPlane, _isInFlankingPlane, _selected,
                                                          indexPtr, len(drawList.indices)))
                # indexPtr = len(drawList.indices)

                indexList[0] += ((np2 + 5) + extraIndices)
                indexList[1] = len(drawList.indices)
                drawList.numVertices += ((np2 + 5) + extraVertices)

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
                _selected = False

                if _isInPlane or _isInFlankingPlane:
                    drawList.indices = np.append(drawList.indices,
                                                 tuple((index + (2 * an), index + (2 * an) + 1, index + np2 + 4) for an in
                                                       ang))

                # add extra indices for the multiplet
                extraIndices = 0  #self.appendExtraIndices(drawList, index + np2 + 4, obj)

                # draw an ellipse at lineWidth
                drawList.vertices = np.append(drawList.vertices, tuple((p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                        p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                        p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                                        p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints))
                                                                       for an in ang))
                drawList.vertices = np.append(drawList.vertices, (p0[0] - r, p0[1] - w,
                                                                  p0[0] + r, p0[1] + w,
                                                                  p0[0] + r, p0[1] - w,
                                                                  p0[0] - r, p0[1] + w,
                                                                  p0[0], p0[1]))

                drawList.colors = np.append(drawList.colors, (*cols, fade) * (np2 + 5))
                drawList.attribs = np.append(drawList.attribs, (p0[0], p0[1]) * (np2 + 5))
                drawList.offsets = np.append(drawList.offsets, (p0[0], p0[1]) * (np2 + 5))
                drawList.lineWidths = (r, w)

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (numPoints + extraVertices),
                                                          _isInPlane, _isInFlankingPlane, _selected,
                                                          indexPtr, len(drawList.indices)))
                # indexPtr = len(drawList.indices)

                indexList[0] += ((np2 + 5) + extraIndices)
                indexList[1] = len(drawList.indices)
                drawList.numVertices += ((np2 + 5) + extraVertices)

    def _appendSymbol(self, spectrumView, objListView, obj):
        """Append a new symbol to the end of the list
        """
        spectrum = spectrumView.spectrum
        drawList = self._GLSymbols[objListView]

        # find the correct scale to draw square pixels
        # don't forget to change when the axes change

        symbolType = self.strip.symbolType
        symbolWidth = self.strip.symbolSize / 2.0
        lineThickness = self.strip.symbolThickness / 2.0

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
        # index = 0
        # indexPtr = len(drawList.indices)
        indexing = [0, len(drawList.indices)]

        # for pls in spectrum.peakLists:

        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        listCol = getAutoColourRgbRatio(pls.symbolColour, pls.spectrum,
                                        self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])

        spectrumFrequency = spectrum.spectrometerFrequencies

        strip = spectrumView.strip
        self._appendSymbolItem(strip, obj, listCol, indexing, r, w,
                               spectrumFrequency, symbolType, drawList, spectrumView)

    def _updateHighlightedLabels(self, spectrumView, objListView):
        if objListView not in self._GLLabels:
            return

        drawList = self._GLLabels[objListView]
        strip = self.strip

        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        listCol = getAutoColourRgbRatio(pls.textColour, pls.spectrum, self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])

        for drawStr in drawList.stringList:

            obj = drawStr.object

            if obj and not obj.isDeleted:
                # get visible/plane status
                _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                if _isInPlane or _isInFlankingPlane:

                    if self._isSelected(obj):
                        drawStr.setColour((*self._GLParent.highlightColour[:3], fade))
                    else:
                        drawStr.setColour((*listCol, fade))

    def updateHighlightSymbols(self):
        """Respond to an update highlight notifier and update the highlighted symbols/labels
        """
        for spectrumView in self.strip.spectrumViews:
            # for peakListView in spectrumView.peakListViews:
            for objListView in self.listViews(spectrumView):

                if objListView in self._GLSymbols.keys():
                    self._updateHighlightedSymbols(spectrumView, objListView)
                    self._updateHighlightedLabels(spectrumView, objListView)

    def updateAllSymbols(self):
        """Respond to update all notifier
        """
        for spectrumView in self.strip.spectrumViews:
            # for peakListView in spectrumView.peakListViews:
            for objListView in self.listViews(spectrumView):

                if objListView in self._GLSymbols.keys():
                    objListView.buildSymbols = True
                    objListView.buildLabels = True

    def _updateHighlightedSymbols(self, spectrumView, objListView):
        """update the highlighted symbols
        """
        spectrum = spectrumView.spectrum
        strip = self.strip

        symbolType = strip.symbolType
        symbolWidth = strip.symbolSize / 2.0
        lineThickness = strip.symbolThickness / 2.0

        drawList = self._GLSymbols[objListView]
        drawList.indices = np.empty(0, dtype=np.uint32)

        index = 0
        indexPtr = 0

        # pls = objListView.peakList
        pls = self.objectList(objListView)

        listCol = getAutoColourRgbRatio(pls.symbolColour, pls.spectrum, self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])

        if symbolType == 0:
            for pp in range(0, len(drawList.pids), GLDefs.LENPID):

                # check whether the peaks still exists
                obj = drawList.pids[pp]
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                if not obj.isDeleted:
                    _selected = False

                    # get visible/plane status
                    _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                    if _isInPlane or _isInFlankingPlane:
                        if self._isSelected(obj):
                            _selected = True
                            cols = self._GLParent.highlightColour[:3]
                            drawList.indices = np.append(drawList.indices, (index, index + 1, index + 2, index + 3,
                                                                            index, index + 2, index + 2, index + 1,
                                                                            index, index + 3, index + 3, index + 1))
                        else:
                            cols = listCol

                            drawList.indices = np.append(drawList.indices, (index, index + 1, index + 2, index + 3))

                        # make sure that links for the multiplets are added
                        extraIndices = self.appendExtraIndices(drawList, index + 4, obj)
                        drawList.colors[offset * 4:(offset + POINTCOLOURS) * 4] = (*cols, fade) * POINTCOLOURS  #numPoints

                    # list MAY contain out of plane peaks
                    drawList.pids[pp + 3:pp + 8] = (_isInPlane, _isInFlankingPlane, _selected,
                                                    indexPtr, len(drawList.indices))
                    indexPtr = len(drawList.indices)

                index += numPoints

        elif symbolType == 1:

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):

                # check whether the peaks still exists
                obj = drawList.pids[pp]
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]
                np2 = 2 * numPoints

                if not obj.isDeleted:
                    ang = list(range(numPoints))

                    _selected = False
                    # get visible/plane status
                    _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                    if _isInPlane or _isInFlankingPlane:
                        drawList.indices = np.append(drawList.indices, tuple((index + (2 * an), index + (2 * an) + 1) for an in ang))

                        if self._isSelected(obj):
                            _selected = True
                            cols = self._GLParent.highlightColour[:3]
                            drawList.indices = np.append(drawList.indices, (index + np2, index + np2 + 2,
                                                                            index + np2 + 2, index + np2 + 1,
                                                                            index + np2, index + np2 + 3,
                                                                            index + np2 + 3, index + np2 + 1))
                        else:
                            cols = listCol

                        drawList.colors[offset * 4:(offset + np2 + 5) * 4] = (*cols, fade) * (np2 + 5)

                    drawList.pids[pp + 3:pp + 8] = (_isInPlane, _isInFlankingPlane, _selected,
                                                    indexPtr, len(drawList.indices))
                    indexPtr = len(drawList.indices)

                index += np2 + 5

        elif symbolType == 2:

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):

                # check whether the peaks still exists
                obj = drawList.pids[pp]
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]
                np2 = 2 * numPoints

                if not obj.isDeleted:
                    ang = list(range(numPoints))

                    _selected = False
                    # get visible/plane status
                    _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                    if _isInPlane or _isInFlankingPlane:
                        drawList.indices = np.append(drawList.indices, tuple((index + (2 * an), index + (2 * an) + 1, index + np2 + 4)
                                                                             for an in ang))
                        if self._isSelected(obj):
                            _selected = True
                            cols = self._GLParent.highlightColour[:3]
                        else:
                            cols = listCol

                        drawList.colors[offset * 4:(offset + np2 + 5) * 4] = (*cols, fade) * (np2 + 5)

                    drawList.pids[pp + 3:pp + 8] = (_isInPlane, _isInFlankingPlane, _selected,
                                                    indexPtr, len(drawList.indices))
                    indexPtr = len(drawList.indices)

                index += np2 + 5

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Rescaling
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _rescaleSymbols(self, spectrumView, objListView):
        """rescale symbols when the screen dimensions change
        """
        drawList = self._GLSymbols[objListView]

        # if drawList.refreshMode == GLREFRESHMODE_REBUILD:

        symbolType = self.strip.symbolType
        symbolWidth = self.strip.symbolSize / 2.0
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
            # for pp in range(0, 2 * drawList.numVertices, 8):
            #     drawList.vertices[pp:pp + 8] = drawList.attribs[pp:pp + 8] + offsets

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):
                index = 2 * drawList.pids[pp + 1]
                try:
                    drawList.vertices[index:index + 8] = drawList.attribs[index:index + 8] + offsets
                except:
                    pass

            pass

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

    def _rescaleLabels(self, spectrumView=None, objListView=None, drawList=None):
        """Rescale all labels to the new dimensions of the screen
        """
        symbolType = self.strip.symbolType
        symbolWidth = self.strip.symbolSize / 2.0
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

    def _buildSymbolsCountItem(self, strip, spectrumView, obj, symbolType):
        """return the number of indices and vertices for the object
        """
        # get visible/plane status
        _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

        # skip if not visible
        if not _isInPlane and not _isInFlankingPlane:
            return 0, 0

        if symbolType == 0:  # draw a cross
            if self._isSelected(obj):
                ind = 12
            else:
                ind = 4

            ind += self.extraIndicesCount(obj)

            extraVertices = self.extraVerticesCount(obj)
            vert = (4 + extraVertices)
            return ind, vert

        elif symbolType == 1:  # draw an ellipse at lineWidth

            if obj.lineWidths[0] and obj.lineWidths[1]:
                numPoints = 24
            else:
                numPoints = 12

            np2 = 2 * numPoints
            ind = np2
            if self._isSelected(obj):
                ind += 8
            vert = (np2 + 5)
            return ind, vert

        elif symbolType == 2:  # draw a filled ellipse at lineWidth

            if obj.lineWidths[0] and obj.lineWidths[1]:
                numPoints = 24
            else:
                numPoints = 12

            ind = 3 * numPoints
            vert = ((2 * numPoints) + 5)
            return ind, vert

    def _buildSymbolsCount(self, spectrumView, objListView, drawList):
        """count the number of indices and vertices for the label list
        """
        spectrum = spectrumView.spectrum

        pls = self.objectList(objListView)

        # reset the object pointers
        self._objectStore = {}

        indCount = 0
        vertCount = 0
        objCount = 0
        for tcount, obj in enumerate(self.objects(pls)):
            ind, vert = self._buildSymbolsCountItem(self.strip, spectrumView, obj, self.strip.symbolType)
            indCount += ind
            vertCount += vert
            if ind:
                objCount += 1

        # set up arrays
        drawList.indices = np.empty(indCount, dtype=np.uint32)
        drawList.vertices = np.empty(vertCount * 2, dtype=np.float32)
        drawList.colors = np.empty(vertCount * 4, dtype=np.float32)
        drawList.attribs = np.empty(vertCount * 2, dtype=np.float32)
        drawList.offsets = np.empty(vertCount * 2, dtype=np.float32)
        drawList.pids = np.empty(objCount * GLDefs.LENPID, dtype=np.object_)
        drawList.numindices = 0
        drawList.numVertices = 0

        return indCount, vertCount

    def _buildSymbols(self, spectrumView, objListView):
        spectrum = spectrumView.spectrum

        if objListView not in self._GLSymbols:
            self._GLSymbols[objListView] = GLSymbolArray(GLContext=self,
                                                         spectrumView=spectrumView,
                                                         objListView=objListView)

        drawList = self._GLSymbols[objListView]

        if drawList.renderMode == GLRENDERMODE_RESCALE:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode
            self._rescaleSymbols(spectrumView=spectrumView, objListView=objListView)
            # self._rescaleLabels(spectrumView=spectrumView,
            #                     objListView=objListView,
            #                     drawList=self._GLLabels[objListView])

            drawList.defineIndexVBO(enableVBO=False)

        elif drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            # times = [time.time(), self]

            # drawList.clearArrays()

            # find the correct scale to draw square pixels
            # don't forget to change when the axes change

            symbolType = self.strip.symbolType
            symbolWidth = self.strip.symbolSize / 2.0

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
            # index = 0
            # indexPtr = 0
            indexing = [0, 0]
            buildIndex = [0, 0]

            pls = self.objectList(objListView)

            listCol = getAutoColourRgbRatio(pls.symbolColour, pls.spectrum,
                                            self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])

            spectrumFrequency = spectrum.spectrometerFrequencies
            strip = spectrumView.strip

            # tk = time.time() - times[0]
            # times.append('_col:' + str(tk))

            ind, vert = self._buildSymbolsCount(spectrumView, objListView, drawList)
            if ind:

                # tsum = 0
                for tcount, obj in enumerate(self.objects(pls)):
                    self._insertSymbolItem(strip, obj, listCol, indexing, r, w,
                                           spectrumFrequency, symbolType, drawList,
                                           spectrumView, buildIndex)
                    # tsum += (time.time() - times[0])

                # times.append('_sym:' + str((time.time() - times[0])))
                # times.append('_t:' + str(tcount))

            drawList.defineIndexVBO(enableVBO=False)

            # times.append('_def:' + str(time.time() - times[0]))
            # print(', '.join([str(t) for t in times]))

    def buildSymbols(self):
        if self.strip.isDeleted:
            return

        # times = [time.time(), self]

        # list through the valid peakListViews attached to the strip - including undeleted
        for spectrumView in self.strip.spectrumViews:
            # for peakListView in spectrumView.peakListViews:
            for objListView in self.listViews(spectrumView):  # spectrumView.peakListViews:

                if objListView in self._GLSymbols.keys():
                    if self._GLSymbols[objListView].renderMode == GLRENDERMODE_RESCALE:
                        self._buildSymbols(spectrumView, objListView)

                # times.append('_rescale:'+str(time.time()-times[0]))
                if objListView.buildSymbols:
                    objListView.buildSymbols = False

                    # set the interior flags for rebuilding the GLdisplay
                    if objListView in self._GLSymbols.keys():
                        self._GLSymbols[objListView].renderMode = GLRENDERMODE_REBUILD

                    self._buildSymbols(spectrumView, objListView)
                    # times.append('_build:'+str(time.time()-times[0]))

    def buildLabels(self):
        if self.strip.isDeleted:
            return

        _buildList = []
        for spectrumView in self.strip.spectrumViews:
            # for peakListView in spectrumView.peakListViews:
            for objListView in self.listViews(spectrumView):

                if objListView in self._GLLabels.keys():
                    if self._GLLabels[objListView].renderMode == GLRENDERMODE_RESCALE:
                        self._rescaleLabels(spectrumView, objListView, self._GLLabels[objListView])
                        self._GLLabels[objListView].renderMode = GLRENDERMODE_DRAW
                        continue

                if objListView.buildLabels:
                    objListView.buildLabels = False

                    if objListView in self._GLLabels.keys():
                        self._GLLabels[objListView].renderMode = GLRENDERMODE_REBUILD

                    # self._buildPeakListLabels(spectrumView, peakListView)
                    _buildList.append([spectrumView, objListView])

        if _buildList:
            self._buildAllLabels(_buildList)
            # self._rescalePeakListLabels(spectrumView, peakListView, self._GLPeakListLabels[peakListView])

    def _buildAllLabels(self, viewList):
        for ii, view in enumerate(viewList):
            spectrumView = view[0]
            objListView = view[1]
            if objListView not in self._GLLabels.keys():
                self._GLLabels[objListView] = GLLabelArray(GLContext=self,
                                                           spectrumView=spectrumView,
                                                           objListView=objListView)
                drawList = self._GLLabels[objListView]
                drawList.stringList = []

        buildQueue = (viewList, self._GLParent, self._GLLabels)

        # not calling as a thread because it's not multiprocessing AND its slower
        self._threadBuildAllLabels(*buildQueue)

        # buildPeaks = Thread(name=str(self.strip.pid),
        #                     target=self._threadBuildAllLabels,
        #                     args=buildQueue)
        # buildPeaks.start()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Threads
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _threadBuildLabels(self, spectrumView, objListView, drawList, glStrip):

        global _totalTime
        global _timeCount
        global _numTimes

        tempList = []
        pls = self.objectList(objListView)

        # append all labels separately
        for obj in self.objects(pls):
            self._appendLabel(spectrumView, objListView, tempList, obj)

        # # append all labels in one go
        # self._fillLabels(spectrumView, objListView, tempList, pls, self.objects)

        drawList.stringList = tempList
        drawList.renderMode = GLRENDERMODE_RESCALE

    def _threadBuildAllLabels(self, viewList, glStrip, _outList):
        # def _threadBuildAllPeakListLabels(self, threadQueue):#viewList, glStrip, _outList):
        #   print ([obj for obj in threadQueue])
        #   viewList = threadQueue[0]
        #   glStrip = threadQueue[1]
        #   _outList = threadQueue[2]
        #   stringList = threadQueue[3]

        for ii, view in enumerate(viewList):
            spectrumView = view[0]
            objListView = view[1]
            self._threadBuildLabels(spectrumView, objListView,
                                    _outList[objListView],
                                    glStrip)

        glStrip.GLSignals.emitPaintEvent(source=glStrip)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Drawing
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def drawSymbols(self, spectrumSettings):
        """Draw the symbols to the screen
        """
        if self.strip.isDeleted:
            return

        self._spectrumSettings = spectrumSettings
        self.buildSymbols()

        lineThickness = self.strip.symbolThickness
        GL.glLineWidth(lineThickness)

        # loop through the attached objListViews to the strip
        for spectrumView in self._GLParent._ordering:  #self._parent.spectrumViews:
            # for peakListView in spectrumView.peakListViews:
            for objListView in self.listViews(spectrumView):
                if spectrumView.isVisible() and objListView.isVisible():

                    if objListView in self._GLSymbols.keys():
                        # self._GLSymbols[objListView].drawIndexArray()
                        self._GLSymbols[objListView].drawIndexVBO(enableVBO=False)

        GL.glLineWidth(1.0)

    def drawLabels(self, spectrumSettings):
        """Draw the labelling to the screen
        """
        if self.strip.isDeleted:
            return

        self._spectrumSettings = spectrumSettings
        self.buildLabels()

        # loop through the attached peakListViews to the strip
        for spectrumView in self._GLParent._ordering:  #self._parent.spectrumViews:
            # for peakListView in spectrumView.peakListViews:
            for objListView in self.listViews(spectrumView):
                if spectrumView.isVisible() and objListView.isVisible():

                    if objListView in self._GLLabels.keys():

                        for drawString in self._GLLabels[objListView].stringList:
                            drawString.drawTextArray()
                            # drawString.defineTextArray()


class GLpeak1dLabelling(GLpeakNdLabelling):
    """Class to handle symbol and symbol labelling for 1d displays
    """

    def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
        """Initialise the class
        """
        super(GLpeak1dLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)

    def _updateHighlightedSymbols(self, spectrumView, objListView):
        """update the highlighted symbols
        """
        spectrum = spectrumView.spectrum
        strip = self.strip

        symbolType = strip.symbolType
        symbolWidth = strip.symbolSize / 2.0
        lineThickness = strip.symbolThickness / 2.0

        drawList = self._GLSymbols[objListView]
        drawList.indices = np.empty(0, dtype=np.uint32)

        index = 0
        indexPtr = 0

        if symbolType is not None:
            listView = self.objectList(objListView)
            listCol = getAutoColourRgbRatio(listView.symbolColour,
                                            listView.spectrum,
                                            self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):

                # check whether the peaks still exists
                obj = drawList.pids[pp]
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                if not obj.isDeleted:
                    _selected = False
                    if self._isSelected(obj):
                        # if hasattr(obj, '_isSelected') and obj._isSelected:
                        _selected = True
                        cols = self._GLParent.highlightColour[:3]
                        drawList.indices = np.append(drawList.indices, (index, index + 1, index + 2, index + 3,
                                                                        index, index + 2, index + 2, index + 1,
                                                                        index, index + 3, index + 3, index + 1))
                    else:
                        cols = listCol

                        drawList.indices = np.append(drawList.indices, (index, index + 1, index + 2, index + 3))

                    # make sure that links for the multiplets are added
                    extraIndices = self.appendExtraIndices(drawList, index + 4, obj)
                    drawList.colors[offset * 4:(offset + POINTCOLOURS) * 4] = (*cols, 1.0) * POINTCOLOURS  # numPoints

                    drawList.pids[pp + 3:pp + 8] = (True, True, _selected,
                                                    indexPtr, len(drawList.indices))
                    indexPtr = len(drawList.indices)

                index += numPoints

    def _buildSymbols(self, spectrumView, objListView):
        spectrum = spectrumView.spectrum

        if objListView not in self._GLSymbols:
            self._GLSymbols[objListView] = GLSymbolArray(GLContext=self,
                                                         spectrumView=spectrumView,
                                                         objListView=objListView)

        drawList = self._GLSymbols[objListView]

        if drawList.renderMode == GLRENDERMODE_RESCALE:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode
            self._rescaleSymbols(spectrumView=spectrumView, objListView=objListView)
            self._rescaleLabels(spectrumView=spectrumView,
                                objListView=objListView,
                                drawList=self._GLLabels[objListView])

        elif drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            # drawList.refreshMode = GLRENDERMODE_DRAW

            drawList.clearArrays()

            # find the correct scale to draw square pixels
            # don't forget to change when the axes change

            symbolType = self.strip.symbolType
            symbolWidth = self.strip.symbolSize / 2.0
            # lineThickness = self._preferences.symbolThickness / 2.0

            x = abs(self._GLParent.pixelX)
            y = abs(self._GLParent.pixelY)
            if x <= y:
                r = symbolWidth
                w = symbolWidth * y / x
            else:
                w = symbolWidth
                r = symbolWidth * x / y

            if symbolType is not None:  #== 0:  # a cross

                # change the ratio on resize
                drawList.refreshMode = GLREFRESHMODE_REBUILD
                drawList.drawMode = GL.GL_LINES
                drawList.fillMode = None

            # build the peaks VBO
            index = 0
            indexPtr = 0

            # pls = peakListView.peakList
            pls = self.objectList(objListView)

            listCol = getAutoColourRgbRatio(pls.symbolColour, pls.spectrum,
                                            self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])

            # for obj in pls.peaks:
            for obj in self.objects(pls):

                strip = spectrumView.strip
                if self._isSelected(obj):
                    cols = self._GLParent.highlightColour[:3]
                else:
                    cols = listCol

                # test axisCodes
                try:
                    ax = obj.axisCodes
                except Exception as es:
                    pass

                pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
                p0 = (obj.position[pIndex[0]], obj.height)

                # # get the correct coordinates based on the axisCodes
                # p0 = [0.0] * 2  #len(self.axisOrder)
                # for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
                #     for pp, ppCode in enumerate(obj.axisCodes):
                #
                #         if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                #             if ppCode[0] == psCode[0]:
                #                 p0[ps] = obj.position[pp]
                #             else:
                #                 p0[ps] = obj.height
                #
                #         elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                #             if ppCode == psCode:
                #                 p0[ps] = obj.position[pp]
                #             else:
                #                 p0[ps] = obj.height

                if None in p0:
                    getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
                    continue

                if symbolType is not None:  #== 0:

                    # draw a cross
                    # keep the cross square at 0.1ppm

                    _selected = False
                    if self._isSelected(obj):
                        # if hasattr(obj, '_isSelected') and obj._isSelected:
                        _selected = True
                        drawList.indices = np.append(drawList.indices, (index, index + 1, index + 2, index + 3,
                                                                        index, index + 2, index + 2, index + 1,
                                                                        index, index + 3, index + 3, index + 1))
                    else:
                        drawList.indices = np.append(drawList.indices, (index, index + 1, index + 2, index + 3))

                    # add extra indices for the multiplet
                    extraIndices = self.appendExtraIndices(drawList, index + 4, obj)

                    drawList.vertices = np.append(drawList.vertices, (p0[0] - r, p0[1] - w,
                                                                      p0[0] + r, p0[1] + w,
                                                                      p0[0] + r, p0[1] - w,
                                                                      p0[0] - r, p0[1] + w))
                    drawList.colors = np.append(drawList.colors, (*cols, 1.0) * GLDefs.LENCOLORS)
                    drawList.attribs = np.append(drawList.attribs, (p0[0], p0[1],
                                                                    p0[0], p0[1],
                                                                    p0[0], p0[1],
                                                                    p0[0], p0[1]))

                    # add extra vertices for the multiplet
                    extraVertices = self.appendExtraVertices(drawList, obj, p0, (*cols, 1.0), 1.0)

                    # keep a pointer to the obj
                    drawList.pids = np.append(drawList.pids, (obj, index, (4 + extraVertices),
                                                              True, True, _selected,
                                                              indexPtr, len(drawList.indices)))
                    indexPtr = len(drawList.indices)

                    index += (4 + extraIndices)
                    drawList.numVertices += (4 + extraVertices)

    def _rescaleSymbols(self, spectrumView, objListView):
        """rescale symbols when the screen dimensions change
        """
        drawList = self._GLSymbols[objListView]

        # if drawList.refreshMode == GLREFRESHMODE_REBUILD:

        symbolType = self.strip.symbolType
        symbolWidth = self.strip.symbolSize / 2.0
        x = abs(self._GLParent.pixelX)
        y = abs(self._GLParent.pixelY)

        # fix the aspect ratio of the cross to match the screen
        # minIndex = 0 if x <= y else 1
        # pos = [symbolWidth, symbolWidth * y / x]
        # w = r = pos[minIndex]

        if x <= y:
            r = symbolWidth
            w = symbolWidth * y / x
        else:
            w = symbolWidth
            r = symbolWidth * x / y

        if symbolType is not None:  #== 0:  # a cross
            # drawList.clearVertices()
            # drawList.vertices.copy(drawList.attribs)
            offsets = np.array([-r, -w, +r, +w, +r, -w, -r, +w], np.float32)
            # for pp in range(0, 2 * drawList.numVertices, 8):
            #     drawList.vertices[pp:pp + 8] = drawList.attribs[pp:pp + 8] + offsets

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):
                index = 2 * drawList.pids[pp + 1]
                drawList.vertices[index:index + 8] = drawList.attribs[index:index + 8] + offsets

    def _appendSymbol(self, spectrumView, objListView, obj):
        """Append a new symbol to the end of the list
        """
        spectrum = spectrumView.spectrum
        drawList = self._GLSymbols[objListView]

        # find the correct scale to draw square pixels
        # don't forget to change when the axes change

        symbolType = self.strip.symbolType
        symbolWidth = self.strip.symbolSize / 2.0
        lineThickness = self.strip.symbolThickness / 2.0

        x = abs(self._GLParent.pixelX)
        y = abs(self._GLParent.pixelY)
        if x <= y:
            r = symbolWidth
            w = symbolWidth * y / x
        else:
            w = symbolWidth
            r = symbolWidth * x / y

        if symbolType is not None:  #== 0:  # a cross

            # change the ratio on resize
            drawList.refreshMode = GLREFRESHMODE_REBUILD
            drawList.drawMode = GL.GL_LINES
            drawList.fillMode = None

        # build the peaks VBO
        index = 0
        indexPtr = len(drawList.indices)

        # for pls in spectrum.peakLists:

        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        spectrumFrequency = spectrum.spectrometerFrequencies
        listCol = getAutoColourRgbRatio(pls.symbolColour, pls.spectrum,
                                        self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])

        strip = spectrumView.strip
        # get visible/plane status
        _isInPlane, _isInFlankingPlane, fade = self.objIsInVisiblePlanes(spectrumView, obj)

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            cols = listCol

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        p0 = (obj.position[pIndex[0]], obj.height)

        # # get the correct coordinates based on the axisCodes
        # p0 = [0.0] * 2  # len(self.axisOrder)
        # for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
        #     for pp, ppCode in enumerate(obj.axisCodes):
        #
        #         if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
        #             if ppCode[0] == psCode[0]:
        #                 p0[ps] = obj.position[pp]
        #             else:
        #                 p0[ps] = obj.height
        #
        #         elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
        #             if ppCode == psCode:
        #                 p0[ps] = obj.position[pp]
        #             else:
        #                 p0[ps] = obj.height

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if symbolType is not None:  #== 0:

            # draw a cross
            # keep the cross square at 0.1ppm

            _selected = False
            drawList.indices = np.append(drawList.indices, (index, index + 1, index + 2, index + 3))

            if self._isSelected(obj):
                # if hasattr(obj, '_isSelected') and obj._isSelected:
                _selected = True
                drawList.indices = np.append(drawList.indices, (index, index + 2, index + 2, index + 1,
                                                                index, index + 3, index + 3, index + 1))

            # add extra indices for the multiplet
            extraIndices = self.appendExtraIndices(drawList, index + 4, obj)

            drawList.vertices = np.append(drawList.vertices, (p0[0] - r, p0[1] - w,
                                                              p0[0] + r, p0[1] + w,
                                                              p0[0] + r, p0[1] - w,
                                                              p0[0] - r, p0[1] + w))
            drawList.colors = np.append(drawList.colors, (*cols, 1.0) * 4)
            drawList.attribs = np.append(drawList.attribs, (p0[0], p0[1],
                                                            p0[0], p0[1],
                                                            p0[0], p0[1],
                                                            p0[0], p0[1]))

            # add extra vertices for the multiplet
            extraVertices = self.appendExtraVertices(drawList, obj, p0, (*cols, 1.0), 1.0)

            # keep a pointer to the obj
            drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (4 + extraVertices),
                                                      True, True, _selected,
                                                      indexPtr, len(drawList.indices)))

            index += (4 + extraIndices)
            drawList.numVertices += (4 + extraVertices)

    def _removeSymbol(self, spectrumView, objListView, delObj):
        """Remove a symbol from the list
        """
        symbolType = self.strip.symbolType

        drawList = self._GLSymbols[objListView]

        index = 0
        indexOffset = 0
        numPoints = 0

        pp = 0
        while (pp < len(drawList.pids)):
            # check whether the peaks still exists
            obj = drawList.pids[pp]

            if obj == delObj:
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                # _isInPlane = drawList.pids[pp + 3]
                # _isInFlankingPlane = drawList.pids[pp + 4]
                # _selected = drawList.pids[pp + 5]
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

    def _appendLabel(self, spectrumView, objListView, stringList, obj):
        """Append a new label to the end of the list
        """
        spectrum = spectrumView.spectrum
        spectrumFrequency = spectrum.spectrometerFrequencies

        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        symbolWidth = self.strip.symbolSize / 2.0
        x = abs(self._GLParent.pixelX)
        y = abs(self._GLParent.pixelY)
        if x <= y:
            r = symbolWidth
            w = symbolWidth * y / x
        else:
            w = symbolWidth
            r = symbolWidth * x / y

        # get the correct coordinates based on the axisCodes
        p0 = [0.0] * 2  # len(self.axisOrder)
        for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
            for pp, ppCode in enumerate(obj.axisCodes):

                if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                    if ppCode[0] == psCode[0]:
                        p0[ps] = obj.position[pp]
                    else:
                        p0[ps] = obj.height

                elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                    if ppCode == psCode:
                        p0[ps] = obj.position[pp]
                    else:
                        p0[ps] = obj.height

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if self._isSelected(obj):
            listCol = self._GLParent.highlightColour[:3]
        else:
            listCol = getAutoColourRgbRatio(pls.textColour, pls.spectrum,
                                            self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])

        text = self.getLabelling(obj, self.strip.peakLabelling)

        stringList.append(GLString(text=text,
                                   font=self._GLParent.globalGL.glSmallFont,
                                   x=p0[0], y=p0[1],
                                   ox=r * np.sign(self._GLParent.pixelX), oy=w * np.sign(self._GLParent.pixelY),
                                   # ox=symbolWidth, oy=symbolWidth,
                                   # x=self._screenZero[0], y=self._screenZero[1]
                                   color=(*listCol, 1.0),
                                   GLContext=self._GLParent,
                                   obj=obj))

    def _rescaleLabels(self, spectrumView=None, objListView=None, drawList=None):
        """Rescale all labels to the new dimensions of the screen
        """
        symbolType = self.strip.symbolType
        symbolWidth = self.strip.symbolSize / 2.0
        x = abs(self._GLParent.pixelX)
        y = abs(self._GLParent.pixelY)

        if symbolType is not None:  #== 0:  # a cross
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


class GLmultipletListMethods():
    """Class of methods common to 1d and Nd multiplets
    This is added to the Multiplet Classes below and doesn't require an __init__
    """

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # List handlers
    #   The routines that have to be changed when accessing different named
    #   lists.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _isSelected(self, multiplet):
        """return True if the obj in the defined object list
        """
        if self.current.multiplets:
            return multiplet in self.current.multiplets

    def objects(self, obj):
        """return the multiplets attached to the object
        """
        return obj.multiplets

    def objectList(self, obj):
        """return the multipletList attached to the multiplet
        """
        return obj.multipletList

    def listViews(self, multipletList):
        """Return the multipletListViews attached to the multipletList
        """
        return multipletList.multipletListViews

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # List specific routines
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def objIsInPlane(self, strip, multiplet) -> bool:
        """is multiplet in currently displayed planes for strip?
        Use the first peak to determine the spectrumView and the actual multiplet position
        """
        if not multiplet.peaks:
            return False

        peak = multiplet.peaks[0]
        spectrumView = strip.findSpectrumView(peak.peakList.spectrum)
        if spectrumView is None:
            return False
        displayIndices = spectrumView._displayOrderSpectrumDimensionIndices
        orderedAxes = strip.orderedAxes[2:]

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:
                # If no axis matches the index may be None
                zPosition = multiplet.position[displayIndex]
                if not zPosition:
                    return False
                zPlaneSize = 0.
                zRegion = orderedAxes[ii].region
                if zPosition < zRegion[0] - zPlaneSize or zPosition > zRegion[1] + zPlaneSize:
                    return False

        return True

    def objIsInFlankingPlane(self, strip, multiplet) -> bool:
        """is peak in planes flanking currently displayed planes for strip?
        Use the first peak to determine the spectrumView and the actual multiplet position
        """
        if not multiplet.peaks:
            return False

        peak = multiplet.peaks[0]
        spectrumView = strip.findSpectrumView(peak.peakList.spectrum)
        if spectrumView is None:
            return False
        displayIndices = spectrumView._displayOrderSpectrumDimensionIndices
        orderedAxes = strip.orderedAxes[2:]

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:
                # If no axis matches the index may be None
                zPosition = multiplet.position[displayIndex]
                if not zPosition:
                    return False
                zRegion = orderedAxes[ii].region
                zWidth = orderedAxes[ii].width
                if zRegion[0] - zWidth < zPosition < zRegion[0] or zRegion[1] < zPosition < zRegion[1] + zWidth:
                    return True

        return False

    def getLabelling(self, obj, labelType):
        """get the object label based on the current labelling method
        """
        return obj.pid

    def extraIndicesCount(self, multiplet):
        """Calculate how many indices to add
        """
        return len(multiplet.peaks) + 1 if multiplet.peaks else 0

    def appendExtraIndices(self, drawList, index, multiplet):
        """Add extra indices to the index list
        """
        if not multiplet.peaks:
            return 0

        drawList.indices = np.append(drawList.indices, tuple((index, 1 + index + ii) for ii in range(len(multiplet.peaks))))
        return len(multiplet.peaks) + 1


class GLmultipletNdLabelling(GLmultipletListMethods, GLpeakNdLabelling):
    """Class to handle symbol and symbol labelling for Nd displays
    """

    def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
        """Initialise the class
        """
        super(GLmultipletNdLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)

        self.autoColour = self._GLParent.SPECTRUMNEGCOLOUR

    def extraVerticesCount(self, multiplet):
        """Calculate how many vertices to add
        """
        return 2 * len(multiplet.peaks)

    def appendExtraVertices(self, drawList, multiplet, p0, colour, fade):
        """Add extra vertices to the vertex list
        """
        if not multiplet.peaks:
            return 0

        # cols = getColours()[CCPNGLWIDGET_MULTIPLETLINK][:3]
        cols = getAutoColourRgbRatio(multiplet.multipletList.lineColour, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = [p0]

        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes
            p1 = [0.0] * 2  # len(self.axisOrder)
            axisCount = 0
            for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
                for pp, ppCode in enumerate(peak.axisCodes):

                    if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                        if ppCode[0] == psCode[0]:
                            p1[ps] = peak.position[pp]
                            axisCount += 1

                    elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                        if ppCode == psCode:
                            p1[ps] = peak.position[pp]
                            axisCount += 1

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                continue

            posList.append(p1)

        numVertices = len(posList)
        drawList.vertices = np.append(drawList.vertices, posList)
        drawList.colors = np.append(drawList.colors, (*cols, fade) * numVertices)
        drawList.attribs = np.append(drawList.attribs, p0 * numVertices)

        return numVertices


class GLmultiplet1dLabelling(GLmultipletListMethods, GLpeak1dLabelling):
    """Class to handle symbol and symbol labelling for 1d displays
    """

    def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
        """Initialise the class
        """
        super(GLmultiplet1dLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)

        self.autoColour = self._GLParent.SPECTRUMNEGCOLOUR

    def extraVerticesCount(self, multiplet):
        """Calculate how many vertices to add
        """
        return 2 * len(multiplet.peaks)

    def appendExtraVertices(self, drawList, multiplet, p0, colour, fade):
        """Add extra vertices to the vertex list
        """
        if not multiplet.peaks:
            return 0

        # cols = getColours()[CCPNGLWIDGET_MULTIPLETLINK][:3]
        cols = getAutoColourRgbRatio(multiplet.multipletList.lineColour, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = [p0]
        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes
            p1 = [0.0] * 2  # len(self.axisOrder)
            axisCount = 0
            for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
                for pp, ppCode in enumerate(peak.axisCodes):

                    if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                        if ppCode[0] == psCode[0]:
                            p1[ps] = peak.position[pp]
                        else:
                            p1[ps] = peak.height

                    elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                        if ppCode == psCode:
                            p1[ps] = peak.position[pp]
                        else:
                            p1[ps] = peak.height

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                continue

            posList.append(p1)

        numVertices = len(posList)
        drawList.vertices = np.append(drawList.vertices, posList)
        drawList.colors = np.append(drawList.colors, (*cols, fade) * numVertices)
        drawList.attribs = np.append(drawList.attribs, p0 * numVertices)

        return numVertices


class GLintegralListMethods():
    """Class of methods common to 1d and Nd integrals
    This is added to the Integral Classes below and doesn't require an __init__
    """

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # List handlers
    #   The routines that have to be changed when accessing different named
    #   lists.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _isSelected(self, integral):
        """return True if the obj in the defined object list
        """
        if self.current.integrals:
            return integral in self.current.integrals

    def objects(self, obj):
        """return the integrals attached to the object
        """
        return obj.integrals

    def objectList(self, obj):
        """return the integralList attached to the integral
        """
        return obj.integralList

    def listViews(self, integralList):
        """Return the integralListViews attached to the integralList
        """
        return integralList.integralListViews

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # List specific routines
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def getLabelling(self, obj, labelType):
        """get the object label based on the current labelling method
        """
        return obj.id + '\n' + str(obj.value)

    def extraIndicesCount(self, multiplet):
        """Calculate how many indices to add
        """
        return 0

    def appendExtraIndices(self, drawList, index, obj):
        """Add extra indices to the index list
        """
        return 0

    def appendExtraVertices(self, drawList, obj, p0, colour, fade):
        """Add extra vertices to the vertex list
        """
        return 0


class GLintegralNdLabelling(GLintegralListMethods, GLpeakNdLabelling):
    """Class to handle symbol and symbol labelling for Nd displays
    """

    def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
        """Initialise the class
        """
        super(GLintegralNdLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)

    def _updateHighlightedSymbols(self, spectrumView, integralListView):
        drawList = self._GLSymbols[integralListView]
        drawList._rebuild()

    def objIsInPlane(self, strip, integral) -> bool:
        """is integral in currently displayed planes for strip?"""
        return True

    def objIsInFlankingPlane(self, strip, integral) -> bool:
        """is integral in planes flanking currently displayed planes for strip?"""
        return True

    def drawSymbols(self, spectrumSettings):
        if self.strip.isDeleted:
            return

        self._spectrumSettings = spectrumSettings
        self.buildSymbols()

        # loop through the attached integralListViews to the strip
        for spectrumView in self._GLParent._ordering:  #self.strip.spectrumViews:
            for integralListView in spectrumView.integralListViews:
                if spectrumView.isVisible() and integralListView.isVisible():

                    if integralListView in self._GLSymbols.keys():
                        self._GLSymbols[integralListView].drawIndexArray()

                        # draw the integralAreas if they exist
                        for integralArea in self._GLSymbols[integralListView]._regions:
                            if hasattr(integralArea, '_integralArea'):
                                if self._GLParent._stackingMode:
                                    # use the stacking matrix to offset the 1D spectra
                                    self._GLParent.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
                                                                                                  1, GL.GL_FALSE,
                                                                                                  self._GLParent._spectrumSettings[
                                                                                                      spectrumView][
                                                                                                      GLDefs.SPECTRUM_STACKEDMATRIX])

                                integralArea._integralArea.drawVertexColor()

        self._GLParent.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._GLParent._IMatrix)

    def _rescaleLabels(self, spectrumView=None, objListView=None, drawList=None):
        """Rescale all labels to the new dimensions of the screen
        """
        for drawStr in drawList.stringList:
            vertices = drawStr.numVertices

            if vertices:
                if drawStr.axisIndex == 0:
                    offsets = [drawStr.axisPosition + (3.0 * self._GLParent.pixelX),
                               self._GLParent.axisT - (36.0 * self._GLParent.pixelY)]
                else:
                    offsets = [self._GLParent.axisL + (3.0 * self._GLParent.pixelX),
                               drawStr.axisPosition + (3.0 * self._GLParent.pixelY)]

                for pp in range(0, 2 * vertices, 2):
                    drawStr.attribs[pp:pp + 2] = offsets

    def rescaleIntegralLists(self):
        for il in self._GLSymbols.values():
            il._rescale()

    def _buildSymbols(self, spectrumView, integralListView):

        if integralListView not in self._GLSymbols:
            self._GLSymbols[integralListView] = GLIntegralRegion(project=self.strip.project, GLContext=self._GLParent,
                                                                 spectrumView=spectrumView,
                                                                 integralListView=integralListView)

        drawList = self._GLSymbols[integralListView]

        if drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            drawList.clearArrays()
            drawList._clearRegions()

            ils = integralListView.integralList
            listCol = getAutoColourRgbRatio(ils.symbolColour, ils.spectrum, self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])

            for integral in ils.integrals:
                drawList.addIntegral(integral, integralListView, colour=None,
                                     brush=(*listCol, CCPNGLWIDGET_INTEGRALSHADE))

        elif drawList.renderMode == GLRENDERMODE_RESCALE:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode
            drawList._rebuildIntegralAreas()

    def _deleteSymbol(self, integral):
        for ils in self._GLSymbols.values():

            # confusing as peakList and integralList share the same list :)
            if not ils.integralListView.isDeleted and integral.integralList == ils.integralListView.integralList:

                for reg in ils._regions:

                    if reg._object == integral:
                        ils._regions.remove(reg)
                        ils._rebuild()
                        return

    def _createSymbol(self, integral):
        for ils in self._GLSymbols.values():

            if not ils.integralListView.isDeleted and integral.integralList == ils.integralListView.integralList:
                listCol = getAutoColourRgbRatio(ils.integralListView.integralList.symbolColour,
                                                ils.integralListView.integralList.spectrum, self._GLParent.SPECTRUMPOSCOLOUR,
                                                getColours()[CCPNGLWIDGET_FOREGROUND])

                ils.addIntegral(integral, ils.integralListView, colour=None,
                                brush=(*listCol, CCPNGLWIDGET_INTEGRALSHADE))
                return

    def _changeSymbol(self, integral):
        for ils in self._GLSymbols.values():
            for reg in ils._regions:
                if reg._object == integral:
                    ils._resize()
                    return

    def _appendLabel(self, spectrumView, objListView, stringList, obj):
        """Append a new label to the end of the list
        """
        spectrum = spectrumView.spectrum
        spectrumFrequency = spectrum.spectrometerFrequencies

        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        symbolWidth = self.strip.symbolSize / 2.0

        # get the correct coordinates based on the axisCodes
        p0 = [0.0] * 2  # len(self.axisOrder)
        for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
            for pp, ppCode in enumerate(obj.axisCodes):

                if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                    if ppCode[0] == psCode[0]:

                        # need to put the position in here

                        if self._GLParent.INVERTXAXIS:
                            p0[ps] = pos = max(obj.limits[0])  # obj.position[pp]
                        else:
                            p0[ps] = pos = min(obj.limits[0])  # obj.position[pp]
                    else:
                        p0[ps] = 0.0  #obj.height

                elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                    if ppCode == psCode:
                        if self._GLParent.INVERTXAXIS:
                            p0[ps] = pos = max(obj.limits[0])  # obj.position[pp]
                        else:
                            p0[ps] = pos = min(obj.limits[0])  # obj.position[pp]
                    else:
                        p0[ps] = 0.0  #obj.height

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if self._isSelected(obj):
            listCol = self._GLParent.highlightColour[:3]
        else:
            listCol = getAutoColourRgbRatio(pls.textColour, pls.spectrum,
                                            self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])

        text = self.getLabelling(obj, self.strip.peakLabelling)

        textX = pos or 0.0 + (3.0 * self._GLParent.pixelX)
        textY = self._GLParent.axisT - (36.0 * self._GLParent.pixelY)

        stringList.append(GLString(text=text,
                                   font=self._GLParent.globalGL.glSmallFont,
                                   # x=p0[0], y=p0[1],
                                   x=textX,
                                   y=textY,
                                   # ox=symbolWidth, oy=symbolWidth,
                                   # x=self._screenZero[0], y=self._screenZero[1]
                                   color=(*listCol, 1.0),
                                   GLContext=self._GLParent,
                                   obj=obj))

        # this is in the attribs
        stringList[-1].axisIndex = 0
        stringList[-1].axisPosition = pos or 0.0


class GLintegral1dLabelling(GLintegralNdLabelling):
    """Class to handle symbol and symbol labelling for 1d displays
    """

    def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
        """Initialise the class
        """
        super(GLintegral1dLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)
