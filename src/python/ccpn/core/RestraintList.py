"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-11-02 17:47:51 +0000 (Mon, November 02, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from typing import Sequence, Union
from ccpn.util.Common import _validateName
from ccpn.core.lib import Pid
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.DataSet import DataSet
from ccpnmodel.ccpncore.lib import Constants as coreConstants
from ccpnmodel.ccpncore.api.ccp.nmr.NmrConstraint import AbstractConstraintList as ApiAbstractConstraintList
from ccpn.util.Tensor import Tensor
from ccpn.util.decorators import logCommand
from ccpn.core.lib.ContextManagers import newObject, renameObject


class RestraintList(AbstractWrapperObject):
    """ An object containing Restraints. Note: the object is not a (subtype of a) Python list.
    To access all Restraint objects, use RestraintList.restraints.

    The type of restraint is determined by the restraintType attribute.
    Typical examples are Distance, Dihedral and Rdc restraints, but can also be used to store
    measurements or derived values (Rdc, J coupling, T1, T2, Chemical Shift, ...)
    """

    #: Short class name, for PID.
    shortClassName = 'RL'
    # Attribute it necessary as subclasses must use superclass className
    className = 'RestraintList'

    _parentClass = DataSet

    #: Name of plural link to instances of class
    _pluralLinkName = 'restraintLists'

    #: List of child classes.
    _childClasses = []

    # Qualified name of matching API class
    _apiClassQualifiedName = ApiAbstractConstraintList._metaclass.qualifiedName()

    #TODO: this needs to be explicit here
    restraintTypes = tuple(coreConstants.constraintListType2ItemLength.keys())

    def __init__(self, project, wrappedData):

        # NB The name will only be unique within the DataSet.
        # NEF I/O therefore adds a prefix to distinguish the DataSet

        self._wrappedData = wrappedData
        self._project = project

        namePrefix = self._wrappedData.constraintType[:3].capitalize() + '-'
        defaultName = ('%s%s' % (namePrefix, wrappedData.serial))
        self._setUniqueStringKey(defaultName)
        super().__init__(project, wrappedData)

    # Special error-raising functions for people who think RestraintList is a list
    def __iter__(self):
        raise TypeError("'RestraintList object is not iterable"
                        " - for a list of restraints use RestraintList.restraints")

    def __getitem__(self, index):
        raise TypeError("'RestraintList object does not support indexing"
                        " - for a list of restraints use RestraintList.restraints")

    def __len__(self):
        raise TypeError("'RestraintList object has no length"
                        " - for a list of restraints use RestraintList.restraints")

    # CCPN properties
    @property
    def _apiRestraintList(self) -> ApiAbstractConstraintList:
        """ CCPN ConstraintList matching RestraintList"""
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
        """serial number of RestraintList, used in Pid and to identify the RestraintList. """
        return self._wrappedData.serial

    @property
    def _parent(self) -> DataSet:
        """DataSet containing RestraintList."""
        return self._project._data2Obj[self._wrappedData.nmrConstraintStore]

    dataSet = _parent

    @property
    def name(self) -> str:
        """name of Restraint List"""
        return self._wrappedData.name

    @name.setter
    def name(self, value:str):
        """Set name of RestraintList."""
        self.rename(value)

    # @property
    # def comment(self) -> str:
    #     """Free-form text comment"""
    #     return self._wrappedData.details
    #
    # @comment.setter
    # def comment(self, value: str):
    #     self._wrappedData.details = value

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
        apiRestraintList = self._wrappedData
        return Tensor(axial=apiRestraintList.tensorMagnitude,
                      rhombic=apiRestraintList.tensorRhombicity,
                      isotropic=apiRestraintList.tensorIsotropicValue)

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

    #=========================================================================================
    # Implementation functions
    #=========================================================================================

    @classmethod
    def _getAllWrappedData(cls, parent: DataSet) -> list:
        """get wrappedData - all ConstraintList children of parent NmrConstraintStore"""
        return parent._wrappedData.sortedConstraintLists()

    @renameObject()
    @logCommand(get='self')
    def rename(self, value: str):
        """Rename RestraintList, changing its name and Pid.
        """
        _validateName(self.project, RestraintList, value=value, allowWhitespace=False)

        # rename functions from here
        oldName = self.name
        self._wrappedData.name = value
        return (oldName,)

    #=========================================================================================
    # CCPN functions
    #=========================================================================================

    #===========================================================================================
    # new'Object' and other methods
    # Call appropriate routines in their respective locations
    #===========================================================================================

    @logCommand(get='self')
    def newRestraint(self, figureOfMerit: float = None, comment: str = None,
                      peaks: Sequence[Union['Peak', str]] = (), vectorLength: float = None, **kwds):
        """Create new Restraint within RestraintList.

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
        """Create a Restraint with a single RestraintContribution within the RestraintList.
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

@newObject(RestraintList)
def _newRestraintList(self: DataSet, restraintType, name: str = None, origin: str = None,
                      comment: str = None, unit: str = None, potentialType: str = 'unknown',
                      tensorMagnitude: float = 0.0, tensorRhombicity: float = 0.0,
                      tensorIsotropicValue: float = 0.0, tensorChainCode: str = None,
                      tensorSequenceCode: str = None, tensorResidueType: str = None,
                      serial: int = None, restraintItemLength=None) -> RestraintList:
    """Create new RestraintList of type restraintType within DataSet.

    See the RestraintList class for details.

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
    :param serial: optional serial number.
    :return: a new RestraintList instance.
    """

    if not name:
        name = RestraintList._nextAvailableName(RestraintList, self)
    _validateName(self, RestraintList, name)

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
        raise RuntimeError('Unable to generate new RestraintList item')

    if serial is not None:
        try:
            result.resetSerial(serial)
        except ValueError:
            self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
                                         % (result, serial))

    return result


#EJB 20181206: moved to DataSet
# DataSet.newRestraintList = _newRestraintList
# del _newRestraintList

# Notifiers:
for clazz in ApiAbstractConstraintList._metaclass.getNonAbstractSubtypes():
    className = clazz.qualifiedName()
    Project._apiNotifiers.extend(
            (('_finaliseApiRename', {}, className, 'setName'),
             )
            )
