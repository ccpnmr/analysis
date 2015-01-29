"""GUI SpectrumDisplay class

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
  def _getAllWrappedData(cls, parent:GuiTask)-> list:
    """get wrappedData (ccp.gui.Module) for all SpectrumDisplay children of parent GuiTask"""
    return [x for x in parent._wrappedData.sortedModules()
            if isinstance(x, Ccpn_SpectrumDisplay)]

def newSpectrumDisplay(parent:GuiTask, axisCodes:Sequence, stripDirection:str=None,
                       name:str=None, gridCell:Sequence=(1,1), gridSpan:Sequence=(1,1),
                       window:GuiWindow=None, comment:str=None, independentStrips=False,
                       nmrResidue=None):

  # Map to determine display type
  displayTypeMap = {
    (True, True,False):('newDisplay1d','newStrip1d'),
    (True, False,False):('newStripDisplay1d','newStrip1d'),
    (False, True,False):('newDisplayNd','newStripNd'),
    (False, False,False):('newStripDisplayNd','newStripNd'),
    (False, False,True):('newStripDisplayNd','newFreeStripNd'),
    (True, False,True):('newStripDisplay1d','newFreeStrip1d'),
  }

  ccpnGuiTask = parent._wrappedData

  if len(axisCodes) <2:
    raise ValueError("New SpectrumDisplay must have at least two axisCodes")

  # set display type discriminator and get display types
  mapTuple = (
    axisCodes[1] == 'intensity',   # 1d display
    stripDirection is None,        # single=pane display
    bool(independentStrips)        # free-strip display
  )
  tt = displayTypeMap.get(mapTuple)
  if tt is None:
    raise ValueError("stripDirection must be set if independentStrips is True")
  else:
    newDisplayFunc, newStripFunc = tt

  # set parameters for display
  displayPars = dict(
    stripDirection=stripDirection, gridCell=gridCell, gridSpan=gridSpan, window=window,
    details=comment, nmrResidue=nmrResidue
  )
  # Add name, setting and insuring uniqueness if necessary
  if name is None:
    if 'intensity' in axisCodes:
      name = ''.join(['1D:', axisCodes[0]] + axisCodes[2:])
    else:
      name = ''.join(axisCodes)
  while ccpnGuiTask.findFirstModule(name=name):
    name = commonUtil.incrementName(name)
  displayPars['name'] = name

  if independentStrips:
    # Create FreeStripDisplay and first strip
    ccpnSpectrumDisplay = getattr(ccpnGuiTask, newDisplayFunc)(**displayPars)
    ccpnStrip = ccpnSpectrumDisplay.newStrip(axisCodes=axisCodes, axisOrder=axisCodes)
  else:
    # Create Boundstrip/Nostrip display and first strip
    displayPars['axisCodes'] = displayPars['axisOrder'] = axisCodes
    ccpnSpectrumDisplay = getattr(ccpnGuiTask, newDisplayFunc)(**displayPars)
    ccpnStrip = ccpnSpectrumDisplay.newStrip()

# Connections to parents:
Project._childClasses.append(SpectrumDisplay)
Project.newSpectrumDisplay = newSpectrumDisplay

# Notifiers:
className = Ccpn_SpectrumDisplay._metaclass.qualifiedName()
Project._apiNotifiers.extend(
  ( ('_newObject', {'cls':SpectrumDisplay}, className, '__init__'),
    ('_finaliseDelete', {}, className, 'delete')
  )
)
