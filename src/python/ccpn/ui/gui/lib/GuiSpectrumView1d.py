"""Module Documentation here

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
__dateModified__ = "$dateModified: 2021-01-29 01:01:07 +0000 (Fri, January 29, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
from ccpn.ui.gui.lib.GuiSpectrumView import GuiSpectrumView
from ccpn.util.Colour import spectrumColours, colorSchemeTable


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

    def getVisibleState(self):
        """Get the visible state for the X/Y axes
        """
        return (self._getSpectrumViewParams(0),)

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

    def refreshData(self):
        # self.spectrum._intensities = None  # UGLY, but need to force data to be reloaded
        self.data = self.spectrum.positions, self.spectrum.intensities

        # spawn a rebuild in the openGL strip
        self.buildContours = True
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
        # NOTE:ED - not sure how to handle this
        pass

    def _getVisiblePlaneList(self, firstVisible=None, minimumValuePerPoint=None):
        # No visible planes for 1d
        return None, None, None
