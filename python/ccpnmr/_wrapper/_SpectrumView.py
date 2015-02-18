"""Spectrum View in a specific SpectrumDisplay

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpncore.util import pid as Pid

__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon Skinner, Geerten Vuister"
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
from collections.abc import Sequence

from ccpn._wrapper._AbstractWrapperObject import AbstractWrapperObject
from ccpn._wrapper._Project import Project
from ccpnmr._wrapper._SpectrumDisplay import SpectrumDisplay
from ccpnmr._wrapper._Strip import Strip
from ccpncore.api.ccpnmr.gui.Task import SpectrumView as ApiSpectrumView
from ccpnmrcore.modules.GuiSpectrumView1d import GuiSpectrumView1d
from ccpnmrcore.modules.GuiSpectrumViewNd import GuiSpectrumViewNd


class SpectrumView(AbstractWrapperObject):
  """Display Strip for 1D or nD spectrum"""
  
  #: Short class name, for PID.
  shortClassName = 'GV'

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectrumViews'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def apiSpectrumView(self) -> ApiSpectrumView:
    """ CCPN SpectrumView matching SpectrumView"""
    return self._wrappedData

  @property
  def stripSerial(self) -> int:
    """serial number, key for deriving attached Strip, part of object ke
    stripSerial 0 signifies 'all strips'"""
    return self._wrappedData.stripSerial

  @property
  def spectrumName(self) -> str:
    """Name of connected spectrum"""
    return self._wrappedData.spectrumName
    
  @property
  def _parent(self) -> SpectrumDisplay:
    """Parent (containing) object."""
    return self._project._data2Obj.get(self._wrappedData.spectrumDisplay)


  @property
  def experimentType(self) -> str:
    """Experiment type of attached experiment - used for reconnecting to correct spectrum"""
    return self._wrappedData.experimentType

  @experimentType.setter
  def experimentType(self, value:str):
    self._wrappedData.experimentType = value

  @property
  def dimensionOrdering(self) -> tuple:
    """Display order of Spectrum dimensions (DataDim.dim). 0 for 'no spectrum axis displayed'"""
    return self._wrappedData.dimensionOrdering

  @dimensionOrdering.setter
  def dimensionOrdering(self, value:Sequence):
    self._wrappedData.dimensionOrdering = value

  @property
  def isDisplayed(self) -> bool:
    """Is spectrum displayed?"""
    return self._wrappedData.isDisplayed

  @isDisplayed.setter
  def isDisplayed(self, value:bool):
    self._wrappedData.isDisplayed = value

  @property
  def positiveContourColour(self) -> str:
    """Colour identifier for positive contours"""
    wrappedData = self._wrappedData
    result = wrappedData.positiveContourColour
    if result is None:
      obj = wrappedData.dataSource
      result = obj and obj.positiveContourColour
    return result

  @positiveContourColour.setter
  def positiveContourColour(self, value:str):
    wrappedData = self._wrappedData
    self._wrappedData.positiveContourColour = value

  @property
  def positiveContourCount(self) -> int:
    """Number of positive contours"""
    return self._wrappedData.positiveContourCount

  @positiveContourCount.setter
  def positiveContourCount(self, value:int):
    self._wrappedData.positiveContourCount = value

  @property
  def positiveContourBase(self) -> float:
    """Base level for positive contours"""
    return self._wrappedData.positiveContourBase

  @positiveContourBase.setter
  def positiveContourBase(self, value:float):
    self._wrappedData.positiveContourBase = value

  @property
  def positiveContourFactor(self) -> float:
    """Level multiplication factor for positive contours"""
    return self._wrappedData.positiveContourFactor

  @positiveContourFactor.setter
  def positiveContourFactor(self, value:float):
    self._wrappedData.positiveContourFactor = value

  @property
  def displayNegativeContours(self) -> bool:
    """Are negative contours displayed?"""
    return self._wrappedData.displayNegativeContours

  @displayNegativeContours.setter
  def displayNegativeContours(self, value:bool):
    self._wrappedData.displayNegativeContours = value

  @property
  def negativeContourColour(self) -> str:
    """Colour identifier for negative contours"""
    return self._wrappedData.negativeContourColour

  @negativeContourColour.setter
  def negativeContourColour(self, value:str):
    self._wrappedData.negativeContourColour = value

  @property
  def negativeContourCount(self) -> int:
    """Number of negative contours"""
    return self._wrappedData.negativeContourCount

  @negativeContourCount.setter
  def negativeContourCount(self, value:int):
    self._wrappedData.negativeContourCount = value

  @property
  def negativeContourBase(self) -> float:
    """Base level for negative contours"""
    return self._wrappedData.negativeContourBase

  @negativeContourBase.setter
  def negativeContourBase(self, value:float):
    self._wrappedData.negativeContourBase = value

  @property
  def negativeContourFactor(self) -> float:
    """Level multiplication factor for negative contours"""
    return self._wrappedData.negativeContourFactor

  @negativeContourFactor.setter
  def negativeContourFactor(self, value:float):
    self._wrappedData.negativeContourFactor = value

  @property
  def displayNegativeContours(self) -> bool:
    """Are negative contours displayed?"""
    return self._wrappedData.displayNegativeContours

  @displayNegativeContours.setter
  def displayNegativeContours(self, value:bool):
    self._wrappedData.displayNegativeContours = value

  @property
  def sliceColour(self) -> str:
    """Colour for 1D slices and 1D spectra"""
    return self._wrappedData.sliceColour

  @sliceColour.setter
  def sliceColour(self, value:str):
    self._wrappedData.sliceColour = value

  @property
  def strips(self) -> Strip:
    """Strips attached to SpectrumView -n either one, or all in Display"""
    stripSerial = self.stripSerial
    if stripSerial:
      ll = tuple(self._project._data2Obj.get(
        self._parent._wrappedData.findFirstStrip(serial=stripSerial)))
    else:
      return self._parent.orderedStrips

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:SpectrumDisplay)-> list:
    """get wrappedData (ccp.gui.Strip) in serial number order"""
    return parent._wrappedData.sortedSpextrumViews()

  #CCPN functions


# Define subtypes and factory function
class SpectrumView1d(SpectrumView, GuiSpectrumView1d):
  """1D Spectrum View"""

  def __init__(self, project:Project, wrappedData:ApiSpectrumView):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiSpectrumView1d.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """id string - combined spectrumName and stripSerial"""
    return Pid.IDSEP.join((self.spectrumName, str(self.stripSerial)))


class SpectrumViewNd(SpectrumView, GuiSpectrumViewNd):
  """ND Spectrum View"""

  def __init__(self, project:Project, wrappedData:ApiSpectrumView):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiSpectrumViewNd.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """id string - combined spectrumName and stripSerial"""
    return Pid.IDSEP.join((self.spectrumName, str(self.stripSerial)))


def _factoryFunction(project:Project, wrappedData:ApiSpectrumView) -> SpectrumView:
  """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
  if 'intensity' in wrappedData.spectrumDisplay.axisCodes:
    # 1D display
    return SpectrumView1d(project, wrappedData)
  else:
    # ND display
    return SpectrumViewNd(project, wrappedData)

# Connections to parents:
SpectrumDisplay._childClasses.append(SpectrumView)
SpectrumView._factoryFunction = staticmethod(_factoryFunction)

# Notifiers:
className = ApiSpectrumView._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':SpectrumView._factoryFunction}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
