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
from ccpncore.api.ccp.nmr.NmrConstraint import RdcConstraintList


class RdcRestraintList(AbstractRestraintList):
  """Peak List."""
  
  #: Short class name, for PID.
  shortClassName = 'RL'

  # Number of atoms in a Restraint item - set in subclasses
  restraintItemLength = 2

  #: Name of plural link to instances of class
  _pluralLinkName = 'rdcRestraintLists'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnRdcRestraintList(self) -> RdcConstraintList:
    """ CCPN RdcConstraintList matching RdcRestraintList"""
    return self._wrappedData

  @property
  def tensorMagnitude(self) -> float:
    """magnitude of orientation tensor """
    return self._wrappedData.tensorMagnitude

  @tensorMagnitude.setter
  def tensorMagnitude(self, value:float):
    self._wrappedData.tensorMagnitude = value

  @property
  def tensorRhombicity(self) -> float:
    """rhombicity of orientation tensor """
    return self._wrappedData.tensorRhombicity

  @tensorRhombicity.setter
  def tensorRhombicity(self, value:float):
    self._wrappedData.tensorRhombicity = value

  @property
  def tensorChainCode(self) -> str:
    """Chain code of residue anchoring orientation tensor"""
    return self._wrappedData.tensorChainCode

  @tensorChainCode.setter
  def tensorChainCode(self, value:str):
    self._wrappedData.tensorChainCode = value

  @property
  def tensorSequenceCode(self) -> str:
    """Sequence code of residue anchoring orientation tensor"""
    return self._wrappedData.tensorSequenceCode

  @tensorSequenceCode.setter
  def tensorSequenceCode(self, value:str):
    self._wrappedData.tensorSequenceCode = value

  @property
  def tensorResidueType(self) -> str:
    """Residue Type of residue anchoring orientation tensor"""
    return self._wrappedData.tensorResidueType

  @tensorResidueType.setter
  def tensorResidueType(self, value:str):
    self._wrappedData.tensorResidueType = value
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: RestraintSet)-> list:
    """get wrappedData - all RdcConstraintList children of parent NmrConstraintStore"""
    return [x for x in parent._wrappedData.sortedConstraintLists()
            if x.className == 'RdcConstraintList']

# Connections to parents:
RestraintSet._childClasses.append(RdcRestraintList)

def newRdcRestraintList(parent:RestraintSet,name:str=None, comment:str=None,
                             unit:str=None, potentialType:str=None) -> RdcRestraintList:
  """Create new child RdcRestraintList"""
  nmrConstraintStore = parent._wrappedData
  obj = nmrConstraintStore.newRdcConstraintList(name=name, details=comment, unit=unit,
                                                potentialType=potentialType)
  return parent._project._data2Obj.get(obj)

RestraintSet.newPeakList = newRdcRestraintList

# Notifiers:
className = RdcConstraintList._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':RdcRestraintList}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
