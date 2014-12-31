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
from ccpncore.api.ccp.nmr.NmrConstraint import DihedralConstraintList


class DihedralRestraintList(AbstractRestraintList):
  """Peak List."""
  
  #: Short class name, for PID.
  shortClassName = 'HL'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = 4

  #: Name of plural link to instances of class
  _pluralLinkName = 'dihedralRestraintLists'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnDihedralRestraintList(self) -> DihedralConstraintList:
    """ CCPN DihedralConstraintList matching DihedralRestraintList"""
    return self._wrappedData
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: RestraintSet)-> list:
    """get wrappedData - all DihedralConstraintList children of parent NmrConstraintStore"""
    return [x for x in parent._wrappedData.sortedConstraintLists()
            if x.className == 'DihedralConstraintList']

# Connections to parents:
RestraintSet._childClasses.append(DihedralRestraintList)

def newDihedralRestraintList(parent:RestraintSet,name:str=None, comment:str=None,
                             unit:str=None, potentialType:str=None) -> DihedralRestraintList:
  """Create new child DihedralRestraintList"""
  nmrConstraintStore = parent._wrappedData
  obj = nmrConstraintStore.newDihedralConstraintList(name=name, details=comment, unit=unit,
                                                     potentialType=potentialType)
  return parent._project._data2Obj.get(obj)

RestraintSet.newPeakList = newDihedralRestraintList

# Notifiers:
className = DihedralConstraintList._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':DihedralRestraintList}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
