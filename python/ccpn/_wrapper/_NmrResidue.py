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
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import NmrChain
from ccpn import Residue
from ccpncore.lib import Constants
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
    NB resetting sequenceDoe will rename the NmrResidue"""
    return self._wrappedData.sequenceCode

  @property
  def _key(self) -> str:
    """Residue local ID"""
    return Pid.createId(self.sequenceCode, self.residueType)
    
  @property
  def _parent(self) -> NmrChain:
    """NmrChain containing NmrResidue.
    NB, exceptionally we can reset the NmrChain - this will rename the NmrResidue"""
    return self._project._data2Obj[self._wrappedData.nmrChain]

  @_parent.setter
  def _parent(self, value:NmrChain):
    if value is None:
      raise ValueError("%s NmrResidue.nmrChain cannot be set to None" % self)
    else:
      self._wrappedData.nmrChain = value._wrappedData

  
  nmrChain = _parent

  @property
  def residueType(self) -> str:
    """Residue type string (e.g. 'Ala')
    NB resetting residueType is not possible for assigned NmrReaidues.
    It will rename the NmrResidue"""
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
  def probableResidues(self) -> tuple:
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
    for weight, residue in value:
      apiResonanceGroup.newResidueProb(possibility=residue._wrappedData, weight=weight)

  @property
  def probableResidueTypes(self) -> tuple:
    """tuple of (residueType, probability) tuples for probable residue types"""
    ll = [(x.weight, x.possibility) for x in self._wrappedData.residueTypeProbs]
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
    """Remove sequenceCode and residueType assignment, reset to default NmrChain,
    and remove from connected stretches"""
    apiResonanceGroup = self._apiResonanceGroup
    apiResonanceGroup.sequenceCode = None
    apiResonanceGroup.resetResidueType(None)
    apiResonanceGroup.nmrChain = apiResonanceGroup.nmrProject.findFirstNmrChain(
      code=Constants.defaultNmrChainCode)
    apiResonanceGroup.nextResonanceGroup = None
    apiResonanceGroup.previousResonanceGroup = None

  def rename(self, value:str=None):
    """Rename NmrResidue. 'None' deassigns; partly set names ('.xyz' ir 'xyz.' partly deassign"""
    apiResonanceGroup = self._apiResonanceGroup
    sequenceCode = residueType = None
    if value:
      ll = value.split(Pid.IDSEP, 1)
      sequenceCode = ll[0] or None
      if len(ll) > 1:
        residueType = ll[1] or None
    #
    apiResonanceGroup.sequenceCode = sequenceCode
    apiResonanceGroup.resetResidueType(residueType)

  def reassigned(self, residueId:str=None, chainCode:str=None, sequenceCode:Union[int,str]=None,
               residueType:str=None, objectMergeAllowed=True) -> 'NmrResidue':
    """Get NmrResidue reassigned according to residueId or other parameters.
    Result may be self changed in place or a copy (with self delted), so ALWAYS use the return value.
    Setting residueId deassigns empty fields,
    while empty parameters (e.g. chainCode=None) cause no change.
    If the nmrResidue being reassigned to exists and merging is allowed, the two will be merged.
    NB Merging is NOT undoable
    """

    clearUndo = False
    undo = self._apiResonanceGroup.root._undo

    sequenceCode = str(sequenceCode) if sequenceCode else None

    apiResonanceGroup = self._apiResonanceGroup

    if residueId:
      if any((chainCode, sequenceCode, residueType)):
        raise ValueError("reassigned: assignment parameters only allowed if residueId is None")
      else:
        # Remove colon prefix, if any, and set parameters
        residueId = residueId.split(Pid.PREFIXSEP,1)[-1]
        # NB trick with setting ll first required
        # because the pssed-in Pid may not ahve all three components
        ll = [None, None, None]
        for ii,val in enumerate(Pid.splitId(residueId)):
          ll[ii] = val
        chainCode, sequenceCode, residueType = ll
        if chainCode is None:
          raise ValueError("chainCode part of residueId cannot be empty'")

    else:
      # set missing parameters to existing values
      chainCode = chainCode or apiResonanceGroup.nmrChain.code
      sequenceCode = sequenceCode or apiResonanceGroup.sequenceCode
      residueType = residueType or apiResonanceGroup.residueType

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
      apiResonanceGroup.nmrChain = newNmrChain._apiNmrChain
      apiResonanceGroup.sequenceCode = sequenceCode
      apiResonanceGroup.resetResidueType(residueType)

    else:
      #We are assigning to an existing NmrResidue
      result = self._project._data2Obj[newApiResonanceGroup]
      if not objectMergeAllowed:
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


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: NmrChain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    return parent._wrappedData.sortedResonanceGroups()

def getter(self:NmrResidue) -> tuple:
  apiResult = self._wrappedData.nmrChain.findAllResonanceGroups(seqCode=self.seqCode,
                                                                seqInsertCode=self.seqinsertCode)
  return tuple(sorted(self._project._data2Obj.get(x) for x in apiResult))
NmrResidue.nmrResidueCluster = property(getter, None, None,
                                        "All NmrResidues with the same sequenceCode "
                                        "except for different offSet suffixes '_1', '+1', etc.")

def getter(self:NmrResidue) -> NmrResidue:
  obj = self._wrappedData.nextResidue
  return None if obj is None else self._project._data2Obj.get(obj)
def setter(self:NmrResidue, value:NmrResidue):
  self._wrappedData.nextResidue = None if value is None else value._wrappedData
NmrResidue.nextNmrResidue = property(getter, setter, None, "Next NmrResidue in sequence")

def getter(self:NmrResidue) -> NmrResidue:
  obj = self._wrappedData.previousResidue
  return None if obj is None else self._project._data2Obj.get(obj)
def setter(self:NmrResidue, value:NmrResidue):
  self._wrappedData.previousResidue = None if value is None else value._wrappedData
NmrResidue.previousNmrResidue = property(getter, setter, None, "Previous NmrResidue in sequence")

def getter(self:Residue) -> NmrResidue:
  apiResidue = self._wrappedData
  apiNmrProject = self._project._wrappedData
  apiNmrChain = apiNmrProject.findFirstNmrChain(code=apiResidue.chain.code)
  if apiNmrChain is not None:
    obj = apiNmrProject.findFirstResonanceGroup(chainSerial=apiNmrChain.serial,
                                                seqCode=apiResidue.seqCode,
                                                seqInsertCode=apiResidue.seqInsertCode.strip()
                                                or None)
    return None if obj is None else self._project._data2Obj.get(obj)
  return None

def setter(self:Residue, value:NmrResidue):
  oldValue = self.nmrResidue
  if oldValue is value:
    return
  elif oldValue is not None:
    oldValue.assignedResidue = None

  if value is not None:
    value.assignedResidue = self
Residue.nmrResidue = property(getter, setter, None, "NmrResidue to which Residue is assigned")

del getter
del setter
    
def newNmrResidue(self:NmrChain, residueType:str=None, sequenceCode:Union[int,str]=None, comment:str=None) -> NmrResidue:
  """Create new child NmrResidue"""
  sequenceCode = str(sequenceCode) if sequenceCode else None
  apiNmrChain = self._wrappedData
  nmrProject = apiNmrChain.nmrProject
  obj = nmrProject.newResonanceGroup(sequenceCode=sequenceCode, name=residueType, details=comment,
                                     residueType=residueType, nmrChain=apiNmrChain)
  if residueType is not None:
    # get chem comp ID strings from residue type
    tt = self._project._residueName2chemCompId.get(residueType)
    if tt is not None:
      obj.molType, obj.ccpCode = tt
  #
  return self._project._data2Obj.get(obj)


def fetchNmrResidue(self:NmrChain, sequenceCode:Union[int,str]=None, residueType:str=None) -> NmrResidue:
  """Fetch NmrResidue with residueType=residueType, creating it if necessary"""
  sequenceCode = str(sequenceCode) if sequenceCode else None
  apiResonanceGroup = self._wrappedData.findFirstResonanceGroup(sequenceCode=sequenceCode)
  if apiResonanceGroup:
    if residueType is not None and residueType != apiResonanceGroup.residueType:
      raise ValueError("%s has residue type %s, not %s" % (sequenceCode,
                                                           apiResonanceGroup.residueType,
                                                           residueType))
    else:
      result = self._project._data2Obj.get(apiResonanceGroup)
  else:
    result = self.newNmrResidue(residueType=residueType, sequenceCode=sequenceCode)
  #
  return result

# Connections to parents:
NmrChain._childClasses.append(NmrResidue)

NmrChain.newNmrResidue = newNmrResidue
NmrChain.fetchNmrResidue = fetchNmrResidue

# Notifiers:
#NBNB TBD We must make Resonance.ResonanceGroup 1..1 when we move beyond transition model
className = ApiResonanceGroup._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':NmrResidue}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_resetPid', {}, className, 'setSequenceCode'),
    ('_resetPid', {}, className, 'setAssignedResidue'),
    ('_resetPid', {}, className, 'setNmrChain'),
    ('_resetPid', {}, className, 'setResidueType'),
    ('_resetPid', {}, className, 'setResonances'),
    ('_resetPid', {}, className, 'addResonance')
  )
)
