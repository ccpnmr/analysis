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
__dateModified__ = "$dateModified: 2023-02-03 13:41:08 +0000 (Fri, February 03, 2023) $"
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
from adjustText import adjust_text

fileName = 'RelaxationAnalysisResults'
filePath = f'/Users/luca/Documents/V3-testings/{fileName}'

RSDMResultsDataTable = get('DT:RSDMResults')

if RSDMResultsDataTable is None:
    errorMess = 'Cannot display results. Ensure you have the RSDMResults dataTable in the project or you inserted the correct pid in the macro'
    raise RuntimeError(errorMess)


data =  RSDMResultsDataTable.data
# just for testing
todrop = data.index[-1]
data.drop(todrop, inplace=True)

x = data[sv.NMRRESIDUECODE]
x = x.astype(int)
R1 = data[sv.R1]
R2 = data[sv.R2]
NOE = data[sv.HETNOE_VALUE]

R1_ERR = data[sv.R1_ERR]
R2_ERR  = data[sv.R2_ERR]
NOE_ERR = data[sv.HETNOE_VALUE_ERR]

# recalculate the ratio here so don't need to use another dataTable
R2R1 = R2/R1
R2R1_ERR = lf.calculateUncertaintiesError(R1, R2, R1_ERR, R2_ERR)

J0 = data[sv.J0]
J0_ERR = data[sv.J0_ERR]
JWH = data[sv.JwH]
JWH_ERR = data[sv.JwH_ERR]
JWN = data[sv.JwX]
JWN_ERR = data[sv.JwX_ERR]

# init pdf
with PdfPages(f'{filePath}.pdf') as pdf:

    fig = plt.figure(dpi=300)
    axR1 = plt.subplot(311)
    axR2 = plt.subplot(312)
    axNOE = plt.subplot(313)

    axR1.bar(x, R1, yerr=R1_ERR, color='black',  ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))
    axR2.bar(x, R2,  yerr=R2_ERR, color='black',  ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))
    axNOE.bar(x, NOE, yerr=NOE_ERR, color='black',  ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))

    axR1.set_title('R1', fontsize=8)
    axR2.set_title('R2', fontsize=8)
    axNOE.set_title('HetNOE', fontsize=8)

    axR1.set_ylabel('R$_{1}$ (sec$^{-1}$)', fontsize=8)
    axR2.set_ylabel('R$_{2}$ (sec$^{-1}$)', fontsize=8)
    axNOE.set_ylabel('het-NOE ratio', fontsize=8)
    axNOE.set_xlabel('Residue Number', fontsize=5, )

    axR1.get_shared_x_axes().join(axR1, axR2, axNOE)

    ml = MultipleLocator(1)
    for ax in [axR1, axR2, axNOE]:
        ax.spines[['right', 'top']].set_visible(False)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(ml)
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.tick_params(axis='both', which='minor', labelsize=5)
    plt.tight_layout()
    plt.subplots_adjust( hspace=1.4)
    pdf.savefig()  # saves the current figure into a pdf page
    plt.close()

    #page two R2/R1 Ratio
    fig2 = plt.figure(dpi=300)
    axR2R1 = plt.subplot(311)
    axR2R1.bar(x, R2R1, yerr=R2R1_ERR, color='black', ecolor='red', error_kw=dict(lw=1, capsize=2, capthick=0.5))
    axR2R1.set_title('R2/R1', fontsize=8)
    axR2R1.set_ylabel('R$_{2}$/R$_{1}$', fontsize=8)
    axR2R1.set_xlabel('Residue Number', fontsize=5, )
    axR1R2 = plt.subplot(312)
    t1v = 1/R1.values
    t2v = 1/R2.values
    axR1R2.scatter(t2v, t1v, s=1, color='black', )
    for i, txt in enumerate(x.values):
        axR1R2.annotate(str(txt), (t2v[i], t1v[i]), fontsize=2)
    axR1R2.set_title('T1 vs T2', fontsize=8)
    axR1R2.set_ylabel('T$_{2} (s)$', fontsize=8)
    axR1R2.set_xlabel('T$_{1} (s)$', fontsize=8, )
    ml = MultipleLocator(1)
    for ax in [axR2R1, axR1R2]:
        ax.spines[['right', 'top']].set_visible(False)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(ml)
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.tick_params(axis='both', which='minor', labelsize=5)
    plt.tight_layout()
    plt.subplots_adjust(hspace=1.4)
    pdf.savefig()
    plt.close()

    # page three RSDM

    fig3 = plt.figure(dpi=300)
    j0 = plt.subplot(311)
    jwh = plt.subplot(312)
    jwx = plt.subplot(313)

    j0.errorbar(x, J0, yerr=J0_ERR, fmt="o", color='black',  ms=2, ecolor='red', elinewidth=1, capsize=2,)
    jwh.errorbar(x, JWH, yerr=JWH_ERR, fmt="o", color='black', ms=2, ecolor='red', elinewidth=1, capsize=2,)
    jwx.errorbar(x, JWN, yerr=JWN_ERR, fmt="o", color='black',  ms=2, ecolor='red', elinewidth=1, capsize=2,)

    j0.set_title('J0',  fontsize=8)
    jwh.set_title('$J(\omega_{H})$', fontsize=8)
    jwx.set_title('$J(\omega_{N})$',  fontsize=8)

    j0.set_ylabel('J0 (sec/rad)',  fontsize=8)
    jwh.set_ylabel('$J(\omega_{H})$ (sec/rad)', fontsize=8)
    jwx.set_ylabel('$J(\omega_{N})$ (sec/rad)',  fontsize=8)

    ml = MultipleLocator(1)
    for ax in [j0, jwh, jwx]:
        ax.spines[['right', 'top']].set_visible(False)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(ml)
        ax.tick_params(axis='both', which='major', labelsize=8)
        ax.tick_params(axis='both', which='minor', labelsize=5)
        ax.yaxis.get_offset_text().set_x(-0.02)
        ax.yaxis.get_offset_text().set_size(5)

    j0.get_shared_x_axes().join(j0, jwh, jwx)

    jwx.set_xlabel('Residue Number', fontsize=5, )
    plt.tight_layout()
    plt.subplots_adjust(hspace=1.4)
    pdf.savefig()
    plt.close()
