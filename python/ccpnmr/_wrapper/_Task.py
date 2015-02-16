"""GUI Task class

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
from ccpnmr._wrapper._Window import Window
from ccpncore.api.ccpnmr.gui.Task import GuiTask as ApiGuiTask
from ccpncore.lib import pid as Pid


class Task(AbstractWrapperObject):
  """GUI task, corresponds to set of interacting modules"""
  
  #: Short class name, for PID.
  shortClassName = 'GT'

  #: Name of plural link to instances of class
  _pluralLinkName = 'tasks'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def apiGuiTask(self) -> ApiGuiTask:
    """ CCPN GuiTask matching Task"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """local id, of form nameSpace.name"""
    return Pid.IDSEP.join((self._wrappedData.nameSpace, self._wrappedData.name))

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
  def windows(self) -> Window:
    """Gui windows where Task is shown"""
    ff = self._project._data2Obj.get
    return tuple(ff(x) for x in self._wrappedData.windows)

  @windows.setter
  def windows(self, value:Sequence):
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
    nmrProject = parent._wrappedData
    return tuple(nmrProject.sortedGuiTasks())

  # CCPN functions
  def passivate(self):
    """passivate active task"""
    if self.status == 'active':
      self._wrappedData.passivate()
      self._unwrapAll()
    else:
      raise ValueError("Cannot passivate %s task: %s" % (self.status, self))

  def activate(self, window:Window=None):
    """activate passive task"""
    if self.status == 'passive':
      window=window and window._wrappedData
      self._wrappedData.activate(window=window)
      self._initializeAll()
    else:
      raise ValueError("Cannot activate %s task: %s" % (self.status, self))

  def clone(self, name:str, nameSpace:str=None):
    """copy task exactly, first passivating if active"""
    return self._project._data2Obj.get(self._wrappedData.clone())

  def loadAsTemplate(self, name:str, nameSpace:str=None, window:Window=None):
    """copy and activate template task, adapting and pruning contents to fit"""
    window=window and window._wrappedData
    newObj = self._wrappedData.adaptedCopy(nmrProject=self._project._wrappedData,
                                           window=window, name=name, nameSpace=nameSpace)
    return self._project._data2Obj.get(newObj)

  def pruneSpectrumViews(self, name:str, nameSpace:str=None):
    """Remove spectrum views that do not match existing spectra, e.g. after loading a template"""
    self._wrappedData.pruneSpectrumViews()


def newTask(parent:Project, name:str, nameSpace:str=None, comment:str=None) -> Task:
  """Create new child Task"""

  nmrProject = parent.nmrProject

  newApiTask = nmrProject.root.newGuiTask(name=name, nameSpace=nameSpace,
                                                nmrProject=nmrProject, details=comment)

  return parent._data2Obj.get(newApiTask)

# Connections to parents:
Project._childClasses.append(Task)
Project.newTask = newTask

# Notifiers:

# NBNB TBD Add notifiers, one way or the other, for activating and passivating tasks

className = ApiGuiTask._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':Task}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
