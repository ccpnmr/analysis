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
from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject

class AbstractRestraintContribution(AbstractWrapperObject):
  """Abstract restraint contribution."""
  
  #: Short class name, for PID.
  shortClassName = None

  # Tag for Item creation function
  newItemFuncName = None

  # CCPN properties
  @property
  def id(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for Peak"""
    return self._wrappedData.serial

  @property
  def targetValue(self) -> float:
    """targetValue of contribution """
    return str(self._wrappedData.targetValue)

  @targetValue.setter
  def targetValue(self, value:float):
    self._wrappedData.targetValue = value

  @property
  def error(self) -> float:
    """error of contribution """
    return str(self._wrappedData.error)

  @error.setter
  def error(self, value:float):
    self._wrappedData.error = value

  @property
  def weight(self) -> float:
    """weight of contribution """
    return str(self._wrappedData.weight)

  @weight.setter
  def weight(self, value:float):
    self._wrappedData.weight = value

  @property
  def upperLimit(self) -> float:
    """upperLimit of contribution """
    return str(self._wrappedData.upperLimit)

  @upperLimit.setter
  def upperLimit(self, value:float):
    self._wrappedData.upperLimit = value

  @property
  def lowerLimit(self) -> float:
    """lowerLimit of contribution """
    return str(self._wrappedData.lowerLimit)

  @lowerLimit.setter
  def lowerLimit(self, value:float):
    self._wrappedData.lowerLimit = value

  @property
  def additionalUpperLimit(self) -> float:
    """additionalUpperLimit of contribution """
    return str(self._wrappedData.additionalUpperLimit)

  @additionalUpperLimit.setter
  def additionalUpperLimit(self, value:float):
    self._wrappedData.additionalUpperLimit = value

  @property
  def additionalLowerLimit(self) -> float:
    """additionalLowerLimit of contribution """
    return str(self._wrappedData.additionalLowerLimit)

  @additionalLowerLimit.setter
  def additionalLowerLimit(self, value:float):
    self._wrappedData.additionalLowerLimit = value

  @property
  def restraintItems(self) -> tuple:
    """restraint items of contribution """

    # NBNB TBD must be overridden for restraints with one-resonance items

    result = []
    ff = self._project._data2Obj.get
    sortkey = self._project._pidSortKey
    for ccpnItem in self._wrappedData.items:
      assignments = [ff(x)._pid for x in ccpnItem.resonances]
      if sortkey(assignments[0]) > sortkey(assignments[-1]):
        # order so smallest string comes first
        # NB This assumes that assignments are either length 2 or ordered (as is so far the case)
        assignments.reverse()
      result.append(tuple(assignments))
    #
      return tuple(sorted(result, key=sortkey))

  @restraintItems.setter
  def restraintItems(self, value:Sequence):

    # NBNB TBD must be overridden for restraints with one-resonance items

    for ll in value:
      # make new items
      if len(ll) != self.restraintItemLength:
        raise ValueError("RestraintItems must have length %s: %s" % (self.restraintItemLength, ll))

    ccpnContribution = self._wrappedData
    for item in ccpnContribution.items:
      # remove old items
      item.delete()

    fetchFixedResonance = self._parent._parent._fetchFixedResonance
    for ll in value:
      # make new items
      getattr(ccpnContribution, self._newItemFuncName)(
        resonances=fetchFixedResonance(pid) for pid in ll)
    
  # Implementation functions

# Connections to parents:

# Notifiers: