"""Module Documentation here

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
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2019-06-12 10:28:40 +0000 (Wed, Jun 12, 2019) $"
#=========================================================================================
# Start of code
#=========================================================================================



import pandas as pd
import os
import glob
import numpy as np
from collections import OrderedDict as od
from ccpn.util.Common import getAxisCodeMatchIndices
from ccpn.framework.PathsAndUrls import macroPath as mp
from ccpn.core.lib.ContextManagers import undoBlock

StarPath = 'nmrStar3_1Examples'
BmrbPath = os.path.join(mp, StarPath)



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
    ac = {
        "H":"H",
        "N":"N",
        "Ca":"C"
        }

    key= NmrAtom name as appears in the CSL ; value = AxisCode name to Assign to the Spectrum AxisCode
    E.G. use NmrAtom Ca from CSL (imported from BMRB) and assign to a peak with axisCode named C

    :param csl: chemicalShiftList Object
    :param nmrAtomNames: tuple of str containing Atoms of interest
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
            print('Error assigning NmrResidue %s . %s1' %(nmrResidue,e))


#
acMap = od([
            ("H", "H"),
            ("HA", "H1")]
            )

mybmrb = '/Users/luca/AnalysisV3/src/python/ccpn/macros/nmrStar3_1Examples/test2'
lines = _openBmrb(mybmrb)
df = makeDataFrame(lines)
with undoBlock():
    csl = makeCSLfromDF(df, chemicalShiftListName='')
    _simulatedSpectrumFromCSL(csl, axesCodesMap=acMap)


