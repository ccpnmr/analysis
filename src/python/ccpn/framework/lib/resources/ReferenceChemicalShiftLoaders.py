"""
A module to handle Reference ChemicalShifts loaded from disk as JSON files.
"""
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
__dateModified__ = "$dateModified: 2024-01-09 15:28:43 +0000 (Tue, January 09, 2024) $"
__version__ = "$Revision: 3.2.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Luca Mureddu $"
__date__ = "$Date: 2023-08-30 15:14:00 +0100 (Wed, August 30, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.framework.lib.resources import ResourcesNameSpaces as rns
from ccpn.framework.lib.resources.ResourcesNameSpaces import ResourcesLoadingLevel
from ccpn.util.traits.CcpNmrJson import CcpNmrJson, CcpnJsonDirectoryABC
from ccpn.util.traits.CcpNmrTraits import Unicode, Int, Float, Bool, RecursiveList, List, Tuple, CTuple
from ccpn.framework.PathsAndUrls import ccpnResourcesChemicalShifts, userCcpnResourcesPath
from ccpn.util.Path import aPath
import numpy as np
from scipy.stats import norm

class AtomChemicalShift(CcpNmrJson):
    """Class to store ReferenceChemicalShift information for a single Atom
    """
    classVersion = rns.VERSION
    saveAllTraitsToJson = True

    atomName = Unicode(allow_none=False, default_value='??').tag(info='The atomName identifier, e.g.: H1, etc')
    atomElementName = Unicode(allow_none=False, default_value='??').tag(info='The element identifier, e.g.: H, etc')
    atomAverageShift = Float(allow_none=True, default_value=0.0).tag(info='The average Chemical Shift in ppm.')
    atomStdShift = Float(allow_none=True, default_value=0.0).tag(info='The std Shift')
    atomMinShift = Float(allow_none=True, default_value=0.0).tag(info='')
    atomMaxShift = Float(allow_none=True, default_value=0.0).tag(info='')
    atomDistributionRefValue = Float(allow_none=True, default_value=0.0).tag(info='')
    atomDistributionValuePerPoint = Float(allow_none=True, default_value=0.0).tag(info='')
    atomStatisticalDistribution = List(default_value=[]).tag(info='The probability distribution values at the various ppm observations.')
    _isIntensitiesReconstructed = False # False if the distribution definition is not given and the plottable intensitiesArray is reconstructed by the other definitions
    _defaultArrayLength = 100

    @property
    def ppmArray(self):
        """
        :return: A 1D array with a ppm Scale for plotting the Distribution intensities
        """
        return self._getPpmArray()

    @property
    def intensitiesArray(self):
        """
        :return: A 1D Probability density Distribution array for plotting the ReferenceChemicalShifts statistical observations.
        The distribution array is given by:
        1) json file definition "atomStatisticalDistribution"
        2) reconstructed as a Gaussian curve by the "minShift","maxShift", "averageShift" and "stdShift" definition of the json file.  AKA: Probability density function evaluated at the ppmArray
        3) flat line of zeros if not any of  "averageShift" and "stdShift" definition in the json file
        4) empty, if  the minimal information are not given ("minShift","maxShift" values)
        Options 2-4 will set the _isIntensitiesReconstructed to True
        """
        if len(self.atomStatisticalDistribution) > 0:
            return self.atomStatisticalDistribution
        else:
            _isIntensitiesReconstructed = True
            return self._getIntensitiesArray()

    # -------- Private methods -------- #

    def _getIntensitiesArray(self):
        ppmArray = self._getPpmArray()
        averageShift = self.atomAverageShift
        stdShift = self.atomStdShift
        length = len(ppmArray)
        if len(ppmArray) == 0: # empty, cannot do anything.  the minimal information are not given (min, max values)
            return ppmArray
        if not averageShift or not stdShift: # flat line
            distribution = np.zeros(length)
        else:
            distribution = norm.pdf(ppmArray, averageShift, stdShift) # Gaussian, a Probability density function evaluated at ppmArray
        return distribution

    def _getPpmArray(self):
        minShift = self.atomMinShift
        maxShift = self.atomMaxShift
        distribution = self.atomStatisticalDistribution
        if minShift is None:
            return np.array([])
        if maxShift is None:
            return np.array([])
        length = self._defaultArrayLength if len(distribution) == 0 else len(distribution)
        ppmDistribution = np.linspace(minShift, maxShift, length)
        return ppmDistribution

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.atomName}")'

AtomChemicalShift.register()

class ReferenceChemicalShift(CcpNmrJson):
    """Class to store ReferenceChemicalShift information for a compound
    """
    classVersion = rns.VERSION
    saveAllTraitsToJson = True
    chemicalShiftName = Unicode(allow_none=False, default_value='??').tag(info='')
    chemicalShiftComment = Unicode(allow_none=False, default_value='??').tag(info='')
    chemicalShiftEntryDate = Unicode(allow_none=True, default_value='??').tag(info='')
    compoundName = Unicode(allow_none=False, default_value='??').tag(info='The full compoundName identifier, e.g.: Alanine, etc')
    compoundShortName = Unicode(allow_none=False, default_value='??').tag(info='The short Name identifier, e.g.: ALA, etc')
    compoundCcpCode = Unicode(allow_none=False, default_value='??').tag(info='The ccpcode (ChemComp) identifier, e.g.: Ala, etc')
    compoundType = Unicode(allow_none=False, default_value='??').tag(info='The moleculeType identifier, e.g.: Protein, etc')
    compoundTypeClassification = Unicode(allow_none=True, default_value='??').tag(info='The moleculeType classification, e.g.: Peptide linking, etc')
    compoundPrecursorName = Unicode(allow_none=True, default_value='??').tag(info='Usually used for Non-Standards. The full precursor or parent compound name, e.g.: Alanine, for a the ALPHA-AMINOBUTYRIC ACID ')
    loadingLevel = Int(allow_none=False, default_value='??').tag(info='The loading source level. e.g.: 0 for distribution, 1 for internal, 2 for project. Set automatically, not read from json ')
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
        return f'{self.__class__.__name__}("{self.chemicalShiftName}:{self.compoundType}-{self.compoundCcpCode}")'

ReferenceChemicalShift.register()

class _ReferenceChemicalShiftsABC(CcpnJsonDirectoryABC):
    """
    Class to handle the loading of ReferenceChemicalShifts from Json Files.
        -- compound (trait):
            -- chemicalShiftName: CCPN V3 Default Protein
            -- compoundName: Alanine
            -- ...
            - Atoms (traits):
                - atomName: H1
                - ...
    """
    attributeName = rns.SHORTNAME  # attribute of object whose value functions as the key to store the object
    directory = None
    recursive = True
    extension = '.json'
    searchPattern = str(aPath('**') / '*.json') # recursive search in all subdirectories
    loadingLevel = ResourcesLoadingLevel.EXTERNAL

    def __init__(self):
        super().__init__() # will trigger the loading from super class
        self._setAtomTraits()
        self._setLoadingLevel()

    def _setAtomTraits(self):
        """ Recursively load any AtomTrait in the main objects"""
        for k, res in self.items():
            res._setAtomTraits()

    def _setLoadingLevel(self):
        """ set the _setLoadingLevel to each element"""
        for k, res in self.items():
            res.loadingLevel = self.loadingLevel.value

class _DefaultReferenceChemicalShiftsLoader(_ReferenceChemicalShiftsABC):
    loadingLevel = ResourcesLoadingLevel.INSTALLATION
    directory = aPath(ccpnResourcesChemicalShifts)

class _InternalReferenceChemicalShiftsLoader(_ReferenceChemicalShiftsABC):
    loadingLevel = ResourcesLoadingLevel.INTERNAL
    directory = aPath(userCcpnResourcesPath)

class _ProjectReferenceChemicalShiftsLoader(_ReferenceChemicalShiftsABC):
    loadingLevel = ResourcesLoadingLevel.PROJECT
    directory = None # added at runtime

class _ExternalReferenceChemicalShiftsLoader(_ReferenceChemicalShiftsABC):
    """ Subclass this in a plugin to add custom ReferenceChemicalShiftsLoaders """
    loadingLevel = ResourcesLoadingLevel.EXTERNAL
    directory = None #  ==> Mandatory <== added in subclassed plugin  #


## An example of custom External usage:
'''class MyChemicalShiftsLoader(_ExternalReferenceChemicalShiftsLoader):
    """ Custom ReferenceChemicalShiftsLoaders which load Protein ReferenceChemicalShifts """
    directory = aPath('path/to/myChemicalShifts/') # ==> Mandatory in subclass

class MyPlugin():
    def __init__(self, *args, **kwargs):
        ## Register the new referenceChemicalShifts
        self.application = getApplication()
        referenceChemicalShifts = self.application.resources.referenceChemicalShifts
        referenceChemicalShifts.register(MyChemicalShiftsLoader)
        referenceChemicalShifts._activateChemicalShiftName('Protein', 'MyProteinChemicalShifts')
        
'''
