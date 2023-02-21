"""
A macro for creating a scatter plot of  T1 vs T2  with S2 and Tc as contouring lines

This macro requires a  dataset  created after performing  the Reduced Spectral density Mapping calculation model
on the Relaxation Analysis Module (alpha)
Which is a dataset that contains a table with the following (mandatory) columns:
    -  nmrResidueCode
    -  R1 and  R1_err
    - R2 and  R2_err
    - HetNoe and  HetNoe_err

Macro created for Analysis Version 3.1.1

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
__dateModified__ = "$dateModified: 2023-02-21 20:12:09 +0000 (Tue, February 21, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-02-03 10:04:03 +0000 (Fri, February 03, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================


############################################################
#####################    User Settings      #######################
############################################################

dataTableName = 'RSDM_results'

##  demo sequence for the GB1 protein . Replace with an empty str if not available, e.g.: sequence  = ''
sequence  = 'KLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDAATKTFTVTE'
##  secondary structure  for the above sequence  using the DSSP nomenclature.  Replace with an empty str if not available. e.g.: ss_sequence  = ''
ss_sequence   =  'BBBBBCCCCBBBBBBCCCCHHHHHHHHHHHHHHCCCCCBBBBCCCCCBBBBBC'


####### S2_contours
##  Order Parameter Lines
S2_contours_minValue = 0.3
S2_contours_maxValue = 1.0
S2_contours_stepValue = 0.1

##  Tm  Contours Lines (rotational correlation Time Lines)
Tm_line_minValue = 3
Tm_line_maxValue = 8
Tm_line_stepValue = 0.5

##  Physical  Params
spectrometerFrequency=600.130
NH_bondLenght = 1.0150 # Armstrong
InternalCorrelationTimeTe = itc =  50.0
CSA15N = -160.0 # ppm
rctScalingFactor = 1e-9
ictScalingFactor = 1e-12

## Some Graphics Settings

titlePdf  = 'GB1 Relaxation Rates with Isotropic-Model Contouring Lines '
showInteractivePlot = False # True if you want the plot to popup as a new windows, to allow the zooming and panning of the figure.

fontTitleSize = 6
fontXSize = 4
fontYSize =  4
labelMajorSize=4
labelMinorSize=3
titleColor = 'blue'
hspace= 1
figureTitleFontSize = 10

rctLineColour =  'blue'
s2LineColour =  'red'

# exporting to pdf: Default save to same location and name.pdf as this macro
#  alternatively, provide a full valid path
outputPath = None

############################################################
##################   End User Settings     ########################
############################################################


import numpy as np
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import ccpn.framework.lib.experimentAnalysis.spectralDensityLib as sdl
import ccpn.macros.relaxation._macrosLib as macrosLib
from ccpn.util.Common import percentage

def _plotClusters(pdf, xMaxLim=800):
    fig = plt.figure(dpi=300)
    fig.suptitle(titlePdf, fontsize=fontTitleSize)

    ax = plt.subplot(111)
    ## R1 vs R2
    T1 = 1/R1*1e3
    T2 = 1 / R2*1e3
    ax.scatter(T1, T2, s=1, color='black', )
    for i, txt in enumerate(x):
        extraY = percentage(0.5, T2[i])
        yPos = T2[i] + extraY
        extraX = percentage(0.5, T1[i])
        xPos = T1[i] + extraX
        ax.annotate(str(txt), xy=(T1[i], T2[i]), xytext=(xPos, yPos), fontsize=3.5, arrowprops=dict(facecolor='grey',arrowstyle="-",lw=0.3  ))

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

    for i in rctLines:
        n, lines = i
        rctArray = np.array(lines)
        rct = rctArray.transpose()
        xRct, yRct = rct
        n = float(n)
        if n.is_integer():
            ax.plot(xRct, yRct, rctLineColour, linewidth=0.5, label='_'+str(round(n, 2)))
        else:
            ax.plot(xRct, yRct, rctLineColour, linewidth=0.2, label='_' + str(round(n, 2)))
        # add labels
    macrosLib.labelLines(plt.gca().get_lines(), xvals=[xMaxLim+10]*len(rctLines), color=rctLineColour, align=False, clip_on=False, fontsize=4, zorder=None)

    for j in s2Lines:
        n, lines = j
        s2Array = np.array(lines)
        s2L = s2Array.transpose()
        xSe, ySe = s2L
        ax.plot(xSe, ySe, 'r',  linewidth=0.5)
        # add labels
        ixMinxSe = macrosLib.findNearestIndex(xSe, np.min(xSe))
        lXse = xSe[ixMinxSe]
        lYse = ySe[ixMinxSe]
        ax.annotate(str(round(n, 2)), (lXse, lYse), color=s2LineColour, fontsize=5)
    ax.plot([],[], rctLineColour, linewidth=0.5, label='$T_m$ rotational correlation time') # just a  placeholder
    ax.plot([],[],  s2LineColour, linewidth=0.5, label='$S^2$ order parameter')

    ax.set_xlim(300, xMaxLim+10)
    ax.set_ylim(0, 500)
    ax.legend(prop={'size': 6})

    pdf.savefig()
    return fig

###################      start inline macro       #####################
args = macrosLib.getArgs().parse_args()
globals().update(args.__dict__)

#### Data #####
dataTable = macrosLib._getDataTableForMacro(dataTableName)
data =  dataTable.data
x = data[sv.NMRRESIDUECODE]
x = x.astype(int)
x = x.values

R1 = data[sv.R1].values
R2 = data[sv.R2].values
NOE = data[sv.HETNOE_VALUE]

rctLines, s2Lines = sdl.calculateSpectralDensityContourLines(
                                                            spectrometerFrequency=spectrometerFrequency,
                                                            lenNh=NH_bondLenght,
                                                            ict=InternalCorrelationTimeTe,
                                                            csaN=CSA15N,
                                                            minS2=S2_contours_minValue,
                                                            maxS2=S2_contours_maxValue,
                                                            stepS2=S2_contours_stepValue,
                                                            rctScalingFactor=rctScalingFactor,
                                                            ictScalingFactor=ictScalingFactor,
                                                            minRct=Tm_line_minValue,
                                                            maxRct=Tm_line_maxValue,
                                                            stepRct=Tm_line_stepValue
                                                        )


filePath = macrosLib._getExportingPath(__file__, outputPath)
with PdfPages(filePath) as pdf:
    fig1 = _plotClusters(pdf)
    info(f'Report saved in {filePath}')

if showInteractivePlot:
    plt.show()
else:
    plt.close(fig1)



