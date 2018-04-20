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
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:29 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
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
# from ccpn.core.Spectrum import Spectrum
from ccpn.core.MultipletList import MultipletList
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
#from ccpnmodel.ccpncore.lib import Util as modelUtil
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Multiplet as apiMultiplet
# from ccpn.core.MultipletList import MultipletList
from typing import Optional, Tuple, Union, Sequence
from ccpn.util.Common import makeIterableList


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

  _parentClass = MultipletList

  #: Name of plural link to instances of class
  _pluralLinkName = 'multiplets'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = apiMultiplet._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiMultiplet(self) -> apiMultiplet:
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
  def _parent(self) -> Optional[MultipletList]:
    """parent containing multiplet."""
    return  self._project._data2Obj[self._wrappedData.multipletList]

  multipletList = _parent

  @property
  def height(self) -> Optional[float]:
    """height of Peak"""
    return self._wrappedData.height

  @height.setter
  def height(self, value: float):
    self._wrappedData.height = value

  @property
  def heightError(self) -> Optional[float]:
    """height error of Peak"""
    return self._wrappedData.heightError

  @heightError.setter
  def heightError(self, value: float):
    self._wrappedData.heightError = value

  @property
  def volume(self) -> Optional[float]:
    """volume of Peak"""
    return self._wrappedData.volume

  @volume.setter
  def volume(self, value: float):
    self._wrappedData.volume = value

  @property
  def volumeError(self) -> Optional[float]:
    """volume error of Peak"""
    return self._wrappedData.volumeError

  @volumeError.setter
  def volumeError(self, value: float):
    self._wrappedData.volumeError = value

  @property
  def figureOfMerit(self) -> Optional[float]:
    """figureOfMerit of Peak, between 0.0 and 1.0 inclusive."""
    return self._wrappedData.figOfMerit

  @figureOfMerit.setter
  def figureOfMerit(self, value: float):
    self._wrappedData.figOfMerit = value

  @property
  def annotation(self) -> Optional[str]:
    """Peak text annotation"""
    return self._wrappedData.annotation

  @annotation.setter
  def annotation(self, value: str):
    self._wrappedData.annotation = value

  @property
  def comment(self) -> Optional[str]:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value: str):
    self._wrappedData.details = value

  @property
  def peaks(self) -> Optional[Tuple[Peak]]:
    """List of peaks attached to the multiplet"""
    return self._wrappedData.sortedPeaks()

  @property
  def numPeaks(self) -> int:
    """return number of peaks in the multiplet"""
    return len(self._wrappedData.sortedPeaks())

  @property
  def position(self) -> Tuple[float, ...]:
    """Peak position in ppm (or other relevant unit) in dimension order."""
    pks = self.peaks
    if pks:
      self._position = self._wrappedData.sortedPeaks[0]
    return tuple(x.value for x in self._wrappedData.sortedPeakDims())

  @property
  def positionError(self) -> Tuple[Optional[float], ...]:
    """Peak position error in ppm (or other relevant unit)."""
    return tuple(x.valueError for x in self._wrappedData.sortedPeakDims())

  @property
  def boxWidths(self) -> Tuple[Optional[float], ...]:
    """The full width of the peak footprint in points for each dimension,
    i.e. the width of the area that should be considered for integration, fitting, etc. ."""
    return tuple(x.boxWidth for x in self._wrappedData.sortedPeakDims())

  @property
  def lineWidths(self) -> Tuple[Optional[float], ...]:
    """Full-width-half-height of peak/multiplet for each dimension, in Hz. """
    return tuple(x.lineWidth for x in self._wrappedData.sortedPeakDims())

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: MultipletList)-> Tuple[apiMultiplet, ...]:
    """get wrappedData (Multiplets) for all Multiplet children of parent MultipletList"""
    return parent._wrappedData.sortedMultiplets()

# Connections to parents:
def _newMultiplet(self:MultipletList, peaks:['Peak']=None, serial:int=None) -> Multiplet:
  """Create new Multiplet within multipletList"""

  defaults = collections.OrderedDict(
    (('peaks', None), ('serial', None),
    )
  )

  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
  # throw more understandable errors for the python console
  spectrum = self.multipletListParent
  pks = makeIterableList(peaks)
  for pp in pks:
    if not isinstance(pp, Peak):
      raise TypeError('%s is not of type Peak' % pp)
    if pp not in spectrum.peaks:
      raise ValueError('%s does not belong to spectrum: %s' % (pp.pid, spectrum.pid))
  #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

  undo = self._project._undo
  self._startCommandEchoBlock('newMultiplet', values=locals(), defaults=defaults,
                              parName='newMultiplet')

  try:
    apiParent = self._apiMultipletList
    if pks:
      apiMultiplet = apiParent.newMultiplet(multipletType='multiplet',
                                              peaks=[p._wrappedData for p in pks])
    else:
      apiMultiplet = apiParent.newMultiplet(multipletType='multiplet')
    
    result = self._project._data2Obj.get(apiMultiplet)

  finally:
    self._endCommandEchoBlock()

  return result

Multiplet._parentClass.newMultiplet = _newMultiplet
del _newMultiplet
