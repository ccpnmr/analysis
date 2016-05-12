"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
from typing import Optional

from ccpn.util import Pid

from ccpn import AbstractWrapperObject
from ccpn import Chain
from ccpncore.api.ccp.molecule.MolSystem import Residue as ApiResidue


class Residue(AbstractWrapperObject):
  """Molecular Residue."""
  
  #: Short class name, for PID.
  shortClassName = 'MR'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Residue'

  #: Name of plural link to instances of class
  _pluralLinkName = 'residues'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiResidue._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiResidue(self) -> ApiResidue:
    """ API residue matching Residue"""
    return self._wrappedData
  
  
  @property
  def sequenceCode(self) -> str:
    """Residue sequence code and id (e.g. '1', '127B') """
    obj = self._wrappedData
    objSeqCode = obj.seqCode
    result = (obj.seqInsertCode or '').strip()
    if objSeqCode is not None:
      result = str(objSeqCode) + result
    return result

  @property
  def _key(self) -> str:
    """Residue ID. Identical to sequenceCode.residueType. Characters translated for pid"""
    return Pid.createId(self.sequenceCode, self.residueType)
    
  @property
  def _parent(self) -> Chain:
    """Chain containing residue."""
    return self._project._data2Obj[self._wrappedData.chain]
  
  chain = _parent
    
  @property
  def residueType(self) -> str:
    """Residue type name string (e.g. 'ALA')"""
    return self._wrappedData.code3Letter or ''

  @property
  def shortName(self) -> str:
    return self._wrappedData.chemCompVar.chemComp.code1Letter or '?'
  
  @property
  def linking(self) -> str:
    """linking (substitution pattern) code for residue


    Allowed values are:

     For linear polymers: 'start', 'end', 'middle', 'single', 'break', 'cyclic'
     For other molecules: 'nonlinear'

     'cyclic' and 'break' are used at the end of linear polymer stretches to signify,
     respectively, that the polymer is cyclic, or that the residue is bound to an
     unknown residue or to a cap, so that the linear polymer chain does not continue."""

    molType = self._wrappedData.molType
    if molType in ('protein', 'DNA', 'RNA'):
      linkString = self._wrappedData.linking
      if linkString == 'none':
        return 'single'
      elif linkString in ('start', 'end'):
        return linkString
      else:
        assert linkString == 'middle', ("Illegal API linking value for linear polymer: %s"
                                        % linkString)

         # NBNB TBD FIXME - This does (MAY?) not deal properly with capped residues

        nextResidue = self.nextResidue
        previousResidue = self.previousResidue
        if previousResidue is None:
          if nextResidue is None:
            return 'single'
          else:
            return 'break'
        elif nextResidue is None:
          return 'break'
        else:

          # NBNB The detection of 'cyclic' only works if residues are given in
          # sequential order. This is not given - but is unlikely ever to break.

          seqId = self._wrappedData.seqId
          if (previousResidue._wrappedData.seqId > seqId
              and previousResidue._wrappedData.linking == 'middle'):
            return 'cyclic'
          elif (nextResidue._wrappedData.seqId < seqId
              and nextResidue._wrappedData.linking == 'middle'):
            return 'cyclic'
          else:
            return 'middle'

    else:
      # All other types have linking 'non-linear' in the wrapper
      return 'nonlinear'
    return self._wrappedData.linking
    
  @linking.setter
  def linking(self, value:str):

    # NBNB TBD FIXME - this will not work as intended when value is 'nonlinear'

    if value in ('break', 'cyclic'):
      value = 'middle'
    elif value == 'single':
      value = 'none'
    self._wrappedData.linking = value

  @property
  def residueVariant(self) -> Optional[str]:
    """NEF convention Residue variant descriptor (protonation state etc.) for residue"""
    # NBNB TBD FIXME not implemented yet, pending sorting out the NEF standard on this point
    return None

  @property
  def descriptor(self) -> str:
    """variant descriptor (protonation state etc.) for residue, as defined in the CCPN V2 ChemComp
    description."""
    return self._wrappedData.descriptor
    
  @descriptor.setter
  def descriptor(self, value:str):
    self._wrappedData.descriptor = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def nextResidue(self) -> Optional['Residue']:
    """Next residue in sequence, if any, otherwise None"""
    apiResidue = self._wrappedData

    molResidue = apiResidue.molResidue.nextMolResidue
    if molResidue is None:
      result = None
    else:
      result = self._project._data2Obj.get(
        apiResidue.chain.findFirstResidue(seqId=molResidue.serial))
    #
    return result

  @property
  def previousResidue(self) -> Optional['Residue']:
    """Previous residue in sequence, if any,otherwise None"""
    apiResidue = self._wrappedData

    molResidue = apiResidue.molResidue.previousMolResidue
    if molResidue is None:
      result = None
    else:
      result = self._project._data2Obj.get(
        apiResidue.chain.findFirstResidue(seqId=molResidue.serial))
    #
    return result

  # Implementation functions

  @classmethod
  def _getAllWrappedData(cls, parent: Chain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    # NB this is not the sort we want - sorted elsewhere
    return parent._apiChain.sortedResidues()

def getter(self:Residue) -> Residue:
  apiResidue = self._wrappedData
  nextApiMolResidue = apiResidue.molResidue.nextMolResidue
  if nextApiMolResidue is None:
    return None
  else:
    return self._project._data2Obj.get(
      apiResidue.chain.findFirstResidue(seqId=nextApiMolResidue.serial))
Residue.nextResidue = property(getter, None, None, "Next sequentially connected Residue")

def getter(self:Residue) -> Residue:
  apiResidue = self._wrappedData
  previousApiMolResidue = apiResidue.molResidue.previousMolResidue
  if previousApiMolResidue is None:
    return None
  else:
    return self._project._data2Obj.get(
      apiResidue.chain.findFirstResidue(seqId=previousApiMolResidue.serial))
Residue.previousResidue = property(getter, None, None, "Previous sequentially connected Residue")

del getter
    
# Connections to parents:
Chain._childClasses.append(Residue)

# No 'new' function - chains are made elsewhere

# Notifiers:
