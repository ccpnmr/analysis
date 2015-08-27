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
from ccpn import Chain
from ccpncore.api.ccp.lims.Sample import SampleComponent as ApiSampleComponent
from ccpncore.util import Pid


class SampleComponent(AbstractWrapperObject):
  """Sample Component - material making up sample."""
  
  #: Short class name, for PID.
  shortClassName = 'SC'
  # Attribute it necessary as subclasses must use superclass className
  className = 'SampleComponent'

  #: Name of plural link to instances of class
  _pluralLinkName = 'sampleComponents'
  
  #: List of child classes.
  _childClasses = []

  # CCPN properties  
  @property
  def apiSampleComponent(self) -> ApiSampleComponent:
    """ API sampleComponent matching SampleComponent"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - name.labeling"""
    obj =  self._wrappedData
    return Pid.IDSEP.join(getattr(obj,tag).translate(Pid.remapSeparators)
                          for tag in ('name', 'labeling'))

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
    return self.swrappedData.concentrationError

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
  def chains(self) -> tuple:
    tt = tuple(self._project.getChain(x) for x in self._wrappedData.chainCodes)
    return tuple(x for x in tt if x is not None)


  @chains.setter
  def chains(self, value):

    wrappedData = self._wrappedData
    chainCodes = [x.shortName for x in value]
    for sampleComponent in wrappedData.sample.sampleComponents:
      if sampleComponent is not wrappedData:
        for chainCode in chainCodes:
          if chainCode in sampleComponent.chainCodes:
            sampleComponent.removeChainCode(chainCode)

    wrappedData.chainCodes = chainCodes

  # @property
  # def chemicalShiftList(self) -> ChemicalShiftList:
  #   """ChemicalShiftList associated with Spectrum."""
  #   return self._project._data2Obj.get(self._wrappedData.shiftList)
  #
  # @chemicalShiftList.setter
  # def chemicalShiftList(self, value):
  #
  #   value = self.getById(value) if isinstance(value, str) else value
  #   apiPeakList = self._wrappedData
  #   if value is None:
  #     apiPeakList.shiftList = None
  #   else:
  #     apiPeakList.shiftList = value._wrappedData
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Sample)-> list:
    """get wrappedData (SampleComponent) for all SampleComponent children of parent Sample"""
    return parent._wrappedData.sortedSampleComponents()

# Connections to parents:
Sample._childClasses.append(SampleComponent)

def newSampleComponent(parent:Sample, name:str, labeling:str, role:str=None,
                       concentration:float=None, concentrationError:float=None,
                       concentrationUnit:str=None, purity:float=None, comment:str=None,
                      ) -> SampleComponent:
  """Create new child SampleComponent"""
  apiSample = parent._wrappedData
  obj = apiSample.newSampleComponent(name=name, labeling=labeling, role=role,
                                     concentration=concentration,
                                     concentrationError=concentrationError,
                                     concentrationUnit=concentrationUnit, details=comment,
                                     purity=purity)
  return parent._project._data2Obj.get(obj)

Sample.newSampleComponent = newSampleComponent

# Notifiers:
className = ApiSampleComponent._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':SampleComponent}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
