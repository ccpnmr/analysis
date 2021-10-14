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
__dateModified__ = "$dateModified: 2021-10-14 12:10:14 +0100 (Thu, October 14, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-12-11 17:51:39 +0000 (Fri, December 11, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from ccpn.util.Colour import getAutoColourRgbRatio
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.guiSettings import getColours, CCPNGLWIDGET_MULTIPLETLINK
from ccpn.ui.gui.lib.OpenGL import CcpnOpenGLDefs as GLDefs
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLLabelling import DEFAULTLINECOLOUR, GLLabelling, GL1dLabelling
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import getAliasSetting


class GLmultipletListMethods():
    """Class of methods common to 1d and Nd multiplets
    This is added to the Multiplet Classes below and doesn't require an __init__
    """

    LENSQ = GLDefs.LENSQMULT
    LENSQ2 = GLDefs.LENSQ2MULT
    LENSQ4 = GLDefs.LENSQ4MULT
    POINTCOLOURS = GLDefs.POINTCOLOURSMULT

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Predefined indices/vertex lists
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    _circleVertices = np.array((7, 9, 9, 10, 10, 6, 6, 11, 11, 12, 12, 8,
                                8, 13, 13, 14, 14, 5, 5, 15, 15, 16, 16, 7), dtype=np.uint32)

    _squareMultSymbol = ((np.append(np.array((0, 1, 2, 3), dtype=np.uint32), _circleVertices),
                          np.append(np.array((0, 1, 2, 3, 0, 2, 2, 1, 0, 3, 3, 1), dtype=np.uint32), _circleVertices)),
                         (np.append(np.array((0, 4, 4, 3, 3, 0), dtype=np.uint32), _circleVertices),
                          np.append(np.array((0, 4, 4, 3, 3, 0, 0, 2, 2, 1, 3, 1), dtype=np.uint32), _circleVertices)),
                         (np.append(np.array((2, 4, 4, 1, 1, 2), dtype=np.uint32), _circleVertices),
                          np.append(np.array((2, 4, 4, 1, 1, 2, 0, 2, 0, 3, 3, 1), dtype=np.uint32), _circleVertices)))

    _squareMultSymbolLen = tuple(tuple(len(sq) for sq in squareList) for squareList in _squareMultSymbol)

    _plusMultSymbol = ((np.append(np.array((5, 6, 7, 8), dtype=np.uint32), _circleVertices),
                        np.append(np.array((5, 6, 7, 8, 0, 2, 2, 1, 0, 3, 3, 1), dtype=np.uint32), _circleVertices)),
                       (np.append(np.array((6, 4, 4, 5, 4, 8), dtype=np.uint32), _circleVertices),
                        np.append(np.array((6, 4, 4, 5, 4, 8, 0, 2, 2, 1, 3, 1, 0, 3), dtype=np.uint32), _circleVertices)),
                       (np.append(np.array((6, 4, 4, 5, 4, 7), dtype=np.uint32), _circleVertices),
                        np.append(np.array((6, 4, 4, 5, 4, 7, 0, 2, 2, 1, 3, 1, 0, 3), dtype=np.uint32), _circleVertices)))

    _plusMultSymbolLen = tuple(tuple(len(pl) for pl in plusList) for plusList in _plusMultSymbol)

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
        return False

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
            return 0, 0

        insertNum = len(multiplet.peaks)
        drawList.indices = np.append(drawList.indices, np.array(tuple(val for ii in range(insertNum)
                                                                      for val in (index, 1 + index + ii)), dtype=np.uint32))
        return 2 * insertNum, insertNum + 1

    def insertExtraIndices(self, drawList, indexPtr, index, multiplet):
        """insert extra indices into the index list
        Returns (len, ind)
            len: length of the inserted array
            ind: number of unique indices
        """
        if not multiplet.peaks:
            return 0, 0

        insertNum = len(multiplet.peaks)
        drawList.indices[indexPtr:indexPtr + 2 * insertNum] = tuple(val for ii in range(insertNum)
                                                                    for val in (index, 1 + index + ii))
        return 2 * insertNum, insertNum + 1

    def _getSquareSymbolCount(self, planeIndex, obj):
        """returns the number of indices required for the symbol based on the planeIndex
        type of planeIndex - currently 0/1/2 indicating whether normal, infront or behind
        currently visible planes
        """
        return self._squareMultSymbolLen[planeIndex % 3][self._isSelected(obj)]

    def _makeSquareSymbol(self, drawList, indexEnd, vertexStart, planeIndex, obj):
        """Make a new square symbol based on the planeIndex type.
        """
        _selected = self._isSelected(obj)
        _indices = self._squareMultSymbol[planeIndex % 3][_selected] + vertexStart
        iCount = len(_indices)
        drawList.indices[indexEnd:indexEnd + iCount] = _indices

        return iCount, _selected

    def _appendSquareSymbol(self, drawList, vertexStart, planeIndex, obj):
        """Append a new square symbol based on the planeIndex type.
        """
        _selected = self._isSelected(obj)
        _indices = self._squareMultSymbol[planeIndex % 3][_selected] + vertexStart
        iCount = len(_indices)
        drawList.indices = np.append(drawList.indices, _indices)

        return iCount, _selected

    def _getPlusSymbolCount(self, planeIndex, obj):
        """returns the number of indices required for the symbol based on the planeIndex
        type of planeIndex - currently 0/1/2 indicating whether normal, infront or behind
        currently visible planes
        """
        return self._plusMultSymbolLen[planeIndex % 3][self._isSelected(obj)]

    def _makePlusSymbol(self, drawList, indexEnd, vertexStart, planeIndex, obj):
        """Make a new plus symbol based on the planeIndex type.
        """
        _selected = self._isSelected(obj)
        _indices = self._plusMultSymbol[planeIndex % 3][_selected] + vertexStart
        iCount = len(_indices)
        drawList.indices[indexEnd:indexEnd + iCount] = _indices

        return iCount, _selected

    def _appendPlusSymbol(self, drawList, vertexStart, planeIndex, obj):
        """Append a new plus symbol based on the planeIndex type.
        """
        _selected = self._isSelected(obj)
        _indices = self._plusMultSymbol[planeIndex % 3][_selected] + vertexStart
        iCount = len(_indices)
        drawList.indices = np.append(drawList.indices, _indices)

        return iCount, _selected

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

        col = multiplet.multipletList.lineColour
        cols = getAutoColourRgbRatio(col or DEFAULTLINECOLOUR, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = p0

        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes
            pp = peak.pointPositions
            p1 = (pp[pIndex[0]] - 1, pp[pIndex[1]] - 1)

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                posList += p0
            else:
                posList += p1

        peakAlias = multiplet.peaks[0].aliasing
        alias = getAliasSetting(peakAlias[pIndex[0]], peakAlias[pIndex[1]])

        numVertices = len(multiplet.peaks) + 1
        drawList.vertices = np.append(drawList.vertices, np.array(posList, dtype=np.float32))
        drawList.colors = np.append(drawList.colors, np.array((*cols, fade) * numVertices, dtype=np.float32))
        drawList.attribs = np.append(drawList.attribs, np.array((alias,) * numVertices, dtype=np.float32))
        drawList.offsets = np.append(drawList.offsets, np.array(p0 * numVertices, dtype=np.float32))

        return numVertices

    def insertExtraVertices(self, drawList, vertexPtr, pIndex, multiplet, p0, colour, fade):
        """insert extra vertices into the vertex list
        """
        if not multiplet.peaks:
            return 0

        col = multiplet.multipletList.lineColour
        cols = getAutoColourRgbRatio(col or DEFAULTLINECOLOUR, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = p0

        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes
            pp = peak.pointPositions
            p1 = (pp[pIndex[0]] - 1, pp[pIndex[1]] - 1)

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                posList += p0
            else:
                posList += p1

        peakAlias = multiplet.peaks[0].aliasing
        alias = getAliasSetting(peakAlias[pIndex[0]], peakAlias[pIndex[1]])

        numVertices = len(multiplet.peaks) + 1
        drawList.vertices[vertexPtr:vertexPtr + 2 * numVertices] = posList
        drawList.colors[2 * vertexPtr:2 * vertexPtr + 4 * numVertices] = (*cols, fade) * numVertices
        drawList.attribs[vertexPtr // 2:(vertexPtr // 2) + numVertices] = (alias,) * numVertices
        drawList.offsets[vertexPtr:vertexPtr + 2 * numVertices] = p0 * numVertices

        return numVertices

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
        drawList.attribs[vertexPtr // 2:(vertexPtr // 2) + self.LENSQ] = (alias,) * self.LENSQ
        drawList.offsets[vertexPtr:vertexPtr + self.LENSQ2] = (p0[0], p0[1]) * self.LENSQ

        # add extra indices
        extraIndices, extraIndexCount = self.insertExtraIndices(drawList, indexing.end + iCount, indexing.start + self.LENSQ, obj)
        # add extra vertices for the multiplet
        extraVertices = self.insertExtraVertices(drawList, vertexPtr + self.LENSQ2, pIndex, obj, p0, (*cols, fade), fade)
        try:
            # keep a pointer to the obj
            drawList.pids[objNum:objNum + GLDefs.LENPID] = (obj, drawList.numVertices, (self.LENSQ + extraVertices),
                                                            _isInPlane, _isInFlankingPlane, _selected,
                                                            indexing.end, indexing.end + iCount + extraIndices,
                                                            planeIndex, 0, 0, 0)
        except Exception as es:
            # NOTE:ED - check and remove this error trap
            pass

        indexing.start += (self.LENSQ + extraIndexCount)
        indexing.end += (iCount + extraIndices)
        drawList.numVertices += (self.LENSQ + extraVertices)
        indexing.objNum += GLDefs.LENPID
        indexing.vertexPtr += (2 * (self.LENSQ + extraVertices))
        indexing.vertexStart += (self.LENSQ + extraVertices)

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
        drawList.attribs = np.append(drawList.attribs, np.array((alias,) * self.LENSQ, dtype=np.float32))
        drawList.offsets = np.append(drawList.offsets, np.array((p0[0], p0[1]) * self.LENSQ, dtype=np.float32))

        # add extra indices
        _indexCount, extraIndices = self.appendExtraIndices(drawList, indexing.vertexStart + self.LENSQ, obj)
        # add extra vertices for the multiplet
        extraVertices = self.appendExtraVertices(drawList, pIndex, obj, p0, (*cols, fade), fade)
        # keep a pointer to the obj
        drawList.pids = np.append(drawList.pids, (obj, drawList.numVertices, (self.LENSQ + extraVertices),
                                                  _isInPlane, _isInFlankingPlane, _selected,
                                                  indexing.end, indexing.end + iCount + _indexCount,
                                                  planeIndex, 0, 0, 0))

        indexing.start += (self.LENSQ + extraIndices)
        indexing.end += (iCount + _indexCount)
        drawList.numVertices += (self.LENSQ + extraVertices)
        indexing.vertexStart += (self.LENSQ + extraVertices)


class GLmultipletNdLabelling(GLmultipletListMethods, GLLabelling):  #, GLpeakNdLabelling):
    """Class to handle symbol and symbol labelling for Nd displays
    """

    def __init__(self, parent=None, strip=None, name=None, enableResize=False):
        """Initialise the class
        """
        super().__init__(parent=parent, strip=strip, name=name, enableResize=enableResize)

        # use different colouring
        self.autoColour = self._GLParent.SPECTRUMNEGCOLOUR

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
        try:
            # try to read from the cache
            return self._objIsInVisiblePlanesCache[spectrumView][multiplet]
        except:
            # calculate and store the new value
            value = self._objIsInVisiblePlanes(spectrumView, multiplet, viewOutOfPlaneMultiplets=viewOutOfPlaneMultiplets)
            if spectrumView not in self._objIsInVisiblePlanesCache:
                self._objIsInVisiblePlanesCache[spectrumView] = {multiplet: value}
            else:
                self._objIsInVisiblePlanesCache[spectrumView][multiplet] = value
            return value

    def _objIsInVisiblePlanes(self, spectrumView, multiplet, viewOutOfPlaneMultiplets=True):
        """Return whether in plane or flanking plane

        :param spectrumView: current spectrumView containing multiplets
        :param multiplet: multiplet to test
        :param viewOutOfPlaneMultiplets: whether to show outofplane multiplets, defaults to true
        :return: inPlane - true/false
                inFlankingPlane - true/false
                type of outofplane - currently 0/1/2 indicating whether normal, infront or behind
                fade for colouring
        """
        pntPos = multiplet.pointPositions
        if not pntPos:
            return False, False, 0, 1.0

        displayIndices = self._GLParent.visiblePlaneDimIndices[spectrumView]
        if displayIndices is None:
            return False, False, 0, 1.0

        inPlane = True
        endPlane = 0

        for ii, displayIndex in enumerate(displayIndices[2:]):
            if displayIndex is not None:

                # If no axis matches the index may be None
                zPosition = pntPos[displayIndex]
                if not zPosition:
                    return False, False, 0, 1.0
                actualPlane = int(zPosition + 0.5) - (1 if zPosition >= 0 else 2)

                # settings = self._spectrumSettings[spectrumView]
                # actualPlane = int(settings[GLDefs.SPECTRUM_VALUETOPOINT][ii](zPosition) + 0.5) - 1
                # planes = (self._GLParent.visiblePlaneList[spectrumView])[ii]

                thisVPL = self._GLParent.visiblePlaneList[spectrumView]
                if not thisVPL:
                    return False, False, 0, 1.0

                planes = thisVPL[ii]
                if not (planes and planes[0]):
                    return False, False, 0, 1.0

                visiblePlaneList = planes[0]
                vplLen = len(visiblePlaneList)

                if actualPlane in visiblePlaneList[1:vplLen - 1]:
                    inPlane &= True

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

        col = multiplet.multipletList.lineColour
        cols = getAutoColourRgbRatio(col if col else DEFAULTLINECOLOUR, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = p0
        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes
            p1 = (peak.pointPositions[pIndex[0]] - 1, peak.height)

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                posList += p0
            else:
                posList += p1

        peakAlias = multiplet.peaks[0].aliasing
        alias = getAliasSetting(peakAlias[pIndex[0]], 0)

        numVertices = len(multiplet.peaks) + 1
        drawList.vertices = np.append(drawList.vertices, np.array(posList, dtype=np.float32))
        drawList.colors = np.append(drawList.colors, np.array((*cols, fade) * numVertices, dtype=np.float32))
        drawList.attribs = np.append(drawList.attribs, np.array((alias,) * numVertices, dtype=np.float32))
        drawList.offsets = np.append(drawList.offsets, np.array(p0 * numVertices, dtype=np.float32))

        return numVertices

    def insertExtraVertices(self, drawList, vertexPtr, pIndex, multiplet, p0, colour, fade):
        """insert extra vertices into the vertex list
        """
        if not multiplet.peaks:
            return 0

        col = multiplet.multipletList.lineColour
        cols = getAutoColourRgbRatio(col or DEFAULTLINECOLOUR, multiplet.multipletList.spectrum, self.autoColour,
                                     getColours()[CCPNGLWIDGET_MULTIPLETLINK])

        posList = p0

        for peak in multiplet.peaks:
            # get the correct coordinates based on the axisCodes
            p1 = (peak.pointPositions[pIndex] - 1, peak.height)

            if None in p1:
                getLogger().warning('Peak %s contains undefined position %s' % (str(peak.pid), str(p1)))
                posList += p0
            else:
                posList += p1
        peakAlias = multiplet.peaks[0].aliasing
        alias = getAliasSetting(peakAlias[0], 0)

        numVertices = len(multiplet.peaks) + 1
        drawList.vertices[vertexPtr:vertexPtr + 2 * numVertices] = posList
        drawList.colors[2 * vertexPtr:2 * vertexPtr + 4 * numVertices] = (*cols, fade) * numVertices
        drawList.attribs[vertexPtr // 2:(vertexPtr // 2) + numVertices] = (alias,) * numVertices
        drawList.offsets[vertexPtr:vertexPtr + 2 * numVertices] = p0 * numVertices

        return numVertices

    def objIsInVisiblePlanes(self, spectrumView, obj):
        """Get the current object is in visible planes settings
        """
        return True, False, 0, 1.0
