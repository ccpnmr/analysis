
from collections.abc import Sequence

from ccpn._AbstractWrapperClass import AbstractWrapperClass
from ccpn._Project import Project
from ccpn._PeakList import PeakList
from ccpncore.api.ccp.nmr.Nmr import Peak as Ccpn_Peak


class Peak(AbstractWrapperClass):
  """Peak."""
  
  #: Short class name, for PID.
  shortClassName = 'PK'

  #: Name of plural link to instances of class
  _pluralLinkName = 'peaks'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnPeak(self) -> Ccpn_Peak:
    """ CCPN peaks matching Peak"""
    return self._wrappedData
    
  @property
  def id(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for Peak"""
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> PeakList:
    """Parent (containing) object."""
    return  self._project._data2Obj[self._wrappedData.peakList]
  
  peakList = _parent
  
  @property
  def height(self) -> float:
    """height of Peak"""
    return self._wrappedData.height
    
  @height.setter
  def height(self, value:float):
    self._wrappedData.height = value

  @property
  def volume(self) -> float:
    """volume of Peak"""
    return self._wrappedData.volume

  @volume.setter
  def volume(self, value:float):
    self._wrappedData.volume = value

  @property
  def figureOfMerit(self) -> float:
    """figureOfMerit of Peak"""
    return self._wrappedData.figOfMerit

  @volume.setter
  def figureOfMerit(self, value:float):
    self._wrappedData.figOfMerit = value

  @property
  def annotation(self) -> str:
    """Peak text annotation"""
    return self._wrappedData.annotation
    
  @annotation.setter
  def annotation(self, value:str):
    self._wrappedData.annotation = value

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def position(self) -> tuple:
    """Peak position in ppm (or other relevant unit)."""
    return tuple(x.value for x in self._wrappedData.sotedPeakDims())

  @position.setter
  def position(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.value = value[ii]

  @property
  def pointPosition(self) -> tuple:
    """Peak position in points."""
    return tuple(x.position for x in self._wrappedData.sotedPeakDims())

  @pointPosition.setter
  def pointPosition(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.position = value[ii]

  @property
  def assignments(self) -> tuple:
    """Peak assignment - a single Assignment per dimension.
    More complex assignments must be viewed using the PeakAssignment"""
    result = []
    for peakDim in self._wrappedData.sortedPeakDims():
      ll = peakDim.sortedPeakDimContribs()
      if len(ll) == 1:
        pdc = ll[0]
        if hasattr(pdc, 'resonance'):
          resonance = pdc.resonance
          if resonance:
            result.append(pdc.resonance.getAssignment())
          else:
            result.append('NO.assignment.NBNB.TBD')
        else:
          result.append('COMPLEX.assignment.NBNB.TBD')
      else:
        result.append('MULTIPLE.assignment.NBNB.TBD')
    #
    return tuple(result)

  @assignments.setter
  def assignments(self, value:Sequence):
    raise NotImplemented("assignments.setter awaits sorting out assignments")
    
  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: PeakList)-> list:
    """get wrappedData (Peaks) for all Peak children of parent PeakList"""
    return parent._wrappedData.sortedPeakLists()

# Connections to parents:
PeakList._childClasses.append(Peak)

def newPeak(parent:PeakList,height:float=None, volume:float=None,
            figureOfMerit:float=1.0, annotation:str=None, comment:str=None,
            position:Sequence=(), pointPosition:Sequence=(),
            assignments:Sequence=()) -> PeakList:
  """Create new child Peak"""
  ccpnPeakList = parent._wrappedData
  peak = ccpnPeakList.newPeak(height=height, volume=volume, figureOfMerit=figureOfMerit,
                              annotation=annotation,details=comment)

  # set peak position
  # NBNB TBD currently unused parameters could be added, and will have to come in here as well
  if position:
    for ii,peakDim in enumerate(peak.sortedPeakDims()):
      peakDim.value = position[ii]
  elif pointPosition:
    for ii,peakDim in enumerate(peak.sortedPeakDims()):
      peakDim.position = pointPosition[ii]

  # Setting assignments
  if assignments:
    for ii,peakDim in enumerate(peak.sortedPeakDims()):
      assignment = assignments[ii]

      # NBNB TBD throw error if dimension does not match one-resonance assignment.

      contribs = peakDim.sortedPeakDimContribs()

      if assignment is None:
        for contrib in contribs:
          contrib.delete()
      else:
        resonance = parent._project.assignment2resonance(assignment)
        if not (len(contribs) == 1 and contribs[0].resonance is resonance):
          for contrib in contribs:
            contrib.delete()
        peakDim.newPeakDimContrib(resonance=resonance)
      # NBNB TBD

PeakList.newPeak = newPeak

# Notifiers:
className = Ccpn_Peak._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Peak}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
