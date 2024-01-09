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

from collections import OrderedDict, defaultdict
import pandas as pd
from ccpn.util.Logging import getLogger
from ccpn.util.OrderedSet import OrderedSet
from ccpn.framework.lib.resources import ResourcesNameSpaces as rns

class ReferenceChemicalShifts(object):
    """
    Class to handle all the ReferenceChemicalShifts.
    usage:
    To get this object at runtime:
            referenceChemicalShifts = application.resources.referenceChemicalShifts

    For complex data queries: use the built-in methods getBy which returns a dataFrame representation and can be further filtered as a pipeline.
    See the classes in resources/ReferenceChemicalShiftLoaders for the various properties.

        e.g.:
        - get all data by the "DNA" moleculeType:
            data =  referenceChemicalShifts.dataFrame
            dnaData = referenceChemicalShifts.getBy(dataFrame=data, theProperty='compoundType', values=['DNA'])
        - keep filtering by "C" atomName:
            dnaData = referenceChemicalShifts.getBy(dataFrame=dnaData, theProperty='atomName', values=['P'])
        - keepFiltering by stdShift:
            dnaData = referenceChemicalShifts.getByRange(dataFrame=dnaData, theProperty='stdShift',  minValue=2, maxValue=5)

    """
    _registeredClasses = OrderedSet()

    def __init__(self):
        super().__init__()
        self._objsByClass = {} # used to load/unload objects
        self._registerCcpnReferenceChemicalShiftLoaders()
        self._dataFrame = self._buildDataFrame()

        ##  active ChemicalShifts names used to fetch directly the residues information
        self._proteinChemicalShiftName = rns.PROTEIN
        self._DNAChemicalShiftName = rns.DNA
        self._RNAChemicalShiftName = rns.RNA

    @property
    def dataFrame(self):
        """
        :return: Pandas DataFrame.  All information regarding residues and atoms in a flat dataFrame object
        """
        return self._dataFrame

    def getBy(self, dataFrame, theProperty, values):
        """
        :param dataFrame: the dataFrame containing all data
        :param theProperty: the ReferenceChemicalShift property to filter, can be a residue or atom property.
        :param values: the querying values
        :return: a filtered dataFrame

        Usage:
           - get all data by the "DNA" moleculeType:
            data =  referenceChemicalShifts.dataFrame
            dnaData = referenceChemicalShifts.getBy(dataFrame=data, theProperty='moleculeType', values=['DNA'])
        """
        if theProperty not in self.dataFrame.columns:
            raise ValueError(f"ReferenceChemicalShifts getBy error. Value: {theProperty} not defined in the data structure")
        df = self._getDFforValues(dataFrame, values=values, headerName=theProperty)
        return df

    def getByRange(self, dataFrame, theProperty, minValue, maxValue, minIncluded=True, maxIncluded=True):
        """
        :param dataFrame: the dataFrame containing all data
        :param theProperty:  str. the ReferenceChemicalShift property to filter.  Can be a residue or atom property.
        :param minValue: int or float. The filtering condition
        :param maxValue:  int or float.  The filtering condition
        :param minIncluded: bool. whether  to include the minValue in the filtering results
        :param maxIncluded:  whether  to include the maxValue in the filtering results
        :return: a filtered dataFrame
        Usage:
           - get all data with an averageShift between 3-5 ppm:
            data =  referenceChemicalShifts.dataFrame
            result = referenceChemicalShifts.getByRange(dataFrame=dnaData, theProperty='averageShift',  minValue=3, maxValue=5)
        """
        if theProperty not in self.dataFrame.columns:
            raise ValueError(f"ReferenceChemicalShifts getBy error. Value: {theProperty} not defined in the data structure")
        df =  self._getDFByRange(dataFrame, theProperty, minValue, maxValue, minIncluded=minIncluded, maxIncluded=maxIncluded)
        return df

    @property
    def protein(self):
        proteinData = self.getBy(dataFrame=self.dataFrame, theProperty=rns.COMPOUNDTYPE, values=[rns.PROTEIN])
        proteinData = self.getBy(dataFrame=proteinData, theProperty=rns.CHEMICALSHIFTNAME, values=[self._proteinChemicalShiftName])
        shortnames = proteinData[rns.SHORTNAME].values
        objs = proteinData[rns.COMPOUNDOBJ].values
        results = dict(zip(shortnames, objs))
        return results

    def _activateChemicalShiftName(self, moleculteType, name):
        """
        Set the ChemicalShift Name to be used as the active List.
        This is used when multiple ReferenceChemicalShifts for the same moleculeType are available.
        Example if a user includes new resources in a personal project/internal or via a plugin.
        :param name: str. The name for the available ReferenceChemicalShift
        :return: None
        """
        # need to do error checkings
        if moleculteType == rns.PROTEIN:
            self._proteinChemicalShiftName = name
            self._updateREFDB_fromApplication()
        elif moleculteType == rns.DNA:
            self._DNAChemicalShiftName = name
        elif moleculteType == rns.RNA:
            self._RNAChemicalShiftName = name
        else:
            getLogger().warning(f'Molecule type not yet available. Cannot set {name} to {moleculteType} ')

    ## -------- Private Methods -------- ##

    def _getAvailableMolTypes(self):
        return self.dataFrame.moleculeType.unique()

    @staticmethod
    def _getDFforValues(df, values, headerName):
        df = df.copy()
        return df[df[headerName].isin(values)]

    @staticmethod
    def _getDFByRange(df, theProperty, minValue, maxValue, minIncluded=True, maxIncluded=True):
        df = df.copy()
        try:
            cond1 = '>=' if minIncluded else '>'
            cond2 = '<=' if maxIncluded else '<>>'
            df = df[df.eval(f"{theProperty} {cond1} {minValue} & {theProperty} {cond2} {maxValue}")]
        except Exception as err:
            getLogger().warning(f"Cannot filter by range. {err}")
            df = pd.DataFrame()
        return df

    def _buildDataFrame(self):
        """
        Create a flat dataframe for all the traits definition. 1 Row per Atom.
        Each Colum is exactly the same as the Trait Object property for Residue and Atom
        :return: pandas DataFrame
        """
        data = defaultdict(list) # construct the data in a default dict instead of a normal dict for accommodating  duplicated key values etc
        for loaderClass, loader in self._objsByClass.items():
            for shortName, residueTrait in loader.items():
                residueDict = residueTrait.asDict()
                atoms = residueDict.pop(rns.ATOMS)
                for atomTrait in atoms:
                    for rk, rv in residueDict.items():
                        data[rk].append(rv)
                    # build atoms
                    atomDict = atomTrait.asDict()
                    for k, v in atomDict.items():
                        data[k].append(v)
                    data[rns.PPMARRAY].append(atomTrait.ppmArray)
                    data[rns.INTENSITIESARRAY].append(atomTrait.intensitiesArray)
                    data[rns.COMPOUNDOBJ].append(residueTrait)
        df = pd.DataFrame(data)
        return df


    # Internal

    def _updateREFDB_fromApplication(self):
        """
        This routine is meant to be a temporary solution until we finally remove the hardcoded REFDB_SD_MEAN in
        cpnmodel.ccpncore.lib.assignment.ChemicalShift.
        Update the REFDB  from the registered resources/ReferenceChemicalShifts loaded from Json files
        """
        from ccpnmodel.ccpncore.lib.assignment.ChemicalShift import REFDB_SD_MEAN
        referenceChemicalShifts = self.protein
        for key, atomsDict in REFDB_SD_MEAN.items():
            moleculeType, shortName = key
            ## New Application referencing
            residue = referenceChemicalShifts.get(shortName.upper())
            if residue is None:
                continue
            for atom in residue.atoms:
                atomName = atom.atomName
                averageShift = atom.atomAverageShift
                stdShift = atom.atomStdShift
                # Update the Old REFDB from the new References
                values = atomsDict.get(atomName)
                if values is None:
                    continue
                mean, sd, probabilityOfMissing, directlyBoundAtom = values
                newValues = (averageShift, stdShift, probabilityOfMissing, directlyBoundAtom)
                atomsDict[atomName] = newValues
        return

    ############# Core Registration Methods ##############

    def register(self, theClass, loadObjects=True):
        """"""
        self._registeredClasses.add(theClass)
        if loadObjects:
            obj = theClass()
            self._objsByClass[theClass] = obj
            self._dataFrame = self._buildDataFrame()

    def deregister(self, theClass, unloadObjects=True):
        """ remove the registered class and unload the RCS. E.g. done when switching projects.
        """
        if theClass not in self._registeredClasses:
            getLogger().debug(f'Cannot deregister {theClass} from {self.__class__.__name__}. Value not in the _registeredClasses.')
            return
        self._registeredClasses.pop(theClass)
        if unloadObjects:
            obj = self._objsByClass.pop(theClass, {})
            self._dataFrame = self._buildDataFrame()

    def _registerCcpnReferenceChemicalShiftLoaders(self):
        """ Register the default ReferenceChemicalShifts available in the installation and internal (~/.ccpn/resources) """
        if len(self._registeredClasses) == 0:
            from ccpn.framework.lib.resources.ReferenceChemicalShiftLoaders import _DefaultReferenceChemicalShiftsLoader, _InternalReferenceChemicalShiftsLoader
            self.register(_DefaultReferenceChemicalShiftsLoader)
            self.register(_InternalReferenceChemicalShiftsLoader)

    def _initProjectReferenceChemicalShifts(self):
        """ Add the user-Project-specific Resources ReferenceChemicalShiftsLoader """
        from ccpn.framework.Application import getProject
        from ccpn.framework.PathsAndUrls import CCPN_RESOURCES_DIRECTORY
        from ccpn.framework.lib.resources.ReferenceChemicalShiftLoaders import _ProjectReferenceChemicalShiftsLoader

        if (project := getProject()) is not None:
            projectResourcesPath = project.projectPath / CCPN_RESOURCES_DIRECTORY
            _ProjectReferenceChemicalShiftsLoader.directory = projectResourcesPath
            self.register(_ProjectReferenceChemicalShiftsLoader)

    def _deregisterProjectReferenceChemicalShifts(self):
        """ Remove the user-Project-specific Resources ReferenceChemicalShiftsLoader  """
        from ccpn.framework.lib.resources.ReferenceChemicalShiftLoaders import _ProjectReferenceChemicalShiftsLoader
        self.deregister(_ProjectReferenceChemicalShiftsLoader)
