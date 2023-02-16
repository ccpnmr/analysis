"""
A macro to plot R1*R2 and R2/R1 for the Discrimination of motional Anisotropy and Chemical Exchange
in a Relaxation Analysis

This macro requires a  dataset  created after performing  the Reduced Spectral density Mapping calculation model
on the Relaxation Analysis Module (alpha)

Which is a dataset that contains the following (mandatory) columns:
    - nmrResidueCode
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
__dateModified__ = "$dateModified: 2023-02-16 17:44:59 +0000 (Thu, February 16, 2023) $"
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
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from matplotlib.ticker import FormatStrFormatter
from matplotlib.backends.backend_pdf import PdfPages
from ccpn.util.Common import percentage
import ccpn.framework.lib.experimentAnalysis.SeriesAnalysisVariables as sv
import ccpn.framework.lib.experimentAnalysis.fitFunctionsLib as lf
import ccpn.framework.lib.experimentAnalysis.spectralDensityLib as sdl
from ccpn.ui.gui.widgets.DrawSS import plotSS

############################################################
#####################    User data      ##########################
############################################################

fileName = 'RelaxationAnalysisAnisotropyDetermination'
filePath = f'/Users/luca/Documents/V3-testings/{fileName}'

##  demo sequence for the GB1 protein
sequence  = 'KLILNGKTLKGETTTEAVDAATAEKVFKQYANDNGVDGEWTYDAATKTFTVTE'
##  secondary structure  for the above sequence  using the DSSP nomenclature
ss_sequence   =  'BBBBBCCCCBBBBBBCCCCHHHHHHHHHHHHHHCCCCCBBBBCCCCCBBBBBC'

## Some Graphics Settings
showInteractivePlot = True # True if you want the plot to popup as a new windows, to allow the zooming and panning of the figure.
scatterColor = 'navy'
scatterColorError = 'darkred'
scatterExcludedByNOEColor = 'orange'
scatterSize = 3
scatterErrorLinewidth=0.1
scatterErrorCapSize=0.8
medianLineColour = 'black'
fontTitleSize = 8
fontXSize = 6
fontYSize = 6
scatterFontSize = 5
labelMajorSize=6
labelMinorSize=5
titleColor = 'darkblue'
hspace= 0.5

############################################################
##################   End User data     ##########################
###########################################################


###################      start macro       #########################

RSDMResultsDataTable = get('DT:RSDM_results')
if RSDMResultsDataTable is None:
    errorMess = 'Cannot display results. Ensure you have the RSDMResults dataTable in the project or you inserted the correct pid in the macro'
    raise RuntimeError(errorMess)


######################      data preparation   ## ##################
## get the various values  and perform the needed calculations

data =  RSDMResultsDataTable.data
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
R2R1 = R2/R1
R2R1_ERR = lf.calculateUncertaintiesError(R1, R2, R1_ERR, R2_ERR)
R1R2 = R1*R2
R1R2_ERR = lf.calculateUncertaintiesProductError(R1, R2, R1_ERR, R2_ERR)

NOE_limitExclusion = 0.65
eind =np.argwhere(NOE < NOE_limitExclusion).flatten()

fR1, fR2 = sdl._filterLowNoeFromR1R2(R1, R2, NOE, NOE_limitExclusion)
fR1R2 = fR1*fR2
fR2R1 = fR2/fR1
medianfR1R2 = np.median(fR1R2)
medianfR2R1 = np.median(fR2R1)
maxR1R2 = np.max(fR1R2)
yMedianR1R2 = np.array([medianfR1R2]*len(xSequence))
yMedianR2R1 = np.array([medianfR2R1]*len(xSequence))
yScatterMedianR1R2 = np.linspace(0, np.max(R1R2), len(yMedianR1R2))
xScatterMedianLine = np.linspace(0, np.max(R2R1), len(yMedianR1R2))

####################     end data preparation     ##################


def _setXTicks(ax):
    ml = MultipleLocator(1)
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(ml)
    ax.tick_params(axis='both', which='major', labelsize=labelMajorSize)
    ax.tick_params(axis='both', which='minor', labelsize=labelMinorSize)



def _setCommonYLim(ax, ys):
    extraY = np.ceil(percentage(30, np.max(ys)))
    ylim = np.max(ys) + extraY
    ax.set_ylim([0, ylim])

def _ploteRates(pdf):
    fig = plt.figure(figsize=(5, 3.5), dpi=300, layout="constrained")
    maxRows = 3
    maxCols = 1
    spec = fig.add_gridspec(maxRows, maxCols, height_ratios=[4, 4, 1])
    row = 0
    axR2R1 = fig.add_subplot(spec[row, 0 ])
    row+=1
    axR2R1.errorbar(x, R2R1,  yerr=R2R1_ERR, color = scatterColor, ms=scatterSize, fmt='o', ecolor=scatterColorError, elinewidth=scatterErrorLinewidth, capsize=scatterErrorCapSize )
    # overlay excludeFrom Median calculation on a different colour
    axR2R1.errorbar(x[eind], R2R1[eind], yerr=R2R1_ERR[eind], color=scatterExcludedByNOEColor, ms=scatterSize, fmt='o', ecolor=scatterColorError, elinewidth=scatterErrorLinewidth, capsize=scatterErrorCapSize,  label = f'NOE < {NOE_limitExclusion}')
    axR2R1.plot(xSequence, yMedianR2R1, medianLineColour, linewidth=0.5, label ='R2/R1 median')
    axR2R1.set_title('R2/R1', fontsize=fontTitleSize, color=titleColor)
    axR2R1.set_ylabel('R$_{2}$/R$_{1}$', fontsize=fontYSize)
    _setXTicks(axR2R1)
    # _setYTicks(axR2R1, R2R1)
    axR2R1.legend(prop={'size': 6})
    extraY = np.ceil(percentage(30, np.max(R2R1)))
    ylim = np.max(R2R1)+extraY
    axR2R1.set_ylim([0, ylim])
    axR2R1.spines[['right', 'top']].set_visible(False)

    # R1 x R2
    axR1R2 = fig.add_subplot(spec[row, 0])
    row+=1

    axR1R2.errorbar(x, R1R2,  yerr=R1R2_ERR, ms=scatterSize, color = scatterColor, fmt='o', ecolor=scatterColorError, elinewidth=scatterErrorLinewidth, capsize=scatterErrorCapSize, )
    axR1R2.errorbar(x[eind], R1R2[eind], yerr=R1R2_ERR[eind], color=scatterExcludedByNOEColor, ms=scatterSize, fmt='o', ecolor=scatterColorError, elinewidth=scatterErrorLinewidth, capsize=scatterErrorCapSize,  label = f'NOE < {NOE_limitExclusion}')
    axR1R2.plot(xSequence, yMedianR1R2, medianLineColour, linewidth=0.5, label ='R1R2 median')
    axR1R2.set_title('R1*R2', fontsize=fontTitleSize, color=titleColor)
    axR1R2.set_ylabel('R$_{1}$ * R$_{2}$', fontsize=fontYSize)
    axR1R2.set_xlabel('Residue Number', fontsize=fontXSize, )
    axR1R2.legend(prop={'size': 6})
    axR1R2.spines[['right', 'top']].set_visible(False)
    _setCommonYLim(axR1R2, R1R2)
    _setXTicks(axR1R2)


    # axss = fig.add_subplot(313)
    axss = fig.add_subplot(spec[row, 0])
    plotSS(axss, xSequence, sequence, ss_sequence=ss_sequence, startSequenceCode=startSequenceCode, fontsize=5,
           showSequenceNumber=False, )
    axss.get_shared_x_axes().join(axss, axR2R1, axR1R2,)
    pdf.savefig()
    return fig

def _plotScatterRates(pdf):
    fig = plt.figure( figsize=(5, 3.5), dpi=300)

    #  Scatter
    axRscatter = plt.subplot(111)
    # axRscatter.scatter(R2R1, R1R2)
    axRscatter.errorbar(R2R1, R1R2,
                        yerr=R1R2_ERR/2,
                        xerr=R2R1_ERR/2,
                        color=scatterColor,
                        alpha=0.7, #to see better the labels
                        ms=scatterSize, fmt='o', ecolor=scatterColorError, elinewidth=scatterErrorLinewidth, capsize=scatterErrorCapSize, )
    for i, txt in enumerate(x):
        extraY = percentage(0.5, R1R2[i])
        yPos = R1R2[i] + extraY
        extraX = percentage(0.5, R2R1[i])
        xPos = R2R1[i] + extraX
        axRscatter.annotate(str(txt), xy=(R2R1[i], R1R2[i]), xytext=(xPos, yPos), fontsize=3.5, arrowprops=dict(facecolor='grey',arrowstyle="-",lw=0.3  ))
    axRscatter.plot(yMedianR2R1, yScatterMedianR1R2, medianLineColour, linewidth=0.5, label ='R1R2 median')
    axRscatter.plot(xScatterMedianLine, yMedianR1R2, medianLineColour, linewidth=0.5, label ='R2/R1 median')
    axRscatter.set_title('R$_{1}$R$_{2}$ vs R$_{2}$/R$_{1}$ ', fontsize=fontTitleSize, color=titleColor)
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
    pdf.savefig()
    return fig


# init pdf
with PdfPages(f'{filePath}.pdf') as pdf:
    fig1 = _ploteRates(pdf)
    fig2 = _plotScatterRates(pdf)

if showInteractivePlot:
    plt.show()
else:
    fig1.close()
    fig2.close()
###################      end macro        #########################


