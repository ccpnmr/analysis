############## ========= Developing  MACRO ========= #########################
'''
This macro reads a peakList file (E.G. nh.list.workshop) with assignment from a Sparky project.
Converts in a dataFrame
Splits the Assignment column from type S1990N-H to four columns to type S 1990 N H



'''

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
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:25 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2017-05-28 10:28:42 +0000 (Sun, May 17, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================


import pandas as pd
import re


columns = ['ResidueType', 'ResidueCode', 'FirstAtomName', 'SecondAtomName']


def _createDataFrame(input_path):
    return pd.read_table(input_path, delim_whitespace=True, )


def _splitAssignmentColumn(dataFrame):
    ''' parses the assignment column.
    Splits the column assignment in  four columns: ResidueName ResidueCode AtomName1 AtomName2.
    '''
    assignments = [re.findall('\d+|\D+', s) for s in dataFrame.iloc[:, 0]]
    assignmentsColumns = []
    for a in assignments:
        i, j, *args = a
        atoms = (''.join(args)).split('-')
        if len(atoms) == 2:
            firstAtom, secondAtom = atoms
            assignmentsColumns += ((i, j, firstAtom, secondAtom),)
    return pd.DataFrame(assignmentsColumns, columns=columns)


def _mergeDataFrames(generalDF, assignmentDF):
    '''
    :param generalDF: first dataframe with assignments all in on column
    :param assignmentDF: assignments dataframe  in  4 columns
    :return: new dataframe with four assignment columns + the original without the first column
    '''
    partialDf = generalDF.drop(generalDF.columns[0], axis=1)
    return pd.concat([assignmentDF, partialDf], axis=1, join_axes=[partialDf.index])


def _correctChainResidueCodes(chain, ccpnDataFrame):
    ''' renames Chain residueCodes correctly according with the dataFrame, if duplicates, deletes them.
    '''
    for residue, resNumber, in zip(chain.residues, ccpnDataFrame.ResidueCode):
        try:
            residue.rename(str(resNumber))
        except:
            residue.delete()
    return chain


def _createCcpnChain(project, ccpnDataFrame):
    '''makes a chain from the ResidueTypes.
    CCPN wants a long list of  one Letter Codes without spaces'''
    residueTypes = ''.join([i for i in ccpnDataFrame.ResidueType])
    newChain = project.createChain(residueTypes, molType='protein')
    _correctChainResidueCodes(newChain, ccpnDataFrame)
    return newChain


def _fetchAndAssignNmrAtom(peak, nmrResidue, atomName):
    atom = nmrResidue.fetchNmrAtom(name=str(atomName))
    peak.assignDimension(axisCode=atomName[0], value=[atom])


def _connectNmrResidues(nmrChain):
    updatingNmrChain = None
    nrs = nmrChain.nmrResidues
    for i in range(len(nrs) - 1):
        currentItem, nextItem = nrs[i], nrs[i + 1]
        if currentItem or nextItem is not None:
            updatingNmrChain = currentItem.connectNext(nextItem, )
    return updatingNmrChain


def _assignNmrResiduesToResidues(connectedNmrChain, ccpnChain):
    for nmrResidue, residue in zip(connectedNmrChain.nmrResidues, ccpnChain.residues):
        nmrResidue.residue = residue


def _parseDataFrame(ccpnDataFrame, spectrum, nmrChain):
    lastNmrResidue = None
    newPeakList = spectrum.newPeakList()
    foundResNumber = list(ccpnDataFrame.iloc[:, 1])
    for i, resType, resNumber, atom1, atom2, pos1, pos2, in zip(range(len(ccpnDataFrame.iloc[:, 0]) - 1), ccpnDataFrame.iloc[:, 0],
                                                                ccpnDataFrame.iloc[:, 1], ccpnDataFrame.iloc[:, 2],
                                                                ccpnDataFrame.iloc[:, 3], ccpnDataFrame.iloc[:, 4],
                                                                ccpnDataFrame.iloc[:, 5]):

        peak = newPeakList.newPeak(ppmPositions=(float(pos2), float(pos1)))

        if resNumber in foundResNumber[
                        :i]:  # in case of duplicated Residues Eg sideChain W2023N-H H and W2023NE1-HE1, don't need to create a new nmrResidue, just add the atoms to the previous one.
            nmrResidue = lastNmrResidue
            if nmrResidue:
                _fetchAndAssignNmrAtom(peak, nmrResidue, atom2)
                _fetchAndAssignNmrAtom(peak, nmrResidue, atom1)

        else:
            nmrResidue = nmrChain.fetchNmrResidue(sequenceCode=str(resNumber))
            lastNmrResidue = nmrResidue
            if nmrResidue:
                _fetchAndAssignNmrAtom(peak, nmrResidue, atom2)
                _fetchAndAssignNmrAtom(peak, nmrResidue, atom1)

    return nmrChain


def initParser(project, input_path, spectrum):
    generalDF = _createDataFrame(input_path)
    assignmentDF = _splitAssignmentColumn(generalDF)
    ccpnDataFrame = _mergeDataFrames(generalDF, assignmentDF)
    ccpnChain = _createCcpnChain(project, ccpnDataFrame)
    nmrChain = project.fetchNmrChain('A')
    newNmrChain = _parseDataFrame(ccpnDataFrame, spectrum, nmrChain)
    connectedNmrChain = _connectNmrResidues(newNmrChain)
    _assignNmrResiduesToResidues(connectedNmrChain, ccpnChain)


###### Initialise MACRO  ######

input_path = '/Users/luca/Desktop/masterClassProjects/Sparky/Lists/nh_tor_42.list.workshop'
initParser(project, input_path, project.spectra[-1])
