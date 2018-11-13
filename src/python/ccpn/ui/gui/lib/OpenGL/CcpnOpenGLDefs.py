"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

SPECTRUM_STACKEDMATRIX = 'stackedMatrix'
SPECTRUM_MATRIX = 'spectrumMatrix'
SPECTRUM_MAXXALIAS = 'maxXAlias'
SPECTRUM_MINXALIAS = 'minXAlias'
SPECTRUM_MAXYALIAS = 'maxYAlias'
SPECTRUM_MINYALIAS = 'minYAlias'
SPECTRUM_DXAF = 'dxAF'
SPECTRUM_DYAF = 'dyAF'
SPECTRUM_XSCALE = 'xScale'
SPECTRUM_YSCALE = 'yScale'

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

GLLINE_STYLES = {
    'solid': 0xFFFF,
    'dashed': 0xF0F0,
    'dotted': 0xAAAA
}

GLLINE_STYLES_ARRAY = {
    'solid': None,
    'dashed': [5, 5],
    'dotted': [1, 1]
}

GLLINETYPE = 'line'
GLREGIONTYPE = 'region'

AXISLIMITS = [-1.0e12, 1.0e12]
INVERTED_AXISLIMITS = [1.0e12, -1.0e12]
RANGELIMITS = [1.0e12, 0.0]
RANGEMINSCALE = 1.0


LENPID = 8
LENVERTICES = 2
LENINDICES = 1
LENCOLORS = 4
LENTEXCOORDS = 2
LENATTRIBS = 4
LENOFFSETS = 4

FADE_FACTOR = 0.25

GLFILENAME = 'filename'
GLSPECTRUMDISPLAY = 'spectrumDisplay'
GLSTRIP = 'strip'
GLWIDGET = 'glWidget'
GLPRINTTYPE = 'printType'
GLPAGETYPE = 'pageType'
GLSELECTEDPIDS = 'selectedPids'
GLPEAKSYMBOLS = 'peakSymbols'
GLPEAKLABELS = 'peakLabels'
GLINTEGRALSYMBOLS = 'integralSymbols'
GLINTEGRALLABELS = 'integralLabels'
GLMULTIPLETSYMBOLS = 'multipletSymbols'
GLMULTIPLETLABELS = 'multipletLabels'
GLGRIDLINES = 'Grid Lines'
GLAXISLINES = 'Axis Lines'
GLAXISMARKS = 'Axis Marks'
GLAXISLABELS = 'Axis Labels'
GLSPECTRUMCONTOURS = 'Spectrum Contours'
GLSPECTRUMBORDERS = 'Spectrum Borders'
GLMARKLINES = 'Mark Lines'
GLMARKLABELS = 'Mark Labels'
GLTRACES = 'Traces'
GLSHOWSPECTRAONPHASE = 'Spectra on Phasing'
GLOTHERLINES = 'Other Lines'
GLSTRIPLABELLING = 'Strip Labelling'
GLREGIONS = 'regions'
GLPLOTBORDER = 'plotBorder'
GLFOREGROUND = 'foregroundColour'
GLBACKGROUND = 'backgroundColour'
GLBASETHICKNESS = 'baseThickness'
GLSYMBOLTHICKNESS = 'symbolThickness'

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