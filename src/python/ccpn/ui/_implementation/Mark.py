"""GUI window class

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
import collections
from typing import Sequence, Tuple

from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.Task import Task
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Mark as ApiMark
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import Ruler as ApiRuler


RulerData = collections.namedtuple('RulerData', ['position', 'axisCode', 'unit', 'label'])


class Mark(AbstractWrapperObject):
  """GUI Mark, a set of axiscode,position rulers or lines"""
  
  #: Short class name, for PID.
  shortClassName = 'GM'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Mark'

  _parentClass = Task

  #: Name of plural link to instances of class
  _pluralLinkName = 'marks'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiMark._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiMark(self) -> ApiMark:
    """ CCPN Mark matching Mark"""
    return self._wrappedData

  @property
  def _key(self) -> str:
    """id string - serial number converted to string"""
    return str(self._wrappedData.serial)

  @property
  def serial(self) -> int:
    """serial number of Mark, used in Pid and to identify the Mark. """
    return self._wrappedData.serial

  @property
  def _parent(self) -> Task:
    """Task containing Mark."""
    return  self._project._data2Obj[self._wrappedData.guiTask]

  task = _parent

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
  def positions(self) -> Tuple[float, ...]:
    """Mark position in  float ppm (or other relevant unit) for each ruler making up the mark."""
    return tuple(x.position for x in self._wrappedData.sortedRulers())

  @positions.setter
  def positions(self,value:Sequence):
    for ii,ruler in enumerate(self._wrappedData.sortedRulers()):
      ruler.position = value[ii]

  @property
  def axisCodes(self) -> Tuple[str, ...]:
    """AxisCode (string) for each ruler making up the mark."""
    return tuple(x.axisCode for x in self._wrappedData.sortedRulers())

  @axisCodes.setter
  def axisCodes(self,value:Sequence):
    for ii,ruler in enumerate(self._wrappedData.sortedRulers()):
      ruler.axisCode = value[ii]

  @property
  def units(self) -> Tuple[str, ...]:
    """Unit (string, default is ppm) for each ruler making up the mark."""
    return tuple(x.unit for x in self._wrappedData.sortedRulers())

  @units.setter
  def units(self,value:Sequence):
    for ii,ruler in enumerate(self._wrappedData.sortedRulers()):
      ruler.unit = value[ii]

  @property
  def labels(self) -> Tuple[str, ...]:
    """Optional label (string) for each ruler making up the mark."""
    return tuple(x.label for x in self._wrappedData.sortedRulers())

  @labels.setter
  def labels(self,value:Sequence):
    for ii,ruler in enumerate(self._wrappedData.sortedRulers()):
      ruler.label = value[ii]

  @property
  def rulerData(self) -> tuple:
    """tuple of RulerData ('position', 'axisCode', 'unit', 'label') for the lines in the Mark"""
    return tuple(RulerData(*(getattr(x, tag) for tag in RulerData._fields))
                 for x in self._wrappedData.sortedRulers())

  def newLine(self, position:float, axisCode:str, unit:str='ppm', label:str=None):
    """Add an extra line to the mark."""
    if unit is  None:
      unit = 'ppm'
    defaults = collections.OrderedDict((('unit', 'ppm'), ('label', None)))
    self._startFunctionCommandBlock('newLine', position, axisCode, values=locals(),
                                    defaults=defaults)
    try:
      self._wrappedData.newRuler(position=position, axisCode=axisCode, unit=unit, label=label)
    finally:
      self._project._appBase._endCommandBlock()

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Task)-> list:
    """get wrappedData (ccp.gui.windows) for all Window children of parent NmrProject.windowStore"""

    return parent._wrappedData.sortedMarks()


# newMark functions
def _newMark(self:Task, colour:str, positions:Sequence[float], axisCodes:Sequence,
             style:str='simple', units:Sequence[str]=(), labels:Sequence[str]=()) -> Mark:
  """Create new ccpn.Mark

  :param str colour: Mark colour
  :param tuple/list positions: Position in unit (default ppm) of all lines in the mark
  :param tuple/list axisCodes: Axis codes for all lines in the mark
  :param str style: Mark drawing style (dashed line etc.) default: full line ('simple')
  :param tuple/list units: Axis units for all lines in the mark, Default: all ppm
  :param tuple/list labels: Ruler labels for all lines in the mark. Default: None"""

  defaults = collections.OrderedDict((('style', 'simple'), ('units', ()),
                                     ('labels', ())))

  self._startFunctionCommandBlock('newMark', colour, positions, axisCodes, values=locals(),
                                  defaults=defaults, parName='newMark')
  try:
    apiMark = self._wrappedData.newMark(colour=colour, style=style)

    for ii,position in enumerate(positions):
      dd = {'position':position, 'axisCode':axisCodes[ii]}
      if units:
        unit = units[ii]
        if unit is not None:
         dd['unit'] = unit
      if labels:
        label = labels[ii]
        if label is not None:
         dd['label'] = label
      apiRuler = apiMark.newRuler(**dd)
    #
    result =  self._project._data2Obj.get(apiMark)
  finally:
    self._project._appBase._endCommandBlock()

  return result
Task.newMark = _newMark

def _newSimpleMark(self:Task, colour:str, position:float, axisCode:str, style:str='simple',
            unit:str='ppm', label:str=None) -> Mark:
  """Create new child Mark with a single line

  :param str colour: Mark colour
  :param tuple/list position: Position in unit (default ppm)
  :param tuple/list axisCode: Axis code
  :param str style: Mark drawing style (dashed line etc.) default: full line ('simple')
  :param tuple/list unit: Axis unit. Default: all ppm
  :param tuple/list label: Line label. Default: None"""

  defaults = collections.OrderedDict((('style', 'simple'), ('unit', 'ppm'),
                                     ('label', None)))

  self._startFunctionCommandBlock('newSimpleMark', colour, position, axisCode, values=locals(),
                                  defaults=defaults, parName='newMark')
  try:

    apiMark = self._wrappedData.newMark(colour=colour, style=style)
    if unit is None:
      unit = 'ppm'
    apiMark.newRuler(position=position, axisCode=axisCode, unit=unit, label=label)
    #
    result =  self._project._data2Obj.get(apiMark)
  finally:
    self._project._appBase._endCommandBlock()

  return result


Task.newSimpleMark = _newSimpleMark

# Notifiers:
# Mark changes when rulers are created or deleted
Project._apiNotifiers.extend(
  ( ('_notifyRelatedApiObject', {'pathToObject':'mark', 'action':'change'},
    ApiRuler._metaclass.qualifiedName(), 'postInit'),
    ('_notifyRelatedApiObject', {'pathToObject':'mark', 'action':'change'},
     ApiRuler._metaclass.qualifiedName(), 'preDelete'),
  )
)