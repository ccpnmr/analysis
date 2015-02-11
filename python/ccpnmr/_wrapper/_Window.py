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
from ccpncore.api.ccpnmr.gui.Window import Window as ApiWindow
from ccpnmrcore.modules.GuiWindow import GuiWindow
from ccpnmrcore.modules.GuiMainWindow import GuiMainWindow
from ccpncore.lib import pid as Pid


class Window(GuiWindow, AbstractWrapperObject):
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

  # Implementation functions
  @classmethod
  def _getAllWrappedData(cls, parent:Project)-> list:
    """get wrappedData (ccp.gui.windows) for all Window children of parent NmrProject.windowStore"""
    windowStore = parent._wrappedData.windowStore

    if windowStore is None:
      return []
    else:
      return windowStore.sortedWindows()



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
class MainWindow(GuiMainWindow, Window):
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


class SideWindow(GuiWindow, Window):
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
