"""GUI window class

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
from collections import namedtuple

from ccpn import AbstractWrapperObject
from ccpn import Project
from ccpnmr import Task
from ccpncore.api.ccpnmr.gui.Task import Mark as ApiMark

RulerData = namedtuple('RulerData', ['axisCode', 'position', 'unit', 'label'])


class Mark(AbstractWrapperObject):
  """GUI Mark, a set of axiscode,position rulers or lines"""
  
  #: Short class name, for PID.
  shortClassName = 'GM'

  #: Name of plural link to instances of class
  _pluralLinkName = 'marks'
  
  #: List of child classes.
  _childClasses = []

  # CCPN properties  
  @property
  def apiMark(self) -> ApiMark:
    """ CCPN Mark matching Mark"""
    return self._wrappedData

  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number, key attribute for Peak"""
    return self._wrappedData.serial

  @property
  def _parent(self) -> Task:
    """Task containing Mark."""
    return  self._project._data2Obj[self._wrappedData.guiTask]

  @property
  def colour(self) -> str:
    """Mark colour"""
    return self._wrappedData.colour

  @colour.setter
  def colour(self, value:Sequence):
    self._wrappedData.colour = value

  @property
  def style(self) -> str:
    """Mark drawing style. Defaults to 'simple'"""
    return self._wrappedData.style

  @style.setter
  def style(self, value:str):
    self._wrappedData.style = value

  @property
  def positions(self) -> tuple:
    """Mark position in  float ppm (or other relevant unit) for each ruler making up the mark."""
    return tuple(x.position for x in self._wrappedData.sortedRulers())

  @positions.setter
  def positions(self,value:Sequence):
    for ii,ruler in enumerate(self._wrappedData.sortedRulers()):
      ruler.position = value[ii]

  @property
  def axisCodes(self) -> tuple:
    """AxisCode (string) for each ruler making up the mark."""
    return tuple(x.axisCode for x in self._wrappedData.sortedRulers())

  @axisCodes.setter
  def axisCodes(self,value:Sequence):
    for ii,ruler in enumerate(self._wrappedData.sortedRulers()):
      ruler.axisCode = value[ii]

  @property
  def units(self) -> tuple:
    """Unit (string, default is ppm) for each ruler making up the mark."""
    return tuple(x.unit for x in self._wrappedData.sortedRulers())

  @units.setter
  def units(self,value:Sequence):
    for ii,ruler in enumerate(self._wrappedData.sortedRulers()):
      ruler.unit = value[ii]

  @property
  def labels(self) -> tuple:
    """Optional label (string) for each ruler making up the mark."""
    return tuple(x.label for x in self._wrappedData.sortedRulers())

  @labels.setter
  def labels(self,value:Sequence):
    for ii,ruler in enumerate(self._wrappedData.sortedRulers()):
      ruler.label = value[ii]

  @property
  def rulerData(self) -> tuple:
    """tuple of RulerData ('axisCode', 'position', 'unit', 'label') for the lines in the Mark"""
    return tuple(RulerData(getattr(x, tag) for tag in RulerData._fields)
                 for x in self._wrappedData.sortedRulers())

  def newLine(self, position:float, axisCode:str, unit:str='ppm', label:str=None):
    """Add an extra line to the mark."""
    self.newRuler(position=position, axisCode=axisCode, unit=unit, label=label)

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Task)-> list:
    """get wrappedData (ccp.gui.windows) for all Window children of parent NmrProject.windowStore"""

    return parent.sortedMarks()


def newMark(parent:Task, colour:str, positions:Sequence, axisCodes:Sequence, style:str='simple',
            units:Sequence=(), labels:Sequence=()) -> Mark:
  """Create new child Mark

  :param str colour: Mark colour
  :param tuple/list positions: Position in unit (default ppm) of all lines in the mark
  :param tuple/list axisCodes: Axis codes for all lines in the mark
  :param str style: Mark drawing style (dashed line etc.) default: full line ('simple')
  :param tuple/list units: Axis units for all lines in the mark, Default: all ppm
  :param tuple/list labels: Ruler labels for all lines in the mark. Default: None"""

  apiMark = parent._wrappedData.newMark(colour=colour, style=style)

  for ii,position in enumerate(positions):
    apiRuler = apiMark.newRuler(position=position, axisCode=axisCodes[ii])
    if units:
      apiRuler.unit = units[ii]
    if labels:
      apiRuler.label = labels[ii]

  return parent._project._data2Obj.get(apiMark)


def newSimpleMark(parent:Task, colour:str, position:float, axisCode:str, style:str='simple',
            unit:str='ppm', label:str=None) -> Mark:
  """Create new child Mark with a single line

  :param str colour: Mark colour
  :param tuple/list position: Position in unit (default ppm)
  :param tuple/list axisCode: Axis code
  :param str style: Mark drawing style (dashed line etc.) default: full line ('simple')
  :param tuple/list unit: Axis unit. Default: all ppm
  :param tuple/list label: Line label. Default: None"""

  apiMark = Task._wrappedData.newMark(colour=colour, style=style)
  apiMark.newRuler(position=position, axisCode=axisCode, unit=unit, label=label)

  return parent._project._data2Obj.get(apiMark)

# Connections to parents:
Task._childClasses.append(Mark)
Task.newMark = newMark
Task.newSimpleMark = newSimpleMark


# Notifiers:
className = ApiMark._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Mark}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
