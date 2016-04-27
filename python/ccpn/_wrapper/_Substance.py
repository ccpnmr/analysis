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

from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Sample
from ccpn import Spectrum
from typing import Tuple, Optional, Sequence
from ccpncore.lib.molecule import MoleculeModify
from ccpn import SampleComponent
from ccpncore.api.ccp.lims.RefSampleComponent import AbstractComponent as ApiRefComponent
from ccpncore.api.ccp.nmr import Nmr
from ccpncore.util import Pid


_apiClassNameMap = {
  'MolComponent':'Molecule',
  'Substance':'Material'
}

class Substance(AbstractWrapperObject):
  """Substance (molecule, material, buffer, cell, ..)."""
  
  #: Short class name, for PID.
  shortClassName = 'SU'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Substance'

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
    return Pid.createId(*(getattr(obj,tag) for tag in ('name', 'labeling')))

  @property
  def name(self) -> str:
    """name of Substance"""
    return self._wrappedData.name

  @property
  def labeling(self) -> str:
    """labeling descriptor of Substance (default is 'std')"""
    return self._wrappedData.labeling
    
  @property
  def _parent(self) -> Sample:
    """Project containing Substance."""
    return  self._project

  @property
  def substanceType(self) -> str:
    """Category of substance: Molecule, Cell, Material, or Composite"""
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
    return apiRefComponent.empiricalFormula if hasattr(apiRefComponent, 'empiricalFormula') else None

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
    """Molecular sequence string - set by creation functions that create an associated APiMolecule
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
    labeling = self.labeling
    apiSampleStore = self._project._apiNmrProject.sampleStore
    data2Obj = self._project._data2Obj
    return tuple(data2Obj[x]
                 for y in apiSampleStore.sortedSamples()
                 for x in y.sortedSampleComponents()
                 if x.name == name and x.labeling == labeling)


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
  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> list:
    """get wrappedData (SampleComponent) for all SampleComponent children of parent Sample"""
    componentStore = parent._wrappedData.sampleStore.refSampleComponentStore
    if componentStore is None:
      return []
    else:
      return componentStore.sortedComponents()

# Connections to parents:
Project._childClasses.append(Substance)

def _newSubstance(self:Project, name:str, labeling:str='std', substanceType:str='Molecule',
                  userCode:str=None, smiles:str=None, inChi:str=None, casNumber:str=None,
                  empiricalFormula:str=None, molecularMass:float=None, comment:str=None,
                  synonyms:Sequence[str]=(), atomCount:int=None, bondCount:int=None,
                  ringCount:int=None, hBondDonorCount:int=None, hBondAcceptorCount:int=None,
                  polarSurfaceArea:float=None, logPartitionCoefficient:float=None
                 ) -> Substance:
  """Create new substance WITHOUT attached ApiMolecule (and so not suitable for making chains)
  substanceType defaults to 'Molecule'.
  ADVANCED alternatives are 'Cell', 'Material', and 'Composite'"""

  for ss in (name, labeling):
    if ss and Pid.altCharacter in ss:
      raise ValueError("Character %s not allowed in ccpn.Substance id: %s.%s" %
                       (Pid.altCharacter, name, labeling))

  apiNmrProject = self._wrappedData
  apiComponentStore = apiNmrProject.sampleStore.refSampleComponentStore

  if apiComponentStore.findFirstComponent(name=name, labeling=labeling) is not None:
    raise ValueError("Substance %s.%s already exists" % (name, labeling))

  elif apiNmrProject.root.findFirstMolecule(name=name) is not None:
    raise ValueError("Molecule name %s is already in use for API Molecule")

  else:
    oldSubstance = apiComponentStore.findFirstComponent(name=name)

  params = {
    'name':name, 'labeling':labeling, 'userCode':userCode, 'synonyms':synonyms,
    'details':comment
  }
  apiComponentStore = apiNmrProject.sampleStore.refSampleComponentStore
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
                                                    empiricalFormula=empiricalFormula,
                                                    molecularMass=molecularMass,
                                                    atomCount=atomCount, bondCount=bondCount,
                                                    ringCount=ringCount,
                                                    hBondDonorCount=hBondDonorCount,
                                                    hBondAcceptorCount=hBondAcceptorCount,
                                                    polarSurfaceArea=polarSurfaceArea,
                                                    logPartitionCoefficient=logPartitionCoefficient,
                                                    **params)
  else:
    raise ValueError("Substance type %s not recognised" % substanceType)
  #
  return self._data2Obj[apiResult]

Project.newSubstance = _newSubstance
del _newSubstance


def _createPolymerSubstance(self:Project, sequence:Sequence[str], name:str, labeling:str='std',
              userCode:str=None, smiles:str=None, synonyms:Sequence[str]=(),comment:str=None,
              startNumber:int=1, molType:str=None, isCyclic:bool=False) -> Substance:
  """Make new Substance from sequence of residue codes, using default linking and variants
  NB: For more complex substances, create ccpncore.api.ccp.molecule.Molecule.Molecule
  and use the RefSampleComponentStore.fetchMolComponent to generate the Substance.

  :param Sequence sequence: string of one-letter codes or sequence of str residueNames
  :param str name: name of new substance
  :param str labeling: labeling for new substance
  :param str userCode: user code for new substance (optional)
  :param str smiles: smiles string for new substance (optional)
  :param Sequence[str] synonyms: synonyms for Substance name
  :param str comment: comment for new substance (optional)
  :param int startNumber: number of first residue in sequence
  :param str molType: molType ('protein','DNA', 'RNA'). Required only if sequence is a string.
  :param bool isCyclic: Should substance created be cyclic?

  """

  apiNmrProject = self._wrappedData

  if not sequence:
    raise ValueError("createPolymerSubstance requires non-empty sequence")

  elif apiNmrProject.sampleStore.refSampleComponentStore.findFirstComponent(name=name,
        labeling=labeling) is not None:
    raise ValueError("Substance %s.%s already exists" % (name, labeling))

  elif apiNmrProject.root.findFirstMolecule(name=name) is not None:
    raise ValueError("Molecule name %s is already in use for API Molecule")

  apiMolecule = MoleculeModify.createMolecule(apiNmrProject.root, sequence, molType=molType,
                                              name=name, startNumber=startNumber,
                                              isCyclic=isCyclic)
  apiMolecule.commonNames =synonyms
  apiMolecule.smiles = smiles
  apiMolecule.details=comment

  result = self._data2Obj[apiNmrProject.sampleStore.refSampleComponentStore.fetchMolComponent(
                          apiMolecule, labeling=labeling)]
  result.userCode = userCode
  #
  return result

Project.createPolymerSubstance = _createPolymerSubstance
del _createPolymerSubstance

def _fetchSubstance(self:Project, name:str, labeling:str=None) -> Substance:
  """get or create ccpn.Substance with given name and labeling.
  If labeling is not set it defaults to 'std',
  except that Substances with matching name take priority"""
  apiRefComponentStore= self._apiNmrProject.sampleStore.refSampleComponentStore
  apiResult = apiRefComponentStore.findFirstComponent(name=name, labeling=labeling or 'std')
  if labeling is None and apiResult is None:
    ll = [x for x in apiRefComponentStore.sortedComponents() if x.name == name]
    if ll:
      apiResult = ll[0]

  if apiResult:
    return self._data2Obj[apiResult]
  else:
    return self.newSubstance(name=name, labeling=labeling or 'std')
#
Project.fetchSubstance = _fetchSubstance
del _fetchSubstance


def getter(self:SampleComponent) -> Optional[Substance]:
  apiRefComponentStore = self._parent._apiSample.sampleStore.refSampleComponentStore
  apiComponent = apiRefComponentStore.findFirstComponent(name=self.name, labeling=self.labeling)
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
