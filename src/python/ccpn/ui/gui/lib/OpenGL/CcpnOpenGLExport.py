"""
Code for exporting OpenGL stripDisplay to pdf and svg files.
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
__dateModified__ = "$dateModified: 2021-10-04 19:35:52 +0100 (Mon, October 04, 2021) $"
__version__ = "$Revision: 3.0.4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

# import sys
import os
import io
import numpy as np
from PyQt5 import QtGui
from PyQt5.QtCore import QStandardPaths
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QApplication
from dataclasses import dataclass
from collections import OrderedDict
from collections.abc import Iterable
from reportlab.platypus import SimpleDocTemplate, Paragraph, Flowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.lib import colors
from reportlab.graphics import renderSVG, renderPS, renderPM
from reportlab.graphics.shapes import Drawing, Rect, String, PolyLine, Group, Path
# from reportlab.graphics.shapes import definePath
# from reportlab.graphics.renderSVG import draw, renderScaledDrawing, SVGCanvas
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, portrait, landscape
from reportlab.platypus.tables import Table
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLViewports import viewportDimensions
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import SPECTRUM_STACKEDMATRIX, SPECTRUM_MATRIX, \
    GLLINE_STYLES_ARRAY, SPECTRUM_XLIMITS, SPECTRUM_AF, SPECTRUM_ALIASINGINDEX, SPECTRUM_FOLDINGMODE, \
    SPECTRUM_YLIMITS, SPECTRUM_SCALE

from ccpn.ui.gui.lib.OpenGL import GL
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import GLGRIDLINES, GLAXISLABELS, GLAXISMARKS, \
    GLINTEGRALLABELS, GLINTEGRALSYMBOLS, GLMARKLABELS, GLMARKLINES, GLMULTIPLETLABELS, GLREGIONS, \
    GLMULTIPLETSYMBOLS, GLOTHERLINES, GLPEAKLABELS, GLPEAKSYMBOLS, GLPRINTTYPE, GLSELECTEDPIDS, \
    GLSPECTRUMBORDERS, GLSPECTRUMCONTOURS, GLSPECTRUMLABELS, \
    GLSTRIP, GLSTRIPLABELLING, GLTRACES, GLACTIVETRACES, GLPLOTBORDER, \
    GLPAGETYPE, GLSPECTRUMDISPLAY, GLBACKGROUND, GLBASETHICKNESS, GLSYMBOLTHICKNESS, \
    GLCONTOURTHICKNESS, GLFOREGROUND, GLSHOWSPECTRAONPHASE, \
    GLAXISTITLES, GLAXISUNITS, GLSTRIPDIRECTION, GLSTRIPPADDING, GLEXPORTDPI, \
    GLCURSORS, GLDIAGONALLINE, GLDIAGONALSIDEBANDS, \
    MAINVIEW, MAINVIEWFULLHEIGHT, MAINVIEWFULLWIDTH, \
    RIGHTAXIS, RIGHTAXISBAR, FULLRIGHTAXIS, FULLRIGHTAXISBAR, \
    BOTTOMAXIS, BOTTOMAXISBAR, FULLBOTTOMAXIS, FULLBOTTOMAXISBAR, FULLVIEW, BLANKVIEW, \
    GLALIASSHADE, GLSTRIPREGIONS, \
    GLSCALINGMODE, GLSCALINGOPTIONS, GLSCALINGPERCENT, GLSCALINGBYUNITS, \
    GLPRINTFONT, GLUSEPRINTFONT
# from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLDefs import GLFILENAME, GLWIDGET, GLAXISLINES, GLAXISMARKSINSIDE, \
#     GLFULLLIST, GLEXTENDEDLIST, GLALIASENABLED, GLALIASLABELSENABLED
from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import getAliasSetting
from ccpn.ui.gui.popups.ExportStripToFile import PAGEPORTRAIT
# from ccpn.ui.gui.popups.ExportStripToFile import EXPORTPDF, EXPORTSVG, EXPORTTYPES, \
#     PAGELANDSCAPE, PAGETYPES
from ccpn.ui.gui.popups.ExportStripToFile import EXPORTPNG
# from ccpn.util.Colour import colorSchemeTable
from ccpn.util.Report import Report


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
FRAMEPADDING = 12


def alphaClip(value):
    # return np.clip(float(value), 0.0, 1.0)
    return float(value)


class GLExporter():
    """
    Class container for exporting OpenGL stripDisplay to a file or object
    """

    def __init__(self, parent, strip, filename, params):
        """
        Initialise the exporter
        :param filename - not required
        :param params - parameter dict from the exporter dialog

        Need to have different settingsif the output is to a .png file
        This needs a multiplier based on (output dpi / 72) and scale = (output dpi / 72)
         - a thickness modifier on all drawing output
        Fonts need a 0.5 scaling for .png
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

        self._printType = self.params[GLPRINTTYPE]

        if self._printType == EXPORTPNG:
            # need to set the scaling for a PNG file and alter baseThickness/font size
            self._dpiScale = self.params[GLEXPORTDPI] / 72

            self.baseThickness = self.params[GLBASETHICKNESS] * self._dpiScale
            self.symbolThickness = self.params[GLSYMBOLTHICKNESS]
            self.contourThickness = self.params[GLCONTOURTHICKNESS]

            self._pngScale = 0.5
        else:
            self.baseThickness = self.params[GLBASETHICKNESS]
            self.symbolThickness = self.params[GLSYMBOLTHICKNESS]
            self.contourThickness = self.params[GLCONTOURTHICKNESS]

            self._pngScale = 1.0
            self._dpiScale = 1.0

        # set default colours
        # self.backgroundColour = colors.Color(*self._parent.background[0:3],
        #                                      alpha=alphaClip(self._parent.background[3]))
        self.backgroundColour = colors.Color(*self.params[GLBACKGROUND], alpha=alphaClip(1.0))
        # self.foregroundColour = colors.Color(*self._parent.foreground[0:3],
        #                                      alpha=alphaClip(self._parent.foreground[3]))
        self.foregroundColour = colors.Color(*self.params[GLFOREGROUND], alpha=alphaClip(1.0))

        # build all the sections of the pdf
        self.stripReports = []
        self.stripWidths = []
        self.stripHeights = []
        self.stripSpacing = 0

        if self.params[GLSPECTRUMDISPLAY]:
            spectrumDisplay = self.params[GLSPECTRUMDISPLAY]

            self.numStrips = len(spectrumDisplay.strips)
            for strNum, strip in enumerate(spectrumDisplay.orderedStrips):
                self.stripNumber = strNum
                self._createStrip(strip, singleStrip=False, axesOnly=False)

            # build strip for the floating axis
            self.stripNumber = self.numStrips

            # self._parent still points to the last strip - check not to double up the last axis
            if self.params[GLSTRIPDIRECTION] == 'Y':
                if self._parent and not self._parent._drawRightAxis:
                    self._createStrip(spectrumDisplay.orderedStrips[0], spectrumDisplay._rightGLAxis, singleStrip=False, axesOnly=True)
            else:
                if self._parent and not self._parent._drawBottomAxis:
                    self._createStrip(spectrumDisplay.orderedStrips[0], spectrumDisplay._bottomGLAxis, singleStrip=False, axesOnly=True)

        else:
            self.numStrips = 1
            self.stripNumber = 0
            self._createStrip(self.params[GLSTRIP], singleStrip=True, axesOnly=False)

        self._addTableToStory()

        # this generates the buffer to write to the file
        self._report.buildDocument()

    def _createStrip(self, strip, _parent=None, singleStrip=False, axesOnly=False):
        # point to the correct strip
        self.strip = strip
        self._parent = self.strip._CcpnGLWidget if _parent is None else _parent

        self._buildPage(singleStrip=singleStrip)
        self._buildStrip(axesOnly=axesOnly)
        self._addDrawingToStory()

    def _getFontPaths(self):
        font_paths = QStandardPaths.standardLocations(QStandardPaths.FontsLocation)

        accounted = []
        unloadable = []
        family_to_path = {}

        db = QFontDatabase()
        for fpath in font_paths:  # go through all font paths
            for filename in os.listdir(fpath):  # go through all files at each path
                path = os.path.join(fpath, filename)

                idx = db.addApplicationFont(path)  # add font path

                if idx < 0:
                    unloadable.append(path)  # font wasn't loaded if idx is -1
                else:
                    names = db.applicationFontFamilies(idx)  # load back font family name
                    # for n in names:
                    #     family_to_path[n] = set(names)

                    for n in names:
                        _paths = family_to_path.setdefault(n, set())
                        _paths.add(path)
                        # if n in family_to_path:
                        #     accounted.append((n, path))
                        # else:
                        #     family_to_path[n] = path

                    # this isn't a 1:1 mapping, for example
                    # 'C:/Windows/Fonts/HTOWERT.TTF' (regular) and
                    # 'C:/Windows/Fonts/HTOWERTI.TTF' (italic) are different
                    # but applicationFontFamilies will return 'High Tower Text' for both
        return unloadable, family_to_path, accounted

    def _importFonts(self):
        from ccpn.framework.PathsAndUrls import fontsPath
        from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLGlobal import GLFONT_SUBSTITUTE

        # load all system fonts to find matches with OpenGl fonts
        for glFonts in self._parent.globalGL.fonts.values():
            pdfmetrics.registerFont(TTFont(glFonts.fontName, fontsPath / 'open-sans' / GLFONT_SUBSTITUTE + '.ttf'))

        self._printFont = None
        if self.params[GLUSEPRINTFONT]:
            _fontName, _fontSize = self.params[GLPRINTFONT]
            # self._printFont = QtGui.QFont()
            # self._printFont.fromString(self.params[GLPRINTFONT])

            unloadable, family_to_path, accounted = self._getFontPaths()
            _paths = family_to_path.get(_fontName, [])
            for _path in _paths:
                try:
                    pdfmetrics.registerFont(TTFont(_fontName, _path))
                except Exception as es:
                    print(f' Font could not be loaded for printing: {_fontName} - {_path}')
                    self.params[GLUSEPRINTFONT] = False
            if not _paths:
                print(f' Font could not be loaded for printing: {_fontName}')
                self.params[GLUSEPRINTFONT] = False

        # set a default fontName
        self.fontName = self._parent.getSmallFont().fontName

        # load a .pfb/.afm font for the png exporter
        afmdir = fontsPath / 'open-sans'
        pfbdir = fontsPath / 'open-sans'
        afmFile = afmdir / 'OpenSans-Regular.afm'
        pfbFile = pfbdir / 'OpenSans-Regular.pfb'

        justFace = pdfmetrics.EmbeddedType1Face(afmFile, pfbFile)
        faceName = 'OpenSans'  # pulled from AFM file
        pdfmetrics.registerTypeFace(justFace)

        # this needs to have a space
        justFont = pdfmetrics.Font('Open Sans', faceName, 'WinAnsiEncoding')
        pdfmetrics.registerFont(justFont)

    def _buildPage(self, singleStrip=True):
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

        if singleStrip:
            frame = self.strip
        else:
            frame = self.strip.spectrumDisplay.stripFrame

        # get the method for retrieving the viewport sizes
        getView = self._parent.viewports.getViewportFromWH

        if self.params[GLSTRIPDIRECTION] == 'Y':
            docHeight = self._report.doc.height - (2 * FRAMEPADDING)
            docWidth = self._report.doc.width - (2 * FRAMEPADDING)
            fh = frame.height()
            fw = frame.width()
            _parentH = self._parent.h
            _parentW = self._parent.w
            fw += (self.numStrips - 1) * self.params[GLSTRIPPADDING]

        else:
            docHeight = self._report.doc.height - (2 * FRAMEPADDING)
            docWidth = self._report.doc.width - (2 * FRAMEPADDING)
            fh = frame.height()
            fw = frame.width()
            _parentH = self._parent.h
            _parentW = self._parent.w
            fh += (self.numStrips - 1) * self.params[GLSTRIPPADDING]

        if not self.rAxis and not self.bAxis:
            # no axes visible
            self.mainView = viewportDimensions(*getView(FULLVIEW, _parentW, _parentH))
            self.rAxisMarkView = viewportDimensions(*getView(BLANKVIEW, _parentW, _parentH))
            self.rAxisBarView = viewportDimensions(*getView(BLANKVIEW, _parentW, _parentH))
            self.bAxisMarkView = viewportDimensions(*getView(BLANKVIEW, _parentW, _parentH))
            self.bAxisBarView = viewportDimensions(*getView(BLANKVIEW, _parentW, _parentH))

        elif self.rAxis and not self.bAxis:
            # right axis visible
            self.mainView = viewportDimensions(*getView(MAINVIEWFULLHEIGHT, _parentW, _parentH))
            if self._parent._fullHeightRightAxis:
                self.rAxisMarkView = viewportDimensions(*getView(FULLRIGHTAXIS, _parentW, _parentH))
                self.rAxisBarView = viewportDimensions(*getView(FULLRIGHTAXISBAR, _parentW, _parentH))
            else:
                self.rAxisMarkView = viewportDimensions(*getView(RIGHTAXIS, _parentW, _parentH))
                self.rAxisBarView = viewportDimensions(*getView(RIGHTAXISBAR, _parentW, _parentH))
            self.bAxisMarkView = viewportDimensions(*getView(BLANKVIEW, _parentW, _parentH))
            self.bAxisBarView = viewportDimensions(*getView(BLANKVIEW, _parentW, _parentH))

        elif not self.rAxis and self.bAxis:
            # bottom axis visible
            self.mainView = viewportDimensions(*getView(MAINVIEWFULLWIDTH, _parentW, _parentH))
            self.rAxisMarkView = viewportDimensions(*getView(BLANKVIEW, _parentW, _parentH))
            self.rAxisBarView = viewportDimensions(*getView(BLANKVIEW, _parentW, _parentH))
            if self._parent._fullWidthBottomAxis:
                self.bAxisMarkView = viewportDimensions(*getView(FULLBOTTOMAXIS, _parentW, _parentH))
                self.bAxisBarView = viewportDimensions(*getView(FULLBOTTOMAXISBAR, _parentW, _parentH))
            else:
                self.bAxisMarkView = viewportDimensions(*getView(BOTTOMAXIS, _parentW, _parentH))
                self.bAxisBarView = viewportDimensions(*getView(BOTTOMAXISBAR, _parentW, _parentH))

        else:
            # both axes visible
            self.mainView = viewportDimensions(*getView(MAINVIEW, _parentW, _parentH))
            self.rAxisMarkView = viewportDimensions(*getView(RIGHTAXIS, _parentW, _parentH))
            self.rAxisBarView = viewportDimensions(*getView(RIGHTAXISBAR, _parentW, _parentH))
            self.bAxisMarkView = viewportDimensions(*getView(BOTTOMAXIS, _parentW, _parentH))
            self.bAxisBarView = viewportDimensions(*getView(BOTTOMAXISBAR, _parentW, _parentH))

        # stripFrame ratio
        frameRatio = fh / fw

        # self.pixHeight = docHeight
        # self.pixWidth = self.pixHeight / frameRatio
        # # self.fontScale = 1.025 * self.pixHeight / _parentH
        # self.fontScale = self.pixHeight / _parentH

        # translate to size of drawing Flowable
        if self.params[GLSTRIPDIRECTION] == 'Y':
            # strip axis ratio
            ratio = _parentH / _parentW

            self.pixWidth = docWidth / (fw / _parentW)
            self.pixHeight = self.pixWidth * ratio

            # scale fonts to appear the correct size
            self.fontScale = self._pngScale * self.pixWidth / _parentW

            # if too tall then reduce scaling
            if self.pixHeight > docHeight:
                modRatio = docHeight / self.pixHeight

                self.pixWidth *= modRatio
                self.pixHeight *= modRatio
                self.fontScale *= modRatio

        else:
            # strip axis ratio
            ratio = _parentH / _parentW

            self.pixHeight = docHeight / (fh / _parentH)
            self.pixWidth = self.pixHeight / ratio

            # scale fonts to appear the correct size
            self.fontScale = self._pngScale * self.pixWidth / _parentW

            # if too wide then reduce scaling
            if self.pixWidth > docWidth:
                modRatio = docWidth / self.pixWidth

                self.pixWidth *= modRatio
                self.pixHeight *= modRatio
                self.fontScale *= modRatio

        # modify by the print dialog scaling factor
        if self.params[GLSCALINGMODE] == 0 and (0 <= self.params[GLSCALINGPERCENT] <= 100):
            self.pixWidth *= (self.params[GLSCALINGPERCENT] / 100.0)
            self.pixHeight *= (self.params[GLSCALINGPERCENT] / 100.0)
            self.fontScale *= (self.params[GLSCALINGPERCENT] / 100.0)

        self.fontXOffset = 0.75
        self.fontYOffset = 3.0

        # pixWidth/self.pixHeight are now the dimensions in points for the Flowable
        self.displayScale = self.pixHeight / _parentH

        # don't think these are needed
        pixBottom = pageHeight - self.pixHeight - self.margin
        pixLeft = self.margin

        # read the strip spacing form the params
        self.stripSpacing = self.params[GLSTRIPPADDING] * self.displayScale

    def _addBackgroundBox(self, thisPlot):
        """Make a background box to cover the plot area
        """
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

        # add to the drawing object
        thisPlot.add(gr, name='mainPlotBox')

        # gr = Group()
        # # paint a background box
        # ll = [0.0, 0.0,
        #       0.0, self.pixHeight,
        #       self.pixWidth, self.pixHeight,
        #       self.pixWidth, 0.0]
        # if ll:
        #     pl = Path(fillColor=self.backgroundColour, stroke=None, strokeColor=None)
        #     pl.moveTo(ll[0], ll[1])
        #     for vv in range(2, len(ll), 2):
        #         pl.lineTo(ll[vv], ll[vv + 1])
        #     pl.closePath()
        #     gr.add(pl)

        # # frame the top-left of the main plot area
        # ll = [self.displayScale * self.mainView.left, self.displayScale * self.mainView.bottom,
        #       self.displayScale * self.mainView.left, self.pixHeight,
        #       self.displayScale * self.mainView.width, self.pixHeight]
        # # ll = [self.displayScale * self.mainL, self.displayScale * self.mainB,
        # #       self.displayScale * self.mainL, self.pixHeight,
        # #       self.displayScale * self.mainW, self.pixHeight]
        #
        # if ll and self.params[GLPLOTBORDER]:
        #     pl = Path(strokeColor=self.foregroundColour, strokeWidth=0.5)
        #     pl.moveTo(ll[0], ll[1])
        #     for vv in range(2, len(ll), 2):
        #         pl.lineTo(ll[vv], ll[vv + 1])
        #     gr.add(pl)
        # # add to the drawing object
        # self._mainPlot.add(gr, name='mainPlotBox')

    def _addPlotBorders(self, thisPlot):
        """Add requires borders to the plot area
        """
        # frame the top-left of the main plot area - after other plotting
        gr = Group()
        ll = [self.displayScale * self.mainView.left, self.displayScale * self.mainView.bottom,
              self.displayScale * self.mainView.left, self.pixHeight,
              self.displayScale * self.mainView.width, self.pixHeight,
              self.displayScale * self.mainView.width, self.displayScale * self.mainView.bottom,
              self.displayScale * self.mainView.left, self.displayScale * self.mainView.bottom]

        if ll:
            pl = Path(fillColor=None,
                      strokeColor=self.foregroundColour if self.params[GLPLOTBORDER] else self.backgroundColour,
                      strokeWidth=0.5 * self.baseThickness)
            pl.moveTo(ll[0], ll[1])
            for vv in range(2, len(ll), 2):
                pl.lineTo(ll[vv], ll[vv + 1])
            gr.add(pl)

        thisPlot.add(gr, name='mainPlotBox')

    def _buildStrip(self, axesOnly=False):
        # create an object that can be added to a report
        self._mainPlot = Drawing(self.pixWidth, self.pixHeight)
        self._addBackgroundBox(self._mainPlot)

        # get the list of required spectra
        self._ordering = self.strip.spectrumDisplay.orderedSpectrumViews(self.strip.spectrumViews)

        # set the range for the display
        _oldValues = (self.strip._CcpnGLWidget.axisL, self.strip._CcpnGLWidget.axisR, self.strip._CcpnGLWidget.axisT, self.strip._CcpnGLWidget.axisB)
        try:
            _update = False
            _dd = self.params[GLSTRIPREGIONS][self.strip.id]
            _update = _dd.useRegion
            if _update:
                for ii, ddAxis in enumerate(_dd.axes):
                    if _dd.minMaxMode == 0:
                        self.strip.setAxisRegion(ii, (ddAxis['Min'], ddAxis['Max']), rescale=False, update=False)
                    else:
                        self.strip.setAxisPosition(ii, ddAxis['Centre'], rescale=False, update=False)
                        self.strip.setAxisWidth(ii, ddAxis['Width'], rescale=False, update=False)

                self._axisL = self.strip._CcpnGLWidget.axisL
                self._axisR = self.strip._CcpnGLWidget.axisR
                self._axisT = self.strip._CcpnGLWidget.axisT
                self._axisB = self.strip._CcpnGLWidget.axisB
                self.strip._CcpnGLWidget._rescaleAllAxes(update=False)
                self.strip._CcpnGLWidget._buildGL()
                self.strip._CcpnGLWidget.buildAxisLabels()

            else:
                self._axisL = self.strip._CcpnGLWidget.axisL
                self._axisR = self.strip._CcpnGLWidget.axisR
                self._axisT = self.strip._CcpnGLWidget.axisT
                self._axisB = self.strip._CcpnGLWidget.axisB
        except Exception as es:
            pass

        # print the grid objects
        if self.params[GLGRIDLINES]: self._addGridLines()

        if not axesOnly:
            if self.params[GLDIAGONALLINE]: self._addDiagonalLine()
            if self.params[GLDIAGONALSIDEBANDS]: self._addDiagonalSideBands()

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
            else:
                # currently only in stacking mode
                if self.params[GLSPECTRUMLABELS]: self._addSpectrumLabels()

            if self.params[GLTRACES]: self._addTraces()
            if self.params[GLACTIVETRACES]: self._addLiveTraces()

            if not self._parent._stackingMode:
                if self.params[GLOTHERLINES]: self._addInfiniteLines()
            if self.params[GLSTRIPLABELLING]: self._addOverlayText()

            # frame the top-left of the main plot area - after other plotting
            self._addPlotBorders(self._mainPlot)

            # add the axis labels which requires a mask to clean the edges
            self._addAxisMask()

        self._addGridTickMarks()

        if not axesOnly:
            if self.params[GLCURSORS]: self._addCursors()

        if self.params[GLAXISLABELS] or self.params[GLAXISUNITS] or self.params[GLAXISTITLES]: self._addGridLabels()

        try:
            if _update:
                # reset the strip to the original values
                self.strip._CcpnGLWidget.axisL, self.strip._CcpnGLWidget.axisR, self.strip._CcpnGLWidget.axisT, self.strip._CcpnGLWidget.axisB = _oldValues
                self.strip._CcpnGLWidget._rescaleAllZoom()
                self.strip._CcpnGLWidget._buildGL()
                self.strip._CcpnGLWidget.buildAxisLabels()
        except Exception as es:
            pass

    def _addGridLines(self):
        """
        Add grid lines to the main drawing area.
        """
        if self._parent._gridVisible and self._parent.gridList[0]:
            colourGroups = OrderedDict()
            self._appendIndexLineGroup(indArray=self._parent.gridList[0],
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT  : self.displayScale * self.mainView.left,
                                                PLOTBOTTOM: self.displayScale * self.mainView.bottom,
                                                PLOTWIDTH : self.displayScale * self.mainView.width,
                                                PLOTHEIGHT: self.displayScale * self.mainView.height},
                                       name='grid',
                                       ratioLine=True,
                                       lineWidth=0.5 * self.baseThickness)
            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='grid')

    def _addDiagonalSideBands(self):
        """
        Add the diagonal sideBand lines to the main drawing area.
        """
        if self._parent.diagonalSideBandsGLList and self._parent._matchingIsotopeCodes:
            colourGroups = OrderedDict()
            self._appendIndexLineGroup(indArray=self._parent.diagonalSideBandsGLList,
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT  : self.displayScale * self.mainView.left,
                                                PLOTBOTTOM: self.displayScale * self.mainView.bottom,
                                                PLOTWIDTH : self.displayScale * self.mainView.width,
                                                PLOTHEIGHT: self.displayScale * self.mainView.height},
                                       name='diagonal',
                                       ratioLine=True,
                                       lineWidth=0.5 * self.baseThickness)
            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='diagonal')

    def _addDiagonalLine(self):
        """
        Add the diagonal line to the main drawing area.
        """
        if self._parent.diagonalGLList and self._parent._matchingIsotopeCodes:
            colourGroups = OrderedDict()
            self._appendIndexLineGroup(indArray=self._parent.diagonalGLList,
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT  : self.displayScale * self.mainView.left,
                                                PLOTBOTTOM: self.displayScale * self.mainView.bottom,
                                                PLOTWIDTH : self.displayScale * self.mainView.width,
                                                PLOTHEIGHT: self.displayScale * self.mainView.height},
                                       name='diagonal',
                                       ratioLine=True,
                                       lineWidth=0.5 * self.baseThickness)
            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='diagonal')

    def _addCursors(self):
        """
        Add cursors/double cursor to the main drawing area.
        """
        if self._parent._cursorList:
            colourGroups = OrderedDict()
            self._appendIndexLineGroup(indArray=self._parent._cursorList,
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT  : self.displayScale * self.mainView.left,
                                                PLOTBOTTOM: self.displayScale * self.mainView.bottom,
                                                PLOTWIDTH : self.displayScale * self.mainView.width,
                                                PLOTHEIGHT: self.displayScale * self.mainView.height},
                                       name='cursors',
                                       ratioLine=True,
                                       lineWidth=0.5 * self.baseThickness)
            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='cursors')

    def _addSpectrumViewManager(self, groupName):
        """
        Add the spectrum objects to the main drawing area.
        Generator function to iterate over all the aliasing regions of all
        spectrumViews in the strip and execute user code each iteration

        e.g.

        >>> for data in self._addSpectrumViewManager('spectrumContours'):
        >>>     print(data.spectrum)
        """


        # simple class to export variables from the generator function
        @dataclass
        class _editValues:
            colourGroups = OrderedDict()
            GLObject = None
            specSettings = None
            spectrum = None
            dimensionCount = 0
            matrix = None
            spectrumView = None
            x = 0
            y = 0
            width = 0
            height = 0
            index = 0
            alias = None


        _data = _editValues()

        # set the display parameters
        _data.x = _x = self.displayScale * self.mainView.left
        _data.y = _y = self.displayScale * self.mainView.bottom
        _data.width = _width = self.displayScale * self.mainView.width
        _data.height = _height = self.displayScale * self.mainView.height
        _data.index = 0

        for spectrumView in self._ordering:

            if spectrumView.isDeleted:
                continue

            if spectrumView.spectrum.pid in self.params[GLSELECTEDPIDS]:

                # get the contour list
                _data.GLObject = self._parent._contourList[spectrumView] if spectrumView in self._parent._contourList else None

                if spectrumView in self._parent._spectrumSettings.keys():

                    # get the spectrum settings for the spectrumView
                    _data.specSettings = specSettings = self._parent._spectrumSettings[spectrumView]
                    _data.spectrumView = spectrumView
                    _data.spectrum = spectrumView.spectrum
                    _data.dimensionCount = spectrumView.spectrum.dimensionCount

                    if spectrumView.spectrum.dimensionCount > 1:
                        # draw nD spectra

                        # self.globalGL._shaderProgram1.setGLUniformMatrix4fv('mvMatrix',
                        #                                            1, GL.GL_FALSE,
                        #                                            self._spectrumSettings[spectrumView][SPECTRUM_MATRIX])

                        _, fxMax = specSettings[SPECTRUM_XLIMITS]
                        _, fyMax = specSettings[SPECTRUM_YLIMITS]
                        dxAF, dyAF = specSettings[SPECTRUM_AF]
                        xScale, yScale = specSettings[SPECTRUM_SCALE]
                        alias = specSettings[SPECTRUM_ALIASINGINDEX]
                        folding = specSettings[SPECTRUM_FOLDINGMODE]

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

                                # build the spectrum transformation matrix
                                specMatrix = np.array([xScale * foldX, 0.0, 0.0, 0.0,
                                                       0.0, yScale * foldY, 0.0, 0.0,
                                                       0.0, 0.0, 1.0, 0.0,
                                                       fxMax + (ii * dxAF) + foldXOffset, fyMax + (jj * dyAF) + foldYOffset, 0.0, 1.0],
                                                      dtype=np.float32)
                                _data.matrix = np.transpose(specMatrix.reshape((4, 4)))
                                _data.alias = getAliasSetting(ii, jj)
                                # get the transformation matrix from the spectrumView
                                # mat = np.transpose(self._parent._spectrumSettings[spectrumView][SPECTRUM_MATRIX].reshape((4, 4)))

                                # # clip all colours first - not sure if needed now, but was causing overflow error in the past
                                # _colors = np.clip(thisSpec.colors, 0.0, 0.9999)

                                yield _data  # pass object

                                _data.index += 1

                    else:
                        # draw 1D spectra

                        # # assume that the vertexArray is a GL_LINE_STRIP
                        # if spectrumView in self._parent._contourList.keys():

                        _, fxMax = specSettings[SPECTRUM_XLIMITS]
                        dxAF, _ = specSettings[SPECTRUM_AF]
                        alias = specSettings[SPECTRUM_ALIASINGINDEX]
                        folding = specSettings[SPECTRUM_FOLDINGMODE]

                        for ii in range(alias[0][0], alias[0][1] + 1, 1):

                            if self._parent._stackingMode:
                                _matrix = np.array(specSettings[SPECTRUM_STACKEDMATRIX])
                            else:
                                _matrix = np.array(self._parent._IMatrix)

                            foldX = 1.0
                            foldXOffset = foldYOffset = 0
                            if folding[0] == 'mirror':
                                foldX = pow(-1, ii)
                                foldXOffset = (2 * fxMax - dxAF) if foldX < 0 else 0

                            # take the stacking matrix and insert the correct x-scaling to map the pointPositions to the screen
                            _matrix[0] = foldX
                            _matrix[12] += (ii * dxAF) + foldXOffset
                            _data.matrix = np.transpose(_matrix.reshape((4, 4)))
                            _data.alias = getAliasSetting(ii, 0)

                            yield _data  # pass object back to the calling method

                            _data.index += 1

        if _data.colourGroups:
            self._appendGroup(drawing=self._mainPlot, colourGroups=_data.colourGroups, name=groupName)

    def _addSpectrumContours(self):
        """
        Add the spectrum contours to the main drawing area.
        """
        for data in self._addSpectrumViewManager('spectrumContours'):
            if data.dimensionCount > 1:
                for ppInd in range(0, len(data.GLObject.indices), 2):
                    ppInd0 = int(data.GLObject.indices[ppInd])
                    ppInd1 = int(data.GLObject.indices[ppInd + 1])

                    vectStart = [data.GLObject.vertices[ppInd0 * 2], data.GLObject.vertices[ppInd0 * 2 + 1], 0.0, 1.0]
                    vectStart = data.matrix.dot(vectStart)
                    vectEnd = [data.GLObject.vertices[ppInd1 * 2], data.GLObject.vertices[ppInd1 * 2 + 1], 0.0, 1.0]
                    vectEnd = data.matrix.dot(vectEnd)
                    newLine = [vectStart[0], vectStart[1], vectEnd[0], vectEnd[1]]

                    colour = colors.Color(*data.GLObject.colors[ppInd0 * 4:ppInd0 * 4 + 3], alpha=alphaClip(data.GLObject.colors[ppInd0 * 4 + 3]))
                    colourPath = 'spectrumContours%s%s%s%s%s%s' % (data.spectrumView.pid, data.index, colour.red, colour.green, colour.blue, colour.alpha)

                    newLine = self.lineVisible(self._parent, newLine, x=data.x, y=data.y, width=data.width, height=data.height)
                    if newLine:
                        if colourPath not in data.colourGroups:
                            data.colourGroups[colourPath] = {PDFLINES      : [],
                                                             PDFSTROKEWIDTH: 0.5 * self.baseThickness * self.contourThickness,
                                                             PDFSTROKECOLOR: colour, PDFSTROKELINECAP: 1}
                        data.colourGroups[colourPath][PDFLINES].append(newLine)

            else:
                # drawVertexColor
                self._appendVertexLineGroup(indArray=data.GLObject,
                                            colourGroups=data.colourGroups,
                                            plotDim={PLOTLEFT  : data.x,
                                                     PLOTBOTTOM: data.y,
                                                     PLOTWIDTH : data.width,
                                                     PLOTHEIGHT: data.height},
                                            name='spectrumContours%s%s' % (data.spectrumView.pid, data.index),
                                            mat=data.matrix,
                                            lineWidth=0.5 * self.baseThickness * self.contourThickness
                                            )

    def _addSpectrumBoundaries(self):
        """
        Add the spectrum boundaries to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroup(indArray=self._parent.boundingBoxes,
                                   colourGroups=colourGroups,
                                   plotDim={PLOTLEFT  : self.displayScale * self.mainView.left,
                                            PLOTBOTTOM: self.displayScale * self.mainView.bottom,
                                            PLOTWIDTH : self.displayScale * self.mainView.width,
                                            PLOTHEIGHT: self.displayScale * self.mainView.height},
                                   name='boundary',
                                   lineWidth=0.5 * self.baseThickness)
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='boundaries')

    def _addPeakSymbols(self):
        """
        Add the peak symbols to the main drawing area.
        """
        _symbols = self._parent._GLPeaks._GLSymbols

        for data in self._addSpectrumViewManager('peakSymbols'):
            attribList = data.spectrumView.peakListViews
            validListViews = [_symbols[pp] for pp in attribList
                              if pp in _symbols.keys()
                              and pp.isVisible()
                              and data.spectrumView.isVisible()
                              and pp.peakList.pid in self.params[GLSELECTEDPIDS]
                              ]

            for GLObject in validListViews:
                self._appendIndexLineGroup(indArray=GLObject,
                                           colourGroups=data.colourGroups,
                                           plotDim={PLOTLEFT  : data.x,
                                                    PLOTBOTTOM: data.y,
                                                    PLOTWIDTH : data.width,
                                                    PLOTHEIGHT: data.height},
                                           name='spectrumView%s%s%s' % ('peakSymbols', data.index, data.spectrumView.pid),
                                           mat=data.matrix,
                                           fillMode=None,
                                           splitGroups=False,
                                           lineWidth=0.5 * self.baseThickness * self.symbolThickness,
                                           alias=data.alias)

    def _addMultipletSymbols(self):
        """
        Add the multiplet symbols to the main drawing area.
        """
        _symbols = self._parent._GLMultiplets._GLSymbols

        for data in self._addSpectrumViewManager('multipletSymbols'):
            attribList = data.spectrumView.multipletListViews
            validListViews = [_symbols[pp] for pp in attribList
                              if pp in _symbols.keys()
                              and pp.isVisible()
                              and data.spectrumView.isVisible()
                              and pp.multipletList.pid in self.params[GLSELECTEDPIDS]]

            for GLObject in validListViews:
                self._appendIndexLineGroup(indArray=GLObject,
                                           colourGroups=data.colourGroups,
                                           plotDim={PLOTLEFT  : data.x,
                                                    PLOTBOTTOM: data.y,
                                                    PLOTWIDTH : data.width,
                                                    PLOTHEIGHT: data.height},
                                           name='spectrumView%s%s%s' % ('multipletSymbols', data.index, data.spectrumView.pid),
                                           mat=data.matrix,
                                           fillMode=None,
                                           splitGroups=False,
                                           lineWidth=0.5 * self.baseThickness * self.symbolThickness,
                                           alias=data.alias)

    def _addMarkLines(self):
        """
        Add the mark lines to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroup(indArray=self._parent._marksList,
                                   colourGroups=colourGroups,
                                   plotDim={PLOTLEFT  : self.displayScale * self.mainView.left,
                                            PLOTBOTTOM: self.displayScale * self.mainView.bottom,
                                            PLOTWIDTH : self.displayScale * self.mainView.width,
                                            PLOTHEIGHT: self.displayScale * self.mainView.height},
                                   name='marks',
                                   lineWidth=0.5 * self.baseThickness)
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='marks')

    def _addIntegralLines(self):
        """
        Add the integral lines to the main drawing area.
        """
        colourGroups = OrderedDict()
        self._appendIndexLineGroupFill(indArray=self._parent._GLIntegrals._GLSymbols,
                                       listView='integralList',
                                       colourGroups=colourGroups,
                                       plotDim={PLOTLEFT  : self.displayScale * self.mainView.left,
                                                PLOTBOTTOM: self.displayScale * self.mainView.bottom,
                                                PLOTWIDTH : self.displayScale * self.mainView.width,
                                                PLOTHEIGHT: self.displayScale * self.mainView.height},
                                       name='IntegralListsFill',
                                       fillMode=GL.GL_FILL,
                                       splitGroups=True,
                                       lineWidth=0.5 * self.baseThickness)
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

            _x = self.displayScale * self.mainView.left
            _y = self.displayScale * self.mainView.bottom
            _width = self.displayScale * self.mainView.width
            _height = self.displayScale * self.mainView.height

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

                            newLine = self.lineVisible(self._parent, newLine, x=_x, y=_y, width=_width, height=_height)
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
                                   plotDim={PLOTLEFT  : self.displayScale * self.mainView.left,
                                            PLOTBOTTOM: self.displayScale * self.mainView.bottom,
                                            PLOTWIDTH : self.displayScale * self.mainView.width,
                                            PLOTHEIGHT: self.displayScale * self.mainView.height},
                                   name='regions',
                                   lineWidth=0.5 * self.baseThickness)
        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='regions')

    def _addPeakLabels(self):
        """
        Add the peak labels to the main drawing area.
        """
        colourGroups = OrderedDict()

        for data in self._addSpectrumViewManager('peakLabels'):

            validPeakListViews = [pp for pp in data.spectrumView.peakListViews
                                  if pp.isVisible()
                                  and data.spectrumView.isVisible()
                                  and pp in self._parent._GLPeaks._GLLabels.keys()
                                  and pp.peakList.pid in self.params[GLSELECTEDPIDS]]

            for peakListView in validPeakListViews:  # spectrumView.peakListViews:
                for drawString in self._parent._GLPeaks._GLLabels[peakListView].stringList:

                    if drawString.vertices is None or drawString.vertices.size == 0:
                        continue

                    col = drawString.colors[0]
                    if not isinstance(col, Iterable):
                        col = drawString.colors[0:4]
                    _alias = 1.0
                    if data.alias is not None and drawString._alias is not None:
                        if abs(data.alias - drawString._alias) > 0.5:
                            _alias = self.params[GLALIASSHADE] / 100.0

                    colour = colors.Color(*col[0:3], alpha=_alias * alphaClip(col[3]))
                    colourPath = 'spectrumViewPeakLabels%s%s%s%s%s%s' % (
                        data.spectrumView.pid, data.index, colour.red, colour.green, colour.blue, colour.alpha)

                    if data.matrix is not None:
                        newLine = [drawString.attribs[0], drawString.attribs[1], 0.0, 1.0]
                        newLine = data.matrix.dot(newLine)[0:2]
                    else:
                        newLine = [drawString.attribs[0], drawString.attribs[1]]

                    if self.pointVisible(self._parent, newLine,
                                         x=data.x,
                                         y=data.y,
                                         width=data.width,
                                         height=data.height):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()
                        textGroup = drawString.text.split('\n')
                        textLine = len(textGroup) - 1
                        for text in textGroup:
                            self._addString2(colourGroups, colourPath,
                                             drawString,
                                             (newLine[0], newLine[1]),  # + (textLine * drawString.font.fontSize * self.fontScale)),
                                             colour,
                                             text=text,
                                             offset=textLine
                                             )
                            # colourGroups[colourPath].add(String(newLine[0], newLine[1] + (textLine * drawString.font.fontSize * self.fontScale),
                            #                                     text,
                            #                                     fontSize=drawString.font.fontSize * self.fontScale,
                            #                                     fontName=drawString.font.fontName,
                            #                                     fillColor=colour))
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

                    if drawString.vertices is None or drawString.vertices.size == 0:
                        continue

                    col = drawString.colors[0]
                    if not isinstance(col, Iterable):
                        col = drawString.colors[0:4]
                    colour = colors.Color(*col[0:3], alpha=alphaClip(col[3]))
                    colourPath = 'spectrumViewIntegralLabels%s%s%s%s%s' % (
                        spectrumView.pid, colour.red, colour.green, colour.blue, colour.alpha)

                    newLine = [drawString.attribs[0], drawString.attribs[1]]
                    if self.pointVisible(self._parent, newLine,
                                         x=self.displayScale * self.mainView.left,
                                         y=self.displayScale * self.mainView.bottom,
                                         width=self.displayScale * self.mainView.width,
                                         height=self.displayScale * self.mainView.height):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()
                        textGroup = drawString.text.split('\n')
                        textLine = len(textGroup) - 1
                        for text in textGroup:
                            self._addString2(colourGroups, colourPath,
                                             drawString,
                                             (newLine[0], newLine[1]),  # + (textLine * drawString.font.fontSize * self.fontScale)),
                                             colour,
                                             text=text,
                                             offset=textLine
                                             )
                            # colourGroups[colourPath].add(String(newLine[0], newLine[1] + (textLine * drawString.font.fontSize * self.fontScale),
                            #                                     text,
                            #                                     fontSize=drawString.font.fontSize * self.fontScale,
                            #                                     fontName=drawString.font.fontName,
                            #                                     fillColor=colour))
                            textLine -= 1

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addMultipletLabels(self):
        """
        Add the multiplet labels to the main drawing area.
        """
        colourGroups = OrderedDict()

        for data in self._addSpectrumViewManager('multipletLabels'):

            validMultipletListViews = [pp for pp in data.spectrumView.multipletListViews
                                       if pp.isVisible()
                                       and data.spectrumView.isVisible()
                                       and pp in self._parent._GLMultiplets._GLLabels.keys()
                                       and pp.multipletList.pid in self.params[GLSELECTEDPIDS]]

            for multipletListView in validMultipletListViews:  # spectrumView.multipletListViews:
                for drawString in self._parent._GLMultiplets._GLLabels[multipletListView].stringList:

                    if drawString.vertices is None or drawString.vertices.size == 0:
                        continue

                    col = drawString.colors[0]
                    if not isinstance(col, Iterable):
                        col = drawString.colors[0:4]
                    _alias = 1.0
                    if data.alias is not None and drawString._alias is not None:
                        if abs(data.alias - drawString._alias) > 0.5:
                            _alias = self.params[GLALIASSHADE] / 100.0

                    colour = colors.Color(*col[0:3], alpha=_alias * alphaClip(col[3]))
                    colourPath = 'spectrumViewMultipletLabels%s%s%s%s%s%s' % (
                        data.spectrumView.pid, data.index, colour.red, colour.green, colour.blue, colour.alpha)

                    if data.matrix is not None:
                        newLine = [drawString.attribs[0], drawString.attribs[1], 0.0, 1.0]
                        newLine = data.matrix.dot(newLine)[0:2]
                    else:
                        newLine = [drawString.attribs[0], drawString.attribs[1]]

                    if self.pointVisible(self._parent, newLine,
                                         x=data.x,
                                         y=data.y,
                                         width=data.width,
                                         height=data.height):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()
                        textGroup = drawString.text.split('\n')
                        textLine = len(textGroup) - 1
                        for text in textGroup:
                            self._addString2(colourGroups, colourPath,
                                             drawString,
                                             (newLine[0], newLine[1]),  # + (textLine * drawString.font.fontSize * self.fontScale)),
                                             colour,
                                             text=text,
                                             offset=textLine
                                             )
                            # colourGroups[colourPath].add(String(newLine[0], newLine[1] + (textLine * drawString.font.fontSize * self.fontScale),
                            #                                     text,
                            #                                     fontSize=drawString.font.fontSize * self.fontScale,
                            #                                     fontName=drawString.font.fontName,
                            #                                     fillColor=colour))
                            textLine -= 1

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addMarkLabels(self):
        """
        Add the mark labels to the main drawing area.
        """
        colourGroups = OrderedDict()
        for drawString in self._parent._marksAxisCodes:

            if drawString.vertices is None or drawString.vertices.size == 0:
                continue

            col = drawString.colors[0]
            if not isinstance(col, Iterable):
                col = drawString.colors[0:4]
            colour = colors.Color(*col[0:3], alpha=alphaClip(col[3]))
            colourPath = 'projectMarks%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

            newLine = [drawString.attribs[0], drawString.attribs[1]]
            if self.pointVisible(self._parent, newLine,
                                 x=self.displayScale * self.mainView.left,
                                 y=self.displayScale * self.mainView.bottom,
                                 width=self.displayScale * self.mainView.width,
                                 height=self.displayScale * self.mainView.height):
                if colourPath not in colourGroups:
                    colourGroups[colourPath] = Group()
                self._addString(colourGroups, colourPath, drawString, newLine, colour, boxed=False)

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addSpectrumLabels(self):
        """
        Add the (stacked) spectrum labels to the main drawing area.
        """
        colourGroups = OrderedDict()

        if not (self._parent._spectrumLabelling and self._parent._spectrumLabelling.strings):
            return

        for drawString in self._parent._spectrumLabelling.strings.values():

            if drawString.vertices is None or drawString.vertices.size == 0:
                continue

            col = drawString.colors[0]
            if not isinstance(col, Iterable):
                col = drawString.colors[0:4]
            colour = colors.Color(*col[0:3], alpha=alphaClip(col[3]))
            colourPath = 'projectSpectrumLabels%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

            newLine = [drawString.attribs[0], drawString.attribs[1]]
            if self.pointVisible(self._parent, newLine,
                                 x=self.displayScale * self.mainView.left,
                                 y=self.displayScale * self.mainView.bottom,
                                 width=self.displayScale * self.mainView.width,
                                 height=self.displayScale * self.mainView.height):
                if colourPath not in colourGroups:
                    colourGroups[colourPath] = Group()
                self._addString(colourGroups, colourPath, drawString, newLine, colour, boxed=True)

        for colourGroup in colourGroups.values():
            self._mainPlot.add(colourGroup)

    def _addSingleTrace(self, traceName, trace, spectrumView, colourGroups):
        if spectrumView and not spectrumView.isDeleted and spectrumView.isVisible():
            # drawVertexColor

            if self._parent._stackingMode:
                mat = np.transpose(self._parent._spectrumSettings[spectrumView][SPECTRUM_STACKEDMATRIX].reshape((4, 4)))
            else:
                mat = None

            self._appendVertexLineGroup(indArray=trace,
                                        colourGroups=colourGroups,
                                        plotDim={PLOTLEFT  : self.displayScale * self.mainView.left,
                                                 PLOTBOTTOM: self.displayScale * self.mainView.bottom,
                                                 PLOTWIDTH : self.displayScale * self.mainView.width,
                                                 PLOTHEIGHT: self.displayScale * self.mainView.height},
                                        name='%s%s' % (traceName, spectrumView.pid),
                                        includeLastVertex=not self._parent.is1D,
                                        mat=mat,
                                        lineWidth=0.5 * self.baseThickness * self.contourThickness)

    def _addTraces(self):
        """
        Add the traces to the main drawing area.
        """
        colourGroups = OrderedDict()
        for hTrace in self._parent._staticHTraces:
            self._addSingleTrace('hTrace', hTrace, hTrace.spectrumView, colourGroups)
        for vTrace in self._parent._staticVTraces:
            self._addSingleTrace('vTrace', vTrace, vTrace.spectrumView, colourGroups)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='traces')

    def _addLiveTraces(self):
        """
        Add the live traces to the main drawing area.
        """
        colourGroups = OrderedDict()
        if self._parent.showActivePhaseTrace or not self._parent.spectrumDisplay.phasingFrame.isVisible():

            if self._parent._updateHTrace:
                for spectrumView, hTrace in self._parent._hTraces.items():
                    self._addSingleTrace('hTrace', hTrace, spectrumView, colourGroups)
            if self._parent._updateVTrace:
                for spectrumView, vTrace in self._parent._vTraces.items():
                    self._addSingleTrace('vTrace', vTrace, spectrumView, colourGroups)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='traces')

    def _addInfiniteLines(self):
        """
        Add the infinite lines to the main drawing area.
        """
        colourGroups = OrderedDict()
        _x = self.displayScale * self.mainView.left
        _y = self.displayScale * self.mainView.bottom
        _width = self.displayScale * self.mainView.width
        _height = self.displayScale * self.mainView.height

        for infLine in self._parent._infiniteLines:
            if infLine.visible:
                colour = colors.Color(*infLine.brush[0:3], alpha=alphaClip(infLine.brush[3]))
                colourPath = 'infiniteLines%s%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha, infLine.lineStyle)

                if infLine.orientation == 'h':
                    newLine = [self._axisL, infLine.values, self._axisR, infLine.values]
                else:
                    newLine = [infLine.values, self._axisT, infLine.values, self._axisB]

                newLine = self.lineVisible(self._parent, newLine, x=_x, y=_y, width=_width, height=_height)
                if newLine:
                    if colourPath not in colourGroups:
                        colourGroups[colourPath] = {PDFLINES          : [],
                                                    PDFSTROKEWIDTH    : 0.5 * infLine.lineWidth * self.baseThickness,
                                                    PDFSTROKECOLOR    : colour,
                                                    PDFSTROKELINECAP  : 1, PDFCLOSEPATH: False,
                                                    PDFSTROKEDASHARRAY: GLLINE_STYLES_ARRAY[infLine.lineStyle]}
                    colourGroups[colourPath][PDFLINES].append(newLine)

        self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='infiniteLines')

    def _scaleRatioToWindow(self, values):
        return [values[0] * (self._axisR - self._axisL) + self._axisL,
                values[1] * (self._axisT - self._axisB) + self._axisB]

    def _addOverlayText(self):
        """
        Add the overlay text to the main drawing area.
        """
        colourGroups = OrderedDict()
        drawString = self._parent.stripIDString

        if drawString.vertices is None or drawString.vertices.size == 0:
            return

        colour = self.foregroundColour
        colourPath = 'overlayText%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

        newLine = self._scaleRatioToWindow([drawString.attribs[0] + (self.fontXOffset * self._parent.deltaX),
                                            drawString.attribs[1] + (self.fontYOffset * self._parent.deltaY)])

        if self.pointVisible(self._parent, newLine,
                             x=self.displayScale * self.mainView.left,
                             y=self.displayScale * self.mainView.bottom,
                             width=self.displayScale * self.mainView.width,
                             height=self.displayScale * self.mainView.height):
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
                   0.0, self.displayScale * self.mainView.bottom,
                   self.displayScale * self.mainView.width, self.displayScale * self.mainView.bottom,
                   self.displayScale * self.mainView.width, self.pixHeight,
                   self.pixWidth, self.pixHeight,
                   self.pixWidth, 0.0]
            ll2 = [0.0, 0.0, self.pixWidth, 0.0, self.pixWidth, self.pixHeight]

        elif self.rAxis:
            ll1 = [self.displayScale * self.mainView.width, 0.0,
                   self.displayScale * self.mainView.width, self.pixHeight,
                   self.pixWidth, self.pixHeight,
                   self.pixWidth, 0.0]
            ll2 = [self.pixWidth, 0.0, self.pixWidth, self.pixHeight]

        elif self.bAxis:
            ll1 = [0.0, 0.0,
                   0.0, self.displayScale * self.mainView.bottom,
                   self.pixWidth, self.displayScale * self.mainView.bottom,
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

            # add the right axis if visible
            if self.rAxis and self.params[GLAXISMARKS]:
                indArray = self._parent.gridList[1]

                if indArray.indices is not None and indArray.indices.size != 0:
                    # add the vertices for the grid lines
                    self._appendIndexLineGroup(indArray=indArray,
                                               colourGroups=colourGroups,
                                               plotDim={PLOTLEFT  : self.displayScale * self.rAxisMarkView.left,
                                                        PLOTBOTTOM: self.displayScale * self.rAxisMarkView.bottom,
                                                        PLOTWIDTH : self.displayScale * self.rAxisMarkView.width,
                                                        PLOTHEIGHT: self.displayScale * self.rAxisMarkView.height},
                                               name='gridAxes',
                                               setColour=self.foregroundColour,
                                               ratioLine=True,
                                               lineWidth=0.5 * self.baseThickness)

            # # add the right axis border line if needed
            # if self.params[GLPLOTBORDER] or (self.rAxis and self.params[GLAXISLINES]):
            #     from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray
            #
            #     # dummy list with non-visible line
            #     tempVertexArray = GLVertexArray(numLists=1, drawMode=GL.GL_LINE, dimension=2)
            #     tempVertexArray.indices = [0, 1]
            #     tempVertexArray.vertices = [0.0, 0.0, 0.0, 0.0]
            #
            #     # return the colour list defined by self.foreColour - needs setColour to be defined in the function call
            #     setGroup = self._appendIndexLineGroup(indArray=tempVertexArray,
            #                                           colourGroups=colourGroups,
            #                                           plotDim={PLOTLEFT  : self.displayScale * self.rAxisMarkView.left,
            #                                                    PLOTBOTTOM: self.displayScale * self.rAxisMarkView.bottom,
            #                                                    PLOTWIDTH : self.displayScale * self.rAxisMarkView.width,
            #                                                    PLOTHEIGHT: self.displayScale * self.rAxisMarkView.height},
            #                                           name='gridAxes',
            #                                           setColour=self.foregroundColour,
            #                                           ratioLine=True,
            #                                           lineWidth=0.5 * self.baseThickness)
            #     if setGroup in colourGroups:
            #         colourGroups[setGroup][PDFLINES].append([self.displayScale * self.mainView.width, self.displayScale * self.mainView.bottom,
            #                                                  self.displayScale * self.mainView.width, self.pixHeight])

            # add the bottom axis if visible
            if self.bAxis and self.params[GLAXISMARKS]:
                indArray = self._parent.gridList[2]

                if indArray.indices is not None and indArray.indices.size != 0:
                    # add the vertices for the grid lines
                    self._appendIndexLineGroup(indArray=indArray,
                                               colourGroups=colourGroups,
                                               plotDim={PLOTLEFT  : self.displayScale * self.bAxisMarkView.left,
                                                        PLOTBOTTOM: self.displayScale * self.bAxisMarkView.bottom,
                                                        PLOTWIDTH : self.displayScale * self.bAxisMarkView.width,
                                                        PLOTHEIGHT: self.displayScale * self.bAxisMarkView.height},
                                               name='gridAxes',
                                               setColour=self.foregroundColour,
                                               ratioLine=True,
                                               lineWidth=0.5 * self.baseThickness)

            # # add the bottom axis border line if needed
            # if self.params[GLPLOTBORDER] or (self.bAxis and self.params[GLAXISLINES]):
            #     from ccpn.ui.gui.lib.OpenGL.CcpnOpenGLArrays import GLVertexArray
            #
            #     tempVertexArray = GLVertexArray(numLists=1, drawMode=GL.GL_LINE, dimension=2)
            #     tempVertexArray.indices = [0, 1]
            #     tempVertexArray.vertices = [0.0, 0.0, 0.0, 0.0]
            #
            #     # dummy list with non-visible line
            #     setGroup = self._appendIndexLineGroup(indArray=tempVertexArray,
            #                                           colourGroups=colourGroups,
            #                                           plotDim={PLOTLEFT  : self.displayScale * self.bAxisMarkView.left,
            #                                                    PLOTBOTTOM: self.displayScale * self.bAxisMarkView.bottom,
            #                                                    PLOTWIDTH : self.displayScale * self.bAxisMarkView.width,
            #                                                    PLOTHEIGHT: self.displayScale * self.bAxisMarkView.height},
            #                                           name='gridAxes',
            #                                           setColour=self.foregroundColour,
            #                                           ratioLine=True,
            #                                           lineWidth=0.5 * self.baseThickness)
            #
            #     if setGroup in colourGroups:
            #         colourGroups[setGroup][PDFLINES].append([self.displayScale * self.mainView.left, self.displayScale * self.mainView.bottom,
            #                                                  self.displayScale * self.mainView.width, self.displayScale * self.mainView.bottom])

            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name='gridAxes')

    def _addString(self, colourGroups, colourPath, drawString, position, colour, boxed=False):
        self._addString2(colourGroups, colourPath, drawString, position, colour, boxed=boxed)

        # newStr = String(position[0], position[1],
        #                 drawString.text,
        #                 fontSize=drawString.font.fontSize * self.fontScale,
        #                 fontName=drawString.font.fontName,
        #                 fillColor=colour)
        # if boxed:
        #     bounds = newStr.getBounds()
        #     # arbitrary scaling
        #     dx = drawString.font.fontSize * self.fontScale * 0.11  #bounds[0] - position[0]
        #     dy = drawString.font.fontSize * self.fontScale * 0.125  #(position[1] - bounds[1]) / 2.0
        #     colourGroups[colourPath].add(Rect(bounds[0] - dx, bounds[1] - dy,
        #                                       (bounds[2] - bounds[0]) + 5 * dx, (bounds[3] - bounds[1]) + 2.0 * dy,
        #                                       # newLine[0], newLine[1],
        #                                       # drawString.font.fontSize * self.fontScale * len(newLine),
        #                                       # drawString.font.fontSize * self.fontScale,
        #                                       strokeColor=None,
        #                                       fillColor=self.backgroundColour))
        #
        # colourGroups[colourPath].add(newStr)

    def _addString2(self, colourGroups, colourPath, drawString, position, colour, boxed=False, text=None, offset=0):

        if self.params[GLUSEPRINTFONT]:
            _fontName, _fontSize = self.params[GLPRINTFONT]

            # _fontSize = self._printFont.pointSize()
            # if _fontSize < 0:
            #     _fontSize = self._printFont.pixelSize()
            # _fontName = self._printFont.family()
        else:
            _fontSize = drawString.font.fontSize * self.fontScale
            _fontName = drawString.font.fontName

        newStr = String(position[0], position[1] + (offset * _fontSize),
                        text or drawString.text,
                        fontSize=_fontSize,
                        fontName=_fontName,
                        fillColor=colour)

        if boxed:
            bounds = newStr.getBounds()
            # arbitrary scaling
            dx = _fontSize * 0.11
            dy = _fontSize * 0.125
            colourGroups[colourPath].add(Rect(bounds[0] - dx, bounds[1] - dy,
                                              (bounds[2] - bounds[0]) + 5 * dx, (bounds[3] - bounds[1]) + 2.0 * dy,
                                              strokeColor=None,
                                              fillColor=self.backgroundColour))

        colourGroups[colourPath].add(newStr)

    def _addGridLabels(self):
        """
        Add labels/titles/units to the right/bottom axis areas.
        """
        if self.rAxis or self.bAxis:
            colourGroups = OrderedDict()
            if self.rAxis:
                numStrs = len(self._parent._axisYLabelling)

                for strNum, drawString in enumerate(self._parent._axisYLabelling):

                    # skip empty strings
                    if not drawString.text:
                        continue

                    # drawTextArray
                    colour = self.foregroundColour
                    colourPath = 'axisLabels%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

                    # add (0, 3) to mid-point
                    # mid = self._axisL + (0 + drawString.attribs[0]) * (self._axisR - self._axisL) / self._parent.AXIS_MARGINRIGHT
                    # newLine = [mid, drawString.attribs[1] + (3 * self._parent.pixelY)]
                    # mid = self._axisL + drawString.attribs[0] * (self._axisR - self._axisL) * self._parent.pixelX
                    # newLine = [mid, drawString.attribs[1] + (3 * self._parent.deltaY)]

                    attribPos = (0.0, 0.0) if drawString.attribs.size < 2 else drawString.attribs[0:2]
                    newLine = self._scaleRatioToWindow([(self.fontXOffset + attribPos[0]) / self._parent.AXIS_MARGINRIGHT,
                                                        attribPos[1] + (self.fontYOffset * self._parent.deltaY)])

                    if self.pointVisible(self._parent, newLine,
                                         x=self.displayScale * self.rAxisBarView.left,
                                         y=self.displayScale * self.rAxisBarView.bottom,
                                         width=self.displayScale * self.rAxisBarView.width,
                                         height=self.displayScale * self.rAxisBarView.height):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()

                        # set box around the last 2 elements (axis title and units), and skip if not needed
                        if strNum == numStrs - 1 and self.params[GLAXISUNITS]:
                            # draw units
                            self._addString(colourGroups, colourPath, drawString, newLine, colour,
                                            boxed=True)
                        elif strNum == numStrs - 2 and self.params[GLAXISTITLES]:
                            # draw axis title
                            self._addString(colourGroups, colourPath, drawString, newLine, colour,
                                            boxed=True)
                        elif strNum < numStrs - 2 and self.params[GLAXISLABELS]:
                            # draw labels
                            self._addString(colourGroups, colourPath, drawString, newLine, colour,
                                            boxed=False)

            if self.bAxis:
                numStrs = len(self._parent._axisXLabelling)

                for strNum, drawString in enumerate(self._parent._axisXLabelling):

                    # skip empty strings
                    if not drawString.text:
                        continue

                    # drawTextArray
                    colour = self.foregroundColour
                    colourPath = 'axisLabels%s%s%s%s' % (colour.red, colour.green, colour.blue, colour.alpha)

                    # add (0, 3) to mid
                    # mid = self._axisB + (3 + drawString.attribs[1]) * (self._axisT - self._axisB) / self._parent.AXIS_MARGINBOTTOM
                    # newLine = [drawString.attribs[0] + (0 * self._parent.pixelX), mid]
                    # mid = self._axisB + drawString.attribs[1] * (self._axisT - self._axisB)
                    # newLine = [drawString.attribs[0] + (0 * self._parent.deltaX), mid]

                    attribPos = (0.0, 0.0) if drawString.attribs.size < 2 else drawString.attribs[0:2]
                    newLine = self._scaleRatioToWindow([attribPos[0] + (self.fontXOffset * self._parent.deltaX),
                                                        (self.fontYOffset + attribPos[1]) / self._parent.AXIS_MARGINBOTTOM])

                    if self.pointVisible(self._parent, newLine,
                                         x=self.displayScale * self.bAxisBarView.left,
                                         y=self.displayScale * self.bAxisBarView.bottom,
                                         width=self.displayScale * self.bAxisBarView.width,
                                         height=self.displayScale * self.bAxisBarView.height):
                        if colourPath not in colourGroups:
                            colourGroups[colourPath] = Group()

                        # set box around the last 2 elements (axis title and units), and skip if not needed
                        if strNum == numStrs - 1 and self.params[GLAXISUNITS]:
                            # draw units
                            self._addString(colourGroups, colourPath, drawString, newLine, colour,
                                            boxed=True)
                        elif strNum == numStrs - 2 and self.params[GLAXISTITLES]:
                            # draw axis title
                            self._addString(colourGroups, colourPath, drawString, newLine, colour,
                                            boxed=True)
                        elif strNum < numStrs - 2 and self.params[GLAXISLABELS]:
                            # draw labels
                            self._addString(colourGroups, colourPath, drawString, newLine, colour,
                                            boxed=False)

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
                                mainDim={PLOTLEFT  : 0,  #scale*view.left,
                                         PLOTBOTTOM: 0,  #scale*view.bottom,
                                         PLOTWIDTH : self.pixWidth,  #scale*self.mainView.width,
                                         PLOTHEIGHT: self.pixHeight  #scale*self.mainView.height
                                         }
                                )

    def _addDrawingToStory(self):
        """
        Add the current drawing the story of a document
        """
        report = self.report()
        self.stripReports.append(report)
        self._appendStripSize(report)

    def _appendStripSize(self, report):
        # if self.stripNumber < (self.numStrips-1):
        #     self.stripWidths.append(self.pixWidth + self.stripSpacing)
        #     self.stripHeights.append(self.pixHeight + self.stripSpacing)
        # else:
        #     self.stripWidths.append(self.pixWidth)
        #     self.stripHeights.append(self.pixHeight)

        if self.params[GLSTRIPDIRECTION] == 'Y':
            if self.stripNumber < (self.numStrips - 1):
                self.stripWidths.append(report.width + self.stripSpacing)
                self.stripHeights.append(report.height + self.stripSpacing)
            else:
                self.stripWidths.append(report.width)
                self.stripHeights.append(report.height)

        else:
            if 0 < self.stripNumber < self.numStrips:
                self.stripWidths.append(report.width + self.stripSpacing)
                self.stripHeights.append(report.height + self.stripSpacing)
            else:
                self.stripWidths.append(report.width)
                self.stripHeights.append(report.height)

    def _addTableToStory(self):
        if self.params[GLSTRIPDIRECTION] == 'Y':

            # arrange as a row
            table = (self.stripReports,)
            self._report.story.append(Table(table, colWidths=self.stripWidths))
        else:

            # arrange as a column
            table = tuple((rep,) for rep in self.stripReports)
            heights = self.stripHeights[:]
            self._report.story.append(Table(table, rowHeights=heights))

    def writePNGFile(self):
        """
        Output a PNG file for the GL widget.
        """
        dpi = self.params[GLEXPORTDPI]

        # NOTE:ED - need to look at this as only saves the last created drawing, how to concatenate?
        self._mainPlot.scale(dpi / 72, dpi / 72)
        renderPM.drawToFile(self._mainPlot, self.filename, fmt='PNG', dpi=dpi, showBoundary=False)

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

    def writePSFile(self):
        """
        Output a PS file for the GL widget.
        """
        renderPS.drawToFile(self._mainPlot, self.filename, showBoundary=False)

    def _appendVertexLineGroup(self, indArray, colourGroups, plotDim, name, mat=None,
                               includeLastVertex=False, lineWidth=0.5):
        _x = plotDim[PLOTLEFT]
        _y = plotDim[PLOTBOTTOM]
        _width = plotDim[PLOTWIDTH]
        _height = plotDim[PLOTHEIGHT]

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

            newLine = self.lineVisible(self._parent, newLine, x=_x, y=_y, width=_width, height=_height)
            if newLine:
                colourGroups[colourPath][PDFLINES].append(newLine)

    def _colourID(self, name, colour):
        return 'spectrumView%s%s%s%s%s' % (name, colour.red, colour.green, colour.blue, colour.alpha)

    def _appendIndexLineGroup(self, indArray, colourGroups, plotDim, name, mat=None,
                              fillMode=None, splitGroups=False,
                              setColour=None, lineWidth=0.5, ratioLine=False, alias=None):
        if indArray.drawMode == GL.GL_TRIANGLES:
            indexLen = 3
        elif indArray.drawMode == GL.GL_QUADS:
            indexLen = 4
        else:
            indexLen = 2

        # override so that each element is a new group
        if splitGroups:
            colourGroups = OrderedDict()

        _x = plotDim[PLOTLEFT]
        _y = plotDim[PLOTBOTTOM]
        _width = plotDim[PLOTWIDTH]
        _height = plotDim[PLOTHEIGHT]

        for ii in range(0, len(indArray.indices), indexLen):
            ii0 = [int(ind) for ind in indArray.indices[ii:ii + indexLen]]

            newLine = []
            for vv in ii0:
                if mat is not None:
                    _vec = [indArray.vertices[vv * 2], indArray.vertices[vv * 2 + 1], 0.0, 1.0]
                    _vec = mat.dot(_vec)
                    if ratioLine:
                        newLine.extend(self._scaleRatioToWindow(_vec[0:2]))
                    else:
                        newLine.extend(_vec[0:2])

                else:
                    if ratioLine:
                        # convert ratio to axis coordinates
                        # newLine.extend([self._scaleRatioToWindow(indArray.vertices[vv * 2], (self._axisR - self._axisL), self._axisL),
                        #                 self._scaleRatioToWindow(indArray.vertices[vv * 2 + 1], (self._axisT - self._axisB), self._axisB)])

                        newLine.extend(self._scaleRatioToWindow(indArray.vertices[vv * 2:vv * 2 + 2]))
                    else:
                        newLine.extend([indArray.vertices[vv * 2], indArray.vertices[vv * 2 + 1]])

            _alias = 1.0
            if alias is not None and indArray.attribs is not None and indArray.attribs.size != 0:
                if abs(indArray.attribs[ii0[0]] - alias) > 0.5:
                    _alias = self.params[GLALIASSHADE] / 100.0
            colour = (setColour or colors.Color(*indArray.colors[ii0[0] * 4:ii0[0] * 4 + 3], alpha=_alias * alphaClip(indArray.colors[ii0[0] * 4 + 3])))
            colourPath = self._colourID(name, colour)  # 'spectrumView%s%s%s%s%s' % (name,
            # colour.red, colour.green, colour.blue, colour.alpha)

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

            newLine = self.lineVisible(self._parent, newLine, x=_x, y=_y, width=_width, height=_height)
            if newLine:
                colourGroups[colourPath][PDFLINES].append(newLine)

        # override so that each element is a new group
        if splitGroups:
            self._appendGroup(drawing=self._mainPlot, colourGroups=colourGroups, name=name)

        if setColour is not None:
            return self._colourID(name, setColour)

    def _appendIndexLineGroupFill(self, indArray=None, listView=None, colourGroups=None, plotDim=None, name=None, mat=None,
                                  fillMode=None, splitGroups=False, lineWidth=0.5):
        for spectrumView in self._ordering:
            if spectrumView.isDeleted:
                continue
            specSettings = self._parent._spectrumSettings[spectrumView]
            # get the transformation matrix from the spectrumView
            mat = np.transpose(self._parent._spectrumSettings[spectrumView][SPECTRUM_MATRIX].reshape((4, 4)))

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
                                               mat=mat,
                                               fillMode=fillMode,
                                               splitGroups=splitGroups,
                                               lineWidth=lineWidth)

    def _appendGroup(self, drawing: Drawing = None, colourGroups: dict = None, name: str = None):
        """
        Append a group of polylines to the current drawing object
        :param drawing - drawing to append groups to
        :param colourGroups - OrderedDict of polylines
        :param name - name for the group
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
                elif len(ll) > 4:
                    pl.moveTo(ll[0], ll[1])
                    for vv in range(2, len(ll), 2):
                        try:
                            pl.lineTo(ll[vv], ll[vv + 1])
                        except Exception as es:
                            pass

                    if PDFCLOSEPATH not in colourItem or (PDFCLOSEPATH in colourItem and colourItem[PDFCLOSEPATH] == True):
                        pl.closePath()
            gr.add(pl)
        drawing.add(gr, name=name)

    def between(self, val, l, r):
        return (l - val) * (r - val) <= 0

    def pointVisible(self, _parent, lineList, x=0.0, y=0.0, width=0.0, height=0.0):
        """return true if the line has visible endpoints
        """
        axisL, axisR, axisT, axisB = self._axisL, self._axisR, self._axisT, self._axisB

        if (self.between(lineList[0], axisL, axisR) and
                (self.between(lineList[1], axisT, axisB))):
            lineList[0] = x + width * (lineList[0] - axisL) / (axisR - axisL)
            lineList[1] = y + height * (lineList[1] - axisB) / (axisT - axisB)
            return True

    def lineVisible(self, _parent, lineList, x=0.0, y=0.0, width=0.0, height=0.0, checkIntegral=False):
        """return the list of visible lines
        """
        # make into a list of tuples
        newList = []
        newLine = [[lineList[ll], lineList[ll + 1]] for ll in range(0, len(lineList), 2)]
        if len(newLine) > 2:
            newList = self.clipPoly(_parent, newLine)
        elif len(newLine) == 2:
            newList = self.clipLine(_parent, newLine)

        try:
            if newList:
                axisL, axisR, axisT, axisB = self._axisL, self._axisR, self._axisT, self._axisB

                newList = [pp for outPoint in newList for pp in (x + width * (outPoint[0] - axisL) / (axisR - axisL),
                                                                 y + height * (outPoint[1] - axisB) / (axisT - axisB))]
        except Exception as es:
            pass

        return newList

    def clipPoly(self, _parent, subjectPolygon):
        """Apply Sutherland-Hodgman algorithm for clipping polygons
        """
        axisL, axisR, axisT, axisB = self._axisL, self._axisR, self._axisT, self._axisB

        if self._parent.INVERTXAXIS != self._parent.INVERTYAXIS:
            clipPolygon = [[axisL, axisB],
                           [axisL, axisT],
                           [axisR, axisT],
                           [axisR, axisB]]
        else:
            clipPolygon = [[axisL, axisB],
                           [axisR, axisB],
                           [axisR, axisT],
                           [axisL, axisT]]

        def inside(p):
            return (cp2[0] - cp1[0]) * (p[1] - cp1[1]) > (cp2[1] - cp1[1]) * (p[0] - cp1[0])

        def get_intersect():
            """Returns the point of intersection of the lines passing through a2,a1 and b2,b1.
            """
            pp = np.vstack([s, e, cp1, cp2])  # s for stacked

            h = np.hstack((pp, np.ones((4, 1))))  # h for homogeneous
            l1 = np.cross(h[0], h[1])  # get first line
            l2 = np.cross(h[2], h[3])  # get second line
            x, y, z = np.cross(l1, l2)  # point of intersection
            if z == 0:  # lines are parallel
                return (float('inf'), float('inf'))
            return (x / z, y / z)

        outputList = subjectPolygon
        cLen = len(clipPolygon)
        cp1 = clipPolygon[cLen - 1]

        for clipVertex in clipPolygon:
            cp2 = clipVertex
            inputList = outputList
            outputList = []
            if not inputList:
                break

            ilLen = len(inputList)
            s = inputList[ilLen - 1]

            for e in inputList:
                if inside(e):
                    if not inside(s):
                        outputList.append(get_intersect())
                    outputList.append(e)
                elif inside(s):
                    outputList.append(get_intersect())
                s = e
            cp1 = cp2
        return outputList

    def clipLine(self, _parent, subjectPolygon):
        """Apply Sutherland-Hodgman algorithm for clipping polygons
        """
        axisL, axisR, axisT, axisB = self._axisL, self._axisR, self._axisT, self._axisB

        if self._parent.INVERTXAXIS != self._parent.INVERTYAXIS:
            clipPolygon = [[axisL, axisB],
                           [axisL, axisT],
                           [axisR, axisT],
                           [axisR, axisB]]
        else:
            clipPolygon = [[axisL, axisB],
                           [axisR, axisB],
                           [axisR, axisT],
                           [axisL, axisT]]

        def inside(p):
            return (cp2[0] - cp1[0]) * (p[1] - cp1[1]) > (cp2[1] - cp1[1]) * (p[0] - cp1[0])

        def get_intersect():
            """Returns the point of intersection of the lines passing through a2,a1 and b2,b1.
            """
            pp = np.vstack([s, e, cp1, cp2])  # s for stacked

            h = np.hstack((pp, np.ones((4, 1))))  # h for homogeneous
            l1 = np.cross(h[0], h[1])  # get first line
            l2 = np.cross(h[2], h[3])  # get second line
            x, y, z = np.cross(l1, l2)  # point of intersection
            if z == 0:  # lines are parallel
                return (float('inf'), float('inf'))
            return (x / z, y / z)

        outputList = subjectPolygon
        cLen = len(clipPolygon)
        cp1 = clipPolygon[cLen - 1]

        for clipVertex in clipPolygon:
            cp2 = clipVertex
            inputList = outputList
            outputList = []
            if not inputList:
                break

            ilLen = len(inputList)
            s = inputList[ilLen - 1]

            for e in inputList:
                if inside(e):
                    if not inside(s):
                        outputList.append(get_intersect())
                    outputList.append(e)
                elif inside(s):
                    outputList.append(get_intersect())
                s = e
            cp1 = cp2
        return outputList

    def lineFit(self, _parent, lineList, x=0.0, y=0.0, width=0.0, height=0.0, checkIntegral=False):
        axisL, axisR, axisT, axisB = self._axisL, self._axisR, self._axisT, self._axisB

        for pp in range(0, len(lineList), 2):
            if (self.between(lineList[pp], axisL, axisR) and
                    (self.between(lineList[pp + 1], axisT, axisB) or checkIntegral)):
                fit = True
                break
        else:
            fit = False

        for pp in range(0, len(lineList), 2):
            lineList[pp] = x + width * (lineList[pp] - axisL) / (axisR - axisL)
            lineList[pp + 1] = y + height * (lineList[pp + 1] - axisB) / (axisT - axisB)
        return fit


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

    fred = Clipped_Flowable()
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
