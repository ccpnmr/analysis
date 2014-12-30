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

from ccpn._wrapper._AbstractWrapperClass import AbstractWrapperClass
from ccpn._wrapper._Project import Project
from ccpncore.api.ccp.nmr.NmrConstraint import NmrConstraintStore


class RestraintSet(AbstractWrapperClass):
  """Restraint set."""
  
  #: Short class name, for PID.
  shortClassName = 'RS'

  #: Name of plural link to instances of class
  _pluralLinkName = 'restraintSets'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def nmrConstraintStore(self) -> NmrConstraintStore:
    """ CCPN NmrConstraintStore matching RestraintSet"""
    return self._wrappedData

    
  @property
  def id(self) -> str:
    """short form of name, used for id"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for RestraintSet"""
    return self._wrappedData.serial
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all NmrConstraintStores linked to NmrProject"""
    return parent._wrappedData.sortedNmrConstraintStores()


def newRestraintSet(parent:Project, comment:str=None) -> RestraintSet:
  """Create new empty child NmrConstraintStores

  :param str comment: comment for new chain (optional)"""
  
  nmrProject = parent._wrappedData
  newNmrConstraintStore = nmrProject.root.newNmrConstraintStore(nmrProject=nmrProject,
                                                         details=comment)

  return parent._data2Obj.get(newNmrConstraintStore)

    
    
# Connections to parents:
Project._childClasses.append(RestraintSet)
Project.newRestraintSet = newRestraintSet

# Notifiers:
className = NmrConstraintStore._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':RestraintSet}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
