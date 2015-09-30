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
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import NmrResidue
from ccpn import Atom
from ccpncore.api.ccp.nmr.Nmr import Resonance as ApiResonance
from ccpncore.lib.spectrum.Spectrum import name2IsotopeCode
from ccpncore.util import Pid


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
  

  # CCPN properties  
  @property
  def _apiResonance(self) -> ApiResonance:
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
  def name(self) -> str:
    """Atom name string (e.g. 'HA')"""
    return self._wrappedData.name

  @name.setter
  def name(self, value:str):
    self._wrappedData.name = value

  @property
  def atom(self) -> Atom:
    """Atom to which NmrAtom is assigned. NB resetting the atom will rename the NmrAtom"""
    atom = self._wrappedData.atom
    return None if atom is None else self._project._data2Obj.get(atom)

  @atom.setter
  def atom(self, value:Atom):
    self._wrappedData.atom = None if value is None else value._wrappedData

  @property
  def isotopeCode(self) -> str:
    """isotopeCode of NmrAtom. Set automatically on creation (from NmrAtom name) and cannot be reset"""
    return self._wrappedData.isotopeCode

  # Implementation functions
  def rename(self, value:str):
    """Rename object, changing id, Pid, and internal representation"""
    # NB This is a VERY special case
    # - API code and notifiers will take care of resetting id and Pid
    if value:
      isotopeCode = self._wrappedData.isotopeCode
      newIsotopeCode = name2IsotopeCode(value)
      if isotopeCode == 'unknown':
        self._wrappedData.isotopeCode = newIsotopeCode
      elif newIsotopeCode != isotopeCode:
        raise ValueError("Cannot rename %s type NmrAtom to %s" % (isotopeCode, value))

    self.name = value

  def reassign(self, atomId:str=None, chainCode:str=None, sequenceCode:str=None,
               residueType:str=None, name:str=None, mergeToExisting=True) -> 'NmrAtom':
    """Reassign NmrAtom to NmrAtom given by atomId or other parameters.
    The current id is kept for parts that are not overwritten.
    If the NmrAtom being reassigned to exists, and merging is allowed, the two will be merged.
    NB Merging is NOT undoable
    """
    clearUndo = False
    undo = self._apiResonance.root._undo

    # Get ID parts to reassign to
    idParts = self.id.split(Pid.IDSEP)
    params = [chainCode, sequenceCode, residueType, name]
    if atomId:
      if any(params):
        raise ValueError("produceNmrAtom: other parameters only allowed if atomId is None")
      else:
        for ii,val in enumerate(atomId.split(Pid.IDSEP)):
          if val:
            idParts[ii] = val
    else:
      for ii,val in enumerate(params):
        if val:
          idParts[ii] = val

    oldNmrResidue = self.nmrResidue
    nmrChain = self._project.fetchNmrChain(chainCode)
    nmrResidue = nmrChain.fetchNmrResidue(sequenceCode, residueType)
    result = self

    if nmrResidue is oldNmrResidue:
      if name != self.name:
        if name:
          newNmrAtom = nmrResidue.getNmrAtom(name)
          if newNmrAtom is None:
            self.rename(name)
          else:
            if mergeToExisting:
              newNmrAtom._wrappedData.absorbResonance(self._apiResonance)
              result = newNmrAtom()
            else:
              raise ValueError("New assignment clash with existing assignment,"
                               " and merging is disallowed")
        else:
          self.name = None

    else:
      if name:
        newNmrAtom = nmrResidue.getNmrAtom(name)
        if newNmrAtom is None:
          self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup

        else:
          # WARNING if we get here undo is no longer possible
          if mergeToExisting:
            newNmrAtom._wrappedData.absorbResonance(self._apiResonance)
            result = newNmrAtom()
          else:
            raise ValueError("New assignment clash with existing assignment,"
                             " and merging is disallowed")
      else:
        self._apiResonance.resonanceGroup = nmrResidue._apiResonanceGroup
    #
    if clearUndo:
      undo.clear()
    #
    return result


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
  elif oldValue is not None:
    oldValue.atom = None

  if value is not None:
    value.atom = self
Atom.nmrAtom = property(getter, setter, None, "NmrAtom to which Atom is assigned")

del getter
del setter
    
def newNmrAtom(self:NmrResidue, name:str=None, isotopeCode:str=None) -> NmrAtom:
  """Create new child NmrAtom. If name is None, use nucleus@serial"""
  nmrProject = self._project._wrappedData
  resonanceGroup = self._wrappedData

  if not isotopeCode:
    if name:
      isotopeCode = name2IsotopeCode(name) or 'unknown'
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

def produceNmrAtom(self:Project, atomId:str=None, chainCode:str=None, sequenceCode:str=None,
                   residueType:str=None, name:str=None) -> NmrAtom:
  """get chainCode, sequenceCode, residueType and atomName frm dot-separated  atomId
  or explicit parameters, and find or create an NmrAtom that matches """

  # Get ID parts to use
  idParts = [chainCode, sequenceCode, residueType, name]
  if atomId:
    if any(idParts):
      raise ValueError("produceNmrAtom: other parameters only allowed if atomId is None")
    else:
      # NB, at this point id
      for ii,val in atomId.split(Pid.IDSEP):
        if val:
          idParts[ii] = val

  # Produce chain
  nmrChain = self.fetchNmrChain(shortName=chainCode)
  nmrResidue = nmrChain.fetchNmrResidue(sequenceCode=sequenceCode, residueType=residueType)
  return nmrResidue.fetchNmrAtom(name)

    
# Connections to parents:

NmrResidue._childClasses.append(NmrAtom)

NmrResidue.newNmrAtom = newNmrAtom
NmrResidue.fetchNmrAtom = fetchNmrAtom

# Notifiers:
className = ApiResonance._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':NmrAtom}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_resetPid', {}, className, 'setName'),
    ('_resetPid', {}, className, 'setResonanceGroup')
  )
)
