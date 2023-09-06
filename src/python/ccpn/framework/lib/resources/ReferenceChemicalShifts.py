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
__dateModified__ = "$dateModified: 2023-09-06 14:28:31 +0100 (Wed, September 06, 2023) $"
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
from ccpn.util.Logging import getLogger
from ccpn.util.OrderedSet import OrderedSet


class ReferenceChemicalShifts(OrderedDict):
    """
    Class to handle all the ReferenceChemicalShifts .

    """
    _registeredClasses = OrderedSet()

    def __init__(self):
        super().__init__()
        self._objsByClass = {}
        self._registerCcpnReferenceChemicalShiftLoaders()
        self._activeChemicalShifts = []


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

    def activeChemicalShifts(self):
        return self._activeChemicalShifts

    def setActiveChemicalShifts(self, activeChemicalShifts):
        """ Filter the ReferenceChemicalShifts  by conditions and set as active for all the ongoing calculations"""
        self._activeChemicalShifts = activeChemicalShifts

    def _getAvailableMolTypes(self):
        availableMolTypes = set()
        for obj in self.values():
            availableMolTypes.add(obj.moleculeType)
        return list(availableMolTypes)


    ############# Core Registration Methods ##############

    def register(self, theClass, loadObjects=True):
        """"""
        self._registeredClasses.add(theClass)
        if loadObjects:
            obj = theClass()
            self.update(obj)
            self._objsByClass[theClass] = obj

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
