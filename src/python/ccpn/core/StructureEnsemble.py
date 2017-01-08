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
from typing import Tuple, Sequence, Optional

import numpy

from ccpn.core.Chain import Chain
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.lib import Pid
from ccpn.util import Common as commonUtil
from ccpnmodel.ccpncore.api.ccp.molecule.MolStructure import Atom as ApiCoordAtom
from ccpnmodel.ccpncore.api.ccp.molecule.MolStructure import StructureEnsemble as ApiStructureEnsemble

NaN = float('NaN')

_DATA_ARRAY_TAGS =('coordinateData', 'occupancyData', 'bFactorData')
# NBNB atomNameData not yet implemented
# _DATA_ARRAY_TAGS =('coordinateData', 'occupancyData', 'bFactorData', 'atomNameData')

class StructureEnsemble(AbstractWrapperObject):
  """Ensemble of coordinate structures."""
  
  #: Short class name, for PID.
  shortClassName = 'SE'
  # Attribute is necessary as subclasses must use superclass className
  className = 'StructureEnsemble'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'structureEnsembles'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiStructureEnsemble._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiStructureEnsemble(self) -> ApiStructureEnsemble:
    """ CCPN api StructureEnsemble matching StructureEnsemble"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - ID number converted to string"""
    return str(self._wrappedData.ensembleId)

  @property
  def ensembleId(self) -> int:
    """ID number of StructureEnsemble, used in Pid and to identify the StructureEnsemble. """
    return self._wrappedData.ensembleId

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  @property
  def atomIds(self) -> Tuple[str, ...]:
    """Tuple of atom id ('chainCode.sequenceCode.residueType.atomName' for atoms making up
    structure ensemble. Note that the identifier uses IUPAC atom names and Coordinate-linked
    chain and sequence specifiers, which may not match the Chains.
    The atom IDs and their order is the same for all Models in the ensemble.
    """
    result = []
    residue = None
    for atom in self._wrappedData.orderedAtoms:
      rr = atom.residue
      if rr != residue:
        # Done this way to save on function calls, as atoms are grouped by residue
        residue = rr
        code = residue.chain.code
        sequenceCode = str(residue.seqCode) + residue.seqInsertCode.strip()
        residueType = residue.code3Letter
      result.append(Pid.createId(code, sequenceCode, residueType, atom.name))
    #
    return result

  @property
  def residueIds(self) -> Tuple[str, ...]:
    """Tuple of atom id ('chainCode.sequenceCode.residueType' for residues making up
    structure ensemble
    The residue IDs and their order is the same for all Models in the ensemble."""
    result = []
    residue = None
    for atom in self._wrappedData.orderedAtoms:
      rr = atom.residue
      if rr != residue:
        # Done this way to save on function calls, as atoms are grouped by residue
        residue = rr
        code = residue.chain.code
        sequenceCode = str(residue.seqCode) + residue.seqInsertCode.strip()
        residueType = residue.code3Letter
        result.append(Pid.createId(code, sequenceCode, residueType))
    #
    return result

  @property
  def coordinateData(self) -> numpy.ndarray:
    """modelCount * atomCount * 3 numpy array of coordinates.
    NB the coordinateData array is a cached copy.
    It can be  modified, but modifications will be kept in cache till the attribute is
    set or the project is saved."""
    if hasattr(self, '_coordinateData'):
      return self._coordinateData
    else:
      apiDataMatrix = self._apiStructureEnsemble.findFirstDataMatrix(name='coordinates')
      if apiDataMatrix is None:
        return None
      data = apiDataMatrix.data
      if not data:
        return None
      # We have the data. make cached copy, and return it
      result = self._coordinateData = numpy.full(apiDataMatrix.shape, NaN)
      result.flat = data
      return result


  @coordinateData.setter
  def coordinateData(self, value):
    apiStructureEnsemble = self._apiStructureEnsemble
    shape = (len(apiStructureEnsemble.models), apiStructureEnsemble.nAtoms, 3)
    data = list(commonUtil.flattenIfNumpy(value, shape=shape))

    # Set cached copy to value. NB this is the original, NOT a copy
    if isinstance(value, numpy.ndarray):
      self._coordinateData = value
    else:
      del self._coordinateData

    # Set underlying data values to match
    apiDataMatrix = apiStructureEnsemble.findFirstDataMatrix(name='coordinates')
    if apiDataMatrix is None:
      apiStructureEnsemble.newDataMatrix(name='coordinates', shape=shape, data=data)
    else:
      apiDataMatrix.setSubmatrixData((0,0,0), (), data)

  @property
  def occupancyData(self) -> numpy.ndarray:
    """modelCount * atomCount  numpy array of atom occupancies.
    NB the occupancyData array is a cached copy.
    It can be  modified, but modifications will be kept in cache till the attribute is
    set or the project is saved."""
    if hasattr(self, '_occupancyData'):
      return self._occupancyData
    else:
      apiDataMatrix = self._apiStructureEnsemble.findFirstDataMatrix(name='occupancies')
      if apiDataMatrix is None:
        return None
      data = apiDataMatrix.data
      if not data:
        return None
      # We have the data. make cached copy, and return it
      result = self._occupancyData = numpy.full(apiDataMatrix.shape, NaN)
      result.flat = data
      return result

  @occupancyData.setter
  def occupancyData(self, value):
    apiStructureEnsemble = self._apiStructureEnsemble
    shape = (len(apiStructureEnsemble.models), apiStructureEnsemble.nAtoms)
    data = list(commonUtil.flattenIfNumpy(value, shape=shape))

    # Set cached copy to value. NB this is the original, NOT a copy
    if isinstance(value, numpy.ndarray):
      self._occupancyData = value
    else:
      del self._occupancyData

    # Set underlying data values to match
    apiDataMatrix = apiStructureEnsemble.findFirstDataMatrix(name='occupancies')
    if apiDataMatrix is None:
      apiStructureEnsemble.newDataMatrix(name='occupancies', shape=shape, data=data)
    else:
      apiDataMatrix.setSubmatrixData((0,0), (), data)

  @property
  def bFactorData(self) -> numpy.ndarray:
    """modelCount * atomCount  numpy array of atom B factors.
    NB the occupancyData array is a cached copy.
    It can be modified, but modifications will be kept in cache till the attribute is
    set or the project is saved."""
    if hasattr(self, '_bFactorData'):
      return self._bFactorData
    else:
      apiDataMatrix = self._apiStructureEnsemble.findFirstDataMatrix(name='bFactors')
      if apiDataMatrix is None:
        return None
      data = apiDataMatrix.data
      if not data:
        return None
      # We have the data. make cached copy, and return it
      result = self._bFactorData = numpy.full(apiDataMatrix.shape, NaN)
      result.flat = data
      return result

  @bFactorData.setter
  def bFactorData(self, value):
    apiStructureEnsemble = self._apiStructureEnsemble
    shape = (len(apiStructureEnsemble.models), apiStructureEnsemble.nAtoms)
    data = list(commonUtil.flattenIfNumpy(value, shape=shape))

    # Set cached copy to value. NB this is the original, NOT a copy
    if isinstance(value, numpy.ndarray):
      self._bFactorData = value
    else:
      del self._bFactorData

    # Set underlying data values to match
    apiDataMatrix = apiStructureEnsemble.findFirstDataMatrix(name='bFactors')
    if apiDataMatrix is None:
      apiStructureEnsemble.newDataMatrix(name='bFactors', shape=shape, data=data)
    else:
      apiDataMatrix.setSubmatrixData((0,0), (), data)

  @property
  def atomNameData(self) -> numpy.ndarray:
    """modelCount * atomCount  numpy array of model-specific atom names.
    Intended for storing IUPAC atom names that vary from model to model
    NB the atomNameData array is a cached copy.
    It can be modified, but modifications will be kept in cache till the attribute is
    set or the project is saved."""
    raise NotImplementedError("atomNameData not implemented yet")

  @atomNameData.setter
  def atomNameData(self, value):
    raise NotImplementedError("atomNameData not implemented yet")

  def getAtomCoordinates(self, atomId:str) -> Optional[numpy.ndarray]:
    """get nModels * 3 array of coordinates for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      return None
    else:
      return self.coordinateData[:,apiCoordAtom.index]

  def setAtomCoordinates(self, atomId:str, value:numpy.ndarray):
    """set nModels * 3 array of coordinates for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      raise ValueError("atomId %s not found" % atomId)
    else:
      self.coordinateData[:,apiCoordAtom.index] = value

  def getAtomOccupancies(self, atomId) -> Optional[numpy.ndarray]:
    """get nModels array of occupancies for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      return None
    else:
      return self.occupancyData[:,apiCoordAtom.index]

  def setAtomOccupancies(self, atomId:str, value:numpy.ndarray):
    """set nModels array of occupancies for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      raise ValueError("atomId %s not found" % atomId)
    else:
      self.occupancyData[:,apiCoordAtom.index] = value

  def getAtomBFactors(self, atomId) -> Optional[numpy.ndarray]:
    """get nModels array of bFactors for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      return None
    else:
      return self.bFactorData[:,apiCoordAtom.index]

  def setAtomBFactors(self, atomId:str, value:numpy.ndarray):
    """set nModels array of bFactors for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      raise ValueError("atomId %s not found" % atomId)
    else:
      self.bFactorData[:,apiCoordAtom.index] = value

  def getAtomSpecificNames(self, atomId) -> Optional[numpy.ndarray]:
    """get nModels array of model-specific names for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      return None
    else:
      return self.atomNameData[:,apiCoordAtom.index]

  def setAtomSpecificNames(self, atomId:str, value:numpy.ndarray):
    """set nModels array of specific atom names for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      raise ValueError("atomId %s not found" % atomId)
    else:
      self.atomNameData[:,apiCoordAtom.index] = value

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  def addChain(self, chain:Chain):
    """Add atoms from Chain (in order) to empty structureEnsemble.
    Coordinate data to be added later"""

    apiEnsemble = self._apiStructureEnsemble
    if apiEnsemble.dataMatrices:
      raise ValueError("You cannot add atoms when StructureEnsemble contains data")

    apiChain = chain._apiChain
    code = apiChain.code
    if apiEnsemble.findFirstCoordChain(code=code) is not None:
      raise ValueError("Chain '%s' already present in StructureEnsemble" % code)

    apiCoordChain = apiEnsemble.newCoordChain(code=code)
    for residue in chain.residues:
      # We loop over wrapper chains to get the correct sorted order.
      apiResidue = residue._wrappedData
      coordResidue = apiCoordChain.newResidue(seqCode=apiResidue.seqCode,
                                            seqInsertCode=apiResidue.seqInsertCode,
                                            code3Letter=apiResidue.code3Letter)
      for apiAtom in apiResidue.sortedAtoms():
        coordResidue.newAtom(name=apiAtom.name, elementSymbol=apiAtom.elementSymbol,)

  def addAtomIds(self, atomIds:Sequence[str], override:bool=False):
    """Add atoms matching atomIds (in order) to empty structureEnsemble.
    Coordinate data to be added later.
    If override is True you can add to non-empty ensembles, and consistency is not checked."""

    apiEnsemble = self._apiStructureEnsemble
    if apiEnsemble.dataMatrices and not override:
      raise ValueError("You cannot add atom Ids when StructureEnsemble contains data")

    # Set up map of existing coordResidues
    coordResidues = {}
    for coordChain in apiEnsemble.coordChains:
      code = coordChain.code
      for coordResidue in coordChain.sortedResidues():
        sequenceCode = str(coordResidue.seqCode) + coordResidue.seqInsertCode.strip()
        coordResidues[(code, sequenceCode)] = coordResidue

    # process atomIds
    for atomId in atomIds:
      # idTuple = tuple(Pid.splitId(atomId))
      code, sequenceCode, residueType, name = tuple(Pid.splitId(atomId))
      coordResidue = coordResidues.get((code, sequenceCode))
      if coordResidue is None:
        coordChain = (apiEnsemble.findFirstCoordChain(code=code) or
                      apiEnsemble.newChain(code=code))

        # split sequenceCode in seqCode and seqInsertCode
        seqCode, seqInsertCode, offset = commonUtil.parseSequenceCode(sequenceCode)
        if seqCode is None or offset is not None:
          raise ValueError("atomId %s contains an invalid sequenceCode" % atomId)
        else:
          coordResidue = coordChain.newResidue(seqCode=seqCode, seqInsertCode=seqInsertCode or ' ',
                                               code3Letter=residueType)
          coordResidues[(code,sequenceCode)] = coordResidue

      elif coordResidue.code3Letter != residueType:
        raise ValueError("atomId %s residueType does not match sequenceCode in StructureEnsemble"
                         % atomId)

      if coordResidue.findFirstAtom(name=name) is None:
        elementName = commonUtil.name2ElementSymbol(name) or 'Unknown'
        coordResidue.newAtom(name=name, elementName=elementName)

      else:
        raise ValueError("atomId %s matches pre-existing atom in StructureEnsemble" % atomId)


  def replaceAtomIds(self, atomIds:Sequence[str]):
    """Replace atomIds with new list of the same length,
    without modifying coordinates and other data"""

    oldAtomIds = self.atomIds
    if len(oldAtomIds) != len(atomIds):
      raise ValueError("The number of new atomIds must be the same as the number they replace")

    apiStructureEnsemble = self._wrappedData
    memopsRoot = apiStructureEnsemble.root
    undo = memopsRoot._undo
    memopsRoot.override = True
    if undo is not None:
      undo.increaseBlocking()
    try:
      for apiAtom in reversed(apiStructureEnsemble.orderedAtoms):
        # Done this way to speed up deletion
        apiAtom.delete()
      for apiChain in apiStructureEnsemble.coordChains:
        apiChain.delete()
      self.addAtomIds(atomIds, override=True)
    finally:
      memopsRoot.overide = False
      if undo is not None:
        undo.decreaseBlocking()

    if undo is not None:
      undo.newItem(self.replaceAtomIds, self.replaceAtomIds,
                   undoArgs=(oldAtomIds,), redoArgs=(atomIds,))

  def removeAtomIds(self, atomIds:Sequence[str]):
    """Remove atoms with atomIds, adjusting data matrices to fit"""
    for atomId in atomIds:
      self.removeAtomId(atomId)

    # NBNB TBD Maybe add undo code

  def removeAtomId(self, atomId):
    """Remove atom with atomId, adjusting data matrices to fit"""
    apiAtom = self._atomId2CoordAtom(atomId)
    if apiAtom is None:
      raise ValueError("Atom with atomId %s not found" % atomId)

    # get data arrays before we starts messing with the internals
    data = {}
    for tag in _DATA_ARRAY_TAGS:
      data[tag] = getattr(self, tag)
    # apiOrderedAtoms = apiAtom.topObject.__dict__['orderedAtoms']

    # Make new atom record and rearrange to fit
    root = apiAtom.root
    root.override = True
    undo = root._undo
    if undo is not None:
      undo.increaseBlocking()
    undoData = {}
    try:

      # # change atoms
      index = apiAtom.index
      apiAtom.delete()

      # reset data arrays
      for tag in _DATA_ARRAY_TAGS:
        xx = data.get(tag)
        # if xx:
        # numpy is DISGUSTING!!
        if xx is not None and xx.size:
          undoData[tag] = xx[:,apiAtom.index]
          setattr(self, tag, numpy.delete(xx, index, axis=1))

    finally:
      if undo is not None:
        undo.decreaseBlocking()
      root.override = False

    # NBNB TBD add undo code

  def addAtomId(self,atomId, coordinateData:numpy.ndarray=None, occupancyData:Sequence[float]=None,
              bFactorData:Sequence[float]=None, atomNameData:Sequence[str]=None):
    """Add atom with atomId. Atom is inserted at the end of the matching chain or residue
    (if any) otherwise at the end of the atomId list.
    Data matrices are filled with NaN or with the atom Name (for atomNameData)"""

    # parse atomId
    chainCode, sequenceCode, residueType, name = tuple(Pid.splitId(atomId))
    seqCode, seqInsertCode, offset = commonUtil.parseSequenceCode(sequenceCode)
    seqInsertCode = seqInsertCode or ' '
    if seqCode is None or offset is not None:
      raise ValueError("atomId %s contains an invalid sequenceCode" % atomId)

    # get data arrays before we starts messing with the internals
    data = {}
    for tag in _DATA_ARRAY_TAGS:
      data[tag] = getattr(self, tag)

    apiEnsemble = self._apiStructureEnsemble
    apiOrderedAtoms = apiEnsemble.__dict__['orderedAtoms']

    if apiOrderedAtoms:
      # Get insertion data
      useChain = apiEnsemble.findFirstCoordChain(code=chainCode)
      if useChain is None:
        nextAtomIndex = apiOrderedAtoms[-1].index + 1
      else:
        useResidue = useChain.findFirstResidue(seqCode=seqCode, seqInsertCode=seqInsertCode)
        if useResidue is None:
          ll = useChain.sortedResidues()
          for rr in ll:
            nextAtomIndex = max(x.index for x in rr.atoms)+1
            if (seqCode, seqInsertCode) > (rr.seqCode, rr.seqInsertCode):
              break
          else:
            nextAtomIndex = min(x.index for x in ll[0].atoms)
        elif useResidue.code3Letter != residueType:
          raise ValueError("New residue type of %s incompatible with previous assignment %s%s.%s"
          % (residueType, useResidue.seqCode, useResidue.seqInsertCode.strip(),
             useResidue.code3Letter))
        else:
          if useResidue.findFirstAtom(name=name) is None:
            nextAtomIndex = max(x.index for x in useResidue.atoms) + 1
          else:
            raise ValueError("Atom %s already in StructureEnsemble)" % atomId)

      # Make new atom record and rearrange to fit
      root = apiEnsemble.root
      root.override = True
      undo = root._undo
      if undo is not None:
        undo.increaseBlocking()
      try:
        if useChain is None:
          useChain = apiEnsemble.newChain(code=chainCode)
        if useResidue is None:
          useResidue = useChain.newResidue(seqCode=seqCode, seqInsertCode=seqInsertCode,
                                           code3Letter=residueType)
        newAtom = useResidue.newAtom(name=name,
                                     elementName=commonUtil.name2ElementSymbol(name) or 'Unknown')

        # reset data arrays
        for tag in _DATA_ARRAY_TAGS:
          xx = data.get(tag)
          # if xx:
          # numpy is DISGUSTING!!
          if xx is not None and xx.size:
            if tag == 'atomNameData':
              default = name
            else:
              default = NaN
            values = locals().get(tag) or default
            vv = numpy.insert(xx, nextAtomIndex, values, axis=1)
            setattr(self, tag, vv)

        # Move atom to preferred location
        if nextAtomIndex < apiOrderedAtoms[-1].index:
          for atom in apiOrderedAtoms[nextAtomIndex:]:
            atom.__dict__['index'] += 1
          apiOrderedAtoms.insert(nextAtomIndex, newAtom)
          newAtom.__dict__['index'] = nextAtomIndex
          del apiOrderedAtoms[-1]
      finally:
        if undo is not None:
          undo.decreaseBlocking()
        root.override = False

        # NBNB TBD Add undo registration here

    else:
      # Empty atomIds - just add
      nextAtomIndex = 0
      self.addAtomIds((atomId,), override=True)
      # reset data arrays
      for tag in _DATA_ARRAY_TAGS:
        xx = data.get(tag)
        # if xx:
        # numpy is DISGUSTING!!
        if xx is not None and xx.size:
          if tag == 'atomNameData':
            default = name
          else:
            default = str('NaN')
          values = locals().get(tag) or default
          setattr(self, tag, numpy.append(xx, values, axis=1))


  def _atomId2CoordAtom(self, atomId:str) -> Optional[ApiCoordAtom]:
    """Convert atomId to API MolStructure.Atom"""
    chainCode, sequenceCode, residueType, name = tuple(Pid.splitId(atomId))
    seqCode, seqInsertCode, offset = commonUtil.parseSequenceCode(sequenceCode)
    if seqCode is None or offset is not None:
      raise ValueError("atomId %s contains an invalid sequenceCode" % atomId)
    apiEnsemble = self._apiStructureEnsemble
    apiCoordChain = apiEnsemble.findFirstCoordChain(code=chainCode)
    if apiCoordChain is None:
      return None
    apiCoordResidue = apiCoordChain.findFirstResidue(seqCode=seqCode, seqInsertCode=seqInsertCode or ' ')
    if apiCoordResidue is None:
      return None
    return apiCoordResidue.findFirstAtom(name=name)

  def _flushCachedData(self):
    """Flush cached data to ensure up-to-date data are saved"""

    for tag in ('coordinateData', 'occupancyData', 'bFactorData'):
      _tag = '_' + tag
      if hasattr(self, _tag):
        # Save cached data back to underlying storage
        setattr(self, tag, getattr(self, _tag))
        delattr(self, _tag)


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all NmrConstraintStores linked to NmrProject"""
    return parent._wrappedData.molSystem.structureEnsembles

def _newStructureEnsemble(self:Project, ensembleId:int=None, comment:str=None) -> StructureEnsemble:
  """Create new, empty StructureEnsemble"""

  defaults = collections.OrderedDict((('ensembleId', None), ('comment', None)))
  
  nmrProject = self._wrappedData
  self._startFunctionCommandBlock('newStructureEnsemble', values=locals(), defaults=defaults,
                                  parName='newStructureEnsemble')
  try:
    if ensembleId is None:
      ll = nmrProject.root.structureEnsembles
      ensembleId = max(x.ensembleId for x in ll) + 1 if ll else 1
    newApiStructureEnsemble = nmrProject.root.newStructureEnsemble(molSystem=nmrProject.molSystem,
                                                           ensembleId=ensembleId, details=comment)
  finally:
    self._project._appBase._endCommandBlock()
    return self._data2Obj.get(newApiStructureEnsemble)
    
    
# Connections to parents:
Project.newStructureEnsemble = _newStructureEnsemble
del _newStructureEnsemble

# Notifiers:
