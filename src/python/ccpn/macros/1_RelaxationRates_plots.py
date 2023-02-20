"""
A macro for creating plots of  R1 R2 NOE rates as a function of the sequence code

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
__dateModified__ = "$dateModified: 2023-02-20 12:00:40 +0000 (Mon, February 20, 2023) $"
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

## Some Graphics Settings

titlePdf  = 'GB1 Relaxation Rates Results'
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
figureTitleFontSize = 10

# exporting to pdf: Default save to same location and name.pdf as this macro
#  alternatively, provide a full valid path
exportingFilePath = None

############################################################
##################   End User Settings     ########################
############################################################

import numpy as np
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from ccpn.ui.gui.widgets.DrawSS import plotSS
import  ccpn.ui.gui.modules.experimentAnalysis._macrosLib as macrosLib


def _plotRates(pdf):
    """ Plot the  SS -  R1  - R2 - NOE """
    fig, axes  = macrosLib._makeFigureLayoutWithOneColumn(4, height_ratios=[2, 2, 2, 1])
    axR1, axR2, axNOE, axss = axes

    # plot the data
    axR1.bar(x, R1, yerr=R1_ERR, color=barColour, ecolor=barErrorColour, error_kw=dict(lw=barErrorLW, capsize=barErrorCapsize, capthick=barErrorCapthick))
    axR2.bar(x, R2, yerr=R2_ERR, color=barColour, ecolor=barErrorColour, error_kw=dict(lw=barErrorLW, capsize=barErrorCapsize, capthick=barErrorCapthick))
    axNOE.bar(x, NOE, yerr=NOE_ERR, color=barColour, ecolor=barErrorColour, error_kw=dict(lw=barErrorLW, capsize=barErrorCapsize, capthick=barErrorCapthick))
    plotSS(axss, xSequence, sequence, ss_sequence=ss_sequence, showSequenceNumber=False, startSequenceCode=startSequenceCode, fontsize=labelMinorSize, )

    # set the various labels
    axR1.set_title('R1', fontsize=fontTitleSize, color=titleColor)
    axR2.set_title('R2',  fontsize=fontTitleSize, color=titleColor)
    axNOE.set_title('HetNOE', fontsize=fontTitleSize, color=titleColor)
    axR1.set_ylabel('R$_{1}$ (sec$^{-1}$)', fontsize=fontYSize)
    axR2.set_ylabel('R$_{2}$ (sec$^{-1}$)', fontsize=fontYSize)
    axNOE.set_ylabel('het-NOE ratio', fontsize=fontYSize)
    axNOE.set_xlabel('Residue Number', fontsize=fontXSize, )

    # set the various axis settings
    macrosLib._setJoinedX(axss, [axR1, axR2, axNOE])
    for ax in [axss, axR1, axR2, axNOE]:
        macrosLib._setRightTopSpinesOff(ax)
        macrosLib._setXTicks(ax, labelMajorSize, labelMinorSize)
        macrosLib._setYLabelOffset(ax, -0.05, 0.5)
        if ax != axss:
            macrosLib. _setCommonYLim(ax,  ax.get_ylim())
    if np.all(NOE.astype(float)>0): 
        axNOE.set_ylim([0, 1])
    else:
        axNOE.set_ylim([-1, 1])
    fig.suptitle(titlePdf, fontsize=figureTitleFontSize)
    plt.tight_layout()
    plt.subplots_adjust(hspace=hspace)
    plt.subplots_adjust(top=0.85,) # space title and plots
    pdf.savefig()
    return fig

###################      start inline macro       #####################

## get the data
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

##  init the plot and save to pdf
filePath = macrosLib._getExportingPath(__file__, exportingFilePath)
with PdfPages(filePath) as pdf:
    fig1 = _plotRates(pdf)
    info(f'Report saved in {filePath}')

if showInteractivePlot:
    plt.show()
else:
    plt.close(fig1)

application._showHtmlFile("Show Plots", filePath)

# if interactive plot
# the figure has to be closed manually after  finished with the popup plot  or will stay hanging around in memory!  Cannot close here or you don't see the interactive plot!



