"""eakList View in a specific SpectrumView

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
from ccpn import Project
from ccpn import PeakList
from ccpnmr import SpectrumView
from ccpncore.api.ccpnmr.gui.Task import PeakListView as ApiPeakListView


class PeakListView(AbstractWrapperObject):
  """Peak List View for 1D or nD PeakList"""
  
  #: Short class name, for PID.
  shortClassName = 'GL'

  #: Name of plural link to instances of class
  _pluralLinkName = 'peakListViews'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def apiPeakListView(self) -> ApiPeakListView:
    """ CCPN PeakListView matching PeakListView"""
    return self._wrappedData
    
  @property
  def _parent(self) -> SpectrumView:
    """SpectrumView containing PeakListView."""
    return self._project._data2Obj.get(self._wrappedData.spectrumView)

  spectrumView= _parent

  @property
  def _key(self) -> str:
    """id string - """
    return str(self._wrappedData.serial)

  @property
  def symbolStyle(self) -> str:
    """Symbol style for displayed peak markers"""
    return self._wrappedData.symbolStyle

  @symbolStyle.setter
  def symbolStyle(self, value:str):
    self._wrappedData.symbolStyle = value

  @property
  def symbolColour(self) -> str:
    """Colour of displayed peak markers"""
    return self._wrappedData.symbolColour

  @symbolColour.setter
  def symbolColour(self, value:str):
    self._wrappedData.symbolColour = value

  @property
  def textColour(self) -> str:
    """Colour of displayed peak annotations"""
    return self._wrappedData.textColour

  @textColour.setter
  def textColour(self, value:str):
    self._wrappedData.textColour = value

  @property
  def isSymbolDisplayed(self) -> bool:
    """Is peak marker displayed?"""
    return self._wrappedData.isSymbolDisplayed

  @isSymbolDisplayed.setter
  def isSymbolDisplayed(self, value:bool):
    self._wrappedData.isSymbolDisplayed = value

  @property
  def isTextDisplayed(self) -> bool:
    """Is peak annotation displayed?"""
    return self._wrappedData.isTextDisplayed

  @isTextDisplayed.setter
  def isTextDisplayed(self, value:bool):
    self._wrappedData.isTextDisplayed = value

  @property
  def peakList(self) -> PeakList:
    """PeakList that PeakListView refers to"""
    return self.getWrapperObject(self._wrappedData.peakList)

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:SpectrumView)-> list:
    """get wrappedData (ccpnmr.gui.Task.PeakListView) in serial number order"""
    return parent._wrappedData.sortedPeakLists()

  #CCPN functions

# PeakList.peaListViews property
def _getPeakListViews(peakList:PeakList):
  return tuple(peakList._project._data2Obj[x]
               for x in peakList._wrappedData.sortedPeakListViews())
PeakList.peakListViews = property(_getPeakListViews, None, None,
                                         "PeakListViews showing Spectrum")
del _getPeakListViews


# Connections to parents:
SpectrumView._childClasses.append(PeakListView)

# Notifiers:
className = ApiPeakListView._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':PeakListView}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
