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
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr import Nmr
#from ccpnmodel.ccpncore.lib import Util as modelUtil
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import Multiplet as apiMultiplet
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

  _parentClass = Spectrum

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
  def _parent(self) -> Optional[Spectrum]:
    """parent containing multiplet."""
    #TODO:ED trap that the Multiplet is no longer attached due to deletion
    return  self._project._data2Obj[self._wrappedData.dataSource]

  multipletParent = _parent

  @classmethod
  def _getAllWrappedData(cls, parent: Spectrum)-> Tuple[apiMultiplet, ...]:
    """get wrappedData (Multiplets) for all Multiplet children of parent MultipletList"""
    return parent._wrappedData.sortedMultiplets()

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

  try:
    apiParent = self._wrappedData   #
    if peaks:
      apiMultiplet = apiParent.newMultiplet(clusterType='multiplet',
                                              peaks=[p._wrappedData for p in peaks])
    else:
      apiMultiplet = apiParent.newMultiplet(clusterType='multiplet')
    
    result = self._project._data2Obj.get(apiMultiplet)

  finally:
    self._endCommandEchoBlock()

  return result

Multiplet._parentClass.newMultiplet = _newMultiplet
del _newMultiplet
