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
__dateModified__ = "$dateModified: 2023-09-04 15:09:04 +0100 (Mon, September 04, 2023) $"
__version__ = "$Revision: 3.2.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-08-30 15:14:00 +0100 (Wed, August 30, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from collections import Counter, OrderedDict, defaultdict
from ccpn.util.traits.CcpNmrJson import CcpNmrJson, CcpnJsonDirectoryABC
from ccpn.util.traits.CcpNmrTraits import Unicode, Int, Float, Bool, RecursiveList, List, Tuple, CTuple
from ccpn.framework.PathsAndUrls import ccpnResourcesPath, ccpnResourcesChemicalShifts
from ccpn.util.decorators import singleton
from ccpn.util.Path import aPath
import glob, os

PROTEIN = 'Protein'
DNA = 'DNA'
RNA = 'RNA'
FUNCTIONALGROUP = 'FunctionalGroup'
SMALLMOLECULE = 'SmallMolecule'
VERSION = 1.0

### _metaData Level
TITLE = 'title'
COMMENT = 'comment'

### residues level
MOLECULETYPE = 'moleculeType'
RESIDUES = 'residues'
RESIDUENAME = 'residueName'
SHORTNAME = 'shortName'
CCPCODE = 'ccpcode'
ATOMS = 'atoms'

### Atoms level
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

class AtomChemicalShift(CcpNmrJson):
    """Class to store ReferenceChemicalShift information for a single Atom
    """
    classVersion = VERSION
    saveAllTraitsToJson = True
    atomName =  Unicode(allow_none=False, default_value='??').tag(info='The atomName identifier, e.g. H1, etc')
    element =  Unicode(allow_none=False, default_value='??').tag(info='The element identifier, e.g. H, etc')
    averageShift =  Float(allow_none=True, default_value=0.0).tag(info='The average Chemical Shift in ppm.')
    stdShift =  Float(allow_none=True, default_value=0.0).tag(info='The std Shift')
    minShift =  Float(allow_none=True, default_value=0.0).tag(info='')
    maxShift =  Float(allow_none=True, default_value=0.0).tag(info='')
    distributionRefValue =  Float(allow_none=True, default_value=0.0).tag(info='')
    distributionValuePerPoint =  Float(allow_none=True, default_value=0.0).tag(info='')
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

    @property
    def title(self):
        return self._metadata.get('title')

    @property
    def comment(self):
        return self._metadata.get('comment')

    def __repr__(self):
        # Nothing funcy. keep simple
        return f'{self.__class__.__name__}("{self.shortName}")'

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

class _ReferenceChemicalShiftsLoader(_ReferenceChemicalShiftsABC):
    directory = aPath(ccpnResourcesChemicalShifts)
    recursive = True
    extension = '.json'
    searchPattern = str(aPath('**') / '*.json') # recursive search in all subdirectories

@singleton
class ReferenceChemicalShifts(OrderedDict):
    """
    Class to handle all the ReferenceChemicalShifts .

    """
    _registeredClasses = set()

    def __init__(self):
        super().__init__()
        self._initTraits()
        self._activeChemicalShifts = []

    def activeChemicalShifts(self):
        return self._activeChemicalShifts

    def setActiveChemicalShifts(self, activeChemicalShifts):
        """ Filter the ReferenceChemicalShifts  by conditions and set as active for all the ongoing calculations"""
        self._activeChemicalShifts = activeChemicalShifts

    def getByMoleculeType(self, moleculeType:str):
        """
        Filter all ReferenceChemicalShifts by a given  moleculeType.
        :param moleculeType: str. case-sensitive
        """
        availableMolTypes = self._getAvailableMolTypes()
        if moleculeType not in availableMolTypes:
            msg = f'''Cannot filter ReferenceChemicalShifts by the given moleculeType: "{moleculeType}". Use one of the available: {", ".join(availableMolTypes)}. Case-sensitive'''
            raise ValueError(msg)
        return self.filterBySingleCondition('moleculeType', moleculeType)

    def groupByTitle(self, filteringObjects=None):
        groups = defaultdict(list)
        filteringObjects = filteringObjects or self.values()
        for obj in filteringObjects:
            groups[obj.title].append(obj)
        return groups

    def filterBySingleCondition(self, theProperty, condition, filteringObjects=None):
        """
        Find all ReferenceChemicalShifts that have a property that matches a given condition. E.g.: residueName named 'Valine'.
        :param theProperty: str. attribute of the ReferenceChemicalShift. Eg. residueName, shortName, ccpcode, moleculeType
        :param condition: str, float, int
        :param filteringObjects: list of ReferenceChemicalShift objects. If None, use all available. Default
        :return:  list of ReferenceChemicalShift objects
        """
        filteringObjects = filteringObjects or self.values()
        return [obj for obj in filteringObjects if getattr(obj, theProperty, None) == condition ]

    def filterByMultipleCondition(self, titles, moleculeTypes, filteringObjects=None,):
        """
        Find all ReferenceChemicalShifts that have a property that matches a given condition. E.g.: moleculeTypes = ['Protein', 'DNA']
        titles = ['Protein', 'MyCustomTitle']
        :return:  list of ReferenceChemicalShift objects
        """
        filteringObjects = filteringObjects or self.values()

        values = set()
        for obj in filteringObjects:
            if obj.title in titles and obj.moleculeType in moleculeTypes:
                values.add(obj)
        return list(values)

    def _getAvailableMolTypes(self):
        availableMolTypes = set()
        for obj in self.values():
            availableMolTypes.add(obj.moleculeType)
        return list(availableMolTypes)


    ############# Core Registration Methods ##############

    def _initTraits(self):
        """Update the trait objects read from file to the class """
        for cls in self._registeredClasses:
            obj = cls()
            self.update(obj)

    @staticmethod
    def register(cls):
        """When registered from a Plugin at run-time, you also need to run refreshObjects """
        ReferenceChemicalShifts._registeredClasses.add(cls)



## Register the default distribution  ReferenceChemicalShifts
ReferenceChemicalShifts.register(_ReferenceChemicalShiftsLoader)

rcs = ReferenceChemicalShifts()

# results = rcs.filterBySingleCondition('residueName', 'Valine')
# results = rcs.filterByMultipleCondition(titles=[RNA, DNA], moleculeTypes=[RNA, DNA])
# print(results)
# print(len(rcs))

