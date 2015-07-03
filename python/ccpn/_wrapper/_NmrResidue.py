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
from ccpncore.api.ccp.nmr.Nmr import ResonanceGroup as ApiResonanceGroup


class NmrResidue(AbstractWrapperObject):
  """Nmr Residue, for assignment."""
  
  #: Short class name, for PID.
  shortClassName = 'NR'

  #: Name of plural link to instances of class
  _pluralLinkName = 'nmrResidues'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def apiResonanceGroup(self) -> ApiResonanceGroup:
    """ CCPN resonanceGroup matching Residue"""
    return self._wrappedData
  
  
  @property
  def sequenceCode(self) -> str:
    """Residue sequence code and id (e.g. '1', '127B', '@157+1) """
    return self._wrappedData.sequenceCode

  # NBNB TBD we need rename function to set this

  @property
  def _key(self) -> str:
    """Residue local ID"""
    return Pid.makeId(self.sequenceCode, self.name)
    
  @property
  def _parent(self) -> NmrChain:
    """NmrChain containing NmrResidue."""
    return self._project._data2Obj[self._wrappedData.nmrChain]
  
  nmrChain = _parent

  @property
  def name(self) -> str:
    """Residue type name string (e.g. 'Ala')"""
    return self._wrappedData.residueType or ''

  @name.setter
  def name(self, value:str):
    apiResonanceGroup = self._wrappedData
    apiResonanceGroup.residueType = value

    # get chem comp ID strings from residue name
    tt = self._project._residueName2chemCompId.get(value)
    if tt is not None:
      apiResonanceGroup.molType, apiResonanceGroup.ccpCode = tt
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

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
                                        "except for different offSets suffixes '_1', '+1', etc.")

def getter(self:NmrResidue) -> NmrResidue:
  obj = self._wrappedData.nextResidue
  return None if obj is None else self._project._data2Obj.get(obj)
def setter(self:NmrResidue, value:NmrResidue):
  self._wrappedData.nextResidue = None if value is None else value._wrappedData
NmrResidue.nextResidue = property(getter, setter, None, "Next NmrResidue in sequence")

def getter(self:NmrResidue) -> NmrResidue:
  obj = self._wrappedData.previousResidue
  return None if obj is None else self._project._data2Obj.get(obj)
def setter(self:NmrResidue, value:NmrResidue):
  self._wrappedData.previousResidue = None if value is None else value._wrappedData
NmrResidue.previousResidue = property(getter, setter, None, "Previous NmrResidue in sequence")

del getter
del setter
    
def newNmrResidue(parent:NmrChain, name:str=None, sequenceCode:str=None, comment:str=None) -> NmrResidue:
  """Create new child NmrResidue"""
  apiNmrChain = parent._wrappedData
  nmrProject = apiNmrChain.nmrProject
  obj = nmrProject.newResonanceGroup(sequenceCode=sequenceCode, name=name, details=comment,
                                     nmrChain=apiNmrChain)
  return parent._project._data2Obj.get(obj)


def fetchNmrResidue(parent:NmrChain, sequenceCode:str=None, name:str=None) -> NmrResidue:
  """Fetch NmrResidue with name=name, creating it if necessary"""
  apiResonanceGroup = parent._wrappedData.findFirstResonanceGroup(sequenceCode=sequenceCode)
  if apiResonanceGroup:
    if name is not None and name != apiResonanceGroup.name:
      raise ValueError("%s has residue type %s, not %s" % (sequenceCode,
                                                           apiResonanceGroup.name, name))
    else:
      result = parent._project._data2Obj.get(apiResonanceGroup)
  else:
    result = parent.newNmrResidue(name=name, sequenceCode=sequenceCode)
  #
  return result

# Connections to parents:
NmrChain._childClasses.append(NmrResidue)

NmrChain.newNmrResidue = newNmrResidue
NmrChain.fetchNmrResidue = fetchNmrResidue

# Notifiers:
className = ApiResonanceGroup._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':NmrResidue}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
