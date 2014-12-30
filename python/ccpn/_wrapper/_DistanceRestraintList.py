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

from ccpn._wrapper._AbstractRestraintList import AbstractRestraintList
from ccpn._wrapper._Project import Project
from ccpn._wrapper._RestraintSet import RestraintSet
from ccpncore.api.ccp.nmr.NmrConstraint import DistanceConstraintList


class DistanceRestraintList(AbstractRestraintList):
  """Peak List."""
  
  #: Short class name, for PID.
  shortClassName = 'DL'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = 2

  #: Name of plural link to instances of class
  _pluralLinkName = 'distanceRestraintLists'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnDistanceRestraintList(self) -> DistanceConstraintList:
    """ CCPN DistanceConstraintList matching DistanceRestraintList"""
    return self._wrappedData
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: RestraintSet)-> list:
    """get wrappedData - all DistanceConstraintList children of parent NmrConstraintStore"""
    return [x for x in parent._wrappedData.sortedConstraintLists()
            if x.className == 'DistanceConstraintList']

# Connections to parents:
RestraintSet._childClasses.append(DistanceRestraintList)

def newDistanceRestraintList(parent:RestraintSet,name:str=None, comment:str=None,
                             unit:str=None, potentialType:str=None) -> DistanceRestraintList:
  """Create new child DistanceRestraintList"""
  nmrConstraintStore = parent._wrappedData
  nmrConstraintStore.newDistanceConstraintList(name=name, details=comment, unit=unit,
                                               potentialType=potentialType)

RestraintSet.newPeakList = newDistanceRestraintList

# Notifiers:
className = DistanceConstraintList._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':DistanceRestraintList}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
