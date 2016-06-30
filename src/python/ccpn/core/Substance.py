"""Module Documentation here

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

from collections import OrderedDict
from typing import Tuple, Optional, Sequence

from ccpn.core.Project import Project
from ccpn.core.Sample import Sample
from ccpn.core.SampleComponent import SampleComponent
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.util import Pid
from ccpn.util.Constants import DEFAULT_LABELING
from ccpnmodel.ccpncore.api.ccp.lims.RefSampleComponent import AbstractComponent as ApiRefComponent
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpnmodel.ccpncore.lib import Util as coreUtil
from ccpnmodel.ccpncore.lib.molecule import MoleculeModify

_apiClassNameMap = {
  'MolComponent':'Molecule',
  'Substance':'Material'
}

class Substance(AbstractWrapperObject):
  """Substance (molecule, material, buffer, cell, ..).

  The default substanceType is 'Molecule', corresponding to one or more molecules.
  It is possible (but not mandatory)to make a Substance associated to a single chain molecule,
  using the Project.createPolymerSubstance function. There is currently no provision for
  associating a Substance with several chains in a multi-chain - use Composite instead.
   """
  
  #: Short class name, for PID.
  shortClassName = 'SU'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Substance'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'substances'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiRefComponent._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiSubstance(self) -> ApiRefComponent:
    """ API RefSampleComponent matching Substance"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - name.labeling"""
    obj =  self._wrappedData

    name = obj.name
    labeling = obj.labeling
    if labeling == DEFAULT_LABELING:
      labeling = ''
    return Pid.createId(name, labeling)

  @property
  def name(self) -> str:
    """name of Substance"""
    return self._wrappedData.name

  @property
  def labeling(self) -> str:
    """labeling descriptor of Substance (default is 'std')"""
    result = self._wrappedData.labeling
    if result == DEFAULT_LABELING:
      result = None
    #
    return result
    
  @property
  def _parent(self) -> Sample:
    """Project containing Substance."""
    return  self._project

  @property
  def substanceType(self) -> str:
    """Category of substance: Molecule, Cell, Material, or Composite

    - Molecule is a single molecule, including plasmids

    - Cell is a cell,

    - Material is a mixture, like fetal calf serum, growth medium, or standard buffer,

    - Composite is multiple components in fixed ratio, like a protein-ligand or multiprotein
    complex, or (technically) a Cell containing a particular plasmid.
    """
    result = self._wrappedData.className
    return _apiClassNameMap.get(result, result)

  @property
  def synonyms(self) -> Tuple[str, ...]:
    """Synonyms for Substance name"""
    return self._wrappedData.synonyms

  @synonyms.setter
  def synonyms(self, value):
    """Synonyms for Substance name"""
    self._wrappedData.synonyms = value

  @property
  def userCode(self) -> Optional[str]:
    """User-defined compound code"""
    return self._wrappedData.userCode

  @userCode.setter
  def userCode(self, value:str):
    self._wrappedData.userCode = value

  @property
  def smiles(self) -> Optional[str]:
    """Smiles string - for substances that have one"""
    apiRefComponent = self._wrappedData
    return apiRefComponent.smiles if hasattr(apiRefComponent, 'smiles') else None

  @smiles.setter
  def smiles(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'smiles'):
      apiRefComponent.smiles = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'smiles'" %_apiClassNameMap.get(ss, ss))

  @property
  def inChi(self) -> Optional[str]:
    """inChi string - for substances that have one"""
    apiRefComponent = self._wrappedData
    return apiRefComponent.inChi if hasattr(apiRefComponent, 'inChi') else None

  @inChi.setter
  def inChi(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'inChi'):
      apiRefComponent.inChi = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'inChi'" %_apiClassNameMap.get(ss, ss))

  @property
  def casNumber(self) -> Optional[str]:
    """CAS number string - for substances that have one"""
    apiRefComponent = self._wrappedData
    return apiRefComponent.casNum if hasattr(apiRefComponent, 'casNum') else None

  @casNumber.setter
  def casNumber(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'casNum'):
      apiRefComponent.casNum = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'casNumber'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def empiricalFormula(self) -> Optional[str]:
    """Empirical molecular formula string - for substances that have one"""
    apiRefComponent = self._wrappedData
    return (apiRefComponent.empiricalFormula if hasattr(apiRefComponent, 'empiricalFormula')
            else None)

  @empiricalFormula.setter
  def empiricalFormula(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'empiricalFormula'):
      apiRefComponent.empiricalFormula = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'empiricalFormula'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def sequenceString(self) -> Optional[str]:
    """Molecular sequence string - set by the createPolymerSubstance function. Substances
    created by this function can be used to generate matching chains with the
    createChainFromSubstance function

    For standard polymers defaults to a string of one-letter codes;
    for other molecules to a comma-separated tuple of three-letter codes"""
    apiRefComponent = self._wrappedData
    return apiRefComponent.seqString if hasattr(apiRefComponent, 'seqString') else None

  @property
  def molecularMass(self) -> Optional[float]:
    """Molecular mass - for substances that have one"""
    apiRefComponent = self._wrappedData
    return apiRefComponent.molecularMass if hasattr(apiRefComponent, 'molecularMass') else None

  @molecularMass.setter
  def molecularMass(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'molecularMass'):
      apiRefComponent.molecularMass = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'molecularMass'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def atomCount(self) -> Optional[int]:
    """Number of atoms in the molecule - for Molecular substances"""
    apiRefComponent = self._wrappedData
    return apiRefComponent.atomCount if hasattr(apiRefComponent, 'atomCount') else None

  @atomCount.setter
  def atomCount(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'atomCount'):
      apiRefComponent.atomCount = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'atomCount'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def bondCount(self) -> Optional[int]:
    """Number of bonds in the molecule - for Molecular substances"""
    apiRefComponent = self._wrappedData
    return apiRefComponent.bondCount if hasattr(apiRefComponent, 'bondCount') else None

  @bondCount.setter
  def bondCount(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'bondCount'):
      apiRefComponent.bondCount = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'bondCount'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def ringCount(self) -> Optional[int]:
    """Number of rings in the molecule - for Molecular substances"""
    apiRefComponent = self._wrappedData
    return apiRefComponent.ringCount if hasattr(apiRefComponent, 'ringCount') else None

  @ringCount.setter
  def ringCount(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'ringCount'):
      apiRefComponent.ringCount = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'ringCount'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def hBondDonorCount(self) -> Optional[int]:
    """Number of hydrogen bond donors in the molecule - for Molecular substances"""
    apiRefComponent = self._wrappedData
    return apiRefComponent.hBondDonorCount if hasattr(apiRefComponent, 'hBondDonorCount') else None

  @hBondDonorCount.setter
  def hBondDonorCount(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'hBondDonorCount'):
      apiRefComponent.hBondDonorCount = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'hBondDonorCount'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def hBondAcceptorCount(self) -> Optional[int]:
    """Number of hydrogen bond acceptors in the molecule - for Molecular substances"""
    apiRefComponent = self._wrappedData
    return (apiRefComponent.hBondAcceptorCount if hasattr(apiRefComponent, 'hBondAcceptorCount')
            else None)

  @hBondAcceptorCount.setter
  def hBondAcceptorCount(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'hBondAcceptorCount'):
      apiRefComponent.hBondAcceptorCount = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'hBondAcceptorCount'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def polarSurfaceArea(self) -> Optional[float]:
    """Polar surface area (in square Angstrom) of the molecule - for Molecular substances"""
    apiRefComponent = self._wrappedData
    return (apiRefComponent.polarSurfaceArea if hasattr(apiRefComponent, 'polarSurfaceArea')
            else None)

  @polarSurfaceArea.setter
  def polarSurfaceArea(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'polarSurfaceArea'):
      apiRefComponent.polarSurfaceArea = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'polarSurfaceArea'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def logPartitionCoefficient(self) -> Optional[float]:
    """Logarithm of the octanol-water partition coefficient (logP) - for Molecular substances"""
    apiRefComponent = self._wrappedData
    return (apiRefComponent.logPartitionCoefficient
            if hasattr(apiRefComponent, 'logPartitionCoefficient') else None)

  @logPartitionCoefficient.setter
  def logPartitionCoefficient(self, value):
    apiRefComponent = self._wrappedData
    if hasattr(apiRefComponent, 'logPartitionCoefficient'):
      apiRefComponent.logPartitionCoefficient = value
    else:
      ss = apiRefComponent.className
      raise TypeError( "%s type Substance has no attribute 'logPartitionCoefficient'"
                       %_apiClassNameMap.get(ss, ss))

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value


  @property
  def sampleComponents(self) -> Tuple[SampleComponent, ...]:
    """SampleComponents that correspond to Substance"""
    name = self.name
    apiLabeling = self.labeling
    if apiLabeling is None:
      apiLabeling = DEFAULT_LABELING
    apiSampleStore = self._project._apiNmrProject.sampleStore
    data2Obj = self._project._data2Obj
    return tuple(data2Obj[x]
                 for y in apiSampleStore.sortedSamples()
                 for x in y.sortedSampleComponents()
                 if x.name == name and x.labeling == apiLabeling)


  @property
  def referenceSpectra(self) -> Tuple[Spectrum, ...]:
    """Reference Spectra acquired for Substance.
    There should be only one reference spectrum for each experiment type"""

    name = self.name
    data2Obj = self._project._data2Obj
    return tuple(data2Obj[y] for x in self._project._apiNmrProject.sortedExperiments()
                 for y in x.sortedDataSources()
                 if x.refComponentName == name)

  @referenceSpectra.setter
  def referenceSpectra(self, value):
    name = self.name
    for spectrum in self.referenceSpectra:
      spectrum._apiDataSource.experiment.refComponentName = None
    for spectrum in value:
      spectrum._apiDataSource.experiment.refComponentName = name


  # Implementation functions
  def rename(self, name:str=None, labeling:str=None):
    """Rename Substance, changing its Id and Pid, and rename SampleComponents and SpectrumHits
    with matching names. If name is None, the existing value will be used.
    Labeling 'None'  means 'Natural abundance'"""

    oldName = self.name
    if name is None:
      name = oldName
    elif Pid.altCharacter in name:
      raise ValueError("Character %s not allowed in ccpn.Sample.name" % Pid.altCharacter)

    oldLabeling = self.labeling
    apiLabeling = labeling
    if labeling is None:
      apiLabeling = DEFAULT_LABELING
    elif  Pid.altCharacter in labeling:
        raise ValueError("Character %s not allowed in ccpn.Sample.labeling" % Pid.altCharacter)

    self._startFunctionCommandBlock('rename', name, labeling)
    undo = self._project._undo
    if undo is not None:
      undo.increaseBlocking()

    try:
      renamedObjects = [self]
      for sampleComponent in self.sampleComponents:
        for spectrumHit in sampleComponent.spectrumHits:
          coreUtil._resetParentLink(spectrumHit._wrappedData, 'spectrumHits',
            OrderedDict((('substanceName',name),
                        ('sampledDimension',spectrumHit.pseudoDimensionNumber),
                        ('sampledPoint',spectrumHit.pointNumber)))
          )
          renamedObjects.append(spectrumHit)

        # NB this must be done AFTER the spectrumHit loop to avoid breaking links
        coreUtil._resetParentLink(sampleComponent._wrappedData, 'sampleComponents',
          OrderedDict((('name',name), ('labeling',apiLabeling)))
        )
        renamedObjects.append(sampleComponent)

      # NB this must be done AFTER the sampleComponent loop to avoid breaking links
      coreUtil._resetParentLink(self._wrappedData, 'components',
          OrderedDict((('name',name), ('labeling',apiLabeling)))
        )
      for obj in renamedObjects:
        obj._finaliseAction('rename')
        obj._finaliseAction('change')

    finally:
      if undo is not None:
        undo.decreaseBlocking()
      self._project._appBase._endCommandBlock()

    undo.newItem(self.rename, self.rename, undoArgs=(oldName,oldLabeling),
                 redoArgs=(name, labeling,))


  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> list:
    """get wrappedData (SampleComponent) for all SampleComponent children of parent Sample"""
    componentStore = parent._wrappedData.sampleStore.refSampleComponentStore
    if componentStore is None:
      return []
    else:
      return componentStore.sortedComponents()

# Connections to parents:

def _newSubstance(self:Project, name:str, labeling:str=None, substanceType:str='Molecule',
                  userCode:str=None, smiles:str=None, inChi:str=None, casNumber:str=None,
                  empiricalFormula:str=None, molecularMass:float=None, comment:str=None,
                  synonyms:Sequence[str]=(), atomCount:int=None, bondCount:int=None,
                  ringCount:int=None, hBondDonorCount:int=None, hBondAcceptorCount:int=None,
                  polarSurfaceArea:float=None, logPartitionCoefficient:float=None
                 ) -> Substance:
  """Create new substance WITHOUT storing the sequence internally
  (and hence not suitable for making chains). SubstanceType defaults to 'Molecule'.

  ADVANCED alternatives are 'Cell', 'Material', and 'Composite'"""

  if labeling is None:
    apiLabeling = DEFAULT_LABELING
  else:
    apiLabeling = labeling

  # Default values for 'new' function, as used for echoing to console
  defaults = OrderedDict(
    (('labeling',None), ('substanceType', 'Molecule'),
     ('userCode',None), ('smiles',None), ('inChi', None),
     ('casNumber',None), ('empiricalFormula',None), ('molecularMass', None),
     ('comment',None), ('synonyms',()), ('atomCount', None),
     ('bondCount',None), ('ringCount',None), ('hBondDonorCount', None),
     ('hBondAcceptorCount',None), ('polarSurfaceArea',None), ('logPartitionCoefficient', None)
    )
  )

  for ss in (name, labeling):
    if ss and Pid.altCharacter in ss:
      raise ValueError("Character %s not allowed in ccpn.Substance id: %s.%s" %
                       (Pid.altCharacter, name, labeling))

  apiNmrProject = self._wrappedData
  apiComponentStore = apiNmrProject.sampleStore.refSampleComponentStore

  if apiComponentStore.findFirstComponent(name=name, labeling=apiLabeling) is not None:
    raise ValueError("Substance %s.%s already exists" % (name, labeling))

  else:
    oldSubstance = apiComponentStore.findFirstComponent(name=name)

  params = {
    'name':name, 'labeling':apiLabeling, 'userCode':userCode, 'synonyms':synonyms,
    'details':comment
  }

  self._startFunctionCommandBlock('newSubstance', name, values=locals(), defaults=defaults,
                                  parName='newSubstance')
  try:
    if substanceType == 'Material':
      if oldSubstance is not None and oldSubstance.className != 'Substance':
        raise ValueError("Substance name %s clashes with substance of different type: %s"
                          % (name, oldSubstance.className))
      else:
        apiResult = apiComponentStore.newSubstance(**params)
    elif substanceType == 'Cell':
      if oldSubstance is not None and oldSubstance.className != 'Cell':
        raise ValueError("Substance name %s clashes with substance of different type: %s"
                          % (name, oldSubstance.className))
      else:
        apiResult = apiComponentStore.newCell(**params)
    elif substanceType == 'Composite':
      if oldSubstance is not None and oldSubstance.className != 'Composite':
        raise ValueError("Substance name %s clashes with substance of different type: %s"
                          % (name, oldSubstance.className))
      else:
        apiResult = apiComponentStore.newComposite(**params)
    elif substanceType == 'Molecule':
      if oldSubstance is not None and oldSubstance.className != 'MolComponent':
        raise ValueError("Substance name %s clashes with substance of different type: %s"
                          % (name, oldSubstance.className))
      else:
        apiResult = apiComponentStore.newMolComponent(smiles=smiles, inChi=inChi, casNum=casNumber,
          empiricalFormula=empiricalFormula, molecularMass=molecularMass, atomCount=atomCount,
          bondCount=bondCount, ringCount=ringCount, hBondDonorCount=hBondDonorCount,
          hBondAcceptorCount=hBondAcceptorCount, polarSurfaceArea=polarSurfaceArea,
          logPartitionCoefficient=logPartitionCoefficient, **params)
    else:
      raise ValueError("Substance type %s not recognised" % substanceType)
  finally:
    self._project._appBase._endCommandBlock()
  #
  return self._data2Obj[apiResult]

Project.newSubstance = _newSubstance
del _newSubstance


def _createPolymerSubstance(self:Project, sequence:Sequence[str], name:str, labeling:str=None,
              userCode:str=None, smiles:str=None, synonyms:Sequence[str]=(),comment:str=None,
              startNumber:int=1, molType:str=None, isCyclic:bool=False) -> Substance:
  """Make new Substance from sequence of residue codes, using default linking and variants

  NB: For more complex substances, you must use advanced, API-level commands.

  :param Sequence sequence: string of one-letter codes or sequence of residueNames
  :param str name: name of new substance
  :param str labeling: labeling for new substance. Optional - None means 'natural abundance'
  :param str userCode: user code for new substance (optional)
  :param str smiles: smiles string for new substance (optional)
  :param Sequence[str] synonyms: synonyms for Substance name
  :param str comment: comment for new substance (optional)
  :param int startNumber: number of first residue in sequence
  :param str molType: molType ('protein','DNA', 'RNA'). Required only if sequence is a string.
  :param bool isCyclic: Should substance created be cyclic?

  """

  if labeling is None:
    apiLabeling = DEFAULT_LABELING
  else:
    apiLabeling = labeling

  defaults = OrderedDict(
    (
      ('labeling', None), ('userCode', None), ('smiles', None),
      ('synonyms', ()), ('comment', None), ('startNumber', 1), ('molType', None),
      ('isCyclic', False)
    )
  )

  apiNmrProject = self._wrappedData

  if not sequence:
    raise ValueError("createPolymerSubstance requires non-empty sequence")

  elif apiNmrProject.sampleStore.refSampleComponentStore.findFirstComponent(name=name,
        labeling=apiLabeling) is not None:
    raise ValueError("Substance %s.%s already exists" % (name, labeling))

  elif apiNmrProject.root.findFirstMolecule(name=name) is not None:
    raise ValueError("Molecule name %s is already in use for API Molecule")

  self._startFunctionCommandBlock('createPolymerSubstance', sequence, name,
                                  values=locals(), defaults=defaults,
                                  parName='newPolymerSubstance')
  try:
    apiMolecule = MoleculeModify.createMolecule(apiNmrProject.root, sequence, molType=molType,
                                                name=name, startNumber=startNumber,
                                                isCyclic=isCyclic)
    apiMolecule.commonNames =synonyms
    apiMolecule.smiles = smiles
    apiMolecule.details=comment

    result = self._data2Obj[apiNmrProject.sampleStore.refSampleComponentStore.fetchMolComponent(
                            apiMolecule, labeling=apiLabeling)]
    result.userCode = userCode
  finally:
    self._project._appBase._endCommandBlock()
  #
  return result

Project.createPolymerSubstance = _createPolymerSubstance
del _createPolymerSubstance

def _fetchSubstance(self:Project, name:str, labeling:str=None) -> Substance:
  """get or create ccpn.Substance with given name and labeling."""


  if labeling is None:
    apiLabeling = DEFAULT_LABELING
  else:
    apiLabeling = labeling

  values = {'labeling':labeling}

  apiRefComponentStore= self._apiNmrProject.sampleStore.refSampleComponentStore
  apiResult = apiRefComponentStore.findFirstComponent(name=name, labeling=apiLabeling)

  self._startFunctionCommandBlock('fetchSubstance', name, values=values, parName='newSubstance')
  try:
    if apiResult:
      result = self._data2Obj[apiResult]
    else:
      result = self.newSubstance(name=name, labeling=labeling)
  finally:
    self._project._appBase._endCommandBlock()
  return result
#
Project.fetchSubstance = _fetchSubstance
del _fetchSubstance


def getter(self:SampleComponent) -> Optional[Substance]:
  apiRefComponentStore = self._parent._apiSample.sampleStore.refSampleComponentStore
  apiComponent = apiRefComponentStore.findFirstComponent(name=self.name,
                                                         labeling=self.labeling or DEFAULT_LABELING)
  if apiComponent is None:
    return None
  else:
    return self._project._data2Obj[apiComponent]
#
SampleComponent.substance = property(getter, None, None,
                                     "Substance corresponding to SampleComponent")

def getter(self:Spectrum) -> Substance:
  apiRefComponent = self._apiDataSource.experiment.refComponent
  return apiRefComponent or self._project._data2Obj[apiRefComponent]
def setter(self:Spectrum, value:Substance):
  apiRefComponent = value or value._apiSubstance
  self._apiDataSource.experiment.refComponent = apiRefComponent
#
Spectrum.referenceSubstance = property(getter, setter, None,
                                       "Substance that has this Spectrum as reference spectrum")
del getter
del setter

# Notifiers:

# Substance - SampleComponent link is derived through the keys of the linked objects
# There is therefore no need to monitor the link, and notifiers should be put
# on object creation and renaming
className = Nmr.Experiment._metaclass.qualifiedName()
Project._apiNotifiers.append(
  ('_modifiedLink', {'classNames':('Spectrum','Substance')}, className, 'setRefComponentName'),
)
