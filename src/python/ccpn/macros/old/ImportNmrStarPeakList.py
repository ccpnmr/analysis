_UI = True  # Default opens a popup for selecting the input and run the macro

Warnings = "Warning: This is only a Pre-alpha BMRB Importer. It might not work or work partially. Always inspect the results!"

InfoMessage = """
        This popup will create a new chemical shift list from the NMR-STAR v3.1 file selected.

    """

## Start of Macro

import pandas as pd
import os
import glob
import numpy as np
from collections import OrderedDict as od
from ccpn.util.Common import getAxisCodeMatchIndices
from ccpn.framework.PathsAndUrls import macroPath as mp
from ccpn.core.lib.ContextManagers import undoBlock

_Spectral_peak_list = "_Spectral_peak_list."  # used to find the loop of interest in the BMRB and shorten the column header name on the DataFrame
_Peak_char = "_Peak_char.Peak_ID"

# only the entries of interest to map to CcpNmr V3 objects. Can be increased as needed
Sf_category = "Sf_category"
Peak_ID = "Peak_ID"
Spectral_dim_ID = "Spectral_dim_ID"
Val = "Val"
Comp_ID = "Comp_ID"
Atom_ID = "Atom_ID"
Atom_type = "Atom_type"
STOP = "stop_"
Spectral_peak_list = _Spectral_peak_list+Sf_category
Peak_char = _Peak_char+Peak_ID

# NOT IN USE, just to map BMRB nomenclature to V3
# V3_BMRB_map = {
#                 "residueType"  : Comp_ID,  # nmrResidue, e.g. ALA
#                 "sequenceCode" : Seq_ID,   # nmrResidue, e.g. 1
#                 "name"         : Atom_ID,  # nmrAtom,    e.g. HA
#                 "position"     : Val,      # peak,       always ppm value !?
#                }

def _openBmrb(filePath):
    # HardCoded bit to find just the Peak List Sections, Replace with NEF Style
    # Currently only reads first peak list - later expand to include all
    lines = []
    k = 0
    with open(filePath, "r") as bmrbFileText:
        for line in bmrbFileText:
            if Spectral_peak_list in line:
                lines.append(line)
                break
        for line in bmrbFileText:
            if Peak_char in line:
                k = 1
                if STOP in line and k == 1:
                    break
                lines.append(line)
    print(lines)
    return lines

def makeDataFrame(bmrbLines):
    ## create dataframe of interest using the same names as appear in the BMRB.
    # NB Columns are not always the same in number (E.G. fileA=10columns, fileB=12columns).
    table = []
    columns = []
    for i in [sub.splitlines() for sub in bmrbLines]:
        vv = [j.strip() for j in i if j]
        columns += [j for j in [i for i in vv if i.startswith('_')]]
        row = [j for i in [i.split(' ') for i in vv if not i.startswith('_')] for j in i if j]
        if len(row) > 0:
            table.append(row)
    shortColumns = [c.replace(_Atom_chem_shift, '') for c in columns]
    return pd.DataFrame(table, columns=shortColumns)


def makeCSLfromDF(df, chemicalShiftListName=None):
    """

    :param df: Pandas dataFrame
    :param chemicalShiftListName: str, default if None
    :return: Chemical Shift List Object
    """

    chemicalShiftList = project.newChemicalShiftList(name=chemicalShiftListName)

    nmrChain = project.fetchNmrChain()
    for index, row in df.iterrows():
        nmrResidue = nmrChain.fetchNmrResidue(residueType=row[Comp_ID], sequenceCode=row[Seq_ID])
        nmrAtom = nmrResidue.fetchNmrAtom(row[Atom_ID])
        if chemicalShiftList:
            if row[Val] is not None:
                cs = chemicalShiftList.newChemicalShift(value=float(row[Val]), nmrAtom=nmrAtom)
                if row[Val_err] is not None:
                    cs.valueError = float(row[Val_err])
    return chemicalShiftList


def _importAndCreateV3Objs(file):
    lines = _openBmrb(file)
    df = makeDataFrame(lines)
    with undoBlock():
        makeCSLfromDF(df)


#######################################
##############  GUI POPUP #############
#######################################

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showInfo
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog


class BMRBcslToV3(CcpnDialog):

    def __init__(self, parent=None, bmrbFilePath=None, directory=None,
                 title='Import CSL from BMRB (Pre-Alpha)', **kw):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)
        self.bmrbFilePath = bmrbFilePath or ''
        self.directory = directory or ''

        row = 0
        bmrbFileLabel = Label(self, text="BMRB File", grid=(row, 0))
        self.inputDialog = LineEditButtonDialog(self, textLineEdit=self.bmrbFilePath, directory=self.directory,
                                                grid=(row, 1))
        row += 1
        self.buttonList = ButtonList(self, ['Info', 'Cancel', 'Import'], [self._showInfo, self.reject, self._okButton],
                                     grid=(row, 1))

    def _showInfo(self):
        showWarning(Warnings, InfoMessage)

    def _okButton(self):
        bmrbFile = self.inputDialog.get()
        _openBmrb(mybmrb)
        self.accept()


############################################
##############  INIT the Macro  ############
############################################


if __name__ == "__main__":

    relativePath = os.path.join(mp, 'nmrStar3_1Examples')
    fileName = 'bmr5493.str'

    mybmrb = os.path.join(relativePath, fileName)  # if not using UI:  replace with the full bmrb file path  of interest
    if _UI:
        popup = BMRBcslToV3(bmrbFilePath=mybmrb, directory=relativePath)
        popup.show()
        popup.raise_()
    else:
 #       _importAndCreateV3Objs(mybmrb)
        _openBmrb(mybmrb)