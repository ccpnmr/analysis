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
from ccpn._wrapper._RdcRestraintList import RdcRestraintList
from ccpncore.api.ccp.nmr.NmrConstraint import RdcConstraint


class RdcRestraint(AbstractRestraint):
  """Rdc Restraint."""
  
  #: Short class name, for PID.
  shortClassName = 'RR'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = RdcRestraintList.restraintItemLength

  #: Name of plural link to instances of class
  _pluralLinkName = 'rdcRestraints'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnRestraint(self) -> RdcConstraint:
    """ CCPN RdcConstraint matching RdcRestraint"""
    return self._wrappedData

  @property
  def _parent(self) -> RdcRestraintList:
    """Parent (containing) object."""
    return  self._project._data2Obj[self._wrappedData.rdcConstraintList]
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:RdcRestraintList)-> list:
    """get wrappedData - all RdcConstraint children of parent RdcConstraintList"""
    return parent._wrappedData.sortedConstraints()

# Connections to parents:
RdcRestraintList._childClasses.append(RdcRestraint)

def newRestraint(parent:RdcRestraintList,comment:str=None,
                         peaks:Sequence=()) -> RdcRestraint:
  """Create new child RdcRestraint"""
  constraintList = parent._wrappedData
  obj = constraintList.newRdcConstraint(details=comment, peaks=peaks)
  return parent._project._data2Obj.get(obj)

def makeSimpleRestraint(parent:RdcRestraintList,comment:str=None,
                        peaks:Sequence=(),  targetValue:float=None, error:float=None,
                        weight:float=None, upperLimit:float=None,  lowerLimit:float=None,
                        additionalUpperLimit:float=None, additionalLowerLimit:float=None,
                        restraintItems:Sequence=()) -> RdcRestraint:

  restraint = parent.newRestraint(comment=comment, peaks=peaks)
  restraint.newContribution(targetValue=targetValue,error=error, weight=weight,
                            upperLimit=upperLimit, lowerLimit=lowerLimit,
                            additionalUpperLimit=additionalUpperLimit,
                            additionalLowerLimit=additionalLowerLimit,
                            restraintItems=restraintItems)
  #
  return restraint

RdcRestraintList.newRestraint = newRestraint
RdcRestraintList.makeSimpleRestraint = makeSimpleRestraint

# Notifiers:
className = RdcConstraint._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':RdcRestraint}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
