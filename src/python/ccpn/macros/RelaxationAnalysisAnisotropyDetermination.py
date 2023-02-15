"""
A macro to plot R1*R2 and R2/R1 for the Discrimination of Motional Anisotropy and Chemical Exchange
in a Relaxation Analysis

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
__dateModified__ = "$dateModified: 2023-02-15 12:25:30 +0000 (Wed, February 15, 2023) $"
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
import ccpn.framework.lib.experimentAnalysis.spectralDensityLib as sdl
import pandas as pd
import matplotlib.pyplot as plt
import math
from matplotlib.backends.backend_pdf import PdfPages
from ccpn.util.Logging import getLogger
from matplotlib.ticker import MultipleLocator
from ccpn.ui.gui.widgets.DrawSS import createBlocksFromSequence, plotSS


fileName = 'RelaxationAnalysisAnisotropyDetermination'
filePath = f'/Users/luca/Documents/V3-testings/{fileName}'
RSDMResultsDataTable = get('DT:RSDM_results')

if RSDMResultsDataTable is None:
    errorMess = 'Cannot display results. Ensure you have the RSDMResults dataTable in the project or you inserted the correct pid in the macro'
    raise RuntimeError(errorMess)

ss_sequence   =  'BBBBBCCCCBBBBBBCCCCHHHHHHHHHHHHHHCCCCCBBBBCCCCCBBBBBC'
sequence  = 'KLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDAATKTFTVTE'
blocks = createBlocksFromSequence(ss_sequence=ss_sequence)

######## data #######

data =  RSDMResultsDataTable.data
x = data[sv.NMRRESIDUECODE]
x = x.astype(int)
x = x.values
startSequenceCode = x[0]
endSequenceCode = startSequenceCode + len(ss_sequence)
startOffsetExtraXTicks = 3 # used to align the ss to the plots
xSequence = np.arange(startSequenceCode, endSequenceCode)
R1 = data[sv.R1].values
R2 = data[sv.R2].values
NOE = data[sv.HETNOE_VALUE]
R1_ERR = data[sv.R1_ERR]
R2_ERR  = data[sv.R2_ERR]
NOE_ERR = data[sv.HETNOE_VALUE_ERR]
R2R1 = R2/R1
R2R1_ERR = lf.calculateUncertaintiesError(R1, R2, R1_ERR, R2_ERR)
R1R2 = R1*R2
R1R2_ERR = R2R1_ERR

######## graphics #######

fontTitleSize = 8
fontXSize = 6
fontYSize = 6
scatterFontSize = 5
labelMajorSize=6
labelMinorSize=5
titleColor = 'blue'
hspace= 0.5


def _closeFig(fig, pdf, plt):
    pdf.savefig()
    plt.close(fig)


def _ploteRates(pdf):
    fig = plt.figure(dpi=300)
    axR2R1 = plt.subplot(411)
    axR2R1.bar(x, R2R1, yerr=R2R1_ERR, color='black', ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))
    axR2R1.set_title('R2/R1', fontsize=fontTitleSize, color=titleColor)
    axR2R1.set_ylabel('R$_{2}$/R$_{1}$', fontsize=fontYSize)
    # axR2R1.set_xlabel('Residue Number', fontsize=fontXSize, )
    ml = MultipleLocator(1)
    axR2R1.spines[['right', 'top']].set_visible(False)
    axR2R1.minorticks_on()
    axR2R1.xaxis.set_minor_locator(ml)
    axR2R1.tick_params(axis='both', which='major', labelsize=labelMajorSize)
    axR2R1.tick_params(axis='both', which='minor', labelsize=labelMinorSize)
    
    # R1 x R2
    axR1R2 = plt.subplot(412)
    axR1R2.bar(x, R1R2, yerr=R1R2_ERR, color='black', ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))
    axR1R2.set_title('R1 * R2', fontsize=fontTitleSize, color=titleColor)
    axR1R2.set_ylabel('R$_{1}$ * R$_{2}$', fontsize=fontYSize)
    axR1R2.set_xlabel('Residue Number', fontsize=fontXSize, )
    ml = MultipleLocator(1)
    axR1R2.spines[['right', 'top']].set_visible(False)
    axR1R2.minorticks_on()
    axR1R2.xaxis.set_minor_locator(ml)
    axR1R2.tick_params(axis='both', which='major', labelsize=labelMajorSize)
    axR1R2.tick_params(axis='both', which='minor', labelsize=labelMinorSize)

    axss = fig.add_subplot(413)
    plotSS(axss, xSequence, blocks, sequence, startSequenceCode=startSequenceCode, fontsize=5)
    axss.get_shared_x_axes().join(axss, axR2R1, axR1R2,)

    plt.tight_layout()
    # plt.subplots_adjust(hspace=hspace, wspace=0.3)
    # plt.subplots_adjust(left=0.1, right=0.2, top=.3, bottom=0.2)
    _closeFig(fig, pdf, plt)


def _ploteScatterRates(pdf):
    fig = plt.figure(dpi=300)

    #  Scatter
    axRscatter = plt.subplot(111)
    axRscatter.errorbar(R2R1, R1R2,
                        yerr=R1R2_ERR,
                        xerr=R2R1_ERR,
                        ms=2, fmt='o', ecolor='red', elinewidth=1, capsize=2, )
    for i, txt in enumerate(x):
        axRscatter.annotate(str(txt), (R2R1[i], R1R2[i]), fontsize=2)
    axRscatter.set_title('R$_{1}$*R$_{2}$ vs R$_{2}$/R$_{1}$ ', fontsize=fontTitleSize, color=titleColor)
    axRscatter.set_xlabel('R$_{2}$/R$_{1}$', fontsize=fontYSize, )
    axRscatter.set_ylabel('R$_{1}$*R$_{2}$', fontsize=fontYSize)
    ml = MultipleLocator(1)
    axRscatter.spines[['right', 'top']].set_visible(False)
    axRscatter.minorticks_on()
    axRscatter.xaxis.set_minor_locator(ml)
    axRscatter.tick_params(axis='both', which='major', labelsize=labelMajorSize)
    axRscatter.tick_params(axis='both', which='minor', labelsize=labelMinorSize)
    axRscatter.yaxis.get_offset_text().set_x(-0.02)
    axRscatter.yaxis.get_offset_text().set_size(5)
    axRscatter.xaxis.get_offset_text().set_size(5)
    axRscatter.set_xlim(xmin=0)
    axRscatter.set_ylim(ymin=0)
    plt.tight_layout()
    plt.subplots_adjust(hspace=hspace)

    _closeFig(fig, pdf, plt)


# init pdf
with PdfPages(f'{filePath}.pdf') as pdf:

    _ploteRates(pdf)
    _ploteScatterRates(pdf)





