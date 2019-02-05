"""
Code for exporting OpenGL stripDisplay to pdf and svg files.
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
__dateModified__ = "$dateModified: 2018-12-20 16:42:44 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
from PyQt5 import QtWidgets
from reportlab.platypus import SimpleDocTemplate, Paragraph, Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.lib.pagesizes import A4
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import SPECTRUM_STACKEDMATRIX, SPECTRUM_MATRIX, \
    GLLINE_STYLES_ARRAY
from collections import OrderedDict, Iterable
import io
import numpy as np

try:
    from OpenGL import GL, GLU, GLUT
except ImportError:
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QMessageBox.critical(None, "OpenGL CCPN",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)
from reportlab.lib import colors
from reportlab.graphics import renderSVG, renderPS
from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Line, Group, Path
from reportlab.graphics.shapes import definePath
from reportlab.graphics.renderSVG import draw, renderScaledDrawing, SVGCanvas
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import A4, portrait, landscape
from reportlab.platypus.tables import Table
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from ccpn.util.Report import Report
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import GLFILENAME, GLGRIDLINES, GLAXISLABELS, GLAXISMARKS, \
    GLINTEGRALLABELS, GLINTEGRALSYMBOLS, GLMARKLABELS, GLMARKLINES, GLMULTIPLETLABELS, GLREGIONS, \
    GLMULTIPLETSYMBOLS, GLOTHERLINES, GLPEAKLABELS, GLPEAKSYMBOLS, GLPRINTTYPE, GLSELECTEDPIDS, \
    GLSPECTRUMBORDERS, GLSPECTRUMCONTOURS, GLSTRIP, GLSTRIPLABELLING, GLTRACES, GLWIDGET, GLPLOTBORDER, \
    GLPAGETYPE, GLSPECTRUMDISPLAY, GLAXISLINES, GLBACKGROUND, GLBASETHICKNESS, GLSYMBOLTHICKNESS, \
    GLFOREGROUND, GLSHOWSPECTRAONPHASE
from ccpn.ui.gui.popups.ExportStripToFile import EXPORTPDF, EXPORTSVG, EXPORTTYPES, \
    PAGEPORTRAIT, PAGELANDSCAPE, PAGETYPES
from ccpn.util.Logging import getLogger


PLOTLEFT = 'plotLeft'
PLOTBOTTOM = 'plotBottom'
PLOTWIDTH = 'plotWidth'
PLOTHEIGHT = 'plotHeight'

PDFSTROKEWIDTH = 'strokeWidth'
PDFSTROKECOLOR = 'strokeColor'
PDFSTROKELINECAP = 'strokeLineCap'
PDFFILLCOLOR = 'fillColor'
PDFFILL = 'fill'
PDFFILLMODE = 'fillMode'
PDFSTROKE = 'stroke'
PDFSTROKEDASHARRAY = 'strokeDashArray'
PDFCLOSEPATH = 'closePath'
PDFLINES = 'lines'


def alphaClip(value):
    return np.clip(float(value), 0.0, 1.0)


class GLExporter():
    """
    Class container for exporting OpenGL stripDisplay to a file or object
    """

    def __init__(self, parent, strip, filename, params):
        """
        Initialise the exporter
        :param fileName - not required:
        :param params - parameter dict from the exporter dialog:
        """
        self._parent = parent
        self.strip = strip
        self.project = self.strip.project
        self.filename = filename
        self.params = params

        # set the page orientation
        if self.params[GLPAGETYPE] == PAGEPORTRAIT:
            pageType = portrait
        else:
            pageType = landscape
        self._report = Report(self, self.project, filename, pagesize=pageType(A4))

        self._ordering = []
        self._importFonts()

        # set default colours
        # self.backgroundColour = colors.Color(*self._parent.background[0:3],
        #                                      alpha=alphaClip(self._parent.background[3]))
        self.backgroundColour = colors.Color(*self.params[GLBACKGROUND], alpha=alphaClip(1.0))
        # self.foregroundColour = colors.Color(*self._parent.foreground[0:3],
        #                                      alpha=alphaClip(self._parent.foreground[3]))
        self.foregroundColour = colors.Color(*self.params[GLFOREGROUND], alpha=alphaClip(1.0))

        self.baseThickness = self.params[GLBASETHICKNESS]
        self.symbolThickness = self.params[GLSYMBOLTHICKNESS]

        # build all the sections of the pdf
        self.stripReports = []
        self.stripWidths = []
        self.stripSpacing = 0

        if self.params[GLSPECTRUMDISPLAY]:
            spectrumDisplay = self.params[GLSPECTRUMDISPLAY]

            self.numStrips = len(spectrumDisplay.strips)
            for strip in spectrumDisplay.orderedStrips:
                # point to the correct strip
                self.strip = strip
                self._parent = strip._CcpnGLWidget

                self._buildPage()
                self._buildStrip()
                self._addDrawingToStory()
        else:
            self.numStrips = 1
            self.strip = self.params[GLSTRIP]
            self._parent = self.strip._CcpnGLWidget

            self._buildPage()
            self._buildStrip()
            self._addDrawingToStory()

        self._addTableToStory()

        # this generates the buffer to write to the file
        self._report.buildDocument()

    def _importFonts(self):
        import os
        from ccpn.framework.PathsAndUrls import fontsPath
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import SUBSTITUTEFONT

        # load all system fonts to find matches with OpenGl fonts
        for glFonts in self._parent.globalGL.fonts.values():
            pdfmetrics.registerFont(TTFont(glFonts.fontName, os.path.join(fontsPath, 'open-sans', SUBSTITUTEFONT + '.ttf')))

        # set a default fontName
        self.fontName = self._parent.globalGL.glSmallFont.fontName

    def _buildPage(self):
        """Build the main sections of the pdf file from a drawing object
        and add the drawing object to a reportlab document
        """
        dpi = 72  # drawing object and documents are hard-coded to this
        pageWidth = A4[0]
        pageHeight = A4[1]

        # keep aspect ratio of the original screen
        self.margin = 2.0 * cm

        self.main = True
        self.rAxis = self._parent._drawRightAxis
        self.bAxis = self._parent._drawBottomAxis

        if not self.rAxis and not self.bAxis:
            # no axes visible
            self.mainH = self._parent.h
            self.mainW = self._parent.w
            self.mainL = 0
            self.mainB = 0

        elif self.rAxis and not self.bAxis:
            # right axis visible
            self.rAxisW = self._parent.AXIS_MARGINRIGHT
            self.rAxisH = self._parent.h
            self.rAxisL = self._parent.w - self._parent.AXIS_MARGINRIGHT
            self.rAxisB = 0
            self.mainW = self._parent.w - self._parent.AXIS_MARGINRIGHT
            self.mainH = self._parent.h
            self.mainL = 0
            self.mainB = 0

        elif not self.rAxis and self.bAxis:
            # bottom axis visible
            self.bAxisW = self._parent.w
            self.bAxisH = self._parent.AXIS_MARGINBOTTOM
            self.bAxisL = 0
            self.bAxisB = 0
            self.mainW = self._parent.w
            self.mainH = self._parent.h - self._parent.AXIS_MARGINBOTTOM
            self.mainL = 0
            self.mainB = self._parent.AXIS_MARGINBOTTOM

        else:
            # both axes visible
            self.rAxisW = self._parent.AXIS_MARGINRIGHT
            self.rAxisH = self._parent.h - self._parent.AXIS_MARGINBOTTOM
            self.rAxisL = self._parent.w - self._parent.AXIS_MARGINRIGHT
            self.rAxisB = self._parent.AXIS_MARGINBOTTOM
            self.bAxisW = self._parent.w - self._parent.AXIS_MARGINRIGHT
            self.bAxisH = self._parent.AXIS_MARGINBOTTOM
            self.bAxisL = 0
            self.bAxisB = 0
            self.mainW = self._parent.w - self._parent.AXIS_MARGINRIGHT
            self.mainH = self._parent.h - self._parent.AXIS_MARGINBOTTOM
            self.mainL = 0
            self.mainB = self._parent.AXIS_MARGINBOTTOM

        # stripFrame ratio
        frame = self.strip.spectrumDisplay.stripFrame
        fh = frame.height()
        fw = frame.width()
        frameRatio = fh / fw

        self.pixHeight = self._report.doc.height - (2.0 * cm)
        self.pixWidth = self.pixHeight / frameRatio
        # self.fontScale = 1.025 * self.pixHeight / self._parent.h
        self.fontScale = self.pixHeight / self._parent.h

        # strip axis ratio
        ratio = self._parent.h / self._parent.w

        # translate to size of drawing Flowable
        self.pixWidth = self._report.doc.width / (fw / self._parent.w)  #self.numStrips
        self.pixHeight = self.pixWidth * ratio

        # scale fonts to appear the correct size
        self.fontScale = 1.0 * self.pixWidth / self._parent.w  #   1.1

        # if too tall then flip the scaling
        if self.pixHeight > (self._report.doc.height - 2 * cm):
            self.pixHeight = self._report.doc.height - (2 * cm)
            self.pixWidth = self.pixHeight / ratio
            self.fontScale = 1.0 * self.pixHeight / self._parent.h  # 1.025

        self.fontXOffset = 0.75
        self.fontYOffset = 3.0

        # pixWidth/self.pixHeight are now the dimensions in points for the Flowable
        self.displayScale = self.pixHeight / self._parent.h

        # don't think these are needed
        pixBottom = pageHeight - self.pixHeight - self.margin
        pixLeft = self.margin

        # assume that the spacing between strips is 5 pixels
        self.stripSpacing = 5.0 * self.displayScale

    def _buildStrip(self):
        # create an object that can be added to a report
        self._mainPlot = Drawing(self.pixWidth, self.pixHeight)

        gr = Group()
        # paint a background box
        ll = [0.0, 0.0,
              0.0, self.pixHeight,
              self.pixWidth, self.pixHeight,
              self.pixWidth, 0.0]

        if ll:
            pl = Path(fillColor=self.backgroundColour, stroke=None, strokeColor=None)
            pl.moveTo(ll[0], ll[1])
            for vv in range(2, len(ll), 2):
                pl.lineTo(ll[vv], ll[vv + 1])
            pl.closePath()
            gr.add(pl)

        # frame the top-left of the main plot area
        ll = [self.displayScale * self.mainL, self.displayScale * self.mainB,
              self.displayScale * self.mainL, self.pixHeight,
              self.displayScale * self.mainW, self.pixHeight]

        if ll and self.params[GLPLOTBORDER]:
            pl = Path(strokeColor=self.foregroundColour, strokeWidth=0.5)
            pl.moveTo(ll[0], ll[1])
            for vv in range(2, len(ll), 2):
                pl.lineTo(ll[vv], ll[vv + 1])
            gr.add(pl)

        # add to the drawing object
        self._mainPlot.add(gr, name='mainPlotBox')

        self._ordering = self.strip.spectrumDisplay.orderedSpectrumViews(self.strip.spectrumViews)

        # print the objects
        if self.params[GLGRIDLINES]: self._addGridLines()

        # check parameters to decide what to print

        if not self._parent.spectrumDisplay.is1D or \
                not self._parent.spectrumDisplay.phasingFrame.isVisible() or \
                self.params[GLSHOWSPECTRAONPHASE]:

            if self.params[GLSPECTRUMCONTOURS]: self._addSpectrumContours()
            if self.params[GLSPECTRUMBORDERS]: self._addSpectrumBoundaries()

        if not self._parent._stackingMode:
            if self.params[GLINTEGRALSYMBOLS]: self._addIntegralAreas()
            if self.params[GLINTEGRALSYMBOLS]: self._addIntegralLines()
            if self.params[GLPEAKSYMBOLS]: self._addPeakSymbols()
            if self.params[GLMULTIPLETSYMBOLS]: self._addMultipletSymbols()
            if self.params[GLMARKLINES]: self._addMarkLines()
            if self.params[GLREGIONS]: self._addRegions()
            if self.params[GLPEAKLABELS]: self._addPeakLabels()
            if self.params[GLINTEGRALLABELS]: self._addIntegralLabels()
            if self.params[GLMULTIPLETLABELS]: self._addMultipletLabels()
            if self.params[GLMARKLABELS]: self._addMarkLabels()

        if self.params[GLTRACES]: self._addTraces()

        if not self._parent._stackingMode:
            if self.params[GLOTHERLINES]: self._addInfiniteLines()
        if self.params[GLSTRIPLABELLING]: self._addOverlayText()

        self._addAxisMask()
        self._addGridTickMarks()
        if self.params[GLAXISLABELS]: self._addGridLabels()

    def _addGridLines(self):
        """
        Add grid lines to the main drawing area.
        """
        if self.strip.gridVisible:
            colourGroups = OrderedDict()
            self._appendIndexLineGroup(indArray=self._parent.gridList[0],
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT  : self.displayScale * self.mainL,
                                                PLOTBOTTOM: self.displayScale * self.mainB,
                                                PLOTWIDTH : self.displayScale * self.mainW,
                                                PLOTHEIGHT: self.displayScale * self.mainH},
                                       name='grid',
                                       ratioLine=True)
            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='grid')

    def _addSpectrumContours(self):
        """
        Add the spectrum contours to the main drawing area.
        """
        colourGroups = OrderedDict()
        for spectrumView in self._ordering:

            if spectrumView.isDeleted:
                continue

            # if spectrumView.isVisible():
            if spectrumView.spectrum.pid in self.params[GLSELECTEDPIDS]:

                if spectrumView.spectrum.dimensionCount > 1:
                    if spectrumView in self._parent._spectrumSettings.keys():
                        # self.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
                        #                                            1, GL.GL_FALSE,
                        #                                            self._spectrumSettings[spectrumView][SPECTRUM_MATRIX])

                        mat = np.transpose(self._parent._spectrumSettings[spectrumView][SPECTRUM_MATRIX].reshape((4, 4)))
                        # mat = np.transpose(self._parent._spectrumSettings[spectrumView][SPECTRUM_MATRIX].reshape((4, 4)))

                        thisSpec = self._parent._contourList[spectrumView]

                        # drawVertexColor
                        # gr = Group()
                        for ii in range(0, len(thisSpec.indices), 2):
                            ii0 = int(thisSpec.indices[ii])
                            ii1 = int(thisSpec.indices[ii + 1])

                            vectStart = [thisSpec.vertices[ii0 * 2], thisSpec.vertices[ii0 * 2 + 1], 0.0, 1.0]
                            vectStart = mat.dot(vectStart)
                            vectEnd = [thisSpec.vertices[ii1 * 2], thisSpec.vertices[ii1 * 2 + 1], 0.0, 1.0]
                            vectEnd = mat.dot(vectEnd)
                            newLine = [vectStart[0], vectStart[1], vectEnd[0], vectEnd[1]]

                            colour = colors.Color(*thisSpec.colors[ii0 * 4:ii0 * 4 + 3], alpha=alphaClip(thisSpec.colors[ii0 * 4 + 3]))
                            colourPath = 'spectrumViewContours%s%s%s%s%s' % (spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                            newLine = self._parent.lineVisible(newLine,
                                                               x=self.displayScale * self.mainL,
                                                               y=self.displayScale * self.mainB,
                                                               width=self.displayScale * self.mainW,
                                                               height=self.displayScale * self.mainH)
                            if newLine:
                                if colourPath not in colourGroups:
                                    colourGroups[colourPath] = {PDFLINES      : [],
                                                                PDFSTROKEWIDTH: 0.5 * self.baseThickness,
                                                                PDFSTROKECOLOR: colour, PDFSTROKELINECAP: 1}
                                colourGroups[colourPath][PDFLINES].append(newLine)

                else:

                    # assume that the vertexArray is a GL_LINE_STRIP
                    if spectrumView in self._parent._contourList.keys():
                        if self._parent._stackingMode:
                            mat = np.transpose(self._parent._spectrumSettings[spectrumView][SPECTRUM_STACKEDMATRIX].reshape((4, 4)))
                        else:
                            mat = None

                        thisSpec = self._parent._contourList[spectrumView]

                        # drawVertexColor
                        self._appendVertexLineGroup(indArray=thisSpec,
                                                    colourGroups=colourGroups,
                                                    plotDim={PLOTLEFT  : self.displayScale * self.mainL,
                                                             PLOTBOTTOM: self.displayScale * self.mainB,
                                                             PLOTWIDTH : self.displayScale * self.mainW,
                                                             PLOTHEIGHT: self.displayScale * self.mainH},
                                                    name='spectrumContours%s' % spectrumView.pid,
                                                    mat=mat)
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='boundaries')

    def _addSpectrumBoundaries(self):
        """
        Add the spectrum boundaries to the main drawing area.
        """
        colourGroups = OrderedDict()
        for spectrumView in self._ordering:
            if spectrumView.isDeleted:
                continue

            # if spectrumView.isVisible() and spectrumView.spectrum.dimensionCount > 1:
            if spectrumView.spectrum.pid in self.params[GLSELECTEDPIDS] and spectrumView.spectrum.dimensionCount > 1:
                self._spectrumValues = spectrumView._getValues(dimensionCount=2)

                # get the bounding box of the spectra
                fx0, fx1 = self._spectrumValues[0].maxAliasedFrequency, self._spectrumValues[0].minAliasedFrequency
                if spectrumView.spectrum.dimensionCount > 1:
                    fy0, fy1 = self._spectrumValues[1].maxAliasedFrequency, self._spectrumValues[1].minAliasedFrequency
                    colour = colors.Color(*spectrumView.posColour[0:3], alpha=alphaClip(0.5))
                else:
                    fy0, fy1 = np.max(spectrumView.spectrum.intensities), np.min(spectrumView.spectrum.intensities)

                    colour = spectrumView.sliceColour
                    colR = int(colour.strip('# ')[0:2], 16) / 255.0
                    colG = int(colour.strip('# ')[2:4], 16) / 255.0
                    colB = int(colour.strip('# ')[4:6], 16) / 255.0

                    colour = colors.Color(colR, colG, colB, alpha=alphaClip(0.5))

                colourPath = 'spectrumViewBoundaries%s%s%s%s%s' % (
                    spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                # generate the bounding box
                newLine = [fx0, fy0, fx0, fy1, fx1, fy1, fx1, fy0, fx0, fy0]
                newLine = self._parent.lineVisible(newLine,
                                                   x=self.displayScale * self.mainL,
                                                   y=self.displayScale * self.mainB,
                                                   width=self.displayScale * self.mainW,
                                                   height=self.displayScale * self.mainH)
                if newLine:
                    if colourPath not in colourGroups:
                        colourGroups[colourPath] = {PDFLINES        : [],
                                                    PDFSTROKEWIDTH  : 0.5 * self.baseThickness,
                                                    PDFSTROKECOLOR  : colour,
                                                    PDFSTROKELINECAP: 1, PDFCLOSEPATH: False}
                    colourGroups[colourPath][PDFLINES].append(newLine)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='boundaries')

    def _addPeakSymbols(self):
        """
        Add the peak symbols to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroupFill(indArray=self._parent._GLPeaks._GLSymbols,
                                       listView='peakList',
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT  : self.displayScale * self.mainL,
                                                PLOTBOTTOM: self.displayScale * self.mainB,
                                                PLOTWIDTH : self.displayScale * self.mainW,
                                                PLOTHEIGHT: self.displayScale * self.mainH},
                                       name='peakSymbols',
                                       fillMode=None,
                                       lineWidth=0.5 * self.baseThickness * self.symbolThickness)
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='peakSymbols')

    def _addMultipletSymbols(self):
        """
        Add the multiplet symbols to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroupFill(indArray=self._parent._GLMultiplets._GLSymbols,
                                       listView='multipletList',
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT  : self.displayScale * self.mainL,
                                                PLOTBOTTOM: self.displayScale * self.mainB,
                                                PLOTWIDTH : self.displayScale * self.mainW,
                                                PLOTHEIGHT: self.displayScale * self.mainH},
                                       name='multipletSymbols',
                                       fillMode=None,
                                       lineWidth=0.5 * self.baseThickness * self.symbolThickness)
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='multipletSymbols')

    def _addMarkLines(self):
        """
        Add the mark lines to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroup(indArray=self._parent._marksList,
                                   colourGroups=colourGroups,
                                   plotDim={PLOTLEFT  : self.displayScale * self.mainL,
                                            PLOTBOTTOM: self.displayScale * self.mainB,
                                            PLOTWIDTH : self.displayScale * self.mainW,
                                            PLOTHEIGHT: self.displayScale * self.mainH},
                                   name='marks')
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='marks')

    def _addIntegralLines(self):
        """
        Add the integral lines to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroupFill(indArray=self._parent._GLIntegrals._GLSymbols,
                                       listView='integralList',
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT  : self.displayScale * self.mainL,
                                                PLOTBOTTOM: self.displayScale * self.mainB,
                                                PLOTWIDTH : self.displayScale * self.mainW,
                                                PLOTHEIGHT: self.displayScale * self.mainH},
                                       name='IntegralListsFill',
                                       fillMode=GL.GL_FILL,
                                       splitGroups=True)
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='integralLists')

    def _addIntegralAreas(self):
        """
        Add the integral filled areas to the main drawing area.
        """
        colourGroups = OrderedDict()
        for spectrumView in self._ordering:
            if spectrumView.isDeleted:
                continue

            validIntegralListViews = [pp for pp in spectrumView.integralListViews
                                      if pp.isVisible()
                                      and spectrumView.isVisible()
                                      and pp in self._parent._GLIntegrals._GLSymbols.keys()
                                      and pp.integralList.pid in self.params[GLSELECTEDPIDS]]

            for integralListView in validIntegralListViews:  # spectrumView.integralListViews:
                mat = None
                if spectrumView.spectrum.dimensionCount > 1:
                    if spectrumView in self._parent._spectrumSettings.keys():
                        # draw
                        pass

                else:

                    # assume that the vertexArray is a GL_LINE_STRIP
                    if spectrumView in self._parent._contourList.keys():
                        if self._parent._stackingMode:
                            mat = np.transpose(self._parent._spectrumSettings[spectrumView][SPECTRUM_STACKEDMATRIX].reshape((4, 4)))
                        else:
                            mat = None

                # draw the integralAreas if they exist
                for integralArea in self._parent._GLIntegrals._GLSymbols[integralListView]._regions:
                    if hasattr(integralArea, '_integralArea'):

                        thisSpec = integralArea._integralArea
                        for vv in range(0, len(thisSpec.vertices) - 4, 2):

                            if mat is not None:

                                vectStart = [thisSpec.vertices[vv], thisSpec.vertices[vv + 1], 0.0, 1.0]
                                vectStart = mat.dot(vectStart)
                                vectMid = [thisSpec.vertices[vv + 2], thisSpec.vertices[vv + 3], 0.0, 1.0]
                                vectMid = mat.dot(vectMid)
                                vectEnd = [thisSpec.vertices[vv + 4], thisSpec.vertices[vv + 5], 0.0, 1.0]
                                vectEnd = mat.dot(vectEnd)
                                newLine = [vectStart[0], vectStart[1],
                                           vectMid[0], vectMid[1],
                                           vectEnd[0], vectEnd[1]]
                            else:
                                newLine = list(thisSpec.vertices[vv:vv + 6])

                            colour = colors.Color(*thisSpec.colors[vv * 2:vv * 2 + 3], alpha=alphaClip(thisSpec.colors[vv * 2 + 3]))
                            colourPath = 'spectrumViewIntegralFill%s%s%s%s%s' % (
                                spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                            newLine = self._parent.lineVisible(newLine,
                                                               x=self.displayScale * self.mainL,
                                                               y=self.displayScale * self.mainB,
                                                               width=self.displayScale * self.mainW,
                                                               height=self.displayScale * self.mainH)
                            if newLine:
                                if colourPath not in colourGroups:
                                    colourGroups[colourPath] = {PDFLINES: [], PDFFILLCOLOR: colour, PDFSTROKE: None, PDFSTROKECOLOR: None}
                                colourGroups[colourPath][PDFLINES].append(newLine)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='integralListsAreaFill')

    def _addRegions(self):
        """
        Add the regions to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroup(indArray=self._parent._externalRegions,
                                   colourGroups=colourGroups,
                                   plotDim={PLOTLEFT  : self.displayScale * self.mainL,
                                            PLOTBOTTOM: self.displayScale * self.mainB,
                                            PLOTWIDTH : self.displayScale * self.mainW,
                                            PLOTHEIGHT: self.displayScale * self.mainH},
                                   name='regions')
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='regions')

    def _addPeakLabels(self):
        """
        Add the peak labels to the main drawing area.
        """
        colourGroups = OrderedDict()
        for spectrumView in self._ordering:
            if spectrumView.isDeleted:
                continue

            validPeakListViews = [pp for pp in spectrumView.peakListViews
                                  if pp.isVisible()
                                  and spectrumView.isVisible()
                                  and pp in self._parent._GLPeaks._GLLabels.keys()
                                  and pp.peakList.pid in self.params[GLSELECTEDPIDS]]

            for peakListView in validPeakListViews:  # spectrumView.peakListViews:
                for drawString in self._parent._GLPeaks._GLLabels[peakListView].stringList:

                    col = drawString.colors[0]
                    if not isinstance(col, Iterable):
                        col = drawString.colors[0:4]
                    colour = colors.Color(*col[0:3], alpha=alphaClip(col[3]))
                    colourPath = 'spectrumViewPeakLabels%s%s%s%s%s' % (
                        spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                    newLine = [drawString.attribs[0], drawString.attribs[1]]
                    if self._parent.pointVisible(newLine,
                                                 x=self.displayScale * self.mainL,
                                                 y=self.displayScale * self.mainB,
                                                 width=self.displayScale * self.mainW,
                                                 height=self.displayScale * self.mainH):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()
                        textGroup = drawString.text.split('\n')
                        textLine = len(textGroup) - 1
                        for text in textGroup:
                            colourGroups[colourPath].add(String(newLine[0], newLine[1] + (textLine * drawString.font.fontSize * self.fontScale),
                                                                text,
                                                                fontSize=drawString.font.fontSize * self.fontScale,
                                                                fontName=drawString.font.fontName,
                                                                fillColor=colour))
                            textLine -= 1

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addIntegralLabels(self):
        """
        Add the integral labels to the main drawing area.
        """
        colourGroups = OrderedDict()
        for spectrumView in self._ordering:
            if spectrumView.isDeleted:
                continue

            validIntegralListViews = [pp for pp in spectrumView.integralListViews
                                      if pp.isVisible()
                                      and spectrumView.isVisible()
                                      and pp in self._parent._GLIntegrals._GLLabels.keys()
                                      and pp.integralList.pid in self.params[GLSELECTEDPIDS]]

            for integralListView in validIntegralListViews:  # spectrumView.integralListViews:
                for drawString in self._parent._GLIntegrals._GLLabels[integralListView].stringList:

                    col = drawString.colors[0]
                    if not isinstance(col, Iterable):
                        col = drawString.colors[0:4]
                    colour = colors.Color(*col[0:3], alpha=alphaClip(col[3]))
                    colourPath = 'spectrumViewIntegralLabels%s%s%s%s%s' % (
                        spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                    newLine = [drawString.attribs[0], drawString.attribs[1]]
                    if self._parent.pointVisible(newLine,
                                                 x=self.displayScale * self.mainL,
                                                 y=self.displayScale * self.mainB,
                                                 width=self.displayScale * self.mainW,
                                                 height=self.displayScale * self.mainH):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()
                        textGroup = drawString.text.split('\n')
                        textLine = len(textGroup) - 1
                        for text in textGroup:
                            colourGroups[colourPath].add(String(newLine[0], newLine[1] + (textLine * drawString.font.fontSize * self.fontScale),
                                                                text,
                                                                fontSize=drawString.font.fontSize * self.fontScale,
                                                                fontName=drawString.font.fontName,
                                                                fillColor=colour))
                            textLine -= 1

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addMultipletLabels(self):
        """
        Add the multiplet labels to the main drawing area.
        """
        colourGroups = OrderedDict()
        for spectrumView in self._ordering:
            if spectrumView.isDeleted:
                continue

            validMultipletListViews = [pp for pp in spectrumView.multipletListViews
                                       if pp.isVisible()
                                       and spectrumView.isVisible()
                                       and pp in self._parent._GLMultiplets._GLLabels.keys()
                                       and pp.multipletList.pid in self.params[GLSELECTEDPIDS]]

            for multipletListView in validMultipletListViews:  # spectrumView.multipletListViews:
                for drawString in self._parent._GLMultiplets._GLLabels[multipletListView].stringList:

                    col = drawString.colors[0]
                    if not isinstance(col, Iterable):
                        col = drawString.colors[0:4]
                    colour = colors.Color(*col[0:3], alpha=alphaClip(col[3]))
                    colourPath = 'spectrumViewMultipletLabels%s%s%s%s%s' % (
                        spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                    newLine = [drawString.attribs[0], drawString.attribs[1]]
                    if self._parent.pointVisible(newLine,
                                                 x=self.displayScale * self.mainL,
                                                 y=self.displayScale * self.mainB,
                                                 width=self.displayScale * self.mainW,
                                                 height=self.displayScale * self.mainH):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()
                        textGroup = drawString.text.split('\n')
                        textLine = len(textGroup) - 1
                        for text in textGroup:
                            colourGroups[colourPath].add(String(newLine[0], newLine[1] + (textLine * drawString.font.fontSize * self.fontScale),
                                                                text,
                                                                fontSize=drawString.font.fontSize * self.fontScale,
                                                                fontName=drawString.font.fontName,
                                                                fillColor=colour))
                            textLine -= 1

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addMarkLabels(self):
        """
        Add the mark labels to the main drawing area.
        """
        colourGroups = OrderedDict()
        for drawString in self._parent._marksAxisCodes:
            # drawString.drawTextArrayVBO(enableVBO=True)

            col = drawString.colors[0]
            if not isinstance(col, Iterable):
                col = drawString.colors[0:4]
            colour = colors.Color(*col[0:3], alpha=alphaClip(col[3]))
            colourPath = 'projectMarks%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

            newLine = [drawString.attribs[0], drawString.attribs[1]]
            if self._parent.pointVisible(newLine,
                                         x=self.displayScale * self.mainL,
                                         y=self.displayScale * self.mainB,
                                         width=self.displayScale * self.mainW,
                                         height=self.displayScale * self.mainH):
                if colourPath not in colourGroups:
                    colourGroups[colourPath] = Group()
                self._addString(colourGroups, colourPath, drawString, newLine, colour, boxed=False)

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addTraces(self):
        """
        Add the traces to the main drawing area.
        """
        colourGroups = OrderedDict()
        for hTrace in self._parent._staticHTraces:
            if hTrace.spectrumView and not hTrace.spectrumView.isDeleted and hTrace.spectrumView.isVisible():
                # drawVertexColor

                if self._parent._stackingMode:
                    mat = np.transpose(self._parent._spectrumSettings[hTrace.spectrumView][SPECTRUM_STACKEDMATRIX].reshape((4, 4)))
                else:
                    mat = None

                self._appendVertexLineGroup(indArray=hTrace,
                                            colourGroups=colourGroups,
                                            plotDim={PLOTLEFT  : self.displayScale * self.mainL,
                                                     PLOTBOTTOM: self.displayScale * self.mainB,
                                                     PLOTWIDTH : self.displayScale * self.mainW,
                                                     PLOTHEIGHT: self.displayScale * self.mainH},
                                            name='hTrace%s' % hTrace.spectrumView.pid,
                                            includeLastVertex=not self._parent.is1D,
                                            mat=mat)

        for vTrace in self._parent._staticVTraces:
            if vTrace.spectrumView and not vTrace.spectrumView.isDeleted and vTrace.spectrumView.isVisible():
                # drawVertexColor

                if self._parent._stackingMode:
                    mat = np.transpose(self._parent._spectrumSettings[vTrace.spectrumView][SPECTRUM_STACKEDMATRIX].reshape((4, 4)))
                else:
                    mat = None

                self._appendVertexLineGroup(indArray=vTrace,
                                            colourGroups=colourGroups,
                                            plotDim={PLOTLEFT  : self.displayScale * self.mainL,
                                                     PLOTBOTTOM: self.displayScale * self.mainB,
                                                     PLOTWIDTH : self.displayScale * self.mainW,
                                                     PLOTHEIGHT: self.displayScale * self.mainH},
                                            name='vTrace%s' % vTrace.spectrumView.pid,
                                            includeLastVertex=not self._parent.is1D,
                                            mat=mat)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='traces')

    def _addInfiniteLines(self):
        """
        Add the infinite lines to the main drawing area.
        """
        colourGroups = OrderedDict()
        for infLine in self._parent._infiniteLines:
            if infLine.visible:
                colour = colors.Color(*infLine.brush[0:3], alpha=alphaClip(infLine.brush[3]))
                colourPath = 'infiniteLines%s%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha, infLine.lineStyle)

                if infLine.orientation == 'h':
                    newLine = [self._parent.axisL, infLine.values, self._parent.axisR, infLine.values]
                else:
                    newLine = [infLine.values, self._parent.axisT, infLine.values, self._parent.axisB]

                newLine = self._parent.lineVisible(newLine,
                                                   x=self.displayScale * self.mainL,
                                                   y=self.displayScale * self.mainB,
                                                   width=self.displayScale * self.mainW,
                                                   height=self.displayScale * self.mainH)
                if newLine:
                    if colourPath not in colourGroups:
                        colourGroups[colourPath] = {PDFLINES          : [], PDFSTROKEWIDTH: 0.5 * infLine.lineWidth, PDFSTROKECOLOR: colour,
                                                    PDFSTROKELINECAP  : 1, PDFCLOSEPATH: False,
                                                    PDFSTROKEDASHARRAY: GLLINE_STYLES_ARRAY[infLine.lineStyle]}
                    colourGroups[colourPath][PDFLINES].append(newLine)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='infiniteLines')

    def _scaleRatioToWindow(self, values):
        return [values[0] * (self._parent.axisR - self._parent.axisL) + self._parent.axisL,
                values[1] * (self._parent.axisT - self._parent.axisB) + self._parent.axisB]

    def _addOverlayText(self):
        """
        Add the overlay text to the main drawing area.
        """
        colourGroups = OrderedDict()
        drawString = self._parent.stripIDString

        colour = self.foregroundColour
        colourPath = 'overlayText%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

        # newLine = [drawString.attribs[0], drawString.attribs[1]]
        # newLine = self._scaleRatioToWindow(drawString.attribs[0:2])

        newLine = self._scaleRatioToWindow([drawString.attribs[0] + (self.fontXOffset * self._parent.deltaX),
                                            drawString.attribs[1] + (self.fontYOffset * self._parent.deltaY)])

        if self._parent.pointVisible(newLine,
                                     x=self.displayScale * self.mainL,
                                     y=self.displayScale * self.mainB,
                                     width=self.displayScale * self.mainW,
                                     height=self.displayScale * self.mainH):
            pass

        if colourPath not in colourGroups:
            colourGroups[colourPath] = Group()
        self._addString(colourGroups, colourPath, drawString, newLine, colour, boxed=True)

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addAxisMask(self):
        """
        Add a mask to clean the right/bottom axis areas.
        """
        ll1 = None
        ll2 = None
        if self.rAxis and self.bAxis:
            ll1 = [0.0, 0.0,
                   0.0, self.displayScale * self.mainB,
                   self.displayScale * self.mainW, self.displayScale * self.mainB,
                   self.displayScale * self.mainW, self.pixHeight,
                   self.pixWidth, self.pixHeight,
                   self.pixWidth, 0.0]
            ll2 = [0.0, 0.0, self.pixWidth, 0.0, self.pixWidth, self.pixHeight]

        elif self.rAxis:
            ll1 = [self.displayScale * self.mainW, 0.0,
                   self.displayScale * self.mainW, self.pixHeight,
                   self.pixWidth, self.pixHeight,
                   self.pixWidth, 0.0]
            ll2 = [self.pixWidth, 0.0, self.pixWidth, self.pixHeight]

        elif self.bAxis:
            ll1 = [0.0, 0.0,
                   0.0, self.displayScale * self.mainB,
                   self.pixWidth, self.displayScale * self.mainB,
                   self.pixWidth, 0.0]
            ll2 = [0.0, 0.0, self.pixWidth, 0.0]

        if ll1:
            pl = Path(fillColor=self.backgroundColour, stroke=None, strokeColor=None)
            pl.moveTo(ll1[0], ll1[1])
            for vv in range(2, len(ll1), 2):
                pl.lineTo(ll1[vv], ll1[vv + 1])
            pl.closePath()
            self._mainPlot.add(pl)

            pl = Path(fillColor=None, strokeColor=self.backgroundColour, strokeWidth=1.0)
            pl.moveTo(ll2[0], ll2[1])
            for vv in range(2, len(ll2), 2):
                pl.lineTo(ll2[vv], ll2[vv + 1])
            self._mainPlot.add(pl)

    def _addGridTickMarks(self):
        """
        Add tick marks to the main drawing area.
        """
        if self.rAxis or self.bAxis:
            colourGroups = OrderedDict()
            if self.rAxis:
                if self.params[GLAXISMARKS]:
                    self._appendIndexLineGroup(indArray=self._parent.gridList[1],
                                               colourGroups=colourGroups,
                                               plotDim={PLOTLEFT  : self.displayScale * (self.mainW - self._parent.AXIS_LINE),
                                                        PLOTBOTTOM: self.displayScale * self.mainB,
                                                        PLOTWIDTH : self.displayScale * self._parent.AXIS_LINE,
                                                        PLOTHEIGHT: self.displayScale * self.mainH},
                                               name='gridAxes',
                                               setColour=self.foregroundColour,
                                               ratioLine=True)
                    if self.params[GLPLOTBORDER] or self.params[GLAXISLINES]:
                        list(colourGroups.values())[0][PDFLINES].append([self.displayScale * self.mainW, self.displayScale * self.mainB,
                                                                         self.displayScale * self.mainW, self.pixHeight])
                elif self.params[GLPLOTBORDER] or self.params[GLAXISLINES]:
                    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray

                    tempVertexArray = GLVertexArray(numLists=1, drawMode=GL.GL_LINE, dimension=2)
                    tempVertexArray.indices = [0, 1]
                    tempVertexArray.vertices = [0.0, 0.0, 0.0, 0.0]

                    self._appendIndexLineGroup(indArray=tempVertexArray,
                                               colourGroups=colourGroups,
                                               plotDim={PLOTLEFT  : self.displayScale * (self.mainW - self._parent.AXIS_LINE),
                                                        PLOTBOTTOM: self.displayScale * self.mainB,
                                                        PLOTWIDTH : self.displayScale * self._parent.AXIS_LINE,
                                                        PLOTHEIGHT: self.displayScale * self.mainH},
                                               name='gridAxes',
                                               setColour=self.foregroundColour,
                                               ratioLine=True)
                    list(colourGroups.values())[0][PDFLINES] = [[self.displayScale * self.mainW, self.displayScale * self.mainB,
                                                                 self.displayScale * self.mainW, self.pixHeight]]

            if self.bAxis:
                if self.params[GLAXISMARKS]:
                    self._appendIndexLineGroup(indArray=self._parent.gridList[2],
                                               colourGroups=colourGroups,
                                               plotDim={PLOTLEFT  : 0.0,
                                                        PLOTBOTTOM: self.displayScale * self.mainB,
                                                        PLOTWIDTH : self.displayScale * self.mainW,
                                                        PLOTHEIGHT: self.displayScale * self._parent.AXIS_LINE},
                                               name='gridAxes',
                                               setColour=self.foregroundColour,
                                               ratioLine=True)
                    if self.params[GLPLOTBORDER] or self.params[GLAXISLINES]:
                        list(colourGroups.values())[0][PDFLINES].append([0.0, self.displayScale * self.bAxisH,
                                                                         self.displayScale * self.mainW, self.displayScale * self.bAxisH])
                elif self.params[GLPLOTBORDER] or self.params[GLAXISLINES]:
                    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray

                    tempVertexArray = GLVertexArray(numLists=1, drawMode=GL.GL_LINE, dimension=2)
                    tempVertexArray.indices = [0, 1]
                    tempVertexArray.vertices = [0.0, 0.0, 0.0, 0.0]

                    self._appendIndexLineGroup(indArray=tempVertexArray,
                                               colourGroups=colourGroups,
                                               plotDim={PLOTLEFT  : self.displayScale * (self.mainW - self._parent.AXIS_LINE),
                                                        PLOTBOTTOM: self.displayScale * self.mainB,
                                                        PLOTWIDTH : self.displayScale * self._parent.AXIS_LINE,
                                                        PLOTHEIGHT: self.displayScale * self.mainH},
                                               name='gridAxes',
                                               setColour=self.foregroundColour,
                                               ratioLine=True)

                    # if the rAxis is not visible then just set this line, otherwise append to the above line
                    if not self.rAxis:
                        list(colourGroups.values())[0][PDFLINES] = []
                    list(colourGroups.values())[0][PDFLINES].append([0.0, self.displayScale * self.bAxisH,
                                                                     self.displayScale * self.mainW, self.displayScale * self.bAxisH])

            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='gridAxes')

    def _addString(self, colourGroups, colourPath, drawString, position, colour, boxed=False):
        newStr = String(position[0], position[1],
                        drawString.text,
                        fontSize=drawString.font.fontSize * self.fontScale,
                        fontName=drawString.font.fontName,
                        fillColor=colour)
        if boxed:
            bounds = newStr.getBounds()
            dx = drawString.font.fontSize * self.fontScale * 0.11  #bounds[0] - position[0]
            dy = drawString.font.fontSize * self.fontScale * 0.125  #(position[1] - bounds[1]) / 2.0
            colourGroups[colourPath].add(Rect(bounds[0] - dx, bounds[1] - dy,
                                              (bounds[2] - bounds[0]) + 5 * dx, (bounds[3] - bounds[1]) + 2.0 * dy,
                                              # newLine[0], newLine[1],
                                              # drawString.font.fontSize * self.fontScale * len(newLine),
                                              # drawString.font.fontSize * self.fontScale,
                                              strokeColor=None,
                                              fillColor=self.backgroundColour))
            # fillColor = colors.lightgreen))
        colourGroups[colourPath].add(newStr)

    def _addGridLabels(self):
        """
        Add marks to the right/bottom axis areas.
        """
        if self.rAxis or self.bAxis:
            colourGroups = OrderedDict()
            if self.rAxis:
                for strNum, drawString in enumerate(self._parent._axisYLabelling):

                    # skip empty strings
                    if not drawString.text:
                        continue

                    # drawTextArray
                    colour = self.foregroundColour
                    colourPath = 'axisLabels%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

                    # add (0, 3) to mid-point
                    # mid = self._parent.axisL + (0 + drawString.attribs[0]) * (self._parent.axisR - self._parent.axisL) / self._parent.AXIS_MARGINRIGHT
                    # newLine = [mid, drawString.attribs[1] + (3 * self._parent.pixelY)]
                    # mid = self._parent.axisL + drawString.attribs[0] * (self._parent.axisR - self._parent.axisL) * self._parent.pixelX
                    # newLine = [mid, drawString.attribs[1] + (3 * self._parent.deltaY)]

                    attribPos = (0.0, 0.0) if drawString.attribs.size < 2 else drawString.attribs[0:2]
                    newLine = self._scaleRatioToWindow([(self.fontXOffset + attribPos[0]) / self._parent.AXIS_MARGINRIGHT,
                                                        attribPos[1] + (self.fontYOffset * self._parent.deltaY)])

                    if self._parent.pointVisible(newLine,
                                                 x=self.displayScale * self.rAxisL,
                                                 y=self.displayScale * self.rAxisB,
                                                 width=self.displayScale * self.rAxisW,
                                                 height=self.displayScale * self.rAxisH):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()

                        # set box around the last 2 elements (name and dimensions)
                        self._addString(colourGroups, colourPath, drawString, newLine, colour,
                                        boxed=False if strNum < len(self._parent._axisYLabelling) - 2 else True)

            if self.bAxis:
                for strNum, drawString in enumerate(self._parent._axisXLabelling):

                    # skip empty strings
                    if not drawString.text:
                        continue

                    # drawTextArray
                    colour = self.foregroundColour
                    colourPath = 'axisLabels%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

                    # add (0, 3) to mid
                    # mid = self._parent.axisB + (3 + drawString.attribs[1]) * (self._parent.axisT - self._parent.axisB) / self._parent.AXIS_MARGINBOTTOM
                    # newLine = [drawString.attribs[0] + (0 * self._parent.pixelX), mid]
                    # mid = self._parent.axisB + drawString.attribs[1] * (self._parent.axisT - self._parent.axisB)
                    # newLine = [drawString.attribs[0] + (0 * self._parent.deltaX), mid]

                    attribPos = (0.0, 0.0) if drawString.attribs.size < 2 else drawString.attribs[0:2]
                    newLine = self._scaleRatioToWindow([attribPos[0] + (self.fontXOffset * self._parent.deltaX),
                                                        (self.fontYOffset + attribPos[1]) / self._parent.AXIS_MARGINBOTTOM])

                    if self._parent.pointVisible(newLine,
                                                 x=self.displayScale * self.bAxisL,
                                                 y=self.displayScale * self.bAxisB,
                                                 width=self.displayScale * self.bAxisW,
                                                 height=self.displayScale * self.bAxisH):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()

                        # set box around the last 2 elements (name and dimensions)
                        self._addString(colourGroups, colourPath, drawString, newLine, colour,
                                        boxed=False if strNum < len(self._parent._axisXLabelling) - 2 else True)

            for colourGroup in colourGroups.values():
                self._mainPlot.add(colourGroup)

    def report(self):
        """
        Return the current report for the GL widget.
        This is the vector image for the current strip containing the GL widget,
        it is a reportlab Flowable type object that can be added to reportlab documents.
        :return reportlab.platypus.Flowable:
        """
        scale = self.displayScale
        return Clipped_Flowable(width=self.pixWidth, height=self.pixHeight,
                                mainPlot=self._mainPlot,
                                mainDim={PLOTLEFT  : 0,  #scale*self.mainL,
                                         PLOTBOTTOM: 0,  #scale*self.mainB,
                                         PLOTWIDTH : self.pixWidth,  #scale*self.mainW,
                                         PLOTHEIGHT: self.pixHeight  #scale*self.mainH
                                         }
                                )

    def _addDrawingToStory(self):
        """
        Add the current drawing the story of a document
        """
        report = self.report()
        self.stripReports.append(report)
        self.stripWidths.append(report.width + self.stripSpacing)
        # report = self.report()
        # table = ((report, report, report, report),)
        # self._report.story.append(self.report())

    def _addTableToStory(self):
        table = (self.stripReports,)  # tuple
        self._report.story.append(Table(table, colWidths=self.stripWidths))

    def writeSVGFile(self):
        """
        Output an SVG file for the GL widget.
        """
        renderSVG.drawToFile(self._mainPlot, self.filename, showBoundary=False)

    def writePDFFile(self):
        """
        Output a PDF file for the GL widget.
        """
        self._report.writeDocument()

    def _appendVertexLineGroup(self, indArray, colourGroups, plotDim, name, mat=None,
                               includeLastVertex=False, lineWidth=0.5):
        for vv in range(0, len(indArray.vertices) - 2, 2):

            if mat is not None:

                vectStart = [indArray.vertices[vv], indArray.vertices[vv + 1], 0.0, 1.0]
                vectStart = mat.dot(vectStart)
                vectEnd = [indArray.vertices[vv + 2], indArray.vertices[vv + 3], 0.0, 1.0]
                vectEnd = mat.dot(vectEnd)
                newLine = [vectStart[0], vectStart[1], vectEnd[0], vectEnd[1]]
            else:
                newLine = list(indArray.vertices[vv:vv + 4])

            colour = colors.Color(*indArray.colors[vv * 2:vv * 2 + 3], alpha=alphaClip(indArray.colors[vv * 2 + 3]))
            colourPath = '%s%s%s%s%s' % (name, colour.red, colour.green, colour.blue, colour.alpha)
            if colourPath not in colourGroups:
                cc = colourGroups[colourPath] = {}
                if (indArray.fillMode or GL.GL_LINE) == GL.GL_LINE:
                    cc[PDFLINES] = []
                    cc[PDFSTROKEWIDTH] = lineWidth
                    cc[PDFSTROKECOLOR] = colour
                    cc[PDFSTROKELINECAP] = 1
                else:
                    # assume that it is GL.GL_FILL
                    cc[PDFLINES] = []
                    cc[PDFFILLCOLOR] = colour
                    cc[PDFSTROKE] = None
                    cc[PDFSTROKECOLOR] = None

            newLine = self._parent.lineVisible(newLine,
                                               x=plotDim[PLOTLEFT],
                                               y=plotDim[PLOTBOTTOM],
                                               width=plotDim[PLOTWIDTH],
                                               height=plotDim[PLOTHEIGHT])
            if newLine:
                colourGroups[colourPath][PDFLINES].append(newLine)

    def _appendIndexLineGroup(self, indArray, colourGroups, plotDim, name,
                              fillMode=None, splitGroups=False,
                              setColour=None, lineWidth=0.5, ratioLine=False):
        if indArray.drawMode == GL.GL_TRIANGLES:
            indexLen = 3
        elif indArray.drawMode == GL.GL_QUADS:
            indexLen = 4
        else:
            indexLen = 2

        # override so that each element is a new group
        if splitGroups:
            colourGroups = OrderedDict()

        for ii in range(0, len(indArray.indices), indexLen):
            ii0 = [int(ind) for ind in indArray.indices[ii:ii + indexLen]]

            newLine = []
            for vv in ii0:
                if ratioLine:
                    # convert ratio to axis coordinates
                    # newLine.extend([self._scaleRatioToWindow(indArray.vertices[vv * 2], (self._parent.axisR - self._parent.axisL), self._parent.axisL),
                    #                 self._scaleRatioToWindow(indArray.vertices[vv * 2 + 1], (self._parent.axisT - self._parent.axisB), self._parent.axisB)])

                    newLine.extend(self._scaleRatioToWindow(indArray.vertices[vv * 2:vv * 2 + 2]))
                else:
                    newLine.extend([indArray.vertices[vv * 2], indArray.vertices[vv * 2 + 1]])

            colour = (setColour or colors.Color(*indArray.colors[ii0[0] * 4:ii0[0] * 4 + 3], alpha=alphaClip(indArray.colors[ii0[0] * 4 + 3])))
            colourPath = 'spectrumView%s%s%s%s%s' % (name,
                                                     colour.red, colour.green, colour.blue, colour.alpha)

            # # override so that each element is a new group
            # if splitGroups:
            #     colourGroups = OrderedDict()

            if colourPath not in colourGroups:
                cc = colourGroups[colourPath] = {}
                if (fillMode or indArray.fillMode or GL.GL_LINE) == GL.GL_LINE:
                    cc[PDFLINES] = []
                    cc[PDFSTROKEWIDTH] = lineWidth
                    cc[PDFSTROKECOLOR] = colour
                    cc[PDFSTROKELINECAP] = 1
                else:
                    # assume that it is GL.GL_FILL
                    cc[PDFLINES] = []
                    cc[PDFFILLCOLOR] = colour
                    cc[PDFSTROKE] = None
                    cc[PDFSTROKECOLOR] = None

            newLine = self._parent.lineVisible(newLine,
                                               x=plotDim[PLOTLEFT],
                                               y=plotDim[PLOTBOTTOM],
                                               width=plotDim[PLOTWIDTH],
                                               height=plotDim[PLOTHEIGHT])
            if newLine:
                colourGroups[colourPath][PDFLINES].append(newLine)

        # override so that each element is a new group
        if splitGroups:
            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name=name)

    def _appendIndexLineGroupFill(self, indArray=None, listView=None, colourGroups=None, plotDim=None, name=None,
                                  fillMode=None, splitGroups=False, lineWidth=0.5):
        for spectrumView in self._ordering:
            if spectrumView.isDeleted:
                continue

            attribList = getattr(spectrumView, listView + 'Views')
            validListViews = [pp for pp in attribList
                              if pp.isVisible()
                              and spectrumView.isVisible()
                              and getattr(pp, listView).pid in self.params[GLSELECTEDPIDS]]

            for thisListView in validListViews:
                if thisListView in indArray.keys():
                    thisSpec = indArray[thisListView]
                    self._appendIndexLineGroup(indArray=thisSpec,
                                               colourGroups=colourGroups,
                                               plotDim=plotDim,
                                               name='spectrumView%s%s' % (name, spectrumView.pid),
                                               fillMode=fillMode,
                                               splitGroups=splitGroups,
                                               lineWidth=lineWidth)

    def _appendGroup(self, drawing: Drawing = None, colourGroups: dict = None, name: str = None):
        """
        Append a group of polylines to the current drawing object
        :param drawing - drawing to append groups to:
        :param colourGroups - OrderedDict of polylines:
        :param name - name for the group:
        """
        gr = Group()
        for colourItem in colourGroups.values():
            # pl = PolyLine(ll[PDFLINES], strokeWidth=ll[PDFSTROKEWIDTH], strokeColor=ll[PDFSTROKECOLOR], strokeLineCap=ll[PDFSTROKELINECAP])

            wanted_keys = [PDFSTROKEWIDTH,
                           PDFSTROKECOLOR,
                           PDFSTROKELINECAP,
                           PDFFILLCOLOR,
                           PDFFILL,
                           PDFFILLMODE,
                           PDFSTROKE,
                           PDFSTROKEDASHARRAY]

            newColour = dict((k, colourItem[k]) for k in wanted_keys if k in colourItem)

            pl = Path(
                    **newColour)  #  strokeWidth=colourItem[PDFSTROKEWIDTH], strokeColor=colourItem[PDFSTROKECOLOR], strokeLineCap=colourItem[PDFSTROKELINECAP])
            for ll in colourItem[PDFLINES]:
                if len(ll) == 4:
                    pl.moveTo(ll[0], ll[1])
                    pl.lineTo(ll[2], ll[3])
                else:
                    pl.moveTo(ll[0], ll[1])
                    for vv in range(2, len(ll), 2):
                        pl.lineTo(ll[vv], ll[vv + 1])
                    if PDFCLOSEPATH not in colourItem or (PDFCLOSEPATH in colourItem and colourItem[PDFCLOSEPATH] == True):
                        pl.closePath()
            gr.add(pl)
        drawing.add(gr, name=name)


class Clipped_Flowable(Flowable):
    def __init__(self, width=0.0, height=0.0,
                 mainPlot=None, mainDim=None):
        Flowable.__init__(self)
        self.mainPlot = mainPlot
        self.mainDim = mainDim
        self.width = width
        self.height = height

    def draw(self):
        if self.mainPlot:
            self.canv.saveState()

            # make a clippath for the mainPlot
            pl = self.canv.beginPath()
            pl.moveTo(self.mainDim[PLOTLEFT], self.mainDim[PLOTBOTTOM])
            pl.lineTo(self.mainDim[PLOTLEFT], self.mainDim[PLOTHEIGHT] + self.mainDim[PLOTBOTTOM])
            pl.lineTo(self.mainDim[PLOTLEFT] + self.mainDim[PLOTWIDTH], self.mainDim[PLOTHEIGHT] + self.mainDim[PLOTBOTTOM])
            pl.lineTo(self.mainDim[PLOTLEFT] + self.mainDim[PLOTWIDTH], self.mainDim[PLOTBOTTOM])
            pl.close()
            self.canv.clipPath(pl, fill=0, stroke=0)

            # draw the drawing into the canvas
            self.mainPlot.drawOn(self.canv, self.mainDim[PLOTLEFT], self.mainDim[PLOTBOTTOM])

        # restore preclipping state
        self.canv.restoreState()
        # draw the axes


if __name__ == '__main__':
    buf = io.BytesIO()

    # Setup the document with paper size and margins
    doc = SimpleDocTemplate(
            buf,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            pagesize=A4,
            )

    # Styling paragraphs
    styles = getSampleStyleSheet()

    # Write things on the document
    paragraphs = []
    paragraphs.append(
            Paragraph('This is a paragraph testing CCPN pdf generation', styles['Normal']))
    paragraphs.append(
            Paragraph('This is another paragraph', styles['Normal']))

    from reportlab.lib import colors
    from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Group
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas


    dpi = 72
    mmwidth = 150
    mmheight = 150
    pixWidth = int(mmwidth * mm)
    pixHeight = int(mmheight * mm)

    # the width doesn't mean anything, but the height defines how much space is added to the story
    # co-ordinates are origin bottom-left
    d = Drawing(pixWidth, pixHeight, )

    d.add(Rect(0.0, 0.0, pixWidth, pixHeight, fillColor=colors.yellow, stroke=0, fill=0))
    d.add(String(150.0, 100.0, 'Hello World', fontSize=18, fillColor=colors.red))
    d.add(String(180.0, 86.0, 'Special characters \
                            \xc2\xa2\xc2\xa9\xc2\xae\xc2\xa3\xce\xb1\xce\xb2',
                 fillColor=colors.red))

    pl = PolyLine([120, 110, 130, 150],
                  strokeWidth=2,
                  strokeColor=colors.red)
    d.add(pl)

    # pl = definePath(isClipPath=1)
    # pl.moveTo(30.0, 30.0)
    # pl.lineTo(30.0, pixHeight/2)
    # pl.lineTo(pixWidth/2, pixHeight/2)
    # pl.lineTo(pixWidth/2, 30.0)
    # pl.closePath()
    # d.add(pl)

    gr = Group()
    gr.add(Rect(0.0, 0.0, 20.0, 20.0, fillColor=colors.yellow))
    gr.add(Rect(30.0, 30.0, 20.0, 20.0, fillColor=colors.blue))
    d.add(gr)
    # d.add(Rect(0.0, 0.0, 20.0, 20.0, fillColor=colors.yellow))
    # d.add(Rect(30.0, 30.0, 20.0, 20.0, fillColor=colors.blue))

    # paragraphs.append(d)

    fred = Clipped_Flowable(d)
    paragraphs.append(fred)

    doc.pageCompression = None
    # this generates the buffer to write to the file
    doc.build(paragraphs)

    c = canvas.Canvas(filename='/Users/ejb66/Desktop/testCCPNpdf3.pdf', pagesize=A4)

    # make a clippath
    pl = c.beginPath()
    pl.moveTo(0, 0)
    pl.lineTo(0, 100)
    pl.lineTo(100, 100)
    pl.lineTo(100, 0)
    pl.close()
    c.clipPath(pl, fill=0, stroke=0)

    # draw the drawing to the canvas after clipping defined
    d.drawOn(c, 0, 0)
    c.save()

    # Write the PDF to a file
    with open('/Users/ejb66/Desktop/testCCPNpdf.pdf', 'wb') as fd:
        fd.write(buf.getvalue())

    c = canvas.Canvas(filename='/Users/ejb66/Desktop/testCCPNpdf2.pdf', pagesize=A4)

    # define a clipping path
    pageWidth = A4[0]
    pageHeight = A4[1]

    p = c.beginPath()
    p.moveTo(0, 0)
    p.lineTo(0, 200)
    p.lineTo(200, 200)
    p.lineTo(200, 0)
    p.close()
    c.clipPath(p, fill=0, stroke=0)

    red50transparent = colors.Color(100, 0, 0, alpha=alphaClip(0.5))
    c.setFillColor(colors.black)
    c.setFont('Helvetica', 10)
    c.drawString(25, 180, 'solid')
    c.setFillColor(colors.blue)
    c.rect(25, 25, 100, 100, fill=True, stroke=False)
    c.setFillColor(colors.red)
    c.rect(100, 75, 100, 100, fill=True, stroke=False)
    c.setFillColor(colors.black)
    c.drawString(225, 180, 'transparent')
    c.setFillColor(colors.blue)
    c.rect(225, 25, 100, 100, fill=True, stroke=False)
    c.setFillColor(red50transparent)
    c.rect(300, 75, 100, 100, fill=True, stroke=False)

    c.rect(0, 0, 100, 100, fill=True, stroke=False)

    # this is much better as it remembers the transparency and object grouping
    from reportlab.lib.units import inch


    h = inch / 3.0
    k = inch / 2.0
    c.setStrokeColorRGB(0.2, 0.3, 0.5)
    c.setFillColorRGB(0.8, 0.6, 0.2)
    c.setLineWidth(4)
    p = c.beginPath()
    for i in (1, 2, 3, 4):
        for j in (1, 2):
            xc, yc = inch * i, inch * j
            p.moveTo(xc, yc)
            p.arcTo(xc - h, yc - k, xc + h, yc + k, startAng=0, extent=60 * i)
            # close only the first one, not the second one
            if j == 1:
                p.close()
    c.drawPath(p, fill=1, stroke=1)

    c.save()
