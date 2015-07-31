"""GUI SpectrumDisplay class

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
from ccpn import NmrResidue
from ccpn import Spectrum
from ccpnmr import Task
from ccpnmr import Window
from ccpncore.api.ccpnmr.gui.Task import SpectrumDisplay as ApiSpectrumDisplay
from ccpncore.api.ccpnmr.gui.Task import BoundDisplay as ApiBoundDisplay
from ccpncore.api.ccpnmr.gui.Task import FreeDisplay as ApiFreeDisplay
from ccpncore.util import Common as commonUtil
from ccpncore.lib.spectrum import Spectrum as libSpectrum
from ccpnmrcore.modules.GuiSpectrumDisplay import GuiSpectrumDisplay
from ccpnmrcore.modules.GuiStripDisplayNd import GuiStripDisplayNd
from ccpnmrcore.modules.GuiStripDisplay1d import GuiStripDisplay1d


# list1 = [GuiSpectrumDisplay,AbstractWrapperObject]
#
# for item in list1:
#   print(item, type(item))
#   if hasattr(item, '__metaclass__'):
#     print(item, item.__metaclass__)
class SpectrumDisplay(GuiSpectrumDisplay, AbstractWrapperObject):
  """Spectrum display for 1D or nD spectrum"""
  
  #: Short class name, for PID.
  shortClassName = 'GD'
  # Attribute it necessary as subclasses must use superclass className
  className = 'SpectrumDisplay'

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectrumDisplays'
  #: List of child classes.
  _childClasses = []

  # CCPN properties  
  @property
  def apiSpectrumDisplay(self) -> ApiSpectrumDisplay:
    """ CCPN SpectrumDisplay matching SpectrumDisplay"""
    return self._wrappedData

  @property
  def name(self) -> str:
    """SpectrumDisplay name"""
    return self._wrappedData.name
    
  @property
  def _parent(self) -> Task:
    """Task containing spectrumDisplay."""
    return self._project._data2Obj.get(self._wrappedData.guiTask)

  task = _parent

  @property
  def stripDirection(self) -> str:
    """Strip axis direction ('X', 'Y', None) - None only for non-strip plots"""
    return self._wrappedData.stripDirection

  @property
  def stripCount(self) -> str:
    """Number of strips"""
    return self._wrappedData.stripCount

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

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
  def window(self) -> Window:
    """Gui window showing SpectrumDisplay"""
    return self._project._data2Obj.get(self._wrappedData.window)

  @window.setter
  def window(self, value:Window):
    value = self.getById(value) if isinstance(value, str) else value
    self._wrappedData.window = value and value._wrappedData

  @property
  def nmrResidue(self) -> NmrResidue:
    """NmrResidue attached to SpectrumDisplay"""
    return  self._project._data2Obj.get(self._wrappedData.resonanceGroup)

  @nmrResidue.setter
  def nmrResidue(self, value:NmrResidue):
    value = self.getById(value) if isinstance(value, str) else value
    self._wrappedData.resonanceGroup = value and value._wrappedData

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
  def orderedStrips(self) -> tuple:
    """Strips in displayed order """
    ff = self._project._data2Obj.get
    return tuple(ff(x) for x in self._wrappedData.orderedStrips)

  @orderedStrips.setter
  def orderedStrips(self, value:Sequence):
    value = [self.getById(x) if isinstance(x, str) else x for x in value]
    self._wrappedData.orderedStrips = tuple(x._wrappedData for x in value)

  @property
  def positions(self) -> (float,):
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
  def _getAllWrappedData(cls, parent:Task)-> list:
    """get wrappedData (ccp.gui.Module) for all SpectrumDisplay children of parent Task"""
    return [x for x in parent._wrappedData.sortedModules()
            if isinstance(x, ApiSpectrumDisplay)]

  # CCPN functions
  def resetAxisOrder(self):
    """Reset display to original axis order"""
    self._wrappedData.resetAxisOrder()

  def findAxis(self, axisCode):
    """Reset display to original axis order"""
    return self._project._data2Obj.get(self._wrappedData.findAxis(axisCode))

  def displaySpectrum(self, spectrum, axisOrder:(str,)=()):
    """Display additional spectrum, with spectrum axes ordered according ton axisOrder
    """
    spectrum = self.getById(spectrum) if isinstance(spectrum, str) else spectrum
    self.strips[0].displaySpectrum(spectrum, axisOrder=axisOrder)

# Window.spectrumDisplays property
def _getSpectrumDisplays(window:Window):
  ll = [x for x in window._wrappedData.sortedModules() if isinstance(x, ApiSpectrumDisplay)]
  return tuple(window._project._data2Obj[x] for x in ll)
Window.spectrumDisplays = property(_getSpectrumDisplays, None, None,
                                   "SpectrumDisplays shown in Window")

def newSpectrumDisplay(parent:Task, axisCodes:(str,), stripDirection:str='Y',
                       name:str=None, window:Window=None, comment:str=None,
                       independentStrips=False, nmrResidue=None):

  # NBNB TBD recheck after classes are done

  # # Map to determine display type
  # displayTypeMap = {
  #   (True, True,False):('newDisplay1d','newStrip1d'),
  #   (True, False,False):('newStripDisplay1d','newStrip1d'),
  #   (False, True,False):('newDisplayNd','newStripNd'),
  #   (False, False,False):('newStripDisplayNd','newStripNd'),
  #   (False, False,True):('newFreeStripDisplayNd','newFreeStripNd'),
  #   (True, False,True):('newFreeStripDisplay1d','newFreeStrip1d'),
  # }

  window = parent.getById(window) if isinstance(window, str) else window
  nmrResidue = parent.getById(nmrResidue) if isinstance(nmrResidue, str) else nmrResidue

  apiTask = parent._wrappedData

  if len(axisCodes) <2:
    raise ValueError("New SpectrumDisplay must have at least two axisCodes")

  # # set display type discriminator and get display types
  # mapTuple = (
  #   axisCodes[1] == 'intensity',   # 1d display
  #   stripDirection is None,        # single=pane display
  #   bool(independentStrips)        # free-strip display
  # )
  # tt = displayTypeMap.get(mapTuple)
  # if tt is None:
  #   raise ValueError("stripDirection must be set if independentStrips is True")
  # else:
  #   newDisplayFunc, newStripFunc = tt

  # set parameters for display
  window = window or apiTask.sortedWindows()[0]
  displayPars = dict(
    stripDirection=stripDirection, window=window,
    details=comment, resonanceGroup=nmrResidue and nmrResidue._wrappedData
  )
  # Add name, setting and insuring uniqueness if necessary
  if name is None:
    if 'intensity' in axisCodes:
      name = ''.join(['1D:', axisCodes[0]] + list(axisCodes[2:]))
    else:
      name = ''.join([str(x) for x in axisCodes])
  while apiTask.findFirstModule(name=name):
    name = commonUtil.incrementName(name)
  displayPars['name'] = name

  # Create SpectrumDisplay
  if independentStrips:
    # Create FreeStripDisplay
    apiSpectrumDisplay = apiTask.newFreeDisplay(**displayPars)
  else:
    # Create Boundstrip/Nostrip display and first strip
    displayPars['axisCodes'] = displayPars['axisOrder'] = axisCodes
    apiSpectrumDisplay = apiTask.newBoundDisplay(**displayPars)

  # Create axes
    for ii, code in enumerate(axisCodes):
      # if (ii == 0 and stripDirection == 'X' or ii == 1 and stripDirection == 'Y' or
      #    not stripDirection):
      # Reactivate this code if we reintroduce non-strip displays (stripDirection == None)
      if (ii == 0 and stripDirection == 'X' or ii == 1 and stripDirection == 'Y'):
        stripSerial = 0
      else:
        stripSerial = 1

      if code[0].isupper():
        apiSpectrumDisplay.newFrequencyAxis(code=code, stripSerial=stripSerial)
      elif code == 'intensity':
        apiSpectrumDisplay.newIntensityAxis(code=code, stripSerial=stripSerial)
      elif code.startswith('fid'):
        apiSpectrumDisplay.newFidAxis(code=code, stripSerial=stripSerial)
      else:
        apiSpectrumDisplay.newSampledAxis(code=code, stripSerial=stripSerial)

  # Create first strip
  if independentStrips:
    apiStrip = apiSpectrumDisplay.newFreeStrip(axisCodes=axisCodes, axisOrder=axisCodes)
  else:
    apiStrip = apiSpectrumDisplay.newBoundStrip()
  #
  return parent._project._data2Obj.get(apiSpectrumDisplay)



# CCPN functions
def _createSpectrumDisplay(window, spectrum:Spectrum, displayAxisCodes:Sequence=(),
                          axisOrder:Sequence=(), name:str=None, positions:Sequence=(),
                          widths:Sequence=(), units:Sequence=(),
                          stripAxis:str='Y', is1d:bool=False,
                          independentStrips:bool=False):

  """
  :param \*str, displayAxisCodes: display axis codes to use in display order - default to spectrum axisCodes in heuristic order
  :param \*str axisOrder: spectrum axis codes in display order - default to spectrum axisCodes in heuristic order
  :param \*float positions: axis positions in order - default to heuristic
  :param \*float widths: axis widths in order - default to heuristic
  :param \*str units: axis units in display order - default to heuristic
  :param str stripAxis: if 'X' or 'Y' set strip axis
  :param bool is1d: If True, or spectrum passed in is 1D, do 1D display
  :param bool independentStrips: if True do freeStrip display.
  """

  spectrum = window.getById(spectrum) if isinstance(spectrum, str) else spectrum

  dataSource = spectrum._wrappedData

  task = window.task
  if task is None:
    raise ValueError("Window %s is not attached to any Task" % window)

  spectrumAxisCodes = spectrum.axisCodes

  mapIndices = ()
  if axisOrder:
    mapIndices = libSpectrum.axisCodeMapIndices(spectrumAxisCodes, axisOrder)
    if displayAxisCodes:
      if not libSpectrum.doAxisCodesMatch(axisOrder, displayAxisCodes):
        raise ValueError("AxisOrder %s do not match display axisCodes %s"
                         % (axisOrder, displayAxisCodes))
    else:
      displayAxisCodes = axisOrder
  elif displayAxisCodes:
    mapIndices = libSpectrum.axisCodeMapIndices(spectrumAxisCodes, displayAxisCodes)
  else:
    displayAxisCodes = list(spectrumAxisCodes)
    mapIndices = list(range(dataSource.numDim))
    if is1d:
      displayAxisCodes.insert(1, 'intensity')
      mapIndices.insert(1,None)

  # Make DataDim ordering
  sortedDataDims = dataSource.sortedDataDims()
  orderedDataDims = []
  for index in mapIndices:
    if index is None:
      orderedDataDims.append(None)
    else:
      orderedDataDims.append(sortedDataDims[index])

  # Make dimensionOrdering
  dimensionOrdering = [(0 if x is None else x.dim) for x in orderedDataDims]

  # Add intensity dimension for 1D if necessary
  if dataSource.numDim == 1 and len(displayAxisCodes) ==1:
    displayAxisCodes.append('intensity')
    dimensionOrdering.append(0)

  #
  display = task.newSpectrumDisplay(axisCodes=displayAxisCodes,stripDirection=stripAxis,
                                    independentStrips=independentStrips,
                                    name=name)

  # Set unit, position and width
  orderedApiAxes = display._wrappedData.orderedAxes
  for ii, dataDim in enumerate(orderedDataDims):

    if dataDim is not None:
      # Set values only if we have a spectrum axis

      # Get unit, position and width
      dataDimRef = dataDim.primaryDataDimRef
      if dataDimRef:
        # This is a FreqDataDim
        unit = dataDimRef.expDimRef.unit
        position = dataDimRef.pointToValue(1) - dataDimRef.spectralWidth/2
        if ii < 2:
          width = dataDimRef.spectralWidth
        else:
          width = dataDimRef.valuePerPoint

      elif dataDim.className == 'SampledDataDim':
        unit = dataDim.unit
        width = len(dataDim.pointValues)
        position = 1 + width // 2
        if ii >= 2:
          width = 1
        # NBNB TBD this may not work, once we implement sampled axes

      else:
        # This is a FidDataDim
        unit = dataDim.unit
        width = dataDim.maxValue - dataDim.firstValue
        position = width / 2
        if ii >= 2:
          width = dataDim.valuePerPoint

      # Set values
      apiAxis = orderedApiAxes[ii]
      apiAxis.unit = unit
      apiAxis.position = position
      apiAxis.width = width
  # Make spectrumView
  stripSerial = 1 if independentStrips else 0
  display._wrappedData.newSpectrumView(spectrumName=dataSource.name,
                                       stripSerial=stripSerial,dataSource=dataSource,
                                       dimensionOrdering=dimensionOrdering)
  return display

# Connections to parents:
Task._childClasses.append(SpectrumDisplay)
Task.newSpectrumDisplay = newSpectrumDisplay

Window.createSpectrumDisplay = _createSpectrumDisplay


# Define subtypes and factory function
class StripDisplay1d(GuiStripDisplay1d, SpectrumDisplay):
  """1D bound display"""

  def __init__(self, project:Project, wrappedData:ApiBoundDisplay):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiStripDisplay1d.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """short form of name, corrected to use for id"""
    return self._wrappedData.name


class StripDisplayNd(GuiStripDisplayNd, SpectrumDisplay):
  """ND bound display"""

  def __init__(self, project:Project, wrappedData:ApiBoundDisplay):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiStripDisplayNd.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """short form of name, corrected to use for id"""
    return self._wrappedData.name

def _factoryFunction(project:Project, wrappedData:ApiSpectrumDisplay) -> SpectrumDisplay:
  """create SpectrumDisplay, dispatching to subtype depending on wrappedData"""
  if wrappedData.stripType == 'Bound':
    if wrappedData.is1d:
      return StripDisplay1d(project, wrappedData)
    else:
      return StripDisplayNd(project, wrappedData)
  else:
    raise ValueError("Attempt to make SpectrumDisplay from illegal object type: %s"
    % wrappedData)


SpectrumDisplay._factoryFunction = staticmethod(_factoryFunction)

# Drag-n-drop functions:
SpectrumDisplay.processSpectrum = SpectrumDisplay.displaySpectrum

# Notifiers:
className = ApiSpectrumDisplay._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':SpectrumDisplay._factoryFunction}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
