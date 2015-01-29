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
from ccpn._wrapper._NmrResidue import NmrResidue
from ccpnmr._wrapper._GuiTask import GuiTask
from ccpnmr._wrapper._GuiWindow import GuiWindow
from ccpncore.api.ccpnmr.gui.Task import SpectrumDisplay as Ccpn_SpectrumDisplay
from ccpncore.util import Common as commonUtil
from ccpncore.lib import pid as Pid


class SpectrumDisplay(AbstractWrapperObject):
  """Spectrum display for 1D or nD spectrum"""
  
  #: Short class name, for PID.
  shortClassName = 'GD'

  #: Name of plural link to instances of class
  _pluralLinkName = 'spectrumDisplays'
  
  #: List of child classes.
  _childClasses = []
  

  # CCPN properties  
  @property
  def ccpnSpectrumDisplay(self) -> Ccpn_SpectrumDisplay:
    """ CCPN SpectrumDisplay matching SpectrumDisplay"""
    return self._wrappedData
    
  @property
  def _key(self) -> str:
    """short form of name, corrected to use for id"""
    return self._wrappedData.name

  @property
  def name(self) -> str:
    """SpectrumDisplay name"""
    return self._wrappedData.name
    
  @property
  def _parent(self) -> GuiTask:
    """Parent (containing) object."""
    return self._project._data2Obj.get(self._wrappedData.guiTask)

  @property
  def stripDirection(self) -> str:
    """Strip axis direction ('X', 'Y', None) - None only for non-strip plots"""
    return self._wrappedData.stripDirection

  @property
  def stripCount(self) -> str:
    """Number of strips"""
    return self._wrappedData.stripCount

  @property
  def gridCell(self) -> tuple:
    """Display grid cell as (x,y)"""
    return self._wrappedData.gridCell

  @gridCell.setter
  def gridCell(self, value:Sequence):
    self._wrappedData.gridCell = value
  
  @property
  def gridSpan(self) -> tuple:
    """Display grid span as (x,y)"""
    return self._wrappedData.gridSpan

  @gridSpan.setter
  def gridSpan(self, value:Sequence):
    self._wrappedData.gridSpan = value

  @property
  def comment(self) -> str:
    """Free-form text comment"""
    return self._wrappedData.details

  @comment.setter
  def comment(self, value:str):
    self._wrappedData.details = value

  @property
  def guiWindow(self) -> GuiWindow:
    """Gui window showing SpectrumDisplay"""
    return self._project._data2Obj.get(self._wrappedData.window)

  @guiWindow.setter
  def guiWindow(self, value:GuiWindow):
    self._wrappedData.window = value and value._wrappedData

  @property
  def nmrResidue(self) -> NmrResidue:
    """NmrResidue attached to SpectrumDisplay"""
    return  self._project._data2Obj.get(self._wrappedData.resonanceGroup)

  @nmrResidue.setter
  def nmrResidue(self, value:NmrResidue):
    self._wrappedData.resonanceGroup = value and value._wrappedData

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
