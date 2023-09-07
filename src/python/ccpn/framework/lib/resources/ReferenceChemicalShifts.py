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

from collections import OrderedDict, defaultdict
import pandas as pd
from ccpn.util.Logging import getLogger
from ccpn.util.OrderedSet import OrderedSet
from ccpn.framework.lib.resources import ResourcesNameSpaces as rns

class ReferenceChemicalShifts(OrderedDict):
    """
    Class to handle all the ReferenceChemicalShifts.
    The ReferenceChemicalShifts object is represented by an OrderedDict.

    The OrderedDict is structured as
        - key -> residue shortName
        - value -> residue Traitlet object (see /resources/ReferenceChemicalShiftLoaders.py)

    usage:
    To get this object at runtime:
                referenceChemicalShifts = application.resources.referenceChemicalShifts

    Objects can be retrieved simply by the built-in dictionary methods.
        e.g.: by residue shortName:
            ala = referenceChemicalShifts.get('ALA')

    For more complex data queries: use the built-in methods getBy which returns a dataFrame representation and can be further filtered as a pipeline.

        e.g.:
        - get all data by the "DNA" moleculeType:
            data =  referenceChemicalShifts.dataFrame
            dnaData = referenceChemicalShifts.getBy(dataFrame=data, theProperty='moleculeType', values=['DNA'])
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
        Create a flat dataframe for all the traits definition.
        :return:
        """
        _data = []
        for residueTrait in self.values():
            residueTraitDict = dict(residueTrait.items())
            residueTraitDict[rns.TITLE] = residueTrait.title
            residueTraitDict[rns.COMMENT] = residueTrait.comment
            residueTraitDict[rns.RESIDUEOBJ] = residueTrait
            atomTraits = residueTraitDict.pop(rns.ATOMS, [])
            for atomTrait in atomTraits:
                atomTraitDict = dict(atomTrait.items())
                atomTraitDict.pop(rns.DISTRIBUTION, [])
                atomTraitDict[rns.PPMARRAY] = atomTrait.ppmArray
                atomTraitDict[rns.INTENSITIESARRAY] = atomTrait.intensitiesArray
                atomTraitDict[rns.ATOMOBJ] = atomTrait
                _row = residueTraitDict | atomTraitDict
                _data.append(_row)
        df = pd.DataFrame(_data)
        return df

    ############# Core Registration Methods ##############

    def register(self, theClass, loadObjects=True):
        """"""
        self._registeredClasses.add(theClass)
        if loadObjects:
            obj = theClass()
            self.update(obj)
            self._objsByClass[theClass] = obj
            self._dataFrame = self._buildDataFrame()

    def deregister(self, theClass, unloadObjects=True):
        """ remove the registered class and unload the RCS. E.g. done when switching projects.
        """
        if theClass not in self._registeredClasses:
            getLogger().warning(f'Cannot deregister {theClass} from {self.__class__.__name__}. Value not in the _registeredClasses.')
            return
        self._registeredClasses.pop(theClass)
        if unloadObjects:
            obj = self._objsByClass.pop(theClass, {})
            for key in obj:
                self.pop(key, None)
            del obj
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
