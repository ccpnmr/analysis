"""
BMRB Chemical Shift List Importer from NMR-STAR v3.1.
This is not a full BMRB importer to Analysis V3.
Please, read warnings and info message

Usage:
    UI
    - Menu Menus > Macro > Run... > Select this file.py
    - select BMRB file  of interest
    - select entries
    - Create
    Non-UI:
    - scroll down to "Init the macro section"
    - replace filename path
    - run the macro within V3

1) Menu Menus > Macro > Run... > Select this file.py
2) Menu Menus > View PythonConsole (space-space)
                %run -i your/path/to/this/file.py (without quotes)

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:21 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b5 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca M $"
__date__ = "$Date: 2019-06-12 10:28:40 +0000 (Wed, Jun 12, 2019) $"
#=========================================================================================
# Start of code
#=========================================================================================

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

_Atom_chem_shift = "_Atom_chem_shift." # used to find the loop of interest in the BMRB and shorten the column header name on the DataFrame

# only the entries of interest to map to CcpNmr V3 objects. Can be increased as needed
ID = "ID"
Seq_ID = "Seq_ID"
Comp_ID = "Comp_ID"
Atom_ID = "Atom_ID"
Atom_type = "Atom_type"
Val = "Val"
Val_err = "Val_err"
Details = "Details"
STOP = "stop_"
Atom_chem_shift = _Atom_chem_shift+ID

# NOT IN USE, just to map BMRB nomenclature to V3
# V3_BMRB_map = {
#                 "residueType"  : Comp_ID,  # nmrResidue, e.g. ALA
#                 "sequenceCode" : Seq_ID,   # nmrResidue, e.g. 1
#                 "name"         : Atom_ID,  # nmrAtom,    e.g. HA
#                 "position"     : Val,      # peak,       always ppm value !?
#                }

def _openBmrb(filePath):
    # HardCoded bit to find just the Chemical Shifts, Replace with NEF Style
    lines = []
    with open (filePath, "r") as bmrbFileText:
        for line in bmrbFileText:
            if Atom_chem_shift in line:
                lines.append(line)
                break
        for line in bmrbFileText:
            if STOP in line:
                break
            lines.append(line)
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
        if len(row)>0:
            table.append(row)
    shortColumns = [c.replace(_Atom_chem_shift,'') for c in columns]
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

    def __init__(self, parent=None, bmrbFilePath = None, directory=None,
                 title='Import CSL from BMRB (Pre-Alpha)', **kw):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)
        self.bmrbFilePath = bmrbFilePath or ''
        self.directory = directory or ''

        row = 0
        bmrbFileLabel = Label(self, text="BMRB File", grid=(row, 0))
        self.inputDialog = LineEditButtonDialog(self,textLineEdit=self.bmrbFilePath, directory=self.directory, grid=(row, 1))
        row += 1
        self.buttonList = ButtonList(self, ['Info','Cancel', 'Create'], [self._showInfo, self.reject, self._okButton], grid=(row, 1))

    def _showInfo(self):
        showWarning(Warnings, InfoMessage)

    def _okButton(self):
        bmrbFile = self.inputDialog.get()
        _importAndCreateV3Objs(bmrbFile)
        self.accept()



############################################
##############  INIT the Macro  ############
############################################


if __name__ == "__main__":

    relativePath = os.path.join(mp, 'nmrStar3_1Examples')
    fileName = 'bmr5493.str'

    mybmrb = os.path.join(relativePath, fileName) # if not using UI:  replace with the full bmrb file path  of interest
    if _UI:
        popup = BMRBcslToV3(bmrbFilePath=mybmrb, directory=relativePath)
        popup.show()
        popup.raise_()
    else:
        _importAndCreateV3Objs(mybmrb)