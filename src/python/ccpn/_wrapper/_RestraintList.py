"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import operator
# from ccpn.util import Common as commonUtil
from ccpncore.lib import Constants as coreConstants
from ccpn.util.Tensor import Tensor
from ccpn.util import Pid
from ccpncore.api.ccp.nmr.NmrConstraint import AbstractConstraintList as ApiAbstractConstraintList
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import DataSet


class RestraintList(AbstractWrapperObject):
  """ RestraintList - A container for restraints, with type determined by the restraintType
  attribute. Typical examples are Distance and Dihedral restraints, but can also be used to store
  measurements or derived values (Rdc, J coupling, T1, T2, Chemical Shift, ...)
  """

  
  #: Short class name, for PID.
  shortClassName = 'RL'
  # Attribute it necessary as subclasses must use superclass className
  className = 'RestraintList'

  #: Name of plural link to instances of class
  _pluralLinkName = 'restraintLists'

  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiAbstractConstraintList._metaclass.qualifiedName()

  # # Number of atoms in a Restraint item, by restraint type
  # _restraintType2Length = {
  #   'Distance':2,
  #   'Dihedral':4,
  #   'Rdc':2,
  #   'HBond':2,
  #   'JCoupling':2,
  #   'Csa':1,
  #   'ChemicalShift':1,
  # }

  def __init__(self, project, wrappedData):

    # NB The name will only be unique within the DataSet, which could cause
    # problems if anyone was silly enough to write out restraintLists from
    # different DataSets to the same NEF file.

    self._wrappedData = wrappedData
    self._project = project
    defaultName = ('%ss%s' %
                   (self._wrappedData.constraintType, wrappedData.serial))
    self._setUniqueStringKey(wrappedData, defaultName)
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
    """DataSet containing ccpn.RestraintList."""
    return  self._project._data2Obj[self._wrappedData.nmrConstraintStore]
  
  dataSet = _parent
  
  @property
  def name(self) -> str:
    """name of Restraint List"""
    return self._wrappedData.name
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def unit(self) -> str:
    """Unit for restraints"""
    return self._wrappedData.unit

  @unit.setter
  def unit(self, value:str):
    self._wrappedData.unit = value

  @property
  def potentialType(self) -> str:
    """Potential type for restraints"""
    return self._wrappedData.potentialType

  @potentialType.setter
  def potentialType(self, value:str):
    self._wrappedData.potentialType = value

  @property
  def measurementType(self) -> str:
    """Type of measurements giving rise to Restraints.
    Used for restraintTypes like T1 (types z, zz), T2 (types SQ, DQ), ...
    Freely settable for now - precise enumerations will eventually be introduced."""
    return self._wrappedData.measurementType

  @measurementType.setter
  def measurementType(self, value:str):
    self._wrappedData.measurementType = value

  @property
  def origin(self) -> str:
    """Data origin for restraints. Free text. Examples would be
    'noe', 'hbond', 'mutation', or  'shift-perturbation' (for a distance restraint list),
    'jcoupling' or 'talos' (for a dihedral restraint list), 'measured' (for any observed value)"""
    return self._wrappedData.origin

  @origin.setter
  def origin(self, value:str):
    self._wrappedData.origin = value

  @property
  def tensor(self) -> Tensor:
    """orientation tensor for restraints. """
    apiRestraintList = self._wrappedData
    return Tensor(axial=apiRestraintList.tensorMagnitude,
                  rhombic=apiRestraintList.tensorRhombicity,
                  isotropic=apiRestraintList.tensorIsotropicValue)

  @tensor.setter
  def tensor(self, value:Tensor):
      self._wrappedData.tensorIsotropicValue= value.isotropic
      self._wrappedData.tensorMagnitude= value.axial
      self._wrappedData.tensorRhombicity= value.rhombic

  @property
  def tensorChainCode(self) -> float:
    """tensorChainCode of orientation tensor. Used to identify tensor in coordinate files"""
    return self._wrappedData.tensorChainCode

  @tensorChainCode.setter
  def tensorChainCode(self, value:float):
    self._wrappedData.tensorChainCode = value

  @property
  def tensorSequenceCode(self) -> float:
    """tensorSequenceCode of orientation tensor. Used to identify tensor in coordinate files """
    return self._wrappedData.tensorSequenceCode

  @tensorSequenceCode.setter
  def tensorSequenceCode(self, value:float):
    self._wrappedData.tensorSequenceCode = value

  @property
  def tensorResidueType(self) -> float:
    """tensorResidueType of orientation tensor. Used to identify tensor in coordinate files """
    return self._wrappedData.tensorResidueType

  @tensorResidueType.setter
  def tensorResidueType(self, value:float):
    self._wrappedData.tensorResidueType = value
    
  # Implementation functions
  def rename(self, value):
    """rename RestraintList, changing Id and Pid"""
    if not value:
      raise ValueError("RestraintList name must be set")

    elif Pid.altCharacter in value:
      raise ValueError("Character %s not allowed in ccpn.RestraintList.name:" % Pid.altCharacter)

    else:
      self._wrappedData.name = value

  @classmethod
  def _getAllWrappedData(cls, parent: DataSet)-> list:
    """get wrappedData - all ConstraintList children of parent NmrConstraintStore"""
    return sorted(parent._wrappedData.constraintLists, key=operator.attrgetter('name'))

# Connections to parents:
DataSet._childClasses.append(RestraintList)

def _newRestraintList(self:DataSet, restraintType, name:str=None, origin:str=None,
                      comment:str=None, unit:str=None, potentialType:str='unknown',
                      tensorMagnitude:float=0.0, tensorRhombicity:float=0.0,
                      tensorIsotropicValue:float=0.0, tensorChainCode:str=None,
                      tensorSequenceCode:str=None, tensorResidueType:str=None) -> RestraintList:
  """Create new ccpn.RestraintList of type restraintType within ccpn.DataSet"""

  if name and Pid.altCharacter in name:
    raise ValueError("Character %s not allowed in ccpn.RestraintList.name:" % Pid.altCharacter)

  itemLength = coreConstants.constraintListType2ItemLength.get(restraintType)
  if itemLength is None:
    raise ValueError("restraintType %s not recognised" % restraintType)

  obj = self._wrappedData.newGenericConstraintList(name=name, details=comment, unit=unit,
                                                   origin=origin,
                                                   constraintType=restraintType,
                                                   itemLength=itemLength,
                                                   potentialType=potentialType,
                                                   tensorMagnitude=tensorMagnitude,
                                                   tensorRhombicity=tensorRhombicity,
                                                   tensorIsotropicValue=tensorIsotropicValue,
                                                   tensorChainCode=tensorChainCode,
                                                   tensorSequenceCode=tensorSequenceCode,
                                                   tensorResidueType=tensorResidueType )
  return self._project._data2Obj.get(obj)

DataSet.newRestraintList = _newRestraintList
del _newRestraintList

# Notifiers:
for clazz in ApiAbstractConstraintList._metaclass.getNonAbstractSubtypes():
  className = clazz.qualifiedName()
  Project._apiNotifiers.extend(
    ( ('_finaliseApiRename', {}, className, 'setName'),
    )
)
