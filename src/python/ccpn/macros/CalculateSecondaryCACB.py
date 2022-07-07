
"""
A macro for calculating the secondary CA and CB chemical shifts using the random coil values from
S. Spera and A. Bax. J. Am. Chem. Soc. 1991, 113, 14, 5490–5492. (they are given in the figure legend of Fig 1)

Requirements:
    - CcpNmrAnalysis 3.1.0
    - A chemicalshift list with CA-CB assignments (either one or both)

This example uses the chemicalshift list imported from the bmrb file bmr7280_3.str (GB1)
(https://bmrb.io/ftp/pub/bmrb/entry_directories/bmr7280/bmr7280_3.str)
To load this chemicalshiftList (CSL):
    > start  AnalysisAssign 3.1.0
    > drop the file bmr7280_3.str and select import or start a new project.
    > open the macro editor from MainMenu -> Macro -> New Macro editor
    > copy and paste the macro in the macro editor
    > press the green play button to run to plot the results.
    > if you want save as table, provide the full path in the "savingPath" variable and set "doExport = True"

If you use your own CSL
    > Go to sidebar, expand the CSL branch, select your CSL of interest,
    > right click > copy pid to clipboard,
    > go to the ln of this macro where defines "chemicalshiftList = get('PID') "and replace the the pid
    > run as normal

"""

#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2022-07-07 20:00:50 +0100 (Thu, July 07, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: LucaM $"
__date__ = "$Date: 2022-07-07 19:53:29 +0100 (Thu, July 07, 2022) $"
#=========================================================================================
__title__ = "Secondary CA and CB chemical shifts using the random coil values"
# Start of code
#=========================================================================================

#========================== User's settings ==============================================

## copy and paste the chemicalShiftList pid from sidebar (right-click > copy pid)
chemicalshiftList = get('CL:entry7280') # Replace 'CL:entry7280' with your CSL name

doExport = False # set to True if you want export the results as a table
savingFileName = 'secondaryShifts.xlsx'
savingPath = '~/' # set the directory where to export (full path)
plotResults = True # set to True if want to visualise the results as a bar plot

CA = 'CA'
CB = 'CB'
filteringAtoms = [CA, CB]
## Filter atoms (CA-CB). Add more atoms if you have more and amend the AA_shifts dictionary accordingly

AA_shifts = {
            'ALA': {CA:52.3, CB:19.0},
            'ARG': {CA:56.1, CB:30.3},
            'ASN': {CA:52.8, CB:37.9},
            'ASP': {CA:54.0, CB:40.8},
            'CYS': {CA:56.9, CB:28.9},
            'GLN': {CA:56.1, CB:28.4},
            'GLU': {CA:56.4, CB:29.7},
            'GLY': {CA:45.1, CB:None},
            'ILE': {CA:61.3, CB:38.0},
            'LEU': {CA:55.1, CB:42.3},
            'LYS': {CA:56.5, CB:32.5},
            'MET': {CA:55.3, CB:32.6},
            'PHE': {CA:58.0, CB:39.0},
            'PRO': {CA:63.1, CB:31.7},
            'SER': {CA:58.2, CB:63.2},
            'THR': {CA:62.1, CB:69.2},
            'TRP': {CA:57.7, CB:30.3},
            'TYR': {CA:58.1, CB:38.8},
            'VAL': {CA:62.3, CB:32.1}
          }

#========================== start of the macro ===========================================

import ccpn.core.ChemicalShiftList as csl
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from ccpn.util.Path import aPath
import pandas as pd
import numpy as np
from ccpn.ui.gui.widgets.MessageDialog import showWarning

if not chemicalshiftList:
    showWarning('chemicalShift list not found', 'Set the chemicalShiftList pid in the macro.')
df = chemicalshiftList._data


filteredDf =  df[df[csl.CS_ATOMNAME].isin(filteringAtoms)]

resultDf = pd.DataFrame(columns=[csl.CS_SEQUENCECODE, csl.CS_RESIDUETYPE, CA, CB])
for ix, row in filteredDf.iterrows():
    residueType = row[csl.CS_RESIDUETYPE]
    sequenceCode = row[csl.CS_SEQUENCECODE]
    if residueType in AA_shifts:
        for atomName in filteringAtoms:
            if row[csl.CS_ATOMNAME] == atomName:
                refShifts = AA_shifts.get(residueType)
                refAtomShift = refShifts.get(atomName)
                expShiftValue = row[csl.CS_VALUE]
                newRowName = f'{sequenceCode}.{residueType}'
                if all([refAtomShift, expShiftValue]):
                    secShift = expShiftValue - refAtomShift ## Subtract from references
                    resultDf.loc[newRowName, atomName] = secShift ## build the columns/rows on the resultDf
                    resultDf.loc[newRowName, csl.CS_SEQUENCECODE] = sequenceCode
                    resultDf.loc[newRowName, csl.CS_RESIDUETYPE] = residueType
resultDf.sort_index()

def plotCACBResults(resultDf):
    caValues = resultDf[CA]
    cbValues = resultDf[CB]
    labels = resultDf.index
    x = pd.to_numeric(resultDf['sequenceCode'])
    width = 0.35  # the width of the bars
    fig, ax = plt.subplots()
    caAx = ax.bar(x - width/2, caValues, width, label=CA, align='center')
    cbAx = ax.bar(x + width/2, cbValues, width, label=CB, align='center')
    baseline = ax.plot(np.arange(*ax.get_xlim()), np.arange(*ax.get_xlim())*0, 'black')
    # Change labels, title  etc.
    ax.set_ylabel('Delta shifts')
    ax.set_title('Secondary Shifts for CA-CB')
    ax.set_xticks(x, labels)
    ax.legend()
    tick_spacing = 0.5
    ax.yaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
    plt.xticks(rotation=90)
    plt.show()

if plotResults:
    plotCACBResults(resultDf)

if doExport:
    exportingPath = aPath(savingPath)
    exportingPath = exportingPath.joinpath(savingFileName)
    exportingPath = exportingPath.assureSuffix('.csv')
    resultDf.to_csv(str(exportingPath))

