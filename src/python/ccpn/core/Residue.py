"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import typing

from ccpn.util import Common as commonUtil
from ccpn.core.Project import Project
from ccpn.core.Chain import Chain
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccp.molecule.MolSystem import Residue as ApiResidue


class Residue(AbstractWrapperObject):
  """A molecular Residue, contained in a Chain, and containing Atoms.
  Crucial attributes: residueType (e.g. 'ALA'), residueVariant (NEF-based), sequenceCode (e.g. '123')
  """
  
  #: Short class name, for PID.
  shortClassName = 'MR'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Residue'

  _parentClass = Chain

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
  def _localCcpnSortKey(self) -> typing.Tuple:
    """Local sorting key, in context of parent."""
    return(self._wrappedData.seqId,)
    
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

        nextResidue = self.nextResidue
        previousResidue = self.previousResidue
        if previousResidue is None:
          if nextResidue is None:
            return 'single'
        elif nextResidue is None:
          chainResidues = self.chain.residues
          if self is chainResidues[-1]:
            # Last residue in chain
            return 'middle'
          else:
            nextInLine = chainResidues[chainResidues.index(self) + 1]
            if nextInLine._wrappedData.linking in ('start', 'none'):
              # Next in chain is start or non-linear
              return 'middle'
            altSelf = nextInLine.previousResidue
            if (altSelf and altSelf._wrappedData.seqId > nextInLine.seqId
              and altSelf._wrappedData.linking == 'middle'):
              # Next residue is cyclic (start of)
              return 'middle'
            else:
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

    elif molType == 'dummy':
      return 'dummy'

    else:
      # All other types have linking 'non-linear' in the wrapper
      return 'single'
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
  def residueVariant(self) -> typing.Optional[str]:
    """NEF convention Residue variant descriptor (protonation state etc.) for residue"""
    atomNamesRemoved, atomNamesAdded = self._wrappedData.getAtomNameDifferences()
    ll = ['-' + x for x in sorted(atomNamesRemoved)]
    ll.extend('+' + x for x in sorted(atomNamesAdded))
    return ','.join(ll) or None

  @property
  def descriptor(self) -> str:
    """variant descriptor (protonation state etc.) for residue, as defined in the CCPN V2 ChemComp
    description."""
    return self._wrappedData.descriptor
    
  @descriptor.setter
  def descriptor(self, value:str):
    self._wrappedData.descriptor = value

  @property
  def configuration(self) -> typing.Optional[str]:
    """Residue conformation or other non-covalent distinction.

    Example: cis/trans/None for the peptide bonds N-terminal to a residue"""
    return self._wrappedData.configuration

  @configuration.setter
  def configuration(self, value):
    # TODO implement this as a proper enumeration
    allowedValues = ('cis', 'trans', None)
    if value in allowedValues:
      self._wrappedData.configuration = value
    else:
      raise ValueError("%s configuration must be one of %s" % (self, allowedValues))
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def nextResidue(self) -> typing.Optional['Residue']:
    """Next residue in sequence, if any, otherwise None"""
    apiResidue = self._wrappedData

    molResidue = apiResidue.molResidue.nextMolResidue
    if molResidue is None:
      result = None
      self._project._logger.debug("No next residue - API ")
    else:
      result = self._project._data2Obj.get(
        apiResidue.chain.findFirstResidue(seqId=molResidue.serial))
    #
    return result

  @property
  def previousResidue(self) -> typing.Optional['Residue']:
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

  def rename(self, sequenceCode:str=None):
    """Reset Residue.sequenceCode (residueType is immutable).
    Renaming to None sets the sequence code to the seqId (serial number equivalent)
    """
    apiResidue = self._wrappedData

    self._startCommandEchoBlock('rename', sequenceCode)
    self._project.blankNotification()
    try:
      if sequenceCode is None:
        seqCode = apiResidue.seqId
        seqInsertCode = ' '

      else:
        # Parse values from sequenceCode
        code, ss, offset = commonUtil.parseSequenceCode(sequenceCode)
        if code is None or offset is not None:
          raise ValueError("Illegal value for Residue.sequenceCode: %s" % sequenceCode)
        seqCode = code
        seqInsertCode = ss or ' '

      previous = apiResidue.chain.findFirstResidue(seqCode=seqCode, seqInsertCode=seqInsertCode)
      if (previous not in (None, apiResidue)):
        raise ValueError("New sequenceCode %s clashes with existing Residue %s"
                         % (sequenceCode, self._project._data2Obj.get(previous)))

      apiResidue.seqCode = seqCode
      apiResidue.seqInsertCode = seqInsertCode
    finally:
      self._endCommandEchoBlock()
      self._project.unblankNotification()
    self._finaliseAction('rename')
    self._finaliseAction('change')

  def resetVariantToDefault(self):
    """Reset Residue.residueVariant to the default variant"""
    atomNamesMissing, extraAtomNames = self._wrappedData.getAtomNameDifferences()
    # No need for testing - the names returned are guaranteed to be missing/superfluous
    for atomName in atomNamesMissing:
      self.newAtom(name=atomName)
    for atomName in extraAtomNames:
      self.getAtom(atomName).delete()

  # Implementation functions

  def _setFragmentResidues(self, chainFragment, residues):
    """set the residues connected to the chainFragment
    CCPN Internal - ussed to handle removing reside link from the api
    """
    chainFragment.__dict__['residues'] = tuple(residues)

  def delete(self):
    """delete residue.
    Causes an error when just calling residue._wrappedData.delete()
    new method to delete from the chainFragment
    """
    chainFragment = self._wrappedData.chainFragment
    apiResidue = self._wrappedData

    if self.allNmrResidues:
      raise TypeError('Cannot delete residue that has assigned nmrResidues')

    if self._wrappedData in chainFragment.residues:

      self._startCommandEchoBlock('delete')
      undo = self._project._undo

      try:
        oldResidues = list(chainFragment.residues)
        newResidues = list(chainFragment.residues)
        delRes = newResidues.pop(newResidues.index(apiResidue))
        delRes.delete()

        # delete the residue from the fragment
        chainFragment.__dict__['residues'] = tuple(newResidues)

        # add new undo item to set the residues in the chainFragment
        if undo is not None:
          undo.newItem(self._setFragmentResidues, self._setFragmentResidues,
                         undoArgs=(chainFragment, oldResidues),
                         redoArgs=(chainFragment, newResidues))

      finally:
        self._endCommandEchoBlock()

  @property
  def nextResidue(self) -> 'Residue':
    "Next sequentially connected Residue"
    apiResidue = self._wrappedData
    nextApiMolResidue = apiResidue.molResidue.nextMolResidue
    if nextApiMolResidue is None:
      return None
    else:
      return self._project._data2Obj.get(
              apiResidue.chain.findFirstResidue(seqId=nextApiMolResidue.serial))

  @property
  def previousResidue(self) -> 'Residue':
    "Previous sequentially connected Residue"
    apiResidue = self._wrappedData
    previousApiMolResidue = apiResidue.molResidue.previousMolResidue
    if previousApiMolResidue is None:
      return None
    else:
      return self._project._data2Obj.get(
              apiResidue.chain.findFirstResidue(seqId=previousApiMolResidue.serial))

  @property
  def nmrResidue(self) -> typing.Optional['NmrResidue']:
    "NmrResidue to which Residue is assigned"
    try:
      return self._project.getNmrResidue(self._id)
    except:
      return None

  # GWV 20181122: removed setters between Chain/NmrChain, Residue/NmrResidue, Atom/NmrAtom
  # @nmrResidue.setter
  # def nmrResidue(self, value:'NmrResidue'):
  #   oldValue = self.nmrResidue
  #   if oldValue is value:
  #     return
  #   elif oldValue is not None:
  #     oldValue.assignTo()
  #   #
  #   if value is not None:
  #     value.residue = self

  @property
  def allNmrResidues(self)-> typing.Tuple['NmrResidue']:
    """AllNmrResidues corresponding to Residue - E.g. (for MR:A.87)
    NmrResidues NR:A.87, NR:A.87+0, NR:A.88-1, NR:A.82+5, etc.
    """
    result = []

    nmrChain = self.chain.nmrChain
    if nmrChain is not None:
      nmrResidue = self.nmrResidue
      if nmrResidue is not None:
        result = [nmrResidue]

      for offset in set(x.relativeOffset for x in nmrChain.nmrResidues):
        if offset is not None:
          residue = self
          if offset > 0:
            for ii in range(offset):
              residue = residue.previousResidue
              if residue is None:
                break
          elif offset < 0:
            for ii in range(-offset):
              residue = residue.nextResidue
              if residue is None:
                break
          #
          if residue is not None:
            sequenceCode = '%s%+d' % (residue.sequenceCode, offset)
            ll = [x for x in nmrChain.nmrResidues if x.sequenceCode == sequenceCode]
            if ll:
              result.extend(ll)
    return tuple(sorted(result))

  @property
  def hasAssignedAtoms(self) -> bool:
    """
    :return: True if any of its atoms have an assignment
    """
    return any([a.isAssigned for a in self.atoms])

  #=========================================================================================
  # Implementation functions
  #=========================================================================================

  @classmethod
  def _getAllWrappedData(cls, parent: Chain)-> list:
    """get wrappedData (MolSystem.Residues) for all Residue children of parent Chain"""
    # NB this sorts in seqId order - which is the order we want.
    # If the seqId order does not match the sequence we have a problem anyway.
    # NBNB the doe relies on this sorting order to handle position-specific labeling
    # for substances
    return parent._apiChain.sortedResidues()

#=========================================================================================

# GWV 20181122: Moved into class
# def getter(self:Residue) -> Residue:
#   apiResidue = self._wrappedData
#   nextApiMolResidue = apiResidue.molResidue.nextMolResidue
#   if nextApiMolResidue is None:
#     return None
#   else:
#     return self._project._data2Obj.get(
#       apiResidue.chain.findFirstResidue(seqId=nextApiMolResidue.serial))
# Residue.nextResidue = property(getter, None, None, "Next sequentially connected Residue")

# GWV 20181122: Moved into class
# def getter(self:Residue) -> Residue:
#   apiResidue = self._wrappedData
#   previousApiMolResidue = apiResidue.molResidue.previousMolResidue
#   if previousApiMolResidue is None:
#     return None
#   else:
#     return self._project._data2Obj.get(
#       apiResidue.chain.findFirstResidue(seqId=previousApiMolResidue.serial))
# Residue.previousResidue = property(getter, None, None, "Previous sequentially connected Residue")
#
# del getter
    
# Connections to parents:

# No 'new' function - chains are made elsewhere

# Notifiers:
Project._apiNotifiers.extend(
  (
    ('_finaliseApiRename', {}, ApiResidue._metaclass.qualifiedName(), 'setSeqCode'),
    ('_finaliseApiRename', {}, ApiResidue._metaclass.qualifiedName(), 'setSeqInsertCode'),
  )
)
