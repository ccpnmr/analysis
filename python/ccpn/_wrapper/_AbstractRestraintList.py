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

from ccpn._wrapper._AbstractWrapperClass import AbstractWrapperClass
from ccpn._wrapper._RestraintSet import RestraintSet

class AbstractRestraintList(AbstractWrapperClass):
  """ Abstract RestraintList - superclass of actual restraint lists."""
  
  #: Short class name, for PID.
  shortClassName = None

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = None

  # CCPN properties
  @property
  def id(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for PeakList"""
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> RestraintSet:
    """Parent (containing) object."""
    return  self._project._data2Obj[self._wrappedData.nmrConstraintStore]
  
  restraintSet = _parent
  
  @property
  def name(self) -> str:
    """name of Restraint List"""
    return self._wrappedData.name
    
  @name.setter
  def name(self, value:str):
    self._wrappedData.name = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def unit(self) -> str:
    """Unit for restraints"""
    return self._wrappedData.unit

  @unit.setter
  def unit(self, value:str):
    self._wrappedData.unit = value

  @property
  def potentialType(self) -> str:
    """Potential type for restraints"""
    return self._wrappedData.potentialType

  @potentialType.setter
  def potentialType(self, value:str):
    self._wrappedData.potentialType = value
    
  # Implementation functions

# Connections to parents:

# Notifiers:
