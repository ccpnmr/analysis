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
from ccpn._wrapper._AbstractRestraint import AbstractRestraint
from ccpn._wrapper._Project import Project
from ccpn._wrapper._HBondRestraintList import HBondRestraintList
from ccpncore.api.ccp.nmr.NmrConstraint import HBondConstraint


class HBondRestraint(AbstractRestraint):
  """HBond Restraint."""
  
  #: Short class name, for PID.
  shortClassName = 'BR'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = HBondRestraintList.restraintItemLength

  #: Name of plural link to instances of class
  _pluralLinkName = 'hBondRestraints'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnRestraint(self) -> HBondConstraint:
    """ CCPN HBondConstraint matching HBondRestraint"""
    return self._wrappedData

  @property
  def _parent(self) -> HBondRestraintList:
    """Parent (containing) object."""
    return  self._project._data2Obj[self._wrappedData.parentList]
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:HBondRestraintList)-> list:
    """get wrappedData - all HBondConstraint children of parent HBondConstraintList"""
    return parent._wrappedData.sortedConstraints()

# Connections to parents:
HBondRestraintList._childClasses.append(HBondRestraint)

def newRestraint(parent:HBondRestraintList,comment:str=None,
                         peaks:Sequence=()) -> HBondRestraint:
  """Create new child HBondRestraint"""
  constraintList = parent._wrappedData
  obj = constraintList.newHBondConstraint(details=comment, peaks=peaks)
  return parent._project._data2Obj.get(obj)

def makeSimpleRestraint(parent:HBondRestraintList,comment:str=None,
                        peaks:Sequence=(),  targetValue:float=None, error:float=None,
                        weight:float=None, upperLimit:float=None,  lowerLimit:float=None,
                        additionalUpperLimit:float=None, additionalLowerLimit:float=None,
                        restraintItems:Sequence=()) -> HBondRestraint:

  restraint = parent.newRestraint(comment=comment, peaks=peaks)
  restraint.newContribution(targetValue=targetValue,error=error, weight=weight,
                            upperLimit=upperLimit, lowerLimit=lowerLimit,
                            additionalUpperLimit=additionalUpperLimit,
                            additionalLowerLimit=additionalLowerLimit,
                            restraintItems=restraintItems)
  #
  return restraint

HBondRestraintList.newRestraint = newRestraint
HBondRestraintList.makeSimpleRestraint = makeSimpleRestraint

# Notifiers:
className = HBondConstraint._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':HBondRestraint}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
