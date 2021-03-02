"""
Module Documentation here
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
__dateModified__ = "$dateModified: 2021-03-02 15:00:01 +0000 (Tue, March 02, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 13:28:13 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from enum import Enum
from ccpn.util.LabelledEnum import LabelledEnum


SPECTRUM_STACKEDMATRIX = 'stackedMatrix'
SPECTRUM_STACKEDMATRIXOFFSET = 'stackedMatrixOffset'
SPECTRUM_MATRIX = 'spectrumMatrix'
SPECTRUM_MAXXALIAS = 'maxXAlias'
SPECTRUM_MINXALIAS = 'minXAlias'
SPECTRUM_MAXYALIAS = 'maxYAlias'
SPECTRUM_MINYALIAS = 'minYAlias'
SPECTRUM_DXAF = 'dxAF'
SPECTRUM_DYAF = 'dyAF'
SPECTRUM_XSCALE = 'xScale'
SPECTRUM_YSCALE = 'yScale'
SPECTRUM_POINTINDEX = 'pointIndex'
SPECTRUM_VALUEPERPOINT = 'valuePerPoint'
SPECTRUM_SPINNINGRATE = 'spinningRate'
SPECTRUM_REGIONBOUNDS = 'regionBounds'

MAINVIEW = 'mainView'
MAINVIEWFULLWIDTH = 'mainViewFullWidth'
MAINVIEWFULLHEIGHT = 'mainViewFullHeight'
RIGHTAXIS = 'rightAxis'
RIGHTAXISBAR = 'rightAxisBar'
FULLRIGHTAXIS = 'fullRightAxis'
FULLRIGHTAXISBAR = 'fullRightAxisBar'
BOTTOMAXIS = 'bottomAxis'
BOTTOMAXISBAR = 'bottomAxisBar'
FULLBOTTOMAXIS = 'fullBottomAxis'
FULLBOTTOMAXISBAR = 'fullBottomAxisBar'
FULLVIEW = 'fullView'
AXISCORNER = 'axisCorner'
BLANKVIEW = 'blankView'

GLLINE_STYLES = {
    'solid'       : 0xFFFF,
    'dashed'      : 0xF0F0,
    'short-dashed': 0xCCCC,
    'dotted'      : 0xAAAA
    }

GLLINE_STYLES_ARRAY = {
    'solid' : None,
    'dashed': [5, 5],
    'dotted': [1, 1]
    }

GLDEFAULTLINETHICKNESS = 1.0
GLLINETYPE = 'line'
GLREGIONTYPE = 'region'

AXISLIMITS = [-1.0e12, 1.0e12]
INVERTED_AXISLIMITS = [1.0e12, -1.0e12]
RANGELIMITS = [1.0e12, 0.0]
RANGEMINSCALE = 1.0

LENPID = 12
LENVERTICES = 2
LENINDICES = 1
LENTEXCOORDS = 2
LENATTRIBS = 4
LENOFFSETS = 4
LENSQ = 9
LENSQ2 = 2 * LENSQ
LENSQ4 = 4 * LENSQ
LENSQMULT = 17
LENSQ2MULT = 2 * LENSQMULT
LENSQ4MULT = 4 * LENSQMULT
POINTCOLOURS = 9
POINTCOLOURSMULT = LENSQMULT

DEFAULTCOLOUR = '#7f7f7f'
DEFAULTFADE = 0.3
OUTOFPLANEFADE = 1.0
INPLANEFADE = 1.0

# export to file settings
GLFILENAME = 'filename'
GLSPECTRUMDISPLAY = 'spectrumDisplay'
GLSTRIP = 'strip'
GLWIDGET = 'glWidget'
GLPRINTTYPE = 'printType'
GLPAGETYPE = 'pageType'
GLSELECTEDPIDS = 'selectedPids'

# check box items
GLPEAKSYMBOLS = 'Peak Symbols'
GLPEAKLABELS = 'Peak Labels'
GLINTEGRALSYMBOLS = 'Integral Symbols'
GLINTEGRALLABELS = 'Integral Labels'
GLMULTIPLETSYMBOLS = 'Multiplet Symbols'
GLMULTIPLETLABELS = 'Multiplet Labels'
GLGRIDLINES = 'Grid Lines'
GLDIAGONALLINE = 'Diagonal'
GLDIAGONALSIDEBANDS = 'SpinningRate SideBands'
GLAXISTITLES = 'Axis Titles'
GLAXISLINES = 'Axis Lines'
GLAXISMARKS = 'Axis Marks'
GLAXISMARKSINSIDE = 'Axis Marks Inside'
GLAXISLABELS = 'Axis Labels'
GLAXISUNITS = 'Axis Units'
GLSPECTRUMCONTOURS = 'Spectrum Contours'
GLSPECTRUMBORDERS = 'Spectrum Borders'
GLSPECTRUMLABELS = 'Spectrum Labels'
GLMARKLINES = 'Mark Lines'
GLMARKLABELS = 'Mark Labels'
GLCURSORS = 'Show Cursors'
GLTRACES = 'Traces'
GLACTIVETRACES = 'Active Traces'
GLSHOWSPECTRAONPHASE = 'Spectra on Phasing'
GLOTHERLINES = 'Other Lines'
GLSTRIPLABELLING = 'Strip Labelling'
GLREGIONS = 'Regions'
GLPLOTBORDER = 'Plot Border'

# export to file user settings
GLFOREGROUND = 'Foreground Colour'
GLBACKGROUND = 'Background Colour'
GLBASETHICKNESS = 'Base Thickness'
GLSYMBOLTHICKNESS = 'Symbol Thickness'
GLCONTOURTHICKNESS = 'Contour Thickness'
GLALIASENABLED = 'Alias Enabled'
GLALIASSHADE = 'Alias Shade'
GLSTRIPDIRECTION = 'Strip Direction'
GLSTRIPPADDING = 'Strip Padding'
GLEXPORTDPI = 'Image dpi'

AXISDRAWOFFSET = 0.001

GLFULLLIST = (GLPEAKSYMBOLS,
              GLPEAKLABELS,
              GLINTEGRALSYMBOLS,
              GLINTEGRALLABELS,
              GLMULTIPLETSYMBOLS,
              GLMULTIPLETLABELS,
              GLGRIDLINES,
              GLDIAGONALLINE,
              GLDIAGONALSIDEBANDS,
              GLAXISTITLES,
              # GLAXISLINES,
              GLAXISMARKS,
              # GLAXISMARKSINSIDE,
              GLAXISLABELS,
              GLAXISUNITS,
              GLSPECTRUMCONTOURS,
              GLSPECTRUMBORDERS,
              GLSPECTRUMLABELS,
              GLMARKLINES,
              GLMARKLABELS,
              GLCURSORS,
              GLTRACES,
              GLACTIVETRACES,
              GLSHOWSPECTRAONPHASE,
              GLOTHERLINES,
              GLSTRIPLABELLING,
              GLREGIONS,
              GLPLOTBORDER)

GLEXTENDEDLIST = (GLGRIDLINES,
                  GLDIAGONALLINE,
                  GLDIAGONALSIDEBANDS,
                  GLAXISTITLES,
                  # GLAXISLINES,
                  GLAXISMARKS,
                  # GLAXISMARKSINSIDE,
                  GLAXISLABELS,
                  GLAXISUNITS,
                  GLSPECTRUMCONTOURS,
                  GLSPECTRUMBORDERS,
                  GLSPECTRUMLABELS,
                  GLMARKLINES,
                  GLMARKLABELS,
                  GLCURSORS,
                  GLTRACES,
                  GLACTIVETRACES,
                  GLSHOWSPECTRAONPHASE,
                  GLOTHERLINES,
                  GLSTRIPLABELLING,
                  GLREGIONS,
                  GLPLOTBORDER)

LEFTBORDER = 1
RIGHTBORDER = 1
TOPBORDER = 1
BOTTOMBORDER = 1

TITLEXOFFSET = 1
TITLEYOFFSET = 1.2
AXISTEXTXOFFSET = 8
AXISTEXTYOFFSET = 7
MARKTEXTXOFFSET = 2
MARKTEXTYOFFSET = 2

AXISUNITSPPM = '[ppm]'
AXISUNITSHZ = '[Hz]'
AXISUNITSPOINTS = '[pnts]'
AXISUNITSINTENSITY = ''
XAXISUNITS = [AXISUNITSPPM, AXISUNITSHZ, AXISUNITSPOINTS]
YAXISUNITS = [AXISUNITSPPM, AXISUNITSHZ, AXISUNITSPOINTS]
YAXISUNITS1D = [AXISUNITSINTENSITY]
AXISXUNITS = 'xUnits'
AXISYUNITS = 'yUnits'
AXISASPECTRATIOMODE = 'aspectRatioMode'
AXISASPECTRATIOS = 'aspectRatios'

ANNOTATIONTYPES = 'annotationTypes'
SYMBOLTYPES = 'symbolTypes'
SYMBOLSIZE = 'symbolSize'
SYMBOLTHICKNESS = 'symbolThickness'
STRIPGRID = 'stripGrid'
STRIPCONTOURS = 'stripContours'
STRIPCURSOR = 'stripCursor'
STRIPDOUBLECURSOR = 'stripDoubleCursor'
SPECTRUMBORDERS = 'spectrumBorders'
DISPLAYTOOLBARS = 'displayToolbars'
GRIDVISIBLE = 'gridVisible'
CROSSHAIRVISIBLE = 'crosshairVisible'
DOUBLECROSSHAIRVISIBLE = 'doubleCrosshairVisible'
SIDEBANDSVISIBLE = 'sideBandsVisible'
ALIASENABLED = 'aliasEnabled'
ALIASSHADE = 'aliasShade'
STRINGSCALE = 0.7

PEAKLABEL_MINIMAL = 'peaklabelMinimal'
PEAKLABEL_SHORT = 'peaklabelShort'
PEAKLABEL_FULL = 'peaklabelFull'
PEAKLABEL_PID = 'peaklabelPid'
PEAKLABEL_ID = 'peaklabelId'

PEAKSYMBOL_CROSS = 'peakSymbolCross'
PEAKSYMBOL_LINEWIDTH = 'peakSymbolLineWidth'
PEAKSYMBOL_FILLEDLINEWIDTH = 'peakSymbolFilledLineWidth'
PEAKSYMBOL_PLUS = 'peakSymbolPlus'

LOCKNONE = 0
LOCKSCREEN = 1
LOCKX = 2
LOCKY = 4
LOCKLEFT = 8
LOCKRIGHT = 16
LOCKTOP = 32
LOCKBOTTOM = 64
LOCKAXIS = 128

LOCKEDSTRING = 'Locked'
FIXEDSTRING = 'Fixed'
VIEWPORTSATTRIB = 'viewports'


class PaintModes(Enum):
    PAINT_NONE = 0
    PAINT_ALL = 1
    PAINT_MOUSEONLY = 2


class AxisModes(LabelledEnum):
    AXIS_OFF = 0, 'Off'
    AXIS_DEFAULT = 1, 'Default'
    AXIS_FULLHEIGHT = 2, 'Full'


class CursorFrameCounterModes(LabelledEnum):
    CURSOR_DEFAULT = 0, 'Default'
    CURSOR_DRAWLAST = 1, 'DrawLast'
    CURSOR_DRAWNEXT = 2, 'DrawNext'
