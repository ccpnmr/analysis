"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2024"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2024-05-30 13:45:36 +0100 (Thu, May 30, 2024) $"
__version__ = "$Revision: 3.2.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Union

from ccpn.core.lib import Pid
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.StructureData import StructureData
from ccpnmodel.ccpncore.lib import Constants as coreConstants
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import AbstractConstraintList as ApiAbstractConstraintList
from ccpn.util.Tensor import Tensor
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, renameObject
from ccpn.util.Logging import getLogger


class RestraintTable(AbstractWrapperObject):
    """ An object containing Restraints. Note: the object is not a (subtype of a) Python list.
    To access all Restraint objects, use RestraintTable.restraints.

    The type of restraint is determined by the restraintType attribute.
    Typical examples are Distance, Dihedral and Rdc restraints, but can also be used to store
    measurements or derived values (Rdc, J coupling, T1, T2, Chemical Shift, ...)
    """

    #: Short class name, for PID.
    shortClassName = 'RT'
    # Attribute it necessary as subclasses must use superclass className
    className = 'RestraintTable'

    _isPandasTableClass = True

    _parentClass = StructureData

    #: Name of plural link to instances of class
    _pluralLinkName = 'restraintTables'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiAbstractConstraintList._metaclass.qualifiedName()

    #TODO: this needs to be explicit here
    restraintTypes = tuple(coreConstants.constraintListType2ItemLength.keys())

    def __init__(self, project, wrappedData):

        # NB The name will only be unique within the StructureData.
        # NEF I/O therefore adds a prefix to distinguish the StructureData

        self._wrappedData = wrappedData
        self._project = project

        try:
            namePrefix = self._wrappedData.constraintType[:3].capitalize() + '-'
        except:
            namePrefix = 'myRestraintTable_'
        defaultName = ('%s%s' % (namePrefix, wrappedData.serial))
        self._setUniqueStringKey(defaultName)
        super().__init__(project, wrappedData)

    # Special error-raising functions for people who think RestraintTable is a list
    def __iter__(self):
        raise TypeError("'RestraintTable object is not iterable"
                        " - for a list of restraints use RestraintTable.restraints")

    def __getitem__(self, index):
        raise TypeError("'RestraintTable object does not support indexing"
                        " - for a list of restraints use RestraintTable.restraints")

    def __len__(self):
        raise TypeError("'RestraintTable object has no length"
                        " - for a list of restraints use RestraintTable.restraints")

    #=========================================================================================
    # CCPN properties
    #=========================================================================================

    @property
    def _apiRestraintTable(self) -> ApiAbstractConstraintList:
        """CCPN ConstraintList matching RestraintTable"""
        return self._wrappedData

    @property
    def _key(self) -> str:
        """id string - serial number converted to string"""
        return self._wrappedData.name.translate(Pid.remapSeparators)

    @property
    def restraintType(self) -> str:
        """Restraint type.

        Recommended types are Distance, Rdc, JCoupling, ChemicalShift, Csa, Dihedral, T1, T2, ...
        Freely settable for now - further enumerations will eventually be introduced."""
        return self._wrappedData.constraintType

    @property
    def restraintItemLength(self) -> int:
        """Length of restraintItem - number of atom ID identifying a restraint"""
        return self._wrappedData.itemLength

    @property
    def serial(self) -> int:
        """serial number of RestraintTable, used in Pid and to identify the RestraintTable. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> StructureData:
        """StructureData containing RestraintTable."""
        return self._project._data2Obj[self._wrappedData.nmrConstraintStore]

    structureData = _parent

    @property
    def name(self) -> str:
        """name of Restraint List"""
        return self._wrappedData.name

    @name.setter
    def name(self, value: str):
        """Set name of RestraintTable."""
        self.rename(value)

    @property
    def unit(self) -> str:
        """Unit for restraints"""
        return self._wrappedData.unit

    @unit.setter
    def unit(self, value: str):
        self._wrappedData.unit = value

    @property
    def potentialType(self) -> str:
        """Potential type for restraints"""
        return self._wrappedData.potentialType

    @potentialType.setter
    def potentialType(self, value: str):
        self._wrappedData.potentialType = value

    @property
    def measurementType(self) -> str:
        """Type of measurements giving rise to Restraints.
        Used for restraintTypes like T1 (types z, zz), T2 (types SQ, DQ), ...
        Freely settable for now - precise enumerations will eventually be introduced."""
        return self._wrappedData.measurementType

    @measurementType.setter
    def measurementType(self, value: str):
        self._wrappedData.measurementType = value

    @property
    def origin(self) -> str:
        """Data origin for restraints. Free text. Examples would be
        'noe', 'hbond', 'mutation', or  'shift-perturbation' (for a distance restraint list),
        'jcoupling' or 'talos' (for a dihedral restraint list), 'measured' (for any observed value)"""
        return self._wrappedData.origin

    @origin.setter
    def origin(self, value: str):
        self._wrappedData.origin = value

    @property
    def tensor(self) -> Tensor:
        """orientation tensor for restraints. """
        apiRestraintTable = self._wrappedData
        return Tensor(axial=apiRestraintTable.tensorMagnitude,
                      rhombic=apiRestraintTable.tensorRhombicity,
                      isotropic=apiRestraintTable.tensorIsotropicValue)

    @tensor.setter
    def tensor(self, value: Tensor):
        self._wrappedData.tensorIsotropicValue = value.isotropic
        self._wrappedData.tensorMagnitude = value.axial
        self._wrappedData.tensorRhombicity = value.rhombic

    @property
    def tensorMagnitude(self) -> float:
        """tensor Magnitude of orientation tensor. """
        return self._wrappedData.tensorMagnitude

    @property
    def tensorRhombicity(self) -> float:
        """tensor Rhombicity of orientation tensor. U"""
        return self._wrappedData.tensorRhombicity

    @property
    def tensorIsotropicValue(self) -> float:
        """tensor IsotropicValue of orientation tensor."""
        return self._wrappedData.tensorIsotropicValue

    @property
    def tensorChainCode(self) -> float:
        """tensorChainCode of orientation tensor. Used to identify tensor in coordinate files"""
        return self._wrappedData.tensorChainCode

    @tensorChainCode.setter
    def tensorChainCode(self, value: float):
        self._wrappedData.tensorChainCode = value

    @property
    def tensorSequenceCode(self) -> float:
        """tensorSequenceCode of orientation tensor. Used to identify tensor in coordinate files """
        return self._wrappedData.tensorSequenceCode

    @tensorSequenceCode.setter
    def tensorSequenceCode(self, value: float):
        self._wrappedData.tensorSequenceCode = value

    @property
    def tensorResidueType(self) -> float:
        """tensorResidueType of orientation tensor. Used to identify tensor in coordinate files """
        return self._wrappedData.tensorResidueType

    @tensorResidueType.setter
    def tensorResidueType(self, value: float):
        self._wrappedData.tensorResidueType = value

    @property
    def moleculeFilePath(self):
        """
        :return: a filePath for corresponding molecule. Saved in the parent Class StructureData
        E.g., PDB file path for displaying molecules in a molecular viewer
        """
        return self._parent.moleculeFilePath

    @moleculeFilePath.setter
    def moleculeFilePath(self, filePath: str = None):
        """
        :param filePath: a filePath for corresponding molecule
        :return: None
        """
        getLogger().warning('Deprecated. Please set the Molecule File Path from the StructureData object.')
        self._parent.moleculeFilePath = filePath

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: StructureData) -> list:
        """get wrappedData - all ConstraintList children of parent NmrConstraintStore"""
        return parent._wrappedData.sortedConstraintLists()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename RestraintTable, changing its name and Pid.
        """
        return self._rename(value)

    def _rename(self, value: str):
        """Generic rename method that individual classes can use for implementation
        of their rename method to minimises code duplication
        """
        # validate the name from the parent structureData
        name = self._uniqueName(parent=self.structureData, name=value)

        # rename functions from here
        oldName = self.name
        # self._oldPid = self.pid

        self._wrappedData.name = name

        return (oldName,)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new<Object> and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newRestraint(self, figureOfMerit: float = None, comment: str = None,
                     peaks: Sequence[Union['Peak', str]] = (), vectorLength: float = None, **kwds):
        """Create new Restraint within RestraintTable.

        ADVANCED: Note that you just create at least one RestraintContribution afterwards in order to
        have valid data. Use the simpler createSimpleRestraint instead, unless you have specific
        reasons for needing newRestraint.

        See the Restraint class for details.

        Optional keyword arguments can be passed in; see Restraint._newRestraint for details.

        :param figureOfMerit:
        :param comment: optional comment string
        :param peaks: optional list of peaks as objects or pids
        :param vectorLength:
        :return: a new Restraint instance.
        """
        from ccpn.core.Restraint import _newRestraint

        return _newRestraint(self, figureOfMerit=figureOfMerit, peaks=peaks, vectorLength=vectorLength,
                             comment=comment, **kwds)

    @logCommand(get='self')
    def createSimpleRestraint(self, comment: str = None, figureOfMerit: float = None,
                              peaks: Sequence = (), targetValue: float = None, error: float = None,
                              weight: float = 1.0, upperLimit: float = None, lowerLimit: float = None,
                              additionalUpperLimit: float = None, additionalLowerLimit: float = None,
                              scale=1.0, vectorLength=None, restraintItems: Sequence = (), **kwds):
        """Create a Restraint with a single RestraintContribution within the RestraintTable.
        The function takes all the information needed and creates the RestraintContribution as
        well as the Restraint proper.

        This function should be used routinely, unless there is a need to create more complex
        Restraints.

        See the Restraint class for details.

        Optional keyword arguments can be passed in; see Restraint._createSimpleRestraint for details.

        :param comment:
        :param figureOfMerit:
        :param peaks:
        :param targetValue:
        :param error:
        :param weight:
        :param upperLimit:
        :param lowerLimit:
        :param additionalUpperLimit:
        :param additionalLowerLimit:
        :param scale:
        :param vectorLength:
        :param restraintItems:
        :return: a new simple Restraint instance.
        """
        from ccpn.core.Restraint import _createSimpleRestraint

        return _createSimpleRestraint(self, comment=comment, figureOfMerit=figureOfMerit,
                                      peaks=peaks, targetValue=targetValue, error=error,
                                      weight=weight, upperLimit=upperLimit, lowerLimit=lowerLimit,
                                      additionalUpperLimit=additionalUpperLimit, additionalLowerLimit=additionalLowerLimit,
                                      scale=scale, vectorLength=vectorLength, restraintItems=restraintItems, **kwds)


#=========================================================================================
# Connections to parents:
#=========================================================================================

@newObject(RestraintTable)
def _newRestraintTable(self: StructureData, restraintType, name: str = None, origin: str = None,
                       comment: str = None, unit: str = None, potentialType: str = 'unknown',
                       tensorMagnitude: float = 0.0, tensorRhombicity: float = 0.0,
                       tensorIsotropicValue: float = 0.0, tensorChainCode: str = None,
                       tensorSequenceCode: str = None, tensorResidueType: str = None,
                       restraintItemLength=None, **kwargs) -> RestraintTable:
    """Create new RestraintTable of type restraintType within StructureData.

    See the RestraintTable class for details.

    :param restraintType:
    :param name:
    :param origin:
    :param comment:
    :param unit:
    :param potentialType:
    :param tensorMagnitude:
    :param tensorRhombicity:
    :param tensorIsotropicValue:
    :param tensorChainCode:
    :param tensorSequenceCode:
    :param tensorResidueType:
    :param restraintItemLength:
    :return: a new RestraintTable instance.
    """

    # get unique name from the parent structureData
    name = RestraintTable._uniqueName(parent=self, name=name)

    if restraintItemLength is None:
        restraintItemLength = coreConstants.constraintListType2ItemLength.get(restraintType)
    if restraintItemLength is None:
        raise ValueError('restraintType "%s" not recognised' % restraintType)

    obj = self._wrappedData.newGenericConstraintList(name=name, details=comment, unit=unit,
                                                     origin=origin,
                                                     constraintType=restraintType,
                                                     itemLength=restraintItemLength,
                                                     potentialType=potentialType,
                                                     tensorMagnitude=tensorMagnitude,
                                                     tensorRhombicity=tensorRhombicity,
                                                     tensorIsotropicValue=tensorIsotropicValue,
                                                     tensorChainCode=tensorChainCode,
                                                     tensorSequenceCode=tensorSequenceCode,
                                                     tensorResidueType=tensorResidueType)
    result = self._project._data2Obj.get(obj)
    if result is None:
        raise RuntimeError('Unable to generate new RestraintTable item')

    kwargs.pop('serial', None)
    for k, v in kwargs.items():
        try:
            setattr(result, k, v)
        except Exception:
            self.project._logger.warning("Could not set %s to %s" % (k, v))

    return result

# # Notifiers:
# for clazz in ApiAbstractConstraintList._metaclass.getNonAbstractSubtypes():
#     className = clazz.qualifiedName()
#     Project._apiNotifiers.extend(
#             (('_finaliseApiRename', {}, className, 'setName'),
#              )
#             )
