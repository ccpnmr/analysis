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
__dateModified__ = "$dateModified: 2019-10-31 16:32:32 +0100 (Thu, Oct 31, 2019) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2019-10-31 16:32:32 +0100 (Thu, Oct 31, 2019) $"
#=========================================================================================
__title__ = "Convert residues from one- to three-letter code"
#=========================================================================================


"""
This macro will convert the residue types of an NmrChain from One Letter code to Three Letter code using ChemComp
definitions.
Molecule Types: protein, DNA, RNA
"""

def convertResidueCode(residueName, inputCodeType='oneLetter', outputCodeType='threeLetter', molType ='protein'):
    """
    :param inputCodeType: oneLetter, threeLetter, synonym, molFormula
    :type inputCodeType: str
    :param molType: 'protein', 'DNA', 'RNA'
    :type molType: str
    :return: the same residue with the new letter code/name
    :rtype: str
    """
    from ccpnmodel.ccpncore.lib.chemComp.ChemCompOverview import chemCompStdDict
    modes = ['oneLetter', 'threeLetter', 'synonym', 'molFormula'] # order as they come from ChemCom dictionary
    if inputCodeType not in modes or outputCodeType not in modes:
        print('Code type not recognised. It has to be one of: ', modes)
        return
    for k, v in chemCompStdDict.get(molType).items():
        dd = {i:j for i,j in zip(modes,v)}
        if residueName == dd.get(inputCodeType):
            return dd.get(outputCodeType)


def convertNmrChain1to3LetterCode(nmrChain, molType='protein'):
    """
    converts NmrResidues from 1 to 3 LetterCode.
    :param nmrChain: Ccpn object NmrChain
    :param molType: 'protein', 'DNA', 'RNA'
    :return:
    """
    for nmrResidue in nmrChain.nmrResidues:
        if len(nmrResidue.residueType) == 1:
            newNmrResidueName = convertResidueCode(nmrResidue.residueType, inputCodeType='oneLetter', outputCodeType='threeLetter', molType=molType)
            try:
                nmrResidue.rename('.'.join([nmrResidue.sequenceCode, newNmrResidueName]))
            except Exception as err:
                print('Error renaming NmrResidue %s.' %nmrResidue.pid, err)
        else:
            if not nmrResidue.residueType:
                print('Skipping... ResidueType not found for nmrResidue %s' %nmrResidue.pid)
            else:
                print('Skipping... Could not rename to 3 Letter code for nmrResidue %s' % nmrResidue.pid)


# Do this on every NmrChain in the project
for nmrChain in project.nmrChains:
    convertNmrChain1to3LetterCode(nmrChain)
