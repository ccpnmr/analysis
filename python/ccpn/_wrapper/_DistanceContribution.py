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
from ccpn._wrapper._AbstractRestraintContribution import AbstractRestraintContribution
from ccpn._wrapper._Project import Project
from ccpn._wrapper._DistanceRestraint import DistanceRestraint
from ccpncore.api.ccp.nmr.NmrConstraint import DistanceContribution as CcpnDistanceContribution


class DistanceContribution(AbstractRestraintContribution):
  """Distance Contribution."""
  
  #: Short class name, for PID.
  shortClassName = 'DC'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = DistanceRestraint.restraintItemLength

  #: Name of plural link to instances of class
  _pluralLinkName = 'distanceContributions'
  
  #: List of child classes.
  _childClasses = []


  # CCPN properties  
  @property
  def ccpnContribution(self) -> DistanceContribution:
    """ CCPN DistanceContribution matching DistanceContribution"""
    return self._wrappedData

  @property
  def _parent(self) -> DistanceRestraint:
    """Parent (containing) object."""
    return  self._project._data2Obj[self._wrappedData.distanceConstraint]
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:DistanceRestraint)-> list:
    """get wrappedData - all DistanceConstraint children of parent DistanceConstraintList"""
    return parent._wrappedData.sortedContributions()

# Connections to parents:
DistanceRestraint._childClasses.append(DistanceContribution)

def newContribution(parent:DistanceRestraint, targetValue:float=None, error:float=None,
                    weight:float=None, upperLimit:float=None,  lowerLimit:float=None,
                    additionalUpperLimit:float=None, additionalLowerLimit:float=None,
                    restraintItems:Sequence=()) -> DistanceContribution:
  """Create new child DistanceContribution"""
  constraint = parent._wrappedData
  obj = constraint.newDistanceContribution(targetValue=targetValue, error=error,
                                           weight=weight, upperLimit=upperLimit,
                                           lowerLimit=lowerLimit,
                                           additionalUpperLimit=additionalUpperLimit,
                                           additionalLowerLimit=additionalLowerLimit)
  result = parent._project._data2Obj.get(obj)
  result.restraintItems = restraintItems
  return result

DistanceRestraint.newRestraint = newContribution

# Notifiers:
className = DistanceContribution._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':DistanceContribution}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
