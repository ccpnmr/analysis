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
from ccpn._wrapper._DistanceRestraintList import DistanceRestraintList
from ccpncore.api.ccp.nmr.NmrConstraint import DistanceConstraint


class DistanceRestraint(AbstractRestraint):
  """Distance Restraint."""
  
  #: Short class name, for PID.
  shortClassName = 'DR'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = DistanceRestraintList.restraintItemLength

  #: Name of plural link to instances of class
  _pluralLinkName = 'distanceRestraints'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnDistanceRestraint(self) -> DistanceConstraint:
    """ CCPN DistanceConstraint matching DistanceRestraint"""
    return self._wrappedData
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:DistanceRestraintList)-> list:
    """get wrappedData - all DistanceConstraint children of parent DistanceConstraintList"""
    return parent._wrappedData.sortedConstraints()

# Connections to parents:
DistanceRestraintList._childClasses.append(DistanceRestraint)

def newDistanceRestraint(parent:DistanceRestraintList,comment:str=None, peaks:Sequence,
                         targetValue) -> DistanceRestraint:
  """Create new child DistanceRestraint"""
  constraintList = parent._wrappedData
  constraintList.newDistanceConstraint(name=name, details=comment, unit=unit,
                                               potentialType=potentialType)

DistanceRestraintList.newPeakList = newDistanceRestraint

# Notifiers:
className = DistanceConstraint._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':DistanceRestraint}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
