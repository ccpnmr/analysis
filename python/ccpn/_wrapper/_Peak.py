from collections.abc import Sequence

from ccpn._wrapper._AbstractWrapperClass import AbstractWrapperClass
from ccpn._wrapper._Project import Project
from ccpn._wrapper._PeakList import PeakList
from ccpncore.api.ccp.nmr.Nmr import Peak as Ccpn_Peak


class Peak(AbstractWrapperClass):
  """Peak. Includes values for per-dimension values and for assignments.
  Assignments are complete for normal shift dimensions, but only the main referencing is used
  in each dimension. For assigning splittings, J-couplings, MQ dimensions, reduced-dimensionality
  experiments etc. you must use the PeakAssignment object (NBNB still to be written).
  Assignments are per dimension, and for now assume that each assignment can be combined with
  all assignments for other dimensions """
  
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

  @figureOfMerit.setter
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
    return tuple(x.value for x in self._wrappedData.sortedPeakDims())

  @position.setter
  def position(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.value = value[ii]

  @property
  def pointPosition(self) -> tuple:
    """Peak position in points."""
    return tuple(x.position for x in self._wrappedData.sortedPeakDims())

  @pointPosition.setter
  def pointPosition(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.position = value[ii]

  @property
  def assignments(self) -> tuple:
    """Peak assignment - a list of possible single Assignment for each dimension.
    It is assumed (for now) that all combinations are possible"""
    result = []
    for peakDim in self._wrappedData.sortedPeakDims():

      mainPeakDimContribs = peakDim.mainPeakDimContribs
      # Done this way as a quick way of sorting the values
      mainPeakDimContribs = [x for x in peakDim.sortedPeakDimContribs() if x in mainPeakDimContribs]
      dimResults = []
      result.append(dimResults)
      func = self._project._resonance2Assignment
      for pdc in mainPeakDimContribs:
        if hasattr(pdc, 'resonance'):
          resonance = pdc.resonance
          if resonance:
            result.append(func(resonance))
        else:
          result.append('COMPLEX.assignment.NBNB.TBD')
    #
    return tuple(result)

  @assignments.setter
  def assignments(self, value:Sequence):
    ccpnPeak = self._wrappedData
    _setPeakAssignments(ccpnPeak, self._project, value)

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: PeakList)-> list:
    """get wrappedData (Peaks) for all Peak children of parent PeakList"""
    return parent._wrappedData.sortedPeaks()

# Connections to parents:
PeakList._childClasses.append(Peak)

def newPeak(parent:PeakList,height:float=None, volume:float=None,
            figureOfMerit:float=1.0, annotation:str=None, comment:str=None,
            position:Sequence=(), pointPosition:Sequence=(),
            assignments:Sequence=()) -> PeakList:
  """Create new child Peak"""
  ccpnPeakList = parent._wrappedData
  ccpnPeak = ccpnPeakList.newPeak(height=height, volume=volume, figureOfMerit=figureOfMerit,
                              annotation=annotation,details=comment)

  # set peak position
  # NBNB TBD currently unused parameters could be added, and will have to come in here as well
  if position:
    for ii,peakDim in enumerate(ccpnPeak.sortedPeakDims()):
      peakDim.value = position[ii]
  elif pointPosition:
    for ii,peakDim in enumerate(ccpnPeak.sortedPeakDims()):
      peakDim.position = pointPosition[ii]

  # Setting assignments
  if assignments:
    _setPeakAssignments(ccpnPeak, parent._project, assignments)

PeakList.newPeak = newPeak

# Notifiers:
className = Ccpn_Peak._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Peak}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)

def _setPeakAssignments(ccpnPeak, wrapperProject, value):
  """Set assignments on peak
  Separate utility function to avoid duplicating code in assignments setter and newPeak function
  """
  numDim =  ccpnPeak.peakList.dataSource.numDim
  if len(value) != numDim:
    raise ValueError("Assignment length does not match peak list dimensionality %s: %s"
                      % (numDim, value))

  for ii, val in enumerate(value):
    if len(set(val)) != len(val):
      raise ValueError("Assignments contain duplicates in dimension %s: %s" % (ii+1, value))

  func = wrapperProject.assignment2Resonance
  for ii,peakDim in enumerate(ccpnPeak.sortedPeakDims()):
    dimAssignments = value[ii]
    resonances = [func(x) for x in dimAssignments]
    mainPeakDimContribs = peakDim.mainPeakDimContribs
    for pdc in mainPeakDimContribs:
      # Remove unwanted contribs and purge pre-existing resonances from input.
      if hasattr(pdc, 'resonance'):
        resonance = pdc.resonance
        if resonance in resonances:
          resonances.remove(resonance)
        else:
          pdc.delete()

    for resonance in resonances:
      # Add new contrib for missing resonances
      peakDim.newPeakDimContrib(resonance=resonance)