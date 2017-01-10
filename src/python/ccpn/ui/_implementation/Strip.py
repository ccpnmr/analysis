"""GUI Display Strip class

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
from typing import Sequence, Tuple

from ccpn.util import Common as commonUtil
from ccpn.core.Peak import Peak
from ccpn.core.Spectrum import Spectrum
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.SpectrumDisplay import SpectrumDisplay
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import BoundStrip as ApiBoundStrip


class Strip(AbstractWrapperObject):
  """Display Strip for 1D or nD spectrum"""
  
  #: Short class name, for PID.
  shortClassName = 'GS'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Strip'

  _parentClass = SpectrumDisplay

  #: Name of plural link to instances of class
  _pluralLinkName = 'strips'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiBoundStrip._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiStrip(self) -> ApiBoundStrip:
    """ CCPN Strip matching Strip"""
    return self._wrappedData

  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of Strip, used in Pid and to identify the Strip. """
    return self._wrappedData.serial
    
  @property
  def _parent(self) -> SpectrumDisplay:
    """SpectrumDisplay containing strip."""
    return self._project._data2Obj.get(self._wrappedData.spectrumDisplay)

  spectrumDisplay = _parent

  @property
  def axisCodes(self) ->  Tuple[str, ...]:
    """Fixed string Axis codes in original display order (X, Y, Z1, Z2, ...)"""
    return self._wrappedData.axisCodes

  @property
  def axisOrder(self) ->  Tuple[str, ...]:
    """String Axis codes in display order (X, Y, Z1, Z2, ...), determine axis display order"""
    return self._wrappedData.axisOrder

  @axisOrder.setter
  def axisOrder(self, value:Sequence):
    self._wrappedData.axisOrder = value

  @property
  def positions(self) ->  Tuple[float, ...]:
    """Axis centre positions, in display order"""
    return self._wrappedData.positions

  @positions.setter
  def positions(self, value):
    self._wrappedData.positions = value

  @property
  def widths(self) ->  Tuple[float, ...]:
    """Axis display widths, in display order"""
    return self._wrappedData.widths

  @widths.setter
  def widths(self, value):
    self._wrappedData.widths = value

  @property
  def units(self) ->  Tuple[str, ...]:
    """Axis units, in display order"""
    return self._wrappedData.units

  @property
  def spectra(self) -> Tuple[Spectrum]:
    """The spectra attached to the strip (whether display is currently turned on  or not)"""
    return tuple (x.spectrum for x in self.spectrumViews)

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:SpectrumDisplay)-> list:
    """get wrappedData (ccpnmr.gui.Task.Strip) in serial number order"""
    return parent._wrappedData.sortedStrips()

  def delete(self):
    """Overrides normal delete"""

    # NBNB TODO - should this not be moved to the corresponding GUI class?
    # Is there always a layout, regardless of application?

    # NB - echoing should be done normally, through the delete command

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
        for r in range(layout.rowCount()):
          items = []
          if spectrumDisplay.stripDirection == 'Y':
            for m in range(index, n):
              item = layout.itemAtPosition(r, m)
              if m > index:
                items.append(item)
              layout.removeItem(item)
            for m, item in enumerate(items):
              layout.addItem(item, r, m+index)
          elif spectrumDisplay.stripDirection == 'X':
            for m in range(index, n):
              item = layout.itemAtPosition(m, 0)
              if m > index:
                items.append(item)
              layout.removeItem(item)
            for m, item in enumerate(items):
              layout.addItem(item, m+index, 0)
      self.plotWidget.deleteLater()
      ###self.spinSystemLabel.deleteLater()
      if hasattr(self, 'planeToolbar'):
        self.planeToolbar.deleteLater()
      ccpnStrip.delete()

      #self.deleteLater()  # Qt call, is this needed???
      
    else:
      raise  ValueError("The last strip in a display cannot be deleted")

  #CCPN functions
  def clone(self):
    """create new strip that duplicates this one, appending it at the end"""
    self._startFunctionCommandBlock('clone')
    try:
      newStrip = self._project._data2Obj.get(self._wrappedData.clone())

      # NBNB TODO Why is this necessary? Presumably it should be the same width as the source?
      newStrip.setMinimumWidth(200)
    finally:
      self._project._appBase._endCommandBlock()
    
    return newStrip

  def moveTo(self, newIndex:int):
    """Move strip to index newIndex in orderedStrips"""
    
    currentIndex = self._wrappedData.index
    if currentIndex == newIndex:
      return

    stripCount = self.spectrumDisplay.stripCount

    if newIndex >= stripCount:
      # Put strip at the right, which means newIndex should be stripCount - 1
      if newIndex > stripCount:
        # warning
        self._project._logger.warning(
          "Attempt to copy strip to position %s in display with only %s strips"
          % (newIndex, stripCount))
      newIndex = stripCount - 1

    self._startFunctionCommandBlock('moveTo', newIndex)
    try:
      # management of API objects
      self._wrappedData.moveTo(newIndex)
    finally:
      self._project._appBase._endCommandBlock()

    # NB - no echo blocking below, as none of the layout stuff is modeled (?)

    # NBNB TODO - should the stuff below not be moved to the corresponding GUI class?
    # Is there always a layout, regardless of application?

    # management of Qt layout
    # TBD: need to soup up below with extra loop when have tiles
    spectrumDisplay = self.spectrumDisplay
    layout = spectrumDisplay.stripFrame.layout()
    if not layout: # should always exist but play safe:
      return

    for r in range(layout.rowCount()):
      items = []
      if spectrumDisplay.stripDirection == 'Y':
        if currentIndex < newIndex:
          for n in range(currentIndex, newIndex+1):
            item = layout.itemAtPosition(r, n)
            items.append(item)
            layout.removeItem(item)
          items = items[1:] + [items[0]]
          for m, item in enumerate(items):
            layout.addItem(item, r, m+currentIndex, )
        else:
          for n in range(newIndex, currentIndex+1):
            item = layout.itemAtPosition(r, n)
            items.append(item)
            layout.removeItem(item)
          items = [items[-1]] + items[:-1]
          for m, item in enumerate(items):
            layout.addItem(item, r, m+newIndex, )

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
    self._startFunctionCommandBlock('resetAxisOrder')
    try:
      self._wrappedData.resetAxisOrder()
    finally:
      self._project._appBase._endCommandBlock()


  def findAxis(self, axisCode):
    """Reset display to original axis order"""
    return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

  def displaySpectrum(self, spectrum:Spectrum, axisOrder:Sequence=()):
    """
    Display additional spectrum on strip, with spectrum axes ordered according to axisOrder
    """

    spectrum = self.getByPid(spectrum) if isinstance(spectrum, str) else spectrum

    dataSource = spectrum._wrappedData
    apiStrip = self._wrappedData
    if apiStrip.findFirstSpectrumView(dataSource=dataSource) is not None:
      return

    displayAxisCodes = apiStrip.axisCodes

    # make axis mapping indices
    if axisOrder and axisOrder != displayAxisCodes:
      # Map axes to axisOrder, and remap to original setting
      ll = commonUtil._axisCodeMapIndices(spectrum.axisCodes, axisOrder)
      mapIndices = [ll[axisOrder.index(x)] for x in displayAxisCodes]
    else:
      # Map axes to original display setting
      mapIndices = commonUtil._axisCodeMapIndices(spectrum.axisCodes, displayAxisCodes)

    if mapIndices is None:
      return
      
    # if None in mapIndices[:2]: # make sure that x/y always mapped
    #   return
    if mapIndices[0] is None or mapIndices[1] is None and displayAxisCodes[1] != 'intensity':
      return
      
    if mapIndices.count(None) + spectrum.dimensionCount != len(mapIndices):
      return
      
    # Make dimensionOrdering
    sortedDataDims = dataSource.sortedDataDims()
    dimensionOrdering = []
    for index in mapIndices:
      if index is None:
        dimensionOrdering.append(0)
      else:
        dimensionOrdering.append(sortedDataDims[index].dim)

    # Set stripSerial
    if 'Free' in apiStrip.className:
      # Independent strips
      stripSerial = apiStrip.serial
    else:
      stripSerial = 0


    self._startFunctionCommandBlock('displaySpectrum', spectrum, values=locals(),
                                    defaults={'axisOrder':()})
    try:
      # Make spectrumView
      obj = apiStrip.spectrumDisplay.newSpectrumView(spectrumName=dataSource.name,
                                                     stripSerial=stripSerial, dataSource=dataSource,
                                                     dimensionOrdering=dimensionOrdering)
    finally:
      self._project._appBase._endCommandBlock()
    result =  self._project._data2Obj[apiStrip.findFirstStripSpectrumView(spectrumView=obj)]
    #
    return result

  def peakIsInPlane(self, peak:Peak) -> bool:
    """is peak in currently displayed planes for strip?"""
    apiSpectrumView = self._wrappedData.findFirstSpectrumView(
      dataSource=peak._wrappedData.peakList.dataSource)

    if apiSpectrumView is None:
      return False

    orderedAxes = self.orderedAxes
    for ii,zDataDim in enumerate(apiSpectrumView.orderedDataDims[2:]):
      if zDataDim:
        zPosition = peak.position[zDataDim.dimensionIndex]
        # NBNB W3e do not think this should add anything - the region should be set correctly.
        # RHF, WB
        # zPlaneSize = zDataDim.getDefaultPlaneSize()
        zPlaneSize = 0.
        zRegion = orderedAxes[2+ii].region
        if zPosition < zRegion[0]-zPlaneSize or zPosition > zRegion[1]+zPlaneSize:
          return False
    #
    return True

  def peakIsInFlankingPlane(self, peak:Peak) -> bool:

    """is peak in planes flanking currently displayed planes for strip?"""
    apiSpectrumView = self._wrappedData.findFirstSpectrumView(
      dataSource=peak._wrappedData.peakList.dataSource)

    if apiSpectrumView is None:
      return False

    orderedAxes = self.orderedAxes
    for ii,zDataDim in enumerate(apiSpectrumView.orderedDataDims[2:]):
      if zDataDim:
        zPosition = peak.position[zDataDim.dimensionIndex]
        # NBNB W3e do not think this should add anything - the region should be set correctly.
        # RHF, WB
        # zPlaneSize = zDataDim.getDefaultPlaneSize()
        zRegion = orderedAxes[2+ii].region
        zWidth = orderedAxes[2+ii].width
        if zRegion[0]-zWidth < zPosition < zRegion[0] or zRegion[1] < zPosition < zRegion[1]+zWidth:
          return True

    return False


# newStrip functions
# We should NOT have any newStrip function, except possibly for FreeStrips
def _copyStrip(self:SpectrumDisplay, strip:Strip, newIndex=None) -> Strip:
  """Make copy of strip in self, at position newIndex - or rightmost"""

  strip = self.getByPid(strip) if isinstance(strip, str) else strip

  stripCount = self.stripCount
  if newIndex and newIndex >= stripCount:
    # Put strip at the right, which means newIndex should be None
    if newIndex > stripCount:
      # warning
      self._project._logger.warning(
        "Attempt to copy strip to position %s in display with only %s strips"
        % (newIndex, stripCount))
    newIndex = None

  self._startFunctionCommandBlock('copyStrip', strip, values=locals(), defaults={'newIndex':None},
                                  parName='newStrip')
  try:
    if strip.spectrumDisplay is self:
      # Within same display. Not that useful, but harmless
      newStrip = strip.clone()
      if newIndex is not None:
        newStrip.moveTo(newIndex)

    else:
      mapIndices = commonUtil._axisCodeMapIndices(strip.axisOrder, self.axisOrder)
      if mapIndices is None:
        raise ValueError("Strip %s not compatible with window %s" % (strip.pid, self.pid))
      else:
        positions = strip.positions
        widths = strip.widths
        newStrip = self.orderedStrips[0].clone()
        if newIndex is not None:
          newStrip.moveTo(newIndex)
        for ii,axis in enumerate(newStrip.orderedAxes):
          ind = mapIndices[ii]
          if ind is not None and axis._wrappedData.axis.stripSerial != 0:
            # Override if there is a mapping and axis is not shared for all strips
            axis.position = positions[ind]
            axis.widths = widths[ind]
  finally:
    self._project._appBase._endCommandBlock()
  #
  return newStrip
SpectrumDisplay.copyStrip = _copyStrip
del _copyStrip

# SpectrumDisplay.orderedStrips property
def getter(self) -> Tuple[Strip, ...]:
  ff = self._project._data2Obj.get
  return tuple(ff(x) for x in self._wrappedData.orderedStrips)
def setter(self, value:Sequence):
  value = [self.getByPid(x) if isinstance(x, str) else x for x in value]
  self._wrappedData.orderedStrips = tuple(x._wrappedData for x in value)
SpectrumDisplay.orderedStrips = property(getter, setter, None,
                                         "ccpn.Strips in displayed order ")
del getter
del setter

# Drag-n-drop functions:
Strip.processSpectrum = Strip.displaySpectrum
