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
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from itertools import zip_longest
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import CcpnGLWidget, GLVertexArray, GLRENDERMODE_DRAW, \
    GLRENDERMODE_RESCALE
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import YAXISUNITS1D, SPECTRUM_VALUEPERPOINT
import ccpn.util.Phasing as Phasing
from ccpn.core.lib.AxisCodeLib import getAxisCodeMatchIndices
from ccpn.ui.gui.lib.OpenGL import CcpnOpenGLDefs as GLDefs
from ccpn.util.Logging import getLogger
from ccpn.core.lib.peakUtils import movePeak

from ccpn.ui.gui.lib.OpenGL import GL


class GuiNdWidget(CcpnGLWidget):
    is1D = False
    INVERTXAXIS = True
    INVERTYAXIS = True
    SPECTRUMPOSCOLOUR = 'positiveContourColour'
    SPECTRUMNEGCOLOUR = 'negativeContourColour'
    AXIS_INSIDE = False

    def __init__(self, strip=None, mainWindow=None, stripIDLabel=None):
        super().__init__(strip=strip, mainWindow=mainWindow, stripIDLabel=stripIDLabel)

    def _mouseInPeak(self, xPosition, yPosition, firstOnly=False):
        """Find the peaks under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        xPositions = [xPosition - self.symbolX, xPosition + self.symbolX]
        yPositions = [yPosition - self.symbolY, yPosition + self.symbolY]
        if len(self._orderedAxes) > 2:
            zPositions = self._orderedAxes[2].region
        else:
            zPositions = None

        peaks = []

        for spectrumView in self.strip.spectrumViews:
            for peakListView in spectrumView.peakListViews:
                if spectrumView.isVisible() and peakListView.isVisible():

                    peakList = peakListView.peakList

                    spectrumIndices = spectrumView.dimensionOrdering
                    xAxis = spectrumIndices[0]
                    yAxis = spectrumIndices[1]

                    for peak in peakList.peaks:
                        if len(peak.axisCodes) > 2 and zPositions is not None:

                            zAxis = spectrumIndices[2]

                            if (xPositions[0] < float(peak.position[xAxis]) < xPositions[1]
                                    and yPositions[0] < float(peak.position[yAxis]) < yPositions[1]):

                                # within the XY bounds so check whether inPlane
                                _isInPlane, _isInFlankingPlane, planeIndex, fade = self._GLPeaks.objIsInVisiblePlanes(spectrumView, peak)

                                # if zPositions[0] < float(peak.position[zAxis]) < zPositions[1]:
                                if _isInPlane:
                                    peaks.append(peak)
                                    if firstOnly:
                                        return peaks
                        else:
                            if (xPositions[0] < float(peak.position[xAxis]) < xPositions[1]
                                    and yPositions[0] < float(peak.position[yAxis]) < yPositions[1]):
                                peaks.append(peak)
                                if firstOnly:
                                    return peaks if peak in self.current.peaks else []

        return peaks

    def _mouseInMultiplet(self, xPosition, yPosition, firstOnly=False):
        """Find the multiplets under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        xPositions = [xPosition - self.symbolX, xPosition + self.symbolX]
        yPositions = [yPosition - self.symbolY, yPosition + self.symbolY]

        if len(self._orderedAxes) > 2:
            zPositions = self._orderedAxes[2].region
        else:
            zPositions = None

        multiplets = []

        for spectrumView in self.strip.spectrumViews:

            for multipletListView in spectrumView.multipletListViews:
                if spectrumView.isVisible() and multipletListView.isVisible():

                    multipletList = multipletListView.multipletList

                    spectrumIndices = spectrumView.dimensionOrdering
                    xAxis = spectrumIndices[0]
                    yAxis = spectrumIndices[1]

                    for multiplet in multipletList.multiplets:
                        if not multiplet.position:
                            continue

                        if len(multiplet.axisCodes) > 2 and zPositions is not None:

                            zAxis = spectrumIndices[2]

                            if (xPositions[0] < float(multiplet.position[xAxis]) < xPositions[1]
                                    and yPositions[0] < float(multiplet.position[yAxis]) < yPositions[1]):

                                # within the XY bounds so check whether inPlane
                                _isInPlane, _isInFlankingPlane, planeIndex, fade = self._GLMultiplets.objIsInVisiblePlanes(spectrumView, multiplet)

                                # if zPositions[0] < float(multiplet.position[zAxis]) < zPositions[1]:
                                if _isInPlane:
                                    multiplets.append(multiplet)
                                    if firstOnly:
                                        return multiplets
                        else:
                            if (xPositions[0] < float(multiplet.position[xAxis]) < xPositions[1]
                                    and yPositions[0] < float(multiplet.position[yAxis]) < yPositions[1]):
                                multiplets.append(multiplet)
                                if firstOnly:
                                    return multiplets if multiplet in self.current.multiplets else []

        return multiplets

    def _mouseInIntegral(self, xPosition, yPosition, firstOnly=False):
        """Find the integrals under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        Currently not-defined for Nd integrals
        """
        return []

    def _updateVisibleSpectrumViews(self):
        """Update the list of visible spectrumViews when change occurs
        """

        # make the list of ordered spectrumViews
        self._ordering = self.spectrumDisplay.orderedSpectrumViews(self.strip.spectrumViews)

        # GWV: removed as new data reader returns zeros; blank spectra can be displayed
        # self._ordering = [specView for specView in self._ordering if specView.spectrum.hasValidPath()]

        for specView in tuple(self._spectrumSettings.keys()):
            if specView not in self._ordering:
                del self._spectrumSettings[specView]

                # delete the 1d string relating to the spectrumView
                self._spectrumLabelling.removeString(specView)

        # make a list of the visible and not-deleted spectrumViews
        # visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
        visibleSpectrumViews = [specView for specView in self._ordering if not specView.isDeleted and specView.isVisible()]

        self._visibleOrdering = visibleSpectrumViews

        # set the first visible, or the first in the ordered list
        self._firstVisible = visibleSpectrumViews[0] if visibleSpectrumViews else self._ordering[0] if self._ordering and not self._ordering[
            0].isDeleted else None
        self.visiblePlaneList = {}
        self.visiblePlaneListPointValues = {}
        self.visiblePlaneDimIndices = {}

        # generate the new axis labels based on the visible spectrum axisCodes
        self._buildAxisCodesWithWildCards()

        minList = [self._spectrumSettings[sp][SPECTRUM_VALUEPERPOINT] if SPECTRUM_VALUEPERPOINT in self._spectrumSettings[sp] else None
                   for sp in self._ordering if sp in self._spectrumSettings]

        minimumValuePerPoint = None

        # check the length of the min values, may have lower dimension spectra overlaid
        for val in minList:
            if minimumValuePerPoint and val is not None:
                minimumValuePerPoint = [min(ii, jj) for ii, jj in zip_longest(minimumValuePerPoint, val, fillvalue=0.0)]
            elif minimumValuePerPoint:
                # val is None so ignore
                pass
            else:
                # set the first value
                minimumValuePerPoint = val

        for visibleSpecView in self._ordering:
            visValues = visibleSpecView._getVisiblePlaneList(
                    firstVisible=self._firstVisible,
                    minimumValuePerPoint=minimumValuePerPoint)

            self.visiblePlaneList[visibleSpecView], \
            self.visiblePlaneListPointValues[visibleSpecView], \
            self.visiblePlaneDimIndices[visibleSpecView] = visValues

        # update the labelling lists
        self._GLPeaks.setListViews(self._ordering)
        self._GLIntegrals.setListViews(self._ordering)
        self._GLMultiplets.setListViews(self._ordering)

    def getPeakPositionFromMouse(self, peak, lastStartCoordinate, cursorPosition=None):
        """Get the centre position of the clicked peak
        """
        indices = getAxisCodeMatchIndices(self._axisCodes, peak.axisCodes)
        for ii, ind in enumerate(indices[:2]):
            if ind is not None:
                lastStartCoordinate[ii] = peak.position[ind]
            else:
                lastStartCoordinate[ii] = cursorPosition[ii]

    def _movePeak(self, peak, deltaPosition):
        """Move the peak to new position
        """
        indices = getAxisCodeMatchIndices(self.axisCodes, peak.axisCodes)

        # get the correct coordinates based on the axisCodes
        p0 = list(peak.position)
        for ii, ind in enumerate(indices[:2]):
            if ind is not None:
                # update the peak position
                p0[ind] += deltaPosition[ii]

        aliasInds = peak.spectrum.aliasingIndexes
        lims = peak.spectrum.spectrumLimits
        widths = peak.spectrum.spectralWidths

        for dim, pos in enumerate(p0):
            # update the aliasing so that the peak stays within the bounds of the spectrumLimits/aliasingLimits
            minSpectrumFrequency, maxSpectrumFrequency = sorted(lims[dim])
            regionBounds = (minSpectrumFrequency + aliasInds[dim][0] * widths[dim],
                            maxSpectrumFrequency + aliasInds[dim][1] * widths[dim])
            p0[dim] = (pos - regionBounds[0]) % (regionBounds[1] - regionBounds[0]) + regionBounds[0]

        movePeak(peak, p0, updateHeight=True)

    def _tracesNeedUpdating(self, spectrumView=None):
        """Check if traces need updating on _lastTracePoint, use spectrumView to see
        if cursor has moved sufficiently far to warrant an update of the traces
        """

        cursorCoordinate = self.getCurrentCursorCoordinate()
        if spectrumView not in self._lastTracePoint:
            numDim = len(spectrumView.strip.axes)
            self._lastTracePoint[spectrumView] = [-1] * numDim

        lastTrace = self._lastTracePoint[spectrumView]

        ppm2point = spectrumView.spectrum.ppm2point

        # get the correct ordering for horizontal/vertical
        planeDims = self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX]

        point = [0] * len(cursorCoordinate)
        for n in range(2):
            point[planeDims[n]] = ppm2point(cursorCoordinate[n], dimension=planeDims[n] + 1) - 1

        point = [round(p) for p in point]

        if None in planeDims:
            getLogger().warning(f'bad planeDims {planeDims}')
            return
        if None in point:
            getLogger().warning(f'bad point {point}')
            return

        # numPoints = spectrumView.spectrum.pointCounts
        # xNumPoints, yNumPoints = numPoints[planeDims[0]], numPoints[planeDims[1]]
        # if point[planeDims[0]] >= xNumPoints or point[planeDims[1]] >= yNumPoints:
        #     # Extra check whether the new point is out of range if numLimits
        #     return False

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

    def drawAliasedLabels(self):
        """Draw all the labels that require aliasing to multiple regions
        """
        _shader = self.globalGL._shaderProgramTexAlias.makeCurrent()
        # set the scale to the axis limits, needs addressing correctly, possibly same as grid
        _shader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB,
                                  self.axisT, -1.0, 1.0)
        _shader.setPTexMatrix(self._uPMatrix)

        self._axisScale[0:4] = [self.pixelX, self.pixelY, 0.0, 1.0]
        _shader.setAxisScale(self._axisScale)
        _shader.setStackOffset(np.array((0.0, 0.0), dtype=np.float32))

        _shader.setAliasEnabled(self._aliasEnabled and self._aliasLabelsEnabled)

        # change to correct value for shader
        _shader.setAliasShade(self._aliasShade / 100.0)

        for specView in self._ordering:  #self._ordering:                             # strip.spectrumViews:       #.orderedSpectrumViews():

            if specView.isDeleted:
                continue

            if specView.isVisible() and specView in self._spectrumSettings.keys():
                # set correct transform when drawing this contour

                specSettings = self._spectrumSettings[specView]
                # pIndex = specSettings[GLDefs.SPECTRUM_POINTINDEX]
                # if None in pIndex:
                #     continue

                # should move this to buildSpectrumSettings
                # and emit a signal when visibleAliasingRange or foldingModes are changed

                # fx0 = specSettings[GLDefs.SPECTRUM_MAXXALIAS]
                # # fx1 = specSettings[GLDefs.SPECTRUM_MINXALIAS]
                # fy0 = specSettings[GLDefs.SPECTRUM_MAXYALIAS]
                # # fy1 = specSettings[GLDefs.SPECTRUM_MINYALIAS]
                # dxAF = specSettings[GLDefs.SPECTRUM_DXAF]
                # dyAF = specSettings[GLDefs.SPECTRUM_DYAF]
                # xScale = specSettings[GLDefs.SPECTRUM_XSCALE]
                # yScale = specSettings[GLDefs.SPECTRUM_YSCALE]

                specMatrix = np.array(specSettings[GLDefs.SPECTRUM_MATRIX], dtype=np.float32)

                # alias = specView.spectrum.visibleAliasingRange
                # folding = specView.spectrum.foldingModes

                _, fxMax = specSettings[GLDefs.SPECTRUM_XLIMITS]
                _, fyMax = specSettings[GLDefs.SPECTRUM_YLIMITS]
                dxAF, dyAF = specSettings[GLDefs.SPECTRUM_AF]
                xScale, yScale = specSettings[GLDefs.SPECTRUM_SCALE]
                alias = specSettings[GLDefs.SPECTRUM_ALIASINGINDEX]
                folding = specSettings[GLDefs.SPECTRUM_FOLDINGMODE]

                for ii in range(alias[0][0], alias[0][1] + 1, 1):
                    for jj in range(alias[1][0], alias[1][1] + 1, 1):

                        foldX = foldY = 1.0
                        foldXOffset = foldYOffset = 0
                        if folding[0] == 'mirror':
                            foldX = pow(-1, ii)
                            foldXOffset = -dxAF if foldX < 0 else 0
                        if folding[1] == 'mirror':
                            foldY = pow(-1, jj)
                            foldYOffset = -dyAF if foldY < 0 else 0

                        self._axisScale[0:4] = [foldX * self.pixelX / xScale,
                                                foldY * self.pixelY / yScale,
                                                0.0, 1.0]
                        _shader.setAxisScale(self._axisScale)

                        specMatrix[0:16] = [xScale * foldX, 0.0, 0.0, 0.0,
                                            0.0, yScale * foldY, 0.0, 0.0,
                                            0.0, 0.0, 1.0, 0.0,
                                            fxMax + (ii * dxAF) + foldXOffset, fyMax + (jj * dyAF) + foldYOffset, 0.0, 1.0]

                        # flipping in the same GL region -  xScale = -xScale
                        #                                   offset = fx0-dxAF
                        # circular -    offset = fx0 + dxAF*alias, alias = min->max
                        _shader.setMVMatrix(specMatrix)
                        _shader.setAliasPosition(ii, jj)

                        self._GLPeaks.drawLabels(specView)
                        self._GLMultiplets.drawLabels(specView)

    def drawAliasedSymbols(self):
        """Draw all the symbols that require aliasing to multiple regions
        """
        _shader = self.globalGL._shaderProgramAlias.makeCurrent()
        # set the scale to the axis limits, needs addressing correctly, possibly same as grid
        _shader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB,
                                  self.axisT, -1.0, 1.0)
        _shader.setPMatrix(self._uPMatrix)

        lineThickness = self._symbolThickness
        GL.glLineWidth(lineThickness * self.viewports.devicePixelRatio)
        _shader.setAliasEnabled(self._aliasEnabled)

        # change to correct value for shader
        _shader.setAliasShade(self._aliasShade / 100.0)

        for specView in self._ordering:  #self._ordering:                             # strip.spectrumViews:       #.orderedSpectrumViews():

            if specView.isDeleted:
                continue

            if specView.isVisible() and specView in self._spectrumSettings.keys():
                specSettings = self._spectrumSettings[specView]
                # pIndex = specSettings[GLDefs.SPECTRUM_POINTINDEX]
                # if None in pIndex:
                #     continue

                # should move this to buildSpectrumSettings
                # and emit a signal when visibleAliasingRange or foldingModes are changed

                # fx0 = specSettings[GLDefs.SPECTRUM_MAXXALIAS]
                # # fx1 = specSettings[GLDefs.SPECTRUM_MINXALIAS]
                # fy0 = specSettings[GLDefs.SPECTRUM_MAXYALIAS]
                # # fy1 = specSettings[GLDefs.SPECTRUM_MINYALIAS]
                # dxAF = specSettings[GLDefs.SPECTRUM_DXAF]
                # dyAF = specSettings[GLDefs.SPECTRUM_DYAF]
                # xScale = specSettings[GLDefs.SPECTRUM_XSCALE]
                # yScale = specSettings[GLDefs.SPECTRUM_YSCALE]

                specMatrix = np.array(specSettings[GLDefs.SPECTRUM_MATRIX], dtype=np.float32)

                # alias = specView.spectrum.visibleAliasingRange
                # folding = specView.spectrum.foldingModes

                _, fxMax = specSettings[GLDefs.SPECTRUM_XLIMITS]
                _, fyMax = specSettings[GLDefs.SPECTRUM_YLIMITS]
                dxAF, dyAF = specSettings[GLDefs.SPECTRUM_AF]
                xScale, yScale = specSettings[GLDefs.SPECTRUM_SCALE]
                alias = specSettings[GLDefs.SPECTRUM_ALIASINGINDEX]
                folding = specSettings[GLDefs.SPECTRUM_FOLDINGMODE]

                for ii in range(alias[0][0], alias[0][1] + 1, 1):
                    for jj in range(alias[1][0], alias[1][1] + 1, 1):

                        foldX = foldY = 1.0
                        foldXOffset = foldYOffset = 0
                        if folding[0] == 'mirror':
                            foldX = pow(-1, ii)
                            foldXOffset = -dxAF if foldX < 0 else 0
                        if folding[1] == 'mirror':
                            foldY = pow(-1, jj)
                            foldYOffset = -dyAF if foldY < 0 else 0

                        specMatrix[0:16] = [xScale * foldX, 0.0, 0.0, 0.0,
                                            0.0, yScale * foldY, 0.0, 0.0,
                                            0.0, 0.0, 1.0, 0.0,
                                            fxMax + (ii * dxAF) + foldXOffset, fyMax + (jj * dyAF) + foldYOffset, 0.0, 1.0]

                        # flipping in the same GL region -  xScale = -xScale
                        #                                   offset = fx0-dxAF
                        # circular -    offset = fx0 + dxAF*alias, alias = min->max
                        _shader.setMVMatrix(specMatrix)
                        _shader.setAliasPosition(ii, jj)

                        self._GLPeaks.drawSymbols(specView)
                        self._GLMultiplets.drawSymbols(specView)

        GL.glLineWidth(GLDefs.GLDEFAULTLINETHICKNESS * self.viewports.devicePixelRatio)

    def drawIntegralLabels(self):
        """Draw all the integral labels
        """
        pass

    def drawBoundingBoxes(self):
        if self.strip.isDeleted:
            return

        currentShader = self.globalGL._shaderProgram1

        # set transform to identity - ensures only the pMatrix is applied
        currentShader.setMVMatrix(self._IMatrix)

        # build the bounding boxes
        index = 0
        drawList = self.boundingBoxes

        # NOTE:ED - shouldn't need to build this every time :|
        drawList.clearArrays()

        # if self._preferences.showSpectrumBorder:
        if self.strip.spectrumBordersVisible:
            for spectrumView in self._ordering:

                if spectrumView.isDeleted:
                    continue

                if spectrumView.isVisible() and spectrumView.spectrum.dimensionCount > 1 and spectrumView in self._spectrumSettings.keys():
                    specSettings = self._spectrumSettings[spectrumView]

                    fxMin, _ = specSettings[GLDefs.SPECTRUM_XFOLDLIMITS]
                    fyMin, _ = specSettings[GLDefs.SPECTRUM_YFOLDLIMITS]
                    dxAF, dyAF = specSettings[GLDefs.SPECTRUM_AF]
                    alias = specSettings[GLDefs.SPECTRUM_ALIASINGINDEX]

                    try:
                        _posColour = spectrumView.posColours[0]
                        col = (*_posColour[0:3], 0.5)
                    except Exception as es:
                        col = (0.9, 0.1, 0.2, 0.5)

                    for ii in range(alias[0][0], alias[0][1] + 2, 1):
                        # draw the vertical lines
                        x0 = fxMin + (ii * dxAF)
                        y0 = fyMin + (alias[1][0] * dyAF)
                        y1 = fyMin + ((alias[1][1] + 1) * dyAF)
                        drawList.indices = np.append(drawList.indices, np.array((index, index + 1), dtype=np.uint32))
                        drawList.vertices = np.append(drawList.vertices, np.array((x0, y0, x0, y1), dtype=np.float32))
                        drawList.colors = np.append(drawList.colors, np.array(col * 2, dtype=np.float32))
                        drawList.numVertices += 2
                        index += 2

                    for jj in range(alias[1][0], alias[1][1] + 2, 1):
                        # draw the horizontal lines
                        y0 = fyMin + (jj * dyAF)
                        x0 = fxMin + (alias[0][0] * dxAF)
                        x1 = fxMin + ((alias[0][1] + 1) * dxAF)
                        drawList.indices = np.append(drawList.indices, np.array((index, index + 1), dtype=np.uint32))
                        drawList.vertices = np.append(drawList.vertices, np.array((x0, y0, x1, y0), dtype=np.float32))
                        drawList.colors = np.append(drawList.colors, np.array(col * 2, dtype=np.float32))
                        drawList.numVertices += 2
                        index += 2

            # define and draw the boundaries
            drawList.defineIndexVBO()

            with self._disableGLAliasing():
                GL.glEnable(GL.GL_BLEND)

                # use the viewports.devicePixelRatio for retina displays
                GL.glLineWidth(self._contourThickness * self.viewports.devicePixelRatio)

                drawList.drawIndexVBO()

                # reset lineWidth
                GL.glLineWidth(GLDefs.GLDEFAULTLINETHICKNESS * self.viewports.devicePixelRatio)

    def drawSpectra(self):
        if self.strip.isDeleted:
            return

        currentShader = self.globalGL._shaderProgram1

        GL.glLineWidth(self._contourThickness * self.viewports.devicePixelRatio)
        GL.glDisable(GL.GL_BLEND)

        for spectrumView in self._ordering:  #self._ordering:                             # strip.spectrumViews:       #.orderedSpectrumViews():

            if spectrumView.isDeleted or not spectrumView._showContours:
                continue

            if spectrumView.isVisible() and spectrumView in self._spectrumSettings.keys():

                # set correct transform when drawing this contour
                if spectrumView.spectrum.displayFoldedContours:
                    specSettings = self._spectrumSettings[spectrumView]

                    pIndex = specSettings[GLDefs.SPECTRUM_POINTINDEX]

                    if None in pIndex:
                        continue

                    # should move this to buildSpectrumSettings
                    # and emit a signal when visibleAliasingRange or foldingModes are changed

                    _, fxMax = specSettings[GLDefs.SPECTRUM_XLIMITS]
                    _, fyMax = specSettings[GLDefs.SPECTRUM_YLIMITS]
                    dxAF, dyAF = specSettings[GLDefs.SPECTRUM_AF]
                    xScale, yScale = specSettings[GLDefs.SPECTRUM_SCALE]
                    alias = specSettings[GLDefs.SPECTRUM_ALIASINGINDEX]
                    folding = specSettings[GLDefs.SPECTRUM_FOLDINGMODE]

                    specMatrix = np.array(specSettings[GLDefs.SPECTRUM_MATRIX], dtype=np.float32)

                    for ii in range(alias[0][0], alias[0][1] + 1, 1):
                        for jj in range(alias[1][0], alias[1][1] + 1, 1):

                            foldX = foldY = 1.0
                            foldXOffset = foldYOffset = 0
                            if folding[0] == 'mirror':
                                foldX = pow(-1, ii)
                                foldXOffset = -dxAF if foldX < 0 else 0

                            if folding[1] == 'mirror':
                                foldY = pow(-1, jj)
                                foldYOffset = -dyAF if foldY < 0 else 0

                            specMatrix[0:16] = [xScale * foldX, 0.0, 0.0, 0.0,
                                                0.0, yScale * foldY, 0.0, 0.0,
                                                0.0, 0.0, 1.0, 0.0,
                                                fxMax + (ii * dxAF) + foldXOffset, fyMax + (jj * dyAF) + foldYOffset, 0.0, 1.0]

                            # flipping in the same GL region -  xScale = -xScale
                            #                                   offset = fxMax-dxAF
                            # circular -    offset = fxMax + dxAF*alias, alias = min->max
                            currentShader.setMVMatrix(specMatrix)

                            self._contourList[spectrumView].drawIndexVBO()

                else:
                    # set the scaling/offset for a single spectrum GL contour
                    currentShader.setMVMatrix(self._spectrumSettings[spectrumView][
                                                  GLDefs.SPECTRUM_MATRIX])

                    self._contourList[spectrumView].drawIndexVBO()

        # reset lineWidth
        GL.glLineWidth(GLDefs.GLDEFAULTLINETHICKNESS * self.viewports.devicePixelRatio)

    def _drawDiagonalLineV2(self, x0, x1, y0, y1):
        """Generate a simple diagonal mapped to (0..1/0..1)
        """
        yy0 = float(x0 - y0) / (y1 - y0)
        yy1 = float(x1 - y0) / (y1 - y0)

        return (0, yy0, 1, yy1)

    def _addDiagonalLine(self, drawList, x0, x1, y0, y1, col):
        """Add a diagonal line to the drawList
        """
        index = len(drawList.indices)
        drawList.indices = np.append(drawList.indices, np.array((index, index + 1), dtype=np.uint32))
        drawList.vertices = np.append(drawList.vertices, np.array(self._drawDiagonalLineV2(x0, x1, y0, y1), dtype=np.float32))
        drawList.colors = np.append(drawList.colors, np.array(col * 2, dtype=np.float32))
        drawList.numVertices += 2

    def _buildDiagonalList(self):
        """Build a list containing the diagonal and the spinningRate lines for the sidebands
        """
        # get spectral width in X and Y
        # get max number of diagonal lines to draw in each axis
        # map to the valueToRatio screen
        # zoom should take care in bounding to the viewport

        # draw the diagonals for the visible spectra
        if self.strip.isDeleted:
            return

        # build the bounding boxes
        drawList = self.diagonalGLList
        drawList.clearArrays()
        drawListSideBands = self.diagonalSideBandsGLList
        drawListSideBands.clearArrays()

        x0 = self.axisL
        x1 = self.axisR
        y0 = self.axisB
        y1 = self.axisT
        col = (0.5, 0.5, 0.5, 0.5)

        diagonalCount = 0
        for spectrumView in self._ordering:  #self._ordering:                             # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            if spectrumView.isVisible() and spectrumView in self._spectrumSettings.keys():
                specSettings = self._spectrumSettings[spectrumView]
                pIndex = specSettings[GLDefs.SPECTRUM_POINTINDEX]

                if not diagonalCount:
                    # add lines to drawList
                    if self._matchingIsotopeCodes:
                        mTypes = spectrumView.spectrum.measurementTypes
                        xaxisType = mTypes[pIndex[0]]
                        yaxisType = mTypes[pIndex[1]]

                        # extra multiple-quantum diagonals
                        if xaxisType == 'MQShift' and yaxisType == 'Shift':
                            self._addDiagonalLine(drawList, x0, x1, 2 * y0, 2 * y1, col)
                        elif xaxisType == 'Shift' and yaxisType == 'MQShift':
                            self._addDiagonalLine(drawList, 2 * x0, 2 * x1, y0, y1, col)
                        else:
                            # add the standard diagonal
                            self._addDiagonalLine(drawList, x0, x1, y0, y1, col)
                    diagonalCount += 1

                spinningRate = spectrumView.spectrum.spinningRate
                if spinningRate:
                    sFreqs = spectrumView.spectrum.spectrometerFrequencies
                    spinningRate /= sFreqs[pIndex[0]]  # might need to pick the correct axis here

                    nmin = -int(self._preferences.numSideBands)
                    nmax = int(self._preferences.numSideBands)

                    for n in range(nmin, nmax + 1):
                        if n:
                            # add lines to drawList
                            self._addDiagonalLine(drawListSideBands, x0 + n * spinningRate, x1 + n * spinningRate, y0, y1, col)

        drawList.defineIndexVBO()
        drawListSideBands.defineIndexVBO()

    def buildDiagonals(self):
        # determine whether the isotopeCodes of the first two visible axes are matching
        self._matchingIsotopeCodes = False

        for specView in self._ordering:

            # check whether the spectrumView is still active
            if specView.isDeleted or specView._flaggedForDelete:
                continue

            spec = specView.spectrum

            # inside the paint event, so sometimes specView may not exist
            if specView in self._spectrumSettings:
                pIndex = self._spectrumSettings[specView][GLDefs.SPECTRUM_POINTINDEX]

                if pIndex and None not in pIndex:
                    if spec.isotopeCodes[pIndex[0]] == spec.isotopeCodes[pIndex[1]]:
                        self._matchingIsotopeCodes = True

                    # build the diagonal list here from the visible spectra - each may have a different spinning rate
                    # remove from _build axe - not needed there
                    self._buildDiagonalList()
                    break

    def _buildSpectrumSetting(self, spectrumView, stackCount=0):
        # if spectrumView.spectrum.headerSize == 0:
        #     return

        self._spectrumSettings[spectrumView] = {}

        self._spectrumValues = spectrumView.getVisibleState()

        # set defaults for undefined spectra
        if not self._spectrumValues[0].pointCount:
            dx = -1.0 if self.INVERTXAXIS else -1.0
            fxMax, fxMin = 1.0, -1.0
            fxFoldMax, fxFoldMin = 1.0, -1.0
            dxAF = fxMax - fxMin
            xScale = dx * dxAF

            dy = -1.0 if self.INVERTYAXIS else -1.0
            fyMax, fyMin = 1.0, -1.0
            fyFoldMax, fyFoldMin = 1.0, -1.0
            dyAF = fyMax - fyMin
            yScale = dy * dyAF
            xAliasingIndex = (0, 0)
            yAliasingIndex = (0, 0)
            xFoldingMode = yFoldingMode = None

            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * dxAF)
            self._maxXRange = max(self._maxXRange, dxAF)
            self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * dyAF)
            self._maxYRange = max(self._maxYRange, dyAF)

        else:

            # get the bounding box of the spectra
            dx = -1.0 if self.INVERTXAXIS else -1.0  # self.sign(self.axisR - self.axisL)
            fxMax, fxMin = self._spectrumValues[0].maxSpectrumFrequency, self._spectrumValues[0].minSpectrumFrequency
            xAliasingIndex = self._spectrumValues[0].aliasingIndex
            xFoldingMode = self._spectrumValues[0].foldingMode
            fxFoldMax, fxFoldMin = self._spectrumValues[0].maxFoldingFrequency, self._spectrumValues[0].minFoldingFrequency

            # check tolerances
            if not self._widthsChangedEnough((fxMax, 0.0), (fxMin, 0.0), tol=1e-10):
                fxMax, fxMin = 1.0, -1.0

            dxAF = fxFoldMax - fxFoldMin  # fxMax - fxMin
            xScale = dx * dxAF / self._spectrumValues[0].pointCount

            dy = -1.0 if self.INVERTYAXIS else -1.0  # self.sign(self.axisT - self.axisB)
            fyMax, fyMin = self._spectrumValues[1].maxSpectrumFrequency, self._spectrumValues[1].minSpectrumFrequency
            yAliasingIndex = self._spectrumValues[1].aliasingIndex
            yFoldingMode = self._spectrumValues[1].foldingMode
            fyFoldMax, fyFoldMin = self._spectrumValues[1].maxFoldingFrequency, self._spectrumValues[1].minFoldingFrequency

            # check tolerances
            if not self._widthsChangedEnough((fyMax, 0.0), (fyMin, 0.0), tol=1e-10):
                fyMax, fyMin = 1.0, -1.0

            dyAF = fyFoldMax - fyFoldMin  # fyMax - fyMin
            yScale = dy * dyAF / self._spectrumValues[1].pointCount

            # set to nD limits to twice the width of the spectrum and a few data points
            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * dxAF / self._spectrumValues[0].pointCount)
            self._maxXRange = max(self._maxXRange, dxAF)
            self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * dyAF / self._spectrumValues[1].pointCount)
            self._maxYRange = max(self._maxYRange, dyAF)

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
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_SPINNINGRATE] = spectrumView.spectrum.spinningRate
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_ALIASINGINDEX] = (xAliasingIndex, yAliasingIndex)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_FOLDINGMODE] = (xFoldingMode, yFoldingMode)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_XFOLDLIMITS] = (fxFoldMin, fxFoldMax)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_YFOLDLIMITS] = (fyFoldMin, fyFoldMax)

        indices = getAxisCodeMatchIndices(self.strip.axisCodes, spectrumView.spectrum.axisCodes)
        # only need the axes for this spectrum
        indices = indices[:spectrumView.spectrum.dimensionCount]
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX] = indices
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_REGIONBOUNDS] = (self._spectrumValues[0].regionBounds, self._spectrumValues[1].regionBounds)

        if len(self._spectrumValues) > 2:
            # store a list for the extra dimensions - should only be one per spectrumDisplay really
            # needed so that the planeDepth is calculated correctly for visible spectra
            vPP = ()
            for dim in range(2, len(self._spectrumValues)):
                specVal = self._spectrumValues[dim]
                vPP = vPP + (specVal.valuePerPoint,)

            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = vPP

        else:
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_VALUEPERPOINT] = None

        self._maxX = max(self._maxX, fxMax)
        self._minX = min(self._minX, fxMin)
        self._maxY = max(self._maxY, fyMax)
        self._minY = min(self._minY, fyMin)

        self._buildAxisCodesWithWildCards()

    def initialiseTraces(self):
        # set up the arrays and dimension for showing the horizontal/vertical traces
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            self._spectrumSettings[spectrumView] = {}
            self._spectrumValues = spectrumView.getVisibleState(dimensionCount=2)

            # get the bounding box of the spectra
            dx = self.sign(self.axisR - self.axisL)
            fxMax, fxMin = self._spectrumValues[0].maxSpectrumFrequency, self._spectrumValues[0].minSpectrumFrequency

            # check tolerances
            if not self._widthsChangedEnough((fxMax, 0.0), (fxMin, 0.0), tol=1e-10):
                fxMax, fxMin = 1.0, -1.0

            dxAF = fxMax - fxMin
            xScale = dx * dxAF / self._spectrumValues[0].pointCount

            dy = self.sign(self.axisT - self.axisB)
            fyMax, fyMin = self._spectrumValues[1].maxSpectrumFrequency, self._spectrumValues[1].minSpectrumFrequency

            # check tolerances
            if not self._widthsChangedEnough((fyMax, 0.0), (fyMin, 0.0), tol=1e-10):
                fyMax, fyMin = 1.0, -1.0

            dyAF = fyMax - fyMin
            yScale = dy * dyAF / self._spectrumValues[1].pointCount

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

            indices = getAxisCodeMatchIndices(self.strip.axisCodes, spectrumView.spectrum.axisCodes)
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX] = indices


class Gui1dWidget(CcpnGLWidget):
    AXIS_MARGINRIGHT = 80
    YAXISUSEEFORMAT = True
    INVERTXAXIS = True
    INVERTYAXIS = False
    AXISLOCKEDBUTTON = True
    AXISLOCKEDBUTTONALLSTRIPS = True
    is1D = True
    SPECTRUMPOSCOLOUR = 'sliceColour'
    SPECTRUMNEGCOLOUR = 'sliceColour'
    SPECTRUMXZOOM = 1.0e2
    SPECTRUMYZOOM = 1.0e6
    SHOWSPECTRUMONPHASING = False
    YAXES = YAXISUNITS1D

    def __init__(self, strip=None, mainWindow=None, stripIDLabel=None):
        super(Gui1dWidget, self).__init__(strip=strip,
                                          mainWindow=mainWindow,
                                          stripIDLabel=stripIDLabel)

    def _mouseInPeak(self, xPosition, yPosition, firstOnly=False):
        """Find the peaks under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        xPositions = [xPosition - self.symbolX, xPosition + self.symbolX]
        yPositions = [yPosition - self.symbolY, yPosition + self.symbolY]

        peaks = []
        for spectrumView in self.strip.spectrumViews:
            for peakListView in spectrumView.peakListViews:
                if spectrumView.isVisible() and peakListView.isVisible():

                    peakList = peakListView.peakList

                    for peak in peakList.peaks:
                        if (xPositions[0] < float(peak.position[0]) < xPositions[1]
                                and yPositions[0] < float(peak.height) < yPositions[1]):

                            peaks.append(peak)
                            if firstOnly:
                                return peaks if peak in self.current.peaks else []

        return peaks

    def _mouseInIntegral(self, xPosition, yPosition, firstOnly=False):
        """Find the integrals under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        integrals = []

        if not self._stackingMode and not (self.is1D and self.strip._isPhasingOn):
            for reg in self._GLIntegrals._GLSymbols.values():
                if not reg.integralListView.isVisible() or not reg.spectrumView.isVisible():
                    continue
                integralPressed = self.mousePressIn1DArea(reg._regions)
                if integralPressed:
                    for ilp in integralPressed:
                        obj = ilp[0]._object
                        integrals.append(obj)
                        if firstOnly:
                            return integrals if obj in self.current.integrals else []

        return integrals

    def _mouseInMultiplet(self, xPosition, yPosition, firstOnly=False):
        """Find the multiplets under the mouse.
        If firstOnly is true, return only the first item, else an empty list
        """
        xPositions = [xPosition - self.symbolX, xPosition + self.symbolX]
        yPositions = [yPosition - self.symbolY, yPosition + self.symbolY]

        multiplets = []
        for spectrumView in self.strip.spectrumViews:
            for multipletListView in spectrumView.multipletListViews:
                if spectrumView.isVisible() and multipletListView.isVisible():

                    multipletList = multipletListView.multipletList

                    for multiplet in multipletList.multiplets:
                        if not multiplet.position:
                            continue

                        if (xPositions[0] < float(multiplet.position[0]) < xPositions[1]
                                and yPositions[0] < float(multiplet.height) < yPositions[1]):

                            multiplets.append(multiplet)
                            if firstOnly:
                                return multiplets if multiplet in self.current.multiplets else []

        return multiplets

    def _newStatic1DTraceData(self, spectrumView, tracesDict, positionPixel,
                              ph0=None, ph1=None, pivot=None):
        """Create a new static 1D phase trace
        """
        try:
            # ignore for 1D if already in the traces list
            for thisTrace in tracesDict:
                if spectrumView == thisTrace.spectrumView:
                    return

            data = spectrumView.spectrum.intensities
            if ph0 is not None and ph1 is not None and pivot is not None:
                preData = Phasing.phaseRealData(data, ph0, ph1, pivot)
            else:
                preData = data

            x = spectrumView.spectrum.positions
            colour = spectrumView._getColour(self.SPECTRUMPOSCOLOUR, '#aaaaaa')
            colR = int(colour.strip('# ')[0:2], 16) / 255.0
            colG = int(colour.strip('# ')[2:4], 16) / 255.0
            colB = int(colour.strip('# ')[4:6], 16) / 255.0

            tracesDict.append(GLVertexArray(numLists=1,
                                            renderMode=GLRENDERMODE_RESCALE,
                                            blendMode=False,
                                            drawMode=GL.GL_LINE_STRIP,
                                            dimension=2,
                                            GLContext=self))

            numVertices = len(x)
            hSpectrum = tracesDict[-1]
            hSpectrum.indices = numVertices
            hSpectrum.numVertices = numVertices
            hSpectrum.indices = np.arange(numVertices, dtype=np.uint32)

            if self._showSpectraOnPhasing:
                hSpectrum.colors = np.array(self._phasingTraceColour * numVertices, dtype=np.float32)
            else:
                hSpectrum.colors = np.array((colR, colG, colB, 1.0) * numVertices, dtype=np.float32)

            hSpectrum.vertices = np.empty(hSpectrum.numVertices * 2, dtype=np.float32)
            hSpectrum.vertices[::2] = x
            hSpectrum.vertices[1::2] = preData

            # store the pre-phase data
            hSpectrum.data = data
            hSpectrum.positionPixel = positionPixel
            hSpectrum.spectrumView = spectrumView

        except Exception as es:
            tracesDict = []

    @property
    def showSpectraOnPhasing(self):
        return self._showSpectraOnPhasing

    @showSpectraOnPhasing.setter
    def showSpectraOnPhasing(self, visible):
        self._showSpectraOnPhasing = visible
        self._updatePhasingColour()
        self.update()

    def toggleShowSpectraOnPhasing(self):
        self._showSpectraOnPhasing = not self._showSpectraOnPhasing
        self._updatePhasingColour()
        self.update()

    def _updatePhasingColour(self):
        for trace in self._staticHTraces:
            colour = trace.spectrumView._getColour(self.SPECTRUMPOSCOLOUR, '#aaaaaa')
            colR = int(colour.strip('# ')[0:2], 16) / 255.0
            colG = int(colour.strip('# ')[2:4], 16) / 255.0
            colB = int(colour.strip('# ')[4:6], 16) / 255.0

            numVertices = trace.numVertices
            if self._showSpectraOnPhasing:
                trace.colors = np.array(self._phasingTraceColour * numVertices, dtype=np.float32)
            else:
                trace.colors = np.array((colR, colG, colB, 1.0) * numVertices, dtype=np.float32)

            trace.renderMode = GLRENDERMODE_RESCALE

    def buildSpectra(self):
        """set the GL flags to build spectrum contour lists
        """
        if self.strip.isDeleted:
            return

        stackCount = 0

        # self._spectrumSettings = {}
        rebuildFlag = False
        for stackCount, spectrumView in enumerate(self._ordering):  # .strip.spectrumViews:
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
                                                                    drawMode=GL.GL_LINE_STRIP,
                                                                    dimension=2,
                                                                    GLContext=self)
                spectrumView._buildGLContours(self._contourList[spectrumView])

                self._buildSpectrumSetting(spectrumView=spectrumView, stackCount=stackCount)
                # if self._stackingMode:
                #     stackCount += 1
                rebuildFlag = True

                # define the VBOs to pass to the graphics card
                self._contourList[spectrumView].defineIndexVBO()

        # rebuild the traces as the spectrum/plane may have changed
        if rebuildFlag:
            self.rebuildTraces()

    def _updateVisibleSpectrumViews(self):
        """Update the list of visible spectrumViews when change occurs
        """

        # make the list of ordered spectrumViews
        self._ordering = self.spectrumDisplay.orderedSpectrumViews(self.strip.spectrumViews)

        self._ordering = [specView for specView in self._ordering]

        for specView in tuple(self._spectrumSettings.keys()):
            if specView not in self._ordering:
                # print('>>>_updateVisibleSpectrumViews delete', specView, id(specView))
                # print('>>>', [id(spec) for spec in self._ordering])
                del self._spectrumSettings[specView]

                # delete the 1d string relating to the spectrumView
                self._spectrumLabelling.removeString(specView)

        # make a list of the visible and not-deleted spectrumViews
        # visibleSpectra = [specView.spectrum for specView in self._ordering if not specView.isDeleted and specView.isVisible()]
        visibleSpectrumViews = [specView for specView in self._ordering if not specView.isDeleted and specView.isVisible()]

        self._visibleOrdering = visibleSpectrumViews

        # set the first visible, or the first in the ordered list
        self._firstVisible = visibleSpectrumViews[0] if visibleSpectrumViews else self._ordering[0] if self._ordering and not self._ordering[
            0].isDeleted else None

        # generate the new axis labels based on the visible spectrum axisCodes
        self._buildAxisCodesWithWildCards()

        # update the labelling lists
        self._GLPeaks.setListViews(self._ordering)
        self._GLIntegrals.setListViews(self._ordering)
        self._GLMultiplets.setListViews(self._ordering)

    def getPeakPositionFromMouse(self, peak, lastStartCoordinate, cursorPosition=None):
        """Get the centre position of the clicked 1d peak
        """
        indices = getAxisCodeMatchIndices(self._axisCodes, peak.axisCodes)

        # check that the mappings are okay
        for ii, ind in enumerate(indices[:2]):
            if ind is not None:
                lastStartCoordinate[ii] = peak.position[ind]
            else:
                lastStartCoordinate[ii] = peak.height

    def _movePeak(self, peak, deltaPosition):
        """Move the peak to new position
        """
        peak.height += deltaPosition[1]
        position = peak.position[0]
        position += deltaPosition[0]
        peak.position = [position]

    def _tracesNeedUpdating(self, spectrumView=None):
        """Check if traces need updating on _lastTracePoint, use spectrumView to see
        if cursor has moved sufficiently far to warrant an update of the traces
        """
        # for 1d spectra, traces never need updating, they never move with the cursor
        return False

    def drawAliasedLabels(self):
        """Draw all the labels that require aliasing to multiple regions
        """
        _shader = self.globalGL._shaderProgramTexAlias.makeCurrent()
        # set the scale to the axis limits, needs addressing correctly, possibly same as grid
        _shader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB,
                                  self.axisT, -1.0, 1.0)
        _shader.setPTexMatrix(self._uPMatrix)

        self._axisScale[0:4] = [self.pixelX, self.pixelY, 0.0, 1.0]
        _shader.setAxisScale(self._axisScale)
        _shader.setStackOffset(np.array((0.0, 0.0), dtype=np.float32))

        _shader.setAliasEnabled(self._aliasEnabled and self._aliasLabelsEnabled)

        # change to correct value for shader
        _shader.setAliasShade(self._aliasShade / 100.0)

        for specView in self._ordering:

            if specView.isDeleted:
                continue

            if specView.isVisible() and specView in self._spectrumSettings.keys():
                specSettings = self._spectrumSettings[specView]

                # should move this to buildSpectrumSettings
                # and emit a signal when visibleAliasingRange or foldingModes are changed

                # fx0 = specSettings[GLDefs.SPECTRUM_MAXXALIAS]
                # xScale = specSettings[GLDefs.SPECTRUM_XSCALE]

                _, fxMax = specSettings[GLDefs.SPECTRUM_XLIMITS]
                dxAF, _ = specSettings[GLDefs.SPECTRUM_AF]
                xScale, _ = specSettings[GLDefs.SPECTRUM_SCALE]
                alias = specSettings[GLDefs.SPECTRUM_ALIASINGINDEX]
                folding = specSettings[GLDefs.SPECTRUM_FOLDINGMODE]

                for ii in range(alias[0][0], alias[0][1] + 1, 1):

                    foldX = 1.0
                    foldXOffset = 0
                    if folding[0] == 'mirror':
                        foldX = pow(-1, ii)
                        foldXOffset = -dxAF if foldX < 0 else 0

                    if self._stackingMode:
                        _matrix = np.array(specSettings[GLDefs.SPECTRUM_STACKEDMATRIX])
                    else:
                        _matrix = np.array(self._IMatrix)

                    # take the stacking matrix and insert the correct x-scaling to map the pointPositions to the screen
                    _matrix[0] = xScale * foldX
                    _matrix[12] += (fxMax + (ii * dxAF) + foldXOffset)
                    _shader.setMVMatrix(_matrix)

                    self._axisScale[0:4] = [foldX * self.pixelX / xScale,
                                            self.pixelY,
                                            0.0, 1.0]
                    _shader.setAxisScale(self._axisScale)
                    _shader.setAliasPosition(ii, 0)

                    self._GLPeaks.drawLabels(specView)
                    self._GLMultiplets.drawLabels(specView)

    def drawAliasedSymbols(self):
        """Draw all the symbols that require aliasing to multiple regions
        """
        _shader = self.globalGL._shaderProgramAlias.makeCurrent()
        # set the scale to the axis limits, needs addressing correctly, possibly same as grid
        _shader.setProjectionAxes(self._uPMatrix, self.axisL, self.axisR, self.axisB,
                                  self.axisT, -1.0, 1.0)
        _shader.setPMatrix(self._uPMatrix)

        lineThickness = self._symbolThickness
        GL.glLineWidth(lineThickness * self.viewports.devicePixelRatio)
        _shader.setAliasEnabled(self._aliasEnabled)

        # change to correct value for shader
        _shader.setAliasShade(self._aliasShade / 100.0)

        for specView in self._ordering:  #self._ordering:                             # strip.spectrumViews:       #.orderedSpectrumViews():

            if specView.isDeleted:
                continue

            if specView.isVisible() and specView in self._spectrumSettings.keys():
                specSettings = self._spectrumSettings[specView]

                # should move this to buildSpectrumSettings
                # and emit a signal when visibleAliasingRange or foldingModes are changed

                # fx0 = specSettings[GLDefs.SPECTRUM_MAXXALIAS]
                # xScale = specSettings[GLDefs.SPECTRUM_XSCALE]

                _, fxMax = specSettings[GLDefs.SPECTRUM_XLIMITS]
                dxAF, _ = specSettings[GLDefs.SPECTRUM_AF]
                xScale, _ = specSettings[GLDefs.SPECTRUM_SCALE]
                alias = specSettings[GLDefs.SPECTRUM_ALIASINGINDEX]
                folding = specSettings[GLDefs.SPECTRUM_FOLDINGMODE]

                for ii in range(alias[0][0], alias[0][1] + 1, 1):

                    foldX = 1.0
                    foldXOffset = 0
                    if folding[0] == 'mirror':
                        foldX = pow(-1, ii)
                        foldXOffset = -dxAF if foldX < 0 else 0

                    if self._stackingMode:
                        _matrix = np.array(specSettings[GLDefs.SPECTRUM_STACKEDMATRIX])
                    else:
                        _matrix = np.array(self._IMatrix)

                    # take the stacking matrix and insert the correct x-scaling to map the pointPositions to the screen
                    _matrix[0] = xScale * foldX
                    _matrix[12] += (fxMax + (ii * dxAF) + foldXOffset)
                    _shader.setMVMatrix(_matrix)
                    _shader.setAliasPosition(ii, 0)

                    # draw the symbols
                    self._GLPeaks.drawSymbols(specView)
                    self._GLMultiplets.drawSymbols(specView)

        GL.glLineWidth(GLDefs.GLDEFAULTLINETHICKNESS * self.viewports.devicePixelRatio)

    def drawIntegralLabels(self):
        """Draw all the integral labels
        """
        for specView in self._ordering:  #self._ordering:                             # strip.spectrumViews:       #.orderedSpectrumViews():

            if specView.isDeleted:
                continue

            if specView.isVisible():
                self._GLIntegrals.drawLabels(specView)

    def drawBoundingBoxes(self):
        """Draw all the bounding boxes
        """
        pass

    def KEEPdrawSpectra(self):
        if self.strip.isDeleted:
            return

        currentShader = self.globalGL._shaderProgram1

        # self.buildSpectra()

        GL.glLineWidth(self._contourThickness * self.viewports.devicePixelRatio)
        GL.glDisable(GL.GL_BLEND)

        # only draw the traces for the spectra that are visible
        specTraces = [trace.spectrumView for trace in self._staticHTraces]

        _visibleSpecs = [specView for specView in self._ordering
                         if not specView.isDeleted and
                         specView.isVisible() and
                         specView._showContours and
                         specView in self._spectrumSettings.keys() and
                         specView in self._contourList.keys() and
                         (specView not in specTraces or self.showSpectraOnPhasing)]

        # for spectrumView in self._ordering:  #self._ordering:                             # strip.spectrumViews:       #.orderedSpectrumViews():
        #
        #     if spectrumView.isDeleted:
        #         continue
        #     if not spectrumView._showContours:
        #         continue
        #
        #     if spectrumView.isVisible() and spectrumView in self._spectrumSettings.keys():
        #         # set correct transform when drawing this contour
        #
        #         if spectrumView in self._contourList.keys() and \
        #                 (spectrumView not in specTraces or self.showSpectraOnPhasing):

        for spectrumView in _visibleSpecs:
            if self._stackingMode:
                # use the stacking matrix to offset the 1D spectra
                currentShader.setMVMatrix(self._spectrumSettings[spectrumView][
                                              GLDefs.SPECTRUM_STACKEDMATRIX])
            # draw contours
            self._contourList[spectrumView].drawVertexColorVBO()

        # reset lineWidth
        GL.glLineWidth(GLDefs.GLDEFAULTLINETHICKNESS * self.viewports.devicePixelRatio)

    def drawSpectra(self):
        if self.strip.isDeleted:
            return

        currentShader = self.globalGL._shaderProgram1

        GL.glLineWidth(self._contourThickness * self.viewports.devicePixelRatio)
        GL.glDisable(GL.GL_BLEND)

        for spectrumView in self._ordering:  #self._ordering:                             # strip.spectrumViews:       #.orderedSpectrumViews():

            if spectrumView.isDeleted:
                continue
            if not spectrumView._showContours:
                continue

            # only draw the traces for the spectra that are visible
            specTraces = [trace.spectrumView for trace in self._staticHTraces]

            if spectrumView.isVisible() and spectrumView in self._spectrumSettings.keys():

                # set correct transform when drawing this contour
                if spectrumView.spectrum.displayFoldedContours:
                    specSettings = self._spectrumSettings[spectrumView]

                    # should move this to buildSpectrumSettings
                    # and emit a signal when visibleAliasingRange or foldingModes are changed

                    _, fxMax = specSettings[GLDefs.SPECTRUM_XLIMITS]
                    dxAF, _ = specSettings[GLDefs.SPECTRUM_AF]
                    alias = specSettings[GLDefs.SPECTRUM_ALIASINGINDEX]
                    folding = specSettings[GLDefs.SPECTRUM_FOLDINGMODE]

                    for ii in range(alias[0][0], alias[0][1] + 1, 1):

                        if self._stackingMode:
                            _matrix = np.array(specSettings[GLDefs.SPECTRUM_STACKEDMATRIX])
                        else:
                            _matrix = np.array(self._IMatrix)

                        # # take the stacking matrix and insert the correct x-scaling to map the pointPositions to the screen
                        # _matrix[0] = xScale
                        # _matrix[12] += fx0

                        foldX = 1.0
                        foldXOffset = foldYOffset = 0
                        if folding[0] == 'mirror':
                            foldX = pow(-1, ii)
                            foldXOffset = (2 * fxMax - dxAF) if foldX < 0 else 0
                        # foldYOffset = ii * 1e8 #if foldX < 0 else 0

                        # specMatrix[0:16] = [xScale * foldX, 0.0, 0.0, 0.0,
                        #                     0.0, 1.0, 0.0, 0.0,
                        #                     0.0, 0.0, 1.0, 0.0,
                        #                     fx0 + (ii * dxAF) + foldXOffset, 0.0, 0.0, 1.0]

                        # take the stacking matrix and insert the correct x-scaling to map the pointPositions to the screen
                        _matrix[0] = foldX
                        _matrix[12] += (ii * dxAF) + foldXOffset
                        # _matrix[12] += foldXOffset
                        # _matrix[13] += foldYOffset

                        # flipping in the same GL region -  xScale = -xScale
                        #                                   offset = fx0-dxAF
                        # circular -    offset = fx0 + dxAF*alias, alias = min->max
                        currentShader.setMVMatrix(_matrix)

                        if spectrumView in self._contourList:
                            self._contourList[spectrumView].drawVertexColorVBO()

                else:
                    if spectrumView in self._contourList.keys() and \
                            (spectrumView not in specTraces or self.showSpectraOnPhasing):

                        if self._stackingMode:
                            # use the stacking matrix to offset the 1D spectra
                            currentShader.setMVMatrix(self._spectrumSettings[spectrumView][
                                                          GLDefs.SPECTRUM_STACKEDMATRIX])
                        # draw contours
                        if spectrumView in self._contourList:
                            self._contourList[spectrumView].drawVertexColorVBO()

        # reset lineWidth
        GL.glLineWidth(GLDefs.GLDEFAULTLINETHICKNESS * self.viewports.devicePixelRatio)

    def buildDiagonals(self):
        """Build a list containing the diagonal and the spinningRate lines for the sidebands
        """
        pass

    def _buildSpectrumSetting(self, spectrumView, stackCount=0):
        # if spectrumView.spectrum.headerSize == 0:
        #     return

        self._spectrumSettings[spectrumView] = {}

        self._spectrumValues = spectrumView.getVisibleState()

        # set defaults for undefined spectra
        if not self._spectrumValues[0].pointCount:
            dx = -1.0 if self.INVERTXAXIS else -1.0
            fxMax, fxMin = 1.0, -1.0
            fxFoldMax, fxFoldMin = 1.0, -1.0
            dxAF = fxMax - fxMin
            xScale = dx * dxAF

            dy = -1.0 if self.INVERTYAXIS else -1.0
            fyMax, fyMin = 1.0, -1.0
            fyFoldMax, fyFoldMin = 1.0, -1.0
            dyAF = fyMax - fyMin
            yScale = dy * dyAF
            xAliasingIndex = (0, 0)
            yAliasingIndex = (0, 0)
            xFoldingMode = yFoldingMode = None

            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * dxAF)
            self._maxXRange = max(self._maxXRange, dxAF)
            self._minYRange = min(self._minYRange, GLDefs.RANGEMINSCALE * dyAF)
            self._maxYRange = max(self._maxYRange, dyAF)

        else:

            # get the bounding box of the spectra
            dx = -1.0 if self.INVERTXAXIS else -1.0  # self.sign(self.axisR - self.axisL)
            fxMax, fxMin = self._spectrumValues[0].maxSpectrumFrequency, self._spectrumValues[0].minSpectrumFrequency
            xAliasingIndex = self._spectrumValues[0].aliasingIndex
            xFoldingMode = self._spectrumValues[0].foldingMode
            fxFoldMax, fxFoldMin = self._spectrumValues[0].maxFoldingFrequency, self._spectrumValues[0].minFoldingFrequency

            # check tolerances
            if not self._widthsChangedEnough((fxMax, 0.0), (fxMin, 0.0), tol=1e-10):
                fxMax, fxMin = 1.0, -1.0

            dxAF = fxFoldMax - fxFoldMin  # fxMax - fxMin
            xScale = dx * dxAF / self._spectrumValues[0].pointCount

            dy = -1.0 if self.INVERTYAXIS else -1.0  # dy = self.sign(self.axisT - self.axisB)

            if spectrumView.spectrum.intensities is not None and spectrumView.spectrum.intensities.size != 0:
                fyMax = float(np.max(spectrumView.spectrum.intensities))
                fyMin = float(np.min(spectrumView.spectrum.intensities))
            else:
                fyMax, fyMin = 0.0, 0.0
            yAliasingIndex = (0, 0)
            yFoldingMode = None

            # check tolerances
            if not self._widthsChangedEnough((fyMax, 0.0), (fyMin, 0.0), tol=1e-10):
                fyMax, fyMin = 1.0, -1.0

            dyAF = fyMax - fyMin
            yScale = dy * dyAF / 1.0

            # set to 1D limits to twice the width of the spectrum and the intensity limit
            self._minXRange = min(self._minXRange, GLDefs.RANGEMINSCALE * dxAF / max(self._spectrumValues[0].pointCount, self.SPECTRUMXZOOM))
            self._maxXRange = max(self._maxXRange, dxAF)
            # self._minYRange = min(self._minYRange, 3.0 * dyAF / self.SPECTRUMYZOOM)
            self._minYRange = min(self._minYRange, self._intensityLimit)
            self._maxYRange = max(self._maxYRange, dyAF)

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
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_SPINNINGRATE] = spectrumView.spectrum.spinningRate
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_ALIASINGINDEX] = (xAliasingIndex, yAliasingIndex)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_FOLDINGMODE] = (xFoldingMode, yFoldingMode)
        self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_XFOLDLIMITS] = (fxFoldMin, fxFoldMax)

        indices = getAxisCodeMatchIndices(self.strip.axisCodes, spectrumView.spectrum.axisCodes)
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

    def initialiseTraces(self):
        # set up the arrays and dimension for showing the horizontal/vertical traces
        for spectrumView in self._ordering:  # strip.spectrumViews:

            if spectrumView.isDeleted:
                continue

            self._spectrumSettings[spectrumView] = {}
            self._spectrumValues = spectrumView.getVisibleState(dimensionCount=2)

            # get the bounding box of the spectra
            dx = self.sign(self.axisR - self.axisL)
            fxMax, fxMin = self._spectrumValues[0].maxSpectrumFrequency, self._spectrumValues[0].minSpectrumFrequency

            # check tolerances
            if not self._widthsChangedEnough((fxMax, 0.0), (fxMin, 0.0), tol=1e-10):
                fxMax, fxMin = 1.0, -1.0

            dxAF = fxMax - fxMin
            xScale = dx * dxAF / self._spectrumValues[0].pointCount

            dy = self.sign(self.axisT - self.axisB)
            if spectrumView.spectrum.intensities is not None and spectrumView.spectrum.intensities.size != 0:
                fyMax = float(np.max(spectrumView.spectrum.intensities))
                fyMin = float(np.min(spectrumView.spectrum.intensities))
            else:
                fyMax, fyMin = 0.0, 0.0

            # check tolerances
            if not self._widthsChangedEnough((fyMax, 0.0), (fyMin, 0.0), tol=1e-10):
                fyMax, fyMin = 1.0, -1.0

            dyAF = fyMax - fyMin
            yScale = dy * dyAF / 1.0

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

            indices = getAxisCodeMatchIndices(self.strip.axisCodes, spectrumView.spectrum.axisCodes)
            self._spectrumSettings[spectrumView][GLDefs.SPECTRUM_POINTINDEX] = indices
