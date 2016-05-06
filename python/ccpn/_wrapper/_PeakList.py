"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
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

from ccpn import AbstractWrapperObject
from ccpn import Spectrum
from ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList


class PeakList(AbstractWrapperObject):
  """Peak List."""
  
  #: Short class name, for PID.
  shortClassName = 'PL'
  # Attribute it necessary as subclasses must use superclass className
  className = 'PeakList'

  #: Name of plural link to instances of class
  _pluralLinkName = 'peakLists'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiPeakList._metaclass.qualifiedName()

  # Special error-raising functions for people who think PeakList is a list
  def __iter__(self):
    raise TypeError("'PeakList object is not iterable - for a list of peaks use Peaklist.peaks")

  def __getitem__(self, index):
    raise TypeError("'PeakList object does not support indexing - for a list of peaks use Peaklist.peaks")

  def __len__(self):
    raise TypeError("'PeakList object has no length - for a list of peaks use Peaklist.peaks")

  # CCPN properties  
  @property
  def _apiPeakList(self) -> ApiPeakList:
    """ API peakLists matching PeakList"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of PeakList, used in Pid and to identify the PeakList. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> Spectrum:
    """Spectrum containing Peaklist."""
    return  self._project._data2Obj[self._wrappedData.dataSource]
  
  spectrum = _parent
  
  @property
  def name(self) -> str:
    """name of PeakList"""
    return self._wrappedData.name
    
  @name.setter
  def name(self, value:str):
    self._wrappedData.name = value
  
  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details
    
  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def symbolStyle(self) -> str:
    """Symbol style for peak annotation display"""
    return self._wrappedData.symbolStyle

  @symbolStyle.setter
  def symbolStyle(self, value:str):
    self._wrappedData.symbolStyle = value

  @property
  def symbolColour(self) -> str:
    """Symbol colour for peak annotation display"""
    return self._wrappedData.symbolColour

  @symbolColour.setter
  def symbolColour(self, value:str):
    self._wrappedData.symbolColour = value

  @property
  def textColour(self) -> str:
    """Text colour for peak annotation display"""
    return self._wrappedData.textColour

  @textColour.setter
  def textColour(self, value:str):
    self._wrappedData.textColour = value

  @property
  def isSimulated(self) -> bool:
    """Is peakList simulated"""
    return self._wrappedData.isSimulated

  @isSimulated.setter
  def isSimulated(self, value:bool):
    self._wrappedData.isSimulated = value

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent: Spectrum)-> list:
    """get wrappedData (PeakLists) for all PeakList children of parent Spectrum"""
    return [x for x in parent._wrappedData.sortedPeakLists() if x.dataType == 'Peak']

# Connections to parents:
Spectrum._childClasses.append(PeakList)

def _newPeakList(self:Spectrum,name:str=None, comment:str=None,
             isSimulated:bool=False) -> PeakList:
  """Create new empty ccpn.PeakList within ccpn.Spectrum"""
  apiDataSource = self._wrappedData
  obj = apiDataSource.newPeakList(name=name, details=comment, isSimulated=isSimulated)
  return self._project._data2Obj.get(obj)

Spectrum.newPeakList = _newPeakList
del _newPeakList

# Notifiers:
