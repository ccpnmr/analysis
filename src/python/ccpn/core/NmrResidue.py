"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================

import collections
from typing import Tuple, Optional
from typing import Union

from ccpn.core.NmrChain import NmrChain
from ccpn.core.Project import Project
from ccpn.core.Residue import Residue
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import CcpnSorting
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.lib import Util as modelUtil
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiResonanceGroup
from ccpnmodel.ccpncore.lib import Constants
#from ccpnmodel.ccpncore.lib.molecule import MoleculeQuery


class NmrResidue(AbstractWrapperObject):
  """Nmr Residue, for assignment."""
  
  #: Short class name, for PID.
  shortClassName = 'NR'
  # Attribute it necessary as subclasses must use superclass className
  className = 'NmrResidue'

  _parentClass = NmrChain

  #: Name of plural link to instances of class
  _pluralLinkName = 'nmrResidues'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiResonanceGroup._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiResonanceGroup(self) -> ApiResonanceGroup:
    """ CCPN resonanceGroup matching Residue"""
    return self._wrappedData
  
  
  @property
  def sequenceCode(self) -> str:
    """Residue sequence code and id (e.g. '1', '127B', '\@157+1)
    Names of the form '\@ijk' ,'\@ijk+n', and '\@ijk-n' (where ijk and n are integers)
    are reserved and cannot be set. They are obtained by the deassign command."""
    return self._wrappedData.sequenceCode

  @property
  def serial(self) -> int:
    """NmrResidue serial number - set at creation and unchangeable"""
    return self._wrappedData.serial

  @property
  def _key(self) -> str:
    """Residue local ID"""
    return Pid.createId(self.sequenceCode, self.residueType)
    
  @property
  def _parent(self) -> NmrChain:
    """NmrChain containing NmrResidue. Use self.assignTo to reset the NmrChain"""
    return self._project._data2Obj[self._wrappedData.nmrChain]
  
  nmrChain = _parent

  @property
  def residueType(self) -> str:
    """Residue type string (e.g. 'ALA'). Part of id. Use self.assignTo or self.rename to reset the residueType"""
    apiResonanceGroup = self._wrappedData
    apiResidue = apiResonanceGroup.assignedResidue
    if apiResidue is None:
      return apiResonanceGroup.residueType or ''
    else:
      return apiResidue.code3Letter

  @property
  def relativeOffset(self) -> Optional[int]:
    """Sequential offset of NmrResidue relative to mainNmrResidue
    May be 0. Is None for residues that are not offset."""
    return self._wrappedData.relativeOffset

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def residue(self) -> Residue:
    """Residue to which NmrResidue is assigned"""
    residue = self._wrappedData.assignedResidue
    return None if residue is None else self._project._data2Obj.get(residue)

  @residue.setter
  def residue(self, value:Residue):
    self._wrappedData.assignedResidue = None if value is None else value._wrappedData

  @property
  def offsetNmrResidues(self) -> Tuple['NmrResidue', ...]:
    """"All other NmrResidues with the same sequenceCode sorted by offSet suffix '-1', '+1', etc."""
    getDataObj = self._project._data2Obj.get
    return tuple(getDataObj(x) for x in self._wrappedData.offsetResonanceGroups)

  def getOffsetNmrResidue(self, offset:int) -> Optional['NmrResidue']:
    """Get offset NmrResidue with indicated offset
    (or None, if no such offset NmrResidue exists"""
    for result in self.offsetNmrResidues:
      if result.relativeOffset == offset:
        return result
    #
    return None

  @property
  def mainNmrResidue(self) -> Optional['NmrResidue']:
    """Main NmrResidue (self, or the residue that self is offset relative to"""
    return self._project._data2Obj.get(self._wrappedData.mainResonanceGroup)

  @property
  def nextNmrResidue(self) -> Optional['NmrResidue']:
    """Next sequentially connected NmrResidue (or None, as appropriate).
    Either from a connected NmrChain,
    or the NmrResidue assigned to the next Residue in the same Chain"""

    apiResonanceGroup = self._wrappedData
    apiNmrChain = apiResonanceGroup.directNmrChain
    residue = self.residue

    result = None

    if apiNmrChain and apiNmrChain.isConnected:
      # Connected stretch
      stretch = apiNmrChain.mainResonanceGroups
      if apiResonanceGroup is stretch[-1]:
        result = None
      else:
        result = self._project._data2Obj.get(stretch[stretch.index(apiResonanceGroup) + 1])

    elif residue:
      # Assigned to residue
      nextResidue = residue.nextResidue
      if nextResidue:
        result = nextResidue.nmrResidue
    #
    return result

  def connectNext(self, value:Union['NmrResidue', str]) -> NmrChain:
    """Connect free end of self to free end of next residue in sequence,
    and return resulting connected NmrChain

    Raises error if self is assigned, of if either self or value is offset.

    NB Undoing a connection between two connected stretches
    will get back a 'value' stretch with a new shortName"""
    apiResonanceGroup = self._wrappedData
    # apiResidue = apiResonanceGroup.assignedResidue
    apiNmrChain = apiResonanceGroup.directNmrChain

    project = self._project

    if value is None:
      raise ValueError("Cannot connect to value: None")
    elif isinstance(value, str):
      xx = project.getByPid(value)
      if xx is None:
        raise ValueError("No object found matching Pid %s" % value)
      else:
        value = xx

    apiValueNmrChain = value._wrappedData.nmrChain

    if self.relativeOffset is not None:
      raise ValueError("Cannot connect from offset residue")

    elif value.relativeOffset is not None:
      raise ValueError("Cannot connect to offset NmrResidue")

    elif self.residue is not None:
      raise ValueError("Cannot connect assigned NmrResidue - assign the value instead")

    elif value.residue is not None:
      raise ValueError("Cannot connect to assigned NmrResidue - assign the NmrResidue instead")

    elif self.nextNmrResidue is not None:
      raise ValueError("Cannot connect next NmrResidue - it is already connected")

    elif value.previousNmrResidue is not None:
      raise ValueError("Cannot connect to next NmrResidue - it is already connected")

    elif apiNmrChain.isConnected and apiValueNmrChain is apiNmrChain:
      raise ValueError("Cannot make cyclical connected NmrChain")

    self._startFunctionCommandBlock('connectNext', value)
    try:
      if apiNmrChain.isConnected:
        # At this point, self must be the last NmrResidue in a connected chain
        if apiValueNmrChain.isConnected:
          undo = project._undo
          if undo is not None:
            undo.increaseBlocking()
          try:
            # Value is first NmrResidue in a connected NmrChain
            for rg in apiValueNmrChain.mainResonanceGroups:
              rg.directNmrChain = apiNmrChain
            apiValueNmrChain.delete()
          finally:
            if undo is not None:
              undo.decreaseBlocking()

          if undo is not None:
            undo.newItem(self.disconnectNext, self.connectNext, redoArgs=(value,))
        else:
          value._wrappedData.directNmrChain = apiNmrChain
        result = self.nmrChain

      else:
        # self is unassigned, unconnected NmrResidue
        if apiValueNmrChain.isConnected:
          # At this point value must be the first NmrResidue in a connected NmrChain
          undo = apiValueNmrChain.root._undo
          if undo is not None:
            undo.increaseBlocking()
          try:
            apiResonanceGroup.directNmrChain = apiValueNmrChain
            # Move self from last to first in target NmrChain
            ll = apiValueNmrChain.__dict__['mainResonanceGroups']
            ll.insert(0, ll.pop())
          finally:
            if undo is not None:
              undo.decreaseBlocking()

          if undo is not None:
            undo.newItem(apiResonanceGroup.setDirectNmrChain,
                         self.connectNext, undoArgs=(apiNmrChain,), redoArgs=(value,))
        else:
          newApiNmrChain = apiNmrChain.nmrProject.newNmrChain(isConnected=True)
          apiResonanceGroup.directNmrChain = newApiNmrChain
          value._wrappedData.directNmrChain = newApiNmrChain
        result = value.nmrChain
    finally:
      self._project._appBase._endCommandBlock()
    #
    return result

  def disconnectNext(self):
    """Cut connected NmrChain after NmrResidue, creating new connected NmrChain if necessary
    Does nothing if nextNmrResidue is empty;
    Raises ValueError for assigned NmrResidues"""


    apiResonanceGroup = self._wrappedData
    apiNmrChain = apiResonanceGroup.directNmrChain
    defaultChain =  apiNmrChain.nmrProject.findFirstNmrChain(code=Constants.defaultNmrChainCode)

    self._startFunctionCommandBlock('disconnectNext')
    try:
      if apiNmrChain is None:
        # offset residue: no-op
        return

      elif apiResonanceGroup.assignedResidue is not None:
        # Assigned residue with successor residue - error
        raise ValueError("Assigned NmrResidue %s cannot be disconnected" % self)

      if apiNmrChain.isConnected:
        # Connected stretch - break stretch, keeping first half in the NmrChain
        stretch = apiNmrChain.mainResonanceGroups

        if apiResonanceGroup is stretch[-1]:
          return

        if apiResonanceGroup is stretch[0]:
          # chop off end ResonanceGroup
          apiResonanceGroup.directNmrChain = defaultChain
          if len(stretch) == 2:
            stretch[1].directNmrChain = defaultChain
            # delete one-element remaining chain
            apiNmrChain.delete()

        elif apiResonanceGroup is stretch[-2]:
          # chop off end ResonanceGroup
          stretch[-1].directNmrChain = defaultChain

        else:
          # make new connected NmrChain with rightmost ResonanceGroups
          newNmrChain = apiNmrChain.nmrProject.newNmrChain(isConnected=True)
          for rg in reversed(stretch):
            if rg is apiResonanceGroup:
              break
            else:
              rg.directNmrChain = newNmrChain
          newNmrChain.__dict__['mainResonanceGroups'].reverse()
    finally:
      self._project._appBase._endCommandBlock()

  @property
  def previousNmrResidue(self) -> Optional['NmrResidue']:
    """Previous sequentially connected NmrResidue (or None, as appropriate).
    Either from a connected NmrChain,
    or the NmrResidue assigned to the previous Residue in the same Chain"""
    apiResonanceGroup = self._wrappedData
    apiNmrChain = apiResonanceGroup.directNmrChain
    residue = self.residue

    result = None

    if apiNmrChain and apiNmrChain.isConnected:
      # Connected stretch
      stretch = apiNmrChain.mainResonanceGroups
      if apiResonanceGroup is stretch[0]:
        result = None
      else:
        result = self._project._data2Obj.get(stretch[stretch.index(apiResonanceGroup) - 1])

    elif residue:
      # Assigned to residue
      previousResidue = residue.previousResidue
      if previousResidue:
        result = previousResidue.nmrResidue
    #
    return result

  def connectPrevious(self, value) -> NmrChain:
    """Connect free end of self to free end of previous residue in sequence,
    and return resulting connected NmrChain

    Raises error if self is assigned, of if either self or value is offset.

    NB Undoing a connection between two connected stretches
    will get back a 'value' stretch with a new shortName"""

    apiResonanceGroup = self._wrappedData
    # apiResidue = apiResonanceGroup.assignedResidue
    apiNmrChain = apiResonanceGroup.directNmrChain

    project = self._project

    if value is None:
      raise ValueError("Cannot connect to value: None")

    elif isinstance(value, str):
      xx = project.getByPid(value)
      if xx is None:
        raise ValueError("No object found matching Pid %s" % value)
      else:
        value = xx

    apiValueNmrChain = value._wrappedData.nmrChain


    if self.relativeOffset is not None:
      raise ValueError("Cannot connect from offset residue")

    elif value.relativeOffset is not None:
      raise ValueError("Cannot connect to offset NmrResidue")

    elif self.residue is not None:
      raise ValueError("Cannot connect assigned NmrResidue - assign the value instead")

    elif value.residue is not None:
      raise ValueError("Cannot connect to assigned NmrResidue - assign the NmrResidue instead")

    elif self.previousNmrResidue is not None:
      raise ValueError("Cannot connect previous NmrResidue - it is already connected")

    elif value.nextNmrResidue is not None:
      raise ValueError("Cannot connect to previous NmrResidue - it is already connected")

    elif apiNmrChain.isConnected and apiValueNmrChain is apiNmrChain:
      raise ValueError("Cannot make cyclical connected NmrChain")

    self._startFunctionCommandBlock('connectPrevious', value)
    try:
      if apiNmrChain.isConnected:
        # At this point, self must be the first NmrResidue in a connected chain
          undo = apiValueNmrChain.root._undo
          if undo is not None:
            undo.increaseBlocking()
          try:
            ll = apiNmrChain.__dict__['mainResonanceGroups']
            if apiValueNmrChain.isConnected:
              # Value is last NmrResidue in a connected NmrChain
              for rg in reversed(apiValueNmrChain.mainResonanceGroups):
                rg.directNmrChain = apiNmrChain
                ll.insert(0, ll.pop())
              apiValueNmrChain.delete()
              if undo is not None:
                undo.newItem(self.disconnectPrevious,
                             self.connectPrevious, redoArgs=(value,))
            else:
              value._wrappedData.directNmrChain = apiNmrChain
              # Move value from last to first in target NmrChain
              ll.insert(0, ll.pop())
              if undo is not None:
                undo.newItem(value._wrappedData.setDirectNmrChain, self.connectPrevious,
                             undoArgs=(apiValueNmrChain,), redoArgs=(value,))

          finally:
            if undo is not None:
              undo.decreaseBlocking()

          result = self.nmrChain

      else:
        # self is unassigned, unconnected NmrResidue
        if apiValueNmrChain.isConnected:
          # At this point value must be the last NmrResidue in a connected NmrChain
          apiResonanceGroup.directNmrChain = apiValueNmrChain
        else:
          newApiNmrChain = apiNmrChain.nmrProject.newNmrChain(isConnected=True)
          value._wrappedData.directNmrChain = newApiNmrChain
          apiResonanceGroup.directNmrChain = newApiNmrChain
        result = value.nmrChain
    finally:
      self._project._appBase._endCommandBlock()
    #
    return result

  def disconnectPrevious(self):
    """Cut connected NmrChain before NmrResidue, creating new connected NmrChain if necessary
    Does nothing if previousNmrResidue is empty;
    Deletes one-NmrResidue NmrChains  if generated
    Raises ValueError for assigned NmrResidues"""

    apiResonanceGroup = self._wrappedData
    apiNmrChain = apiResonanceGroup.directNmrChain
    defaultChain =  apiNmrChain.nmrProject.findFirstNmrChain(code=Constants.defaultNmrChainCode)

    self._startFunctionCommandBlock('disconnectPrevious')
    try:
      if apiNmrChain is None:
        # offset residue: no-op
        return

      elif apiResonanceGroup.assignedResidue is not None:
        # Assigned residue with successor residue - error
        raise ValueError("Assigned NmrResidue %s cannot be disconnected" % self)

      elif apiNmrChain.isConnected:
        # Connected stretch - break stretch, keeping first half in the NmrChain
        stretch = apiNmrChain.mainResonanceGroups

        if apiResonanceGroup is stretch[0]:
          return

        elif apiResonanceGroup is stretch[-1]:
          # chop off end ResonanceGroup
          apiResonanceGroup.directNmrChain = defaultChain
          if len(stretch) == 2:
            stretch[0].directNmrChain = defaultChain
            # delete one-element remaining chain
            apiNmrChain.delete()

        elif apiResonanceGroup is stretch[1]:
          # chop off end ResonanceGroup
          stretch[0].directNmrChain = defaultChain

        else:
          # make new connected NmrChain with rightmost ResonanceGroups
          newNmrChain = apiNmrChain.nmrProject.newNmrChain(isConnected=True)
          for rg in stretch:
            if rg is apiResonanceGroup:
              break
            else:
              rg.directNmrChain = newNmrChain

    finally:
      self._project._appBase._endCommandBlock()

  def disconnect(self):
    """Move NmrResidue from connected NmrChain to default chain,
    creating new connected NmrChains as necessary"""
    apiResonanceGroup = self._wrappedData
    apiNmrChain = apiResonanceGroup.directNmrChain
    defaultChain = apiNmrChain.nmrProject.findFirstNmrChain(code=Constants.defaultNmrChainCode)

    self._startFunctionCommandBlock('disconnect')
    try:
      if apiNmrChain is None:
        # offset residue: no-op
        return

      elif apiResonanceGroup.assignedResidue is not None:
        # Assigned residue with successor residue - error
        raise ValueError("Assigned NmrResidue %s cannot be disconnected" % self)

      elif apiNmrChain.isConnected:
        # Connected stretch - break stretch, keeping first half in the NmrChain
        stretch = apiNmrChain.mainResonanceGroups

        if len(stretch) < 3 or len(stretch) == 3 and apiResonanceGroup is stretch[1]:
          for rg in reversed(stretch):
            # reversed to add residues back in proper order (they ar added to end)
            rg.directNmrChain = defaultChain
          apiNmrChain.delete()

        else:
          index = stretch.index(apiResonanceGroup)
          data2Obj = self._project._data2Obj

          # NB operations are carefully selected to make sure they undo correctly
          if apiResonanceGroup is stretch[-1]:
            apiResonanceGroup.directNmrChain = defaultChain

          elif apiResonanceGroup is stretch[-2]:
            stretch[-1].directNmrChain = defaultChain
            apiResonanceGroup.directNmrChain = defaultChain

          elif index == 0:
            data2Obj[stretch[1]].disconnectPrevious()

          elif index == 1:
            data2Obj[stretch[1]].disconnectPrevious()
            data2Obj[stretch[2]].disconnectPrevious()
          else:
            self.disconnectNext()
            apiResonanceGroup.directNmrChain = defaultChain
    finally:
      self._project._appBase._endCommandBlock()

  @property
  def probableResidues(self) -> Tuple[Tuple[Residue,float], ...]:
    """tuple of (residue, probability) tuples for probable residue assignments
    sorted by decreasing probability. Probabilities are normalised to 1"""
    getDataObj = self._project._data2Obj.get
    ll = sorted((x.weight, x.possibility) for x in self._wrappedData.residueProbs)
    totalWeight = sum(tt[0] for tt in ll) or 1.0  # If sum is zero give raw weights
    return tuple((getDataObj(tt[1]), tt[0]/totalWeight) for tt in reversed(ll))

  @probableResidues.setter
  def probableResidues(self, value):
    apiResonanceGroup = self._wrappedData
    for residueProb in apiResonanceGroup.residueProbs:
      residueProb.delete()
    for residue, weight in value:
      apiResonanceGroup.newResidueProb(possibility=residue._wrappedData, weight=weight)

  @property
  def probableResidueTypes(self) -> Tuple[Tuple[str,float]]:
    """tuple of (residueType, probability) tuples for probable residue types
    sorted by decreasing probability"""
    ll = sorted((x.weight, x.possibility) for x in self._wrappedData.residueTypeProbs)
    totalWeight = sum(tt[0] for tt in ll) or 1.0  # If sum is zero give raw weights
    return tuple((tt[1].code3Letter, tt[0]/totalWeight) for tt in reversed(ll))

  @probableResidueTypes.setter
  def probableResidueTypes(self, value):
    apiResonanceGroup = self._wrappedData
    root = apiResonanceGroup.root
    for residueTypeProb in apiResonanceGroup.residueTypeProbs:
      residueTypeProb.delete()
    for weight, residueType in value:
      chemComp = root.findFirstChemComp(code3Letter=residueType)
      if chemComp is None:
        print("Residue type %s not recognised - skipping" % residueType)
      else:
        apiResonanceGroup.newResidueTypeProb(chemComp=chemComp, weight=weight)

  def deassign(self):
    """Reset sequenceCode and residueType assignment to default values"""
    self._startFunctionCommandBlock('deassign')
    try:
      apiResonanceGroup = self._apiResonanceGroup
      apiResonanceGroup.sequenceCode = None
      apiResonanceGroup.resetResidueType(None)
    finally:
      self._project._appBase._endCommandBlock()

  def rename(self, value:str=None):
    """Rename NmrResidue. changing its sequenceCode, residiueType, or both.

    The value is a dot-separated string `sequenceCode`.`residueType`.
    Values like None, 'abc', or 'abc.' will set the residueType to None.
    Values like None or '.abc' will set the sequenceCode to None,
    resetting it to its canonical form, '@`serial`."""

    # NBNB TODO - consider changing signature to sequenceCode, residueType

    apiResonanceGroup = self._apiResonanceGroup
    sequenceCode = residueType = None
    if value:
      if Pid.altCharacter in value:
        raise ValueError("Character %s not allowed in ccpn.NmrResidue id: %s" %
                         (Pid.altCharacter, value))
      ll = value.split(Pid.IDSEP, 1)
      sequenceCode = ll[0] or None
      if len(ll) > 1:
        residueType = ll[1] or None

    # Check if name is free
    if sequenceCode is not None:
      previous = apiResonanceGroup.nmrChain.findFirstResonanceGroup(sequenceCode=sequenceCode)
      if previous is not self._wrappedData and previous is not None:
        raise ValueError("Cannot rename %s to %s - assignment already exists" % (self, value))
    #
    self._startFunctionCommandBlock('rename', value)
    try:
      apiResonanceGroup.sequenceCode = sequenceCode
      apiResonanceGroup.resetResidueType(residueType)
    finally:
      self._project._appBase._endCommandBlock()

  def moveToNmrChain(self, newNmrChain:Union['NmrChain', str]=None):
    """Reset NmrChain, breaking connected NmrChain if necessary.

    If set to None resets to NmrChain '@-'
    Illegal for offset NmrResidues"""

    values ={}
    if newNmrChain:
      values['newNmrChain'] = newNmrChain

    apiResonanceGroup = self._apiResonanceGroup
    if apiResonanceGroup.relativeOffset is not None:
      raise ValueError("Cannot reset NmrChain for offset NmrResidue %s" % self.id)

    if newNmrChain is None:
      apiNmrChain = None
    elif isinstance(newNmrChain, str):
      apiNmrChain = self._project.getByPid(newNmrChain)._wrappedData
    else:
      apiNmrChain = newNmrChain._wrappedData

    self._startFunctionCommandBlock('moveToNmrChain', values=values)
    try:
      apiResonanceGroup.moveToNmrChain(apiNmrChain)
    finally:
      self._project._appBase._endCommandBlock()

  def assignTo(self, chainCode:str=None, sequenceCode:Union[int,str]=None,
               residueType:str=None, mergeToExisting:bool=False) -> 'NmrResidue':

    """Assign NmrResidue to new assignment, as defined by the naming parameters
    and return the result.

    Empty parameters (e.g. chainCode=None) retain the previous value. E.g.:
    for NmrResidue NR:A.121.ALA
    calling with sequenceCode=123 will reassign to 'A.123.ALA'.

    If no assignment with the same chainCode and sequenceCode exists, the current NmrResidue
    will be reassigned.
    If an NmrResidue with the same chainCode and sequenceCode already exists,  the function
    will either raise ValueError. If  mergeToExisting is set to False, it will instead merge the
    two NmrResidues, delete the current one, and return the new one .
    NB Merging is NOT undoable.
    WARNING: When calling with mergeToExisting=True, always use in the form "x = x.assignTo(...)",
    as the call 'x.assignTo(...) may cause the source x object to become deleted.

    NB resetting the NmrChain for an NmrResidue in the middle of a connected NmrChain
    will cause an error. Use moveToNmrChain(newNmrChainOrPid) instead
    """

    # Get parameter string for console echo - before parameters are changed
    defaults = collections.OrderedDict(
      (('chainCode', None), ('sequenceCode', None),
       ('residueType', None), ('mergeToExisting', False)
      )
    )

    oldPid = self.longPid
    clearUndo = False
    undo = self._apiResonanceGroup.root._undo


    self._startFunctionCommandBlock('assignTo', values=locals(), defaults=defaults,
                                    parName='mergedNmrResidue')
    try:

      sequenceCode = str(sequenceCode) if sequenceCode else None
      apiResonanceGroup = self._apiResonanceGroup

      # Keep old values to go back to previous state

      oldNmrChain =  apiResonanceGroup.nmrChain
      oldSequenceCode = apiResonanceGroup.sequenceCode
      oldResidueType = apiResonanceGroup.residueType

      # set missing parameters to existing values
      chainCode = chainCode or oldNmrChain.code
      sequenceCode = sequenceCode or oldSequenceCode

      for ss in (chainCode, sequenceCode, residueType):
        if ss and Pid.altCharacter in ss:
          raise ValueError("Character %s not allowed in ccpn.NmrResidue id: %s.%s.%s" %
                           (Pid.altCharacter, chainCode, sequenceCode, residueType))
      newNmrChain = self._project.fetchNmrChain(chainCode)
      newApiResonanceGroup = newNmrChain._wrappedData.findFirstResonanceGroup(
        sequenceCode=sequenceCode)

      if newApiResonanceGroup is apiResonanceGroup:
        # We are reassigning to self - either a no-op or resetting the residueType
        result = self
        if residueType and apiResonanceGroup.residueType != residueType:
          apiResonanceGroup.resetResidueType(residueType)

      elif newApiResonanceGroup is None:
        # we are moving to new, free assignment
        result = self

        try:
          # NB Complex resetting sequence necessary
          # # in case we are setting an offset and illegal sequenceCode
          apiResonanceGroup.sequenceCode = None    # To guarantee against clashes
          apiResonanceGroup.directNmrChain = newNmrChain._apiNmrChain # Only directNmrChain is settable
           # Now we can (re)set - will throw error for e.g. illegal offset values
          apiResonanceGroup.sequenceCode = sequenceCode
          if residueType:
            apiResonanceGroup.resetResidueType(residueType)
        except:
          apiResonanceGroup.resetResidueType(oldResidueType)
          apiResonanceGroup.sequenceCode = None
          apiResonanceGroup.directNmrChain = oldNmrChain
          apiResonanceGroup.sequenceCode = oldSequenceCode
          self._project._logger.error("Attempt to set illegal or inconsistent assignment: %s.%s.%s"
            % (chainCode, sequenceCode, residueType) + "\n  Reset to original state"
          )
          raise


      else:
        #We are assigning to an existing NmrResidue
        result = self._project._data2Obj[newApiResonanceGroup]
        if not mergeToExisting:
          raise ValueError("New assignment clash with existing assignment,"
                           " and merging is disallowed")

        # Move or merge the NmrAtoms across and delete the current NmrResidue
        if not residueType or newApiResonanceGroup.residueType == residueType:
          for resonance in self._wrappedData.resonances:
            newResonance = newApiResonanceGroup.findFirstResonance(implName=resonance.name)
            if newResonance is None:
              resonance.resonanceGroup = newApiResonanceGroup
            else:
              # WARNING. This step is NOT undoable, and clears the undo stack
              clearUndo = True
              newResonance.absorbResonance(resonance)

          apiResonanceGroup.delete()

        else:
          # We cannot reassign if it involves changing residueType on an existing NmrResidue
          raise ValueError("Cannot assign to %s.%s.%s: NR:%s.%s.%s already exists"
          % (chainCode, sequenceCode, residueType,
             chainCode, sequenceCode, newApiResonanceGroup.residueType))
      #
      if clearUndo:
        self._project._logger.warning("Merging NmrAtoms from %s into %s. Merging is NOT undoable."
                                      % (oldPid, result.longPid))
        if undo is not None:
          undo.clear()
    finally:
      self._project._appBase._endCommandBlock()
    #
    return result


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: NmrChain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    if parent.isConnected:
      # for conected NmrChains you keep the order
      return parent._wrappedData.resonanceGroups
    else:
      ll = list((x.sequenceCode, x) for x in parent._wrappedData.resonanceGroups)
      return list(tt[-1] for tt in sorted(ll, key=CcpnSorting.universalSortKey))


def getter(self:Residue) -> NmrResidue:
  apiResidue = self._wrappedData
  apiNmrProject = self._project._wrappedData
  apiNmrChain = apiNmrProject.findFirstNmrChain(code=apiResidue.chain.code)
  if apiNmrChain is not None:
    obj = apiNmrChain.findFirstResonanceGroup(seqCode=apiResidue.seqCode,
                                              seqInsertCode=apiResidue.seqInsertCode.strip() or None,
                                              relativeOffset=None)
    if obj is not None:
      return self._project._data2Obj.get(obj)
  return None

def setter(self:Residue, value:NmrResidue):
  oldValue = self.nmrResidue
  if oldValue is value:
    return
  elif oldValue is not None:
    oldValue._apiResonanceGroup.assignedResidue = None

  if value is not None:
    value._apiResonanceGroup.assignedResidue = self._apiResidue
Residue.nmrResidue = property(getter, setter, None, "NmrResidue to which Residue is assigned")


def getter(self:NmrChain) -> Tuple[NmrResidue]:
  result = list(self._project._data2Obj.get(x)for x in self._wrappedData.mainResonanceGroups)
  if not self.isConnected:
    result.sort()
  return tuple(result)
def setter(self:NmrChain, value):
  self._wrappedData.mainResonanceGroups = [x._wrappedData for x in value]
NmrChain.mainNmrResidues = property(getter, setter, None, """NmrResidues belonging to NmrChain that are NOT defined relative to another NmrResidue
  (sequenceCode ending in '-1', '+1', etc.) For connected NmrChains in sequential order, otherwise sorted by assignment""")

del getter
del setter

def _newNmrResidue(self:NmrChain, sequenceCode:Union[int,str]=None, residueType:str=None,
                   comment:str=None) -> NmrResidue:
  """Create new NmrResidue within NmrChain"""

  originalSequenceCode = sequenceCode

  defaults = collections.OrderedDict((('sequenceCode', None), ('residueType', None),
                                     ('comment', None)))

  apiNmrChain = self._wrappedData
  nmrProject = apiNmrChain.nmrProject
  dd = {'name':residueType, 'details':comment,
        'residueType':residueType,'directNmrChain':apiNmrChain}

  self._startFunctionCommandBlock('newNmrResidue', values=locals(), defaults=defaults,
                                  parName='newNmrResidue')
  self._project.blankNotification() # delay notifiers till NmrResidue is fully ready
  try:

    # Convert value to string, and check
    if isinstance(sequenceCode, int):
      sequenceCode = str(sequenceCode)
    elif sequenceCode is not None and not isinstance(sequenceCode, str):
      raise ValueError("Invalid sequenceCode %s must be int, str, or None" % repr(sequenceCode))

    serial = None
    if sequenceCode:

      # Check the sequenceCode is not taken already
      previous = None
      if Pid.IDSEP in sequenceCode:
        # sequenceCode contains '.' - check against remapped sequenceCode
        sq = sequenceCode.translate(Pid.remapSeparators)
        for nr in self.project.nmrResidues:
          if nr.sequenceCode == sq:
            previous = nr
            break
      else:
        # No '.' - can check in API directly (faster)
        obj0 = self._wrappedData.findFirstResonanceGroup(sequenceCode=sequenceCode)
        if obj0 is not None:
          previous = self._project._data2Obj[obj0]
      if previous is not None:
        raise ValueError("Existing %s clashes with id %s.%s.%s" %
                         (previous.longPid, self.shortName, sequenceCode,residueType or ''))

      # Handle reserved names
      if sequenceCode[0] == '@':
        try:
          serial = int(sequenceCode[1:])
        except ValueError:
          # the rest of the name is not an int. We are OK
          pass
        if serial is not None and serial > 0:
          # this is a reserved name
          if nmrProject.findFirstResonanceGroup(serial=serial) is None:
            # The implied serial is free - we can set it
            sequenceCode = None
          else:
            # Name clashes with existing NmrResidue
            raise ValueError("Cannot create NmrResidue with reserved name %s" % sequenceCode)

    else:
      # Just create new ResonanceGroup with default-type name
      sequenceCode = None

    # Create ResonanceGroup
    dd['sequenceCode'] = sequenceCode
    obj = nmrProject.newResonanceGroup(**dd)
    result = self._project._data2Obj.get(obj)
    if serial is not None:
      try:
        modelUtil.resetSerial(obj, serial, 'resonanceGroups')
      except ValueError:
        self.project._logger.warning(
          "Could not set sequenceCode of %s to %s - keeping default value"
          %(result, originalSequenceCode)
        )

    if residueType is not None:
      # get chem comp ID strings from residue type
      tt = self._project._residueName2chemCompId.get(residueType)
      #tt = MoleculeQuery.fetchStdResNameMap(self._wrappedData.root).get(residueType)
      if tt is not None:
        obj.molType, obj.ccpCode = tt
  finally:
    self._project.unblankNotification()
    self._project._appBase._endCommandBlock()

  # Do creation notifications
  if serial is not None:
    result._finaliseAction('rename')
    # If we have reset serial above this is needed
  result._finaliseAction('create')

  return result


def _fetchNmrResidue(self:NmrChain, sequenceCode:Union[int,str]=None,
                     residueType:str=None) -> NmrResidue:
  """Fetch NmrResidue with residueType=residueType, creating it if necessary"""

  defaults = collections.OrderedDict((('sequenceCode', None), ('residueType', None)))

  self._startFunctionCommandBlock('fetchNmrResidue', values=locals(),
                                  parName='newNmrResidue')
  try:
    if sequenceCode is None:
      result = self.newNmrResidue(sequenceCode=None, residueType=residueType)
    else:
      sq = str(sequenceCode)
      apiResonanceGroup = self._wrappedData.findFirstResonanceGroup(sequenceCode=sq)
      if apiResonanceGroup:
        result = self._project._data2Obj.get(apiResonanceGroup)
        if residueType is not None and residueType != apiResonanceGroup.residueType:
          raise ValueError(
            "Existing %s does not match residue type %s" % (result.longPid, repr(residueType))
          )
      else:
        result = self.newNmrResidue(sequenceCode=sequenceCode, residueType=residueType)
  finally:
    self._project._appBase._endCommandBlock()
  #
  return result


# Connections to parents:

NmrChain.newNmrResidue = _newNmrResidue
del _newNmrResidue
NmrChain.fetchNmrResidue = _fetchNmrResidue

def _renameNmrResidue(self:Project, apiResonanceGroup:ApiResonanceGroup):
  """Reset pid for NmrResidue and all offset NmrResidues"""
  nmrResidue =  self._data2Obj.get(apiResonanceGroup)
  nmrResidue._finaliseAction('rename')
  for xx in nmrResidue.offsetNmrResidues:
    xx._finaliseAction('rename')

# Notifiers:
#NBNB TBD We must make Resonance.ResonanceGroup 1..1 when we move beyond transition model
Project._setupApiNotifier(_renameNmrResidue, ApiResonanceGroup, 'setSequenceCode')
Project._setupApiNotifier(_renameNmrResidue, ApiResonanceGroup, 'setDirectNmrChain')
Project._setupApiNotifier(_renameNmrResidue, ApiResonanceGroup, 'setResidueType')
Project._setupApiNotifier(_renameNmrResidue, ApiResonanceGroup, 'setAssignedResidue')
del _renameNmrResidue

# Rename notifiers put in to ensure renaming of NmrAtoms:
className = ApiResonanceGroup._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_finaliseApiRename', {}, className, 'setResonances'),
    ('_finaliseApiRename', {}, className, 'addResonance'),
  )
)

# NB Residue<->NmrResidue link depends solely on the NmrResidue name.
# So no notifiers on the link - notify on the NmrResidue rename instead.
