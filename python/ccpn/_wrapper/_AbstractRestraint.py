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

class AbstractRestaint(AbstractWrapperClass):
  """Abstract restraint."""
  
  #: Short class name, for PID.
  shortClassName = None

  # CCPN properties
  @property
  def id(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def peaks(self) -> tuple:
    """peaks used to derive restraint"""
    ff = self._project._data2Obj.get
    return tuple(ff(x) for x in self._wrappedData.peaks)

  @peaks.setter
  def peaks(self, value:Sequence):
    self._wrappedData.peaks =  [x._wrappedData for x in value]

  @property
  def targetValue(self) -> float:
    """targetValue of constraint - consensus of all contributions or None"""
    aSet = set(x.targetValue for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @targetValue.setter
  def targetValue(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.targetValue = value

  @property
  def error(self) -> float:
    """error of constraint - consensus of all contributions or None"""
    aSet = set(x.error for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @error.setter
  def error(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.error = value

  @property
  def weight(self) -> float:
    """weight of constraint - consensus of all contributions or None"""
    aSet = set(x.weight for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @weight.setter
  def weight(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.weight = value

  @property
  def upperLimit(self) -> float:
    """upperLimit of constraint - consensus of all contributions or None"""
    aSet = set(x.upperLimit for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @upperLimit.setter
  def upperLimit(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.upperLimit = value

  @property
  def lowerLimit(self) -> float:
    """lowerLimit of constraint - consensus of all contributions or None"""
    aSet = set(x.lowerLimit for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @lowerLimit.setter
  def lowerLimit(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.lowerLimit = value

  @property
  def additionalUpperLimit(self) -> float:
    """additionalUpperLimit of constraint - consensus of all contributions or None"""
    aSet = set(x.additionalUpperLimit for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @additionalUpperLimit.setter
  def additionalUpperLimit(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.additionalUpperLimit = value

  @property
  def additionalLowerLimit(self) -> float:
    """additionalLowerLimit of constraint - consensus of all contributions or None"""
    aSet = set(x.additionalLowerLimit for x in self._wrappedData.contributions)
    if len(aSet) == 1:
      return aSet.pop()
    else:
      return None

  @additionalLowerLimit.setter
  def additionalLowerLimit(self, value:float):
    for contribution in self._wrappedData.contributions:
      contribution.additionalLowerLimit = value
    
  # Implementation functions

# Connections to parents:

# Notifiers: