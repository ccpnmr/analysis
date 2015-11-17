"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpn._wrapper._Atom import Atom

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

import numpy
from ccpncore.util.Types import Tuple, Sequence, Optional
from ccpncore.util import Pid
from ccpncore.util import Common as commonUtil
from ccpncore.lib.spectrum import Spectrum as spectrumLib
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Chain
from ccpncore.api.ccp.molecule.MolStructure import StructureEnsemble as ApiStructureEnsemble
from ccpncore.api.ccp.molecule.MolStructure import Atom as ApiCoordAtom


class StructureEnsemble(AbstractWrapperObject):
  """Ensemble of coordinate structures."""
  
  #: Short class name, for PID.
  shortClassName = 'SE'
  # Attribute is necessary as subclasses must use superclass className
  className = 'StructureEnsemble'

  #: Name of plural link to instances of class
  _pluralLinkName = 'structureEnsembles'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def _apiStructureEnsemble(self) -> ApiStructureEnsemble:
    """ CCPN api StructureEnsemble matching ccpn.StructureEnsemble"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - ID number converted to string"""
    return str(self._wrappedData.ensembleId)

  @property
  def ensembleId(self) -> int:
    """ID number, key attribute for ccpn.StructureEnsemble"""
    return self._wrappedData.ensembleId

  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  @property
  def atomIds(self) -> Tuple[str, ...]:
    """Tuple of atom id ('chainCode.sequenceCode.residueType.atomName' for atoms making up structure ensemble
    The atom IDs and their order is the same for all ccpn.Models in the ensemble."""
    IDSEP = Pid.IDSEP
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
    """Tuple of atom id ('chainCode.sequenceCode.residueType' for residues making up structure ensemble
    The residue IDs and their order is the same for all ccpn.Models in the ensemble."""
    IDSEP = Pid.IDSEP
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
      shape = apiDataMatrix.shape
      result = self._coordinateData = numpy.reshape(data, shape)
      return result


  @coordinateData.setter
  def coordinateData(self, value):
    apiStructureEnsemble = self._apiStructureEnsemble
    shape = (len(apiStructureEnsemble.models), apiStructureEnsemble.nAtoms, 3)
    if value.shape !=  shape:
      raise ValueError("coordinateData value does not match shape %s" % str(shape))

    # Set cached copy to value. NB this is the original, NOT a copy
    self._coordinateData = value

    # Set underlying data values to match
    apiDataMatrix = apiStructureEnsemble.findFirstDataMatrix(name='coordinates')
    if apiDataMatrix is None:
      apiStructureEnsemble.newDataMatrix(name='coordinates', shape=shape, data=value.flat)
    else:
      apiDataMatrix.data = value.flat

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
      shape = apiDataMatrix.shape
      result = self._occupancyData = numpy.reshape(data, shape)
      return result

  @occupancyData.setter
  def occupancyData(self, value):
    apiStructureEnsemble = self._apiStructureEnsemble
    shape = (len(apiStructureEnsemble.models), apiStructureEnsemble.nAtoms)
    if value.shape !=  shape:
      raise ValueError("occupancyData value does not match shape %s" % str(shape))

    # Set cached copy to value. NB this is the original, NOT a copy
    self._occupancyData = value

    # Set underlying data values to match
    apiDataMatrix = apiStructureEnsemble.findFirstDataMatrix(name='occupancies')
    if apiDataMatrix is None:
      apiStructureEnsemble.newDataMatrix(name='occupancies', shape=shape, data=value.flat)
    else:
      apiDataMatrix.data = value.flat

  @property
  def bFactorData(self) -> numpy.ndarray:
    """modelCount * atomCount  numpy array of atom B factors.
    NB the occupancyData array is a cached copy.
    It can be modified, but modifications will be kept in cache till the attribute is
    set or the project is saved."""
    if hasattr(self, '_bFactorData'):
      return self._occupancyData
    else:
      apiDataMatrix = self._apiStructureEnsemble.findFirstDataMatrix(name='bFactors')
      if apiDataMatrix is None:
        return None
      data = apiDataMatrix.data
      if not data:
        return None
      # We have the data. make cached copy, and return it
      shape = apiDataMatrix.shape
      result = self._bFactorData = numpy.reshape(data, shape)
      return result

  @bFactorData.setter
  def bFactorData(self, value):
    apiStructureEnsemble = self._apiStructureEnsemble
    shape = (len(apiStructureEnsemble.models), apiStructureEnsemble.nAtoms)
    if value.shape !=  shape:
      raise ValueError("bFactorData value does not match shape %s" % str(shape))

    # Set cached copy to value. NB this is the original, NOT a copy
    self._bFactorData = value

    # Set underlying data values to match
    apiDataMatrix = apiStructureEnsemble.findFirstDataMatrix(name='bFactors')
    if apiDataMatrix is None:
      apiStructureEnsemble.newDataMatrix(name='bFactors', shape=shape, data=value.flat)
    else:
      apiDataMatrix.data = value.flat

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

  def getAtomCoordinates(self, atomId) -> Optional[numpy.ndarray]:
    """get nModels * 3 array of coordinates for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      return None
    else:
      return self.coordinateData[:,apiCoordAtom.index,:]

  def getAtomOccupancies(self, atomId) -> Optional[numpy.ndarray]:
    """get nModels array of occupancies for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      return None
    else:
      return self.occupancyData[:,apiCoordAtom.index,:]

  def getAtomBFactors(self, atomId) -> Optional[numpy.ndarray]:
    """get nModels array of bFactors for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      return None
    else:
      return self.bFactorData[:,apiCoordAtom.index,:]

  def getAtomSpecificNames(self, atomId) -> Optional[numpy.ndarray]:
    """get nModels array of model-specific names for atom atomId"""
    apiCoordAtom = self._atomId2CoordAtom(atomId)
    if apiCoordAtom is None:
      return None
    else:
      return self.atomNameData[:,apiCoordAtom.index,:]

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
    seqId = -1
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
        elementName = spectrumLib.name2ElementSymbol(name) or 'Unknown'
        coordResidue.newAtom(name=name, elementName=elementName)

      else:
        raise ValueError("atomId %s matches pre-existing atom in StructureEnsemble" % atomId)

  # def removeAtomId(self, atomId):
  #   """Remove atomId from the structureEnsemble, removing coordinates etc. from the data"""
  #   apiCoordAtom = self._atomId2CoordAtom(atomId)
  #   if apiCoordAtom is None:
  #     raise ValueError("Atom %s does not exist" % atomId)
  #   else:
  #     for tag in ('coordinateData', 'occupancyData', 'bFactorData', 'atomNameData'):
  #       #Reset arrays to original value, to flush changes to API level
  #       data = getattr(self, tag)
  #       if data is not None:
  #         setattr(self, tag, data)
  #
  #         NBNB not ready TBD


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


  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData for all NmrConstraintStores linked to NmrProject"""
    return parent._wrappedData.molSystem.sortedStructureEnsembles()

def _newStructureEnsemble(self:Project, ensembleId:int, comment:str=None) -> StructureEnsemble:
  """Create new, empty ccpn.StructureEnsemble"""
  
  nmrProject = self._wrappedData
  newApiStructureEnsemble = nmrProject.root.newStructureEnsemble(molSystem=nmrProject.molSystem,
                                                         ensembleId=ensembleId, details=comment)
  return self._data2Obj.get(newApiStructureEnsemble)
    
    
# Connections to parents:
Project._childClasses.append(StructureEnsemble)
Project.newStructureEnsemble = _newStructureEnsemble
del _newStructureEnsemble

# Notifiers:
className = ApiStructureEnsemble._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':StructureEnsemble}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_finaliseUnDelete', {}, className, 'undelete'),
  )
)
