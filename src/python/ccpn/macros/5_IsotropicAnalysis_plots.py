"""
A Demo report for relaxation isotropic analysis results.


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
__dateModified__ = "$dateModified: 2023-02-17 17:35:26 +0000 (Fri, February 17, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-02-03 10:04:03 +0000 (Fri, February 03, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================
import os.path

import numpy as np
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf
import ccpn.framework.lib.experimentAnalysis.spectralDensityLib as sdl
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

# #########

###################


exportingFileName = 'RelaxationIsotropicAnalysisResults'
exportingDirectoryPath = '/Users/luca/Documents/V3-testings/'

RSDMResultsDataTable = get('DT:RSDM_results')

if RSDMResultsDataTable is None:
    errorMess = 'Cannot display results. Ensure you have the RSDMResults dataTable in the project or you inserted the correct pid in the macro'
    raise RuntimeError(errorMess)

ss_sequence   =  'BBBBBCCCCBBBBBBCCCCHHHHHHHHHHHHHHCCCCCBBBBCCCCCBBBBBC'
sequence  = 'KLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDAATKTFTVTE'


data =  RSDMResultsDataTable.data
x = data[sv.NMRRESIDUECODE]
x = x.astype(int)
x = x.values
startSequenceCode = x[0]
endSequenceCode = startSequenceCode + len(ss_sequence)
startOffsetExtraXTicks = 3 # used to allign the ss to the plots
xSequence = np.arange(startSequenceCode, endSequenceCode)

R1 = data[sv.R1].values
R2 = data[sv.R2].values
NOE = data[sv.HETNOE_VALUE]

R1_ERR = data[sv.R1_ERR]
R2_ERR  = data[sv.R2_ERR]
NOE_ERR = data[sv.HETNOE_VALUE_ERR]


otherAnalysis, meanAnalysis = sdl._fitIsotropicModelFromT1T2NOE(data, spectrometerFrequency=600.130)
S2 = otherAnalysis[sv.S2].values
TE = otherAnalysis[sv.TE].values
REX = otherAnalysis[sv.REX].values

## lax labels
L_JWN = '$J(\omega_{N})$'
L_JWH = '$J(\omega_{H})$'
L_SR = '(sec/rad)'

blocks = createBlocksFromSequence(ss_sequence=ss_sequence)

# graphics
fontTitleSize = 8
fontXSize = 6
fontYSize = 6
scatterFontSize = 5
labelMajorSize=6
labelMinorSize=5
titleColor = 'blue'
hspace= 0.5


def _prettyFormat4Legend(value, rounding=3):
    """ Format mantissa to (rounding) round  and exponent for matplotlib """
    return '$%s^{%s}$' %(round(fMan(value),rounding),  fExp(value))


def _closeFig(fig, pdf, plt):
    pdf.savefig()
    plt.close()
    plt.close(fig)

def _plotIsotropicAnalysisPage1(pdf):
    #  S2, Te, Tm, Rex

    fig = plt.figure(dpi=300)
    fig.suptitle('Isotropic Analysis Results', fontsize=10)
    axSe = plt.subplot(411)
    axTe = plt.subplot(412)
    axRex = plt.subplot(413)
    axss = fig.add_subplot(414)
    plotSS(axss, xSequence, blocks, sequence, startSequenceCode=startSequenceCode, fontsize=5)

    axSe.errorbar(x, S2, yerr=None, fmt="o", color='black', ms=2, ecolor='red', elinewidth=1, capsize=2, )
    axTe.errorbar(x, TE, yerr=None, fmt="o", color='black', ms=2, ecolor='red', elinewidth=1, capsize=2, )
    axRex.errorbar(x, REX, yerr=None, fmt="o", color='black', ms=2, ecolor='red', elinewidth=1, capsize=2, )

    axSe.set_ylim(ymin=0)
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
    _closeFig(fig, pdf, plt)

# init pdf
filePath = os.path.join(exportingDirectoryPath, exportingFileName)
with PdfPages(f'{filePath}.pdf') as pdf:
    _plotIsotropicAnalysisPage1(pdf)





