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
from ccpncore.api.ccpnmr.gui.Window import Window as Ccpn_Window
from ccpncore.util import Common as commonUtil
from ccpncore.lib import pid as Pid


class GuiWindow(AbstractWrapperObject):
  """GUI window, corresponds to OS window"""
  
  #: Short class name, for PID.
  shortClassName = 'GW'

  #: Name of plural link to instances of class
  _pluralLinkName = 'guiWindows'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnGuiWindow(self) -> Ccpn_Window:
    """ CCPN Wndow matching GuiWindow"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """short form of name, corrected to use for id"""
    return self._wrappedData.title.translate(Pid.remapSeparators)

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
    """get wrappedData (ccp.gui.windows) for all WIndow children of parent NmrProject.windowStore"""
    windowStore = parent._wrappedData.windowStore

    if windowStore is None:
      return []
    else:
      return windowStore.sortedWindows()



def newGuiWindow(parent:Project, title:str=None, position:tuple=(), size:tuple=()) -> GuiWindow:
  """Create new child GuiWindow

  :param str title: window  title (optional, defaults to 'Wn' n positive integer
  :param tuple size: x,y size for new window in integer pixels
  :param tuple position: x,y position for new window in integer pixels"""

  windowStore = parent.nmrProject.windowStore

  newCcpnGuiWindow = windowStore.newGuiWindow(title=title)
  if position:
    newCcpnGuiWindow.position = position
  if size:
    newCcpnGuiWindow.size = size

  return parent._data2Obj.get(newCcpnGuiWindow)

# Connections to parents:
Project._childClasses.append(GuiWindow)
Project.newGuiWindow = newGuiWindow

# Notifiers:
className = Ccpn_Window._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':GuiWindow}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
