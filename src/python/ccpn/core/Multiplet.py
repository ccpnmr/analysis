"""
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import itertools
import collections
import operator

from ccpn.util import Undo
from ccpn.util import Common as commonUtil
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.SpectrumReference import SpectrumReference
from ccpn.core.Peak import Peak
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
#from ccpnmodel.ccpncore.lib import Util as modelUtil
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakCluster as apiPeakCluster
# from ccpn.core.MultipletList import MultipletList
from typing import Optional, Tuple, Union, Sequence


class Multiplet(AbstractWrapperObject):
  """Multiplet object, holding position, intensity, and assignment information

  Measurements that require more than one NmrAtom for an individual assignment
  (such as  splittings, J-couplings, MQ dimensions, reduced-dimensionality
  experiments etc.) are not supported (yet). Assignments can be viewed and set
  either as a list of assignments for each dimension (dimensionNmrAtoms) or as a
  list of all possible assignment combinations (assignedNmrAtoms)"""
  
  #: Short class name, for PID.
  shortClassName = 'MT'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Multiplet'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'multiplets'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = apiPeakCluster._metaclass.qualifiedName()

  _linkedMultiplet = None

  # CCPN properties  
  @property
  def _apiMultiplet(self) -> apiPeakCluster:
    """ API multiplets matching Multiplet"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of Multiplet, used in Pid and to identify the Multiplet. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> Optional[Spectrum]:
    """MultipletList containing Multiplet."""
    #TODO:ED trap that the Multiplet is no longer attached due to deletion
    return  self._project._data2Obj[self._wrappedData.nmrProject]

  spectrum = _parent
  
  @property
  def height(self) -> Optional[float]:
    """height of Multiplet"""
    return self._wrappedData.height
    
  @height.setter
  def height(self, value:float):
    self._wrappedData.height = value

  @property
  def heightError(self) -> Optional[float]:
    """height error of Multiplet"""
    return self._wrappedData.heightError

  @heightError.setter
  def heightError(self, value:float):
    self._wrappedData.heightError = value

  @property
  def volume(self) -> Optional[float]:
    """volume of Multiplet"""
    return self._wrappedData.volume

  @volume.setter
  def volume(self, value:float):
    self._wrappedData.volume = value

  @property
  def volumeError(self) -> Optional[float]:
    """volume error of Multiplet"""
    return self._wrappedData.volumeError

  @volumeError.setter
  def volumeError(self, value:float):
    self._wrappedData.volumeError = value

  @property
  def figureOfMerit(self) -> Optional[float]:
    """figureOfMerit of Multiplet, between 0.0 and 1.0 inclusive."""
    return self._wrappedData.figOfMerit

  @figureOfMerit.setter
  def figureOfMerit(self, value:float):
    self._wrappedData.figOfMerit = value

  @property
  def annotation(self) -> Optional[str]:
    """Multiplet text annotation"""
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
    return self.multipletList.spectrum.axisCodes

  @property
  def position(self) -> Tuple[float, ...]:
    """Multiplet position in ppm (or other relevant unit) in dimension order."""
    return tuple(x.value for x in self._wrappedData.sortedMultipletDims())

  @position.setter
  def position(self,value:Sequence):
    for ii,multipletDim in enumerate(self._wrappedData.sortedMultipletDims()):
      multipletDim.value = value[ii]
      multipletDim.realValue = None

  @property
  def positionError(self) -> Tuple[Optional[float], ...]:
    """Multiplet position error in ppm (or other relevant unit)."""
    return tuple(x.valueError for x in self._wrappedData.sortedMultipletDims())

  @positionError.setter
  def positionError(self,value:Sequence):
    for ii,multipletDim in enumerate(self._wrappedData.sortedMultipletDims()):
      multipletDim.valueError = value[ii]

  @property
  def pointPosition(self) -> Tuple[float, ...]:
    """Multiplet position in points."""
    return tuple(x.position for x in self._wrappedData.sortedMultipletDims())

  @pointPosition.setter
  def pointPosition(self,value:Sequence):
    for ii,multipletDim in enumerate(self._wrappedData.sortedMultipletDims()):
      multipletDim.position = value[ii]

  @property
  def boxWidths(self) -> Tuple[Optional[float], ...]:
    """The full width of the multiplet footprint in points for each dimension,
    i.e. the width of the area that should be considered for integration, fitting, etc. ."""
    return tuple(x.boxWidth for x in self._wrappedData.sortedMultipletDims())

  @boxWidths.setter
  def boxWidths(self,value:Sequence):
    for ii,multipletDim in enumerate(self._wrappedData.sortedMultipletDims()):
      multipletDim.boxWidth = value[ii]

  @property
  def lineWidths(self) -> Tuple[Optional[float], ...]:
    """Full-width-half-height of multiplet/multiplet for each dimension, in Hz. """
    return tuple(x.lineWidth for x in self._wrappedData.sortedMultipletDims())

  @lineWidths.setter
  def lineWidths(self,value:Sequence):
    for ii,multipletDim in enumerate(self._wrappedData.sortedMultipletDims()):
      multipletDim.lineWidth = value[ii]

  # @property
  # def dimensionNmrAtoms(self) -> Tuple[Tuple['NmrAtom', ...], ...]:
  #   """Multiplet dimension assignment - a tuple of tuples with the assigned NmrAtoms for each dimension.
  #   One of two alternative views on the Multiplet assignment.
  #
  #   Example, for a 13C HSQC:
  #     ((<NA:A.127.LEU.HA>, <NA:A.127.LEU.HBX>, <NA:A.127.LEU.HBY>, <NA:A.127.LEU.HG>,
  #
  #      (<NA:A.127.LEU.CA>, <NA:A.127.LEU.CB>)
  #      )
  #
  #   Assignments as a list of individual combinations is given in 'assignedNmrAtoms'.
  #   Note that by setting dimensionAssignments you tel the program that all combinations are
  #   possible - in the example that all four protons could be bound to either of the carbons
  #
  #   To (re)set the assignment for a single dimension, use the Multiplet.assignDimension method. """
  #   result = []
  #   for multipletDim in self._wrappedData.sortedMultipletDims():
  #
  #     mainMultipletDimContribs = multipletDim.mainMultipletDimContribs
  #     # Done this way as a quick way of sorting the values
  #     mainMultipletDimContribs = [x for x in multipletDim.sortedMultipletDimContribs() if x in mainMultipletDimContribs]
  #
  #     data2Obj = self._project._data2Obj
  #     dimResults = [data2Obj[pdc.resonance] for pdc in mainMultipletDimContribs
  #                   if hasattr(pdc, 'resonance')]
  #     result.append(tuple(sorted(dimResults)))
  #   #
  #   return tuple(result)
  #
  # @dimensionNmrAtoms.setter
  # def dimensionNmrAtoms(self, value:Sequence):
  #
  #   isotopeCodes = self.multipletList.spectrum.isotopeCodes
  #
  #   apiMultiplet = self._wrappedData
  #   dimResonances = []
  #   for ii,atoms in enumerate(value):
  #     if atoms is None:
  #       dimResonances.append(None)
  #
  #     else:
  #
  #       isotopeCode = isotopeCodes[ii]
  #
  #       if isinstance(atoms, str):
  #         raise ValueError("dimensionNmrAtoms cannot be set to a sequence of strings")
  #       if not isinstance(atoms, Sequence):
  #         raise ValueError("dimensionNmrAtoms must be set to a sequence of list/tuples")
  #
  #       atoms = tuple(self.getByPid(x) if isinstance(x, str) else x for x in atoms)
  #       resonances = tuple(x._wrappedData for x in atoms if x is not None)
  #       if isotopeCode and isotopeCode != '?':
  #         # check for isotope match
  #         if any(x.isotopeCode not in (isotopeCode, '?') for x in resonances):
  #           raise ValueError("NmrAtom assigned to dimension %s must have isotope %s or '?'"
  #                            % (ii+1, isotopeCode))
  #       dimResonances.append(resonances)
  #
  #   apiMultiplet.assignByDimensions(dimResonances)
  #
  # @property
  # def assignedNmrAtoms(self) -> Tuple[Tuple[Optional['NmrAtom'], ...], ...]:
  #   """Multiplet assignment - a tuple of tuples of NmrAtom combinations.
  #   (e.g. a tuple of triplets for a 3D spectrum).
  #   One of two alternative views on the Multiplet assignment.
  #   Missing assignments are entered as None.
  #
  #   Example, for 13H HSQC::
  #     ((<NA:A.127.LEU.HA>, <NA:A.127.LEU.CA>),
  #
  #     (<NA:A.127.LEU.HBX>, <NA:A.127.LEU.CB>),
  #
  #     (<NA:A.127.LEU.HBY>, <NA:A.127.LEU.CB>),
  #
  #     (<NA:A.127.LEU.HG>, None),)
  #
  #   To add a single assignment tuple, use the Multiplet.addAssignment method
  #
  #   See also dimensionNmrAtoms, which gives assignments per dimension.
  #
  #   """
  #   data2Obj = self._project._data2Obj
  #   apiMultiplet = self._wrappedData
  #   multipletDims = apiMultiplet.sortedMultipletDims()
  #   mainMultipletDimContribs = [sorted(x.mainMultipletDimContribs, key=operator.attrgetter('serial'))
  #                          for x in multipletDims]
  #   result = []
  #   for multipletContrib in apiMultiplet.sortedMultipletContribs():
  #     allAtoms = []
  #     multipletDimContribs = multipletContrib.multipletDimContribs
  #     for ii,multipletDim in enumerate(multipletDims):
  #       nmrAtoms = [data2Obj.get(x.resonance) for x in mainMultipletDimContribs[ii]
  #               if x in multipletDimContribs and hasattr(x, 'resonance')]
  #       if not nmrAtoms:
  #         nmrAtoms = [None]
  #       allAtoms.append(nmrAtoms)
  #
  #     # NB this gives a list of tuples
  #     # Remove all-None tuples
  #     result.extend(tt for tt in itertools.product(*allAtoms)
  #                   if any(x is not None for x in tt))
  #     # result += itertools.product(*allAtoms)
  #   #
  #   return tuple(sorted(result))
  #
  #
  # @assignedNmrAtoms.setter
  # def assignedNmrAtoms(self, value:Sequence):
  #
  #   isotopeCodes = tuple(None if x == '?' else x for x in self.multipletList.spectrum.isotopeCodes)
  #
  #   apiMultiplet = self._wrappedData
  #   multipletDims = apiMultiplet.sortedMultipletDims()
  #   dimensionCount = len(multipletDims)
  #
  #   # get resonance, all tuples and per dimension
  #   resonances = []
  #   for tt in value:
  #     ll = dimensionCount*[None]
  #     resonances.append(ll)
  #     for ii, atom in enumerate(tt):
  #       atom = self.getByPid(atom) if isinstance(atom, str) else atom
  #       if atom is not None:
  #         resonance = atom._wrappedData
  #         if isotopeCodes[ii] and resonance.isotopeCode not in (isotopeCodes[ii], '?'):
  #           raise ValueError("NmrAtom %s, isotope %s, assigned to dimension %s must have isotope %s or '?'"
  #                            % (atom, resonance.isotopeCode, ii+1, isotopeCodes[ii]))
  #
  #         ll[ii] = resonance
  #
  #   # set assignments
  #   apiMultiplet.assignByContributions(resonances)
  #
  # def addAssignment(self, value:Sequence[Union[str, 'NmrAtom']]):
  #   """Add a multiplet assignment - a list of one NmrAtom or Pid for each dimension"""
  #
  #   if len(value) != self.multipletList.spectrum.dimensionCount:
  #     raise ValueError("Length of assignment value %s does not match multiplet dimensionality %s "
  #     % (value, self.multipletList.spectrum.dimensionCount))
  #
  #   # Convert to tuple and check for non-existing pids
  #   ll = []
  #   for val in value:
  #     if isinstance(val, str):
  #       vv = self.getByPid(val)
  #       if vv is None:
  #         raise ValueError("No NmrAtom matching string pid %s" % val)
  #       else:
  #         ll .append(vv)
  #     else:
  #       ll .append(val)
  #   value = tuple(value)
  #
  #   assignedNmrAtoms = list(self.assignedNmrAtoms)
  #   if value in assignedNmrAtoms:
  #     self._project._logger.warning("Attempt to add already existing Multiplet Assignment: %s - ignored"
  #                                   % value)
  #   else:
  #     assignedNmrAtoms.append(value)
  #     self.assignedNmrAtoms = assignedNmrAtoms
  #
  # def assignDimension(self, axisCode:str, value:Union[Union[str,'NmrAtom'],
  #                                                     Sequence[Union[str,'NmrAtom']]]=None):
  #   """Assign dimension with axisCode to value (NmrAtom, or Pid or sequence of either, or None)
  #   """
  #
  #   axisCodes = self._parent._parent.axisCodes
  #   try:
  #     index = axisCodes.index(axisCode)
  #   except ValueError:
  #     raise ValueError("axisCode %s not recognised" % axisCode)
  #
  #   if value is None:
  #     value = []
  #   elif isinstance(value, str):
  #     value = [self.getByPid(value)]
  #   elif isinstance(value, Sequence):
  #     value = [(self.getByPid(x) if isinstance(x, str) else x) for x in value]
  #   else:
  #     value = [value]
  #   dimensionNmrAtoms = list(self.dimensionNmrAtoms)
  #   dimensionNmrAtoms[index] = value
  #   self.dimensionNmrAtoms = dimensionNmrAtoms
  #
  # # Utility functions
  #
  # def isPartlyAssigned(self):
  #   """Whether multiplet is partly assigned"""
  #
  #   return any(self.dimensionNmrAtoms)
  #
  # def isFullyAssigned(self):
  #   """Whether multiplet is fully assigned"""
  #
  #   return all(self.dimensionNmrAtoms)
  #
  # def reorderValues(self, values, newAxisCodeOrder):
  #   """Reorder values in spectrum dimension order to newAxisCodeOrder
  #   by matching newAxisCodeOrder to spectrum axis code order"""
  #   return commonUtil.reorder(values, self._parent._parent.axisCodes, newAxisCodeOrder)
  #
  # def getInAxisOrder(self, attributeName:str, axisCodes:Sequence[str]=None):
  #   """Get attributeName in order defined by axisCodes :
  #      (default order if None)
  #   """
  #   if not hasattr(self, attributeName):
  #     raise AttributeError('Multiplet object does not have attribute "%s"' % attributeName)
  #
  #   values = getattr(self, attributeName)
  #   if axisCodes is None:
  #     return values
  #   else:
  #     # change to order defined by axisCodes
  #     return self.reorderValues(values, axisCodes)
  #
  # def setInAxisOrder(self, attributeName:str, values:Sequence, axisCodes:Sequence[str]=None):
  #   """Set attributeName from values in order defined by axisCodes
  #      (default order if None)
  #   """
  #   if not hasattr(self, attributeName):
  #     raise AttributeError('Multiplet object does not have attribute "%s"' % attributeName)
  #
  #   if axisCodes is not None:
  #     # change values to the order appropriate for spectrum
  #     values = self.reorderValues(values, axisCodes)
  #   setattr(self, attributeName, values)
  #
  # def snapToExtremum(self, halfBoxSearchWidth:int=2, halfBoxFitWidth:int=2):
  #   apiPeakCluster.snapToExtremum(self._apiMultiplet, halfBoxSearchWidth=halfBoxSearchWidth, halfBoxFitWidth=halfBoxFitWidth)
  #
  # def fitPositionHeightLineWidths(self):
  #
  #   apiPeakCluster.fitPositionHeightLineWidths(self._apiMultiplet)

  # Implementation functions

  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> Tuple[apiPeakCluster, ...]:
    """get wrappedData (Multiplets) for all Multiplet children of parent MultipletList"""
    return parent._wrappedData.sortedPeakClusters()

# Connections to parents:
def _newMultiplet(self:Project, peaks:['Peak']=None, serial:int=None) -> Multiplet:
  """Create new Multiplet within multipletList"""

  defaults = collections.OrderedDict(
    (('peaks', None), ('serial', None),
    )
  )

  undo = self._project._undo
  self._startCommandEchoBlock('newMultiplet', values=locals(), defaults=defaults,
                              parName='newMultiplet')
  # self._project.blankNotification()
  # undo.increaseBlocking()
  try:
    apiParent = self._wrappedData   #
    if peaks:
      apiMultiplet = apiParent.newPeakCluster(clusterType='multiplet',
                                              peaks=[p._wrappedData for p in peaks])
    else:
      apiMultiplet = apiParent.newPeakCluster(clusterType='multiplet')
    
    result = self._project._data2Obj.get(apiMultiplet)

    # if serial is not None:
    #   try:
    #     result.resetSerial(serial)
    #     # modelUtil.resetSerial(apiMultiplet, serial, 'multiplets')
    #   except ValueError:
    #     self.project._logger.warning("Could not reset serial of %s to %s - keeping original value"
    #                                  %(result, serial))
    # set multiplet position
    # NBNB TBD currently unused parameters could be added, and will have to come in here as well
    # apiMultipletDims = apiMultiplet.sortedMultipletDims()
    # if position:
    #   for ii,multipletDim in enumerate(apiMultipletDims):
    #     multipletDim.value = position[ii]
    # elif pointPosition:
    #   for ii,multipletDim in enumerate(apiMultipletDims):
    #     multipletDim.position = pointPosition[ii]
    # if positionError:
    #   for ii,multipletDim in enumerate(apiMultipletDims):
    #     multipletDim.valueError = positionError[ii]
    # if boxWidths:
    #   for ii,multipletDim in enumerate(apiMultipletDims):
    #     multipletDim.boxWidth = boxWidths[ii]
    # if lineWidths:
    #   for ii,multipletDim in enumerate(apiMultipletDims):
    #     multipletDim.lineWidth = lineWidths[ii]

  finally:
    self._endCommandEchoBlock()
    # self._project.unblankNotification()
    # undo.decreaseBlocking()

  # apiObjectsCreated = [apiMultiplet]
  #
  # undo.newItem(Undo._deleteAllApiObjects, apiMultiplet.root._unDelete,
  #              undoArgs=(apiObjectsCreated,),
  #              redoArgs=(apiObjectsCreated,  (apiMultiplet.topObject,)))

  # # DO creation notifications
  # if serial is not None:
  #   result._finaliseAction('rename')
  # result._finaliseAction('create')

  return result

Multiplet._parentClass.newMultiplet = _newMultiplet
del _newMultiplet

# Additional Notifiers:
#
# NB These API notifiers will be called for API multiplets - which match both Multiplets and Integrals
# className = Nmr.MultipletDim._metaclass.qualifiedName()
# Project._apiNotifiers.append(
#   ('_notifyRelatedApiObject', {'pathToObject':'multiplet', 'action':'change'}, className, ''),
# )
# for clazz in Nmr.AbstractMultipletDimContrib._metaclass.getNonAbstractSubtypes():
#   className = clazz.qualifiedName()
#   # NB - relies on MultipletDimContrib.multipletDim.multiplet still working for deleted multiplet. Should work.
#   Project._apiNotifiers.extend( (
#       ('_notifyRelatedApiObject', {'pathToObject':'multipletDim.multiplet',  'action':'change'},
#        className, 'postInit'),
#       ('_notifyRelatedApiObject', {'pathToObject':'multipletDim.multiplet',  'action':'change'},
#        className, 'delete'),
#     )
#   )
#
# # Notify Multiplets change when SpectrumReference changes
# # (That means DataDimRef referencing information)
# SpectrumReference._setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
#                           {'pathToObject':'spectrum.multiplets', 'action':'change'})
