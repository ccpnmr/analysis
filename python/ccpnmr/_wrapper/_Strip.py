"""GUI Display Strip class

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
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
from ccpncore.api.ccpnmr.gui.Task import Strip as ApiStrip
from ccpncore.api.ccpnmr.gui.Task import Strip1d as ApiStrip1d
from ccpncore.api.ccpnmr.gui.Task import StripNd as ApiStripNd
from ccpnmrcore.modules.GuiStrip import GuiStrip
from ccpnmrcore.modules.GuiStrip1d import GuiStrip1d
from ccpnmrcore.modules.GuiStripNd import GuiStripNd


class Strip(GuiStrip, AbstractWrapperObject):
  """Display Strip for 1D or nD spectrum"""
  
  #: Short class name, for PID.
  shortClassName = 'GS'

  #: Name of plural link to instances of class
  _pluralLinkName = 'strips'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def apiStrip(self) -> ApiStrip:
    """ CCPN Strip matching Strip"""
    return self._wrappedData

  @property
  def serial(self) -> int:
    """serial number, key attribute for Strip"""
    return self._wrappedData.serial

    
  @property
  def _parent(self) -> SpectrumDisplay:
    """Parent (containing) object."""
    return self._project._data2Obj.get(self._wrappedData.spectrumDisplay)


  @property
  def axisCodes(self) -> tuple:
    """Fixed string Axis codes in original display order (X, Y, Z1, Z2, ...)"""
    return self._wrappedData.axisCodes

  @property
  def axisOrder(self) -> tuple:
    """String Axis codes in display order (X, Y, Z1, Z2, ...), determine axis display order"""
    return self._wrappedData.axisOrder

  @axisOrder.setter
  def axisOrder(self, value:Sequence):
    self._wrappedData.axisOrder = value

  @property
  def orderedAxes(self) -> tuple:
    """Axes in display order (X, Y, Z1, Z2, ...) """
    ff = self._project._data2Obj.get
    return tuple(ff(x) for x in self._wrappedData.orderedAxes)

  @orderedAxes.setter
  def orderedAxes(self, value:Sequence):
    self._wrappedData.orderedAxes = tuple(x._wrappedData for x in value)

  @property
  def positions(self) -> tuple:
    """Axis centre positions, in display order"""
    return self._wrappedData.positions

  @positions.setter
  def positions(self, value):
    self._wrappedData.positions = value

  @property
  def widths(self) -> tuple:
    """Axis display widths, in display order"""
    return self._wrappedData.widths

  @widths.setter
  def widths(self, value):
    self._wrappedData.widths = value

  @property
  def units(self) -> tuple:
    """Axis units, in display order"""
    return self._wrappedData.units

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:SpectrumDisplay)-> list:
    """get wrappedData (ccp.gui.Strip) in serial number order"""
    return parent._wrappedData.sortedStrips()

  def delete(self):
    """Overrides normal delete"""
    ccpnStrip = self._wrappedData
    if len(ccpnStrip.spectrumDisplay.strips) > 1:

      ccpnStrip.delete()
    else:
      raise  ValueError("The last strip in a display cannot be deleted")

  #CCPN functions
  def clone(self) -> Strip:
    """create new strip that duplicates this one, appending it at the end"""
    return self._project._data2Obj.get(self._wrappedData.clone())

  def moveTo(self, newIndex:int):
    """Move strip to index newIndex in orderedStrips"""
    self._wrappedData.moveTo(newIndex)

  def resetAxisOrder(self):
    """Reset display to original axis order"""
    self._wrappedData.resetAxisOrder()

  def findAxis(self, axisCode):
    """Reset display to original axis order"""
    return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))


# Connections to parents:
SpectrumDisplay._childClasses.append(Strip)

# We should NOT have any newStrip functions, except possibly for FreeStrips

# Define subtypes and factory function
class Strip1d(GuiStrip1d, Strip):
  """1D strip"""

  def __init__(self, project:Project, wrappedData:ApiStrip1d):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiStrip1d.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

class StripNd(GuiStripNd, Strip):
  """ND strip """

  def __init__(self, project:Project, wrappedData:ApiStripNd):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiStripNd.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

def _factoryFunction(project:Project, wrappedData:ApiStrip) -> Strip:
  """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
  if isinstance(wrappedData, ApiStripNd):
    return StripNd(project, wrappedData)
  elif isinstance(wrappedData, ApiStrip1d):
    return Strip1d(project, wrappedData)
  else:
    raise ValueError("Attempt to make SpectrumDisplay from illegal object type: %s"
    % wrappedData)

Strip._factoryFunction = staticmethod(_factoryFunction)

# Notifiers:
className = ApiStrip._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Strip._factoryFunction}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
