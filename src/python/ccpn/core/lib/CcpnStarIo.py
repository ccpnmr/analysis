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

def makeCSLfromDF(project, df, chemicalShiftListName=None):
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


def _simulatedSpectrumFromCSL(project, csl, axesCodesMap):
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

def _importAndCreateV3Objs(project, file, acMap):
   lines = _openBmrb(file)
   df = makeDataFrame(lines)
   with undoBlock():
       csl = makeCSLfromDF(project, df)
       _simulatedSpectrumFromCSL(project, csl, axesCodesMap=acMap)

