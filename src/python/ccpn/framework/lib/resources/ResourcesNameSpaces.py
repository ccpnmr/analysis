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
__dateModified__ = "$dateModified: 2023-09-15 14:18:06 +0100 (Fri, September 15, 2023) $"
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
VERSION = 1.0

### General terms and prefixes
PROTEIN = 'Protein'
DNA = 'DNA'
RNA = 'RNA'
FUNCTIONALGROUP = 'FunctionalGroup'
SMALLMOLECULE = 'SmallMolecule'
CHEMICALSHIFT = 'chemicalShift'
COMPOUND = 'compound'
ATOM = 'atom'

### Reference ChemicalShift level
CHEMICALSHIFTNAME = f'{CHEMICALSHIFT}Name'
CHEMICALSHIFTENTRYDATE = f'{CHEMICALSHIFT}EntryDate'
CHEMICALSHIFTCOMMENT = f'{CHEMICALSHIFT}Comment'
CHEMICALSHIFTYPE = f'{CHEMICALSHIFT}Type'

### Residue level
COMPOUNDOBJ = f'{COMPOUND}Object'
COMPOUNDTYPE = f'{COMPOUND}Type'
COMPOUNDS = f'{COMPOUND}s'
COMPOUNDNAME = f'{COMPOUND}Name'
SHORTNAME = f'{COMPOUND}ShortName'
CCPCODE = f'{COMPOUND}Ccpcode'
PRECURSOR = f'{COMPOUND}PrecursorName'
COMPOUNDCLASSIFICATION = f'{COMPOUND}TypeClassification'
ATOMS = 'atoms'

### Atom level
ATOMOBJ = 'atomObject'
ATOMNAME = f'{ATOM}Name'
ELEMENT = f'{ATOM}ElementName'
AVERAGESHIFT = f'{ATOM}AverageShift'
STDSHIFT = f'{ATOM}StdShift'
MINSHIFT = f'{ATOM}MinShift'
MAXSHIFT= f'{ATOM}MaxShift'
DISTRIBUTION = f'{ATOM}StatisticalDistribution'
DISTRIBUTIONREFVALUE = f'{ATOM}DistributionRefValue'
DISTRIBUTIONVALUEPERPOINT =  f'{ATOM}DistributionValuePerPoint'
PPMARRAY =  f'{ATOM}DistributionPpmArray'
INTENSITIESARRAY = f'{ATOM}DistributionIntensitiesArray'
