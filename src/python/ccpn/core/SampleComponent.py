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

from typing import Tuple
import collections
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Sample import Sample
from ccpn.core.SpectrumHit import SpectrumHit
from ccpnmodel.ccpncore.api.ccp.lims.Sample import SampleComponent as ApiSampleComponent
from ccpnmodel.ccpncore.api.ccp.lims.Sample import Sample as ApiSample
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from ccpn.util import Pid


class SampleComponent(AbstractWrapperObject):
  """Sample Component - material making up sample."""
  
  #: Short class name, for PID.
  shortClassName = 'SC'
  # Attribute it necessary as subclasses must use superclass className
  className = 'SampleComponent'

  _parentClass = Sample

  #: Name of plural link to instances of class
  _pluralLinkName = 'sampleComponents'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiSampleComponent._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiSampleComponent(self) -> ApiSampleComponent:
    """ API sampleComponent matching SampleComponent"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - name.labeling"""
    obj =  self._wrappedData
    return Pid.createId(*(getattr(obj,tag) for tag in ('name', 'labeling')))

  @property
  def name(self) -> str:
    """name of SampleComponent and corresponding substance"""
    return self._wrappedData.name

  @property
  def labeling(self) -> str:
    """labeling descriptor of SampleComponent and corresponding substance (default is 'std')"""
    return self._wrappedData.labeling
    
  @property
  def _parent(self) -> Sample:
    """Sample containing SampleComponent."""
    return  self._project._data2Obj[self._wrappedData.parent]
  
  sample = _parent

  @property
  def role(self) -> str:
    """Role of SampleComponent in solvent, e.g. 'solvent', 'buffer', 'target', ..."""
    return self._wrappedData.role

  @role.setter
  def role(self, value:str):
    self._wrappedData.role = value

  @property
  def concentration(self) -> float:
    """SampleComponent.concentration"""
    return self._wrappedData.concentration

  @concentration.setter
  def concentration(self, value:float):
    self._wrappedData.concentration = value

  @property
  def concentrationError(self) -> float:
    """Estimated Standard error of SampleComponent.concentration"""
    return self._wrappedData.concentrationError

  @concentrationError.setter
  def concentrationError(self, value:float):
    self._wrappedData.concentrationError = value

  @property
  def concentrationUnit(self) -> str:
    """Unit of SampleComponent.concentration, one of: 'g/L', 'M', 'L/L', 'mol/mol', 'g/g' """
    return self._wrappedData.concentrationUnit

  @concentrationUnit.setter
  def concentrationUnit(self, value:str):
    self._wrappedData.concentrationUnit = value

  @property
  def purity(self) -> float:
    """SampleComponent.purity on a scale between 0 and 1"""
    return self._wrappedData.purity

  @purity.setter
  def purity(self, value:float):
    self._wrappedData.purity = value

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def spectrumHits(self) -> Tuple[SpectrumHit, ...]:
    """ccpn.SpectrumHits found for ccpn.SampleComponent"""
    ff = self._project._data2Obj.get
    return tuple(ff(x) for x in self._apiSampleComponent.sortedSpectrumHits())

    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Sample)-> list:
    """get wrappedData (SampleComponent) for all SampleComponent children of parent Sample"""
    return parent._wrappedData.sortedSampleComponents()


def getter(self:SpectrumHit) -> SampleComponent:
  return self._project._data2Obj.get(self._apiSpectrumHit.sampleComponent)
SpectrumHit.sampleComponent = property(getter, None, None,
                              "ccpn.SampleComponent in which ccpn.SpectrumHit is found")
del getter

# Connections to parents:

def _newSampleComponent(self:Sample, name:str, labeling:str=None, role:str=None,
                       concentration:float=None, concentrationError:float=None,
                       concentrationUnit:str=None, purity:float=None, comment:str=None,
                      ) -> SampleComponent:
  """Create new ccpn.SampleComponent within ccpn.Sample

  Automatically creates the corresponding Substance if the name is not already taken
  """

  # Default values for 'new' function, as used for echoing to console
  defaults = collections.OrderedDict(
    (('name',None), ('labeling',None), ('role', None),
     ('concentration',None), ('concentrationError',None), ('concentrationUnit', None),
     ('purity',None), ('comment', None),
     )
  )

  for ss in (name, labeling):
    if ss and Pid.altCharacter in ss:
      raise ValueError("Character %s not allowed in ccpn.SampleComponent id: %s.%s" %
                       (Pid.altCharacter, name, labeling))

  apiSample = self._wrappedData
  self._startFunctionCommandBlock('newSampleComponent', name, values=locals(), defaults=defaults,
                                  parName='newSampleComponent')
  try:
    substance = self._project.fetchSubstance(name=name, labeling=labeling)
    obj = apiSample.newSampleComponent(name=name, labeling=substance.labeling,
                                       concentration=concentration,
                                       concentrationError=concentrationError,
                                       concentrationUnit=concentrationUnit, details=comment,
                                       purity=purity)
  finally:
    self._project._appBase._endCommandBlock()
  return self._project._data2Obj.get(obj)

Sample.newSampleComponent = _newSampleComponent
del _newSampleComponent

# Notifiers - to notify SampleComponent - SpectrumHit link:
className = Nmr.Experiment._metaclass.qualifiedName()
Project._apiNotifiers.append(
  ('_modifiedLink', {'classNames':('SampleComponent','SpectrumHit')}, className, 'setSample'),
)
className = ApiSample._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_modifiedLink', {'classNames':('SampleComponent','SpectrumHit')}, className,
     'addNmrExperiment'),
    ('_modifiedLink', {'classNames':('SampleComponent','SpectrumHit')}, className,
     'removeNmrExperiment'),
    ('_modifiedLink', {'classNames':('SampleComponent','SpectrumHit')}, className,
     'setNmrExperiments'),
  )
)
