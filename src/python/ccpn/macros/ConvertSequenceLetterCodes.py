"""
Converts a sequence from One Letter code to Three Letter code and vice-versa using ChemComp definitions.
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