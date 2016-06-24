"""Module Documentation here

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

import collections
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.PeakList import PeakList
from ccpn.core.Spectrum import Spectrum
from ccpnmodel.ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList


class IntegralList(AbstractWrapperObject):
  """Integral List."""
  
  #: Short class name, for PID.
  shortClassName = 'IL'
  # Attribute it necessary as subclasses must use superclass className
  className = 'IntegralList'

  _parentClass = Spectrum

  #: Name of plural link to instances of class
  _pluralLinkName = 'integralLists'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class - NB shared with PeakList
  _apiClassQualifiedName = ApiPeakList._metaclass.qualifiedName()

  # Notifiers are handled through the PeakList class (which shares the ApiPeakList wrapped object)
  _registerClassNotifiers = False

  # Special error-raising functions for people who think PeakList is a list
  def __iter__(self):
    raise TypeError("IntegralList object is not iterable -"
                    "for a list of integrals use IntegralList.integrals")

  def __getitem__(self, index):
    raise TypeError("IntegralList object does not support indexing -"
                    " for a list of integrals use IntegralList.integrals")

  def __len__(self):
    raise TypeError("IntegralList object has no length - "
                    "for a list of integrals use IntegralList.integrals")

  # CCPN properties  
  @property
  def _apiPeakList(self) -> ApiPeakList:
    """ API peakLists matching IntegralList"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of IntegralList, used in Pid and to identify the IntegralList. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> Spectrum:
    """Spectrum containing IntegralList."""
    return  self._project._data2Obj[self._wrappedData.dataSource]
  
  spectrum = _parent
  
  @property
  def title(self) -> str:
    """name of IntegralList"""
    return self._wrappedData.name
    
  @title.setter
  def title(self, value:str):
    self._wrappedData.name = value

  @property
  def symbolColour(self) -> str:
    """Symbol colour for integral annotation display"""
    return self._wrappedData.symbolColour

  @symbolColour.setter
  def symbolColour(self, value:str):
    self._wrappedData.symbolColour = value

  @property
  def textColour(self) -> str:
    """Text colour for integral annotation display"""
    return self._wrappedData.textColour

  @textColour.setter
  def textColour(self, value:str):
    self._wrappedData.textColour = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Spectrum)-> list:
    """get wrappedData (PeakLists) for all IntegralList children of parent Spectrum"""
    return [x for x in parent._wrappedData.sortedPeakLists() if x.dataType == 'Integral']

# Connections to parents:

def _newIntegralList(self:Spectrum, title:str=None, comment:str=None) -> IntegralList:
  """Create new ccpn.IntegralList within ccpn.Spectrum"""

  defaults = collections.OrderedDict((('title', None), ('comment', None)))

  apiDataSource = self._wrappedData
  self._startFunctionCommandBlock('newIntegralList', values=locals(), defaults=defaults,
                                  parName='newIntegralList')
  try:
    obj = apiDataSource.newPeakList(name=title, details=comment, dataType='Integral')
  finally:
    self._project._appBase._endCommandBlock()
  return self._project._data2Obj.get(obj)

Spectrum.newIntegralList = _newIntegralList
del _newIntegralList


def _factoryFunction(project:Project, wrappedData:ApiPeakList) -> AbstractWrapperObject:
  """create PeakList or IntegralList from API PeakList"""
  if wrappedData.dataType == 'Peak':
    return PeakList(project, wrappedData)
  elif wrappedData.dataType == 'Integral':
    return IntegralList(project, wrappedData)
  else:
    raise ValueError("API PeakList object has illegal dataType: %s. Must be 'Peak' or 'Integral"
                     % wrappedData.dataType)


IntegralList._factoryFunction = staticmethod(_factoryFunction)
PeakList._factoryFunction = staticmethod(_factoryFunction)

# Notifiers:

# NB API level notifiers are (and must be) in PeakList instead
