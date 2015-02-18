"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from collections.abc import Sequence
import itertools
import operator

from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
from ccpn._wrapper._PeakList import PeakList
from ccpncore.api.ccp.nmr.Nmr import Peak as ApiPeak

from ccpncore.lib.ccp.nmr.Nmr import Peak as ApiLibPeak

class Peak(AbstractWrapperObject):
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
  def apiPeak(self) -> ApiPeak:
    """ API peaks matching Peak"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
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
  def heightError(self) -> float:
    """height error of Peak"""
    return self._wrappedData.heightError

  @heightError.setter
  def heightError(self, value:float):
    self._wrappedData.heightError = value

  @property
  def volume(self) -> float:
    """volume of Peak"""
    return self._wrappedData.volume

  @volume.setter
  def volume(self, value:float):
    self._wrappedData.volume = value

  @property
  def volumeError(self) -> float:
    """volume error of Peak"""
    return self._wrappedData.volumeError

  @volumeError.setter
  def volumeError(self, value:float):
    self._wrappedData.volumeError = value

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
      peakDim.realValue = None

  @property
  def positionError(self) -> tuple:
    """Peak position error in ppm (or other relevant unit)."""
    return tuple(x.valueError for x in self._wrappedData.sortedPeakDims())

  @positionError.setter
  def positionError(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.valueError = value[ii]

  @property
  def pointPosition(self) -> tuple:
    """Peak position in points."""
    return tuple(x.position for x in self._wrappedData.sortedPeakDims())

  @pointPosition.setter
  def pointPosition(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.position = value[ii]

  @property
  def dimensionNmrAtoms(self) -> tuple:
    """Peak dimension assignment - a list of lists of NmrAtoms for each dimension.
    Assignments as a list of individual combinations is given in 'assignedNmrAtoms'.
    Setting dimensionAssignments implies that all combinations are possible"""
    result = []
    for peakDim in self._wrappedData.sortedPeakDims():

      mainPeakDimContribs = peakDim.mainPeakDimContribs
      # Done this way as a quick way of sorting the values
      mainPeakDimContribs = [x for x in peakDim.sortedPeakDimContribs() if x in mainPeakDimContribs]

      data2Obj = self._project._data2Obj
      dimResults = [data2Obj[pdc.resonance] for pdc in mainPeakDimContribs
                    if hasattr(pdc, 'resonance')]
      result.append(dimResults)
    #
    return tuple(result)

  @dimensionNmrAtoms.setter
  def dimensionNmrAtoms(self, value:Sequence):
    apiPeak = self._wrappedData
    dimResonances = list(value)
    for ii, atoms in enumerate(dimResonances):
      dimValues = tuple(x._wrappedData for x in value[ii])
      dimResonances[ii] = tuple(x for x in dimValues if x is not None)

    ApiLibPeak.setPeakDimAssignments(apiPeak, dimResonances)

  @property
  def assignedNmrAtoms(self) -> tuple:
    """Peak assignment - a list of lists of NmrAtom combinations
    (e.g. a list of triplets for a 3D spectrum). Missing assignments are entered as None
    Assignments per dimension are given in 'dimensionAssignments'."""
    data2Obj = self._project._data2Obj
    apiPeak = self._wrappedData
    peakDims = apiPeak.sortedPeakDims()
    mainPeakDimContribs = [sorted(x.mainPeakDimContribs, key=operator.attrgetter('serial'))
                           for x in peakDims]
    result = []
    for peakContrib in apiPeak.sortedPeakContribs():
      allAtoms = []
      peakDimContribs = peakContrib.peakDimContribs
      for ii,peakDim in enumerate(peakDims):
        atoms = [data2Obj.get(x.resonance) for x in mainPeakDimContribs[ii]
                if x in peakDimContribs and hasattr(x, 'resonance')]
        if not atoms:
          atoms = [None]
        allAtoms.append(atoms)

      result += itertools.product(*allAtoms)
    #
    return tuple(result)


  @assignedNmrAtoms.setter
  def assignedNmrAtoms(self, value:Sequence):
    apiPeak = self._wrappedData
    peakDims = apiPeak.sortedPeakDims()
    dimensionCount = len(peakDims)

    # get resonance, all tuples and per dimension
    resonances = []
    for tt in value:
      ll = dimensionCount*[None]
      resonances.append(ll)
      for ii, atom in enumerate(tt):
        if atom is not None:
          ll[ii] = atom._wrappedData

    # set assignments
    ApiLibPeak.setAssignments(apiPeak, resonances)

  @property
  def dimensionAssignments(self) -> tuple:
    """Peak dimension assignments - a list of lists of NmrAtom.id for each dimension.
    Assignments as a list of individual combinations is given in 'assignments'."""

    result = []
    for ll in self.dimensionNmrAtoms:
      result.append(list(x._id for x in ll))
    #
    return tuple(result)

  @property
  def assignments(self) -> tuple:
    """Peak dimension assignments a list of lists of NmrAtom.id combinations
    (e.g. a list of triplets for a 3D spectrum). Missing assignments are entered as None"""

    result = []
    for ll in self.assignedNmrAtoms:
      result.append(list(x and x._id for x in ll))
    #
    return tuple(result)

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
            dimensionAssignments:Sequence=(), assignments:Sequence=()) -> Peak:
  """Create new child Peak"""
  apiPeakList = parent._wrappedData
  apiPeak = apiPeakList.newPeak(height=height, volume=volume, figOfMerit=figureOfMerit,
                              annotation=annotation,details=comment)

  # set peak position
  # NBNB TBD currently unused parameters could be added, and will have to come in here as well
  if position:
    for ii,peakDim in enumerate(apiPeak.sortedPeakDims()):
      peakDim.value = position[ii]
  elif pointPosition:
    for ii,peakDim in enumerate(apiPeak.sortedPeakDims()):
      peakDim.position = pointPosition[ii]

  # Setting assignments
  if dimensionAssignments:
    dimResonances = list(dimensionAssignments)
    for ii, atoms in enumerate(dimResonances):
      dimValues = tuple(x._wrappedData for x in dimensionAssignments[ii])
      dimResonances[ii] = tuple(x for x in dimValues if x is not None)

    # set dimensionAssignments
    ApiLibPeak.setPeakDimAssignments(apiPeak, dimResonances)

  if assignments:
    peakDims = apiPeak.sortedPeakDims()
    dimensionCount = len(peakDims)

    # get resonance, all tuples and per dimension
    resonances = []
    for tt in assignments:
      ll = dimensionCount*[None]
      resonances.append(ll)
      for ii,atom in enumerate(tt):
        if atom is not None:
          ll[ii] = atom._wrappedData

    # set assignments
    ApiLibPeak.setAssignments(apiPeak, resonances)

  return parent._project._data2Obj.get(apiPeak)


PeakList.newPeak = newPeak

# Notifiers:
className = ApiPeak._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Peak}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
