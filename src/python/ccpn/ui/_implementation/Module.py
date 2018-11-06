"""GUI SpectrumDisplay class

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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:40 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import collections
from ccpn.core.Project import Project
from ccpn.core._implementation.AbstractWrapperObject import AbstractWrapperObject
from ccpn.ui._implementation.Window import Window
from ccpn.util import Common as commonUtil
from ccpn.core.lib import Pid
from ccpnmodel.ccpncore.api.ccpnmr.gui.Window import Window as ApiWindow
from ccpnmodel.ccpncore.api.ccpnmr.gui.Task import GenericModule as ApiGenericModule

class Module(AbstractWrapperObject):
  """Generic GUI module (not a spectrum display"""
  
  #: Short class name, for PID.
  shortClassName = 'GO'
  # Attribute it necessary as subclasses must use superclass className
  className = 'Module'

  _parentClass = Project

  #: Name of plural link to instances of class
  _pluralLinkName = 'modules'
  #: List of child classes.
  _childClasses = []

  # Qualified name of matching API class
  _apiClassQualifiedName = ApiGenericModule._metaclass.qualifiedName()

  # CCPN properties  
  @property
  def _apiSpectrumDisplay(self) -> ApiGenericModule:
    """ CCPN GenericModule object matching Module"""
    return self._wrappedData
  
  @property
  def _key(self) -> str:
    """short form of name, corrected to use for id"""
    return self._wrappedData.name.translate(Pid.remapSeparators)

  @property
  def title(self) -> str:
    """Module title

    (corresponds to its name, but the name 'name' is taken by PyQt"""
    return self._wrappedData.name
    
  @property
  def _parent(self) -> Project:
    """Project containing module."""
    return self._project

  project = _parent

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def window(self) -> Window:
    """Gui window showing Module"""
    # TODO: RASMUS window clashes with a Qt attribute.
    # This should be renamed, but that also requires refactoring
    # possibly with a model change that modifies the Task/Window/Module relationship
    return self._project._data2Obj.get(self._wrappedData.window)

  @window.setter
  def window(self, value:Window):
    value = self.getByPid(value) if isinstance(value, str) else value
    self._wrappedData.window = value and value._wrappedData

  @property
  def moduleType(self) ->  str:
    """Type of module, used to determine the graphics implementation used
    (e.g. 'PeakTableModule', 'Assigner', ..."""
    return self._wrappedData.moduleType

  @moduleType.setter
  def moduleType(self, value):
    self._wrappedData.moduleType = value

  @property
  def parameters(self) -> dict:
    """Keyword-value dictionary of parameters.
    NB the value is a copy - modifying it will not modify the actual data.

    Values can be anything that can be exported to JSON,
    including OrderedDict, numpy.ndarray, ccpn.util.Tensor,
    or pandas DataFrame, Series, or Panel"""
    return dict((x.name, x.value) for x in self._wrappedData.parameters)

  def setParameter(self, name:str, value):
    """Add name:value to parameters, overwriting existing entries"""
    apiData = self._wrappedData
    parameter = apiData.findFirstParameter(name=name)
    if parameter is None:
      apiData.newParameter(name=name, value=value)
    else:
      parameter.value = value

  def deleteParameter(self, name:str):
    """Delete parameter named 'name'"""
    apiData = self._wrappedData
    parameter = apiData.findFirstParameter(name=name)
    if parameter is None:
      raise KeyError("No parameter named %s" % name)
    else:
      parameter.delete()

  def clearParameters(self):
    """Delete all parameters"""
    for parameter in self._wrappedData.parameters:
      parameter.delete()

  def updateParameters(self, value:dict):
    """update parameters"""
    for key,val in value.items():
      self.setParameter(key, val)

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (ccp.gui.Module) for all GenericModule children of parent Project"""

    apiGuiTask = (parent._wrappedData.findFirstGuiTask(nameSpace='user', name='View') or
                  parent._wrappedData.root.newGuiTask(nameSpace='user', name='View'))
    return [x for x in apiGuiTask.sortedModules() if isinstance(x, ApiGenericModule)]


# newModule functions
def _newModule(self:Project, moduleType:str, title:str=None, window:Window=None, comment:str=None):

  window = self.getByPid(window) if isinstance(window, str) else window

  apiTask = (self._wrappedData.findFirstGuiTask(nameSpace='user', name='View') or
                self._wrappedData.root.newGuiTask(nameSpace='user', name='View'))

  # set parameters for display
  apiWindow = window._wrappedData if window else apiTask.sortedWindows()[0]
  params = dict(
    window=apiWindow, details=comment, moduleType=moduleType
  )
  # Add name, setting and insuring uniqueness if necessary
  if title is None:
    title = moduleType
  if Pid.altCharacter in title:
    raise ValueError("Character %s not allowed in gui.core.Module.name" % Pid.altCharacter)
  while apiTask.findFirstModule(name=title):
    title = commonUtil.incrementName(title)
  params['name'] = title

  # Create Module
  defaults = collections.OrderedDict((('title', None), ('window', None),
                                     ('comment', None)))
  self._startCommandEchoBlock('newModule', moduleType, values=locals(), defaults=defaults,
                              parName='newModule')
  try:
    apiGenericModule = apiTask.newGenericModule(**params)
    #
    result = self._project._data2Obj.get(apiGenericModule)
  finally:
    self._endCommandEchoBlock()

  return result
Project.newModule = _newModule
del _newModule

# GWV commented 6/11/18 as it does not work
# # Window.modules property
# def getter(window:Window):
#   ll = [x for x in window._wrappedData.sortedModules() if isinstance(x, ApiGenericModule)]
#   return tuple(window._project._data2Obj[x] for x in ll)
# Window.modules = property(getter, None, None, "Modules shown in Window")
# del getter

# Notifiers:

# crosslinks window
# TODO change to calling _setupApiNotifier
Project._apiNotifiers.append(
  ('_modifiedLink', {'classNames':('Window','Module')},
  ApiGenericModule._metaclass.qualifiedName(), 'setWindow'),
)

# WARNING link notifiers for both Window <-> Module and Window<->SpectrumDisplay
# are triggered together when  the change is on the Window side.
# Programmer take care that your notified function will work for both inputs !!!
# TODO change to calling _setupApiNotifier
className = ApiWindow._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_modifiedLink', {'classNames':('Module','Window')}, className, 'addModule'),
    ('_modifiedLink', {'classNames':('Module','Window')}, className, 'removeModule'),
    ('_modifiedLink', {'classNames':('Module','Window')}, className, 'setModules'),
  )
)

