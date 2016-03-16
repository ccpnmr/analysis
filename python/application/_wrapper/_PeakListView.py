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

import operator
from ccpncore.util.Types import Tuple
from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import PeakList
from application import SpectrumView
from ccpncore.api.ccpnmr.gui.Task import StripPeakListView as ApiStripPeakListView
from ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpncore.api.ccp.nmr.Nmr import PeakList as ApiPeakList
from application.core.modules.spectrumItems.GuiPeakListView import GuiPeakListView

class PeakListView(AbstractWrapperObject, GuiPeakListView):
  """Peak List View for 1D or nD PeakList"""
  
  #: Short class name, for PID.
  shortClassName = 'GL'
  # Attribute it necessary as subclasses must use superclass className
  className = 'PeakListView'

  #: Name of plural link to instances of class
  _pluralLinkName = 'peakListViews'
  
  #: List of child classes.
  _childClasses = []
  
  def __init__(self, project:Project, wrappedData:ApiStripPeakListView):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiPeakListView.__init__(self)

  # CCPN properties  
  @property
  def _apiPeakListView(self) -> ApiStripPeakListView:
    """ CCPN PeakListView matching PeakListView"""
    return self._wrappedData
    
  @property
  def _parent(self) -> SpectrumView:
    """SpectrumView containing PeakListView."""
    return self._project._data2Obj.get(self._wrappedData.stripSpectrumView)

  spectrumView = _parent

  def delete(self):
    """PeakListViews cannot be deleted, except as a byproduct of deleting other things"""
    raise Exception("PeakListViews cannot be deleted directly")

  @property
  def _key(self) -> str:
    """id string - """
    return str(self._wrappedData.peakListView.peakListSerial)

  @property
  def symbolStyle(self) -> str:
    """Symbol style for displayed peak markers"""
    wrappedData = self._wrappedData.peakListView
    result = wrappedData.symbolStyle
    if result is None:
      obj = wrappedData.peakList
      result = obj and obj.symbolStyle
    return result

  @symbolStyle.setter
  def symbolStyle(self, value:str):
    if self.symbolStyle != value:
      self._wrappedData.spectrumView.symbolStyle = value

  @property
  def symbolColour(self) -> str:
    """Symbol style for displayed peak markers"""
    wrappedData = self._wrappedData.peakListView
    result = wrappedData.symbolColour
    if result is None:
      obj = wrappedData.peakList
      result = obj and obj.symbolColour
    return result

  @symbolColour.setter
  def symbolColour(self, value:str):
    if self.symbolColour != value:
      self._wrappedData.peakListView.symbolColour = value

  @property
  def textColour(self) -> str:
    """Symbol style for displayed peak markers"""
    wrappedData = self._wrappedData.peakListView
    result = wrappedData.textColour
    if result is None:
      obj = wrappedData.peakList
      result = obj and obj.textColour
    return result

  @textColour.setter
  def textColour(self, value:str):
    if self.textColour != value:
      self._wrappedData.peakListView.textColour = value

  @property
  def isSymbolDisplayed(self) -> bool:
    """Is peak marker displayed?"""
    return self._wrappedData.peakListView.isSymbolDisplayed

  @isSymbolDisplayed.setter
  def isSymbolDisplayed(self, value:bool):
    self._wrappedData.peakListView.isSymbolDisplayed = value

  @property
  def isTextDisplayed(self) -> bool:
    """Is peak annotation displayed?"""
    return self._wrappedData.peakListView.isTextDisplayed

  @isTextDisplayed.setter
  def isTextDisplayed(self, value:bool):
    self._wrappedData.peakListView.isTextDisplayed = value

  @property
  def peakList(self) -> PeakList:
    """PeakList that PeakListView refers to"""
    return self._getWrapperObject(self._wrappedData.peakListView.peakList)

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:SpectrumView)-> list:
    """get wrappedData (ccpnmr.gui.Task.PeakListView) in serial number order"""
    return sorted(parent._wrappedData.stripPeakListViews,
                  key=operator.attrgetter('peakListView.peakListSerial'))

  #CCPN functions

# PeakList.peakListViews property
def _getPeakListViews(peakList:PeakList) -> Tuple[PeakListView, ...]:
  data2ObjDict = peakList._project._data2Obj
  return tuple(data2ObjDict[y]
               for x in peakList._wrappedData.sortedPeakListViews()
               for y in x.sortedStripPeakListViews())
PeakList.peakListViews = property(_getPeakListViews, None, None,
                                  "PeakListViews showing Spectrum")
del _getPeakListViews

# Notifiers
def _peakListAddPeakListViews(project:Project, apiPeakList:ApiPeakList):
  """Add ApiPeakListVIew when ApiPeakList is created"""
  for apiSpectrumView in apiPeakList.dataSource.spectrumViews:
    apiSpectrumView.newPeakListView(peakListSerial=apiPeakList.serial, peakList=apiPeakList)
Project._setupNotifier(_peakListAddPeakListViews, ApiPeakList, 'postInit')

def _SpectrumViewAddPeakListViews(project:Project, apiSpectrumView:ApiSpectrumView):
  """Add ApiPeakListView when ApiSpectrumView is created"""
  for apiPeakList in apiSpectrumView.dataSource.peakLists:
    apiSpectrumView.newPeakListView(peakListSerial=apiPeakList.serial, peakList=apiPeakList)
Project._setupNotifier(_SpectrumViewAddPeakListViews, ApiSpectrumView, 'postInit')


# Connections to parents:
SpectrumView._childClasses.append(PeakListView)

# Notifiers:
className = ApiStripPeakListView._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':PeakListView}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_finaliseUnDelete', {}, className, 'undelete'),
  )
)
