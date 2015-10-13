"""Spectrum View in a specific SpectrumDisplay

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
from ccpn import Spectrum
from ccpnmr import Strip
from ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView
from ccpnmrcore.modules.GuiSpectrumView1d import GuiSpectrumView1d
from ccpnmrcore.modules.GuiSpectrumViewNd import GuiSpectrumViewNd


class SpectrumView(AbstractWrapperObject):
  """Spectrum View for 1D or nD spectrum"""
  
  #: Short class name, for PID.
  shortClassName = 'GV'
  # Attribute it necessary as subclasses must use superclass className
  className = 'SpectrumView'

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectrumViews'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def _apiStripSpectrumView(self) -> ApiStripSpectrumView:
    """ CCPN SpectrumView matching SpectrumView"""
    return self._wrappedData

  @property
  def spectrumName(self) -> str:
    """Name of connected spectrum"""
    return self._wrappedData.spectrumView.spectrumName
    
  @property
  def _parent(self) -> Strip:
    """Strip containing stripSpectrumView."""
    return self._project._data2Obj.get(self._wrappedData.strip)

  strip = _parent

  def delete(self):
    """Delete SpectrumView for all strips"""
    self._wrappedData.spectrumView.delete()

  @property
  def experimentType(self) -> str:
    """Experiment type of attached experiment - used for reconnecting to correct spectrum"""
    return self._wrappedData.spectrumView.experimentType

  @experimentType.setter
  def experimentType(self, value:str):
    self._wrappedData.spectrumView.experimentType = value

  # Removed - should not be used at arapper level
  # @property
  # def dimensionOrdering(self) -> tuple:
  #   """Display order of Spectrum dimensions (DataDim.dim). 0 for 'no spectrum axis displayed'"""
  #   return self._wrappedData.spectrumView.dimensionOrdering
  #
  # @dimensionOrdering.setter
  # def dimensionOrdering(self, value:Sequence):
  #   self._wrappedData.spectrumView.dimensionOrdering = value

  @property
  def isDisplayed(self) -> bool:
    """Is spectrum displayed?"""
    return self._wrappedData.spectrumView.isDisplayed

  @isDisplayed.setter
  def isDisplayed(self, value:bool):
    self._wrappedData.spectrumView.isDisplayed = value

  @property
  def positiveContourColour(self) -> str:
    """Colour identifier for positive contours"""
    wrappedData = self._wrappedData.spectrumView
    result = wrappedData.positiveContourColour
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.positiveContourColour
    return result

  @positiveContourColour.setter
  def positiveContourColour(self, value:str):
    if self.positiveContourColour != value:
      self._wrappedData.spectrumView.positiveContourColour = value

  @property
  def positiveContourCount(self) -> int:
    """Number of positive contours"""
    wrappedData = self._wrappedData.spectrumView
    result = wrappedData.positiveContourCount
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.positiveContourCount
    return result

  @positiveContourCount.setter
  def positiveContourCount(self, value:int):
    if self.positiveContourCount != value:
      self._wrappedData.spectrumView.positiveContourCount = value

  @property
  def positiveContourBase(self) -> float:
    """Base level for positive contours"""
    wrappedData = self._wrappedData.spectrumView
    result = wrappedData.positiveContourBase
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.positiveContourBase
    return result

  @positiveContourBase.setter
  def positiveContourBase(self, value:float):
    if self.positiveContourBase != value:
      self._wrappedData.spectrumView.positiveContourBase = value

  @property
  def positiveContourFactor(self) -> float:
    """Level multiplication factor for positive contours"""
    wrappedData = self._wrappedData.spectrumView
    result = wrappedData.positiveContourFactor
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.positiveContourFactor
    return result

  @positiveContourFactor.setter
  def positiveContourFactor(self, value:float):
    if self.positiveContourFactor != value:
      self._wrappedData.spectrumView.positiveContourFactor = value

  @property
  def displayPositiveContours(self) -> bool:
    """Are positive contours displayed?"""
    return self._wrappedData.spectrumView.displayPositiveContours

  @displayPositiveContours.setter
  def displayPositiveContours(self, value:bool):
    self._wrappedData.spectrumView.displayPositiveContours = value

  @property
  def negativeContourColour(self) -> str:
    """Colour identifier for negative contours"""
    wrappedData = self._wrappedData.spectrumView
    result = wrappedData.negativeContourColour
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.negativeContourColour
    return result

  @negativeContourColour.setter
  def negativeContourColour(self, value:str):
    if self.negativeContourColour != value:
      self._wrappedData.spectrumView.negativeContourColour = value

  @property
  def negativeContourCount(self) -> int:
    """Number of negative contours"""
    wrappedData = self._wrappedData.spectrumView
    result = wrappedData.negativeContourCount
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.negativeContourCount
    return result

  @negativeContourCount.setter
  def negativeContourCount(self, value:int):
    if self.negativeContourCount != value:
      self._wrappedData.spectrumView.negativeContourCount = value

  @property
  def negativeContourBase(self) -> float:
    """Base level for negative contours"""
    wrappedData = self._wrappedData.spectrumView
    result = wrappedData.negativeContourBase
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.negativeContourBase
    return result

  @negativeContourBase.setter
  def negativeContourBase(self, value:float):
    if self.negativeContourBase != value:
      self._wrappedData.spectrumView.negativeContourBase = value

  @property
  def negativeContourFactor(self) -> float:
    """Level multiplication factor for negative contours"""
    wrappedData = self._wrappedData.spectrumView
    result = wrappedData.negativeContourFactor
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.negativeContourFactor
    return result

  @negativeContourFactor.setter
  def negativeContourFactor(self, value:float):
    if self.negativeContourFactor != value:
      self._wrappedData.spectrumView.negativeContourFactor = value

  @property
  def displayNegativeContours(self) -> bool:
    """Are negative contours displayed?"""
    return self._wrappedData.spectrumView.displayNegativeContours

  @displayNegativeContours.setter
  def displayNegativeContours(self, value:bool):
    self._wrappedData.spectrumView.displayNegativeContours = value

  @property
  def positiveLevels(self) -> tuple:
    """Positive contouring levels from lowest to highest"""
    number = self.positiveContourCount
    if number < 1:
      return tuple()
    else:
      result = [self.positiveContourBase]
      factor = self.positiveContourFactor
      for ii in range(1, number):
        result.append(factor * result[-1])
      #
      return tuple(result)

  @property
  def negativeLevels(self) -> tuple:
    """Negative contouring levels from lowest to highest"""
    number = self.negativeContourCount
    if number < 1:
      return tuple()
    else:
      result = [self.negativeContourBase]
      factor = self.negativeContourFactor
      for ii in range(1, number):
        result.append(factor * result[-1])
      #
      return tuple(result)

  @property
  def sliceColour(self) -> str:
    """Colour for 1D slices and 1D spectra"""
    wrappedData = self._wrappedData.spectrumView
    result = wrappedData.sliceColour
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.sliceColour
    return result

  @sliceColour.setter
  def sliceColour(self, value:str):
    if self.sliceColour != value:
      self._wrappedData.spectrumView.sliceColour = value

  @property
  def spectrum(self) -> Spectrum:
    """Spectrum that SpectrumView refers to"""
    return self._project._data2Obj.get(self._wrappedData.spectrumView.dataSource)

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Strip)-> list:
    """get wrappedData (ccpnmr.gui.Task.SpectrumView) in serial number order"""
    return parent._wrappedData.sortedStripSpectrumViews()

  #CCPN functions

# Spectrum.spectrumViews property
def _getSpectrumViews(spectrum:Spectrum):
  return tuple(spectrum._project._data2Obj.get(y)
               for x in spectrum._wrappedData.sortedSpectrumViews()
               for y in x.sortedStripSpectrumViews())
Spectrum.spectrumViews = property(_getSpectrumViews, None, None,
                                   "SpectrumDisplays showing Spectrum")

# Strip.spectrumViews property
def _getSpectrumViews(strip:Strip):
  return tuple(strip._project._data2Obj.get(x)
               for x in strip._wrappedData.sortedStripSpectrumViews())
Strip.spectrumViews = property(_getSpectrumViews, None, None,
                                   "SpectrumDisplays showing Spectrum")
del _getSpectrumViews

# Define subtypes and factory function
class SpectrumView1d(SpectrumView, GuiSpectrumView1d):
  """1D Spectrum View"""

  def __init__(self, project:Project, wrappedData:ApiStripSpectrumView):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiSpectrumView1d.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """id string - combined spectrumName and stripSerial"""
    return self._wrappedData.spectrumView.spectrumName


class SpectrumViewNd(SpectrumView, GuiSpectrumViewNd):
  """ND Spectrum View"""

  def __init__(self, project:Project, wrappedData:ApiStripSpectrumView):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiSpectrumViewNd.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """id string - spectrumName"""
    return self._wrappedData.spectrumView.spectrumName


def _factoryFunction(project:Project, wrappedData:ApiStripSpectrumView) -> SpectrumView:
  """create SpectrumView, dispatching to subtype depending on wrappedData"""
  if 'intensity' in wrappedData.strip.spectrumDisplay.axisCodes:
    # 1D display
    return SpectrumView1d(project, wrappedData)
  else:
    # ND display
    return  SpectrumViewNd(project, wrappedData)

# Connections to parents:
Strip._childClasses.append(SpectrumView)
SpectrumView._factoryFunction = staticmethod(_factoryFunction)

# Notifiers:
className = ApiStripSpectrumView._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':SpectrumView._factoryFunction}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete'),
    ('_finaliseUnDelete', {}, className, 'undelete'),
  )
)
