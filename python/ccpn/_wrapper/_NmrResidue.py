"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

from ccpncore.util import Pid
from ccpncore.util.Types import Tuple, Optional
from ccpncore.util import Common as commonUtil
from ccpncore.lib import Constants
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import NmrChain
from ccpn import Residue
from ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiResonanceGroup

from ccpncore.util.Types import Union


class NmrResidue(AbstractWrapperObject):
  """Nmr Residue, for assignment."""
  
  #: Short class name, for PID.
  shortClassName = 'NR'
  # Attribute it necessary as subclasses must use superclass className
  className = 'NmrResidue'

  #: Name of plural link to instances of class
  _pluralLinkName = 'nmrResidues'
  
  #: List of child classes.
  _childClasses = []

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
    getObj = self._project._data2Obj.get
    return tuple(getObj(x) for x in self._wrappedDatasatelliteResonanceGroups)

  @property
  def mainNmrResidue(self) -> Optional['NmrResidue']:
    """Main NmrResidue (self, or the residue that self is offset relative to"""
    return self._project._data2Obj.get(self._wrappedData.mainNmrResidue)

  @property
  def nextNmrResidue(self) -> Optional['NmrResidue']:
    """Next sequentially connected NmrResidue. Either from a connected NmrChain,
    or the NmrResidue assigned to the next Residue in the same Chain"""
    apiResonanceGroup = self._wrappedData
    apiResidue = apiResonanceGroup.assignedResidue
    apiNmrChain = apiResonanceGroup.directNmrChain

    if apiNmrChain is None:
      # Offset residue result is None
      result = None

    elif apiNmrChain.isConnected:
      # Connected stretch
      stretch = apiNmrChain.mainResonanceGroups
      if apiResonanceGroup is stretch[-1]:
        result = None
      else:
        result = self._project._data2Obj.get(stretch[stretch.index(apiResonanceGroup) + 1])

    elif apiResidue is None:
      result = None

    else:
      # Assigned to residue
      molResidue = apiResidue.molResidue.nextMolResidue
      if molResidue is None:
        result = None
      else:
        result = self._project._data2Obj.get(
          apiResidue.chain.findFirstResidue(seqId=molResidue.seqId))
    #
    return result

  def connectNext(self, value) -> NmrChain:
    """Connect free end of self to free end of next residue in sequence,
    and return resulting connected NmrChain

    Raises error if self is assigned, of if either self or value is offset.

    NB Undoing a connection between two connected stretches
    will get back a 'value' stretch with a new shortName"""

    apiResonanceGroup = self._wrappedData
    # apiResidue = apiResonanceGroup.assignedResidue
    apiNmrChain = apiResonanceGroup.directNmrChain

    if value is None:
      raise ValueError("Cannot connect to value: None")

    apiValueNmrChain = value._wrappedData.nmrChain

    if apiValueNmrChain is None:
      raise ValueError("Cannot connect to offset NmrResidue")

    elif apiNmrChain is None:
      raise ValueError("Cannot connect from offset residue")

    elif self.nextNmrResidue is not None:
      raise ValueError("Cannot connect from NmrResidue in the middle of a connected NmrChain")

    elif apiResonanceGroup.assignedResidue is not None:
      raise ValueError("Cannot connect from assigned residue")

    elif apiValueNmrChain.isConnected and value.previousNmrResidue is not None:
      raise ValueError("Cannot connect to NmrResidue in the middle of a connected NmrChain")

    elif apiValueNmrChain.isConnected and apiValueNmrChain is apiNmrChain:
      raise ValueError("Cannot make cyclical connected NmrChain")

    elif apiNmrChain.isConnected:
      # At this point, self must be the last NmrResidue in a connected chain
      if apiValueNmrChain.isConnected:
        undo = self._project.root._undo
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
      return self.nmrChain

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
      return value.nmrChain

  def disconnectNext(self):
    """Cut connected NmrChain after NmrResidue, creating new connected NmrChain if necessary
    Does nothing if nextNmrResidue is empty;
    Raises ValueError for assigned NmrResidues"""


    apiResonanceGroup = self._wrappedData
    apiNmrChain = apiResonanceGroup.directNmrChain
    defaultChain =  apiNmrChain.nmrProject.findFirstNmrChain(code=Constants.defaultNmrChainCode)

    if apiNmrChain is None:
      # offset residue: no-op
      return

    elif apiNmrChain.isConnected:
      # Connected stretch - break stretch, keeping first half in the NmrChain
      stretch = apiNmrChain.mainResonanceGroups

      if apiResonanceGroup is stretch[-1]:
        return

      elif apiResonanceGroup is stretch[0]:
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

    elif apiResonanceGroup.assignedResidue is not None:
      # Assigned residue with successor residue - error
      raise ValueError("Assigned NmrtResidue cannot be disconnected")

    else:
      # NextResidue is always None. OK.
      return

  @property
  def previousNmrResidue(self) -> Optional['NmrResidue']:
    """Previous sequentially connected NmrResidue. Either from a connected NmrChain,
    or the NmrResidue assigned to the previous Residue in the same Chain"""
    apiResonanceGroup = self._wrappedData
    apiResidue = apiResonanceGroup.assignedResidue
    apiNmrChain = apiResonanceGroup.directNmrChain

    if apiNmrChain is None:
      # Offset residue result is None
      result = None

    elif apiNmrChain.isConnected:
      # Connected stretch
      stretch = apiNmrChain.mainResonanceGroups
      if apiResonanceGroup is stretch[0]:
        result = None
      else:
        result = self._project._data2Obj.get(stretch[stretch.index(apiResonanceGroup) - 1])

    elif apiResidue is None:
      result = None

    else:
      # Assigned to residue
      molResidue = apiResidue.molResidue.previousMolResidue
      if molResidue is None:
        result = None
      else:
        result = self._project._data2Obj.get(
          apiResidue.chain.findFirstResidue(seqId=molResidue.seqId))
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

    if value is None:
      raise ValueError("Cannot connect to value: None")

    apiValueNmrChain = value._wrappedData.nmrChain

    if apiValueNmrChain is None:
      raise ValueError("Cannot connect to offset NmrResidue")

    elif apiNmrChain is None:
      raise ValueError("Cannot connect from offset residue")

    elif self.previousNmrResidue is not None:
      raise ValueError("Cannot connect from NmrResidue in the middle of a connected NmrChain")

    elif apiResonanceGroup.assignedResidue is not None:
      raise ValueError("Cannot connect from assigned residue")

    elif apiValueNmrChain.isConnected and value.nextNmrResidue is not None:
      raise ValueError("Cannot connect to NmrResidue in the middle of a connected NmrChain")

    elif apiValueNmrChain.isConnected and apiValueNmrChain is apiNmrChain:
      raise ValueError("Cannot make cyclical connected NmrChain")

    elif apiNmrChain.isConnected:
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

        return self.nmrChain

    else:
      # self is unassigned, unconnected NmrResidue
      if apiValueNmrChain.isConnected:
        # At this point value must be the last NmrResidue in a connected NmrChain
        apiResonanceGroup.directNmrChain = apiValueNmrChain
      else:
        newApiNmrChain = apiNmrChain.nmrProject.newNmrChain(isConnected=True)
        value._wrappedData.directNmrChain = newApiNmrChain
        apiResonanceGroup.directNmrChain = newApiNmrChain
      return value.nmrChain

  def disconnectPrevious(self):
    """Cut connected NmrChain before NmrResidue, creating new connected NmrChain if necessary
    Does nothing if previousNmrResidue is empty;
    Deletes one-NmrResidue NmrChains  if generated
    Raises ValueError for assigned NmrResidues"""

    apiResonanceGroup = self._wrappedData
    apiNmrChain = apiResonanceGroup.directNmrChain
    defaultChain =  apiNmrChain.nmrProject.findFirstNmrChain(code=Constants.defaultNmrChainCode)

    if apiNmrChain is None:
      # offset residue: no-op
      return

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

    elif apiResonanceGroup.assignedResidue is not None:
      # Assigned residue with successor residue - error
      raise ValueError("Assigned NmrtResidue cannot be disconnected")

    else:
      # NextResidue is always None. OK.
      return

  def disconnect(self):
    """Move NmrResidue from connected NmrChain to default chain,
    creating new connected NmrChains as necessary"""
    apiResonanceGroup = self._wrappedData
    apiNmrChain = apiResonanceGroup.directNmrChain
    defaultChain =  apiNmrChain.nmrProject.findFirstNmrChain(code=Constants.defaultNmrChainCode)#

    if apiNmrChain is None:
      # offset residue: no-op
      return

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

    elif apiResonanceGroup.assignedResidue is not None:
      # Assigned residue with successor residue - error
      raise ValueError("Assigned NmrtResidue cannot be disconnected")

    else:
      # NextResidue is always None. OK.
      return

  @property
  def probableResidues(self) -> Tuple[Tuple[Residue,float], ...]:
    """tuple of (residue, probability) tuples for probable residue assignments"""
    getObj = self._project._data2Obj.get
    ll = [(x.weight, x.possibility) for x in self._wrappedData.residueProbs]
    totalWeight = sum(tt[0] for tt in ll)
    return tuple((getObj(tt[1]), tt[0]/totalWeight) for tt in ll)

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
    sorted b descending probability"""
    ll = reversed(sorted((x.weight, x.possibility)
                         for x in self._wrappedData.residueTypeProbs))
    totalWeight = sum(tt[0] for tt in ll)
    return tuple((tt[1].code3Letter, tt[0]/totalWeight) for tt in ll)

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
    apiResonanceGroup = self._apiResonanceGroup
    apiResonanceGroup.sequenceCode = None
    apiResonanceGroup.resetResidueType(None)

  def rename(self, value:str=None):
    """Rename NmrResidue. 'None' deassigns; partly set names ('.xyz' or 'xyz.' partly deassign"""
    apiResonanceGroup = self._apiResonanceGroup
    sequenceCode = residueType = None
    if value:
      ll = value.split(Pid.IDSEP, 1)
      sequenceCode = ll[0] or None
      if len(ll) > 1:
        residueType = ll[1] or None

    for ss in (sequenceCode, residueType):
      if ss and Pid.altCharacter in ss:
        raise ValueError("Character %s not allowed in ccpn.NmrResidue id: %s.%s" %
                         (Pid.altCharacter, sequenceCode, residueType))

    # Check if name is free
    if sequenceCode is not None:
      previous = apiResonanceGroup.nmrChain.findFirstResonanceGroup(sequenceCode=sequenceCode)
      if previous is not self._wrappedData and previous is not None:
        raise ValueError("Cannot rename %s to %s - assignment already exists" % (self, value))
    #
    apiResonanceGroup.sequenceCode = sequenceCode
    apiResonanceGroup.resetResidueType(residueType)

  def resetNmrChain(self, newNmrChain:Union[NmrChain, str]=None):
    """Reset NmrChain, breaking connected NmrChain if necessary.

    If set to None resets to NmrChain '@-'
    Illegal for offset NmrResidues"""

    apiResonanceGroup = self._apiResonanceGroup
    if apiResonanceGroup.relativeOffset is not None:
      raise ValueError("Cannot reset NmrChain for offset NmrResidue %s" % self.id)

    if newNmrChain is None:
      apiNmrChain = None
    elif isinstance(newNmrChain, str):
      apiNmrChain = self._project.getByPid(newNmrChain)._wrappedData
    else:
      apiNmrChain = newNmrChain._wrappedData

    apiResonanceGroup.resetNmrChain(apiNmrChain)

  def assignTo(self, residueId:str=None, chainCode:str=None, sequenceCode:Union[int,str]=None,
               residueType:str=None, mergeToExisting=True) -> 'NmrResidue':

    """Assign NmrResidue to residueId (or other parameters) and get back the result
    (either a modified self or another NmrResidue with the correct assignment, if one exists).

    NB resetting teh NmrChain for an NmrResieue in the middle of a conneted NmrChain
    will cause an error. Use resetNmrChain(newNmrChainOrPid) instead

    WARNING: If mergeToExisting, always use in the form "x = x.assignTo(...)",
    as the call 'x.assignTo(...) may cause the source x object to become deleted.

    Passing in a residueId deassigns empty residueType or name fields,
    while empty parameters (e.g. chainCode=None) cause no change.
    If the target ccpn.NmrResidue being reassigned to exists and mergeToExisting is True,
    the source will be deleted, and its data merged into the target.
    NB Merging is NOT undoa
    """

    clearUndo = False
    undo = self._apiResonanceGroup.root._undo
    sequenceCode = str(sequenceCode) if sequenceCode else None
    apiResonanceGroup = self._apiResonanceGroup

    # Keep old values to go back to previous statee
    oldNmrChain =  apiResonanceGroup.nmrChain
    oldSequenceCode = apiResonanceGroup.sequenceCode
    oldResidueType = apiResonanceGroup.residueType

    if residueId:
      if any((chainCode, sequenceCode, residueType)):
        raise ValueError("assignTo: assignment parameters only allowed if residueId is None")
      else:
        # Remove colon prefix, if any, and set parameters
        residueId = residueId.split(Pid.PREFIXSEP,1)[-1]
        # NB trick with setting ll first required
        # because the passed-in Pid may not have all three components
        ll = [None, None, None]
        for ii,val in enumerate(Pid.splitId(residueId)):
          ll[ii] = val
        chainCode, sequenceCode, residueType = ll
        if chainCode is None:
          raise ValueError("chainCode part of residueId cannot be empty'")

    else:
      # set missing parameters to existing values
      chainCode = chainCode or oldNmrChain.code
      sequenceCode = sequenceCode or oldSequenceCode
      residueType = residueType or oldResidueType

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
      if newApiResonanceGroup.residueType == residueType:
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
    if undo is not None and clearUndo:
      undo.clear()
    #
    return result


  # Implementation functions numericStringSortKey
  @classmethod
  def _getAllWrappedData(cls, parent: NmrChain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    if parent.isConnected:
      # for conected NmrChains you keep the order
      return parent._wrappedData.resonanceGroups
    else:
      ll = [(commonUtil.numericStringSortKey(x.sequenceCode), x)
            for x in parent._wrappedData.resonanceGroups]
      return [tt[-1] for tt in sorted(ll)]

# def getter(self:NmrResidue) -> NmrResidue:
#   obj = self._wrappedData.nextResidue
#   return None if obj is None else self._project._data2Obj.get(obj)
# def setter(self:NmrResidue, value:NmrResidue):
#   self._wrappedData.nextResidue = None if value is None else value._wrappedData
# NmrResidue.nextNmrResidue = property(getter, setter, None, "Next NmrResidue in sequence")
#
# def getter(self:NmrResidue) -> NmrResidue:
#   obj = self._wrappedData.previousResidue
#   return None if obj is None else self._project._data2Obj.get(obj)
# def setter(self:NmrResidue, value:NmrResidue):
#   self._wrappedData.previousResidue = None if value is None else value._wrappedData
# NmrResidue.previousNmrResidue = property(getter, setter, None, "Previous NmrResidue in sequence")

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


  # @property
  # def connectedNmrResidues(self) -> tuple:
  #   """stretch of connected NmrResidues within NmrChain - there can only be one
  #   Does not include NmrResidues defined as satellites (sequenceCodes that end in '+1', '-1', etc.
  #   If NmrChain matches a proper Chain, there will be an NmrResidue for each residue,
  #   with None for unassigned residues. NBNB TBD draft - needs checking"""
  #
  #   apiNmrChain = self._wrappedData
  #   apiChain = apiNmrChain.chain
  #   if apiChain is None:
  #     apiStretch = apiNmrChain.connectedStretch
  #     if apiStretch is None:
  #       apiResGroups = ()
  #     else:
  #       apiResGroups = apiStretch.activeResonanceGroups
  #   else:
  #     func1 = apiNmrChain.nmrProject.findFirstResonanceGroup
  #     apiResGroups = [func1(seqCode=x.seqCode, seqInsertCode=x.seqInsertCode, relativeOffset=None)
  #                     for x in apiChain.sortedResidues()]
  #   #
  #   func2 =  self._parent._data2Obj.get
  #   return tuple(None if x is None else func2(x) for x in apiResGroups)
  #
  # @connectedNmrResidues.setter
  # def connectedNmrResidues(self, value:Sequence):
  #   # NBNB TBD Check validity of code.
  #   apiNmrChain = self._wrappedData
  #   apiChain = apiNmrChain.chain
  #   if apiChain is None:
  #     apiStretch = apiNmrChain.connectedStretch
  #     if apiStretch is None:
  #       if value:
  #         apiStretch = apiNmrChain.nmrProject.newConnectedStretch(
  #           activeResonanceGroups= [x._wrappedData for x in value],
  #           sequentialAssignment=apiNmrChain.nmrProject.activeSequentialAssignment
  #         )
  #     else:
  #       if value:
  #         apiStretch.activeResonanceGroups = [x._wrappedData for x in value]
  #       else:
  #         apiStretch.delete()
  #   else:
  #     raise ValueError("Cannot set connectedNmrResidues for NmrChain assigned to actual Chain")

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

def _newNmrResidue(self:NmrChain, residueType:str=None, sequenceCode:Union[int,str]=None,
                   comment:str=None) -> NmrResidue:
  """Create new ccpn.NmrResidue within ccpn.NmrChain"""
  sequenceCode = str(sequenceCode) if sequenceCode else None

  for ss in (sequenceCode, residueType):
    if ss and Pid.altCharacter in ss:
      raise ValueError("Character %s not allowed in ccpn.NmrResidue id: %s.%s" %
                       (Pid.altCharacter, sequenceCode, residueType))

  apiNmrChain = self._wrappedData
  nmrProject = apiNmrChain.nmrProject
  obj = nmrProject.newResonanceGroup(sequenceCode=sequenceCode, name=residueType, details=comment,
                                     residueType=residueType, directNmrChain=apiNmrChain)

  if residueType is not None:
    # get chem comp ID strings from residue type
    tt = self._project._residueName2chemCompId.get(residueType)
    if tt is not None:
      obj.molType, obj.ccpCode = tt
  #
  return self._project._data2Obj.get(obj)


def fetchNmrResidue(self:NmrChain, sequenceCode:Union[int,str]=None, residueType:str=None) -> NmrResidue:
  """Fetch NmrResidue with residueType=residueType, creating it if necessary"""
  if sequenceCode is not None:
    sequenceCode = str(sequenceCode) or None
  apiResonanceGroup = self._wrappedData.findFirstResonanceGroup(sequenceCode=sequenceCode)
  if apiResonanceGroup:
    if residueType is not None and residueType != apiResonanceGroup.residueType:
      raise ValueError("%s has residue type %s, not %s" % (sequenceCode,
                                                           apiResonanceGroup.residueType,
                                                           residueType))
    else:
      result = self._project._data2Obj.get(apiResonanceGroup)
  else:
    for ss in (sequenceCode, residueType):
      if ss and Pid.altCharacter in ss:
        raise ValueError("Character %s not allowed in ccpn.NmrResidue id: %s.%s" %
                         (Pid.altCharacter, sequenceCode, residueType))

    result = self.newNmrResidue(residueType=residueType, sequenceCode=sequenceCode)
  #
  return result


# Connections to parents:
NmrChain._childClasses.append(NmrResidue)

NmrChain.newNmrResidue = _newNmrResidue
del _newNmrResidue
NmrChain.fetchNmrResidue = fetchNmrResidue

def _resetNmrResiduePid(self:Project, apiResonanceGroup:ApiResonanceGroup):
  """Reset pid for NmrResidue and all offset NmrResidues"""
  self._resetPid(apiResonanceGroup)
  for xx in apiResonanceGroup.offsetResonanceGroups:
    self._resetPid(xx)

# Notifiers:
#NBNB TBD We must make Resonance.ResonanceGroup 1..1 when we move beyond transition model
Project._setupNotifier(_resetNmrResiduePid, ApiResonanceGroup, 'setSequenceCode')
Project._setupNotifier(_resetNmrResiduePid, ApiResonanceGroup, 'setDirectNmrChain')
Project._setupNotifier(_resetNmrResiduePid, ApiResonanceGroup, 'setResidueType')
Project._setupNotifier(_resetNmrResiduePid, ApiResonanceGroup, 'setAssignedResidue')

className = ApiResonanceGroup._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':NmrResidue}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    # ('_resetPid', {}, className, 'setSequenceCode'),
    # ('_resetPid', {}, className, 'setAssignedResidue'),
    # ('_resetPid', {}, className, 'setDirectNmrChain'),
    # ('_resetPid', {}, className, 'setResidueType'),
    ('_resetPid', {}, className, 'setResonances'),
    ('_resetPid', {}, className, 'addResonance'),
    ('_finaliseUnDelete', {}, className, 'undelete'),
  )
)
