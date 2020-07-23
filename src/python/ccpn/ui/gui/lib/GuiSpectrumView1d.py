"""Module Documentation here

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
__dateModified__ = "$dateModified: 2020-07-23 17:10:53 +0100 (Thu, July 23, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np

from PyQt5 import QtCore

import pyqtgraph as pg

from ccpn.ui.gui.lib.GuiSpectrumView import GuiSpectrumView

from ccpn.util.Colour import spectrumColours, colorSchemeTable
from ccpn.util import Phasing


class GuiSpectrumView1d(GuiSpectrumView):

    hPhaseTrace = None
    buildContours = True
    buildContoursOnly = False

    #def __init__(self, guiSpectrumDisplay, apiSpectrumView, dimMapping=None):
    def __init__(self):
        """ spectrumPane is the parent
            spectrum is the Spectrum name or object
            """
        """ old comment
            region is in units of parent, ordered by spectrum dimensions
            dimMapping is from spectrum numerical dimensions to spectrumPane numerical dimensions
            (for example, xDim is what gets mapped to 0 and yDim is what gets mapped to 1)
        """

        GuiSpectrumView.__init__(self)

        self._application = self.strip.spectrumDisplay.mainWindow.application

        self.data = self.spectrum.positions, self.spectrum.intensities
        # print('>>>filePath', self.spectrum.filePath, self.spectrum.positions, self.spectrum.intensities)

        # for strip in self.strips:
        if self.spectrum.sliceColour is None:
            if len(self.strip.spectrumViews) < 12:
                self.spectrum.sliceColour = list(spectrumColours.keys())[len(self.strip.spectrumViews) - 1]
            else:
                self.spectrum.sliceColour = list(spectrumColours.keys())[(len(self.strip.spectrumViews) % 12) - 1]

        self.hPhaseTrace = None
        self.buildContours = True
        self.buildContoursOnly = False

    def _getValues(self, dimensionCount = None):
        return [self._getSpectrumViewParams(0)]

    def _turnOnPhasing(self):

        phasingFrame = self.strip.spectrumDisplay.phasingFrame
        if phasingFrame.isVisible():
            if self.hPhaseTrace:
                self.hPhaseTrace.setVisible(True)
            else:
                self._newPhasingTrace()

    def _turnOffPhasing(self):

        if self.hPhaseTrace:
            self.hPhaseTrace.setVisible(False)

    def _newPhasingTrace(self):
        """
        # CCPN INTERNAL - called in newPhasingTrace methods of GuiWindow and GuiStrip
        """
        phasingFrame = self.strip.spectrumDisplay.phasingFrame
        if phasingFrame.isVisible() and not self.hPhaseTrace:
            if not self.strip.haveSetHPhasingPivot:
                viewParams = self._getSpectrumViewParams(0)
                self.strip.hPhasingPivot.setPos(0.5 * (viewParams.minSpectrumFrequency +
                                                       viewParams.maxSpectrumFrequency))
                self.strip.hPhasingPivot.setVisible(True)
                self.strip.haveSetHPhasingPivot = True

            trace = pg.PlotDataItem()
            self.strip.plotWidget.addItem(trace)
            self.hPhaseTrace = trace
            self._updatePhasing()

    def removePhasingTraces(self):

        trace = self.hPhaseTrace
        if trace:
            self.strip.plotWidget.scene().removeItem(trace)
            self.hPhaseTrace = None

    def _getTraceParams(self, position):
        # position is in ppm (intensity in y)

        inRange = True
        point = []
        xDataDim = xMinFrequency = xMaxFrequency = xPointCount = None

        for n, pos in enumerate(position):  # n = 0 is x, n = 1 is y, etc.
            if n != 1:

                try:
                    valuePerPoint, _, pointCount, _, _, dataDim, minSpectrumFrequency, maxSpectrumFrequency = self._getSpectrumViewParams(n)
                except:
                    # skip if the dimension doesn't exist
                    break

                if dataDim:
                    if n == 0:
                        xDataDim = dataDim
                        # -1 below because points start at 1 in data model
                        xMinFrequency = int(dataDim.primaryDataDimRef.valueToPoint(maxSpectrumFrequency) - 1)
                        xMaxFrequency = int(dataDim.primaryDataDimRef.valueToPoint(minSpectrumFrequency) - 1)
                        xPointCount = pointCount
                    else:
                        inRange = (minSpectrumFrequency <= pos <= maxSpectrumFrequency)
                        if not inRange:
                            break
                    pnt = (dataDim.primaryDataDimRef.valueToPoint(pos) - 1) % pointCount
                    pnt += (dataDim.pointOffset if hasattr(dataDim, "pointOffset") else 0)
                    point.append(pnt)

        return inRange, point, xDataDim, xMinFrequency, xMaxFrequency, xPointCount

    def refreshData(self):
        # self.spectrum._intensities = None  # UGLY, but need to force data to be reloaded
        self.data = self.spectrum.positions, self.spectrum.intensities

        # spawn a rebuild in the openGL strip
        self.buildContoursOnly = True
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGL import GLNotifier

        GLSignals = GLNotifier(parent=self)
        GLSignals.emitPaintEvent()

    def _buildGLContours(self, glList, firstShow=False):
        # build a glList for the spectrum
        glList.clearArrays()

        numVertices = len(self.spectrum.positions)
        # glList.indices = numVertices
        glList.numVertices = numVertices
        # glList.indices = np.arange(numVertices, dtype=np.uint32)

        colour = self._getColour('sliceColour', '#AAAAAA')
        if not colour.startswith('#'):
            # get the colour from the gradient table or a single red
            colour = colorSchemeTable[colour][0] if colour in colorSchemeTable else '#FF0000'

        colR = int(colour.strip('# ')[0:2], 16) / 255.0
        colG = int(colour.strip('# ')[2:4], 16) / 255.0
        colB = int(colour.strip('# ')[4:6], 16) / 255.0

        glList.colors = np.array([colR, colG, colB, 1.0] * numVertices, dtype=np.float32)
        glList.vertices = np.zeros(numVertices * 2, dtype=np.float32)

        try:
            # may be empty
            glList.vertices[::2] = self.spectrum.positions
            glList.vertices[1::2] = self.spectrum.intensities
        except:
            pass

    def _paintContoursNoClip(self, plotHeight=0.0):
        # EJB not sure how to handle this
        pass
