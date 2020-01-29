"""
Classes to handle drawing of symbols and symbol labelling to the openGL window
Currently this is peaks and multiplets
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-01-29 09:03:04 +0000 (Wed, January 29, 2020) $"
__version__ = "$Revision: 3.0.0 $"
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
from PyQt5 import QtWidgets
from ccpn.util.Logging import getLogger
import numpy as np
from ccpn.core.Peak import Peak
from ccpn.core.NmrAtom import NmrAtom
from ccpn.util.Colour import getAutoColourRgbRatio
from ccpn.ui.gui.guiSettings import CCPNGLWIDGET_FOREGROUND, CCPNGLWIDGET_INTEGRALSHADE, \
    CCPNGLWIDGET_MULTIPLETLINK, getColours
from ccpn.ui.gui.lib.GuiPeakListView import _getScreenPeakAnnotation, _getPeakAnnotation, _getPeakId
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLFonts import GLString
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLRENDERMODE_DRAW, GLRENDERMODE_RESCALE, GLRENDERMODE_REBUILD, \
    GLREFRESHMODE_NEVER, GLREFRESHMODE_REBUILD, GLSymbolArray, GLLabelArray
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLWidgets import GLIntegralRegion
import ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs as GLDefs

try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)

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
        self._ordering = ()
        self._visibleOrdering = ()
        self._listViews = ()
        self._visibleListViews = ()

        self.autoColour = self._GLParent.SPECTRUMPOSCOLOUR

    def rescale(self):
        if self.resizeGL:
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
                            self._updateHighlightedSymbols(spectrumView, objListView)

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
                        if spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

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
                        if spectrumView in self._ordering:  # strip.spectrumViews:

                            if spectrumView.isDeleted:
                                continue

                            drawList = self._GLLabels[objListView]
                            self._appendLabel(spectrumView, objListView, drawList.stringList, obj)
                            self._rescaleLabels(spectrumView, objListView, drawList)

    def _getSymbolWidths(self):
        """return the required r, w, symbolWidth for the current screen scaling.
        """
        symbolType = self.strip.symbolType
        symbolWidth = self.strip.symbolSize / 2.0

        # pixelX/Y don't update on centre zoom yet
        r = self._GLParent.symbolX
        w = self._GLParent.symbolY

        return r, w, symbolType, symbolWidth

    def _appendLabel(self, spectrumView, objListView, stringList, obj):
        """Append a new label to the end of the list
        """
        if obj.isDeleted:
            return

        if not obj.position:
            return

        spectrum = spectrumView.spectrum
        spectrumFrequency = spectrum.spectrometerFrequencies
        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        p0 = (obj.position[pIndex[0]], obj.position[pIndex[1]])
        lineWidths = (obj.lineWidths[pIndex[0]], obj.lineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        r, w, symbolType, symbolWidth = self._getSymbolWidths()

        stringOffset = None
        if symbolType == 1:
            # put to the top-right corner of the lineWidth
            if lineWidths[0] and lineWidths[1]:
                r = GLDefs.STRINGSCALE * (0.5 * lineWidths[0] / frequency[0])
                w = GLDefs.STRINGSCALE * (0.5 * lineWidths[1] / frequency[1])
                stringOffset = (r, w)
            else:
                r = GLDefs.STRINGSCALE * r
                w = GLDefs.STRINGSCALE * w

        elif symbolType == 2:
            # put to the top-right corner of the lineWidth
            if lineWidths[0] and lineWidths[1]:
                r = GLDefs.STRINGSCALE * (0.5 * lineWidths[0] / frequency[0])
                w = GLDefs.STRINGSCALE * (0.5 * lineWidths[1] / frequency[1])
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
                                 font=self._GLParent.getSmallFont(),  # if _isInPlane else self._GLParent.globalGL.glSmallTransparentFont,
                                 x=p0[0], y=p0[1],
                                 ox=r * np.sign(self._GLParent.pixelX), oy=w * np.sign(self._GLParent.pixelY),
                                 # ox=r, oy=w,
                                 # x=self._screenZero[0], y=self._screenZero[1]
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
        # pls = peakListView.peakList
        # pls = self.objectList(objListView)
        # obj = spectrumView.project.getByPid(objPid) if isinstance(objPid, str) else objPid

        # use the first object for referencing
        obj = objectList(pls)[0]

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        p0 = (obj.position[pIndex[0]], obj.position[pIndex[1]])
        lineWidths = (obj.lineWidths[pIndex[0]], obj.lineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        r, w, symbolType, symbolWidth = self._getSymbolWidths()

        stringOffset = None
        if symbolType == 1:
            if lineWidths[0] and lineWidths[1]:
                r = GLDefs.STRINGSCALE * (0.5 * lineWidths[0] / frequency[0])
                w = GLDefs.STRINGSCALE * (0.5 * lineWidths[1] / frequency[1])
                stringOffset = (r, w)
            else:
                r = GLDefs.STRINGSCALE * r
                w = GLDefs.STRINGSCALE * w

        elif symbolType == 2:
            if lineWidths[0] and lineWidths[1]:
                r = GLDefs.STRINGSCALE * (0.5 * lineWidths[0] / frequency[0])
                w = GLDefs.STRINGSCALE * (0.5 * lineWidths[1] / frequency[1])
                stringOffset = (r, w)
            else:
                r = GLDefs.STRINGSCALE * r
                w = GLDefs.STRINGSCALE * w

        # if axisCount == 2:
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
                                 font=self._GLParent.getSmallFont(),  # if _isInPlane else self._GLParent.globalGL.glSmallTransparentFont,
                                 x=p0[0], y=p0[1],
                                 ox=r * np.sign(self._GLParent.pixelX), oy=w * np.sign(self._GLParent.pixelY),
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
                drawList.attribs = np.delete(drawList.attribs, np.s_[2 * offset:2 * (offset + numPoints)])
                # drawList.offsets = np.delete(drawList.offsets, np.s_[2 * offset:2 * (offset + numPoints)])
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

    def _getSquareSymbolCount(self, planeIndex, obj):
        """returns the number of indices required for the symbol based on the planeIndex
        type of planeIndex - currently 0/1/2 indicating whether normal, infront or behind
        currently visible planes
        """
        _selectedCount = [12, 12, 12]
        _unSelectedCount = [4, 6, 6]

        if self._isSelected(obj):
            return _selectedCount[planeIndex]
        else:
            return _unSelectedCount[planeIndex]

    def _makeSquareSymbol(self, drawList, indexPtr, index, planeIndex, obj):
        """Make a new square symbol based on the planeIndex type.
        """
        _selected = False
        if planeIndex == 1:

            # arrow indicating in the front flanking plane
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 12] = (index, index + 4, index + 4, index + 3, index + 3, index,
                                                            index, index + 2, index + 2, index + 1,
                                                            index + 3, index + 1)
                iCount = 12
            else:
                drawList.indices[indexPtr:indexPtr + 6] = (index, index + 4, index + 4, index + 3, index + 3, index)
                iCount = 6

        elif planeIndex == 2:

            # arrow indicating in the back flanking plane
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 12] = (index + 2, index + 4, index + 4, index + 1, index + 1, index + 2,
                                                            index, index + 2,
                                                            index, index + 3, index + 3, index + 1)
                iCount = 12
            else:
                drawList.indices[indexPtr:indexPtr + 6] = (index + 2, index + 4, index + 4, index + 1, index + 1, index + 2)
                iCount = 6

        else:

            # normal square symbol
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 12] = (index, index + 1, index + 2, index + 3,
                                                            index, index + 2, index + 2, index + 1,
                                                            index, index + 3, index + 3, index + 1)
                iCount = 12
            else:
                drawList.indices[indexPtr:indexPtr + 4] = (index, index + 1, index + 2, index + 3)
                iCount = 4

        return iCount, _selected

    def _appendSquareSymbol(self, drawList, indexPtr, index, planeIndex, obj):
        """Append a new square symbol based on the planeIndex type.
        """
        _selected = False
        if planeIndex == 1:

            # arrow indicating in the front flanking plane
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index, index + 4, index + 4, index + 3, index + 3, index,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index + 3, index + 1), dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index, index + 4, index + 4, index + 3, index + 3, index), dtype=np.uint32))

        elif planeIndex == 2:

            # arrow indicating in the back flanking plane
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index + 2, index + 4, index + 4, index + 1, index + 1, index + 2,
                                                                         index, index + 2,
                                                                         index, index + 3, index + 3, index + 1), dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index + 2, index + 4, index + 4, index + 1, index + 1, index + 2), dtype=np.uint32))

        else:

            # normal square symbol
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index, index + 1, index + 2, index + 3,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index, index + 3, index + 3, index + 1), dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index, index + 1, index + 2, index + 3), dtype=np.uint32))

        return _selected

    def _getPlusSymbolCount(self, planeIndex, obj):
        """returns the number of indices required for the symbol based on the planeIndex
        type of planeIndex - currently 0/1/2 indicating whether normal, infront or behind
        currently visible planes
        """
        _selectedCount = [12, 14, 14]
        _unSelectedCount = [4, 6, 6]

        if self._isSelected(obj):
            return _selectedCount[planeIndex]
        else:
            return _unSelectedCount[planeIndex]

    def _makePlusSymbol(self, drawList, indexPtr, index, planeIndex, obj):
        """Make a new plus symbol based on the planeIndex type.
        """
        _selected = False
        if planeIndex == 1:

            # arrow indicating in the front flanking plane - pointing to the left
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 14] = (index + 6, index + 4, index + 4, index + 5, index + 4, index + 8,
                                                            index, index + 2, index + 2, index + 1,
                                                            index + 3, index + 1, index, index + 3)
                iCount = 14
            else:
                drawList.indices[indexPtr:indexPtr + 6] = (index + 6, index + 4, index + 4, index + 5, index + 4, index + 8)
                iCount = 6

        elif planeIndex == 2:

            # arrow indicating in the back flanking plane - pointing to the right
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 14] = (index + 6, index + 4, index + 4, index + 5, index + 4, index + 7,
                                                            index, index + 2, index + 2, index + 1,
                                                            index + 3, index + 1, index, index + 3)
                iCount = 14
            else:
                drawList.indices[indexPtr:indexPtr + 6] = (index + 6, index + 4, index + 4, index + 5, index + 4, index + 7)
                iCount = 6

        else:

            # normal plus symbol
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 12] = (index + 5, index + 6, index + 7, index + 8,
                                                            index, index + 2, index + 2, index + 1,
                                                            index, index + 3, index + 3, index + 1)
                iCount = 12
            else:
                drawList.indices[indexPtr:indexPtr + 4] = (index + 5, index + 6, index + 7, index + 8)
                iCount = 4

        return iCount, _selected

    def _appendPlusSymbol(self, drawList, indexPtr, index, planeIndex, obj):
        """Append a new plus symbol based on the planeIndex type.
        """
        _selected = False
        if planeIndex == 1:

            # arrow indicating in the front flanking plane - pointing to the left
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index + 6, index + 4, index + 4, index + 5, index + 4, index + 8,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index + 3, index + 1, index, index + 3), dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index + 6, index + 4, index + 4, index + 5, index + 4, index + 8), dtype=np.uint32))

        elif planeIndex == 2:

            # arrow indicating in the back flanking plane - pointing to the right
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index + 6, index + 4, index + 4, index + 5, index + 4, index + 7,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index + 3, index + 1, index, index + 3), dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index + 6, index + 4, index + 4, index + 5, index + 4, index + 7), dtype=np.uint32))

        else:

            # normal plus symbol
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index + 5, index + 6, index + 7, index + 8,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index, index + 3, index + 3, index + 1), dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index + 5, index + 6, index + 7, index + 8), dtype=np.uint32))

        return _selected

    def _insertSymbolItem(self, strip, obj, listCol, indexList, r, w,
                          spectrumFrequency, symbolType, drawList, spectrumView,
                          buildIndex):
        """insert a single symbol to the end of the symbol list
        """

        # tk = time.time()
        # times = [('_', tk)]

        index = indexList[0]
        indexPtr = indexList[1]
        objNum = buildIndex[0]
        vertexPtr = buildIndex[1]

        # times.append(('_col:', time.time()))

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

        # times.append(('_sym:', time.time()))

        p0 = (obj.position[pIndex[0]], obj.position[pIndex[1]])
        lineWidths = (obj.lineWidths[pIndex[0]], obj.lineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])

        # times.append(('_p0:', time.time()))

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
                        iCount, _selected = self._makeSquareSymbol(drawList, indexPtr, index, planeIndex, obj)
                    else:
                        iCount, _selected = self._makePlusSymbol(drawList, indexPtr, index, planeIndex, obj)

                # add extra indices
                self._insertSymbolItemVertices(_isInFlankingPlane, _isInPlane, _selected, buildIndex, cols, drawList, fade, iCount, index, indexList, indexPtr,
                                               obj,
                                               objNum, p0, pIndex, planeIndex, r, vertexPtr, w)

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
                    drawList.indices[indexPtr:indexPtr + np2] = tuple(val for an in ang
                                                                      for val in (index + (2 * an), index + (2 * an) + 1))

                    iCount = np2
                    if self._isSelected(obj):
                        _selected = True
                        drawList.indices[indexPtr + np2:indexPtr + np2 + 8] = (index + np2, index + np2 + 2,
                                                                               index + np2 + 2, index + np2 + 1,
                                                                               index + np2, index + np2 + 3,
                                                                               index + np2 + 3, index + np2 + 1)
                        iCount += 8

                # add extra indices
                extraIndices = 0  #self.appendExtraIndices(drawList, index + np2, obj)

                # draw an ellipse at lineWidth
                drawList.vertices[vertexPtr:vertexPtr + 2 * np2] = tuple(val for an in ang
                                                                         for val in (p0[0] - r * math.sin(skip * an * angPlus / numPoints),
                                                                                     p0[1] - w * math.cos(skip * an * angPlus / numPoints),
                                                                                     p0[0] - r * math.sin(
                                                                                             (skip * an + 1) * angPlus / numPoints),
                                                                                     p0[1] - w * math.cos(
                                                                                             (skip * an + 1) * angPlus / numPoints)))
                drawList.vertices[vertexPtr + 2 * np2:vertexPtr + 2 * np2 + 10] = (p0[0] - r, p0[1] - w,
                                                                                   p0[0] + r, p0[1] + w,
                                                                                   p0[0] + r, p0[1] - w,
                                                                                   p0[0] - r, p0[1] + w,
                                                                                   p0[0], p0[1])

                drawList.colors[2 * vertexPtr:2 * vertexPtr + 4 * np2 + 20] = (*cols, fade) * (np2 + 5)
                drawList.attribs[vertexPtr:vertexPtr + 2 * np2 + 10] = (p0[0], p0[1]) * (np2 + 5)
                # drawList.offsets[vertexPtr:vertexPtr + 2 * np2 + 10] = (p0[0]+r, p0[1]+w) * (np2 + 5)
                # drawList.lineWidths = (0, 0)

                # add extra vertices
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (numPoints + extraVertices),
                                                                _isInPlane, _isInFlankingPlane, _selected,
                                                                indexPtr, len(drawList.indices), planeIndex, 0, 0, 0)

                indexList[0] += ((np2 + 5) + extraIndices)
                indexList[1] += (iCount + extraIndices)  # len(drawList.indices)
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
                    drawList.indices[indexPtr:indexPtr + 3 * numPoints] = tuple(val for an in ang
                                                                                for val in (index + (2 * an), index + (2 * an) + 1, index + np2 + 4))
                    iCount = 3 * numPoints

                # add extra indices
                extraIndices = 0  #self.appendExtraIndices(drawList, index + np2 + 4, obj)

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
                drawList.attribs[vertexPtr:vertexPtr + 2 * np2 + 10] = (p0[0], p0[1]) * (np2 + 5)
                # drawList.offsets[vertexPtr:vertexPtr + 2 * np2 + 10] = (p0[0]+r, p0[1]+w) * (np2 + 5)
                # drawList.lineWidths = (0, 0)

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (numPoints + extraVertices),
                                                                _isInPlane, _isInFlankingPlane, _selected,
                                                                indexPtr, len(drawList.indices), planeIndex, 0, 0, 0)
                # indexPtr = len(drawList.indices)

                indexList[0] += ((np2 + 5) + extraIndices)
                indexList[1] += (iCount + extraIndices)  # len(drawList.indices)
                drawList.numVertices += ((np2 + 5) + extraVertices)
                buildIndex[0] += GLDefs.LENPID
                buildIndex[1] += (2 * ((np2 + 5) + extraVertices))

            else:
                raise ValueError('GL Error: bad symbol type')

        # times.append(('_sym:', time.time()))
        # print(', '.join([str(t[0] + str(t[1] - tk)) for t in times]))

    def _insertSymbolItemVertices(self, _isInFlankingPlane, _isInPlane, _selected, buildIndex, cols, drawList, fade, iCount, index, indexList, indexPtr, obj,
                                  objNum, p0, pIndex, planeIndex, r, vertexPtr, w):
        extraIndices, extraIndexCount = self.insertExtraIndices(drawList, indexPtr + iCount, index + self.LENSQ, obj)
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
        drawList.attribs[vertexPtr:vertexPtr + self.LENSQ2] = (p0[0], p0[1]) * self.LENSQ
        # drawList.offsets[vertexPtr:vertexPtr + self.LENSQ2] = (p0[0]+r, p0[1]+w) * self.LENSQ
        # add extra vertices for the multiplet
        extraVertices = self.insertExtraVertices(drawList, vertexPtr + self.LENSQ2, pIndex, obj, p0, (*cols, fade), fade)
        try:
            # keep a pointer to the obj
            drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (self.LENSQ + extraVertices),
                                                            _isInPlane, _isInFlankingPlane, _selected,
                                                            indexPtr, len(drawList.indices), planeIndex, 0, 0, 0)
        except Exception as es:
            pass
        # times.append(('_pids:', time.time()))
        indexList[0] += (self.LENSQ + extraIndexCount)
        indexList[1] += (iCount + extraIndices)  # len(drawList.indices)
        drawList.numVertices += (self.LENSQ + extraVertices)
        buildIndex[0] += GLDefs.LENPID
        buildIndex[1] += (2 * (self.LENSQ + extraVertices))

    def _appendSymbolItem(self, strip, obj, listCol, indexList, r, w,
                          spectrumFrequency, symbolType, drawList, spectrumView):
        """append a single symbol to the end of the symbol list
        """
        index = indexList[0]
        indexPtr = indexList[1]

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

        if not obj.position or not obj.lineWidths:
            getLogger().debug('Object %s contains undefined position' % str(obj.pid))
            return

        p0 = (obj.position[pIndex[0]], obj.position[pIndex[1]])
        lineWidths = (obj.lineWidths[pIndex[0]], obj.lineWidths[pIndex[1]])
        frequency = (spectrumFrequency[pIndex[0]], spectrumFrequency[pIndex[1]])

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
                # unselected
                if _isInPlane or _isInFlankingPlane:
                    if symbolType == 0:  # cross
                        _selected = self._appendSquareSymbol(drawList, indexPtr, index, planeIndex, obj)
                    else:  # plus
                        _selected = self._appendPlusSymbol(drawList, indexPtr, index, planeIndex, obj)

                self._appendSymbolItemVertices(_isInFlankingPlane, _isInPlane, _selected, cols, drawList, fade, index, indexList, indexPtr, obj, p0, pIndex,
                                               planeIndex, r, w)

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
                    drawList.indices = np.append(drawList.indices, np.array(tuple(val for an in ang
                                                                                  for val in (index + (2 * an), index + (2 * an) + 1)), dtype=np.uint32))

                    if self._isSelected(obj):
                        _selected = True
                        drawList.indices = np.append(drawList.indices, np.array((index + np2, index + np2 + 2,
                                                                                 index + np2 + 2, index + np2 + 1,
                                                                                 index + np2, index + np2 + 3,
                                                                                 index + np2 + 3, index + np2 + 1), dtype=np.uint32))

                # add extra indices for the multiplet
                extraIndices = 0  #self.appendExtraIndices(drawList, index + np2, obj)

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
                drawList.attribs = np.append(drawList.attribs, np.array((p0[0], p0[1]) * (np2 + 5), dtype=np.float32))
                # drawList.offsets = np.append(drawList.offsets, (p0[0]+r, p0[1]+w) * (np2 + 5))
                # drawList.lineWidths = (0, 0)

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (numPoints + extraVertices),
                                                          _isInPlane, _isInFlankingPlane, _selected,
                                                          indexPtr, len(drawList.indices), planeIndex, 0, 0, 0))
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
                                                 np.array(tuple(val for an in ang
                                                                for val in (index + (2 * an), index + (2 * an) + 1, index + np2 + 4)), dtype=np.uint32))

                # add extra indices for the multiplet
                extraIndices = 0  #self.appendExtraIndices(drawList, index + np2 + 4, obj)

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
                drawList.attribs = np.append(drawList.attribs, np.array((p0[0], p0[1]) * (np2 + 5), dtype=np.float32))
                # drawList.offsets = np.append(drawList.offsets, (p0[0]+r, p0[1]+w) * (np2 + 5))
                # drawList.lineWidths = (0, 0)

                # add extra vertices for the multiplet
                extraVertices = 0  #self.appendExtraVertices(drawList, obj, p0, [*cols, fade], fade)

                # keep a pointer to the obj
                drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (numPoints + extraVertices),
                                                          _isInPlane, _isInFlankingPlane, _selected,
                                                          indexPtr, len(drawList.indices), planeIndex, 0, 0, 0))
                # indexPtr = len(drawList.indices)

                indexList[0] += ((np2 + 5) + extraIndices)
                indexList[1] = len(drawList.indices)
                drawList.numVertices += ((np2 + 5) + extraVertices)

            else:
                raise ValueError('GL Error: bad symbol type')

    def _appendSymbolItemVertices(self, _isInFlankingPlane, _isInPlane, _selected, cols, drawList, fade, index, indexList, indexPtr, obj, p0, pIndex,
                                  planeIndex, r, w):
        # add extra indices
        extraIndices = self.appendExtraIndices(drawList, index + self.LENSQ, obj)
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
        drawList.attribs = np.append(drawList.attribs, np.array((p0[0], p0[1]) * self.LENSQ, dtype=np.float32))
        # drawList.offsets = np.append(drawList.offsets, (p0[0]+r, p0[1]+w) * self.LENSQ)
        # add extra vertices for the multiplet
        extraVertices = self.appendExtraVertices(drawList, pIndex, obj, p0, (*cols, fade), fade)
        # keep a pointer to the obj
        drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (self.LENSQ + extraVertices),
                                                  _isInPlane, _isInFlankingPlane, _selected,
                                                  indexPtr, len(drawList.indices), planeIndex, 0, 0, 0))
        # indexPtr = len(drawList.indices)
        indexList[0] += (self.LENSQ + extraIndices)
        indexList[1] = len(drawList.indices)
        drawList.numVertices += (self.LENSQ + extraVertices)

    def _appendSymbol(self, spectrumView, objListView, obj):
        """Append a new symbol to the end of the list
        """
        spectrum = spectrumView.spectrum
        drawList = self._GLSymbols[objListView]

        # find the correct scale to draw square pixels
        # don't forget to change when the axes change

        r, w, symbolType, symbolWidth = self._getSymbolWidths()

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
        # index = 0
        # indexPtr = len(drawList.indices)
        indexing = [len(drawList.indices), len(drawList.indices)]

        # for pls in spectrum.peakLists:

        # pls = peakListView.peakList
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
        strip = self.strip

        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        # if objListView.meritEnabled and obj.figureOfMerit < objListView.meritThreshold:
        #     objCol = objListView.meritColour
        # else:
        #     objCol = objListView.textColour or GLDefs.DEFAULTCOLOUR
        #

        listCol = getAutoColourRgbRatio(objListView.textColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])
        meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                         getColours()[CCPNGLWIDGET_FOREGROUND])
        meritEnabled = objListView.meritEnabled
        meritThreshold = objListView.meritThreshold

        for drawStr in drawList.stringList:

            obj = drawStr.object

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
                    drawStr.updateTextArrayVBOColour(enableVBO=True)

    def updateHighlightSymbols(self):
        """Respond to an update highlight notifier and update the highlighted symbols/labels
        """
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            # for peakListView in spectrumView.peakListViews:
            for objListView in self.listViews(spectrumView):

                if objListView in self._GLSymbols.keys():
                    self._updateHighlightedSymbols(spectrumView, objListView)
                    self._updateHighlightedLabels(spectrumView, objListView)

    def updateAllSymbols(self):
        """Respond to update all notifier
        """
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

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
        # symbolWidth = self._GLParent.symbolSize / 2.0
        # lineThickness = self._GLParent.symbolThickness / 2.0

        drawList = self._GLSymbols[objListView]
        drawList.indices = np.empty(0, dtype=np.uint32)

        index = 0
        indexPtr = 0

        # pls = objListView.peakList
        pls = self.objectList(objListView)

        # if objListView.meritEnabled and obj.figureOfMerit < objListView.meritThreshold:
        #     objCol = objListView.meritColour
        # else:
        #     objCol = objListView.symbolColour or GLDefs.DEFAULTCOLOUR
        #
        # listCol = getAutoColourRgbRatio(objCol, pls.spectrum, self.autoColour,
        #                                 getColours()[CCPNGLWIDGET_FOREGROUND])

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

                    # get visible/plane status
                    _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                    if _isInPlane or _isInFlankingPlane:
                        if symbolType == 0:  # cross
                            _selected = self._appendSquareSymbol(drawList, indexPtr, index, planeIndex, obj)
                        else:  # plus
                            _selected = self._appendPlusSymbol(drawList, indexPtr, index, planeIndex, obj)

                        if _selected:
                            cols = self._GLParent.highlightColour[:3]
                        else:
                            if meritEnabled and obj.figureOfMerit < meritThreshold:
                                cols = meritCol
                            else:
                                cols = listCol

                        # make sure that links for the multiplets are added
                        extraIndices = self.appendExtraIndices(drawList, index + self.LENSQ, obj)
                        drawList.colors[offset * 4:(offset + self.POINTCOLOURS) * 4] = (*cols, fade) * self.POINTCOLOURS  #numPoints

                    # list MAY contain out of plane peaks
                    drawList.pids[pp + 3:pp + 9] = (_isInPlane, _isInFlankingPlane, _selected,
                                                    indexPtr, len(drawList.indices), planeIndex)
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
                    _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                    if _isInPlane or _isInFlankingPlane:
                        drawList.indices = np.append(drawList.indices, np.array(tuple(val for an in ang
                                                                                      for val in (index + (2 * an), index + (2 * an) + 1)), dtype=np.uint32))

                        if self._isSelected(obj):
                            _selected = True
                            cols = self._GLParent.highlightColour[:3]
                            drawList.indices = np.append(drawList.indices, np.array((index + np2, index + np2 + 2,
                                                                                     index + np2 + 2, index + np2 + 1,
                                                                                     index + np2, index + np2 + 3,
                                                                                     index + np2 + 3, index + np2 + 1), dtype=np.uint32))
                        else:
                            if objListView.meritEnabled and obj.figureOfMerit < objListView.meritThreshold:
                                cols = meritCol
                            else:
                                cols = listCol

                        drawList.colors[offset * 4:(offset + np2 + 5) * 4] = (*cols, fade) * (np2 + 5)

                    drawList.pids[pp + 3:pp + 9] = (_isInPlane, _isInFlankingPlane, _selected,
                                                    indexPtr, len(drawList.indices), planeIndex)
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
                    _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

                    if _isInPlane or _isInFlankingPlane:
                        drawList.indices = np.append(drawList.indices, np.array(tuple(val for an in ang
                                                                                      for val in (index + (2 * an), index + (2 * an) + 1, index + np2 + 4)),
                                                                                dtype=np.uint32))
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
                                                    indexPtr, len(drawList.indices), planeIndex)
                    indexPtr = len(drawList.indices)

                index += np2 + 5

        else:
            raise ValueError('GL Error: bad symbol type')

        drawList.updateTextArrayVBOColour(enableVBO=True)

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

        r, w, symbolType, symbolWidth = self._getSymbolWidths()

        if symbolType == 0 or symbolType == 3:  # a cross/plus

            # drawList.clearVertices()
            # drawList.vertices.copy(drawList.attribs)
            # offsets = np.array([-r, -w, +r, +w, +r, -w, -r, +w, 0, 0, 0, -w, 0, +w, +r, 0, -r, 0], np.float32)
            offsets, offsetsLENSQ2 = self._rescaleSymbolOffsets(r, w)

            # for pp in range(0, 2 * drawList.numVertices, self.LENSQ2):
            #     drawList.vertices[pp:pp + self.LENSQ2] = drawList.attribs[pp:pp + self.LENSQ2] + offsets

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):
                index = 2 * drawList.pids[pp + 1]
                try:
                    drawList.vertices[index:index + offsetsLENSQ2] = drawList.attribs[index:index + offsetsLENSQ2] + offsets
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

        else:
            raise ValueError('GL Error: bad symbol type')

    def _rescaleLabels(self, spectrumView=None, objListView=None, drawList=None):
        """Rescale all labels to the new dimensions of the screen
        """
        r, w, symbolType, symbolWidth = self._getSymbolWidths()

        if symbolType == 0 or symbolType == 3:  # a cross/plus

            for drawStr in drawList.stringList:
                drawStr.setStringOffset((r * np.sign(self._GLParent.pixelX), w * np.sign(self._GLParent.pixelY)))
                drawStr.updateTextArrayVBOAttribs(enableVBO=True)

        elif symbolType == 1:

            for drawStr in drawList.stringList:
                if drawStr.stringOffset:
                    lr, lw = drawStr.stringOffset
                    drawStr.setStringOffset((lr * np.sign(self._GLParent.pixelX),
                                             lw * np.sign(self._GLParent.pixelY)))
                else:
                    drawStr.setStringOffset((GLDefs.STRINGSCALE * r * np.sign(self._GLParent.pixelX),
                                             GLDefs.STRINGSCALE * w * np.sign(self._GLParent.pixelY)))
                drawStr.updateTextArrayVBOAttribs(enableVBO=True)

        elif symbolType == 2:

            for drawStr in drawList.stringList:
                if drawStr.stringOffset:
                    lr, lw = drawStr.stringOffset
                    drawStr.setStringOffset((lr * np.sign(self._GLParent.pixelX),
                                             lw * np.sign(self._GLParent.pixelY)))
                else:
                    drawStr.setStringOffset((GLDefs.STRINGSCALE * r * np.sign(self._GLParent.pixelX),
                                             GLDefs.STRINGSCALE * w * np.sign(self._GLParent.pixelY)))
                drawStr.updateTextArrayVBOAttribs(enableVBO=True)

        else:
            raise ValueError('GL Error: bad symbol type')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Building
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def _buildSymbolsCountItem(self, strip, spectrumView, obj, symbolType):
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

        else:
            raise ValueError('GL Error: bad symbol type')

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
        # drawList.offsets = np.empty(vertCount * 2, dtype=np.float32)
        drawList.pids = np.empty(objCount * GLDefs.LENPID, dtype=np.object_)
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

            drawList.defineIndexVBO(enableVBO=True)

        elif drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            # times = [time.time(), self]

            # drawList.clearArrays()

            # find the correct scale to draw square pixels
            # don't forget to change when the axes change

            r, w, symbolType, symbolWidth = self._getSymbolWidths()

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
            # index = 0
            # indexPtr = 0
            indexing = [0, 0]
            buildIndex = [0, 0]

            pls = self.objectList(objListView)

            # if objListView.meritEnabled and obj.figureOfMerit < objListView.meritThreshold:
            #     objCol = objListView.meritColour
            # else:
            #     objCol = objListView.symbolColour or GLDefs.DEFAULTCOLOUR

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

                # tsum = 0
                for tcount, obj in enumerate(self.objects(pls)):

                    if meritEnabled and obj.figureOfMerit < meritThreshold:
                        cols = meritCol
                    else:
                        cols = listCol

                    self._insertSymbolItem(strip, obj, cols, indexing, r, w,
                                           spectrumFrequency, symbolType, drawList,
                                           spectrumView, buildIndex)

            drawList.defineIndexVBO(enableVBO=True)

    def buildSymbols(self):
        if self.strip.isDeleted:
            return

        # list through the valid peakListViews attached to the strip - including undeleted
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            # for peakListView in spectrumView.peakListViews:
            for objListView in self.listViews(spectrumView):  # spectrumView.peakListViews:

                if objListView.isDeleted:
                    continue

                if objListView in self._GLSymbols.keys():
                    if self._GLSymbols[objListView].renderMode == GLRENDERMODE_RESCALE:
                        self._buildSymbols(spectrumView, objListView)

                if objListView.buildSymbols:
                    objListView.buildSymbols = False

                    # set the interior flags for rebuilding the GLdisplay
                    if objListView in self._GLSymbols.keys():
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

        # # append all labels in one go
        # self._fillLabels(spectrumView, objListView, tempList, pls, self.objects)

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

    def drawSymbols(self, spectrumSettings):
        """Draw the symbols to the screen
        """
        if self.strip.isDeleted:
            return

        # self._spectrumSettings = spectrumSettings
        # self.buildSymbols()

        lineThickness = self._GLParent._symbolThickness
        GL.glLineWidth(lineThickness * self._GLParent.viewports._devicePixelRatio)

        # # loop through the attached objListViews to the strip
        # for spectrumView in self._GLParent._ordering:  #self._parent.spectrumViews:
        #         if spectrumView.isDeleted:
        #             continue
        #     # for peakListView in spectrumView.peakListViews:
        #     for objListView in self.listViews(spectrumView):
        #         if spectrumView.isVisible() and objListView.isVisible():

        for objListView, specView in self._visibleListViews:
            if not objListView.isDeleted and objListView in self._GLSymbols.keys():
                # self._GLSymbols[objListView].drawIndexArray()
                self._GLSymbols[objListView].drawIndexVBO(enableVBO=False)

        GL.glLineWidth(1.0 * self._GLParent.viewports._devicePixelRatio)

    def drawLabels(self, spectrumSettings):
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
                    drawString.drawTextArrayVBO(enableVBO=True)
                    # drawString.defineTextArray()


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

    def objIsInVisiblePlanes(self, spectrumView, peak, viewOutOfPlanePeaks=True):
        """Return whether in plane or flanking plane

        :param spectrumView: current spectrumView containing peaks
        :param peak: peak to test
        :param viewOutOfPlanePeaks: whether to show outofplane peaks, defaults to true
        :return: inPlane - true/false
                inFlankingPlane - true/false
                type of outofplane - currently 0/1/2 indicating whether normal, infront or behind
                fade for colouring
        """
        if not peak.position:
            return False, False, 0, 1.0

        displayIndices = spectrumView._displayOrderSpectrumDimensionIndices
        inPlane = True
        endPlane = 0

        # # settings = self._spectrumSettings[spectrumView]
        # pos = peak.position
        # thisVPL = self._GLParent.visiblePlaneListPointValues[spectrumView]
        #
        # for ii, displayIndex in enumerate(displayIndices[2:]):
        #     if displayIndex is not None:
        #
        #         # If no axis matches the index may be None
        #         zPosition = pos[displayIndex]
        #         if not zPosition:
        #             return False, False, 0, 1.0
        #
        #         if not thisVPL:
        #             return False, False, 0, 1.0
        #
        #         planes = thisVPL[ii]
        #         if not (planes and planes[0]):
        #             return False, False, 0, 1.0
        #
        #         visiblePlaneListPointValues = planes[0]
        #         vplLen = len(visiblePlaneListPointValues)
        #
        #         if visiblePlaneListPointValues[1] >= zPosition > visiblePlaneListPointValues[vplLen - 2]:
        #             # return True, False, 0, 1.0
        #             # in the visible region
        #             pass
        #
        #         # exit if don't want to view outOfPlane peaks
        #         elif not viewOutOfPlanePeaks:
        #             return False, False, 0, 1.0
        #
        #         # elif actualPlane == visiblePlaneList[0]:
        #         elif visiblePlaneListPointValues[0] >= zPosition > visiblePlaneListPointValues[1]:
        #             # return False, True, 1, GLDefs.OUTOFPLANEFADE
        #             inPlane = False
        #             endPlane = 1
        #
        #         # elif actualPlane == visiblePlaneList[vplLen - 1]:
        #         elif visiblePlaneListPointValues[vplLen-2] >= zPosition > visiblePlaneListPointValues[vplLen-1]:
        #             # return False, True, 2, GLDefs.OUTOFPLANEFADE
        #             inPlane = False
        #             endPlane = 2
        #
        #         else:
        #             # catch any stray conditions
        #             return False, False, 0, 1.0

        settings = self._spectrumSettings[spectrumView]
        pos = peak.position

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:

                # If no axis matches the index may be None
                zPosition = pos[displayIndex]
                if not zPosition:
                    return False, False, 0, 1.0

                zPointFloat0 = settings[GLDefs.SPECTRUM_VALUETOPOINT][ii](zPosition)
                actualPlane = int(zPointFloat0 + 0.5) - (1 if zPointFloat0 >= 0 else 2)

                thisVPL = self._GLParent.visiblePlaneList[spectrumView]
                if not thisVPL:
                    return False, False, 0, 1.0

                planes = thisVPL[ii]
                if not (planes and planes[0]):
                    return False, False, 0, 1.0

                visiblePlaneList = planes[0]
                vplLen = len(visiblePlaneList)

                if actualPlane in visiblePlaneList[1:vplLen - 1]:
                    # return True, False, 0, 1.0
                    pass

                # exit if don't want to view outOfPlane peaks
                elif not viewOutOfPlanePeaks:
                    return False, False, 0, 1.0

                elif actualPlane == visiblePlaneList[0]:
                    # return False, True, 1, GLDefs.OUTOFPLANEFADE
                    inPlane = False
                    endPlane = 1

                elif actualPlane == visiblePlaneList[vplLen - 1]:
                    # return False, True, 2, GLDefs.OUTOFPLANEFADE
                    inPlane = False
                    endPlane = 2

                else:
                    # catch any stray conditions
                    return False, False, 0, 1.0

        # return True, False, 0, 1.0
        return inPlane, (not inPlane), endPlane, GLDefs.INPLANEFADE if inPlane else GLDefs.OUTOFPLANEFADE

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
        elif labelType == 2:
            # return the original pid
            # text = _getPeakAnnotation(obj)
            text = _getScreenPeakAnnotation(obj, useShortCode=False, usePid=True)
        elif labelType == 3:
            # return the minimal form
            text = _getScreenPeakAnnotation(obj, useShortCode=True, useMinimalCode=True)

        else:
            text = _getPeakId(obj)

        return text

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

    def appendExtraVertices(self, *args):
        """Add extra vertices to the vertex list
        """
        return 0

    def insertExtraIndices(self, *args):
        """Insert extra indices into the vertex list
        """
        return 0, 0

    def insertExtraVertices(self, *args):
        """Insert extra vertices into the vertex list
        """
        return 0

    def _processNotifier(self, data):
        """Process notifiers
        """
        triggers = data[Notifier.TRIGGER]
        obj = data[Notifier.OBJECT]

        if isinstance(obj, Peak):

            # update the peak labelling
            if Notifier.DELETE in triggers:
                self._deleteSymbol(obj)
                self._deleteLabel(obj)

            if Notifier.CREATE in triggers:
                self._createSymbol(obj)
                self._createLabel(obj)

            if Notifier.CHANGE in triggers:
                self._changeSymbol(obj)
                self._changeLabel(obj)

        elif isinstance(obj, NmrAtom):

            # update the labels on the peaks
            for peak in obj.assignedPeaks:
                self._changeSymbol(peak)
                self._changeLabel(peak)


class GLpeakNdLabelling(GLpeakListMethods, GLLabelling):
    """Class to handle symbol and symbol labelling for Nd displays
    """
    pass

    # def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
    #     """Initialise the class
    #     """
    #     super().__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)


class GL1dLabelling():
    """Class to handle symbol and symbol labelling for generic 1d displays
    """

    def _updateHighlightedSymbols(self, spectrumView, objListView):
        """update the highlighted symbols
        """
        spectrum = spectrumView.spectrum
        strip = self.strip

        symbolType = strip.symbolType
        # symbolWidth = self._GLParent._symbolSize / 2.0
        # lineThickness = self._GLParent._symbolThickness / 2.0

        drawList = self._GLSymbols[objListView]
        drawList.indices = np.array([], dtype=np.uint32)

        index = 0
        indexPtr = 0

        if symbolType is not None:
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

                    # _selected = False
                    # if self._isSelected(obj):
                    #     # if hasattr(obj, '_isSelected') and obj._isSelected:
                    #     _selected = True
                    #     cols = self._GLParent.highlightColour[:3]
                    #     drawList.indices = np.append(drawList.indices, np.array((index, index + 1, index + 2, index + 3,
                    #                                                              index, index + 2, index + 2, index + 1,
                    #                                                              index, index + 3, index + 3, index + 1), dtype=np.uint32))
                    # else:
                    #     if meritEnabled and obj.figureOfMerit < meritThreshold:
                    #         cols = meritCol
                    #     else:
                    #         cols = listCol
                    #
                    #     drawList.indices = np.append(drawList.indices, np.array((index, index + 1, index + 2, index + 3), dtype=np.uint32))

                    if symbolType == 0:  # cross
                        _selected = self._appendSquareSymbol(drawList, indexPtr, index, 0, obj)
                    else:  # plus
                        _selected = self._appendPlusSymbol(drawList, indexPtr, index, 0, obj)

                    if _selected:
                        cols = self._GLParent.highlightColour[:3]
                    else:
                        if meritEnabled and obj.figureOfMerit < meritThreshold:
                            cols = meritCol
                        else:
                            cols = listCol

                    # make sure that links for the multiplets are added
                    extraIndices = self.appendExtraIndices(drawList, index + self.LENSQ, obj)
                    drawList.colors[offset * 4:(offset + self.POINTCOLOURS) * 4] = (*cols, 1.0) * self.POINTCOLOURS  # numPoints

                    drawList.pids[pp + 3:pp + 9] = (True, True, _selected,
                                                    indexPtr, len(drawList.indices), 0)  # don't need to change planeIndex, but keep space for it
                    indexPtr = len(drawList.indices)

                index += numPoints

            drawList.updateTextArrayVBOColour(enableVBO=True)

    def _insertSymbolItem(self, strip, obj, listCol, indexList, r, w,
                          spectrumFrequency, symbolType, drawList, spectrumView,
                          buildIndex):
        """insert a single symbol to the end of the symbol list
        """
        index = indexList[0]
        indexPtr = indexList[1]
        objNum = buildIndex[0]
        vertexPtr = buildIndex[1]

        if not (obj and obj.position):
            getLogger().warning('Object contains undefined position')
            p0 = (0.0, 0.0)

        else:
            p0 = (obj.position[0], obj.height)
            if None in p0:
                getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
                return

        # if self._isSelected(obj):
        #     _selected = True
        #     cols = self._GLParent.highlightColour[:3]
        #     drawList.indices[indexPtr:indexPtr + 12] = (index, index + 1, index + 2, index + 3,
        #                                                 index, index + 2, index + 2, index + 1,
        #                                                 index, index + 3, index + 3, index + 1)
        #     iCount = 12
        # else:
        #     _selected = False
        #     cols = listCol
        #     drawList.indices[indexPtr:indexPtr + 4] = (index, index + 1, index + 2, index + 3)
        #     iCount = 4

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            cols = listCol

        if symbolType == 0:  # cross
            iCount, _selected = self._makeSquareSymbol(drawList, indexPtr, index, 0, obj)
        else:
            iCount, _selected = self._makePlusSymbol(drawList, indexPtr, index, 0, obj)

        self._insertSymbolItemVertices(True, True, _selected, buildIndex, cols, drawList, 1.0, iCount, index, indexList, indexPtr, obj, objNum, p0, 0, 0, r,
                                       vertexPtr, w)

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

            drawList.defineIndexVBO(enableVBO=True)

        elif drawList.renderMode == GLRENDERMODE_REBUILD:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode

            # drawList.refreshMode = GLRENDERMODE_DRAW

            # drawList.clearArrays()

            # find the correct scale to draw square pixels
            # don't forget to change when the axes change

            r, w, symbolType, symbolWidth = self._getSymbolWidths()

            # change the ratio on resize
            drawList.refreshMode = GLREFRESHMODE_REBUILD
            drawList.drawMode = GL.GL_LINES
            drawList.fillMode = None

            # build the peaks VBO
            # index = 0
            # indexPtr = 0
            indexing = [0, 0]
            buildIndex = [0, 0]

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
                                           spectrumFrequency, 0, drawList,
                                           spectrumView, buildIndex)

            drawList.defineIndexVBO(enableVBO=True)

    def _rescaleSymbols(self, spectrumView, objListView):
        """rescale symbols when the screen dimensions change
        """
        drawList = self._GLSymbols[objListView]

        if not drawList.numVertices:
            return

        # if drawList.refreshMode == GLREFRESHMODE_REBUILD:

        r, w, symbolType, symbolWidth = self._getSymbolWidths()

        if symbolType is not None:  #== 0:  # a cross
            # drawList.clearVertices()
            # drawList.vertices.copy(drawList.attribs)
            # offsets = np.array([-r, -w, +r, +w, +r, -w, -r, +w, 0, 0, 0, -w, 0, +w, +r, 0, -r, 0], np.float32)
            offsets, offsetsLENSQ2 = self._rescaleSymbolOffsets(r, w)

            # for pp in range(0, 2 * drawList.numVertices, self.LENSQ2):
            #     drawList.vertices[pp:pp + self.LENSQ2] = drawList.attribs[pp:pp + self.LENSQ2] + offsets

            for pp in range(0, len(drawList.pids), GLDefs.LENPID):
                index = 2 * drawList.pids[pp + 1]
                try:
                    drawList.vertices[index:index + offsetsLENSQ2] = drawList.attribs[index:index + offsetsLENSQ2] + offsets
                except Exception as es:
                    pass

    def _appendSymbol(self, spectrumView, objListView, obj):
        """Append a new symbol to the end of the list
        """
        spectrum = spectrumView.spectrum
        drawList = self._GLSymbols[objListView]

        # find the correct scale to draw square pixels
        # don't forget to change when the axes change

        r, w, symbolType, symbolWidth = self._getSymbolWidths()

        if symbolType is not None:  #== 0:  # a cross

            # change the ratio on resize
            drawList.refreshMode = GLREFRESHMODE_REBUILD
            drawList.drawMode = GL.GL_LINES
            drawList.fillMode = None

        # build the peaks VBO
        index = len(drawList.indices)
        indexPtr = len(drawList.indices)
        indexing = [len(drawList.indices), len(drawList.indices)]

        # SEEMS TO BE A BUG HERE WITH THE INDEXING BEFORE HIGHLIGHTING!
        # OTHERWISE 1d and Nd SHOULD BE THE SAME _appendSymbolVertices...

        # for pls in spectrum.peakLists:

        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        spectrumFrequency = spectrum.spectrometerFrequencies
        listCol = getAutoColourRgbRatio(objListView.symbolColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])
        meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                         getColours()[CCPNGLWIDGET_FOREGROUND])
        meritEnabled = objListView.meritEnabled
        meritThreshold = objListView.meritThreshold

        strip = spectrumView.strip
        # get visible/plane status
        _isInPlane, _isInFlankingPlane, planeIndex, fade = self.objIsInVisiblePlanes(spectrumView, obj)

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            if meritEnabled and obj.figureOfMerit < meritThreshold:
                cols = meritCol
            else:
                cols = listCol

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        if not obj.position:
            return
        p0 = (obj.position[pIndex[0]], obj.height)

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if symbolType is not None:  #== 0:

            # draw a cross
            _selected = False
            drawList.indices = np.append(drawList.indices, np.array((index, index + 1, index + 2, index + 3), dtype=np.uint32))

            if self._isSelected(obj):
                # if hasattr(obj, '_isSelected') and obj._isSelected:
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index, index + 2, index + 2, index + 1,
                                                                         index, index + 3, index + 3, index + 1), dtype=np.uint32))

            # self._appendSymbolVertices(_selected, cols, drawList, index, indexPtr, obj, p0, pIndex, r, w)
            self._appendSymbolItemVertices(True, True, _selected, cols, drawList, 1.0, index, indexing, indexPtr, obj, p0, pIndex,
                                           0, r, w)

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
                # drawList.offsets = np.delete(drawList.offsets, np.s_[2 * offset:2 * (offset + numPoints)])
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

        r, w, symbolType, symbolWidth = self._getSymbolWidths()

        pIndex = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]
        if not obj.position:
            return
        p0 = (obj.position[pIndex[0]], obj.height)

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
                             ox=r * np.sign(self._GLParent.pixelX), oy=w * np.sign(self._GLParent.pixelY),
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

        if symbolType is not None:  #== 0:  # a cross

            r, w, _, symbolWidth = self._getSymbolWidths()

            for drawStr in drawList.stringList:
                drawStr.setStringOffset((r * np.sign(self._GLParent.pixelX), w * np.sign(self._GLParent.pixelY)))
                drawStr.updateTextArrayVBOAttribs(enableVBO=True)


class GLpeak1dLabelling(GL1dLabelling, GLpeakNdLabelling):
    """Class to handle symbol and symbol labelling for 1d peak displays
    """
    pass


class GLmultipletListMethods():
    """Class of methods common to 1d and Nd multiplets
    This is added to the Multiplet Classes below and doesn't require an __init__
    """

    LENSQ = GLDefs.LENSQMULT
    LENSQ2 = GLDefs.LENSQ2MULT
    LENSQ4 = GLDefs.LENSQ4MULT
    POINTCOLOURS = GLDefs.POINTCOLOURSMULT

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

    def objIsInVisiblePlanes(self, spectrumView, multiplet, viewOutOfPlaneMultiplets=True):
        """Return whether in plane or flanking plane

        :param spectrumView: current spectrumView containing multiplets
        :param multiplet: multiplet to test
        :param viewOutOfPlaneMultiplets: whether to show outofplane multiplets, defaults to true
        :return: inPlane - true/false
                inFlankingPlane - true/false
                type of outofplane - currently 0/1/2 indicating whether normal, infront or behind
                fade for colouring
        """
        if not multiplet.position:
            return False, False, 0, 1.0

        displayIndices = spectrumView._displayOrderSpectrumDimensionIndices
        inPlane = True
        endPlane = 0

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:

                # If no axis matches the index may be None
                zPosition = multiplet.position[displayIndex]
                if not zPosition:
                    return False, False, 0, 1.0

                settings = self._spectrumSettings[spectrumView]
                actualPlane = int(settings[GLDefs.SPECTRUM_VALUETOPOINT][ii](zPosition) + 0.5) - 1
                planes = (self._GLParent.visiblePlaneList[spectrumView])[ii]

                if not (planes and planes[0]):
                    return False, False, 0, 1.0

                visiblePlaneList = planes[0]
                vplLen = len(visiblePlaneList)

                if actualPlane in visiblePlaneList[1:vplLen - 1]:
                    pass

                # exit if don't want to view outOfPlane multiplets
                elif not viewOutOfPlaneMultiplets:
                    return False, False, 0, 1.0

                elif actualPlane == visiblePlaneList[0]:
                    inPlane = False
                    endPlane = 1

                elif actualPlane == visiblePlaneList[vplLen - 1]:
                    inPlane = False
                    endPlane = 2

                else:
                    # catch any stray conditions
                    return False, False, 0, 1.0

        return inPlane, (not inPlane), endPlane, GLDefs.INPLANEFADE if inPlane else GLDefs.OUTOFPLANEFADE

    def getLabelling(self, obj, labelType):
        """get the object label based on the current labelling method
        """
        return obj.pid

    def extraIndicesCount(self, multiplet):
        """Calculate how many indices to add
        Returns the size of array needed to hold the indices, see insertExtraIndices
        """
        return 2 * len(multiplet.peaks) if multiplet.peaks else 0

    def extraVerticesCount(self, multiplet):
        """Calculate how many vertices to add
        """
        return (len(multiplet.peaks) + 1) if multiplet.peaks else 0

    def appendExtraIndices(self, drawList, index, multiplet):
        """Add extra indices to the index list
        Returns the number of unique indices NOT the length of the appended list
        """
        if not multiplet.peaks:
            return 0

        insertNum = len(multiplet.peaks)
        drawList.indices = np.append(drawList.indices, np.array(tuple(val for ii in range(insertNum)
                                                                      for val in (index, 1 + index + ii)), dtype=np.uint32))
        return insertNum + 1

    def insertExtraIndices(self, drawList, indexPTR, index, multiplet):
        """insert extra indices into the index list
        Returns (len, ind)
            len: length of the inserted array
            ind: number of unique indices
        """
        if not multiplet.peaks:
            return 0, 0

        insertNum = len(multiplet.peaks)
        drawList.indices[indexPTR:indexPTR + 2 * insertNum] = tuple(val for ii in range(insertNum)
                                                                    for val in (index, 1 + index + ii))
        return 2 * insertNum, insertNum + 1

    def _getSquareSymbolCount(self, planeIndex, obj):
        """returns the number of indices required for the symbol based on the planeIndex
        type of planeIndex - currently 0/1/2 indicating whether normal, infront or behind
        currently visible planes
        """
        # _selectedCount = [12, 12, 12]
        # _unSelectedCount = [4, 6, 6]

        _selectedCount = [36, 36, 36]
        _unSelectedCount = [28, 30, 30]

        if self._isSelected(obj):
            return _selectedCount[planeIndex]
        else:
            return _unSelectedCount[planeIndex]

    def _makeSquareSymbol(self, drawList, indexPtr, index, planeIndex, obj):
        """Make a new square symbol based on the planeIndex type.
        """
        _selected = False

        circleVertices = (index + 7, index + 9, index + 9, index + 10, index + 10, index + 6,
                          index + 6, index + 11, index + 11, index + 12, index + 12, index + 8,
                          index + 8, index + 13, index + 13, index + 14, index + 14, index + 5,
                          index + 5, index + 15, index + 15, index + 16, index + 16, index + 7,
                          )

        if planeIndex == 1:

            # arrow indicating in the front flanking plane
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 36] = (index, index + 4, index + 4, index + 3, index + 3, index,
                                                            index, index + 2, index + 2, index + 1,
                                                            index + 3, index + 1) + circleVertices
                iCount = 36
            else:
                drawList.indices[indexPtr:indexPtr + 30] = (index, index + 4, index + 4, index + 3, index + 3, index) + circleVertices
                iCount = 30

        elif planeIndex == 2:

            # arrow indicating in the back flanking plane
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 36] = (index + 2, index + 4, index + 4, index + 1, index + 1, index + 2,
                                                            index, index + 2,
                                                            index, index + 3, index + 3, index + 1) + circleVertices
                iCount = 36
            else:
                drawList.indices[indexPtr:indexPtr + 30] = (index + 2, index + 4, index + 4, index + 1, index + 1, index + 2) + circleVertices
                iCount = 30

        else:

            # normal square symbol
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 36] = (index, index + 1, index + 2, index + 3,
                                                            index, index + 2, index + 2, index + 1,
                                                            index, index + 3, index + 3, index + 1,) + circleVertices
                iCount = 36
            else:
                drawList.indices[indexPtr:indexPtr + 28] = (index, index + 1, index + 2, index + 3,) + circleVertices
                iCount = 28

        return iCount, _selected

    def _appendSquareSymbol(self, drawList, indexPtr, index, planeIndex, obj):
        """Append a new square symbol based on the planeIndex type.
        """
        _selected = False

        circleVertices = (index + 7, index + 9, index + 9, index + 10, index + 10, index + 6,
                          index + 6, index + 11, index + 11, index + 12, index + 12, index + 8,
                          index + 8, index + 13, index + 13, index + 14, index + 14, index + 5,
                          index + 5, index + 15, index + 15, index + 16, index + 16, index + 7,
                          )

        if planeIndex == 1:

            # arrow indicating in the front flanking plane
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index, index + 4, index + 4, index + 3, index + 3, index,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index + 3, index + 1) + circleVertices,
                                                                        dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index, index + 4, index + 4, index + 3, index + 3, index) + circleVertices,
                                                                        dtype=np.uint32))

        elif planeIndex == 2:

            # arrow indicating in the back flanking plane
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index + 2, index + 4, index + 4, index + 1, index + 1, index + 2,
                                                                         index, index + 2,
                                                                         index, index + 3, index + 3, index + 1) + circleVertices,
                                                                        dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index + 2, index + 4, index + 4, index + 1, index + 1, index + 2) + circleVertices,
                                                                        dtype=np.uint32))

        else:

            # normal square symbol
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index, index + 1, index + 2, index + 3,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index, index + 3, index + 3, index + 1,) + circleVertices,
                                                                        dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index, index + 1, index + 2, index + 3,) + circleVertices,
                                                                        dtype=np.uint32))

        return _selected

    def _getPlusSymbolCount(self, planeIndex, obj):
        """returns the number of indices required for the symbol based on the planeIndex
        type of planeIndex - currently 0/1/2 indicating whether normal, infront or behind
        currently visible planes
        """
        # _selectedCount = [12, 14, 14]
        # _unSelectedCount = [4, 6, 6]

        _selectedCount = [36, 38, 38]
        _unSelectedCount = [28, 30, 30]

        if self._isSelected(obj):
            return _selectedCount[planeIndex]
        else:
            return _unSelectedCount[planeIndex]

    def _makePlusSymbol(self, drawList, indexPtr, index, planeIndex, obj):
        """Make a new plus symbol based on the planeIndex type.
        """
        _selected = False

        circleVertices = (index + 7, index + 9, index + 9, index + 10, index + 10, index + 6,
                          index + 6, index + 11, index + 11, index + 12, index + 12, index + 8,
                          index + 8, index + 13, index + 13, index + 14, index + 14, index + 5,
                          index + 5, index + 15, index + 15, index + 16, index + 16, index + 7,
                          )

        if planeIndex == 1:

            # arrow indicating in the front flanking plane - pointing to the left
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 38] = (index + 6, index + 4, index + 4, index + 5, index + 4, index + 8,
                                                            index, index + 2, index + 2, index + 1,
                                                            index + 3, index + 1, index, index + 3) + circleVertices
                iCount = 38
            else:
                drawList.indices[indexPtr:indexPtr + 30] = (index + 6, index + 4, index + 4, index + 5, index + 4, index + 8) + circleVertices
                iCount = 30

        elif planeIndex == 2:

            # arrow indicating in the back flanking plane - pointing to the right
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 38] = (index + 6, index + 4, index + 4, index + 5, index + 4, index + 7,
                                                            index, index + 2, index + 2, index + 1,
                                                            index + 3, index + 1, index, index + 3) + circleVertices
                iCount = 38
            else:
                drawList.indices[indexPtr:indexPtr + 30] = (index + 6, index + 4, index + 4, index + 5, index + 4, index + 7) + circleVertices
                iCount = 30

        else:

            # normal plus symbol
            if self._isSelected(obj):
                _selected = True
                drawList.indices[indexPtr:indexPtr + 36] = (index + 5, index + 6, index + 7, index + 8,
                                                            index, index + 2, index + 2, index + 1,
                                                            index, index + 3, index + 3, index + 1) + circleVertices
                iCount = 36
            else:
                drawList.indices[indexPtr:indexPtr + 28] = (index + 5, index + 6, index + 7, index + 8) + circleVertices
                iCount = 28

        return iCount, _selected

    def _appendPlusSymbol(self, drawList, indexPtr, index, planeIndex, obj):
        """Append a new plus symbol based on the planeIndex type.
        """
        _selected = False

        circleVertices = (index + 7, index + 9, index + 9, index + 10, index + 10, index + 6,
                          index + 6, index + 11, index + 11, index + 12, index + 12, index + 8,
                          index + 8, index + 13, index + 13, index + 14, index + 14, index + 5,
                          index + 5, index + 15, index + 15, index + 16, index + 16, index + 7,
                          )

        if planeIndex == 1:

            # arrow indicating in the front flanking plane - pointing to the left
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index + 6, index + 4, index + 4, index + 5, index + 4, index + 8,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index + 3, index + 1, index, index + 3) + circleVertices,
                                                                        dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index + 6, index + 4, index + 4, index + 5, index + 4, index + 8) + circleVertices,
                                                                        dtype=np.uint32))

        elif planeIndex == 2:

            # arrow indicating in the back flanking plane - pointing to the right
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index + 6, index + 4, index + 4, index + 5, index + 4, index + 7,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index + 3, index + 1, index, index + 3) + circleVertices,
                                                                        dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index + 6, index + 4, index + 4, index + 5, index + 4, index + 7) + circleVertices,
                                                                        dtype=np.uint32))

        else:

            # normal plus symbol
            if self._isSelected(obj):
                _selected = True
                drawList.indices = np.append(drawList.indices, np.array((index + 5, index + 6, index + 7, index + 8,
                                                                         index, index + 2, index + 2, index + 1,
                                                                         index, index + 3, index + 3, index + 1) + circleVertices,
                                                                        dtype=np.uint32))
            else:
                drawList.indices = np.append(drawList.indices, np.array((index + 5, index + 6, index + 7, index + 8) + circleVertices,
                                                                        dtype=np.uint32))

        return _selected

    def _rescaleSymbolOffsets(self, r, w):
        return np.array([-r, -w, +r, +w, +r, -w, -r, +w, 0, 0, 0, -w, 0, +w, +r, 0, -r, 0,
                         r * 0.85, w * 0.50,
                         r * 0.5, w * 0.85,
                         - r * 0.5, w * 0.85,
                         - r * 0.85, w * 0.50,
                         - r * 0.85, - w * 0.50,
                         - r * 0.5, - w * 0.85,
                         + r * 0.5, - w * 0.85,
                         + r * 0.85, - w * 0.50, ], np.float32), self.LENSQ2

    # class GLmultipletNdLabelling(GLmultipletListMethods, GLLabelling):  #, GLpeakNdLabelling):
    #     """Class to handle symbol and symbol labelling for Nd displays
    #     """
    #
    #     def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
    #         """Initialise the class
    #         """
    #         super(GLmultipletNdLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)
    #
    #         self.autoColour = self._GLParent.SPECTRUMNEGCOLOUR

    def appendExtraVertices(self, drawList, pIndex, multiplet, p0, colour, fade):
        """Add extra vertices to the vertex list
        """
        if not multiplet.peaks:
            return 0

        # cols = getColours()[CCPNGLWIDGET_MULTIPLETLINK][:3]
        col = multiplet.multipletList.lineColour
        cols = getAutoColourRgbRatio(col or DEFAULTLINECOLOUR, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = p0

        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes

            p1 = (peak.position[pIndex[0]], peak.position[pIndex[1]])

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                continue

            posList += p1

        numVertices = len(multiplet.peaks) + 1  # len(posList)
        drawList.vertices = np.append(drawList.vertices, np.array(posList, dtype=np.float32))
        drawList.colors = np.append(drawList.colors, np.array((*cols, fade) * numVertices, dtype=np.float32))
        drawList.attribs = np.append(drawList.attribs, np.array(p0 * numVertices, dtype=np.float32))
        # drawList.offsets = np.append(drawList.offsets, p0 * numVertices)

        return numVertices

    def insertExtraVertices(self, drawList, vertexPTR, pIndex, multiplet, p0, colour, fade):
        """insert extra vertices into the vertex list
        """
        if not multiplet.peaks:
            return 0

        # cols = getColours()[CCPNGLWIDGET_MULTIPLETLINK][:3]
        col = multiplet.multipletList.lineColour
        cols = getAutoColourRgbRatio(col or DEFAULTLINECOLOUR, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = p0

        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes

            p1 = (peak.position[pIndex[0]], peak.position[pIndex[1]])

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                continue

            posList += p1

        numVertices = len(multiplet.peaks) + 1
        # drawList.vertices = np.append(drawList.vertices, posList)
        # drawList.colors = np.append(drawList.colors, (*cols, fade) * numVertices)
        # drawList.attribs = np.append(drawList.attribs, p0 * numVertices)

        drawList.vertices[vertexPTR:vertexPTR + 2 * numVertices] = posList
        drawList.colors[2 * vertexPTR:2 * vertexPTR + 4 * numVertices] = (*cols, fade) * numVertices
        drawList.attribs[vertexPTR:vertexPTR + 2 * numVertices] = p0 * numVertices
        # drawList.offsets[vertexPTR:vertexPTR + 2 * numVertices] = p0 * numVertices

        return numVertices

    def _insertSymbolItemVertices(self, _isInFlankingPlane, _isInPlane, _selected, buildIndex, cols, drawList, fade, iCount, index, indexList, indexPtr, obj,
                                  objNum, p0, pIndex, planeIndex, r, vertexPtr, w):
        extraIndices, extraIndexCount = self.insertExtraIndices(drawList, indexPtr + iCount, index + self.LENSQ, obj)
        drawList.vertices[vertexPtr:vertexPtr + self.LENSQ2] = (p0[0] - r, p0[1] - w,
                                                                p0[0] + r, p0[1] + w,
                                                                p0[0] + r, p0[1] - w,
                                                                p0[0] - r, p0[1] + w,
                                                                p0[0], p0[1],
                                                                p0[0], p0[1] - w,
                                                                p0[0], p0[1] + w,
                                                                p0[0] + r, p0[1],
                                                                p0[0] - r, p0[1],
                                                                p0[0] + (r * 0.85), p0[1] + (w * 0.50),
                                                                p0[0] + (r * 0.5), p0[1] + (w * 0.85),
                                                                p0[0] - (r * 0.5), p0[1] + (w * 0.85),
                                                                p0[0] - (r * 0.85), p0[1] + (w * 0.50),
                                                                p0[0] - (r * 0.85), p0[1] - (w * 0.50),
                                                                p0[0] - (r * 0.5), p0[1] - (w * 0.85),
                                                                p0[0] + (r * 0.5), p0[1] - (w * 0.85),
                                                                p0[0] + (r * 0.85), p0[1] - (w * 0.50),
                                                                )
        drawList.colors[2 * vertexPtr:2 * vertexPtr + self.LENSQ4] = (*cols, fade) * self.LENSQ
        drawList.attribs[vertexPtr:vertexPtr + self.LENSQ2] = (p0[0], p0[1]) * self.LENSQ
        # drawList.offsets[vertexPtr:vertexPtr + self.LENSQ2] = (p0[0]+r, p0[1]+w) * self.LENSQ
        # add extra vertices for the multiplet
        extraVertices = self.insertExtraVertices(drawList, vertexPtr + self.LENSQ2, pIndex, obj, p0, (*cols, fade), fade)
        try:
            # keep a pointer to the obj
            drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (self.LENSQ + extraVertices),
                                                            _isInPlane, _isInFlankingPlane, _selected,
                                                            indexPtr, len(drawList.indices), planeIndex, 0, 0, 0)
        except Exception as es:
            pass
        # times.append(('_pids:', time.time()))
        indexList[0] += (self.LENSQ + extraIndexCount)
        indexList[1] += (iCount + extraIndices)  # len(drawList.indices)
        drawList.numVertices += (self.LENSQ + extraVertices)
        buildIndex[0] += GLDefs.LENPID
        buildIndex[1] += (2 * (self.LENSQ + extraVertices))

    def _appendSymbolItemVertices(self, _isInFlankingPlane, _isInPlane, _selected, cols, drawList, fade, index, indexList, indexPtr, obj, p0, pIndex,
                                  planeIndex, r, w):
        # add extra indices
        extraIndices = self.appendExtraIndices(drawList, index + self.LENSQ, obj)
        drawList.vertices = np.append(drawList.vertices, np.array((p0[0] - r, p0[1] - w,
                                                                   p0[0] + r, p0[1] + w,
                                                                   p0[0] + r, p0[1] - w,
                                                                   p0[0] - r, p0[1] + w,
                                                                   p0[0], p0[1],
                                                                   p0[0], p0[1] - w,
                                                                   p0[0], p0[1] + w,
                                                                   p0[0] + r, p0[1],
                                                                   p0[0] - r, p0[1],
                                                                   p0[0] + (r * 0.85), p0[1] + (w * 0.50),
                                                                   p0[0] + (r * 0.5), p0[1] + (w * 0.85),
                                                                   p0[0] - (r * 0.5), p0[1] + (w * 0.85),
                                                                   p0[0] - (r * 0.85), p0[1] + (w * 0.50),
                                                                   p0[0] - (r * 0.85), p0[1] - (w * 0.50),
                                                                   p0[0] - (r * 0.5), p0[1] - (w * 0.85),
                                                                   p0[0] + (r * 0.5), p0[1] - (w * 0.85),
                                                                   p0[0] + (r * 0.85), p0[1] - (w * 0.50),
                                                                   ), dtype=np.float32))
        drawList.colors = np.append(drawList.colors, np.array((*cols, fade) * self.LENSQ, dtype=np.float32))
        drawList.attribs = np.append(drawList.attribs, np.array((p0[0], p0[1]) * self.LENSQ, dtype=np.float32))
        # drawList.offsets = np.append(drawList.offsets, (p0[0]+r, p0[1]+w) * self.LENSQ)
        # add extra vertices for the multiplet
        extraVertices = self.appendExtraVertices(drawList, pIndex, obj, p0, (*cols, fade), fade)
        # keep a pointer to the obj
        drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (self.LENSQ + extraVertices),
                                                  _isInPlane, _isInFlankingPlane, _selected,
                                                  indexPtr, len(drawList.indices), planeIndex, 0, 0, 0))
        # indexPtr = len(drawList.indices)
        indexList[0] += (self.LENSQ + extraIndices)
        indexList[1] = len(drawList.indices)
        drawList.numVertices += (self.LENSQ + extraVertices)


class GLmultipletNdLabelling(GLmultipletListMethods, GLLabelling):  #, GLpeakNdLabelling):
    """Class to handle symbol and symbol labelling for Nd displays
    """

    def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
        """Initialise the class
        """
        super(GLmultipletNdLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)

        # use different colouring
        self.autoColour = self._GLParent.SPECTRUMNEGCOLOUR


class GLmultiplet1dLabelling(GL1dLabelling, GLmultipletNdLabelling):
    """Class to handle symbol and symbol labelling for 1d displays
    """

    # def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
    #     """Initialise the class
    #     """
    #     super(GLmultiplet1dLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)
    #
    #     self.autoColour = self._GLParent.SPECTRUMNEGCOLOUR

    def appendExtraVertices(self, drawList, pIndex, multiplet, p0, colour, fade):
        """Add extra vertices to the vertex list
        """
        if not multiplet.peaks:
            return 0

        # cols = getColours()[CCPNGLWIDGET_MULTIPLETLINK][:3]
        col = multiplet.multipletList.lineColour
        cols = getAutoColourRgbRatio(col if col else DEFAULTLINECOLOUR, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = p0
        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes

            p1 = (peak.position[pIndex[0]], peak.height)

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                continue

            posList += p1

        numVertices = len(multiplet.peaks) + 1
        drawList.vertices = np.append(drawList.vertices, np.array(posList, dtype=np.float32))
        drawList.colors = np.append(drawList.colors, np.array((*cols, fade) * numVertices, dtype=np.float32))
        drawList.attribs = np.append(drawList.attribs, np.array(p0 * numVertices, dtype=np.float32))
        # drawList.offsets = np.append(drawList.attribs, p0 * numVertices)

        return numVertices

    def insertExtraVertices(self, drawList, vertexPTR, pIndex, multiplet, p0, colour, fade):
        """insert extra vertices into the vertex list
        """
        if not multiplet.peaks:
            return 0

        # cols = getColours()[CCPNGLWIDGET_MULTIPLETLINK][:3]
        col = multiplet.multipletList.lineColour
        cols = getAutoColourRgbRatio(col or DEFAULTLINECOLOUR, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = p0

        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes

            p1 = (peak.position[pIndex], peak.height)

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                continue

            posList += p1

        numVertices = len(multiplet.peaks) + 1
        # drawList.vertices = np.append(drawList.vertices, posList)
        # drawList.colors = np.append(drawList.colors, (*cols, fade) * numVertices)
        # drawList.attribs = np.append(drawList.attribs, p0 * numVertices)

        drawList.vertices[vertexPTR:vertexPTR + 2 * numVertices] = posList
        drawList.colors[2 * vertexPTR:2 * vertexPTR + 4 * numVertices] = (*cols, fade) * numVertices
        drawList.attribs[vertexPTR:vertexPTR + 2 * numVertices] = p0 * numVertices
        # drawList.offsets[vertexPTR:vertexPTR + 2 * numVertices] = p0 * numVertices

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

    def extraIndicesCount(self, integral):
        """Calculate how many indices to add
        """
        return 0

    def appendExtraIndices(self, *args):
        """Add extra indices to the index list
        """
        return 0

    def extraVerticesCount(self, integral):
        """Calculate how many vertices to add
        """
        return 0

    def appendExtraVertices(self, *args):
        """Add extra vertices to the vertex list
        """
        return 0

    def insertExtraIndices(self, *args):
        """Insert extra indices into the vertex list
        """
        return 0, 0

    def insertExtraVertices(self, *args):
        """Insert extra vertices into the vertex list
        """
        return 0

    def rescaleIntegralLists(self):
        for il in self._GLSymbols.values():
            il._rescale()


class GLintegralNdLabelling(GL1dLabelling, GLintegralListMethods, GLLabelling):  #, GLpeakNdLabelling):
    """Class to handle symbol and symbol labelling for Nd displays
    """

    # def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
    #     """Initialise the class
    #     """
    #     super(GLintegralNdLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)

    def _updateHighlightedSymbols(self, spectrumView, integralListView):
        drawList = self._GLSymbols[integralListView]
        drawList._rebuild()
        drawList.updateTextArrayVBOColour(enableVBO=True)

    def _updateHighlightedLabels(self, spectrumView, objListView):
        if objListView not in self._GLLabels:
            return

        drawList = self._GLLabels[objListView]
        strip = self.strip

        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        listCol = getAutoColourRgbRatio(objListView.textColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                        getColours()[CCPNGLWIDGET_FOREGROUND])
        meritCol = getAutoColourRgbRatio(objListView.meritColour or GLDefs.DEFAULTCOLOUR, pls.spectrum, self.autoColour,
                                         getColours()[CCPNGLWIDGET_FOREGROUND])
        meritEnabled = objListView.meritEnabled
        meritThreshold = objListView.meritThreshold

        for drawStr in drawList.stringList:

            obj = drawStr.object

            if obj and not obj.isDeleted:

                if self._isSelected(obj):
                    drawStr.setStringColour((*self._GLParent.highlightColour[:3], GLDefs.INPLANEFADE))
                else:
                    if meritEnabled and obj.figureOfMerit < meritThreshold:
                        cols = meritCol
                    else:
                        cols = listCol
                    drawStr.setStringColour((*cols, GLDefs.INPLANEFADE))

                drawStr.updateTextArrayVBOColour(enableVBO=True)

    def drawSymbols(self, spectrumSettings):
        if self.strip.isDeleted:
            return

        self._spectrumSettings = spectrumSettings
        self.buildSymbols()

        for integralListView, specView in self._visibleListViews:
            if not integralListView.isDeleted and integralListView in self._GLSymbols.keys():

                # draw the integralAreas if they exist
                for integralArea in self._GLSymbols[integralListView]._regions:
                    if hasattr(integralArea, '_integralArea'):
                        if self._GLParent._stackingMode:
                            # use the stacking matrix to offset the 1D spectra
                            self._GLParent.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
                                                                                          1, GL.GL_FALSE,
                                                                                          self._GLParent._spectrumSettings[
                                                                                              specView][
                                                                                              GLDefs.SPECTRUM_STACKEDMATRIX])

                        # draw the actual integral areas
                        integralArea._integralArea.drawVertexColorVBO(enableVBO=True)

        self._GLParent.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix', 1, GL.GL_FALSE, self._GLParent._IMatrix)

    def drawSymbolRegions(self, spectrumSettings):
        if self.strip.isDeleted:
            return

        self._spectrumSettings = spectrumSettings
        self.buildSymbols()

        for integralListView, specView in self._visibleListViews:
            if not integralListView.isDeleted and integralListView in self._GLSymbols.keys():
                # draw the boxes around the highlighted integral areas - multisampling not required here
                self._GLSymbols[integralListView].drawIndexVBO(enableVBO=True)

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

                drawStr.updateTextArrayVBOAttribs(enableVBO=True)

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
            # listCol = getAutoColourRgbRatio(ils.symbolColour, ils.spectrum, self.autoColour,
            #                                 getColours()[CCPNGLWIDGET_FOREGROUND])

            listCol = getAutoColourRgbRatio(integralListView.symbolColour or GLDefs.DEFAULTCOLOUR, ils.spectrum, self.autoColour,
                                            getColours()[CCPNGLWIDGET_FOREGROUND])
            meritCol = getAutoColourRgbRatio(integralListView.meritColour or GLDefs.DEFAULTCOLOUR, ils.spectrum, self.autoColour,
                                             getColours()[CCPNGLWIDGET_FOREGROUND])
            meritEnabled = integralListView.meritEnabled
            meritThreshold = integralListView.meritThreshold

            for integral in ils.integrals:
                if meritEnabled and integral.figureOfMerit < meritThreshold:
                    cols = meritCol
                else:
                    cols = listCol

                drawList.addIntegral(integral, integralListView, colour=None,
                                     brush=(*cols, CCPNGLWIDGET_INTEGRALSHADE))

            drawList.defineIndexVBO(enableVBO=True)

        elif drawList.renderMode == GLRENDERMODE_RESCALE:
            drawList.renderMode = GLRENDERMODE_DRAW  # back to draw mode
            drawList._rebuildIntegralAreas()

            drawList.defineIndexVBO(enableVBO=True)

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
                ilv = ils.integralListView
                # listCol = getAutoColourRgbRatio(il.symbolColour,
                #                                 il.spectrum, self._GLParent.SPECTRUMPOSCOLOUR,
                #                                 getColours()[CCPNGLWIDGET_FOREGROUND])

                listCol = getAutoColourRgbRatio(ilv.symbolColour or GLDefs.DEFAULTCOLOUR,
                                                ilv.integralList.spectrum, self._GLParent.SPECTRUMPOSCOLOUR,
                                                getColours()[CCPNGLWIDGET_FOREGROUND])
                meritCol = getAutoColourRgbRatio(ilv.meritColour or GLDefs.DEFAULTCOLOUR,
                                                 ilv.integralList.spectrum, self._GLParent.SPECTRUMPOSCOLOUR,
                                                 getColours()[CCPNGLWIDGET_FOREGROUND])
                meritEnabled = ilv.meritEnabled
                meritThreshold = ilv.meritThreshold
                if meritEnabled and integral.figureOfMerit < meritThreshold:
                    cols = meritCol
                else:
                    cols = listCol

                ils.addIntegral(integral, ilv, colour=None,
                                brush=(*cols, CCPNGLWIDGET_INTEGRALSHADE))
                return

    def _changeSymbol(self, integral):
        """update the vertex list attached to the integral
        """
        for ils in self._GLSymbols.values():
            for reg in ils._regions:
                if reg._object == integral:
                    if hasattr(reg, '_integralArea'):
                        # set the rebuild flag for this region
                        reg._integralArea.renderMode = GLRENDERMODE_REBUILD
                        ils._rebuildIntegralAreas()

                        return

    def _appendLabel(self, spectrumView, objListView, stringList, obj):
        """Append a new label to the end of the list
        """
        spectrum = spectrumView.spectrum
        spectrumFrequency = spectrum.spectrometerFrequencies

        # pls = peakListView.peakList
        pls = self.objectList(objListView)

        # symbolWidth = self.strip.symbolSize / 2.0

        # get the correct coordinates based on the axisCodes
        p0 = [0.0] * 2  # len(self.axisOrder)
        lims = obj.limits[0] if obj.limits else (0.0, 0.0)

        for ps, psCode in enumerate(self._GLParent.axisOrder[0:2]):
            for pp, ppCode in enumerate(obj.axisCodes):

                if self._GLParent._preferences.matchAxisCode == 0:  # default - match atom type
                    if ppCode[0] == psCode[0]:

                        # need to put the position in here

                        if self._GLParent.INVERTXAXIS:
                            p0[ps] = pos = max(lims)  # obj.position[pp]
                        else:
                            p0[ps] = pos = min(lims)  # obj.position[pp]
                    else:
                        p0[ps] = 0.0  #obj.height

                elif self._GLParent._preferences.matchAxisCode == 1:  # match full code
                    if ppCode == psCode:
                        if self._GLParent.INVERTXAXIS:
                            p0[ps] = pos = max(lims)  # obj.position[pp]
                        else:
                            p0[ps] = pos = min(lims)  # obj.position[pp]
                    else:
                        p0[ps] = 0.0  #obj.height

        if None in p0:
            getLogger().warning('Object %s contains undefined position %s' % (str(obj.pid), str(p0)))
            return

        if self._isSelected(obj):
            cols = self._GLParent.highlightColour[:3]
        else:
            # listCol = getAutoColourRgbRatio(pls.textColour, pls.spectrum,
            #                                 self.autoColour,
            #                                 getColours()[CCPNGLWIDGET_FOREGROUND])

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

        textX = pos or 0.0 + (3.0 * self._GLParent.pixelX)
        textY = self._GLParent.axisT - (36.0 * self._GLParent.pixelY)

        newString = GLString(text=text,
                             font=self._GLParent.getSmallFont(),
                             # x=p0[0], y=p0[1],
                             x=textX,
                             y=textY,
                             # ox=symbolWidth, oy=symbolWidth,
                             # x=self._screenZero[0], y=self._screenZero[1]
                             colour=(*cols, 1.0),
                             GLContext=self._GLParent,
                             obj=obj)
        # this is in the attribs
        newString.axisIndex = 0
        newString.axisPosition = pos or 0.0

        stringList.append(newString)

        # # this is in the attribs
        # stringList[-1].axisIndex = 0
        # stringList[-1].axisPosition = pos or 0.0


class GLintegral1dLabelling(GLintegralNdLabelling):
    """Class to handle symbol and symbol labelling for 1d displays
    """
    # 20190607:ED Note, this is not quite correct, but there are no Nd regions yet

    pass

    # def __init__(self, parent=None, strip=None, name=None, resizeGL=False):
    #     """Initialise the class
    #     """
    #     super(GLintegral1dLabelling, self).__init__(parent=parent, strip=strip, name=name, resizeGL=resizeGL)
