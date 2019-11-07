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
This macro will convert 

"""

Residues3Lett = {'CYS': 'C', 'ASP': 'D', 'SER': 'S', 'GLN': 'Q', 'LYS': 'K',
            'ILE': 'I', 'PRO': 'P', 'THR': 'T', 'PHE': 'F', 'ASN': 'N',
            'GLY': 'G', 'HIS': 'H', 'LEU': 'L', 'ARG': 'R', 'TRP': 'W', 'TER': '*',
            'ALA': 'A', 'VAL': 'V', 'GLU': 'E', 'TYR': 'Y', 'MET': 'M', 'XAA': 'X'}

Residues1Lett = {v: k for k, v in Residues3Lett.items()}

# Do this on every NmrChain in the project
for nmrChain in project.nmrChains:
    # Do this on every NmrResidue in the Chain
    for nmrRes in nmrChain.mainNmrResidues:
        temp = str(nmrRes)
        components = temp.split('.')
        components[2] = components[2][0:-1]
        if len(components[2]) == 1:
            components[2] = Residues1Lett.get(components[2])
        newName = '.'.join(components[1:])
        get(nmrRes.pid).rename(newName)

