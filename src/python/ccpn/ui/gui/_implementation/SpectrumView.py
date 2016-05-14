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

from PyQt4 import QtCore, QtGui

import operator
from typing import Tuple
from ccpn.util import Pid
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.core.Project import Project
from ccpn.core.Spectrum import Spectrum
from ccpn.ui.gui._implementation.Strip import Strip
from ccpncore.api.ccpnmr.gui.Task import StripSpectrumView as ApiStripSpectrumView
from ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpn.ui.gui.modules.GuiSpectrumView1d import GuiSpectrumView1d
from ccpn.ui.gui.modules.GuiSpectrumViewNd import GuiSpectrumViewNd


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

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiStripSpectrumView._metaclass.qualifiedName()
  

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
  def positiveLevels(self) ->  Tuple[float, ...]:
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
  def negativeLevels(self) ->  Tuple[float, ...]:
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

  @property
  def _displayOrderSpectrumDimensionIndices(self) -> Tuple[int, ...]:
    """Indices of spectrum dimensions in display order (x, y, Z1, ...)"""
    apiStripSpectrumView = self._wrappedData
    apiStrip = apiStripSpectrumView.strip

    axisCodes = apiStrip.axisCodes

    # DImensionOrdering is one-origin (first dim is dim 1)
    dimensionOrdering = apiStripSpectrumView.spectrumView.dimensionOrdering

    # Convert to zero-origin (for indices) and return
    ll = tuple(dimensionOrdering[axisCodes.index(x)] for x in apiStrip.axisOrder)
    return tuple(None if x is None else x-1 for x in ll)



  def _spectrumViewHasChanged(self):
    """Change action icon colour and other changes when spectrumView changes

    NB SpectrumView change notifiers are triggered when either DataSource or ApiSpectrumView change"""
    spectrumDisplay = self.strip.spectrumDisplay
    apiDataSource = self.spectrum._wrappedData

    # Update action icol colour
    action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
    if action:
      pix=QtGui.QPixmap(QtCore.QSize(60, 10))
      if spectrumDisplay.is1D:
        pix.fill(QtGui.QColor(self.sliceColour))
      else:
        pix.fill(QtGui.QColor(self.positiveContourColour))
      action.setIcon(QtGui.QIcon(pix))

    # Update strip
    self.strip.update()

  def _createdSpectrumView(self):
    """Set up SpectrumDisplay when new StripSpectrumView is created - for notifiers"""

    # NBNB TBD FIXME get rid of API objects

    spectrumDisplay = self.strip.spectrumDisplay
    spectrum = self.spectrum

    # Set Z widgets for nD strips
    if not spectrumDisplay.is1D:
      strip = self.strip
      if not strip.haveSetupZWidgets:
        strip.setZWidgets()

    # Handle action buttons
    apiDataSource = spectrum._wrappedData
    action = spectrumDisplay.spectrumActionDict.get(apiDataSource)
    if not action:
      # add toolbar action (button)
      spectrumName = spectrum.name
      if len(spectrumName) > 12:
        spectrumName = spectrumName[:12]+'.....'
      action = spectrumDisplay.spectrumToolBar.addAction(spectrumName)
      action.setCheckable(True)
      action.setChecked(True)
      action.setToolTip(spectrum.name)
      widget = spectrumDisplay.spectrumToolBar.widgetForAction(action)
      widget.setIconSize(QtCore.QSize(120, 10))
      if spectrumDisplay.is1D:
        widget.setFixedSize(100, 30)
      else:
        widget.setFixedSize(75, 30)
      widget.spectrumView = self._wrappedData
      spectrumDisplay.spectrumActionDict[apiDataSource] = action
      # The following call sets the icon colours:
      self._spectrumViewHasChanged()

    if spectrumDisplay.is1D:
      action.toggled.connect(self.plot.setVisible)
    action.toggled.connect(self.setVisible)


  def _deletedSpectrumView(self):
    """Update interface when a spectrumView is deleted"""
    scene = self.strip.plotWidget.scene()
    scene.removeItem(self)
    if hasattr(self, 'plot'):  # 1d
      scene.removeItem(self.plot)

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Strip)-> list:
    """get wrappedData (ccpnmr.gui.Task.SpectrumView) in serial number order"""
    return sorted(parent._wrappedData.stripSpectrumViews,
                  key=operator.attrgetter('spectrumView.spectrumName'))

  #CCPN functions

# Spectrum.spectrumViews property
def _getSpectrumViews(spectrum:Spectrum):
  return tuple(spectrum._project._data2Obj.get(y)
               for x in spectrum._wrappedData.sortedSpectrumViews()
               for y in x.sortedStripSpectrumViews())
Spectrum.spectrumViews = property(_getSpectrumViews, None, None,
                                   "SpectrumViews showing Spectrum")

# Strip.spectrumViews property
def _getSpectrumViews(strip:Strip):
  return tuple(strip._project._data2Obj.get(x)
               for x in strip._wrappedData.sortedStripSpectrumViews())
Strip.spectrumViews = property(_getSpectrumViews, None, None,
                                   "SpectrumViews shown in Strip")
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
    return self._wrappedData.spectrumView.spectrumName.translate(Pid.remapSeparators)


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
    return self._wrappedData.spectrumView.spectrumName.translate(Pid.remapSeparators)


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
# Notify SpectrumView change when SpiSpectrumView changes (underlying object is StripSpectrumView)
Project._apiNotifiers.append(
  ('_notifyRelatedApiObject', {'pathToObject':'stripSpectrumViews', 'action':'change'},
   ApiSpectrumView._metaclass.qualifiedName(), '')
)

# Notify SpectrumView change when Spectrum changes
Spectrum.setupCoreNotifier('change', AbstractWrapperObject._finaliseRelatedObject,
                          {'pathToObject':'spectrumViews', 'action':'change'})

# Links to SpectrumView and Spectrum are fixed after creation - any link notifiers should be put in
# create/destroy instead

# # Update Strip when SpectrumView changes
# SpectrumView.setupCoreNotifier('change', Strip.update)

SpectrumView.setupCoreNotifier('delete', SpectrumView._deletedSpectrumView)

SpectrumView.setupCoreNotifier('create', SpectrumView._createdSpectrumView)


SpectrumView.setupCoreNotifier('change', SpectrumView._spectrumViewHasChanged)
