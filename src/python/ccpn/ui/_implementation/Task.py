"""GUI Task class

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-05-24 16:28:35 +0100 (Wed, May 24, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================
import typing
import collections

from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.Window import Window
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import GuiTask as ApiGuiTask


class Task(AbstractWrapperObject):
  """GUI task, corresponds to set of interacting modules"""
  
  #: Short class name, for PID.
  shortClassName = 'GT'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Task'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'tasks'
  
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiGuiTask._metaclass.qualifiedName()
  

  # CCPN properties  
  @property
  def _apiGuiTask(self) -> ApiGuiTask:
    """ CCPN GuiTask matching Task"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """local id, of form nameSpace.name"""
    return Pid.createId(self._wrappedData.nameSpace, self._wrappedData.name)

  @property
  def _localCcpnSortKey(self) -> typing.Tuple:
    """Local sorting key, in context of parent."""
    return(self._wrappedData.nameSpace, self._wrappedData.name)

  @property
  def nameSpace(self) -> str:
    """Task nameSpace"""
    return self._wrappedData.nameSpace

  @property
  def name(self) -> str:
    """Task name"""
    return self._wrappedData.name
    
  @property
  def _parent(self) -> Project:
    """Parent (containing) object."""
    return self._project

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @property
  def windows(self) -> typing.Tuple[Window, ...]:
    """Gui windows where Task is shown"""

    ff = self._project._data2Obj.get
    return tuple(ff(x) for x in self._wrappedData.sortedWindows())

  @windows.setter
  def windows(self, value:typing.Sequence):
    value = [self.getByPid(x) if isinstance(x, str) else x for x in value]
    self._wrappedData.windows = tuple(x._wrappedData for x in value)

  @property
  def status(self) -> str:
    """Status of task: connected to Project, disconnected form Project,
    or unrelated (template only)"""
    if self._wrappedData.nmrProject is self._project._wrappedData:
      return 'active'
    elif self._wrappedData.nmrProjectName is self._project._wrappedData.name:
      return 'passive'
    else:
      return 'template'

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (ccp.gui.guiTasks) for all GuiTasks connected to NmrProject"""
    return parent._wrappedData.sortedGuiTasks()


  # # NBNB Commented out 22/6/2016 as the functions are not in use (and likely never will be
  # # CCPN functions
  # def passivate(self):
  #   """passivate active task"""
  #   if self.status == 'active':
  #     self._wrappedData.passivate()
  #     self._unwrapAll()
  #   else:
  #     raise ValueError("Cannot passivate %s task: %s" % (self.status, self))
  #
  # def activate(self, window:Window=None):
  #   """activate passive task"""
  #   if self.status == 'passive':
  #     window=window and window._wrappedData
  #     self._wrappedData.activate(window=window)
  #     self._initializeAll()
  #   else:
  #     raise ValueError("Cannot activate %s task: %s" % (self.status, self))
  #
  # def clone(self, name:str, nameSpace:str=None):
  #   """copy task exactly, first passivating if active"""
  #   return self._project._data2Obj.get(self._wrappedData.clone())
  #
  # def loadAsTemplate(self, name:str, nameSpace:str=None, window:Window=None):
  #   """copy and activate template task, adapting and pruning contents to fit"""
  #
  #   window = self.getByPid(window) if isinstance(window, str) else window
  #   window=window and window._wrappedData
  #   newObj = self._wrappedData.adaptedCopy(nmrProject=self._project._wrappedData,
  #                                          window=window, name=name, nameSpace=nameSpace)
  #   return self._project._data2Obj.get(newObj)
  #
  # def pruneSpectrumViews(self, name:str, nameSpace:str=None):
  #   """Remove spectrum views that do not match existing spectra, e.g. after loading a template"""
  #   self._wrappedData.pruneSpectrumViews()

# newTask function
def _newTask(self:Project, name:str, nameSpace:str=None, comment:str=None) -> Task:
  """Create new Task"""

  for ss in name, nameSpace:
    if ss and Pid.altCharacter in ss:
      raise ValueError("Character %s not allowed in gui.core.Task i %s.%sd"
                       % (Pid.altCharacter, nameSpace, name))

  nmrProject = self._wrappedData
  dd = {'name':name, 'nmrProject':nmrProject, 'details':comment}
  if nameSpace is not None:
    dd['nameSpace'] = nameSpace

  defaults = collections.OrderedDict((('nameSpace', None), ('comment', None)))

  self._startCommandEchoBlock('newTask', name, values=locals(), defaults=defaults,
                              parName='newTask')
  try:
    newApiTask = nmrProject.root.newGuiTask(**dd)
  finally:
    self._endCommandEchoBlock()

  return self._data2Obj.get(newApiTask)
Project.newTask = _newTask

# Window.task crosslink
def getter(window):
  return window._project._data2Obj.get(window._wrappedData.guiTask)
def setter(window, value):
  value = window.getByPid(value) if isinstance(value, str) else value
  window._wrappedData.guiTask = value and value._wrappedData
Window.task = property(getter, setter, None, """Task shown in Window.""")
del getter
del setter

# Notifiers: None

# NBNB TBD Add notifiers, one way or the other, for activating and passivating tasks

