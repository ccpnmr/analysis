"""
A Pre-alpha BMRB Chemical Shift List Importer from NMR-STAR v3.1.
This is not a full BMRB importer to Analysis V3.
Please, read warnings and info message

Usage:
    - Menu Menus > Macro > Run... > Select this file.py
    - select BMRB file  of interest
    - select entries
    - Create (click/read info more)


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



Warnings = "Warning: This is only a Pre-alpha BMRB Importer. It might not work or work partially. Always inspect the results!"

InfoMessage = """
        This popup will create a new chemical shift list from the NMR-STAR v3.1 file selected.
        A new simulated Spectrum from the selected axesCodes and new simulated peakList from the selected BMRB Atom_ID. 
        Once the new assigned peaks are correctly imported, copy the new peakList to your target spectrum.
        
        >>> BMRB Atom_ID: Insert the NmrAtom which you want to import as appears in the BMRB file, comma separated. 
            You will find these on the "Assigned chemical shift lists" table in the BMRB 3.1 Star file as:
             _Atom_chem_shift.Atom_ID e.g. CA or HA 

        >>> Assign To Axis: Insert to which axis you want to assign the corresponding NmrAtom. 1:1
            These axes will be used to create a Simulated Spectrum. Specifying the axes is important for V3 for creating a new assignment,
             especially for ambiguous assignemnts: e.g   
             NmrAtom    -->   Axis Code
              HA        -->     H1
              HB        -->     H2

        
        Limitations: 
        - Import multiple combination of nmrAtoms for same axisCode. 
          Work-around: import twice.
          E.g. first H,N,CA after H,N,CB, copy the two peakList to the target spectrum
        - Peaks and assignments will be created only if all the selected nmrAtoms are present for the nmrResidue in the BMRB.
          E.g  if select Atom_ID: N,H for this BMRB entry:
          >>1 . 1 1   1   1 MET H  C 13  53.890 0.05 . 1 . . . . . . . . 5493 1 >> 
            4 . 1 1   2   2 ILE N  N 15 126.655 0.04 . 1 . . . . . . . . 5493 1
            5 . 1 1   2   2 ILE H  H  1  10.051 0.02 . 1 . . . . . . . . 5493 1
           The residue 1 MET will be skipped as only the Atom_ID H is found.  
            
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
#                 "residueType"  : Comp_ID,  # nmrResidue, E.G ALA
#                 "sequenceCode" : Seq_ID,   # nmrResidue, E.G 1
#                 "name"         : Atom_ID,  # nmrAtom,    E.G HA
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


def _simulatedSpectrumFromCSL(csl, axesCodesMap):
    """

    key= NmrAtom name as appears in the CSL ; value = AxisCode name to Assign to the Spectrum AxisCode
    E.G. use NmrAtom Ca from CSL (imported from BMRB) and assign to a peak with axisCode named C

    :param csl: chemicalShiftList Object
    :param axesCodesMap: Ordered Dict containing Atoms of interest and parallel Spectrum Axes Codes
    :return:
    """
    if csl is None:
        print("Provide a Chemical Shift List")
        return
    if axesCodesMap is None:
        print("Select NmrAtom to use and axis codes")
        return

    nmrAtomNames = list(axesCodesMap.keys())
    targetSpectrumAxCodes = list(axesCodesMap.values())
    targetSpectrum = project.createDummySpectrum(axisCodes=targetSpectrumAxCodes, name=None)#, chemicalShiftList=csl)
    peakList = targetSpectrum.peakLists[-1]

    # filter by NmrAtom of interest
    nmrResiduesOD = od()
    for chemicalShift in csl.chemicalShifts:
        na = chemicalShift.nmrAtom
        if na.name in nmrAtomNames:
            try:
                nmrResiduesOD[na.nmrResidue].append([na, chemicalShift.value])
            except KeyError:
                nmrResiduesOD[na.nmrResidue] = [(na, chemicalShift.value)]

    for nmrResidue in nmrResiduesOD:
        shifts = []
        atoms = []
        for v in nmrResiduesOD[nmrResidue]:
            atoms.append(v[0])
            shifts.append(v[1])

        targetSpectrumAxCodes = targetSpectrum.axisCodes
        axisCodes = [n.name for n in atoms]
        i = getAxisCodeMatchIndices(axisCodes,targetSpectrumAxCodes) # get the correct order.
        if len(i) != len(nmrAtomNames): #if not all the NmrAtoms are found for a specific CSL cannot make the peak, incomplete assignment/shifts
            print('Skipping, not enough information to create and assign peak for NmrResidue: %s' %nmrResidue)
            continue

        i = np.array(i)
        shifts = np.array(shifts)
        atoms = np.array(atoms)
        try: # trap unknown issues
            peak = peakList.newPeak(list(shifts[i]))
            for na, sa in zip(atoms[i],targetSpectrumAxCodes) :
                peak.assignDimension(sa, [na])
        except Exception as e:
            print('Error assigning NmrResidue %s , NmrAtoms: %s, Spectrum Axes: %s, Shifts: %s . Error: %s'
                  %(nmrResidue,atoms,targetSpectrumAxCodes,shifts, e))




#######################################
##############  GUI POPUP #############
#######################################

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.MessageDialog import showWarning, showInfo
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog


class BMRBcslToV3(CcpnDialog):

    def __init__(self, parent=None, axesCodesMap=None, bmrbFilePath = None, directory=None,
                 title='Import CSL from BMRB (Pre-Alpha)', **kw):
        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)
        self.bmrbFilePath = bmrbFilePath or ''
        self._axesCodesMap  = axesCodesMap or od() # Ordered dict as od([("HA","H")]) see info for more
        self.directory = directory or ''

        row = 0
        bmrbFileLabel = Label(self, text="BMRB File", grid=(row, 0))
        self.inputDialog = LineEditButtonDialog(self,textLineEdit=self.bmrbFilePath, directory=self.directory, grid=(row, 1))
        row +=1
        bmrbCodes = Label(self, text="BMRB Atom_ID", grid=(row,0))
        self.bmrbCodesEntry = LineEdit(self, text=','.join(self._axesCodesMap.keys()), grid=(row, 1))
        row += 1
        assignToSpectumCodes = Label(self, text="Assign To Axis", grid=(row,0))
        self.assignToSpectumCodes = LineEdit(self, text=','.join(self._axesCodesMap.values()), grid=(row, 1))
        row += 1
        self.buttonList = ButtonList(self, ['Info','Cancel', 'Create'], [self._showInfo, self.reject, self._okButton], grid=(row, 1))

    def _showInfo(self):
        showWarning(Warnings, InfoMessage)

    def _okButton(self):
        self._axesCodesMap.clear()
        bmrbFile = self.inputDialog.get()
        bmrbCodes = self.bmrbCodesEntry.get().replace(" ","").split(',')
        assignToSpectumCodes = self.assignToSpectumCodes.get().replace(" ","").split(',')
        for bmrbCode, sac in zip(bmrbCodes,assignToSpectumCodes):
          self._axesCodesMap[bmrbCode]=sac
        self._importAndCreateV3Objs(bmrbFile, self._axesCodesMap)
        self.accept()

    def _importAndCreateV3Objs(self, file, acMap):
       lines = _openBmrb(file)
       df = makeDataFrame(lines)
       with undoBlock():
           csl = makeCSLfromDF(df)
           _simulatedSpectrumFromCSL(csl, axesCodesMap=acMap)


if __name__ == "__main__":
    # from ccpn.ui.gui.widgets.Application import TestApplication
    # app = TestApplication()
    relativePath = os.path.join(mp, 'nmrStar3_1Examples')
    fileName = 'bmr5493.str'
    mybmrb = os.path.join(relativePath, fileName)
    exampleAxesCodesMap = od([
                            ("N", "N"),
                            ("H", "H"),
                            ("CA", "C"),
                            ])
    popup = BMRBcslToV3(axesCodesMap=exampleAxesCodesMap, bmrbFilePath=mybmrb, directory=relativePath)
    popup.show()
    popup.raise_()
    # app.start()