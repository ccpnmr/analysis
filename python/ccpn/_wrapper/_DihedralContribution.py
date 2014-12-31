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
from ccpn._wrapper._DihedralRestraint import DihedralRestraint
from ccpncore.api.ccp.nmr.NmrConstraint import DihedralContribution as Ccpn_DihedralContribution


class DihedralContribution(AbstractRestraintContribution):
  """Dihedral Contribution."""
  
  #: Short class name, for PID.
  shortClassName = 'HC'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = DihedralRestraint.restraintItemLength

  #: Name of plural link to instances of class
  _pluralLinkName = 'dihedralContributions'
  
  #: List of child classes.
  _childClasses = []


  # CCPN properties  
  @property
  def ccpnContribution(self) -> DihedralContribution:
    """ CCPN DihedralContribution matching DihedralContribution"""
    return self._wrappedData

  @property
  def _parent(self) -> DihedralRestraint:
    """Parent (containing) object."""
    return  self._project._data2Obj[self._wrappedData.dihedralConstraint]
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:DihedralRestraint)-> list:
    """get wrappedData - all DihedralConstraint children of parent DihedralConstraintList"""
    return parent._wrappedData.sortedContributions()

# Connections to parents:
DihedralRestraint._childClasses.append(DihedralContribution)

def newContribution(parent:DihedralRestraint, targetValue:float=None, error:float=None,
                    weight:float=None, upperLimit:float=None,  lowerLimit:float=None,
                    additionalUpperLimit:float=None, additionalLowerLimit:float=None,
                    restraintItems:Sequence=()) -> DihedralContribution:
  """Create new child DihedralContribution"""
  constraint = parent._wrappedData
  obj = constraint.newDihedralContribution(targetValue=targetValue, error=error,
                                           weight=weight, upperLimit=upperLimit,
                                           lowerLimit=lowerLimit,
                                           additionalUpperLimit=additionalUpperLimit,
                                           additionalLowerLimit=additionalLowerLimit)
  result = parent._project._data2Obj.get(obj)
  result.restraintItems = restraintItems
  return result

DihedralRestraint.newRestraint = newContribution

# Notifiers:
className = Ccpn_DihedralContribution._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':DihedralContribution}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
