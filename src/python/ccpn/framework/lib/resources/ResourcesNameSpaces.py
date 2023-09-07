"""
A module to handle Reference ChemicalShifts loaded from disk as JSON files.
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Luca Mureddu $"
__dateModified__ = "$dateModified: 2023-09-07 17:23:47 +0100 (Thu, September 07, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-08-30 15:14:00 +0100 (Wed, August 30, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.util.DataEnum import DataEnum


INSTALLATION =  'installation'
EXTERNAL =  'external'
INTERNAL =  'internal'
PROJECT =  'project'

class ResourcesLoadingLevel(DataEnum):
    """
    Define the order and description of a Resource loader
    """
    INSTALLATION    = 0, INSTALLATION
    EXTERNAL           = 1, EXTERNAL
    INTERNAL            = 2, INTERNAL
    PROJECT             = 3, PROJECT
    

###########################################
######## ---- ReferenceChemicalShifts ---- ########
###########################################

### _metaData Level
TITLE = 'title'
COMMENT = 'comment'

PROTEIN = 'Protein'
DNA = 'DNA'
RNA = 'RNA'
FUNCTIONALGROUP = 'FunctionalGroup'
SMALLMOLECULE = 'SmallMolecule'
VERSION = 1.0

### residues level

RESIDUEOBJ = 'residueObject'
MOLECULETYPE = 'moleculeType'
RESIDUES = 'residues'
RESIDUENAME = 'residueName'
SHORTNAME = 'shortName'
CCPCODE = 'ccpcode'
ATOMS = 'atoms'

### Atoms level
ATOMOBJ = 'atomObject'
ATOMNAME = 'atomName'
ELEMENT = 'element'
AVERAGESHIFT = "averageShift"
MINSHIFT = "minShift"
MAXSHIFT= "maxShift"
SHIFTRANGES= "shiftRanges"
STDSHIFT = "stdShift"
DISTRIBUTION = 'distribution'
DISTRIBUTIONREFVALUE = 'distributionRefValue'
DISTRIBUTIONVALUEPERPOINT = 'distributionValuePerPoint'
PPMARRAY = 'ppmArray'
INTENSITIESARRAY = 'intensitiesArray'
