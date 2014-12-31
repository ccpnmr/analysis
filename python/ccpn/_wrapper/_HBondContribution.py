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
from ccpn._wrapper._HBondRestraint import HBondRestraint
from ccpncore.api.ccp.nmr.NmrConstraint import HBondContribution as Ccpn_HBondContribution


class HBondContribution(AbstractRestraintContribution):
  """HBond Contribution."""
  
  #: Short class name, for PID.
  shortClassName = 'BC'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = HBondRestraint.restraintItemLength

  #: Name of plural link to instances of class
  _pluralLinkName = 'hBondContributions'
  
  #: List of child classes.
  _childClasses = []


  # CCPN properties  
  @property
  def ccpnContribution(self) -> HBondContribution:
    """ CCPN HBondContribution matching HBondContribution"""
    return self._wrappedData

  @property
  def _parent(self) -> HBondRestraint:
    """Parent (containing) object."""
    return  self._project._data2Obj[self._wrappedData.hBondConstraint]
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:HBondRestraint)-> list:
    """get wrappedData - all HBondConstraint children of parent HBondConstraintList"""
    return parent._wrappedData.sortedContributions()

# Connections to parents:
HBondRestraint._childClasses.append(HBondContribution)

def newContribution(parent:HBondRestraint, targetValue:float=None, error:float=None,
                    weight:float=None, upperLimit:float=None,  lowerLimit:float=None,
                    additionalUpperLimit:float=None, additionalLowerLimit:float=None,
                    restraintItems:Sequence=()) -> HBondContribution:
  """Create new child HBondContribution"""
  constraint = parent._wrappedData
  obj = constraint.newHBondContribution(targetValue=targetValue, error=error,
                                           weight=weight, upperLimit=upperLimit,
                                           lowerLimit=lowerLimit,
                                           additionalUpperLimit=additionalUpperLimit,
                                           additionalLowerLimit=additionalLowerLimit)
  result = parent._project._data2Obj.get(obj)
  result.restraintItems = restraintItems
  return result

HBondRestraint.newRestraint = newContribution

# Notifiers:
className = Ccpn_HBondContribution._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':HBondContribution}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
