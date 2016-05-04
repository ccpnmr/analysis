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

import operator
from ccpn.lib.Util import AtomIdTuple
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import NmrResidue
from ccpn import Atom
from ccpn import Peak
from ccpncore.lib import Constants
from ccpncore.api.ccp.nmr import Nmr
from ccpncore.lib.spectrum.Spectrum import name2IsotopeCode
from ccpncore.util import Pid
from typing import Union, Tuple, List


class NmrAtom(AbstractWrapperObject):
  """Nmr Atom, used for assigning,peaks and shifts. (corresponds to ApiResonance)."""

  
  #: Short class name, for PID.
  shortClassName = 'NA'
  # Attribute it necessary as subclasses must use superclass className
  className = 'NmrAtom'

  #: Name of plural link to instances of class
  _pluralLinkName = 'nmrAtoms'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = Nmr.Resonance._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiResonance(self) -> Nmr.Resonance:
    """ CCPN atom matching Atom"""
    return self._wrappedData


  @property
  def _parent(self) -> NmrResidue:
    """Parent (containing) object."""
    return self._project._data2Obj[self._wrappedData.resonanceGroup]
  
  nmrResidue = _parent
    
  @property
  def _key(self) -> str:
    """Atom name string (e.g. 'HA') regularised as used for ID"""
    return self._wrappedData.name.translate(Pid.remapSeparators)

  @property
  def _idTuple(self) -> AtomIdTuple:
    """ID as chainCode, sequenceCode, residueType, atomName namedtuple
    NB Unlike the _id and key, these do NOT have reserved characters maped to '^'"""
    parent = self._parent
    return AtomIdTuple(parent._parent.shortName, parent.sequenceCode, parent.residueType, self.name)

  @property
  def name(self) -> str:
    """Atom name string (e.g. 'HA')"""
    return self._wrappedData.name

  @property
  def serial(self) -> int:
    """NmrAtom serial number - set at creation and unchangeable"""
    return self._wrappedData.serial

  @property
  def atom(self) -> Atom:
    """Atom to which NmrAtom is assigned. NB resetting the atom will rename the NmrAtom"""
    atom = self._wrappedData.atom
    return None if atom is None else self._project._data2Obj.get(atom)

  @atom.setter
  def atom(self, value:Atom):
    if value is None:
      self.deassign()
    else:
      self._wrappedData.atom = value._wrappedData

  @property
  def isotopeCode(self) -> str:
    """isotopeCode of NmrAtom. Set automatically on creation (from NmrAtom name) and cannot be reset"""
    return self._wrappedData.isotopeCode

  @property
  def assignedPeaks(self) -> Tuple[Peak]:
    """All ccpn.Peaks assigned to the ccpn.NmrAtom"""
    apiResonance = self._wrappedData
    apiPeaks = [x.peakDim.peak for x in apiResonance.peakDimContribs]
    apiPeaks.extend([x.peakDim.peak for x in apiResonance.peakDimContribNs])

    data2Obj = self._project._data2Obj
    return sorted(data2Obj[x] for x in set(apiPeaks))

  def rename(self, value:str=None):
    """Rename object, changing id, Pid, and internal representation"""
    # NB This is a VERY special case
    # - API code and notifiers will take care of resetting id and Pid
    if value is None:
      self.deassign()

    else:
      if Pid.altCharacter in value:
        raise ValueError("Character %s not allowed in ccpn.NmrAtom.name" % Pid.altCharacter)

      isotopeCode = self._wrappedData.isotopeCode
      newIsotopeCode = name2IsotopeCode(value)
      if newIsotopeCode is not None:
        if isotopeCode == '?':
          self._wrappedData.isotopeCode = newIsotopeCode
        elif newIsotopeCode != isotopeCode:
          raise ValueError("Cannot rename %s type NmrAtom to %s" % (isotopeCode, value))
      #
      self._wrappedData.name = value

  def deassign(self):
    """Reset NmrAtom back to its originalName, cutting all assignment links"""
    self._wrappedData.name = None

  def assignTo(self, atomId:str=None, chainCode:str=None, sequenceCode:Union[int,str]=None,
               residueType:str=None, name:str=None, mergeToExisting=True) -> 'NmrAtom':
    """Assign NmrAtom to atomId (or other parameters) and get back the result
    (either a modified self or another NmrAtom with the correct assignment, if one exists).

    WARNING: is mergeToExisting is True, always use in the form "x = x.assignTo(...)",
    as the call 'x.assignTo(...) may cause the source x object to be deleted.

    Passing in an atomId with empty values gives you a new, empty NmrChain or NmrResidue,
    and deassigns the NmrAtom, depending on which value(s) is empty.
    Passing in empty parameters (e.g. chainCode=None) gets you the current value.
    If the target nmrAtom being reassigned to exists and mergeToExisting is True,
    the source will be deleted, and its data merged into the target.
    NB Merging is NOT undoable
    """
    clearUndo = False
    undo = self._apiResonance.root._undo
    apiResonance = self._apiResonance
    apiResonanceGroup = apiResonance.resonanceGroup
    if sequenceCode is not None:
      sequenceCode = str(sequenceCode) or None

    if atomId:
      if any((chainCode, sequenceCode, residueType, name)):
        raise ValueError("assignTo: assignment parameters only allowed if atomId is None")
      else:
        # Remove colon prefix, if any, and set parameters
        atomId = atomId.split(Pid.PREFIXSEP,1)[-1]
        # NB trick with setting ll first required
        # because the passed-in Pid may not have all four components
        ll = [None, None, None, None]
        for ii,val in enumerate(Pid.splitId(atomId)):
          ll[ii] = val
        chainCode, sequenceCode, residueType, name = ll
        if chainCode is None:
          raise ValueError("chainCode part of atomId cannot be empty'")
        # if sequenceCode is None:
        #   raise ValueError("sequenceCode part of atomId cannot be empty'")

    else:
      # set missing parameters to existing values
      chainCode = chainCode or apiResonanceGroup.nmrChain.code
      sequenceCode = sequenceCode or apiResonanceGroup.sequenceCode
      residueType = residueType or apiResonanceGroup.residueType
      name = name or apiResonance.name

    for ss in chainCode, sequenceCode, residueType, name:
      if ss and Pid.altCharacter in ss:
        raise ValueError("Character %s not allowed in ccpn.NmrAtom id : %s.%s.%s.%s"
                         % (Pid.altCharacter, chainCode, sequenceCode, residueType, name))

    oldNmrResidue = self.nmrResidue
    nmrChain = self._project.fetchNmrChain(chainCode)
    if residueType:
      nmrResidue = nmrChain.fetchNmrResidue(sequenceCode, residueType)
    else:
      nmrResidue = nmrChain.fetchNmrResidue(sequenceCode)

    if name:
      # result is matching NmrAtom, or (if None) self
      result = nmrResidue.getNmrAtom(name) or self
    else:
      # No NmrAtom can match, result is self
      result = self

    if nmrResidue is oldNmrResidue:
      if name != self.name:
        # NB self.name can never be returned as None

        if result is self:
          self._wrappedData.name = name or None

        elif mergeToExisting:
          clearUndo = True
          result._wrappedData.absorbResonance(self._apiResonance)

        else:
          raise ValueError("New assignment clash with existing assignment,"
                           " and merging is disallowed")

    else:

      if result is self:
        if nmrResidue.getNmrAtom(self.name) is None:
          self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
          if name != self.name:
            self._wrappedData.name = name or None
        elif name is None or oldNmrResidue.getNmrAtom(name) is None:
          if name != self.name:
            self._wrappedData.name = name or None
          self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
        else:
          self._wrappedData.name = None  # Necessary to avoid name clashes
          self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
          self._wrappedData.name = name

      elif mergeToExisting:
        # WARNING if we get here undo is no longer possible
        clearUndo = True
        result._wrappedData.absorbResonance(self._apiResonance)

      else:
        raise ValueError("New assignment clash with existing assignment,"
                         " and merging is disallowed")
    #
    if undo is not None and clearUndo:
      undo.clear()
    #
    return result

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: NmrResidue)-> list:
    """get wrappedData (ApiResonance) for all NmrAtom children of parent NmrResidue"""
    return sorted(parent._wrappedData.resonances, key=operator.attrgetter('name'))

def getter(self:Atom) -> NmrAtom:
  nmrResidue = self.residue.nmrResidue
  if nmrResidue is None:
    return None
  else:
    obj = nmrResidue._wrappedData.findFirstResonance(name=self._wrappedData.name)
    return None if obj is None else self._project._data2Obj.get(obj)

def setter(self:Atom, value:NmrAtom):
  oldValue = self.nmrAtom
  if oldValue is value:
    return
  elif value is None:
    raise ValueError("Cannot set Atom.nmrAtom to None")
  elif oldValue is not None:
    raise ValueError("New assignment of Atom clashes with existing assignment")
  else:
    value.atom = self
Atom.nmrAtom = property(getter, setter, None, "NmrAtom to which Atom is assigned")

del getter
del setter
    
def _newNmrAtom(self:NmrResidue, name:str=None, isotopeCode:str=None) -> NmrAtom:
  """Create new ccpn.NmrAtom within ccpn.NmrResidue. If name is None, use nucleus@serial"""
  nmrProject = self._project._wrappedData
  resonanceGroup = self._wrappedData

  if name:
    if Pid.altCharacter in name:
      raise ValueError("Character %s not allowed in ccpn.NmrAtom.name" % Pid.altCharacter)

  if not isotopeCode:
    if name:
      isotopeCode = name2IsotopeCode(name) or '?'
    else:
      raise ValueError("newNmrAtom requires either name or isotopeCode as input")


  return self._project._data2Obj.get(nmrProject.newResonance(resonanceGroup=resonanceGroup,
                                                             name=name,
                                                             isotopeCode=isotopeCode))

def fetchNmrAtom(self:NmrResidue, name:str):
  """Fetch NmrAtom with name=name, creating it if necessary"""
  resonanceGroup = self._wrappedData
  return (self._project._data2Obj.get(resonanceGroup.findFirstResonance(name=name)) or
          self.newNmrAtom(name=name))

def produceNmrAtom(self:Project, atomId:str=None, chainCode:str=None,
                   sequenceCode:Union[int,str]=None,
                   residueType:str=None, name:str=None) -> NmrAtom:
  """get chainCode, sequenceCode, residueType and atomName from dot-separated  atomId or Pid
  or explicit parameters, and find or create an NmrAtom that matches
  Empty chainCode gets NmrChain:@- ; empty sequenceCode get a new NmrResidue"""

  # Get ID parts to use
  if sequenceCode is not None:
    sequenceCode = str(sequenceCode) or None
  params = [chainCode, sequenceCode, residueType, name]
  if atomId:
    if any(params):
      raise ValueError("produceNmrAtom: other parameters only allowed if atomId is None")
    else:
      # Remove colon prefix, if any
      atomId = atomId.split(Pid.PREFIXSEP,1)[-1]
      for ii,val in enumerate(Pid.splitId(atomId)):
        if val:
          params[ii] = val
      chainCode, sequenceCode, residueType, name = params

  if name is None:
    raise ValueError("NmrAtom name must be set")

  elif Pid.altCharacter in name:
    raise ValueError("Character %s not allowed in ccpn.NmrAtom.name" % Pid.altCharacter)

  # Produce chain
  nmrChain = self.fetchNmrChain(shortName=chainCode or Constants.defaultNmrChainCode)
  nmrResidue = nmrChain.fetchNmrResidue(sequenceCode=sequenceCode, residueType=residueType)
  return nmrResidue.fetchNmrAtom(name)

    
# Connections to parents:

NmrResidue._childClasses.append(NmrAtom)

NmrResidue.newNmrAtom = _newNmrAtom
del _newNmrAtom
NmrResidue.fetchNmrAtom = fetchNmrAtom

Project.produceNmrAtom = produceNmrAtom

# Notifiers:
className = Nmr.Resonance._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_finaliseApiRename', {}, className, 'setImplName'),
    ('_finaliseApiRename', {}, className, 'setResonanceGroup'),
  )
)
for clazz in Nmr.AbstractPeakDimContrib._metaclass.getNonAbstractSubtypes():
  className = clazz.qualifiedName()
  Project._apiNotifiers.extend(
    ( ('_modifiedLink', {'classNames':('NmrAtom','Peak')}, className, 'create'),
      ('_modifiedLink', {'classNames':('NmrAtom','Peak')}, className, 'delete'),
    )
  )

# NB Atom<->NmrAtom link depends solely on the NmrAtom name.
# So no notifiers on the link - notify on the NmrAtom rename instead.