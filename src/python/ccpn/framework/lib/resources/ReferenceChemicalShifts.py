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
__dateModified__ = "$dateModified: 2023-08-31 18:07:20 +0100 (Thu, August 31, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-08-30 15:14:00 +0100 (Wed, August 30, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import Counter, OrderedDict
from ccpn.util.traits.CcpNmrJson import CcpNmrJson, CcpnJsonDirectoryABC
from ccpn.util.traits.CcpNmrTraits import Unicode, Int, Float, Bool, RecursiveList, List, Tuple, CTuple
from ccpn.framework.PathsAndUrls import ccpnResourcesPath, ccpnResourcesChemicalShifts
from ccpn.util.decorators import singleton
from ccpn.util.Path import aPath

_PROTEIN = 'protein'
_DNA = 'DNA'
_RNA = 'RNA'
_FUNCTIONALGROUPS = 'functionalGroups'
_SMALLMOLECULES = 'smallMolecules'
VERSION = 1.0

class AtomChemicalShift(CcpNmrJson):
    """Class to store ReferenceChemicalShift information for a single Atom
    """
    classVersion = VERSION
    saveAllTraitsToJson = True
    atomName =  Unicode(allow_none=False, default_value='??').tag(info='The atomName identifier, e.g. H1, etc')
    element =  Unicode(allow_none=False, default_value='??').tag(info='The element identifier, e.g. H, etc')
    averageShift =  Float(allow_none=False, default_value=0.0).tag(info='The average Chemical Shift in ppm.')
    stdShift =  Float(allow_none=False, default_value=0.0).tag(info='The std Shift')
    minShift =  Float(allow_none=False, default_value=0.0).tag(info='')
    maxShift =  Float(allow_none=False, default_value=0.0).tag(info='')
    distributionRefValue =  Float(allow_none=False, default_value=0.0).tag(info='')
    distributionValuePerPoint =  Float(allow_none=False, default_value=0.0).tag(info='')
    distribution =  List(default_value=[]).tag(info='')


    def __repr__(self):
        # Nothing funcy. keep simple
        return f'{self.__class__.__name__}("{self.atomName}")'

class ReferenceChemicalShift(CcpNmrJson):
    """Class to store ReferenceChemicalShift information for a residue
    """
    classVersion = VERSION
    saveAllTraitsToJson = True
    residueName =  Unicode(allow_none=False, default_value='??').tag(info='The full residueName identifier, e.g. Alanine, etc')
    shortName =  Unicode(allow_none=False, default_value='??').tag(info='The short Name identifier, e.g. ALA, etc')
    ccpcode =  Unicode(allow_none=False, default_value='??').tag(info='The ccpcode identifier, e.g. Ala, etc')
    moleculeType =  Unicode(allow_none=False, default_value='??').tag(info='The moleculeType identifier, e.g. Protein, etc')
    atoms = RecursiveList()

    def _setAtomTraits(self):
        atoms = []
        for atomDict in self.atoms:
            atomTrait = AtomChemicalShift()
            atomTrait.update(atomDict)
            atoms.append(atomTrait)
        self.update({'atoms': atoms})

    def __repr__(self):
        # Nothing funcy. keep simple
        return f'{self.__class__.__name__}("{self.residueName}")'

ReferenceChemicalShift.register()

class _ReferenceChemicalShiftsABC(CcpnJsonDirectoryABC):
    """
    Class to handle the ReferenceChemicalShifts from Json Files.
    --- Tree ---
        -- Residue:
            -- residueName: Alanine
            -- shortName: ALA
            -- ccpcode: Ala
            - Atoms:
                - atomName: H1
                - element: H
                - ...
    """
    attributeName = 'shortName'  # attribute of object whose value functions as the key to store the object
    directory = None

    def __init__(self):
        super().__init__()
        self._setAtomTraits()

    def _setAtomTraits(self):
        for k, res in self.items():
            res._setAtomTraits()

class _ReferenceChemicalShiftsProteinLoader(_ReferenceChemicalShiftsABC):
    title = 'Protein'
    directory = aPath(ccpnResourcesChemicalShifts / _PROTEIN )

class _ReferenceChemicalShiftsDNALoader(_ReferenceChemicalShiftsABC):
    title = 'DNA'
    directory = aPath(ccpnResourcesChemicalShifts / _DNA )

class _ReferenceChemicalShiftsRNALoader(_ReferenceChemicalShiftsABC):
    title = 'RNA'
    directory = aPath(ccpnResourcesChemicalShifts / _RNA )

@singleton
class ReferenceChemicalShifts(OrderedDict):
    """
    Class to handle all the ReferenceChemicalShifts .

    """
    _registeredClasses = set()

    def __init__(self):
        super().__init__()
        self._objs = []
        for cls in self._registeredClasses:
            obj = cls()
            self._objs.append(obj)
            self.update(obj)

    @staticmethod
    def register(cls):
        ReferenceChemicalShifts._registeredClasses.add(cls)

## Register the default distribution  ReferenceChemicalShifts
ReferenceChemicalShifts.register(_ReferenceChemicalShiftsProteinLoader)
ReferenceChemicalShifts.register(_ReferenceChemicalShiftsDNALoader)
ReferenceChemicalShifts.register(_ReferenceChemicalShiftsRNALoader)

