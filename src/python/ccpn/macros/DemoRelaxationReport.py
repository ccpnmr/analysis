"""
A Demo report for relaxation analysis results.
- Page 1:  it contains a Plot with  R1 R2 NOE  results  with a shared X axis
- Page 2:  it contains a Plot with  RSDM results with a shared X axis

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
__dateModified__ = "$dateModified: 2023-02-07 17:08:14 +0000 (Tue, February 07, 2023) $"
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
import time
import datetime
from matplotlib.backends.backend_pdf import PdfPages
from ccpn.util.Logging import getLogger
from matplotlib.ticker import MultipleLocator
from ccpn.ui.gui.widgets.DrawSS import createBlocksFromSequence, plotSS
from ccpn.util.floatUtils import fExp, fMan


# #########

###################


fileName = 'RelaxationAnalysisResults2'
filePath = f'/Users/luca/Documents/V3-testings/{fileName}'

RSDMResultsDataTable = get('DT:RSDM_results')

if RSDMResultsDataTable is None:
    errorMess = 'Cannot display results. Ensure you have the RSDMResults dataTable in the project or you inserted the correct pid in the macro'
    raise RuntimeError(errorMess)

ss_sequence   =  'BBBBBCCCCBBBBBBCCCCHHHHHHHHHHHHHHCCCCCBBBBCCCCCBBBBBC'
sequence  = 'KLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDAATKTFTVTE'


data =  RSDMResultsDataTable.data
x = data[sv.NMRRESIDUECODE]
x = x.astype(int)
startSequenceCode = x.values[0]
endSequenceCode = startSequenceCode + len(ss_sequence)
startOffsetExtraXTicks = 3 # used to allign the ss to the plots

R1 = data[sv.R1].values
R2 = data[sv.R2].values
NOE = data[sv.HETNOE_VALUE]

R1_ERR = data[sv.R1_ERR]
R2_ERR  = data[sv.R2_ERR]
NOE_ERR = data[sv.HETNOE_VALUE_ERR]

# recalculate the ratio here so don't need to use another dataTable
R2R1 = R2/R1
R2R1_ERR = lf.calculateUncertaintiesError(R1, R2, R1_ERR, R2_ERR)

J0 = data[sv.J0].values
J0_ERR = data[sv.J0_ERR].values
JWH = data[sv.JwH].values
JWH_ERR = data[sv.JwH_ERR].values
JWN = data[sv.JwX].values
JWN_ERR = data[sv.JwX_ERR].values

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
def _plotRates_page1():
    """ Plot the  SS -  R1  - R2 - NOE """
    fig = plt.figure(dpi=400)
    axss = fig.add_subplot(414)
    plotSS(blocks, sequence, startingResidueCode=startSequenceCode, figure=fig, axis=axss)
    axss.set_xlim(startSequenceCode - startOffsetExtraXTicks, endSequenceCode + 2)
    axR1 = plt.subplot(411)
    axR2 = plt.subplot(412)
    axNOE = plt.subplot(413)
    axR1.bar(x, R1, yerr=R1_ERR, color='black', ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))
    axR2.bar(x, R2, yerr=R2_ERR, color='black', ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))
    axNOE.bar(x, NOE, yerr=NOE_ERR, color='black', ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))
    axR1.set_title('R1', fontsize=fontTitleSize, color=titleColor)
    axR2.set_title('R2',  fontsize=fontTitleSize, color=titleColor)
    axNOE.set_title('HetNOE', fontsize=fontTitleSize, color=titleColor)
    axR1.set_ylabel('R$_{1}$ (sec$^{-1}$)', fontsize=fontYSize)
    axR2.set_ylabel('R$_{2}$ (sec$^{-1}$)', fontsize=fontYSize)
    axNOE.set_ylabel('het-NOE ratio', fontsize=fontYSize)
    axNOE.set_xlabel('Residue Number', fontsize=fontXSize, )
    axR1.get_shared_x_axes().join(axR1, axR2, axNOE)
    ml = MultipleLocator(1)
    for ax in [axss, axR1, axR2, axNOE]:
        ax.spines[['right', 'top']].set_visible(False)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(ml)
        ax.tick_params(axis='both', which='major', labelsize=labelMajorSize)
        ax.tick_params(axis='both', which='minor', labelsize=labelMinorSize)
        ax.yaxis.set_label_coords(-0.05, 0.5) #align the labels to vcenter and middle

    plt.tight_layout()
    plt.subplots_adjust(hspace=hspace)
    pdf.savefig()  # saves the current figure into a pdf page
    plt.close(fig)

def _plotR2R1_page2():
    # page two R2/R1 Ratio
    fig = plt.figure(dpi=300)
    axss = fig.add_subplot(312)
    plotSS(blocks, sequence, startingResidueCode=startSequenceCode, figure=fig, axis=axss)
    axR2R1 = plt.subplot(311)
    axR2R1.bar(x, R2R1, yerr=R2R1_ERR, color='black', ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))
    axR2R1.set_title('R2/R1',  fontsize=fontTitleSize, color=titleColor)
    axR2R1.set_ylabel('R$_{2}$/R$_{1}$', fontsize=fontYSize)
    axR2R1.set_xlabel('Residue Number', fontsize=fontXSize, )
    ml = MultipleLocator(1)
    axR2R1.spines[['right', 'top']].set_visible(False)
    axR2R1.minorticks_on()
    axR2R1.xaxis.set_minor_locator(ml)
    axR2R1.tick_params(axis='both', which='major', labelsize=labelMajorSize)
    axR2R1.tick_params(axis='both', which='minor', labelsize=labelMinorSize)
    plt.tight_layout()
    plt.subplots_adjust(hspace=hspace)
    pdf.savefig()
    plt.close(fig)

def _plotSDM_page3():
    # page three RSDM

    fig = plt.figure(dpi=300)

    axJ0 = plt.subplot(411)
    axJwh = plt.subplot(412)
    axJwx = plt.subplot(413)
    axss = fig.add_subplot(414)
    plotSS(blocks, sequence, startingResidueCode=startSequenceCode, figure=fig, axis=axss)

    axJ0.errorbar(x, J0, yerr=J0_ERR, fmt="o", color='black', ms=2, ecolor='red', elinewidth=1, capsize=2, )
    axJwh.errorbar(x, JWH, yerr=JWH_ERR, fmt="o", color='black', ms=2, ecolor='red', elinewidth=1, capsize=2, )
    axJwx.errorbar(x, JWN, yerr=JWN_ERR, fmt="o", color='black', ms=2, ecolor='red', elinewidth=1, capsize=2, )

    axJ0.set_ylim(ymin=0)
    axJwh.set_ylim(ymin=0)
    axJwx.set_ylim(ymin=0)

    axJ0.set_title('J0',  fontsize=fontTitleSize, color=titleColor)
    axJwh.set_title(L_JWH,  fontsize=fontTitleSize, color='blue')
    axJwx.set_title(L_JWN,  fontsize=fontTitleSize, color=titleColor)

    axJ0.set_ylabel(f'J0 {L_SR}', fontsize=fontYSize)
    axJwh.set_ylabel(f'{L_JWH} {L_SR}', fontsize=fontYSize)
    axJwx.set_ylabel(f'{L_JWN} {L_SR}', fontsize=fontYSize)

    ml = MultipleLocator(1)
    for ax in [axss, axJ0, axJwh, axJwx]:
        ax.spines[['right', 'top']].set_visible(False)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(ml)
        ax.tick_params(axis='both', which='major', labelsize=labelMajorSize)
        ax.tick_params(axis='both', which='minor', labelsize=labelMinorSize)
        ax.yaxis.get_offset_text().set_x(-0.02)
        ax.yaxis.get_offset_text().set_size(5)
        ax.yaxis.set_label_coords(-0.05, 0.5)  # align the labels to vcenter and middle

    axJ0.get_shared_x_axes().join(axJ0, axJwh, axJwx)

    axJwx.set_xlabel('Residue Number', fontsize=fontXSize, )
    plt.tight_layout()
    plt.subplots_adjust(hspace=hspace)
    pdf.savefig()
    plt.close()
    plt.close(fig)


def _plotScatters_page4():
    # page two R2/R1 Ratio
    fig = plt.figure(dpi=300)

    axj0_jwh = plt.subplot(221)
    axj0_jwx = plt.subplot(223)
    axjwh_jwx = plt.subplot(222)
    axR1R2 = plt.subplot(224)

    ##  jwH vs J0
    axj0_jwh.scatter(J0, JWH, s=1, color='black', )
    for i, txt in enumerate(x.values):
        axj0_jwh.annotate(str(txt), (J0[i], JWH[i]), fontsize=3)
    axj0_jwh.set_title(f'{L_JWH} vs J0',  fontsize=fontTitleSize, color=titleColor)
    axj0_jwh.set_xlabel(f'J0 {L_SR}', fontsize=fontYSize, )
    axj0_jwh.set_ylabel(f'{L_JWH} {L_SR}', fontsize=fontYSize)

    # fit aJ + b
    coef = a, b = np.polyfit(J0, JWH, 1)
    poly1d_fn = np.poly1d(coef)
    aVal = '$%s^{%s}$' %(round(fMan(a),3),  fExp(a))
    bVal =  '$%s^{%s}$' %(round(fMan(b),3),  fExp(b))
    axj0_jwh.plot(J0, poly1d_fn(J0), color='blue', linewidth=0.2, label=f'y = {aVal}x + {bVal}')
    axj0_jwh.legend(prop={'size': 6})
    # ##   jwN vs J0
    axj0_jwx.scatter(J0, JWN, s=1, color='black', )

    for i, txt in enumerate(x.values):
        axj0_jwx.annotate(str(txt), (J0[i], JWN[i]), fontsize=3)
    axj0_jwx.set_title(f'{L_JWN} vs J0', fontsize=fontTitleSize, color=titleColor)
    axj0_jwx.set_xlabel(f'J0 {L_SR}', fontsize=fontYSize, )
    axj0_jwx.set_ylabel(f'{L_JWN} {L_SR}', fontsize=fontYSize)
    axj0_jwh.get_shared_x_axes().join(axj0_jwh, axj0_jwx)



    ##  jwN vs  jwH
    axjwh_jwx.scatter(JWH, JWN, s=1, color='black', )
    for i, txt in enumerate(x.values):
        axjwh_jwx.annotate(str(txt), (JWH[i], JWN[i]), fontsize=3)
    axjwh_jwx.set_title(f'{L_JWN} vs {L_JWH}',  fontsize=fontTitleSize, color=titleColor)
    axjwh_jwx.set_xlabel(f'{L_JWH} {L_SR}', fontsize=fontYSize, )
    axjwh_jwx.set_ylabel(f'{L_JWN} {L_SR}', fontsize=fontYSize)

    ## R1 vs R2
    axR1R2.scatter(R2, R1, s=1, color='black', )
    for i, txt in enumerate(x.values):
        axR1R2.annotate(str(txt), (R2[i], R1[i]), fontsize=2)
    axR1R2.set_title('R1 vs R2',  fontsize=fontTitleSize, color=titleColor)
    axR1R2.set_xlabel('R$_{2} (s^{-1})$', fontsize=fontYSize, )
    axR1R2.set_ylabel('R$_{1} (s^{-1})$', fontsize=fontYSize)

    ml = MultipleLocator(1)
    for ax in [axj0_jwh, axj0_jwx, axjwh_jwx, axR1R2]:
        ax.spines[['right', 'top']].set_visible(False)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(ml)
        ax.tick_params(axis='both', which='major', labelsize=labelMajorSize)
        ax.tick_params(axis='both', which='minor', labelsize=labelMinorSize)
        ax.yaxis.get_offset_text().set_x(-0.02)
        ax.yaxis.get_offset_text().set_size(5)
        ax.xaxis.get_offset_text().set_size(5)


    plt.tight_layout()
    plt.subplots_adjust(hspace=hspace)
    pdf.savefig()
    plt.close()
    plt.close(fig)



# init pdf
with PdfPages(f'{filePath}.pdf') as pdf:
    _plotRates_page1()
    _plotR2R1_page2()
    _plotSDM_page3()
    _plotScatters_page4()





