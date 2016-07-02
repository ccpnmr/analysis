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
import itertools
import collections
import operator

from ccpn.util import Undo
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.SpectrumReference import SpectrumReference
from ccpn.core.PeakList import PeakList
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
from typing import Optional, Tuple, Union, Sequence

class Peak(AbstractWrapperObject):
  """Peak. Includes per-dimension values and (multiple) assignments.
  Measurements that require more htn one NmrAtom for an individual assignment
  (such as  splittings, J-couplings, MQ dimensions, reduced-dimensionality
  experiments etc.) are not supported (yet). Assignments can be viewed and set
  either as an assignment list for each dimension (dimensionNmrAtoms) or as a
  list of all possible assignment combinations (assignedNmrAtoms)"""
  
  #: Short class name, for PID.
  shortClassName = 'PK'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Peak'

  _parentClass = PeakList

  #: Name of plural link to instances of class
  _pluralLinkName = 'peaks'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = Nmr.Peak._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiPeak(self) -> Nmr.Peak:
    """ API peaks matching Peak"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of Peak, used in Pid and to identify the Peak. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> PeakList:
    """PeakList containing Peak."""
    return  self._project._data2Obj[self._wrappedData.peakList]
  
  peakList = _parent
  
  @property
  def height(self) -> Optional[float]:
    """height of Peak"""
    return self._wrappedData.height
    
  @height.setter
  def height(self, value:float):
    self._wrappedData.height = value

  @property
  def heightError(self) -> Optional[float]:
    """height error of Peak"""
    return self._wrappedData.heightError

  @heightError.setter
  def heightError(self, value:float):
    self._wrappedData.heightError = value

  @property
  def volume(self) -> Optional[float]:
    """volume of Peak"""
    return self._wrappedData.volume

  @volume.setter
  def volume(self, value:float):
    self._wrappedData.volume = value

  @property
  def volumeError(self) -> Optional[float]:
    """volume error of Peak"""
    return self._wrappedData.volumeError

  @volumeError.setter
  def volumeError(self, value:float):
    self._wrappedData.volumeError = value

  @property
  def figureOfMerit(self) -> Optional[float]:
    """figureOfMerit of Peak, between 0.0 and 1.0 inclusive."""
    return self._wrappedData.figOfMerit

  @figureOfMerit.setter
  def figureOfMerit(self, value:float):
    self._wrappedData.figOfMerit = value

  @property
  def annotation(self) -> Optional[str]:
    """Peak text annotation"""
    return self._wrappedData.annotation
    
  @annotation.setter
  def annotation(self, value:str):
    self._wrappedData.annotation = value

  @property
  def comment(self) -> Optional[str]:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def axisCodes(self) -> Tuple[str, ...]:
    """Spectrum axis codes in dimension order matching position."""
    return self.peakList.spectrum.axisCodes

  @property
  def position(self) -> Tuple[float, ...]:
    """Peak position in ppm (or other relevant unit) in dimension order."""
    return tuple(x.value for x in self._wrappedData.sortedPeakDims())

  @position.setter
  def position(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.value = value[ii]
      peakDim.realValue = None

  @property
  def positionError(self) -> Tuple[Optional[float], ...]:
    """Peak position error in ppm (or other relevant unit)."""
    return tuple(x.valueError for x in self._wrappedData.sortedPeakDims())

  @positionError.setter
  def positionError(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.valueError = value[ii]

  @property
  def pointPosition(self) -> Tuple[float, ...]:
    """Peak position in points."""
    return tuple(x.position for x in self._wrappedData.sortedPeakDims())

  @pointPosition.setter
  def pointPosition(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.position = value[ii]

  @property
  def boxWidths(self) -> Tuple[Optional[float], ...]:
    """The full width of the peak footprint in points for eqach dimension,
    i.e. the width of the area that should be considered for integration, fitting, etc. ."""
    return tuple(x.boxWidth for x in self._wrappedData.sortedPeakDims())

  @boxWidths.setter
  def boxWidths(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.boxWidth = value[ii]

  @property
  def lineWidths(self) -> Tuple[Optional[float], ...]:
    """Full-width-half-height of peak/multiplet for each dimension, in Hz. """
    return tuple(x.lineWidth for x in self._wrappedData.sortedPeakDims())

  @lineWidths.setter
  def lineWidths(self,value:Sequence):
    for ii,peakDim in enumerate(self._wrappedData.sortedPeakDims()):
      peakDim.lineWidth = value[ii]

  @property
  def dimensionNmrAtoms(self) -> Tuple[Tuple['NmrAtom', ...], ...]:
    """Peak dimension assignment - a list of lists of NmrAtoms for each dimension.
    One ofg two alternative views on the Peak assignment.
    Assignments as a list of individual combinations is given in 'assignedNmrAtoms'.
    Setting dimensionAssignments implies that all combinations are possible

    Example:
      ((<NA:A.127.LEU.HA>, <NA:A.127.LEU.HBX>, <NA:A.127.LEU.HBY>,<NA:A.127.LEU.HG>),
       (<NA:A.127.LEU.CA>, <NA:A.127.LEU.CB>)
       )"""
    result = []
    for peakDim in self._wrappedData.sortedPeakDims():

      mainPeakDimContribs = peakDim.mainPeakDimContribs
      # Done this way as a quick way of sorting the values
      mainPeakDimContribs = [x for x in peakDim.sortedPeakDimContribs() if x in mainPeakDimContribs]

      data2Obj = self._project._data2Obj
      dimResults = [data2Obj[pdc.resonance] for pdc in mainPeakDimContribs
                    if hasattr(pdc, 'resonance')]
      result.append(sorted(dimResults))
    #
    return tuple(result)

  @dimensionNmrAtoms.setter
  def dimensionNmrAtoms(self, value:Sequence):

    apiPeak = self._wrappedData
    dimResonances = []
    for atoms in value:
      if atoms is None:
        dimResonances.append(None)

      else:

        if isinstance(atoms, str):
          raise ValueError("dimensionNmrAtoms cannot be set to a sequence of strings")
        if not isinstance(atoms, Sequence):
          raise ValueError("dimensionNmrAtoms must be set to a sequence of list/tuples")

        atoms = tuple(self.getByPid(x) if isinstance(x, str) else x for x in atoms)
        dimResonances.append(tuple(x._wrappedData for x in atoms if x is not None))

    apiPeak.assignByDimensions(dimResonances)

  @property
  def assignedNmrAtoms(self) -> Tuple[Tuple[Optional['NmrAtom'], ...], ...]:
    """Peak assignment - a tuple of tuples of NmrAtom combinations.
    (e.g. a tuple of triplets for a 3D spectrum).
    One of two alternative views on the Peak assignment.
    Missing assignments are entered as None.
    Assignments for each dimension are given in 'dimensionNmrAtoms'.

    Example:
      ((<NA:A.127.LEU.HA>, <NA:A.127.LEU.CA>),
      (<NA:A.127.LEU.HBX>, <NA:A.127.LEU.CB>),
      (<NA:A.127.LEU.HBY>, <NA:A.127.LEU.CB>),
      (<NA:A.127.LEU.HG>, None),)

    """
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
        nmrAtoms = [data2Obj.get(x.resonance) for x in mainPeakDimContribs[ii]
                if x in peakDimContribs and hasattr(x, 'resonance')]
        if not nmrAtoms:
          nmrAtoms = [None]
        allAtoms.append(nmrAtoms)

      # NB this gives a lit of tuples
      result += itertools.product(*allAtoms)
    #
    return tuple(sorted(result))


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
        atom = self.getByPid(atom) if isinstance(atom, str) else atom
        if atom is not None:
          ll[ii] = atom._wrappedData

    # set assignments
    apiPeak.assignByContributions(resonances)

  def addAssignment(self, value:Sequence[Union[str, 'NmrAtom']]):
    """Add a peak assignment - a list of one NmrAtom or Pid for each dimension"""

    if len(value) != self._wrappedData.peakList.numDim:
      raise ValueError("Length of assignment value %s does not match peak dimensionality %s "
      % (value, self._wrappedData.peakList.numDim))

    # Convert to tuple and check for non-existing pids
    ll = []
    for val in value:
      if isinstance(val, str):
        vv = self.getByPid(val)
        if vv is None:
          raise ValueError("No NmrAtom matching string pid %s" % val)
        else:
          ll .append(vv)
      else:
        ll .append(val)
    value = tuple(value)

    assignedNmrAtoms = list(self.assignedNmrAtoms)
    if value in assignedNmrAtoms:
      self._project._logger.warning("Attempt to add already existing Peak Assignment: %s - ignored"
                                    % value)
    else:
      assignedNmrAtoms.append(value)
      self.assignedNmrAtoms = assignedNmrAtoms

  def assignDimension(self, axisCode:str, value:Union[Union[str,'NmrAtom'],
                                                            Sequence[Union[str,'NmrAtom']]]):
    """Assign dimension with axisCode to value (NmrAtom, or Pid or sequence of either, or None)
    """

    axisCodes = self._parent._parent.axisCodes
    try:
      index = axisCodes.index(axisCode)
    except ValueError:
      raise ValueError("axisCode %s not recognised" % axisCode)

    if value is None:
      value = []
    elif isinstance(value, str):
      value = [self.getByPid(value)]
    elif isinstance(value, Sequence):
      value = [(self.getByPid(x) if isinstance(x, str) else x) for x in value]
    else:
      value = [value]
    dimensionNmrAtoms = list(self.dimensionNmrAtoms)
    dimensionNmrAtoms[index] = value
    self.dimensionNmrAtoms = dimensionNmrAtoms

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: PeakList)-> Tuple[Nmr.Peak, ...]:
    """get wrappedData (Peaks) for all Peak children of parent PeakList"""
    return parent._wrappedData.sortedPeaks()

# Connections to parents:

def _newPeak(self:PeakList,height:Optional[float]=None, volume:Optional[float]=None,
             heightError:Optional[float]=None, volumeError:Optional[float]=None,
            figureOfMerit:float=1.0, annotation:str=None, comment:str=None,
            position:Sequence[float]=(), pointPosition:Sequence[float]=()) -> Peak:
  """Create new ccpn.Peak within ccpn.peakList

  NB you must create the peak before you can assign it. The assignment attributes are:

  - assignedNmrAtoms - A list of all (e.g.) assignment triplets for a 3D spectrum

  - dimensionNmrAtoms - A list of list of assignments, one for each dimension"""

  defaults = collections.OrderedDict(
    (('height', None), ('volume', None), ('heightError', None), ('volumeError', None),
     ('figureOfMerit', 1.0), ('annotation', None), ('comment', None), ('position', ()),
     ('pointPosition', ())
    )
  )

  undo = self._project._undo
  self._startFunctionCommandBlock('newPeak', values=locals(), defaults=defaults,
                                  parName='newPeak')
  self._project.blankNotification()
  undo.increaseBlocking()
  try:
    apiPeakList = self._apiPeakList
    apiPeak = apiPeakList.newPeak(height=height, volume=volume,
                                  heightError=heightError, volumeError=volumeError,
                                  figOfMerit=figureOfMerit, annotation=annotation, details=comment)

    # set peak position
    # NBNB TBD currently unused parameters could be added, and will have to come in here as well
    apiPeakDims = apiPeak.sortedPeakDims()
    if position:
      for ii,peakDim in enumerate(apiPeakDims):
        peakDim.value = position[ii]
    elif pointPosition:
      for ii,peakDim in enumerate(apiPeakDims):
        peakDim.position = pointPosition[ii]

  finally:
    self._project._appBase._endCommandBlock()
    self._project.unblankNotification()
    undo.decreaseBlocking()

  apiObjectsCreated = [apiPeak]
  apiObjectsCreated.extend(apiPeakDims)
  undo.newItem(Undo._deleteAllApiObjects, apiPeak.root._unDelete,
               undoArgs=(apiObjectsCreated,),
               redoArgs=(apiObjectsCreated,  (apiPeak.topObject,)))

  result = self._project._data2Obj.get(apiPeak)

  # DO creation notifications
  result._finaliseAction('create')

  return result

PeakList.newPeak = _newPeak
del _newPeak

# Additional Notifiers:
#
# NB These API notifiers will be called for API peaks - which match both Peaks and Integrals
className = Nmr.PeakDim._metaclass.qualifiedName()
Project._apiNotifiers.append(
  ('_notifyRelatedApiObject', {'pathToObject':'peak', 'action':'change'}, className, ''),
)
for clazz in Nmr.AbstractPeakDimContrib._metaclass.getNonAbstractSubtypes():
  className = clazz.qualifiedName()
  # NB - relies on PeakDimContrib.peakDim.peak still working for deleted peak. Should work.
  Project._apiNotifiers.extend( (
      ('_notifyRelatedApiObject', {'pathToObject':'peakDim.peak',  'action':'change'},
       className, 'postInit'),
      ('_notifyRelatedApiObject', {'pathToObject':'peakDim.peak',  'action':'change'},
       className, 'delete'),
    )
  )

# Notify Peaks change when SpectrumReference changes
# (That means DataDimRef referencing information)
SpectrumReference._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
                          {'pathToObject':'spectrum.peaks', 'action':'change'})