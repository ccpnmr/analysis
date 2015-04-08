"""GUI Display Strip class

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
from collections.abc import Sequence

from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpn import Spectrum
from ccpnmr._wrapper._SpectrumDisplay import SpectrumDisplay
from ccpncore.api.ccpnmr.gui.Task import Strip as ApiStrip
from ccpncore.api.ccpnmr.gui.Task import Strip1d as ApiStrip1d
from ccpncore.api.ccpnmr.gui.Task import StripNd as ApiStripNd
from ccpnmrcore.modules.GuiStrip import GuiStrip
from ccpnmrcore.modules.GuiStrip1d import GuiStrip1d
from ccpnmrcore.modules.GuiStripNd import GuiStripNd
from ccpncore.lib.spectrum import Spectrum as libSpectrum


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
    """SpectrumDisplay containing strip."""
    return self._project._data2Obj.get(self._wrappedData.spectrumDisplay)

  spectrumDisplay = _parent

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
    value = [self.getById(x) if isinstance(x, str) else x for x in value]
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
    n = len(ccpnStrip.spectrumDisplay.strips)
    if n > 1:
      index = ccpnStrip.index
      spectrumDisplay = self.spectrumDisplay
      layout = spectrumDisplay.stripFrame.layout()
      if layout: # should always be the case but play safe
        # remove the item for this strip from the layout
        # and shuffle "higher" items down in the layout
        # (by removing them and then adding them back in)
        items = []
        if spectrumDisplay.stripDirection == 'Y':
          for m in range(index, n):
            item = layout.itemAtPosition(0, m)
            if m > index:
              items.append(item)
            layout.removeItem(item)
          for m, item in enumerate(items):
            layout.addItem(item, 0, m+index)
        elif spectrumDisplay.stripDirection == 'X':
          for m in range(index, n):
            item = layout.itemAtPosition(m, 0)
            if m > index:
              items.append(item)
            layout.removeItem(item)
          for m, item in enumerate(items):
            layout.addItem(item, m+index, 0)

      ccpnStrip.delete()
      #self.deleteLater()  # Qt call, is this needed???
      
    else:
      raise  ValueError("The last strip in a display cannot be deleted")

  #CCPN functions
  def clone(self):
    """create new strip that duplicates this one, appending it at the end"""
    newStrip = self._project._data2Obj.get(self._wrappedData.clone())

    # NBNB TBD Why is this necessary? Presumably it should be the same width as the source?
    newStrip.setMinimumWidth(200)
    
    return newStrip

  def moveTo(self, newIndex:int):
    """Move strip to index newIndex in orderedStrips"""
    
    currentIndex = self._wrappedData.index
    if currentIndex == newIndex:
      return
      
    # management of API objects
    self._wrappedData.moveTo(newIndex)
    
    # management of Qt layout
    # TBD: need to soup up below with extra loop when have tiles
    spectrumDisplay = self.spectrumDisplay
    layout = spectrumDisplay.stripFrame.layout()
    if not layout: # should always exist but play safe:
      return
      
    items = []
    items2 = []
    items3 = []
    if spectrumDisplay.stripDirection == 'Y':
      if currentIndex < newIndex:
        for n in range(currentIndex, newIndex+1):
          item = layout.itemAtPosition(0, n)
          items.append(item)
          layout.removeItem(item)
          item = layout.itemAtPosition(1, n)
          items2.append(item)
          layout.removeItem(item)
          item = layout.itemAtPosition(2, n)
          items3.append(item)
          layout.removeItem(item)
        items = [items[-1]] + items[:-1]
        items2 = [items2[-1]] + items2[:-1]
        items3 = [items3[-1]] + items3[:-1]
        for m, item in enumerate(items):
          layout.addItem(item, 0, m+newIndex, )
        for m, item in enumerate(items2):
          layout.addItem(item, 1, m+newIndex)
        for m, item in enumerate(items3):
          layout.addItem(item, 2, m+newIndex)
      else:
        for n in range(newIndex, currentIndex+1):
          item = layout.itemAtPosition(0, n)
          items.append(item)
          layout.removeItem(item)
          item = layout.itemAtPosition(1, n)
          items2.append(item)
          layout.removeItem(item)
          item = layout.itemAtPosition(2, n)
          items3.append(item)
          layout.removeItem(item)
        items = [items[-1]] + items[:-1]
        items2 = [items2[-1]] + items2[:-1]
        items3 = [items3[-1]] + items3[:-1]
        for m, item in enumerate(items):
          layout.addItem(item, 0, m+newIndex, )
        for m, item in enumerate(items2):
          layout.addItem(item, 1, m+newIndex)
        for m, item in enumerate(items3):
          layout.addItem(item, 2, m+newIndex)

    elif spectrumDisplay.stripDirection == 'X':
      if currentIndex < newIndex:
        for n in range(currentIndex, newIndex+1):
          item = layout.itemAtPosition(n, 0)
          items.append(item)
          layout.removeItem(item)
        items = items[1:] + [items[0]]
        for m, item in enumerate(items):
          layout.addItem(item, m+currentIndex, 0)
      else:
        for n in range(newIndex, currentIndex+1):
          item = layout.itemAtPosition(n, 0)
          items.append(item)
          layout.removeItem(item)
        items = [items[-1]] + items[:-1]
        for m, item in enumerate(items):
          layout.addItem(item, m+newIndex, 0)

  def resetAxisOrder(self):
    """Reset display to original axis order"""
    self._wrappedData.resetAxisOrder()

  def findAxis(self, axisCode):
    """Reset display to original axis order"""
    return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

  def displaySpectrum(self, spectrum:Spectrum, axisOrder:Sequence=()):

    """
    Display additional spectrum on strip, with spectrum axes ordered according to axisOrder
    """
    spectrum = self.getById(spectrum) if isinstance(spectrum, str) else spectrum
    dataSource = spectrum._wrappedData
    apiStrip = self._wrappedData
    if apiStrip.findFirstSpectrumView(dataSource=dataSource) is not None:
      return

    displayAxisCodes = apiStrip.axisCodes

    # make axis mapping indices
    if axisOrder and axisOrder != displayAxisCodes:
      # Map axes to axisOrder, and remap to original setting
      ll = libSpectrum.axisCodeMapIndices(spectrum.axisCodes, axisOrder)
      mapIndices = [ll[axisOrder.index(x)] for x in displayAxisCodes]
    else:
      # Map axes to original display setting
      mapIndices = libSpectrum.axisCodeMapIndices(spectrum.axisCodes, displayAxisCodes)

    # Make dimensionOrdering
    sortedDataDims = dataSource.sortedDataDims()
    dimensionOrdering = []
    for index in mapIndices:
      if index is None:
        dimensionOrdering.append(0)
      else:
        dimensionOrdering.append(sortedDataDims[index].dim)

    # Set spectrumSerial
    if 'Free' in apiStrip.className:
      # Independent strips
      stripSerial = apiStrip.serial
    else:
      stripSerial = 0

    # Make spectrumView
    obj = apiStrip.spectrumDisplay.newSpectrumView(spectrumName=dataSource.name,
                                                    stripSerial=stripSerial, dataSource=dataSource,
                                                   dimensionOrdering=dimensionOrdering)
    return self._project._data2Obj[obj]

def copyStrip(spectrumDisplay:SpectrumDisplay, strip:Strip, newIndex=None):
  """Make copy of strip in SpectrumDisplay, at position newIndex - or rightmost"""

  strip = spectrumDisplay.getById(strip) if isinstance(strip, str) else strip

  if strip.spectrumDisplay is spectrumDisplay:
    # Within same display. Not that useful, but harmless
    newStrip = strip.clone()
    if newIndex is not None:
      newStrip.moveTo(newIndex)

  else:
    mapIndices = libSpectrum.axisCodeMapIndices(strip.axisOrder, spectrumDisplay.axisOrder)
    if mapIndices is None:
      raise ValueError("Strip %s not compatible with window %s" % (strip.pid, spectrumDisplay.pid))
    else:
      positions = strip.positions
      widths = strip.widths
      newStrip = spectrumDisplay.orderedStrips[0].clone()
      if newIndex is not None:
        newStrip.moveTo(newIndex)
      for ii,axis in enumerate(newStrip.orderedAxes):
        ind = mapIndices[ii]
        if ind is not None and axis._wrappedData.stripSerial != 0:
          # Override if there is a mapping and axis is not shared for all strips
          axis.position = positions[ind]
          axis.widths = widths[ind]

SpectrumDisplay.copyStrip = copyStrip

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

def _factoryFunction(project:Project, wrappedData:ApiStrip):
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
