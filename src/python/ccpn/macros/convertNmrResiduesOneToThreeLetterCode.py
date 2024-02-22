#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Joanna Fox, Morgan Hayward, Victoria A Higman, Luca Mureddu",
               "Eliza Płoskoń, Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2024-02-22 15:58:35 +0000 (Thu, February 22, 2024) $"
__version__ = "$Revision: 3.2.2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2019-10-31 16:32:32 +0100 (Thu, Oct 31, 2019) $"
#=========================================================================================
__title__ = "Convert residues from one- to three-letter code"
# Start of code
#=========================================================================================


"""
This macro will convert the residue types of an NmrChain from One Letter code to Three Letter code using ChemComp
definitions.
Molecule Types: protein, DNA, RNA
"""

from ccpn.core.lib.ChainLib import SequenceHandler

def convertNmrChain1to3LetterCode(nmrChain, molType='protein'):
    """
    converts NmrResidues from 1 to 3 LetterCode.
    :param nmrChain: Ccpn object NmrChain
    :param molType: 'protein', 'DNA', 'RNA'
    :return:
    """
    project = nmrChain.project
    sequence = [nmrResidue.residueType for nmrResidue in nmrChain.nmrResidues]
    sequenceHandler = SequenceHandler(project, moleculeType=molType)
    sequence3LetterCodes = sequenceHandler.oneToThreeCode(sequence)

    for i, nmrResidue in enumerate(nmrChain.nmrResidues):
        if len(nmrResidue.residueType) == 1:
            newNmrResidueName = sequence3LetterCodes[i]
            try:
                nmrResidue.rename(nmrResidue.sequenceCode, newNmrResidueName)
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
