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
# from ccpn.core.PeakClusterList import PeakClusterList
from typing import Optional, Tuple, Union, Sequence


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

  @classmethod
  def _getAllWrappedData(cls, parent: Project)-> Tuple[apiPeakCluster, ...]:
    """get wrappedData (PeakClusters) for all PeakCluster children of parent PeakClusterList"""
    return parent._wrappedData.sortedPeakClusters()

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
