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
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import RestraintSet
from ccpncore.util import Pid
from ccpncore.api.ccp.nmr.NmrConstraint import AbstractConstraintList as ApiAbstractConstraintList


class RestraintList(AbstractWrapperObject):
  """ RestraintList - All restraints lists, with type determined by the restraintType attribute."""
  
  #: Short class name, for PID.
  shortClassName = 'RL'
  # Attribute it necessary as subclasses must use superclass className
  className = 'RestraintList'

  #: Name of plural link to instances of class
  _pluralLinkName = 'restraintLists'

  #: List of child classes.
  _childClasses = []

  # Number of atoms in a Restraint item, by restraint type
  _restraintType2Length = {
    'Distance':2,
    'Dihedral':4,
    'Rdc':2,
    'HBond':2,
    'JCoupling':2,
    'Csa':1,
    'ChemicalShift':1,
  }

  def __init__(self, project, wrappedData):

    # NB The name will only be unique within the restraintSet, which could cause
    # problems if anyone was silly enough to write out restraintLists from
    # different RestraintSets to the same NEF file.

    self._wrappedData = wrappedData
    self._project = project
    defaultName = ('%ss-%s' %
                   (self._wrappedData.__class__.__name__[:-14], wrappedData.serial))
    self._setUniqueStringKey(wrappedData, defaultName)
    super().__init__(project, wrappedData)

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
    """Restraint type"""
    return self._wrappedData.__class__.__name__[:-14]

  @property
  def restraintItemLength(self) -> int:
    """Length of restraintItem - number of atom ID defining a restraint"""
    return self.restraintType2Length[self.restraintType]

  @property
  def serial(self) -> int:
    """serial number, key attribute for ccpn.RestraintList"""
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> RestraintSet:
    """RestraintSet containing ccpn.RestraintList."""
    return  self._project._data2Obj[self._wrappedData.nmrConstraintStore]
  
  restraintSet = _parent
  
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
  def origin(self) -> str:
    """Data origin for restraints"""
    return self._wrappedData.origin

  @origin.setter
  def origin(self, value:str):
    self._wrappedData.origin = value

  @property
  def tensorMagnitude(self) -> float:
    """magnitude of orientation tensor """
    if self.restraintType == 'Rdc':
      return self._wrappedData.tensorMagnitude
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorMagnitude"
                                    % self.restraintType)

  @tensorMagnitude.setter
  def tensorMagnitude(self, value:float):
    if self.restraintType == 'Rdc':
      self._wrappedData.tensorMagnitude = value
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorMagnitude"
                                    % self.restraintType)

  @property
  def tensorRhombicity(self) -> float:
    """rhombicity of orientation tensor """
    if self.restraintType == 'Rdc':
      return self._wrappedData.tensorRhombicity
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorRhombicity"
                                    % self.restraintType)

  @tensorRhombicity.setter
  def tensorRhombicity(self, value:float):
    if self.restraintType == 'Rdc':
      self._wrappedData.tensorRhombicity = value
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorRhombicity"
                                    % self.restraintType)

  @property
  def tensorChainCode(self) -> float:
    """tensorChainCode of orientation tensor """
    if self.restraintType == 'Rdc':
      return self._wrappedData.tensorChainCode
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorChainCode"
                                    % self.restraintType)

  @tensorChainCode.setter
  def tensorChainCode(self, value:float):
    if self.restraintType == 'Rdc':
      self._wrappedData.tensorChainCode = value
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorChainCode"
                                    % self.restraintType)

  @property
  def tensorSequenceCode(self) -> float:
    """tensorSequenceCode of orientation tensor """
    if self.restraintType == 'Rdc':
      return self._wrappedData.tensorSequenceCode
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorSequenceCode"
                                    % self.restraintType)

  @tensorSequenceCode.setter
  def tensorSequenceCode(self, value:float):
    if self.restraintType == 'Rdc':
      self._wrappedData.tensorSequenceCode = value
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorSequenceCode"
                                    % self.restraintType)

  @property
  def tensorResidueType(self) -> float:
    """tensorResidueType of orientation tensor """
    if self.restraintType == 'Rdc':
      return self._wrappedData.tensorResidueType
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorResidueType"
                                    % self.restraintType)

  @tensorResidueType.setter
  def tensorResidueType(self, value:float):
    if self.restraintType == 'Rdc':
      self._wrappedData.tensorResidueType = value
    else:
      self._project._logger.warning("%sRestraintList has no attribute tensorResidueType"
                                    % self.restraintType)
    
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
  def _getAllWrappedData(cls, parent: RestraintSet)-> list:
    """get wrappedData - all ConstraintList children of parent NmrConstraintStore"""
    return sorted(parent._wrappedData.constraintLists, key=operator.attrgetter('name'))

# Connections to parents:
RestraintSet._childClasses.append(RestraintList)

def _newRestraintList(self:RestraintSet, restraintType, name:str=None, comment:str=None,
                     unit:str=None, potentialType:str=None, tensorMagnitude:float=None,
                     tensorRhombicity:float=None, tensorChainCode:str=None,
                     tensorSequenceCode:str=None,
                     tensorResidueType:str=None) -> RestraintList:
  """Create new ccpn.RestraintList of type restraintType within ccpn.RestraintSet"""

  if name and Pid.altCharacter in name:
    raise ValueError("Character %s not allowed in ccpn.RestraintList.name:" % Pid.altCharacter)

  apiNmrConstraintStore = self._wrappedData
  creator = apiNmrConstraintStore.getattr("new%sConstraintList" % restraintType)
  if restraintType == 'Rdc':
    obj = creator(name=name, details=comment, unit=unit, potentialType=potentialType,
                  tensorMagnitude=tensorMagnitude, tensorRhombicity=tensorRhombicity,
                  tensorChainCode=tensorChainCode,tensorSequenceCode=tensorSequenceCode,
                  tensorResidueType=tensorResidueType )
  else:
    obj = creator(name=name, details=comment, unit=unit, potentialType=potentialType)
  return self._project._data2Obj.get(obj)

RestraintSet.newRestraintList = _newRestraintList
del _newRestraintList

# Notifiers:
for clazz in ApiAbstractConstraintList._metaclass.getNonAbstractSubtypes():
  className = clazz.qualifiedName()
  Project._apiNotifiers.extend(
    ( ('_newObject', {'cls':RestraintList}, className, '__init__'),
      ('_finaliseDelete', {}, className, 'delete'),
    ('_finaliseUnDelete', {}, className, 'undelete'),
      ('_resetPid', {}, className, 'setName'),
    )
)
