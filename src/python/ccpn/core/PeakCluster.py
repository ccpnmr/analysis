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
__version__ = "$Revision: 3.0.b4 $"
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

from ccpn.core.lib import Undo
from ccpn.util import Common as commonUtil
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.SpectrumReference import SpectrumReference
from ccpn.core.Peak import Peak
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
#from ccpnmodel.ccpncore.lib import Util as modelUtil
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakCluster as apiPeakCluster
# from ccpn.core.PeakClusterList import PeakClusterList
from typing import Optional, Tuple, Any, Union, Sequence
from ccpn.util.Common import makeIterableList


class PeakCluster(AbstractWrapperObject):
  """PeakCluster object, holding position, intensity, and assignment information

  Measurements that require more than one NmrAtom for an individual assignment
  (such as  splittings, J-couplings, MQ dimensions, reduced-dimensionality
  experiments etc.) are not supported (yet). Assignments can be viewed and set
  either as a list of assignments for each dimension (dimensionNmrAtoms) or as a
  list of all possible assignment combinations (assignedNmrAtoms)"""
  
  #: Short class name, for PID.
  shortClassName = 'PC'
  # Attribute it necessary as subclasses must use superclass className
  className = 'PeakCluster'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'peakClusters'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = apiPeakCluster._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiPeakCluster(self) -> apiPeakCluster:
    """ API peakClusters matching PeakCluster"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of PeakCluster, used in Pid and to identify the PeakCluster. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> Optional[Project]:
    """parent containing peakCluster."""
    #TODO:ED trap that the PeakCluster is no longer attached due to deletion
    return  self._project._data2Obj[self._wrappedData.nmrProject]

  peakClusterParent = _parent

  @property
  def annotation(self) -> Optional[str]:
    """Peak text annotation"""
    return self._wrappedData.annotation

  @annotation.setter
  def annotation(self, value: str):
    self._wrappedData.annotation = value

  @property
  def peaks(self) -> Optional[Tuple[Any]]:
    """List of peaks attached to the peakCluster"""
    try:
      return tuple([self._project._data2Obj[pk] for pk in self._wrappedData.sortedPeaks()])
    except:
      return None

  @property
  def numPeaks(self) -> int:
    """return number of peaks in the peakCluster"""
    return len(self._wrappedData.sortedPeaks())

  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> Tuple[apiPeakCluster, ...]:
    """get wrappedData (PeakClusters) for all PeakCluster children of parent PeakClusterList"""
    return parent._wrappedData.sortedPeakClusters()


  def addPeaks(self, peaks: ['Peak'] = None):
    """
    Add a peak or list of peaks to the peakCluster
    The peaks must belong to the spectrum containing the multipletList.

    :param peaks - single peak or list of peaks:
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # throw more understandable errors for the python console
    # spectrum = self._parent.spectrum
    pks = makeIterableList(peaks)
    for pp in pks:
      if not isinstance(pp, Peak):
        raise TypeError('%s is not of type Peak' % pp)
    #   if pp not in spectrum.peaks:
    #     raise ValueError('%s does not belong to spectrum: %s' % (pp.pid, spectrum.pid))
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

    defaults = collections.OrderedDict(
            (('peaks', None),
             )
    )
    undo = self._project._undo
    self._startCommandEchoBlock('addPeaks', values=locals(), defaults=defaults,
                                parName='addPeaks')
    try:
      for pk in pks:
        self._wrappedData.addPeak(pk._wrappedData)
    finally:
      self._endCommandEchoBlock()


  def removePeaks(self, peaks: ['Peak'] = None):
    """
    Remove a peak or list of peaks from the peakCluster
    The peaks must belong to the multiplet.

    :param peaks - single peak or list of peaks:
    """
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb
    # throw more understandable errors for the python console
    # spectrum = self._parent.spectrum
    pks = makeIterableList(peaks)
    for pp in pks:
      if not isinstance(pp, Peak):
        raise TypeError('%s is not of type Peak' % pp)
      if pp not in self.peaks:
        raise ValueError('%s does not belong to multiplet: %s' % (pp.pid, self.pid))
      # if pp not in spectrum.peaks:
      #   raise ValueError('%s does not belong to spectrum: %s' % (pp.pid, spectrum.pid))
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ ejb

    defaults = collections.OrderedDict(
            (('peaks', None),
             )
    )
    undo = self._project._undo
    self._startCommandEchoBlock('removePeaks', values=locals(), defaults=defaults,
                                parName='removePeaks')
    try:
      for pk in pks:
        self._wrappedData.removePeak(pk._wrappedData)
    finally:
      self._endCommandEchoBlock()


# Connections to parents:
def _newPeakCluster(self:Project, peaks:['Peak']=None, serial:int=None) -> PeakCluster:
  """Create new PeakCluster within peakClusterList"""

  defaults = collections.OrderedDict(
    (('peaks', None), ('serial', None),
    )
  )

  undo = self._project._undo
  self._startCommandEchoBlock('newPeakCluster', values=locals(), defaults=defaults,
                              parName='newPeakCluster')

  try:
    apiParent = self._wrappedData   #
    if peaks:
      apiPeakCluster = apiParent.newPeakCluster(clusterType='multiplet',
                                              peaks=[p._wrappedData for p in peaks])
    else:
      apiPeakCluster = apiParent.newPeakCluster(clusterType='multiplet')
    
    result = self._project._data2Obj.get(apiPeakCluster)

  finally:
    self._endCommandEchoBlock()

  return result

PeakCluster._parentClass.newPeakCluster = _newPeakCluster
del _newPeakCluster
