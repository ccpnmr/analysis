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
from ccpn._wrapper._DihedralRestraintList import DihedralRestraintList
from ccpncore.api.ccp.nmr.NmrConstraint import DihedralConstraint


class DihedralRestraint(AbstractRestraint):
  """Dihedral Restraint."""
  
  #: Short class name, for PID.
  shortClassName = 'HR'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = DihedralRestraintList.restraintItemLength

  #: Name of plural link to instances of class
  _pluralLinkName = 'dihedralRestraints'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnRestraint(self) -> DihedralConstraint:
    """ CCPN DihedralConstraint matching DihedralRestraint"""
    return self._wrappedData

  @property
  def _parent(self) -> DihedralRestraintList:
    """Parent (containing) object."""
    return  self._project._data2Obj[self._wrappedData.parentList]
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:DihedralRestraintList)-> list:
    """get wrappedData - all DihedralConstraint children of parent DihedralConstraintList"""
    return parent._wrappedData.sortedConstraints()

# Connections to parents:
DihedralRestraintList._childClasses.append(DihedralRestraint)

def newRestraint(parent:DihedralRestraintList,comment:str=None,
                         peaks:Sequence=()) -> DihedralRestraint:
  """Create new child DihedralRestraint"""
  constraintList = parent._wrappedData
  obj = constraintList.newDihedralConstraint(details=comment, peaks=peaks)
  return parent._project._data2Obj.get(obj)

def makeSimpleRestraint(parent:DihedralRestraintList,comment:str=None,
                        peaks:Sequence=(),  targetValue:float=None, error:float=None,
                        weight:float=None, upperLimit:float=None,  lowerLimit:float=None,
                        additionalUpperLimit:float=None, additionalLowerLimit:float=None,
                        restraintItems:Sequence=()) -> DihedralRestraint:

  restraint = parent.newRestraint(comment=comment, peaks=peaks)
  restraint.newContribution(targetValue=targetValue,error=error, weight=weight,
                            upperLimit=upperLimit, lowerLimit=lowerLimit,
                            additionalUpperLimit=additionalUpperLimit,
                            additionalLowerLimit=additionalLowerLimit,
                            restraintItems=restraintItems)
  #
  return restraint

DihedralRestraintList.newRestraint = newRestraint
DihedralRestraintList.makeSimpleRestraint = makeSimpleRestraint

# Notifiers:
className = DihedralConstraint._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':DihedralRestraint}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
