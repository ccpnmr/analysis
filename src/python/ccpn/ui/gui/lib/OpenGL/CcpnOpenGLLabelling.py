"""
Classes to handle drawing of symbols and symbol labelling to the openGL window
Currently this is peaks and multiplets
"""
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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-03-02 15:00:02 +0000 (Tue, March 02, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import math
import numpy as np
from PyQt5 import QtWidgets
from ccpn.core.lib.Notifiers import Notifier
from ccpn.util.Colour import getAutoColourRgbRatio
from ccpn.util.AttrDict import AttrDict
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_FOREGROUND, getColours
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import GLString
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLRENDERMODE_DRAW, GLRENDERMODE_RESCALE, GLRENDERMODE_REBUILD, \
    GLREFRESHMODE_NEVER, GLREFRESHMODE_REBUILD, GLSymbolArray, GLLabelArray
import ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs as GLDefs
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import getAliasSetting


# NOTE:ED - remember these for later, may create larger vertex arrays for symbols, but should be quicker
#       --
#       x = np.array([1, 2, 3, -1, 5, 0, 3, 4, 4, 7, 3, 5, 9, 0, 5, 4, 3], dtype=np.uint32)
#       seems to be the fastest way of getting masked values
#           SKIPINDEX = np.uint32(-1) = 4294967295
#           i.e. max index number, use as fill
#           timeit.timeit('import numpy as np; x = np.array([1, 2, 3, -1, 5, 0, 3, 4, 4, 7, 3, 5, 9, 0, 5, 4, 3], dtype=np.uint32); x[np.where(x != 3)]', number=200000)
#       fastest way to create filled arrays
#           *** timeit.timeit('import numpy as np; x = np.array([1, 2, 3, -1, 5, 0, 3, 4, 4, 7, 3, 5, 9, 0, 5, 4, 3], dtype=np.uint32); a = x[x != SKIPINDEX]', number=200000)
#               timeit.timeit('import numpy as np; x = np.array([1, 2, 3, -1, 5, 0, 3, 4, 4, 7, 3, 5, 9, 0, 5, 4, 3], dtype=np.uint32); mx = np.full(200000, SKIPINDEX, dtype=np.uint32)', number=20000)
#       --
#       np.take(x, np.where(x != 3))
#       mx = np.ma.masked_values(x, 3)
#       a = x[np.where(x != 3)]
#       *** a = x[x != SKIPINDEX]

from ccpn.ui.gui.lib.OpenGL import GL, GLU, GLUT

OBJ_ISINPLANE = 0
OBJ_ISINFLANKINGPLANE = 1
OBJ_LINEWIDTHS = 2
OBJ_SPECTRALFREQUENCIES = 3
OBJ_OTHER = 4
OBJ_STORELEN = 5

_totalTime = 0.0
_timeCount = 0
_numTimes = 12

DEFAULTLINECOLOUR = '#7f7f7f'


class GLLabelling():
    """Base class to handle symbol and symbol labelling
    """

    LENSQ = GLDefs.LENSQ
    LENSQ2 = GLDefs.LENSQ2
    LENSQ4 = GLDefs.LENSQ4
    POINTCOLOURS = GLDefs.POINTCOLOURS

    def __init__(self, parent=None, strip=None, name=None, enableResize=False):
        """Initialise the class
        """
        self._GLParent = parent
        self.strip = strip
        self.name = name
        self._resizeEnabled = enableResize
        self._threads = {}
        self._threadupdate = False
        self.current = self.strip.current if self.strip else None
        self._objectStore = {}

        self._GLSymbols = {}
        self._GLLabels = {}
        self._ordering = ()
        self._visibleOrdering = ()
        self._listViews = ()
        self._visibleListViews = ()
        self._objIsInVisiblePlanesCache = {}

        self.autoColour = self._GLParent.SPECTRUMPOSCOLOUR

    def enableResize(self, value):
        """enable resizing for labelling
        """
        if not isinstance(value, bool):
            raise TypeError('enableResize must be a bool')

        self._resizeEnabled = value

    def rescale(self):
        if self._resizeEnabled:
            for pp in self._GLSymbols.values():
                pp.renderMode = GLRENDERMODE_RESCALE
            for pp in self._GLLabels.values():
                pp.renderMode = GLRENDERMODE_RESCALE

    def setListViews(self, spectrumViews):
        """Return a list of tuples containing the visible lists and the containing spectrumView
        """
        self._listViews = [(lv, specView) for specView in spectrumViews
                           for lv in self.listViews(specView)
                           if not lv.isDeleted]
        self._visibleListViews = [(lv, specView) for lv, specView in self._listViews
                                  if lv.isVisible()
                                  and specView.isVisible()]
        # and lv in self._GLSymbols.keys()]
        self._ordering = spectrumViews

    def _handleNotifier(self, triggers, obj):
        if Notifier.DELETE in triggers:
            self._deleteSymbol(obj)
            self._deleteLabel(obj)

        if Notifier.CREATE in triggers:
            self._createSymbol(obj)
            self._createLabel(obj)

        if Notifier.CHANGE in triggers:
            self._changeSymbol(obj)
            self._changeLabel(obj)

    def _processNotifier(self, data):
        """Process notifiers
        """
        triggers = data[Notifier.TRIGGER]
        obj = data[Notifier.OBJECT]

        # update the multiplet labelling
        if Notifier.DELETE in triggers:
            self._deleteSymbol(obj)
            self._deleteLabel(obj)

        if Notifier.CREATE in triggers:
            self._createSymbol(obj)
            self._createLabel(obj)

        if Notifier.CHANGE in triggers:
            self._changeSymbol(obj)
            self._changeLabel(obj)

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
                        if spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            self._removeSymbol(spectrumView, objListView, obj)
                            # self._updateHighlightedSymbols(spectrumView, objListView)
                            self._GLSymbols[objListView].updateAliasedIndexVBO()
                            break

    # from ccpn.util.decorators import profile
    # @profile
    def _createSymbol(self, obj):
        pls = self.objectList(obj)
        if pls:
            spectrum = pls.spectrum

            for objListView in self.listViews(pls):
                if objListView in self._GLSymbols.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            self._appendSymbol(spectrumView, objListView, obj)
                            # self._updateHighlightedSymbols(spectrumView, objListView)
                            self._GLSymbols[objListView].updateAliasedIndexVBO()
                            break

    def _changeSymbol(self, obj):
        pls = self.objectList(obj)
        if pls:
            spectrum = pls.spectrum

            for objListView in self.listViews(pls):
                if objListView in self._GLSymbols.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            self._removeSymbol(spectrumView, objListView, obj)
                            self._appendSymbol(spectrumView, objListView, obj)
                            # self._updateHighlightedSymbols(spectrumView, objListView)
                            self._GLSymbols[objListView].updateAliasedIndexVBO()
                            break

    def _deleteLabel(self, obj):
        for pll in self._GLLabels.keys():
            drawList = self._GLLabels[pll]

            for drawStr in drawList.stringList:
                if drawStr.stringObject == obj:
                    drawList.stringList.remove(drawStr)
                    break

    def _changeLabel(self, obj):
        # NOTE:ED - not the nicest way of changing a label - needs work
        self._deleteLabel(obj)
        self._createLabel(obj)

    def _createLabel(self, obj):
        pls = self.objectList(obj)
        if pls:
            spectrum = pls.spectrum

            for objListView in self.listViews(pls):
                if objListView in self._GLLabels.keys():
                    for spectrumView in spectrum.spectrumViews:
                        if spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            drawList = self._GLLabels[objListView]
                            self._appendLabel(spectrumView, objListView, drawList.stringList, obj)
                            self._rescaleLabels(spectrumView, objListView, drawList)

    def _getSymbolWidths(self, spectrumView):
        """return the required r, w, symbolWidth for the current screen scaling.
        """
        symbolType = self.strip.symbolType
        symbolWidth = self.strip.symbolSize / 2.0

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        vPP = spectrumView.spectrum.valuesPerPoint

        try:
            r = self._GLParent.symbolX * np.sign(self._GLParent.pixelX)
            pr = r / vPP[pIndex[0]]
        except:
            pr = r
        try:
            w = self._GLParent.symbolY * np.sign(self._GLParent.pixelY)
            pw = w / vPP[pIndex[1]]
        except:
            pw = w

        return r, w, symbolType, symbolWidth, pr, pw

    def _appendLabel(self, spectrumView, objListView, stringList, obj):
        """Append a new label to the end of the list
        """
        if obj.isDeleted:
            return

        objPos = obj.ppmPositions
        if not objPos:
            return
        objLineWidths = obj.ppmLineWidths

        spectrum = spectrumView.spectrum
        spectrumFrequency = spectrum.spectrometerFrequencies
        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        p0 = (objPos[pIndex[0]], objPos[pIndex[1]])
        ppmLineWidths = (objLineWidths[pIndex[0]], objLineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        r, w, symbolType, symbolWidth, _, _ = self._getSymbolWidths(spectrumView)

        stringOffset = None
        if symbolType in (1, 2):
            # put to the top-right corner of the lineWidth
            if ppmLineWidths[0] and ppmLineWidths[1]:
                r = - GLDefs.STRINGSCALE * 0.5 * ppmLineWidths[0] / frequency[0]
                w = - GLDefs.STRINGSCALE * 0.5 * ppmLineWidths[1] / frequency[1]
                stringOffset = (r, w)
            else:
                r = GLDefs.STRINGSCALE * r
                w = GLDefs.STRINGSCALE * w

        if pIndex:
            # get visible/plane status
            _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

            # skip if not visible
            if not _isInPlane and not _isInFlankingPlane:
                return

            if self._isSelected(obj):
                listCol = self._GLParent.highlightColour[:3]
            else:
                if objListView.meritEnabled and obj.figureOfMerit < objListView.meritThreshold:
                    objCol = objListView.meritColour or GLDefs.DEFAULTCOLOUR
                else:
                    objCol = objListView.textColour or GLDefs.DEFAULTCOLOUR

                listCol = getAutoColourRgbRatio(objCol, pls.spectrum,
                                                self.autoColour,
                                                getColours()[CCPNGLWIDGET_FOREGROUND])

            text = self.getLabelling(obj, self._GLParent._symbolLabelling)

            newString = GLString(text=text,
                                 font=self._GLParent.getSmallFont(),
                                 x=p0[0], y=p0[1],
                                 ox=r, oy=w,
                                 colour=(*listCol, fade),
                                 GLContext=self._GLParent,
                                 obj=obj, clearArrays=False)
            newString.stringOffset = stringOffset
            stringList.append(newString)

    def _fillLabels(self, spectrumView, objListView, pls, objectList):
        """Append all labels to the new list
        """
        spectrum = spectrumView.spectrum
        spectrumFrequency = spectrum.spectrometerFrequencies

        # use the first object for referencing
        obj = objectList(pls)[0]

        objPos = obj.ppmPositions
        if not objPos:
            return
        objLineWidths = obj.ppmLineWidths

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        p0 = (objPos[pIndex[0]], objPos[pIndex[1]])
        ppmLineWidths = (objLineWidths[pIndex[0]], objLineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        r, w, symbolType, symbolWidth, _, _ = self._getSymbolWidths(spectrumView)

        stringOffset = None
        if symbolType in (1, 2):
            if ppmLineWidths[0] and ppmLineWidths[1]:
                r = - GLDefs.STRINGSCALE * 0.5 * ppmLineWidths[0] / frequency[0]
                w = - GLDefs.STRINGSCALE * 0.5 * ppmLineWidths[1] / frequency[1]
                stringOffset = (r, w)
            else:
                r = GLDefs.STRINGSCALE * r
                w = GLDefs.STRINGSCALE * w

        if pIndex:

            # get visible/plane status
            _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

            # skip if not visible
            if not _isInPlane and not _isInFlankingPlane:
                return

            if self._isSelected(obj):
                listCol = self._GLParent.highlightColour[:3]
            else:
                if objListView.meritEnabled and obj.figureOfMerit < objListView.meritThreshold:
                    objCol = objListView.meritColour or GLDefs.DEFAULTCOLOUR
                else:
                    objCol = objListView.textColour or GLDefs.DEFAULTCOLOUR

                listCol = getAutoColourRgbRatio(objCol, pls.spectrum,
                                                self.autoColour,
                                                getColours()[CCPNGLWIDGET_FOREGROUND])

            text = self.getLabelling(obj, self._GLParent._symbolLabelling)

            outString = GLString(text=text,
                                 font=self._GLParent.getSmallFont(),
                                 x=p0[0], y=p0[1],
                                 ox=r, oy=w,
                                 colour=(*listCol, fade),
                                 GLContext=self._GLParent,
                                 obj=obj, clearArrays=False)
            outString.stringOffset = stringOffset
            return outString

    def _removeSymbol(self, spectrumView, objListView, delObj):
        """Remove a symbol from the list
        """
        symbolType = self.strip.symbolType

        drawList = self._GLSymbols[objListView]
        self.objIsInVisiblePlanesRemove(spectrumView, delObj)  # probably only needed in create/change

        indexOffset = 0
        numPoints = 0

        pp = 0
        while (pp < len(drawList.pids)):
            # check whether the peaks still exists
            obj = drawList.pids[pp]

            if obj == delObj:
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                if symbolType != 0 and symbolType != 3:  # not a cross/plus
                    numPoints = 2 * numPoints + 5

                # _isInPlane = drawList.pids[pp + 3]
                # _isInFlankingPlane = drawList.pids[pp + 4]
                # _selected = drawList.pids[pp + 5]
                indexStart = drawList.pids[pp + 6]
                indexEnd = drawList.pids[pp + 7]
                indexOffset = indexEnd - indexStart

                drawList.indices = np.delete(drawList.indices, np.s_[indexStart:indexEnd])
                drawList.vertices = np.delete(drawList.vertices, np.s_[2 * offset:2 * (offset + numPoints)])
                drawList.attribs = np.delete(drawList.attribs, np.s_[offset:offset + numPoints])
                drawList.offsets = np.delete(drawList.offsets, np.s_[2 * offset:2 * (offset + numPoints)])

                drawList.colors = np.delete(drawList.colors, np.s_[4 * offset:4 * (offset + numPoints)])
                drawList.pids = np.delete(drawList.pids, np.s_[pp:pp + GLDefs.LENPID])
                drawList.numVertices -= numPoints

                # subtract the offset from all the higher indices to account for the removed points
                drawList.indices[np.where(drawList.indices >= offset)] -= numPoints
                break

            else:
                pp += GLDefs.LENPID

        # clean up the rest of the list
        while (pp < len(drawList.pids)):
            drawList.pids[pp + 1] -= numPoints
            drawList.pids[pp + 6] -= indexOffset
            drawList.pids[pp + 7] -= indexOffset
            pp += GLDefs.LENPID

    _squareSymbol = ((np.array((0, 1, 2, 3), dtype=np.uint32), np.array((0, 1, 2, 3, 0, 2, 2, 1, 0, 3, 3, 1), dtype=np.uint32)),
                     (np.array((0, 4, 4, 3, 3, 0), dtype=np.uint32), np.array((0, 4, 4, 3, 3, 0, 0, 2, 2, 1, 3, 1), dtype=np.uint32)),
                     (np.array((2, 4, 4, 1, 1, 2), dtype=np.uint32), np.array((2, 4, 4, 1, 1, 2, 0, 2, 0, 3, 3, 1), dtype=np.uint32)))
    _squareSymbolLen = tuple(tuple(len(sq) for sq in squareList) for squareList in _squareSymbol)

    def _getSquareSymbolCount(self, planeIndex, obj):
        """returns the number of indices required for the symbol based on the planeIndex
        type of planeIndex - currently 0/1/2 indicating whether normal, infront or behind
        currently visible planes
        """
        return self._squareSymbolLen[planeIndex % 3][self._isSelected(obj)]

    def _makeSquareSymbol(self, drawList, indexEnd, vertexStart, planeIndex, obj):
        """Make a new square symbol based on the planeIndex type.
        """
        _selected = self._isSelected(obj)
        _indices = self._squareSymbol[planeIndex % 3][_selected] + vertexStart
        iCount = len(_indices)
        drawList.indices[indexEnd:indexEnd + iCount] = _indices

        return iCount, _selected

    def _appendSquareSymbol(self, drawList, vertexStart, planeIndex, obj):
        """Append a new square symbol based on the planeIndex type.
        """
        _selected = self._isSelected(obj)
        _indices = self._squareSymbol[planeIndex % 3][_selected] + vertexStart
        iCount = len(_indices)
        drawList.indices = np.append(drawList.indices, _indices)

        return iCount, _selected

    _plusSymbol = ((np.array((5, 6, 7, 8), dtype=np.uint32), np.array((5, 6, 7, 8, 0, 2, 2, 1, 0, 3, 3, 1), dtype=np.uint32)),
                   (np.array((6, 4, 4, 5, 4, 8), dtype=np.uint32), np.array((6, 4, 4, 5, 4, 8, 0, 2, 2, 1, 3, 1, 0, 3), dtype=np.uint32)),
                   (np.array((6, 4, 4, 5, 4, 7), dtype=np.uint32), np.array((6, 4, 4, 5, 4, 7, 0, 2, 2, 1, 3, 1, 0, 3), dtype=np.uint32)))
    _plusSymbolLen = tuple(tuple(len(sq) for sq in squareList) for squareList in _plusSymbol)

    def _getPlusSymbolCount(self, planeIndex, obj):
        """returns the number of indices required for the symbol based on the planeIndex
        type of planeIndex - currently 0/1/2 indicating whether normal, infront or behind
        currently visible planes
        """
        return self._plusSymbolLen[planeIndex % 3][self._isSelected(obj)]

    def _makePlusSymbol(self, drawList, indexEnd, vertexStart, planeIndex, obj):
        """Make a new plus symbol based on the planeIndex type.
        """
        _selected = self._isSelected(obj)
        _indices = self._plusSymbol[planeIndex % 3][_selected] + vertexStart
        iCount = len(_indices)
        drawList.indices[indexEnd:indexEnd + iCount] = _indices

        return iCount, _selected

    def _appendPlusSymbol(self, drawList, vertexStart, planeIndex, obj):
        """Append a new plus symbol based on the planeIndex type.
        """
        _selected = self._isSelected(obj)
        _indices = self._plusSymbol[planeIndex % 3][_selected] + vertexStart
        iCount = len(_indices)
        drawList.indices = np.append(drawList.indices, _indices)

        return iCount, _selected

    def _insertSymbolItem(self, strip, obj, listCol, indexing, r, w,
                          spectrumFrequency, symbolType, drawList, spectrumView, tCount):
        """insert a single symbol to the end of the symbol list
        """

        # indexStart = indexing.start
        indexEnd = indexing.end
        objNum = indexing.objNum
        vertexPtr = indexing.vertexPtr
        vertexStart = indexing.vertexStart

        # get visible/plane status
        _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

        # skip if not visible
        if not _isInPlane and not _isInFlankingPlane:
            return

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            cols = listCol

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]

        objPos = obj.pointPositions
        objLineWidths = obj.pointLineWidths
        p0 = (objPos[pIndex[0]] - 1, objPos[pIndex[1]] - 1)
        pointLineWidths = (objLineWidths[pIndex[0]], objLineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])
        _alias = obj.aliasing
        # alias = 1024 * _alias[pIndex[0]] + _alias[pIndex[1]]
        alias = getAliasSetting(_alias[pIndex[0]], _alias[pIndex[1]])

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if not pIndex:
            # if axisCount != 2:
            getLogger().debug('Bad axisCodes: %s - %s' % (obj.pid, obj.axisCodes))
        else:
            if symbolType == 0 or symbolType == 3:

                # draw a cross
                # keep the cross square at 0.1ppm

                _selected = False
                iCount = 0
                # unselected
                if _isInPlane or _isInFlankingPlane:
                    if symbolType == 0:  # cross
                        iCount, _selected = self._makeSquareSymbol(drawList, indexEnd, vertexStart, planeIndex, obj)
                    else:
                        iCount, _selected = self._makePlusSymbol(drawList, indexEnd, vertexStart, planeIndex, obj)

                # add extra indices
                self._insertSymbolItemVertices(_isInFlankingPlane, _isInPlane, _selected, cols, drawList, fade, iCount, indexing, obj,
                                               objNum, p0, pIndex, planeIndex, r, vertexPtr, w, alias)

            elif symbolType == 1:  # draw an ellipse at lineWidth

                if pointLineWidths[0] and pointLineWidths[1]:
                    # draw 24 connected segments
                    r = 0.5 * pointLineWidths[0]
                    w = 0.5 * pointLineWidths[1]
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

                # # need to subclass the different point types a lot better :|
                # _numPoints = 24
                # _angPlus = 2.0 * np.pi
                # _skip = 1
                # _ang = list(range(numPoints))
                # _indicesLineWidth = np.array(tuple(val for an in _ang for val in ((2 * an), (2 * an) + 1)), dtype=np.uint32)
                # _np1 = len(_indicesLineWidth)
                # _indicesLineWidthSelect = _indicesLineWidth + np.array((_np1, _np1 + 2,
                #                                                         _np1 + 2, _np1 + 1,
                #                                                         _np1, _np1 + 3,
                #                                                         _np1 + 3, _np1 + 1), dtype=np.uint32)
                # _np2 = len(_indicesLineWidthSelect)
                #
                # _vertexLineWidth = np.array(tuple(val for an in _ang
                #                                   for val in (- r * math.sin(_skip * an * _angPlus / _numPoints),
                #                                               - w * math.cos(_skip * an * _angPlus / _numPoints),
                #                                               - r * math.sin((_skip * an + 1) * _angPlus / _numPoints),
                #                                               - w * math.cos((_skip * an + 1) * _angPlus / _numPoints))), dtype=np.float32) + \
                #                    np.array((- r, - w, + r, + w, + r, - w, - r, + w, 0, 0), dtype=np.float32)
                # _vp1 = len(_vertexLineWidth)
                # _vp2 = _vp1 // 2
                #
                # if self._isSelected(obj):
                #     iCount = _np1
                #     drawList.indices[indexEnd:indexEnd + _np1] = _indicesLineWidth + indexStart
                # else:
                #     iCount = _np2
                #     drawList.indices[indexEnd:indexEnd + _np2] = _indicesLineWidthSelect + indexStart
                #
                # _pos = (p0[0], p0[1]) * _vp2
                # drawList.vertices[vertexPtr:vertexPtr + _vp1] = _vertexLineWidth + _pos

                _vertexStart = indexing.vertexStart
                if _isInPlane or _isInFlankingPlane:
                    drawList.indices[indexEnd:indexEnd + np2] = tuple(val for an in ang
                                                                      for val in (_vertexStart + (2 * an), _vertexStart + (2 * an) + 1))

                    iCount = np2
                    if self._isSelected(obj):
                        _selected = True
                        drawList.indices[indexEnd + np2:indexEnd + np2 + 8] = (_vertexStart + np2, _vertexStart + np2 + 2,
                                                                               _vertexStart + np2 + 2, _vertexStart + np2 + 1,
                                                                               _vertexStart + np2, _vertexStart + np2 + 3,
                                                                               _vertexStart + np2 + 3, _vertexStart + np2 + 1)
                        iCount += 8

                # add extra indices
                extraIndices = 0  #self.appendExtraIndices(drawList, indexStart + np2, obj)

                # draw an ellipse at lineWidth
                drawList.vertices[vertexPtr:vertexPtr + 2 * np2] = tuple(val for an in ang
                                                                         for val in (p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                                     p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                                     p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                                                     p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints)))
                drawList.vertices[vertexPtr + 2 * np2:vertexPtr + 2 * np2 + 10] = (p0[0] - r, p0[1] - w,
                                                                                   p0[0] + r, p0[1] + w,
                                                                                   p0[0] + r, p0[1] - w,
                                                                                   p0[0] - r, p0[1] + w,
                                                                                   p0[0], p0[1])

                drawList.colors[2 * vertexPtr:2 * vertexPtr + 4 * np2 + 20] = (*cols, fade) * (np2 + 5)
                drawList.attribs[vertexPtr // 2:(vertexPtr // 2) + np2 + 5] = (alias,) * (np2 + 5)
                drawList.offsets[vertexPtr:vertexPtr + 2 * np2 + 10] = (p0[0], p0[1]) * (np2 + 5)

                # add extra vertices
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (numPoints + extraVertices),
                                                                _isInPlane, _isInFlankingPlane, _selected,
                                                                indexEnd, indexEnd + iCount + extraIndices,
                                                                planeIndex, 0, 0, 0)

                indexing.start += ((np2 + 5) + extraIndices)
                indexing.end += (iCount + extraIndices)  # len(drawList.indices)
                drawList.numVertices += ((np2 + 5) + extraVertices)
                indexing.objNum += GLDefs.LENPID
                indexing.vertexPtr += (2 * ((np2 + 5) + extraVertices))
                indexing.vertexStart += ((np2 + 5) + extraVertices)

            elif symbolType == 2:  # draw a filled ellipse at lineWidth

                if pointLineWidths[0] and pointLineWidths[1]:
                    # draw 24 connected segments
                    r = 0.5 * pointLineWidths[0]  # / frequency[0]
                    w = 0.5 * pointLineWidths[1]  # / frequency[1]
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

                _vertexStart = indexing.vertexStart
                if _isInPlane or _isInFlankingPlane:
                    drawList.indices[indexEnd:indexEnd + 3 * numPoints] = tuple(val for an in ang
                                                                                for val in (_vertexStart + (2 * an), _vertexStart + (2 * an) + 1, _vertexStart + np2 + 4))
                    iCount = 3 * numPoints

                # add extra indices
                extraIndices = 0  #self.appendExtraIndices(drawList, indexStart + np2 + 4, obj)

                # draw an ellipse at lineWidth
                drawList.vertices[vertexPtr:vertexPtr + 2 * np2] = tuple(val for an in ang
                                                                         for val in (p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                                     p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                                     p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                                                     p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints)))
                drawList.vertices[vertexPtr + 2 * np2:vertexPtr + 2 * np2 + 10] = (p0[0] - r, p0[1] - w,
                                                                                   p0[0] + r, p0[1] + w,
                                                                                   p0[0] + r, p0[1] - w,
                                                                                   p0[0] - r, p0[1] + w,
                                                                                   p0[0], p0[1])

                drawList.colors[2 * vertexPtr:2 * vertexPtr + 4 * np2 + 20] = (*cols, fade) * (np2 + 5)
                drawList.attribs[vertexPtr // 2:(vertexPtr // 2) + np2 + 5] = (alias,) * (np2 + 5)
                drawList.offsets[vertexPtr:vertexPtr + 2 * np2 + 10] = (p0[0], p0[1]) * (np2 + 5)

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (numPoints + extraVertices),
                                                                _isInPlane, _isInFlankingPlane, _selected,
                                                                indexEnd, indexEnd + iCount + extraIndices,
                                                                planeIndex, 0, 0, 0)

                indexing.start += ((np2 + 5) + extraIndices)
                indexing.end += (iCount + extraIndices)  # len(drawList.indices)
                drawList.numVertices += ((np2 + 5) + extraVertices)
                indexing.objNum += GLDefs.LENPID
                indexing.vertexPtr += (2 * ((np2 + 5) + extraVertices))
                indexing.vertexStart += ((np2 + 5) + extraVertices)

            else:
                raise ValueError('GL Error: bad symbol type')

    def _insertSymbolItemVertices(self, _isInFlankingPlane, _isInPlane, _selected, cols, drawList, fade, iCount, indexing, obj,
                                  objNum, p0, pIndex, planeIndex, r, vertexPtr, w, alias):

        drawList.vertices[vertexPtr:vertexPtr + self.LENSQ2] = (p0[0] - r, p0[1] - w,
                                                                p0[0] + r, p0[1] + w,
                                                                p0[0] + r, p0[1] - w,
                                                                p0[0] - r, p0[1] + w,
                                                                p0[0], p0[1],
                                                                p0[0], p0[1] - w,
                                                                p0[0], p0[1] + w,
                                                                p0[0] + r, p0[1],
                                                                p0[0] - r, p0[1]
                                                                )
        drawList.colors[2 * vertexPtr:2 * vertexPtr + self.LENSQ4] = (*cols, fade) * self.LENSQ
        drawList.attribs[vertexPtr // 2:(vertexPtr // 2) + self.LENSQ] = (alias,) * self.LENSQ
        drawList.offsets[vertexPtr:vertexPtr + self.LENSQ2] = (p0[0], p0[1]) * self.LENSQ

        # add extra indices
        extraIndices, extraIndexCount = self.insertExtraIndices(drawList, indexing.end + iCount, indexing.start + self.LENSQ, obj)
        # add extra vertices for the multiplet
        extraVertices = self.insertExtraVertices(drawList, vertexPtr + self.LENSQ2, pIndex, obj, p0, (*cols, fade), fade)

        # keep a pointer to the obj
        drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (self.LENSQ + extraVertices),
                                                        _isInPlane, _isInFlankingPlane, _selected,
                                                        indexing.end, indexing.end + iCount + extraIndices,
                                                        planeIndex, 0, 0, 0)

        indexing.start += (self.LENSQ + extraIndexCount)
        indexing.end += (iCount + extraIndices)  # len(drawList.indices)
        drawList.numVertices += (self.LENSQ + extraVertices)
        indexing.objNum += GLDefs.LENPID
        indexing.vertexPtr += (2 * (self.LENSQ + extraVertices))
        indexing.vertexStart += (self.LENSQ + extraVertices)

    # NOTE:ED - new pre-defined indices/vertex lists
    # # indices for lineWidth symbols, not selected/selected in different number of points
    # _lineWidthIndices = {numPoints: ((np.append(np.array(tuple(val for an in range(numPoints) for val in ((2 * an), (2 * an) + 1)), dtype=np.uint32),
    #                                             np.array((0, 1, 2, 3), dtype=np.uint32)),
    #                                   np.append(np.array(tuple(val for an in range(numPoints) for val in ((2 * an), (2 * an) + 1)), dtype=np.uint32),
    #                                             np.array((0, 1, 2, 3, 0, 2, 2, 1, 0, 3, 3, 1), dtype=np.uint32))))
    #                      for numPoints in (12, 18, 24, 36)}
    #
    # # vertices for lineWidth symbols
    # _lineWidthVertices = {numPoints: np.append(np.array(tuple(val for an in range(numPoints)
    #                                                           for val in (- math.sin(skip * an * angPlus / numPoints),
    #                                                                       - math.cos(skip * an * angPlus / numPoints),
    #                                                                       - math.sin((skip * an + 1) * angPlus / numPoints),
    #                                                                       - math.cos((skip * an + 1) * angPlus / numPoints)))),
    #                                            np.array((-1, -1, 1, 1, 1, -1, -1, 1, 0, 0), dtype=np.float32))
    #                       for numPoints, skip, angPlus in ((12),
    #                                                        (18),
    #                                                        (24),
    #                                                        (36))}

    def _appendSymbolItem(self, strip, obj, listCol, indexing, r, w,
                          spectrumFrequency, symbolType, drawList, spectrumView):
        """append a single symbol to the end of the symbol list
        """
        # indexStart, indexEnd are indexes into the drawList.indices for the indices for this symbol
        # indexStart = indexing.start  # indexList[0]
        indexEnd = indexing.end  #indexList[1]
        vertexStart = indexing.vertexStart

        # get visible/plane status
        _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

        # skip if not visible
        if not _isInPlane and not _isInFlankingPlane:
            return

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            cols = listCol

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]

        objPos = obj.pointPositions
        objLineWidths = obj.pointLineWidths

        if not objPos or not objLineWidths:
            getLogger().debug('Object %s contains undefined position' % str(obj.pid))
            return

        p0 = (objPos[pIndex[0]] - 1, objPos[pIndex[1]] - 1)
        pointLineWidths = (objLineWidths[pIndex[0]], objLineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])
        _alias = obj.aliasing
        # alias = 1024 * _alias[pIndex[0]] + _alias[pIndex[1]]
        alias = getAliasSetting(_alias[pIndex[0]], _alias[pIndex[1]])

        if None in p0:
            getLogger().debug('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if not pIndex:
            # if axisCount != 2:
            getLogger().debug('Bad axisCodes: %s - %s' % (obj.pid, obj.axisCodes))
        else:
            if symbolType == 0 or symbolType == 3:

                # draw a cross
                # keep the cross square at 0.1ppm

                _selected = False
                iCount = 0
                if _isInPlane or _isInFlankingPlane:
                    if symbolType == 0:  # cross
                        iCount, _selected = self._appendSquareSymbol(drawList, vertexStart, planeIndex, obj)
                    else:  # plus
                        iCount, _selected = self._appendPlusSymbol(drawList, vertexStart, planeIndex, obj)

                self._appendSymbolItemVertices(_isInFlankingPlane, _isInPlane, _selected, cols, drawList, fade, iCount, indexing,
                                               obj, p0, pIndex, planeIndex, r, w, alias)

            elif symbolType == 1:  # draw an ellipse at lineWidth

                if pointLineWidths[0] and pointLineWidths[1]:
                    # draw 24 connected segments
                    r = 0.5 * pointLineWidths[0]  # / frequency[0]
                    w = 0.5 * pointLineWidths[1]  # / frequency[1]
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
                iCount = 0

                _vertexStart = indexing.vertexStart
                if _isInPlane or _isInFlankingPlane:
                    drawList.indices = np.append(drawList.indices, np.array(tuple(val for an in ang
                                                                                  for val in ((2 * an), (2 * an) + 1)), dtype=np.uint32) + _vertexStart)

                    iCount = np2
                    if self._isSelected(obj):
                        _selected = True
                        drawList.indices = np.append(drawList.indices, np.array((0, 2, 2, 1, 0, 3, 3, 1), dtype=np.uint32) + (_vertexStart + np2))
                        iCount += 8

                # add extra indices for the multiplet
                extraIndices = 0  #self.appendExtraIndices(drawList, indexStart + np2, obj)

                # draw an ellipse at lineWidth
                drawList.vertices = np.append(drawList.vertices, np.array(tuple(val for an in ang
                                                                                for val in (p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                                            p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                                            p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                                                            p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints))),
                                                                          dtype=np.float32))
                drawList.vertices = np.append(drawList.vertices, np.array((p0[0] - r, p0[1] - w,
                                                                           p0[0] + r, p0[1] + w,
                                                                           p0[0] + r, p0[1] - w,
                                                                           p0[0] - r, p0[1] + w,
                                                                           p0[0], p0[1]), dtype=np.float32))

                drawList.colors = np.append(drawList.colors, np.array((*cols, fade) * (np2 + 5), dtype=np.float32))
                drawList.attribs = np.append(drawList.attribs, np.array((alias,) * (np2 + 5), dtype=np.float32))
                drawList.offsets = np.append(drawList.offsets, np.array((p0[0], p0[1]) * (np2 + 5), dtype=np.float32))

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (numPoints + extraVertices),
                                                          _isInPlane, _isInFlankingPlane, _selected,
                                                          indexEnd, indexEnd + iCount + extraIndices,
                                                          planeIndex, 0, 0, 0))
                # indexEnd = len(drawList.indices)

                # indexList[0] += ((np2 + 5) + extraIndices)
                # indexList[1] = len(drawList.indices)
                indexing.start += ((np2 + 5) + extraIndices)
                indexing.end += (iCount + extraIndices)  # len(drawList.indices)
                drawList.numVertices += ((np2 + 5) + extraVertices)
                indexing.vertexStart += ((np2 + 5) + extraVertices)

            elif symbolType == 2:  # draw a filled ellipse at lineWidth

                if pointLineWidths[0] and pointLineWidths[1]:
                    # draw 24 connected segments
                    r = 0.5 * pointLineWidths[0]  # / frequency[0]
                    w = 0.5 * pointLineWidths[1]  # / frequency[1]
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
                iCount = 0

                _vertexStart = indexing.vertexStart
                if _isInPlane or _isInFlankingPlane:
                    drawList.indices = np.append(drawList.indices,
                                                 np.array(tuple(val for an in ang
                                                                for val in ((2 * an), (2 * an) + 1, np2 + 4)), dtype=np.uint32) + _vertexStart)
                    iCount = 3 * numPoints

                # add extra indices for the multiplet
                extraIndices = 0  #self.appendExtraIndices(drawList, indexStart + np2 + 4, obj)

                # draw an ellipse at lineWidth
                drawList.vertices = np.append(drawList.vertices, np.array(tuple(val for an in ang
                                                                                for val in (p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                                            p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                                            p0[0] - r * math.sin((skip * an + 1) * angPlus / numPoints),
                                                                                            p0[1] - w * math.cos((skip * an + 1) * angPlus / numPoints))),
                                                                          dtype=np.float32))

                drawList.vertices = np.append(drawList.vertices, np.array((p0[0] - r, p0[1] - w,
                                                                           p0[0] + r, p0[1] + w,
                                                                           p0[0] + r, p0[1] - w,
                                                                           p0[0] - r, p0[1] + w,
                                                                           p0[0], p0[1]), dtype=np.float32))

                drawList.colors = np.append(drawList.colors, np.array((*cols, fade) * (np2 + 5), dtype=np.float32))
                drawList.attribs = np.append(drawList.attribs, np.array((alias,) * (np2 + 5), dtype=np.float32))
                drawList.offsets = np.append(drawList.offsets, np.array((p0[0], p0[1]) * (np2 + 5), dtype=np.float32))

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (numPoints + extraVertices),
                                                          _isInPlane, _isInFlankingPlane, _selected,
                                                          indexEnd, indexEnd + iCount + extraIndices,
                                                          planeIndex, 0, 0, 0))

                indexing.start += ((np2 + 5) + extraIndices)
                indexing.end += (iCount + extraIndices)
                drawList.numVertices += ((np2 + 5) + extraVertices)
                indexing.vertexStart += ((np2 + 5) + extraVertices)

            else:
                raise ValueError('GL Error: bad symbol type')

    def _appendSymbolItemVertices(self, _isInFlankingPlane, _isInPlane, _selected, cols, drawList, fade, iCount, indexing, obj, p0, pIndex,
                                  planeIndex, r, w, alias):

        drawList.vertices = np.append(drawList.vertices, np.array((p0[0] - r, p0[1] - w,
                                                                   p0[0] + r, p0[1] + w,
                                                                   p0[0] + r, p0[1] - w,
                                                                   p0[0] - r, p0[1] + w,
                                                                   p0[0], p0[1],
                                                                   p0[0], p0[1] - w,
                                                                   p0[0], p0[1] + w,
                                                                   p0[0] + r, p0[1],
                                                                   p0[0] - r, p0[1]
                                                                   ), dtype=np.float32))
        drawList.colors = np.append(drawList.colors, np.array((*cols, fade) * self.LENSQ, dtype=np.float32))
        drawList.attribs = np.append(drawList.attribs, np.array((alias,) * self.LENSQ, dtype=np.float32))
        drawList.offsets = np.append(drawList.offsets, np.array((p0[0], p0[1]) * self.LENSQ, dtype=np.float32))

        # called extraIndices, extraIndexCount above
        # add extra indices
        _indexCount, extraIndices = self.appendExtraIndices(drawList, indexing.vertexStart + self.LENSQ, obj)
        # add extra vertices for the multiplet
        extraVertices = self.appendExtraVertices(drawList, pIndex, obj, p0, (*cols, fade), fade)
        # keep a pointer to the obj
        drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (self.LENSQ + extraVertices),
                                                  _isInPlane, _isInFlankingPlane, _selected,
                                                  indexing.end, indexing.end + iCount + _indexCount, planeIndex, 0, 0, 0))

        indexing.start += (self.LENSQ + extraIndices)
        indexing.end += (iCount + _indexCount)
        drawList.numVertices += (self.LENSQ + extraVertices)
        indexing.vertexStart += (self.LENSQ + extraVertices)

    def _appendSymbol(self, spectrumView, objListView, obj):
        """Append a new symbol to the end of the list
        """
        spectrum = spectrumView.spectrum
        drawList = self._GLSymbols[objListView]
        self.objIsInVisiblePlanesRemove(spectrumView, obj)

        # find the correct scale to draw square pixels
        # don't forget to change when the axes change

        _, _, symbolType, symbolWidth, r, w = self._getSymbolWidths(spectrumView)

        if symbolType == 0 or symbolType == 3:  # a cross/plus

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

        else:
            raise ValueError('GL Error: bad symbol type')

        # build the peaks VBO
        indexing = AttrDict()
        indexing.start = len(drawList.indices)
        indexing.end = len(drawList.indices)
        indexing.vertexStart = drawList.numVertices

        pls = self.objectList(objListView)

        if objListView.meritEnabled and obj.figureOfMerit < objListView.meritThreshold:
            objCol = objListView.meritColour or GLDefs.DEFAULTCOLOUR
        else:
            objCol = objListView.symbolColour or GLDefs.DEFAULTCOLOUR

        listCol = getAutoColourRgbRatio(objCol, pls.spectrum,
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

        pls = self.objectList(objListView)
        listCol = getAutoColourRgbRatio(objListView.textColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])
        meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                         getColours()[CCPNGLWIDGET_FOREGROUND])
        meritEnabled = objListView.meritEnabled
        meritThreshold = objListView.meritThreshold

        for drawStr in drawList.stringList:

            obj = drawStr.stringObject

            if obj and not obj.isDeleted:
                # get visible/plane status
                _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                if _isInPlane or _isInFlankingPlane:

                    if self._isSelected(obj):
                        drawStr.setStringColour((*self._GLParent.highlightColour[:3], fade))
                    else:

                        if meritEnabled and obj.figureOfMerit < meritThreshold:
                            cols = meritCol
                        else:
                            cols = listCol

                        drawStr.setStringColour((*cols, fade))
                    drawStr.updateTextArrayVBOColour()

    def updateHighlightSymbols(self):
        """Respond to an update highlight notifier and update the highlighted symbols/labels
        """
        for spectrumView in self._ordering:

            if spectrumView.isDeleted:
                continue

            for objListView in self.listViews(spectrumView):

                if objListView in self._GLSymbols.keys():
                    self._updateHighlightedSymbols(spectrumView, objListView)
                    self._updateHighlightedLabels(spectrumView, objListView)

    def updateAllSymbols(self):
        """Respond to update all notifier
        """
        for spectrumView in self._ordering:

            if spectrumView.isDeleted:
                continue

            for objListView in self.listViews(spectrumView):

                if objListView in self._GLSymbols.keys():
                    objListView.buildSymbols = True
                    objListView.buildLabels = True

    def _updateHighlightedSymbols(self, spectrumView, objListView):
        """update the highlighted symbols
        """
        strip = self.strip
        symbolType = strip.symbolType

        drawList = self._GLSymbols[objListView]
        drawList.indices = np.empty(0, dtype=np.uint32)

        indexStart = 0
        indexEnd = 0
        vertexStart = 0

        pls = self.objectList(objListView)
        listCol = getAutoColourRgbRatio(objListView.symbolColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])
        meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                         getColours()[CCPNGLWIDGET_FOREGROUND])
        meritEnabled = objListView.meritEnabled
        meritThreshold = objListView.meritThreshold

        if symbolType == 0 or symbolType == 3:

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):

                # check whether the peaks still exists
                obj = drawList.pids[pp]
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                if not obj.isDeleted:
                    _selected = False
                    iCount = 0
                    _indexCount = 0

                    # get visible/plane status
                    _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                    if _isInPlane or _isInFlankingPlane:
                        if symbolType == 0:  # cross
                            iCount, _selected = self._appendSquareSymbol(drawList, vertexStart, planeIndex, obj)
                        else:  # plus
                            iCount, _selected = self._appendPlusSymbol(drawList, vertexStart, planeIndex, obj)

                        if _selected:
                            cols = self._GLParent.highlightColour[:3]
                        else:
                            if meritEnabled and obj.figureOfMerit < meritThreshold:
                                cols = meritCol
                            else:
                                cols = listCol

                        # make sure that links for the multiplets are added
                        _indexCount, extraIndices = self.appendExtraIndices(drawList, indexStart + self.LENSQ, obj)
                        drawList.colors[offset * 4:(offset + self.POINTCOLOURS) * 4] = (*cols, fade) * self.POINTCOLOURS  #numPoints

                    # list MAY contain out of plane peaks
                    drawList.pids[pp + 3:pp + 9] = (_isInPlane, _isInFlankingPlane, _selected,
                                                    indexEnd, indexEnd + iCount + _indexCount, planeIndex)
                    indexEnd += (iCount + _indexCount)

                indexStart += numPoints
                vertexStart += numPoints

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
                    _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                    if _isInPlane or _isInFlankingPlane:
                        drawList.indices = np.append(drawList.indices, np.array(tuple(val for an in ang
                                                                                      for val in (indexStart + (2 * an), indexStart + (2 * an) + 1)), dtype=np.uint32))

                        if self._isSelected(obj):
                            _selected = True
                            cols = self._GLParent.highlightColour[:3]
                            drawList.indices = np.append(drawList.indices, np.array((indexStart + np2, indexStart + np2 + 2,
                                                                                     indexStart + np2 + 2, indexStart + np2 + 1,
                                                                                     indexStart + np2, indexStart + np2 + 3,
                                                                                     indexStart + np2 + 3, indexStart + np2 + 1), dtype=np.uint32))
                        else:
                            if objListView.meritEnabled and obj.figureOfMerit < objListView.meritThreshold:
                                cols = meritCol
                            else:
                                cols = listCol

                        drawList.colors[offset * 4:(offset + np2 + 5) * 4] = (*cols, fade) * (np2 + 5)

                    drawList.pids[pp + 3:pp + 9] = (_isInPlane, _isInFlankingPlane, _selected,
                                                    indexEnd, len(drawList.indices), planeIndex)
                    indexEnd = len(drawList.indices)

                indexStart += np2 + 5

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
                    _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                    if _isInPlane or _isInFlankingPlane:
                        drawList.indices = np.append(drawList.indices, np.array(tuple(val for an in ang
                                                                                      for val in (2 * an, (2 * an) + 1, np2 + 4)),
                                                                                dtype=np.uint32) + indexStart)
                        if self._isSelected(obj):
                            _selected = True
                            cols = self._GLParent.highlightColour[:3]
                        else:
                            if objListView.meritEnabled and obj.figureOfMerit < objListView.meritThreshold:
                                cols = meritCol
                            else:
                                cols = listCol

                        drawList.colors[offset * 4:(offset + np2 + 5) * 4] = (*cols, fade) * (np2 + 5)

                    drawList.pids[pp + 3:pp + 9] = (_isInPlane, _isInFlankingPlane, _selected,
                                                    indexEnd, len(drawList.indices), planeIndex)
                    indexEnd = len(drawList.indices)

                indexStart += np2 + 5

        else:
            raise ValueError('GL Error: bad symbol type')

        drawList.updateIndexVBOIndices()
        drawList.updateTextArrayVBOColour()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Rescaling
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _rescaleSymbolOffsets(self, r, w):
        return np.array([-r, -w, +r, +w, +r, -w, -r, +w, 0, 0, 0, -w, 0, +w, +r, 0, -r, 0], np.float32), self.LENSQ2

    def _rescaleSymbols(self, spectrumView, objListView):
        """rescale symbols when the screen dimensions change
        """
        drawList = self._GLSymbols[objListView]

        if not drawList.numVertices:
            return

        # if drawList.refreshMode == GLREFRESHMODE_REBUILD:

        _, _, symbolType, symbolWidth, r, w = self._getSymbolWidths(spectrumView)

        if symbolType == 0 or symbolType == 3:  # a cross/plus

            offsets, offsetsLENSQ2 = self._rescaleSymbolOffsets(r, w)

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):
                indexStart = 2 * drawList.pids[pp + 1]
                try:
                    drawList.vertices[indexStart:indexStart + offsetsLENSQ2] = drawList.offsets[indexStart:indexStart + offsetsLENSQ2] + offsets
                except:
                    raise RuntimeError('Error _rescaleSymbols')

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
                    indexStart = 2 * drawList.pids[pp + 1]
                    drawList.vertices[indexStart:indexStart + 56] = drawList.offsets[indexStart:indexStart + 56] + offsets

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
                    indexStart = 2 * drawList.pids[pp + 1]
                    drawList.vertices[indexStart:indexStart + 48] = drawList.offsets[indexStart:indexStart + 48] + offsets

        else:
            raise ValueError('GL Error: bad symbol type')

    def _rescaleLabels(self, spectrumView=None, objListView=None, drawList=None):
        """Rescale all labels to the new dimensions of the screen
        """
        r, w, symbolType, symbolWidth, _, _ = self._getSymbolWidths(spectrumView)

        # NOTE:ED - could add in the peakItem offset at this point

        if symbolType == 0 or symbolType == 3:  # a cross/plus

            for drawStr in drawList.stringList:
                drawStr.setStringOffset((r, w))
                drawStr.updateTextArrayVBOAttribs()

        elif symbolType == 1:

            for drawStr in drawList.stringList:
                if drawStr.stringOffset:
                    lr, lw = drawStr.stringOffset
                    drawStr.setStringOffset((lr, lw))
                else:
                    drawStr.setStringOffset((GLDefs.STRINGSCALE * r, GLDefs.STRINGSCALE * w))
                drawStr.updateTextArrayVBOAttribs()

        elif symbolType == 2:

            for drawStr in drawList.stringList:
                if drawStr.stringOffset:
                    lr, lw = drawStr.stringOffset
                    drawStr.setStringOffset((lr, lw))
                else:
                    drawStr.setStringOffset((GLDefs.STRINGSCALE * r, GLDefs.STRINGSCALE * w))
                drawStr.updateTextArrayVBOAttribs()

        else:
            raise ValueError('GL Error: bad symbol type')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Building
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _buildSymbolsCountItem(self, strip, spectrumView, obj, symbolType, tCount):
        """return the number of indices and vertices for the object
        """
        # get visible/plane status
        _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

        # skip if not visible
        if not _isInPlane and not _isInFlankingPlane:
            return 0, 0

        if symbolType == 0:  # draw a cross symbol

            ind = self._getSquareSymbolCount(planeIndex, obj)
            ind += self.extraIndicesCount(obj)
            extraVertices = self.extraVerticesCount(obj)

            vert = (self.LENSQ + extraVertices)
            return ind, vert

        elif symbolType == 3:  # draw a plus symbol

            ind = self._getPlusSymbolCount(planeIndex, obj)
            ind += self.extraIndicesCount(obj)
            extraVertices = self.extraVerticesCount(obj)

            vert = (self.LENSQ + extraVertices)
            return ind, vert

        elif symbolType == 1:  # draw an ellipse at lineWidth

            if obj.pointLineWidths[0] and obj.pointLineWidths[1]:
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

            if obj.pointLineWidths[0] and obj.pointLineWidths[1]:
                numPoints = 24
            else:
                numPoints = 12

            ind = 3 * numPoints
            vert = ((2 * numPoints) + 5)
            return ind, vert

        else:
            raise ValueError('GL Error: bad symbol type')

    def _buildSymbolsCount(self, spectrumView, objListView, drawList):
        """count the number of indices and vertices for the label list
        """

        pls = self.objectList(objListView)

        # reset the object pointers
        self._objectStore = {}

        indCount = 0
        vertCount = 0
        objCount = 0
        for tCount, obj in enumerate(self.objects(pls)):
            ind, vert = self._buildSymbolsCountItem(self.strip, spectrumView, obj, self.strip.symbolType, tCount)
            indCount += ind
            vertCount += vert
            if ind:
                objCount += 1

        # set up arrays
        drawList.indices = np.empty(indCount, dtype=np.uint32)
        drawList.vertices = np.empty(vertCount * 2, dtype=np.float32)
        drawList.colors = np.empty(vertCount * 4, dtype=np.float32)
        drawList.attribs = np.empty(vertCount, dtype=np.float32)
        drawList.offsets = np.empty(vertCount * 2, dtype=np.float32)
        drawList.pids = np.empty(objCount * GLDefs.LENPID, dtype=np.object_)
        drawList.numVertices = 0

        return indCount, vertCount

    def _buildObjIsInVisiblePlanesList(self, spectrumView, objListView):
        """Build the dict of all object is visible values
        """

        objList = self.objectList(objListView)

        # clear the old list for this spectrumView
        if spectrumView in self._objIsInVisiblePlanesCache:
            del self._objIsInVisiblePlanesCache[spectrumView]

        for obj in self.objects(objList):
            self.objIsInVisiblePlanes(spectrumView, obj)

    # from ccpn.util.decorators import profile
    # @profile
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

            drawList.defineAliasedIndexVBO()

        elif drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            # find the correct scale to draw square pixels
            # don't forget to change when the axes change

            _, _, symbolType, symbolWidth, r, w = self._getSymbolWidths(spectrumView)

            if symbolType == 0 or symbolType == 3:  # a cross/plus

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

            else:
                raise ValueError('GL Error: bad symbol type')

            # build the peaks VBO
            indexing = AttrDict()
            indexing.start = 0
            indexing.end = 0
            indexing.vertexPtr = 0
            indexing.vertexStart = 0
            indexing.objNum = 0

            pls = self.objectList(objListView)
            listCol = getAutoColourRgbRatio(objListView.symbolColour or GLDefs.DEFAULTCOLOUR, pls.spectrum,
                                            self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])
            meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, pls.spectrum,
                                             self.autoColour,
                                             getColours()[CCPNGLWIDGET_FOREGROUND])
            meritEnabled = objListView.meritEnabled
            meritThreshold = objListView.meritThreshold

            spectrumFrequency = spectrum.spectrometerFrequencies
            strip = spectrumView.strip

            ind, vert = self._buildSymbolsCount(spectrumView, objListView, drawList)
            if ind:

                for tCount, obj in enumerate(self.objects(pls)):

                    if meritEnabled and obj.figureOfMerit < meritThreshold:
                        cols = meritCol
                    else:
                        cols = listCol

                    self._insertSymbolItem(strip, obj, cols, indexing, r, w,
                                           spectrumFrequency, symbolType, drawList,
                                           spectrumView, tCount)

            drawList.defineAliasedIndexVBO()

    def buildSymbols(self):
        if self.strip.isDeleted:
            return

        # list through the valid peakListViews attached to the strip - including undeleted
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            # for peakListView in spectrumView.peakListViews:
            for objListView in self.listViews(spectrumView):  # spectrumView.peakListViews:

                if objListView.isDeleted or objListView._flaggedForDelete:
                    if objListView in self._objIsInVisiblePlanesCache:
                        del self._objIsInVisiblePlanesCache[objListView]
                    continue

                if objListView in self._GLSymbols:
                    if self._GLSymbols[objListView].renderMode == GLRENDERMODE_RESCALE:
                        self._buildSymbols(spectrumView, objListView)

                if objListView.buildSymbols:
                    objListView.buildSymbols = False

                    # generate the planeVisibility list here - need to integrate with labels
                    self._buildObjIsInVisiblePlanesList(spectrumView, objListView)

                    # set the interior flags for rebuilding the GLdisplay
                    if objListView in self._GLSymbols:
                        self._GLSymbols[objListView].renderMode = GLRENDERMODE_REBUILD

                    self._buildSymbols(spectrumView, objListView)

    def buildLabels(self):
        if self.strip.isDeleted:
            return

        _buildList = []
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            # for peakListView in spectrumView.peakListViews:

            for objListView in self.listViews(spectrumView):
                if objListView.isDeleted:
                    continue

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

        # # # append all labels in one go
        # # self._fillLabels(spectrumView, objListView, tempList, pls, self.objects)
        # print(f'>>> building {len(tempList)} labels')
        # try:
        #     self._tempMax = max(self._tempMax, len(tempList))
        #     print(f'>>> building {len(tempList)} labels  -  {self._tempMax}')
        # except:
        #     self._tempMax = len(tempList)
        #     print(f'>>> building {len(tempList)} labels  -  {self._tempMax}')

        drawList.stringList = tempList
        # drawList.renderMode = GLRENDERMODE_RESCALE

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

    def drawSymbols(self, spectrumSettings, shader=None, stackingMode=True):
        """Draw the symbols to the screen
        """
        if self.strip.isDeleted:
            return

        # self._spectrumSettings = spectrumSettings
        # self.buildSymbols()

        lineThickness = self._GLParent._symbolThickness
        GL.glLineWidth(lineThickness * self._GLParent.viewports.devicePixelRatio)
        shader.setAliasEnabled(self._GLParent._aliasEnabled)

        # change to correct value for shader
        shader.setAliasShade(self._GLParent._aliasShade / 100.0)

        # # loop through the attached objListViews to the strip
        # for spectrumView in self._GLParent._ordering:  #self._parent.spectrumViews:
        #         if spectrumView.isDeleted:
        #             continue
        #     # for peakListView in spectrumView.peakListViews:
        #     for objListView in self.listViews(spectrumView):
        #         if spectrumView.isVisible() and objListView.isVisible():

        for objListView, specView in self._visibleListViews:
            if not objListView.isDeleted and objListView in self._GLSymbols.keys():

                specSettings = self._spectrumSettings[specView]
                pIndex = specSettings[GLDefs.SPECTRUM_POINTINDEX]
                if None in pIndex:
                    continue

                # should move this to buildSpectrumSettings
                # and emit a signal when visibleAliasingRange or foldingModes are changed

                fx0 = specSettings[GLDefs.SPECTRUM_MAXXALIAS]
                # fx1 = specSettings[GLDefs.SPECTRUM_MINXALIAS]
                fy0 = specSettings[GLDefs.SPECTRUM_MAXYALIAS]
                # fy1 = specSettings[GLDefs.SPECTRUM_MINYALIAS]
                dxAF = specSettings[GLDefs.SPECTRUM_DXAF]
                dyAF = specSettings[GLDefs.SPECTRUM_DYAF]
                xScale = specSettings[GLDefs.SPECTRUM_XSCALE]
                yScale = specSettings[GLDefs.SPECTRUM_YSCALE]

                specMatrix = np.array(specSettings[GLDefs.SPECTRUM_MATRIX], dtype=np.float32)

                alias = specView.spectrum.visibleAliasingRange
                folding = specView.spectrum.foldingModes

                for ii in range(alias[pIndex[0]][0], alias[pIndex[0]][1] + 1, 1):
                    for jj in range(alias[pIndex[1]][0], alias[pIndex[1]][1] + 1, 1):

                        foldX = foldY = 1.0
                        foldXOffset = foldYOffset = 0
                        if folding[pIndex[0]] == 'mirror':
                            foldX = pow(-1, ii)
                            foldXOffset = -dxAF if foldX < 0 else 0

                        if folding[pIndex[1]] == 'mirror':
                            foldY = pow(-1, jj)
                            foldYOffset = -dyAF if foldY < 0 else 0

                        specMatrix[0:16] = [xScale * foldX, 0.0, 0.0, 0.0,
                                            0.0, yScale * foldY, 0.0, 0.0,
                                            0.0, 0.0, 1.0, 0.0,
                                            fx0 + (ii * dxAF) + foldXOffset, fy0 + (jj * dyAF) + foldYOffset, 0.0, 1.0]

                        # flipping in the same GL region -  xScale = -xScale
                        #                                   offset = fx0-dxAF
                        # circular -    offset = fx0 + dxAF*alias, alias = min->max
                        shader.setMVMatrix(specMatrix)
                        shader.setAliasPosition(ii, jj)
                        self._GLSymbols[objListView].drawAliasedIndexVBO()

                # if stackingMode:
                #     # use the stacking matrix to offset the 1D spectra
                #     shader.setMVMatrix(spectrumSettings[specView][GLDefs.SPECTRUM_STACKEDMATRIX])
                # # draw the symbols
                # self._GLSymbols[objListView].drawIndexVBO()

        GL.glLineWidth(GLDefs.GLDEFAULTLINETHICKNESS * self._GLParent.viewports.devicePixelRatio)

    def drawLabels(self, spectrumSettings, shader=None, stackingMode=True):
        """Draw the labelling to the screen
        """
        if self.strip.isDeleted:
            return

        # self._spectrumSettings = spectrumSettings
        # self.buildLabels()

        # # loop through the attached peakListViews to the strip
        # for spectrumView in self._GLParent._ordering:  #self._parent.spectrumViews:
        #         if spectrumView.isDeleted:
        #             continue
        #     # for peakListView in spectrumView.peakListViews:
        #     for objListView in self.listViews(spectrumView):
        #         if spectrumView.isVisible() and objListView.isVisible():

        for objListView, specView in self._visibleListViews:
            if not objListView.isDeleted and objListView in self._GLLabels.keys():
                for drawString in self._GLLabels[objListView].stringList:

                    if shader and stackingMode:
                        # use the stacking matrix to offset the 1D spectra
                        shader.setStackOffset(spectrumSettings[specView][GLDefs.SPECTRUM_STACKEDMATRIXOFFSET])

                    # draw text
                    drawString.drawTextArrayVBO()

    def objIsInVisiblePlanesReset(self):
        """Reset the object visibility cache
        """
        self._objIsInVisiblePlanesCache = {}

    def objIsInVisiblePlanesClear(self):
        """clear the object visibility cache for each peak in the spectrumViews
        """
        for specView in self._objIsInVisiblePlanesCache:
            self._objIsInVisiblePlanesCache[specView] = {}

    def objIsInVisiblePlanesRemove(self, spectrumView, obj):
        """Remove a single object from the cache
        """
        try:
            # try to remove from the nested dict
            del self._objIsInVisiblePlanesCache[spectrumView][obj]
        except:
            # nothing needed here
            pass


class GL1dLabelling():
    """Class to handle symbol and symbol labelling for generic 1d displays
    """

    def _updateHighlightedSymbols(self, spectrumView, objListView):
        """update the highlighted symbols
        """

        strip = self.strip
        symbolType = strip.symbolType

        drawList = self._GLSymbols[objListView]
        drawList.indices = np.array([], dtype=np.uint32)

        indexStart = 0
        indexEnd = 0
        vertexStart = 0

        if symbolType == 0 or symbolType == 3:
            listView = self.objectList(objListView)
            listCol = getAutoColourRgbRatio(objListView.symbolColour or GLDefs.DEFAULTCOLOUR, listView.spectrum,
                                            self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])
            meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, listView.spectrum,
                                             self.autoColour,
                                             getColours()[CCPNGLWIDGET_FOREGROUND])
            meritEnabled = objListView.meritEnabled
            meritThreshold = objListView.meritThreshold

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):

                # check whether the peaks still exists
                obj = drawList.pids[pp]
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                if not obj.isDeleted:

                    if symbolType == 0:  # cross
                        iCount, _selected = self._appendSquareSymbol(drawList, vertexStart, 0, obj)
                    else:  # plus
                        iCount, _selected = self._appendPlusSymbol(drawList, vertexStart, 0, obj)

                    if _selected:
                        cols = self._GLParent.highlightColour[:3]
                    else:
                        if meritEnabled and obj.figureOfMerit < meritThreshold:
                            cols = meritCol
                        else:
                            cols = listCol

                    # called extraIndices, extraIndexCount above
                    # make sure that links for the multiplets are added

                    _indexCount, extraIndices = self.appendExtraIndices(drawList, indexStart + self.LENSQ, obj)
                    drawList.colors[offset * 4:(offset + self.POINTCOLOURS) * 4] = (*cols, 1.0) * self.POINTCOLOURS  # numPoints

                    drawList.pids[pp + 3:pp + 9] = (True, True, _selected,
                                                    indexEnd, indexEnd + iCount + _indexCount, 0)  # don't need to change planeIndex, but keep space for it
                    indexEnd += (iCount + _indexCount)

                indexStart += numPoints
                vertexStart += numPoints

            drawList.updateIndexVBOIndices()
            drawList.updateTextArrayVBOColour()

        elif symbolType == 1 or symbolType == 2:
            pass

        else:
            raise ValueError('GL Error: bad symbol type')

    def _insertSymbolItem(self, strip, obj, listCol, indexing, r, w,
                          spectrumFrequency, symbolType, drawList, spectrumView):
        """insert a single symbol to the end of the symbol list
        """

        # indexStart = indexing.start
        indexEnd = indexing.end
        objNum = indexing.objNum
        vertexPtr = indexing.vertexPtr
        vertexStart = indexing.vertexStart

        if not obj:
            return

        objPos = obj.pointPositions
        if not objPos:
            getLogger().warning(f'Object contains undefined position {obj}')
            p0 = (0.0, 0.0)
        else:
            p0 = (objPos[0], obj.height)
            if None in p0:
                getLogger().warning(f'Object {str(obj)} contains undefined position {str(p0)}')
                return

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            cols = listCol

        if symbolType == 0:  # cross
            iCount, _selected = self._makeSquareSymbol(drawList, indexEnd, vertexStart, 0, obj)
        else:
            iCount, _selected = self._makePlusSymbol(drawList, indexEnd, vertexStart, 0, obj)

        self._insertSymbolItemVertices(True, True, _selected, cols, drawList, 1.0, iCount,
                                       indexing, obj, objNum, p0, 0, 0, r, vertexPtr, w, 0.0)

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

            drawList.defineAliasedIndexVBO()

        elif drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            # drawList.refreshMode = GLRENDERMODE_DRAW

            # find the correct scale to draw square pixels
            # don't forget to change when the axes change

            _, _, symbolType, symbolWidth, r, w = self._getSymbolWidths(spectrumView)

            # change the ratio on resize
            drawList.refreshMode = GLREFRESHMODE_REBUILD
            drawList.drawMode = GL.GL_LINES
            drawList.fillMode = None

            # build the peaks VBO
            indexing = AttrDict()
            indexing.start = 0
            indexing.end = 0
            indexing.objNum = 0
            indexing.vertexPtr = 0
            indexing.vertexStart = 0

            pls = self.objectList(objListView)

            listCol = getAutoColourRgbRatio(objListView.symbolColour or GLDefs.DEFAULTCOLOUR, pls.spectrum,
                                            self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])
            meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, pls.spectrum,
                                             self.autoColour,
                                             getColours()[CCPNGLWIDGET_FOREGROUND])
            meritEnabled = objListView.meritEnabled
            meritThreshold = objListView.meritThreshold

            spectrumFrequency = spectrum.spectrometerFrequencies
            strip = spectrumView.strip

            ind, vert = self._buildSymbolsCount(spectrumView, objListView, drawList)
            if ind:
                for tcount, obj in enumerate(self.objects(pls)):

                    if meritEnabled and obj.figureOfMerit < meritThreshold:
                        cols = meritCol
                    else:
                        cols = listCol

                    self._insertSymbolItem(strip, obj, cols, indexing, r, w,
                                           spectrumFrequency, symbolType, drawList,
                                           spectrumView)

            drawList.defineAliasedIndexVBO()

    def _rescaleSymbols(self, spectrumView, objListView):
        """rescale symbols when the screen dimensions change
        """
        drawList = self._GLSymbols[objListView]

        if not drawList.numVertices:
            return

        # if drawList.refreshMode == GLREFRESHMODE_REBUILD:

        _, _, symbolType, symbolWidth, r, w = self._getSymbolWidths(spectrumView)

        if symbolType == 0 or symbolType == 3:  # a cross/plus

            offsets, offsetsLENSQ2 = self._rescaleSymbolOffsets(r, w)

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):
                indexStart = 2 * drawList.pids[pp + 1]
                try:
                    drawList.vertices[indexStart:indexStart + offsetsLENSQ2] = drawList.offsets[indexStart:indexStart + offsetsLENSQ2] + offsets
                except Exception as es:
                    pass

        elif symbolType == 1 or symbolType == 2:
            pass

        else:
            raise ValueError('GL Error: bad symbol type')

    def _appendSymbol(self, spectrumView, objListView, obj):
        """Append a new symbol to the end of the list
        """
        drawList = self._GLSymbols[objListView]

        # find the correct scale to draw square pixels
        # don't forget to change when the axes change

        _, _, symbolType, symbolWidth, r, w = self._getSymbolWidths(spectrumView)

        if symbolType == 0 or symbolType == 3:  # a cross/plus

            # change the ratio on resize
            drawList.refreshMode = GLREFRESHMODE_REBUILD
            drawList.drawMode = GL.GL_LINES
            drawList.fillMode = None

        # build the peaks VBO
        indexing = AttrDict()
        indexing.start = len(drawList.indices)
        indexing.end = len(drawList.indices)
        indexing.vertexStart = drawList.numVertices

        # NOTE:ED - SEEMS TO BE A BUG HERE WITH THE INDEXING BEFORE HIGHLIGHTING!
        #           OTHERWISE 1d and Nd SHOULD BE THE SAME _appendSymbolVertices...
        #           CHECK - but I think solved

        pls = self.objectList(objListView)

        listCol = getAutoColourRgbRatio(objListView.symbolColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])
        meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                         getColours()[CCPNGLWIDGET_FOREGROUND])
        meritEnabled = objListView.meritEnabled
        meritThreshold = objListView.meritThreshold

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            if meritEnabled and obj.figureOfMerit < meritThreshold:
                cols = meritCol
            else:
                cols = listCol

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        if not obj.pointPositions:
            return
        p0 = (obj.pointPositions[pIndex[0]], obj.height)

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if symbolType == 0 or symbolType == 3:  # a cross/plus

            if symbolType == 0:  # cross
                iCount, _selected = self._appendSquareSymbol(drawList, indexing.vertexStart, 0, obj)
            else:  # plus
                iCount, _selected = self._appendPlusSymbol(drawList, indexing.vertexStart, 0, obj)

            self._appendSymbolItemVertices(True, True, _selected, cols, drawList, 1.0, iCount, indexing, obj, p0, pIndex,
                                           0, r, w, 0.0)

    def _removeSymbol(self, spectrumView, objListView, delObj):
        """Remove a symbol from the list
        """

        drawList = self._GLSymbols[objListView]

        indexOffset = 0
        numPoints = 0

        pp = 0
        while (pp < len(drawList.pids)):
            # check whether the peaks still exists
            obj = drawList.pids[pp]

            if obj == delObj:
                offset = drawList.pids[pp + 1]
                numPoints = drawList.pids[pp + 2]

                indexStart = drawList.pids[pp + 6]
                indexEnd = drawList.pids[pp + 7]
                indexOffset = indexEnd - indexStart

                drawList.indices = np.delete(drawList.indices, np.s_[indexStart:indexEnd])
                drawList.vertices = np.delete(drawList.vertices, np.s_[2 * offset:2 * (offset + numPoints)])
                drawList.attribs = np.delete(drawList.attribs, np.s_[offset:offset + numPoints])
                drawList.offsets = np.delete(drawList.offsets, np.s_[2 * offset:2 * (offset + numPoints)])

                drawList.colors = np.delete(drawList.colors, np.s_[4 * offset:4 * (offset + numPoints)])
                drawList.pids = np.delete(drawList.pids, np.s_[pp:pp + GLDefs.LENPID])
                drawList.numVertices -= numPoints

                # subtract the offset from all the higher indices to account for the removed points
                drawList.indices[np.where(drawList.indices >= offset)] -= numPoints
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

        r, w, symbolType, symbolWidth, _, _ = self._getSymbolWidths(spectrumView)

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        if not obj.ppmPositions:
            return
        p0 = (obj.ppmPositions[pIndex[0]], obj.height)

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            listCol = getAutoColourRgbRatio(objListView.textColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])
            meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                             getColours()[CCPNGLWIDGET_FOREGROUND])
            meritEnabled = objListView.meritEnabled
            meritThreshold = objListView.meritThreshold

            if meritEnabled and obj.figureOfMerit < meritThreshold:
                cols = meritCol
            else:
                cols = listCol

        text = self.getLabelling(obj, self._GLParent._symbolLabelling)

        newString = GLString(text=text,
                             font=self._GLParent.getSmallFont(),
                             x=p0[0], y=p0[1],
                             ox=r, oy=w,
                             # ox=symbolWidth, oy=symbolWidth,
                             # x=self._screenZero[0], y=self._screenZero[1]
                             colour=(*cols, 1.0),
                             GLContext=self._GLParent,
                             obj=obj)
        newString.stringOffset = None
        stringList.append(newString)

    def _rescaleLabels(self, spectrumView=None, objListView=None, drawList=None):
        """Rescale all labels to the new dimensions of the screen
        """
        symbolType = self.strip.symbolType

        if symbolType == 0 or symbolType == 3:  # a cross/plus

            r, w, _, symbolWidth, _, _ = self._getSymbolWidths(spectrumView)

            for drawStr in drawList.stringList:
                drawStr.setStringOffset((r, w))
                drawStr.updateTextArrayVBOAttribs()

    # def getObjIsInVisiblePlanes(self, spectrumView, obj):
    #     """Get the current object is in visible planes settings
    #     """
    #     return True, False, 0, 1.0
