"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from ccpn._wrapper._RestraintList import RestraintList
from ccpncore.api.ccp.nmr.NmrConstraint import AbstractConstraint as ApiAbstractConstraint

class Restraint(AbstractWrapperObject):
  """Restraint, of type given in restraintType."""
  
  #: Short class name, for PID.
  shortClassName = 'RE'

  #: Name of plural link to instances of class
  _pluralLinkName = 'restraints'

  #: List of child classes.
  _childClasses = []

  # CCPN properties
  @property
  def apiConstraint(self) -> ApiAbstractConstraint:
    """ CCPN API Constraint matching Restraint"""
    return self._wrappedData

  @property
  def _parent(self) -> RestraintList:
    """RestraintList containing restraint."""
    return  self._project._data2Obj[self._wrappedData.parentList]

  restraintList = _parent

  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for Peak"""
    return self._wrappedData.serial

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def peaks(self) -> tuple:
    """peaks used to derive restraint"""
    ff = self._project._data2Obj.get
    return tuple(sorted(ff(x) for x in self._wrappedData.peaks))

  @peaks.setter
  def peaks(self, value:Sequence):
    self._wrappedData.peaks =  [x._wrappedData for x in value]

  @property
  def targetValue(self) -> float:
    """targetValue of constraint - consensus of all contributions or None"""
    aSet = set(x.targetValue for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @targetValue.setter
  def targetValue(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.targetValue = value

  @property
  def error(self) -> float:
    """error of restraint - consensus of all contributions or None"""
    aSet = set(x.error for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @error.setter
  def error(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.error = value

  @property
  def weight(self) -> float:
    """weight of restraint - consensus of all contributions or None"""
    aSet = set(x.weight for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @weight.setter
  def weight(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.weight = value

  @property
  def upperLimit(self) -> float:
    """upperLimit of restraint - consensus of all contributions or None"""
    aSet = set(x.upperLimit for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @upperLimit.setter
  def upperLimit(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.upperLimit = value

  @property
  def lowerLimit(self) -> float:
    """lowerLimit of restraint - consensus of all contributions or None"""
    aSet = set(x.lowerLimit for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @lowerLimit.setter
  def lowerLimit(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.lowerLimit = value

  @property
  def additionalUpperLimit(self) -> float:
    """additionalUpperLimit of restraint - consensus of all contributions or None"""
    aSet = set(x.additionalUpperLimit for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @additionalUpperLimit.setter
  def additionalUpperLimit(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.additionalUpperLimit = value

  @property
  def additionalLowerLimit(self) -> float:
    """additionalLowerLimit of restraint - consensus of all contributions or None"""
    aSet = set(x.additionalLowerLimit for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @additionalLowerLimit.setter
  def additionalLowerLimit(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.additionalLowerLimit = value
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:RestraintList)-> list:
    """get wrappedData - all Constraint children of parent ConstraintList"""
    return parent._wrappedData.sortedConstraints()

# Connections to parents:
RestraintList._childClasses.append(Restraint)

def newRestraint(parent:RestraintList,comment:str=None,
                         peaks:Sequence=()) -> Restraint:
  """Create new child RdcRestraint"""
  apiConstraintList = parent._wrappedData
  creator = apiConstraintList.getattr("new%sConstraint" % parent.restraintType)
  obj = creator(details=comment, peaks=peaks)
  return parent._project._data2Obj.get(obj)

def makeSimpleRestraint(parent:RestraintList,comment:str=None,
                        peaks:Sequence=(),  targetValue:float=None, error:float=None,
                        weight:float=None, upperLimit:float=None,  lowerLimit:float=None,
                        additionalUpperLimit:float=None, additionalLowerLimit:float=None,
                        restraintItems:Sequence=()) -> Restraint:

  restraint = parent.newRestraint(comment=comment, peaks=peaks)
  restraint.newRestraintContribution(targetValue=targetValue,error=error, weight=weight,
                            upperLimit=upperLimit, lowerLimit=lowerLimit,
                            additionalUpperLimit=additionalUpperLimit,
                            additionalLowerLimit=additionalLowerLimit,
                            restraintItems=restraintItems)
  #
  return restraint

RestraintList.newRestraint = newRestraint
RestraintList.makeSimpleRestraint = makeSimpleRestraint

# Notifiers:
for clazz in ApiAbstractConstraint._metaclass.getNonAbstractSubtypes():
  className = clazz.qualifiedName()
  Project._apiNotifiers.extend(
    ( ('_newObject', {'cls':RestraintList}, className, '__init__'),
      ('_finaliseDelete', {}, className, 'delete')
    )
)