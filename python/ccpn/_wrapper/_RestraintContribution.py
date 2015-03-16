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

from collections.abc import Sequence
from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
from ccpn._wrapper._Restraint import Restraint
from ccpncore.api.ccp.nmr.NmrConstraint import ConstraintContribution as ApiContribution
from ccpncore.api.ccp.nmr.NmrConstraint import FixedResonance as ApiFixedResonance


class RestraintContribution(AbstractWrapperObject):
  """Restraint contribution."""
  
  #: Short class name, for PID.
  shortClassName = 'RC'

  # Number of atoms in a Restraint item, by restraint type
  restraintType2Length = {
    'Distance':2,
    'Dihedral':4,
    'Rdc':2,
    'HBond':2,
    'JCoupling':2,
    'Csa':1,
    'ChemicalShift':1,
  }

  #: Name of plural link to instances of class
  _pluralLinkName = 'restraintContributions'

  #: List of child classes.
  _childClasses = []

  # CCPN properties
  @property
  def apiContribution(self) -> ApiContribution:
    """ API Contribution matching Contribution"""
    return self._wrappedData

  @property
  def _parent(self) -> Restraint:
    """Restraint containing restraintContribution."""
    return  self._project._data2Obj[self._wrappedData.constraint]

  restraint = _parent

  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for Peak"""
    return self._wrappedData.serial

  @property
  def targetValue(self) -> float:
    """targetValue of contribution """
    return self._wrappedData.targetValue

  @targetValue.setter
  def targetValue(self, value:float):
    self._wrappedData.targetValue = value

  @property
  def error(self) -> float:
    """error of contribution """
    return self._wrappedData.error

  @error.setter
  def error(self, value:float):
    self._wrappedData.error = value

  @property
  def weight(self) -> float:
    """weight of contribution """
    return self._wrappedData.weight

  @weight.setter
  def weight(self, value:float):
    self._wrappedData.weight = value

  @property
  def upperLimit(self) -> float:
    """upperLimit of contribution """
    return self._wrappedData.upperLimit

  @upperLimit.setter
  def upperLimit(self, value:float):
    self._wrappedData.upperLimit = value

  @property
  def lowerLimit(self) -> float:
    """lowerLimit of contribution """
    return self._wrappedData.lowerLimit

  @lowerLimit.setter
  def lowerLimit(self, value:float):
    self._wrappedData.lowerLimit = value

  @property
  def additionalUpperLimit(self) -> float:
    """additionalUpperLimit of contribution """
    return self._wrappedData.additionalUpperLimit

  @additionalUpperLimit.setter
  def additionalUpperLimit(self, value:float):
    self._wrappedData.additionalUpperLimit = value

  @property
  def additionalLowerLimit(self) -> float:
    """additionalLowerLimit of contribution """
    return self._wrappedData.additionalLowerLimit

  @additionalLowerLimit.setter
  def additionalLowerLimit(self, value:float):
    self._wrappedData.additionalLowerLimit = value

  @property
  def scale(self) -> float:
    """scaling factor (RDC only) to be multiplied with targetValue to get scaled value """
    if hasattr(self._wrappedData, 'scale'):
      return self._wrappedData.scale
    else:
      raise AttributeError("%s RestraintContribution has no attribute 'scale'" %
      self._parent._parent.restraintType)

  @scale.setter
  def scale(self, value:float):
    if hasattr(self._wrappedData, 'scale'):
      self._wrappedData.scale = value
    else:
      raise AttributeError("%s RestraintContribution has no attribute 'scale'" %
      self._parent._parent.restraintType)

  @property
  def isDistanceDependent(self) -> float:
    """Does targetValue depend on a variable distance (RDC only) """
    if hasattr(self._wrappedData, 'isDistanceDependent'):
      return self._wrappedData.isDistanceDependent
    else:
      raise AttributeError("%s RestraintContribution has no attribute 'isDistanceDependent'" %
      self._parent._parent.restraintType)

  @isDistanceDependent.setter
  def isDistanceDependent(self, value:float):
    if hasattr(self._wrappedData, 'isDistanceDependent'):
      self._wrappedData.isDistanceDependent = value
    else:
      raise AttributeError("%s RestraintContribution has no attribute 'isDistanceDependent'" %
      self._parent._parent.restraintType)

  @property
  def combinationId(self) -> int:
    """combinationId of contribution, describing which contributions are AND'ed together"""
    return self._wrappedData.combinationId

  @combinationId.setter
  def combinationId(self, value:int):
    self._wrappedData.combinationId = value

  @property
  def restraintItems(self) -> tuple:
    """restraint items of contribution - given as a tuple of lists of AtomId """

    itemLength = self.restraintType2Length[self._parent._parent.restraintType]

    result = []
    sortkey = self._project._pidSortKey

    if itemLength > 1:
      for apiItem in self._wrappedData.items:
        atomIds = [_fixedResonance2AtomId(x) for x in apiItem.resonances]
        if sortkey(atomIds[0]) > sortkey(atomIds[-1]):
          # order so smallest string comes first
          # NB This assumes that assignments are either length 2 or ordered (as is so far the case)
          atomIds.reverse()
        result.append(tuple(atomIds))
    else:
      for apiItem in self._wrappedData.items:
        result.append((_fixedResonance2AtomId(apiItem.resonance),))
    #
    return tuple(sorted(result, key=sortkey))

  @restraintItems.setter
  def restraintItems(self, value:Sequence):

    itemLength = self.restraintType2Length[self._parent._parent.restraintType]
    newItemFuncName ="new%sItem" % self._parent._parent.restraintType

    for ll in value:
      # make new items
      if len(ll) != self.restraintItemLength:
        raise ValueError("RestraintItems must have length %s: %s" % (itemLength, ll))

    apiContribution = self._wrappedData
    for item in apiContribution.items:
      # remove old items
      item.delete()

    fetchFixedResonance = self._parent._parent._parent._fetchFixedResonance
    if itemLength > 1:
      for ll in value:
        # make new items
        getattr(apiContribution, newItemFuncName)(
          resonances=tuple(fetchFixedResonance(Pid.splitId(x)) for x in ll))
    else:
      for ll in value:
        # make new items
        getattr(apiContribution, newItemFuncName)(
          resonance=fetchFixedResonance(Pid.splitId(ll[0])))
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Restraint)-> list:
    """get wrappedData - all Constraint children of parent ConstraintList"""
    return parent._wrappedData.sortedContributions()

# Connections to parents:
Restraint._childClasses.append(RestraintContribution)

def newRestraintContribution(parent:Restraint, targetValue:float=None, error:float=None,
                    weight:float=None, upperLimit:float=None,  lowerLimit:float=None,
                    additionalUpperLimit:float=None, additionalLowerLimit:float=None,
                    restraintItems:Sequence=()) -> RestraintContribution:
  """Create new child Contribution"""
  constraint = parent._wrappedData
  creator = constraint.getattr("new%sContribution" % parent._parent.restraintType)
  obj = creator(targetValue=targetValue, error=error, weight=weight, upperLimit=upperLimit,
                lowerLimit=lowerLimit, additionalUpperLimit=additionalUpperLimit,
                additionalLowerLimit=additionalLowerLimit)
  result = parent._project._data2Obj.get(obj)
  result.restraintItems = restraintItems
  return result

Restraint.newRestraintContribution = newRestraintContribution

# Notifiers:
for clazz in ApiContribution._metaclass.getNonAbstractSubtypes():
  className = clazz.qualifiedName()
  Project._apiNotifiers.extend(
    ( ('_newObject', {'cls':RestraintContribution}, className, '__init__'),
      ('_finaliseDelete', {}, className, 'delete')
    )
)

def _fixedResonance2AtomId(fixedResonance:ApiFixedResonance) -> str:
  """Utility function - get AtomId from FixedResonance """
  tags = ('chainCode', 'sequenceCode', 'residueType', 'name')
  return Pid.makeId(*(getattr(fixedResonance, tag) for tag in tags))