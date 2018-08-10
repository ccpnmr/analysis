"""
Code for exporting OpenGL stripDisplay to pdf and svg files.
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
    QtWidgets.QMessageBox.critical(None, "OpenGL hellogl",
                                   "PyOpenGL must be installed to run this example.")
    sys.exit(1)
from reportlab.lib import colors
from reportlab.graphics import renderSVG, renderPS
from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Line, Group, Path
from reportlab.graphics.shapes import definePath
from reportlab.graphics.renderSVG import draw, renderScaledDrawing, SVGCanvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from ccpn.util.Report import Report
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import GLFILENAME, GLGRIDLINES, GLGRIDTICKLABELS, GLGRIDTICKMARKS, \
    GLINTEGRALLABELS, GLINTEGRALSYMBOLS, GLMARKLABELS, GLMARKLINES, GLMULTIPLETLABELS, GLREGIONS, \
    GLMULTIPLETSYMBOLS, GLOTHERLINES, GLPEAKLABELS, GLPEAKSYMBOLS, GLPRINTTYPE, GLSELECTEDPIDS, \
    GLSPECTRUMBORDERS, GLSPECTRUMCONTOURS, GLSTRIP, GLSTRIPLABELLING, GLTRACES, GLWIDGET, GLPLOTBORDER


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
        self.parent = parent
        self.strip = strip
        self.project = self.strip.project
        self.filename = filename
        self.params = params
        self._report = Report(self, self.project, filename)
        self._ordering = []

        import matplotlib.font_manager

        foundFonts = matplotlib.font_manager.findSystemFonts()

        # load all fonts that are in the openGL font list
        for glFonts in self.parent.globalGL.fonts.values():
            for ff in foundFonts:
                if glFonts.fontName + '.ttf' in ff:
                    pdfmetrics.registerFont(TTFont(glFonts.fontName, ff))
                    break
            else:
                raise RuntimeError('Font %s not found.' % (glFonts.fontName + '.ttf'))

        # set a default fontName
        self.fontName = self.parent.globalGL.glSmallFont.fontName

        self.backgroundColour = colors.Color(*self.parent.background[0:3],
                                             alpha=self.parent.background[3])
        self.foregroundColour = colors.Color(*self.parent.foreground[0:3],
                                             alpha=self.parent.foreground[3])

        # build all the sections of the pdf
        self._buildAll()
        self._addDrawingToStory()

        # this generates the buffer to write to the file
        self._report.buildDocument()

    def _buildAll(self):
        """Build the main sections of the pdf file from a drawing object
        and add the drawing object to a reportlab document
        """
        dpi = 72  # drawing object and documents are hard-coded to this
        pageWidth = A4[0]
        pageHeight = A4[1]

        # keep aspect ratio of the original screen
        self.margin = 2.0 * cm

        self.main = True
        self.rAxis = self.parent._drawRightAxis
        self.bAxis = self.parent._drawBottomAxis

        if not self.rAxis and not self.bAxis:
            # no axes visible
            self.mainH = self.parent.h
            self.mainW = self.parent.w
            self.mainL = 0
            self.mainB = 0

        elif self.rAxis and not self.bAxis:
            # right axis visible
            self.rAxisW = self.parent.AXIS_MARGINRIGHT
            self.rAxisH = self.parent.h
            self.rAxisL = self.parent.w - self.parent.AXIS_MARGINRIGHT
            self.rAxisB = 0
            self.mainW = self.parent.w - self.parent.AXIS_MARGINRIGHT
            self.mainH = self.parent.h
            self.mainL = 0
            self.mainB = 0

        elif not self.rAxis and self.bAxis:
            # bottom axis visible
            self.bAxisW = self.parent.w
            self.bAxisH = self.parent.AXIS_MARGINBOTTOM
            self.bAxisL = 0
            self.bAxisB = 0
            self.mainW = self.parent.w
            self.mainH = self.parent.h - self.parent.AXIS_MARGINBOTTOM
            self.mainL = 0
            self.mainB = self.parent.AXIS_MARGINBOTTOM

        else:
            # both axes visible
            self.rAxisW = self.parent.AXIS_MARGINRIGHT
            self.rAxisH = self.parent.h - self.parent.AXIS_MARGINBOTTOM
            self.rAxisL = self.parent.w - self.parent.AXIS_MARGINRIGHT
            self.rAxisB = self.parent.AXIS_MARGINBOTTOM
            self.bAxisW = self.parent.w - self.parent.AXIS_MARGINRIGHT
            self.bAxisH = self.parent.AXIS_MARGINBOTTOM
            self.bAxisL = 0
            self.bAxisB = 0
            self.mainW = self.parent.w - self.parent.AXIS_MARGINRIGHT
            self.mainH = self.parent.h - self.parent.AXIS_MARGINBOTTOM
            self.mainL = 0
            self.mainB = self.parent.AXIS_MARGINBOTTOM

        # strip axis ratio
        ratio = self.parent.h / self.parent.w

        # translate to size of drawing Flowable
        self.pixWidth = self._report.doc.width
        self.pixHeight = self.pixWidth * ratio

        # scale fonts to appear the correct size
        self.fontScale = 1.1 * self.pixWidth / self.parent.w
        if self.pixHeight > (self._report.doc.height - 2 * cm):
            # TODO:ED check what else is stealing the height
            self.pixHeight = self._report.doc.height - (2 * cm)
            self.pixWidth = self.pixHeight / ratio
            self.fontScale = 1.025 * self.pixHeight / self.parent.h

        # pixWidth/self.pixHeight are now the dimensions in points for the Flowable
        self.displayScale = self.pixHeight / self.parent.h

        # don't think these are needed
        pixBottom = pageHeight - self.pixHeight - self.margin
        pixLeft = self.margin

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
        if self.params[GLSPECTRUMCONTOURS]: self._addSpectrumContours()
        if self.params[GLSPECTRUMBORDERS]: self._addSpectrumBoundaries()
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
        if self.params[GLOTHERLINES]: self._addInfiniteLines()
        if self.params[GLSTRIPLABELLING]: self._addOverlayText()

        self._addAxisMask()
        self._addGridTickMarks()
        if self.params[GLGRIDTICKLABELS]: self._addGridLabels()

    def _addGridLines(self):
        """
        Add grid lines to the main drawing area.
        """
        if self.strip.gridVisible:
            colourGroups = OrderedDict()
            self._appendIndexLineGroup(indArray=self.parent.gridList[0],
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                                PLOTBOTTOM: self.displayScale * self.mainB,
                                                PLOTWIDTH: self.displayScale * self.mainW,
                                                PLOTHEIGHT: self.displayScale * self.mainH},
                                       name='grid')
            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='grid')

    def _addSpectrumContours(self):
        """
        Add the spectrum contours to the main drawing area.
        """
        colourGroups = OrderedDict()
        for spectrumView in self._ordering:

            if spectrumView.isDeleted:
                continue

            if spectrumView.isVisible():

                if spectrumView.spectrum.dimensionCount > 1:
                    if spectrumView in self.parent._spectrumSettings.keys():
                        # self.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
                        #                                            1, GL.GL_FALSE,
                        #                                            self._spectrumSettings[spectrumView][SPECTRUM_MATRIX])

                        mat = np.transpose(self.parent._spectrumSettings[spectrumView][SPECTRUM_MATRIX].reshape((4, 4)))
                        # mat = np.transpose(self.parent._spectrumSettings[spectrumView][SPECTRUM_MATRIX].reshape((4, 4)))

                        thisSpec = self.parent._contourList[spectrumView]

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

                            colour = colors.Color(*thisSpec.colors[ii0 * 4:ii0 * 4 + 3], alpha=thisSpec.colors[ii0 * 4 + 3])
                            colourPath = 'spectrumViewContours%s%s%s%s%s' % (spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                            newLine = self.parent.lineVisible(newLine,
                                                              x=self.displayScale * self.mainL,
                                                              y=self.displayScale * self.mainB,
                                                              width=self.displayScale * self.mainW,
                                                              height=self.displayScale * self.mainH)
                            if newLine:
                                if colourPath not in colourGroups:
                                    colourGroups[colourPath] = {PDFLINES: [], PDFSTROKEWIDTH: 0.5, PDFSTROKECOLOR: colour, PDFSTROKELINECAP: 1}
                                colourGroups[colourPath][PDFLINES].append(newLine)

                else:

                    # assume that the vertexArray is a GL_LINE_STRIP
                    if spectrumView in self.parent._contourList.keys():
                        if self.parent._stackingMode:
                            mat = np.transpose(self.parent._spectrumSettings[spectrumView][SPECTRUM_STACKEDMATRIX].reshape((4, 4)))
                        else:
                            mat = None

                        thisSpec = self.parent._contourList[spectrumView]

                        # drawVertexColor
                        self._appendVertexLineGroup(indArray=thisSpec,
                                                    colourGroups=colourGroups,
                                                    plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                                             PLOTBOTTOM: self.displayScale * self.mainB,
                                                             PLOTWIDTH: self.displayScale * self.mainW,
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

            if spectrumView.isVisible() and spectrumView.spectrum.dimensionCount > 1:
                self._spectrumValues = spectrumView._getValues()

                # get the bounding box of the spectra
                fx0, fx1 = self._spectrumValues[0].maxAliasedFrequency, self._spectrumValues[0].minAliasedFrequency
                if spectrumView.spectrum.dimensionCount > 1:
                    fy0, fy1 = self._spectrumValues[1].maxAliasedFrequency, self._spectrumValues[1].minAliasedFrequency
                    colour = colors.Color(*spectrumView.posColour[0:3], alpha=0.5)
                else:
                    fy0, fy1 = max(spectrumView.spectrum.intensities), min(spectrumView.spectrum.intensities)

                    colour = spectrumView.sliceColour
                    colR = int(colour.strip('# ')[0:2], 16) / 255.0
                    colG = int(colour.strip('# ')[2:4], 16) / 255.0
                    colB = int(colour.strip('# ')[4:6], 16) / 255.0

                    colour = colors.Color(colR, colG, colB, alpha=0.5)

                colourPath = 'spectrumViewBoundaries%s%s%s%s%s' % (
                    spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                # generate the bounding box
                newLine = [fx0, fy0, fx0, fy1, fx1, fy1, fx1, fy0, fx0, fy0]
                newLine = self.parent.lineVisible(newLine,
                                                  x=self.displayScale * self.mainL,
                                                  y=self.displayScale * self.mainB,
                                                  width=self.displayScale * self.mainW,
                                                  height=self.displayScale * self.mainH)
                if newLine:
                    if colourPath not in colourGroups:
                        colourGroups[colourPath] = {PDFLINES: [], PDFSTROKEWIDTH: 0.5, PDFSTROKECOLOR: colour,
                                                    PDFSTROKELINECAP: 1, PDFCLOSEPATH: False}
                    colourGroups[colourPath][PDFLINES].append(newLine)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='boundaries')

    def _addPeakSymbols(self):
        """
        Add the peak symbols to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroupFill(indArray=self.parent._GLPeaks._GLSymbols,
                                       listView='peakListViews',
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                                PLOTBOTTOM: self.displayScale * self.mainB,
                                                PLOTWIDTH: self.displayScale * self.mainW,
                                                PLOTHEIGHT: self.displayScale * self.mainH},
                                       name='peakSymbols',
                                       fillMode=None)
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='peakSymbols')

    def _addMultipletSymbols(self):
        """
        Add the multiplet symbols to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroupFill(indArray=self.parent._GLMultiplets._GLSymbols,
                                       listView='multipletListViews',
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                                PLOTBOTTOM: self.displayScale * self.mainB,
                                                PLOTWIDTH: self.displayScale * self.mainW,
                                                PLOTHEIGHT: self.displayScale * self.mainH},
                                       name='multipletSymbols',
                                       fillMode=None)
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='multipletSymbols')

    def _addMarkLines(self):
        """
        Add the mark lines to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroup(indArray=self.parent._marksList,
                                   colourGroups=colourGroups,
                                   plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                            PLOTBOTTOM: self.displayScale * self.mainB,
                                            PLOTWIDTH: self.displayScale * self.mainW,
                                            PLOTHEIGHT: self.displayScale * self.mainH},
                                   name='marks')
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='marks')

    def _addIntegralLines(self):
        """
        Add the integral lines to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroupFill(indArray=self.parent._GLIntegrals._GLSymbols,
                                       listView='integralListViews',
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                                PLOTBOTTOM: self.displayScale * self.mainB,
                                                PLOTWIDTH: self.displayScale * self.mainW,
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
                                      and pp in self.parent._GLIntegrals._GLSymbols.keys()
                                      and pp.integralList.pid in self.params[GLSELECTEDPIDS]]

            for integralListView in validIntegralListViews:  # spectrumView.integralListViews:
                mat = None
                if spectrumView.spectrum.dimensionCount > 1:
                    if spectrumView in self.parent._spectrumSettings.keys():
                        # draw
                        pass

                else:

                    # assume that the vertexArray is a GL_LINE_STRIP
                    if spectrumView in self.parent._contourList.keys():
                        if self.parent._stackingMode:
                            mat = np.transpose(self.parent._spectrumSettings[spectrumView][SPECTRUM_STACKEDMATRIX].reshape((4, 4)))
                        else:
                            mat = None

                # draw the integralAreas if they exist
                for integralArea in self.parent._GLIntegrals._GLSymbols[integralListView]._regions:
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

                            colour = colors.Color(*thisSpec.colors[vv * 2:vv * 2 + 3], alpha=float(thisSpec.colors[vv * 2 + 3]))
                            colourPath = 'spectrumViewIntegralFill%s%s%s%s%s' % (
                                spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                            newLine = self.parent.lineVisible(newLine,
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
        self._appendIndexLineGroup(indArray=self.parent._externalRegions,
                                   colourGroups=colourGroups,
                                   plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                            PLOTBOTTOM: self.displayScale * self.mainB,
                                            PLOTWIDTH: self.displayScale * self.mainW,
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
                                  and pp in self.parent._GLPeaks._GLLabels.keys()
                                  and pp.peakList.pid in self.params[GLSELECTEDPIDS]]

            for peakListView in validPeakListViews:  # spectrumView.peakListViews:
                for drawString in self.parent._GLPeaks._GLLabels[peakListView].stringList:

                    col = drawString.colors[0]
                    if not isinstance(col, Iterable):
                        col = drawString.colors[0:4]
                    colour = colors.Color(*col[0:3], alpha=float(col[3]))
                    colourPath = 'spectrumViewPeakLabels%s%s%s%s%s' % (
                        spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                    newLine = [drawString.attribs[0], drawString.attribs[1]]
                    if self.parent.pointVisible(newLine,
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
                                      and pp in self.parent._GLIntegrals._GLLabels.keys()
                                      and pp.integralList.pid in self.params[GLSELECTEDPIDS]]

            for integralListView in validIntegralListViews:  # spectrumView.integralListViews:
                for drawString in self.parent._GLIntegrals._GLLabels[integralListView].stringList:

                    col = drawString.colors[0]
                    if not isinstance(col, Iterable):
                        col = drawString.colors[0:4]
                    colour = colors.Color(*col[0:3], alpha=float(col[3]))
                    colourPath = 'spectrumViewIntegralLabels%s%s%s%s%s' % (
                        spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                    newLine = [drawString.attribs[0], drawString.attribs[1]]
                    if self.parent.pointVisible(newLine,
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
                                       and pp in self.parent._GLMultiplets._GLLabels.keys()
                                       and pp.multipletList.pid in self.params[GLSELECTEDPIDS]]

            for multipletListView in validMultipletListViews:  # spectrumView.multipletListViews:
                for drawString in self.parent._GLMultiplets._GLLabels[multipletListView].stringList:

                    col = drawString.colors[0]
                    if not isinstance(col, Iterable):
                        col = drawString.colors[0:4]
                    colour = colors.Color(*col[0:3], alpha=float(col[3]))
                    colourPath = 'spectrumViewMultipletLabels%s%s%s%s%s' % (
                        spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                    newLine = [drawString.attribs[0], drawString.attribs[1]]
                    if self.parent.pointVisible(newLine,
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
        for drawString in self.parent._marksAxisCodes:
            # drawString.drawTextArray()

            col = drawString.colors[0]
            if not isinstance(col, Iterable):
                col = drawString.colors[0:4]
            colour = colors.Color(*col[0:3], alpha=float(col[3]))
            colourPath = 'projectMarks%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

            newLine = [drawString.attribs[0], drawString.attribs[1]]
            if self.parent.pointVisible(newLine,
                                        x=self.displayScale * self.mainL,
                                        y=self.displayScale * self.mainB,
                                        width=self.displayScale * self.mainW,
                                        height=self.displayScale * self.mainH):
                if colourPath not in colourGroups:
                    colourGroups[colourPath] = Group()
                colourGroups[colourPath].add(String(newLine[0], newLine[1],
                                                    drawString.text,
                                                    fontSize=drawString.font.fontSize * self.fontScale,
                                                    fontName=drawString.font.fontName,
                                                    fillColor=colour))

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addTraces(self):
        """
        Add the traces to the main drawing area.
        """
        colourGroups = OrderedDict()
        for hTrace in self.parent._staticHTraces:
            if hTrace.spectrumView and not hTrace.spectrumView.isDeleted and hTrace.spectrumView.isVisible():
                # drawVertexColor
                self._appendVertexLineGroup(indArray=hTrace,
                                            colourGroups=colourGroups,
                                            plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                                     PLOTBOTTOM: self.displayScale * self.mainB,
                                                     PLOTWIDTH: self.displayScale * self.mainW,
                                                     PLOTHEIGHT: self.displayScale * self.mainH},
                                            name='hTrace%s' % hTrace.spectrumView.pid,
                                            includeLastVertex=not self.parent.is1D)

        for vTrace in self.parent._staticVTraces:
            if vTrace.spectrumView and not vTrace.spectrumView.isDeleted and vTrace.spectrumView.isVisible():
                # drawVertexColor
                self._appendVertexLineGroup(indArray=vTrace,
                                            colourGroups=colourGroups,
                                            plotDim={PLOTLEFT: self.displayScale * self.mainL,
                                                     PLOTBOTTOM: self.displayScale * self.mainB,
                                                     PLOTWIDTH: self.displayScale * self.mainW,
                                                     PLOTHEIGHT: self.displayScale * self.mainH},
                                            name='vTrace%s' % vTrace.spectrumView.pid,
                                            includeLastVertex=not self.parent.is1D)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='traces')

    def _addInfiniteLines(self):
        """
        Add the infinite lines to the main drawing area.
        """
        colourGroups = OrderedDict()
        for infLine in self.parent._infiniteLines:
            if infLine.visible:
                colour = colors.Color(*infLine.brush[0:3], alpha=float(infLine.brush[3]))
                colourPath = 'infiniteLines%s%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha, infLine.lineStyle)

                if infLine.orientation == 'h':
                    newLine = [self.parent.axisL, infLine.values[0], self.parent.axisR, infLine.values[0]]
                else:
                    newLine = [infLine.values[0], self.parent.axisT, infLine.values[0], self.parent.axisB]

                newLine = self.parent.lineVisible(newLine,
                                                  x=self.displayScale * self.mainL,
                                                  y=self.displayScale * self.mainB,
                                                  width=self.displayScale * self.mainW,
                                                  height=self.displayScale * self.mainH)
                if newLine:
                    if colourPath not in colourGroups:
                        colourGroups[colourPath] = {PDFLINES: [], PDFSTROKEWIDTH: 0.5, PDFSTROKECOLOR: colour,
                                                    PDFSTROKELINECAP: 1, PDFCLOSEPATH: False,
                                                    PDFSTROKEDASHARRAY: GLLINE_STYLES_ARRAY[infLine.lineStyle]}
                    colourGroups[colourPath][PDFLINES].append(newLine)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='infiniteLines')

    def _addOverlayText(self):
        """
        Add the overlay text to the main drawing area.
        """
        colourGroups = OrderedDict()
        drawString = self.parent.stripIDString

        colour = self.foregroundColour
        colourPath = 'overlayText%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

        newLine = [drawString.attribs[0], drawString.attribs[1]]
        if self.parent.pointVisible(newLine,
                                    x=self.displayScale * self.mainL,
                                    y=self.displayScale * self.mainB,
                                    width=self.displayScale * self.mainW,
                                    height=self.displayScale * self.mainH):
            if colourPath not in colourGroups:
                colourGroups[colourPath] = Group()
            colourGroups[colourPath].add(String(newLine[0], newLine[1],
                                                drawString.text,
                                                fontSize=drawString.font.fontSize * self.fontScale,
                                                fontName=drawString.font.fontName,
                                                fillColor=colour))

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
                if self.params[GLGRIDTICKMARKS]:
                    self._appendIndexLineGroup(indArray=self.parent.gridList[1],
                                           colourGroups=colourGroups,
                                           plotDim={PLOTLEFT: self.displayScale * (self.mainW - self.parent.AXIS_LINE),
                                                    PLOTBOTTOM: self.displayScale * self.mainB,
                                                    PLOTWIDTH: self.displayScale * self.parent.AXIS_LINE,
                                                    PLOTHEIGHT: self.displayScale * self.mainH},
                                           name='gridAxes',
                                           setColour=self.foregroundColour)
                    if self.params[GLPLOTBORDER]:
                        list(colourGroups.values())[0][PDFLINES].append([self.displayScale * self.mainW, self.displayScale * self.mainB,
                                                                     self.displayScale * self.mainW, self.pixHeight])
                elif self.params[GLPLOTBORDER]:
                    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray

                    tempVertexArray = GLVertexArray(numLists=1, drawMode=GL.GL_LINE, dimension=2)
                    tempVertexArray.indices = [0, 1]
                    tempVertexArray.vertices = [0.0, 0.0, 0.0, 0.0]

                    self._appendIndexLineGroup(indArray=tempVertexArray,
                                           colourGroups=colourGroups,
                                           plotDim={PLOTLEFT: self.displayScale * (self.mainW - self.parent.AXIS_LINE),
                                                    PLOTBOTTOM: self.displayScale * self.mainB,
                                                    PLOTWIDTH: self.displayScale * self.parent.AXIS_LINE,
                                                    PLOTHEIGHT: self.displayScale * self.mainH},
                                           name='gridAxes',
                                           setColour=self.foregroundColour)
                    list(colourGroups.values())[0][PDFLINES] = [[self.displayScale * self.mainW, self.displayScale * self.mainB,
                                                                     self.displayScale * self.mainW, self.pixHeight]]

            if self.bAxis:
                if self.params[GLGRIDTICKMARKS]:
                    self._appendIndexLineGroup(indArray=self.parent.gridList[2],
                                           colourGroups=colourGroups,
                                           plotDim={PLOTLEFT: 0.0,
                                                    PLOTBOTTOM: self.displayScale * self.mainB,
                                                    PLOTWIDTH: self.displayScale * self.mainW,
                                                    PLOTHEIGHT: self.displayScale * self.parent.AXIS_LINE},
                                           name='gridAxes',
                                           setColour=self.foregroundColour)
                    if self.params[GLPLOTBORDER]:
                        list(colourGroups.values())[0][PDFLINES].append([0.0, self.displayScale * self.bAxisH,
                                                                     self.displayScale * self.mainW, self.displayScale * self.bAxisH])
                elif self.params[GLPLOTBORDER]:
                    from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray

                    tempVertexArray = GLVertexArray(numLists=1, drawMode=GL.GL_LINE, dimension=2)
                    tempVertexArray.indices = [0, 1]
                    tempVertexArray.vertices = [0.0, 0.0, 0.0, 0.0]

                    self._appendIndexLineGroup(indArray=tempVertexArray,
                                           colourGroups=colourGroups,
                                           plotDim={PLOTLEFT: self.displayScale * (self.mainW - self.parent.AXIS_LINE),
                                                    PLOTBOTTOM: self.displayScale * self.mainB,
                                                    PLOTWIDTH: self.displayScale * self.parent.AXIS_LINE,
                                                    PLOTHEIGHT: self.displayScale * self.mainH},
                                           name='gridAxes',
                                           setColour=self.foregroundColour)
                    # append because the first line is set above
                    list(colourGroups.values())[0][PDFLINES].append([0.0, self.displayScale * self.bAxisH,
                                                                     self.displayScale * self.mainW, self.displayScale * self.bAxisH])

            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='gridAxes')

    def _addGridLabels(self):
        """
        Add marks to the right/bottom axis areas.
        """
        if self.rAxis or self.bAxis:
            colourGroups = OrderedDict()
            if self.rAxis:
                for drawString in self.parent._axisYLabelling:

                    # drawTextArray
                    colour = self.foregroundColour
                    colourPath = 'axisLabels%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

                    # add (0, 3) to mid-point
                    mid = self.parent.axisL + (0 + drawString.attribs[0]) * (self.parent.axisR - self.parent.axisL) / self.parent.AXIS_MARGINRIGHT
                    newLine = [mid, drawString.attribs[1] + (3 * self.parent.pixelY)]
                    if self.parent.pointVisible(newLine,
                                                x=self.displayScale * self.rAxisL,
                                                y=self.displayScale * self.rAxisB,
                                                width=self.displayScale * self.rAxisW,
                                                height=self.displayScale * self.rAxisH):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()
                        colourGroups[colourPath].add(String(newLine[0], newLine[1],
                                                            drawString.text,
                                                            fontSize=drawString.font.fontSize * self.fontScale,
                                                            fontName=drawString.font.fontName,
                                                            fillColor=colour))

            if self.bAxis:
                for drawString in self.parent._axisXLabelling:

                    # drawTextArray
                    colour = self.foregroundColour
                    colourPath = 'axisLabels%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

                    # add (0, 3) to mid
                    mid = self.parent.axisB + (3 + drawString.attribs[1]) * (self.parent.axisT - self.parent.axisB) / self.parent.AXIS_MARGINBOTTOM
                    newLine = [drawString.attribs[0] + (0 * self.parent.pixelX), mid]
                    if self.parent.pointVisible(newLine,
                                                x=self.displayScale * self.bAxisL,
                                                y=self.displayScale * self.bAxisB,
                                                width=self.displayScale * self.bAxisW,
                                                height=self.displayScale * self.bAxisH):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()
                        colourGroups[colourPath].add(String(newLine[0], newLine[1],
                                                            drawString.text,
                                                            fontSize=drawString.font.fontSize * self.fontScale,
                                                            fontName=drawString.font.fontName,
                                                            fillColor=colour))

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
                                mainDim={PLOTLEFT: 0,  #scale*self.mainL,
                                         PLOTBOTTOM: 0,  #scale*self.mainB,
                                         PLOTWIDTH: self.pixWidth,  #scale*self.mainW,
                                         PLOTHEIGHT: self.pixHeight  #scale*self.mainH
                                         }
                                )

    def _addDrawingToStory(self):
        """
        Add the current drawing the story of a document
        """
        self._report.story.append(self.report())

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

    def _appendVertexLineGroup(self, indArray, colourGroups, plotDim, name, mat=None, includeLastVertex=False):
        for vv in range(0, len(indArray.vertices) - 2, 2):

            if mat is not None:

                vectStart = [indArray.vertices[vv], indArray.vertices[vv + 1], 0.0, 1.0]
                vectStart = mat.dot(vectStart)
                vectEnd = [indArray.vertices[vv + 2], indArray.vertices[vv + 3], 0.0, 1.0]
                vectEnd = mat.dot(vectEnd)
                newLine = [vectStart[0], vectStart[1], vectEnd[0], vectEnd[1]]
            else:
                newLine = list(indArray.vertices[vv:vv + 4])

            colour = colors.Color(*indArray.colors[vv * 2:vv * 2 + 3], alpha=float(indArray.colors[vv * 2 + 3]))
            colourPath = '%s%s%s%s%s' % (name, colour.red, colour.green, colour.blue, colour.alpha)
            if colourPath not in colourGroups:
                cc = colourGroups[colourPath] = {}
                if (indArray.fillMode or GL.GL_LINE) == GL.GL_LINE:
                    cc[PDFLINES] = []
                    cc[PDFSTROKEWIDTH] = 0.5
                    cc[PDFSTROKECOLOR] = colour
                    cc[PDFSTROKELINECAP] = 1
                else:
                    # assume that it is GL.GL_FILL
                    cc[PDFLINES] = []
                    cc[PDFFILLCOLOR] = colour
                    cc[PDFSTROKE] = None
                    cc[PDFSTROKECOLOR] = None

            newLine = self.parent.lineVisible(newLine,
                                              x=plotDim[PLOTLEFT],
                                              y=plotDim[PLOTBOTTOM],
                                              width=plotDim[PLOTWIDTH],
                                              height=plotDim[PLOTHEIGHT])
            if newLine:
                colourGroups[colourPath][PDFLINES].append(newLine)

    def _appendIndexLineGroup(self, indArray, colourGroups, plotDim, name,
                              fillMode=None, splitGroups=False,
                              setColour=None):
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
                newLine.extend([indArray.vertices[vv * 2], indArray.vertices[vv * 2 + 1]])

            colour = (setColour or colors.Color(*indArray.colors[ii0[0] * 4:ii0[0] * 4 + 3], alpha=indArray.colors[ii0[0] * 4 + 3]))
            colourPath = 'spectrumView%s%s%s%s%s' % (name,
                                                     colour.red, colour.green, colour.blue, colour.alpha)

            # # override so that each element is a new group
            # if splitGroups:
            #     colourGroups = OrderedDict()

            if colourPath not in colourGroups:
                cc = colourGroups[colourPath] = {}
                if (fillMode or indArray.fillMode or GL.GL_LINE) == GL.GL_LINE:
                    cc[PDFLINES] = []
                    cc[PDFSTROKEWIDTH] = 0.5
                    cc[PDFSTROKECOLOR] = colour
                    cc[PDFSTROKELINECAP] = 1
                else:
                    # assume that it is GL.GL_FILL
                    cc[PDFLINES] = []
                    cc[PDFFILLCOLOR] = colour
                    cc[PDFSTROKE] = None
                    cc[PDFSTROKECOLOR] = None

            newLine = self.parent.lineVisible(newLine,
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
                                  fillMode=None, splitGroups=False):
        for spectrumView in self._ordering:
            if spectrumView.isDeleted:
                continue

            attribList = getattr(spectrumView, listView)
            validListViews = [pp for pp in attribList
                              if pp.isVisible()
                              and spectrumView.isVisible()]

            for thisListView in validListViews:
                if thisListView in indArray.keys():
                    thisSpec = indArray[thisListView]
                    self._appendIndexLineGroup(indArray=thisSpec,
                                               colourGroups=colourGroups,
                                               plotDim=plotDim,
                                               name='spectrumView%s%s' % (name, spectrumView.pid),
                                               fillMode=fillMode,
                                               splitGroups=splitGroups)

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

    red50transparent = colors.Color(100, 0, 0, alpha=0.5)
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
