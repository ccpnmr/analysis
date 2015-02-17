"""GUI window class

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
from ccpn._wrapper._Spectrum import Spectrum
from ccpncore.api.ccpnmr.gui.Window import Window as ApiWindow
from ccpnmrcore.modules.GuiWindow import GuiWindow
from ccpnmrcore.modules.GuiMainWindow import GuiMainWindow
from ccpncore.lib import Spectrum as libSpectrum
from ccpncore.lib import pid as Pid


class Window(AbstractWrapperObject):
  """GUI window, corresponds to OS window"""
  
  #: Short class name, for PID.
  shortClassName = 'GW'

  #: Name of plural link to instances of class
  _pluralLinkName = 'guiWindows'
  
  #: List of child classes.
  _childClasses = []

  # CCPN properties  
  @property
  def apiWindow(self) -> ApiWindow:
    """ CCPN Window matching Window"""
    return self._wrappedData

  @property
  def title(self) -> str:
    """Window display title"""
    return self._wrappedData.title
    
  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  @property
  def position(self) -> tuple:
    """Window X,Y position in integer pixels"""
    return self._wrappedData.position

  @position.setter
  def position(self, value:Sequence):
    self._wrappedData.position = value
  
  @property
  def size(self) -> tuple:
    """Window X,Y size in integer pixels"""
    return self._wrappedData.size

  @size.setter
  def size(self, value:Sequence):
    self._wrappedData.size = value

  @property
  def task(self):
    """Task shown in Window."""
    return self._project._data2Obj.get(self._wrappedData.guiTask)

  @task.setter
  def task(self, value):
    self._wrappedData.guiTask = value and value._wrappedData

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (ccp.gui.windows) for all Window children of parent NmrProject.windowStore"""
    windowStore = parent._wrappedData.windowStore

    if windowStore is None:
      return []
    else:
      return windowStore.sortedWindows()


  # CCPN functions
  def createSpectrumDisplay(self, spectrum:Spectrum, displayAxisCodes:Sequence=(),
                            axisOrder:Sequence=(), name:str=None, positions:Sequence=(),
                            widths:Sequence=(), units:Sequence=(),
                            stripAxis:str=None, contour:bool=True,
                            independentStrips:bool=False, gridCell:Sequence=(1,1),
                            gridSpan:Sequence=(1,1)):

    """
    displayAxisCodes: display axis codes to use in display order - default to spectrum axisCodes in heuristic order
    axisOrder: spectrum axis codes in display order - default to spectrum axisCodes in heuristic order
    positions: axis positions in order - default to heuristic
    widths: axis widths in order - default to heuristic
    units: axis units in display order - default to heuristic
    stripAxis: if 'X' or 'Y' set strip axis, if None set to non-strip display
    contour: If False, or spectrum passed in is 1D, do 1D display
    independentStrips: if True do freeStrip display.
    """

    dataSource = spectrum._wrappedData

    task = self.task
    if task is None:
      raise ValueError("Window %s is not attached to any Task" % self)

    params = {
      'stripAxis': stripAxis,
      'contour':contour,
      'independentStrips':independentStrips,
      'name':name,
      'gridSpan':gridSpan,
      'gridCell':gridCell,
    }

    apiAxisCodes = spectrum.axisCodes

    mapIndices = ()
    if axisOrder:
      mapIndices = libSpectrum.axisCodeMapIndices(apiAxisCodes, axisOrder)
      if displayAxisCodes:
        if not libSpectrum.doAxisCodesMatch(axisOrder, displayAxisCodes):
          raise ValueError("AxisOrder %s do not match display axisCodes %s"
                           % (axisOrder, displayAxisCodes))
      else:
        displayAxisCodes = axisOrder
    elif displayAxisCodes:
      mapIndices = libSpectrum.axisCodeMapIndices(apiAxisCodes, displayAxisCodes)
    else:
      displayAxisCodes = list(apiAxisCodes)
      mapIndices = list(range(dataSource.numDims))

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
    display = task.newSpectrumDisplay(axisCodes=displayAxisCodes,stripAxis=stripAxis,
                                      contour=contour, independentStrips=independentStrips,
                                      name=name, gridSpan=gridSpan,gridCell=gridCell)

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
          position = dataDimRef.pointToValue(1) + dataDimRef.spectralWidth/2
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
    display._wrappedData.newSpectrumView(dataSource=dataSource,
                                         stripSerial=stripSerial,
                                         dimensionOrdering=dimensionOrdering)


def newWindow(parent:Project, title:str=None, position:tuple=(), size:tuple=()) -> Window:
  """Create new child Window

  :param str title: window  title (optional, defaults to 'Wn' n positive integer
  :param tuple size: x,y size for new window in integer pixels
  :param tuple position: x,y position for new window in integer pixels"""

  windowStore = parent.nmrProject.windowStore

  newApiWindow = windowStore.newGuiWindow(title=title)
  if position:
    newApiWindow.position = position
  if size:
    newApiWindow.size = size

  return parent._data2Obj.get(newApiWindow)

# Connections to parents:
Project._childClasses.append(Window)
Project.newWindow = newWindow


# Define subtypes and factory function
class MainWindow(Window, GuiMainWindow):
  """GUI main window, corresponds to OS window"""

  def __init__(self, project:Project, wrappedData:object):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiMainWindow.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """short form of name, corrected to use for id"""
    return self._wrappedData.title.translate(Pid.remapSeparators)


class SideWindow(Window, GuiWindow):
  """GUI side window, corresponds to OS window"""

  def __init__(self, project:Project, wrappedData:object):
    """Local override init for Qt subclass"""
    AbstractWrapperObject. __init__(self, project, wrappedData)
    GuiWindow.__init__(self)

  # put in subclass to make superclass abstract
  @property
  def _key(self) -> str:
    """short form of name, corrected to use for id"""
    return self._wrappedData.title.translate(Pid.remapSeparators)

def _factoryFunction(project:Project, wrappedData:ApiWindow) ->Window:
  """create Window, dispatching to subtype depending on wrappedData"""
  if wrappedData.title == 'Main':
    return MainWindow(project, wrappedData)
  else:
    return SideWindow(project, wrappedData)


Window._factoryFunction = staticmethod(_factoryFunction)

# Notifiers:
className = ApiWindow._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Window._factoryFunction}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
