"""
A macro to plot  clusters of  T2/T1  relaxation  analysis results.

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-02-14 16:55:18 +0000 (Tue, February 14, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-02-03 10:04:03 +0000 (Fri, February 03, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf
import pandas as pd
import matplotlib.pyplot as plt
import math
import time
import datetime
from matplotlib.backends.backend_pdf import PdfPages
from ccpn.util.Logging import getLogger
from matplotlib.ticker import MultipleLocator
from ccpn.ui.gui.widgets.DrawSS import createBlocksFromSequence, plotSS
from ccpn.util.floatUtils import fExp, fMan
import ccpn.framework.lib.experimentAnalysis.experimentConstants as constants
import ccpn.framework.lib.experimentAnalysis.spectralDensityLib as sdl
from math import atan2,degrees


####### User's Settings  ###################
fileName = 'RelaxClustersAnalysisResults'
filePath = f'/Users/luca/Documents/V3-testings/{fileName}'

####### S2_contours
##  Order Parameter Lines
S2_contours_minValue = 0.3
S2_contours_maxValue = 1.0
S2_contours_stepValue = 0.1

##  Tm  Contours Lines (rotational correlation Time Lines)
Tm_line_minValue = 5.0
Tm_line_maxValue = 14.0
Tm_line_stepValue = 1.0

##  Physical  Params
SPECTROMETERFREQUENCY = 600.130
NH_bondLenght = 1.0150 # Armstrong
InternalCorrelationTimeTe = itc =  50.0
CSA15N = -160.0 # ppm

##  GUI - T1 vs T2 scatter  X-Y limits
Cluster_maxDifferenceMs = 20.0
Cluster_minSize  = 5.0
Cluster_MinX_T1 = 300
Cluster_MaxX_T1 = 1000
Cluster_MinY_T2 = 20
Cluster_MaxY_T2 = 700

ss_sequence = 'BBBBBCCCCBBBBBBCCCCHHHHHHHHHHHHHHCCCCCBBBBCCCCCBBBBBC'
sequence = 'KLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDAATKTFTVTE'

# graphics
fontTitleSize = 8
fontXSize = 6
fontYSize = 6
scatterFontSize = 5
labelMajorSize=6
labelMinorSize=5
titleColor = 'blue'
hspace= 0.5

CLUSTER_COLORS = (
                  '#800000',
                  '#000080',
                  '#008000',
                  '#808000',
                  '#800080',
                  '#008080',
                  '#808080',
                  '#000000',
                  '#804000',
                  '#004080'
                )

CLUSTER_SYMBOLS = ('circle', 'square', 'triangle')


RSDMResultsDataTable = get('DT:RSDM_results')


data =  RSDMResultsDataTable.data
x = data[sv.NMRRESIDUECODE]
x = x.astype(int)
x = x.values

R1 = data[sv.R1].values
R2 = data[sv.R2].values
NOE = data[sv.HETNOE_VALUE]


def findNearestIndex(array, value):
    idx = (np.abs(array - value)).argmin()
    return idx


def labelLine(line,x,label=None,align=True,**kwargs):
    ax = line.axes
    xdata = line.get_xdata()
    ydata = line.get_ydata()
    if (x < xdata[0]) or (x > xdata[-1]):
        print('x label location is outside data range!')
        return
    #Find corresponding y co-ordinate and angle of the line
    ip = 1
    for i in range(len(xdata)):
        if x < xdata[i]:
            ip = i
            break
    y = ydata[ip-1] + (ydata[ip]-ydata[ip-1])*(x-xdata[ip-1])/(xdata[ip]-xdata[ip-1])
    if not label:
        label = line.get_label()
    if align:
        #Compute the slope
        dx = xdata[ip] - xdata[ip-1]
        dy = ydata[ip] - ydata[ip-1]
        ang = degrees(atan2(dy,dx))
        #Transform to screen co-ordinates
        pt = np.array([x,y]).reshape((1,2))
        trans_angle = ax.transData.transform_angles(np.array((ang,)),pt)[0]
    else:
        trans_angle = 0
    if 'color' not in kwargs:
        kwargs['color'] = line.get_color()
    if ('horizontalalignment' not in kwargs) and ('ha' not in kwargs):
        kwargs['ha'] = 'center'
    if ('verticalalignment' not in kwargs) and ('va' not in kwargs):
        kwargs['va'] = 'center'
    if 'backgroundcolor' not in kwargs:
        kwargs['backgroundcolor'] = ax.get_facecolor()
    if 'clip_on' not in kwargs:
        kwargs['clip_on'] = True
    if 'zorder' not in kwargs:
        kwargs['zorder'] = 2.5
    color = kwargs.get('color', )
    fontsize = kwargs.get('fontsize', 5)
    ax.text(x, y, label, rotation=0, color=color, fontsize=fontsize, )
    # ax.text(x,y,label,rotation=trans_angle,**kwargs)

def labelLines(lines, align=True,xvals=None,**kwargs):
    ax = lines[0].axes
    labLines = []
    labels = []
    for line in lines:
        label = line.get_label()
        if "_line" not in label:
            labLines.append(line)
            label = label.lstrip('_')
            labels.append(label)
    if xvals is None:
        xmin,xmax = ax.get_xlim()
        xvals = np.linspace(xmin,xmax,len(labLines)+2)[1:-1]
    for line,x,label in zip(labLines,xvals,labels):
        labelLine(line,x,label,align,**kwargs)


def _plotClusters(pdf, xMaxLim=800):
    fig = plt.figure(dpi=300)
    fig.suptitle(' R2 vs R1 Isotropic Analysis Scatter', fontsize=10)

    ax = plt.subplot(111)
    ## R1 vs R2
    T1 = 1/R1*1e3
    T2 = 1 / R2*1e3
    ax.scatter(T1, T2, s=1, color='black', )
    for i, txt in enumerate(x):
        ax.annotate(str(txt), (T1[i], T2[i]), fontsize=2)
    plt.subplots_adjust(hspace=hspace)
    ax.set_title('T2 vs T1',  fontsize=fontTitleSize, color=titleColor)
    ax.set_xlabel('T$_{1} (ms)$', fontsize=fontYSize, )
    ax.set_ylabel('T$_{2} (ms)$', fontsize=fontYSize)
    ax.spines[['right', 'top']].set_visible(False)
    ax.tick_params(axis='both', which='major', labelsize=labelMajorSize)
    ax.tick_params(axis='both', which='minor', labelsize=labelMinorSize)
    ax.yaxis.get_offset_text().set_x(-0.02)
    ax.yaxis.get_offset_text().set_size(5)
    ax.xaxis.get_offset_text().set_size(5)
    plt.tight_layout()

    rctLines, s2Lines = sdl.calculateSpectralDensityContourLines(minRct = 3.0,
                                         maxRct=8, stepRct=0.5)
    for i in rctLines:
        n, lines = i
        rctArray = np.array(lines)
        rct = rctArray.transpose()
        xRct, yRct = rct
        n = float(n)
        if n.is_integer():
            ax.plot(xRct, yRct, 'blue', linewidth=0.5, label='_'+str(round(n, 2)))
        else:
            ax.plot(xRct, yRct, 'blue', linewidth=0.2, label='_' + str(round(n, 2)))
        # add labels
    labelLines(plt.gca().get_lines(), xvals=[xMaxLim+10]*len(rctLines), color='blue', align=False, clip_on=False, fontsize=4, zorder=None)

    for j in s2Lines:
        n, lines = j
        s2Array = np.array(lines)
        s2L = s2Array.transpose()
        xSe, ySe = s2L
        ax.plot(xSe, ySe, 'r',  linewidth=0.5)
        # add labels
        ixMinxSe = findNearestIndex(xSe, np.min(xSe))
        lXse = xSe[ixMinxSe]
        lYse = ySe[ixMinxSe]
        ax.annotate(str(round(n, 2)), (lXse, lYse), color='r', fontsize=5)
    ax.plot([],[],  'blue', linewidth=0.5, label='$Tm$ rotational correlation time') # just a  placeholder
    ax.plot([],[],  'r', linewidth=0.5, label='$S^2$ order parameter')

    ax.set_xlim(300, xMaxLim+10)
    ax.set_ylim(0, 500)
    ax.legend(prop={'size': 6})

    pdf.savefig()
    plt.close()


# init pdf
with PdfPages(f'{filePath}.pdf') as pdf:
    _plotClusters(pdf)




