"""
A macro for creating plots of R1, R2 and NOE  isotropic analysis results for GB1.
Note. This macro is for demonstration purpose only.
It uses the original LZ model from Model-Free which is wrong for the current example of GB1.

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
__dateModified__ = "$dateModified: 2023-02-20 13:04:21 +0000 (Mon, February 20, 2023) $"
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

NOE_limitExclusion = 0.65
spectrometerFrequency=600.13

## Some Graphics Settings
titlePdf  = 'Anisotropy and Chemical Exchange Determination of GB1'
figureTitleFontSize = 8
showInteractivePlot = False # True if you want the plot to popup as a new windows, to allow the zooming and panning of the figure.
barColour='black'
barErrorColour='red'
barErrorLW = 1
barErrorCapsize=2
barErrorCapthick=0.5
fontTitleSize = 6
fontXSize = 4
fontYSize =  4
labelMajorSize=4
labelMinorSize=3
titleColor = 'blue'
hspace= 1
scatterColor = 'navy'
scatterColorError = 'darkred'
scatterExcludedByNOEColor = 'orange'
scatterSize = 3
scatterErrorLinewidth=0.1
scatterErrorCapSize=0.8
TrimmedLineColour = 'black'
scatterFontSize = 5

# exporting to pdf: Default save to same location and name.pdf as this macro
#  alternatively, provide a full valid path
exportingFilePath = None

############################################################
##################   End User Settings     ########################
############################################################

import numpy as np
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.framework.lib.experimentAnalysis.spectralDensityLib as sdl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.ticker import MultipleLocator
from ccpn.ui.gui.widgets.DrawSS import plotSS
import  ccpn.ui.gui.modules.experimentAnalysis._macrosLib as macrosLib


def _plotIsotropicAnalysisPage1(pdf):
    #  S2, Te, Tm, Rex
    fig = plt.figure(dpi=300)
    fig.suptitle('Isotropic Analysis Results', fontsize=10)
    axSe = plt.subplot(411)
    axTe = plt.subplot(412)
    axRex = plt.subplot(413)
    axss = fig.add_subplot(414)
    plotSS(axss, xSequence, sequence, ss_sequence=ss_sequence, startSequenceCode=startSequenceCode, fontsize=5,
           showSequenceNumber=False, )

    axSe.bar(x, S2, yerr=None, color=barColour, ecolor=barErrorColour, error_kw=dict(lw=barErrorLW, capsize=barErrorCapsize, capthick=barErrorCapthick))
    axTe.bar(x, TE, yerr=None, color=barColour, ecolor=barErrorColour, error_kw=dict(lw=barErrorLW, capsize=barErrorCapsize, capthick=barErrorCapthick))
    axRex.bar(x, REX, yerr=None, color=barColour, ecolor=barErrorColour, error_kw=dict(lw=barErrorLW, capsize=barErrorCapsize, capthick=barErrorCapthick))

    axSe.set_ylim(ymin=0, ymax=1)
    axTe.set_ylim(ymin=0)
    axRex.set_ylim(ymin=0)

    axSe.set_title('$S^2$',  fontsize=fontTitleSize, color=titleColor)
    axTe.set_title('Te',  fontsize=fontTitleSize, color='blue')
    axRex.set_title('Rex',  fontsize=fontTitleSize, color=titleColor)

    axSe.set_ylabel(f'$S^2$', fontsize=fontYSize)
    axTe.set_ylabel(f'Te  (ps)', fontsize=fontYSize)
    axRex.set_ylabel(f'Rex', fontsize=fontYSize)

    ml = MultipleLocator(1)
    for ax in [axss, axSe, axTe, axRex]:
        ax.spines[['right', 'top']].set_visible(False)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(ml)
        ax.tick_params(axis='both', which='major', labelsize=labelMajorSize)
        ax.tick_params(axis='both', which='minor', labelsize=labelMinorSize)
        ax.yaxis.get_offset_text().set_x(-0.02)
        ax.yaxis.get_offset_text().set_size(5)
        ax.yaxis.set_label_coords(-0.05, 0.5)  # align the labels to vcenter and middle

    axss.get_shared_x_axes().join(axss, axSe, axTe, axRex)
    axRex.set_xlabel('Residue Number', fontsize=fontXSize, )
    plt.tight_layout()
    plt.subplots_adjust(hspace=hspace)
    bestGct = otherAnalysis.TM.values[0]
    plt.figtext(0.5, 0.01, f'Global Molecular Tumbling CorrelationTime Tm: {round(bestGct, 3)} ns',
                ha="center", fontsize=6,)

    pdf.savefig()
    return fig

###################      start inline macro       #####################

## data preparation
## get the various values  and perform the needed calculations
dataTable = macrosLib._getDataTableForMacro(dataTableName)
data =  dataTable.data
x = data[sv.NMRRESIDUECODE]
x = x.astype(int)
x = x.values
startSequenceCode = x[0]
endSequenceCode = startSequenceCode + len(ss_sequence)
xSequence = np.arange(startSequenceCode, endSequenceCode)
R1 = data[sv.R1].values
R2 = data[sv.R2].values
NOE = data[sv.HETNOE_VALUE].values
R1_ERR = data[sv.R1_ERR]
R2_ERR  = data[sv.R2_ERR]
NOE_ERR = data[sv.HETNOE_VALUE_ERR]

otherAnalysis, meanAnalysis = sdl._fitIsotropicModelFromT1T2NOE(data, spectrometerFrequency=spectrometerFrequency)
S2 = otherAnalysis[sv.S2].values
TE = otherAnalysis[sv.TE].values
REX = otherAnalysis[sv.REX].values

##  init the plot and save to pdf
filePath = macrosLib._getExportingPath(__file__, exportingFilePath)

with PdfPages(filePath) as pdf:
    fig1 = _plotIsotropicAnalysisPage1(pdf)
    info(f'Report saved in {filePath}')

if showInteractivePlot:
    plt.show()
else:
    plt.close(fig1)

application._showHtmlFile("Show Plots", filePath)

###################      end macro        #########################


