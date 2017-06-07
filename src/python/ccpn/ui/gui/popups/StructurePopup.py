"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy$"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.popups.Dialog import CcpnDialog

class StructurePopup(CcpnDialog):
  """
  Open a small popup to allow changing the label of a StructureEnsemble
  """
  def __init__(self, parent=None, mainWindow=None, title='Notes', structure=None, **kw):
    """
    Initialise the widget
    """
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    self.structure = structure
    self.structureLabel = Label(self, "Structure Name: "+self.structure.pid, grid=(0, 0))
    self.structureText = LineEdit(self, self.structure.name, grid=(0, 1))
    ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(1, 1))

  def _okButton(self):
    """
    When ok button pressed: update StructureEnsemble and exit
    """
    newName = self.structureText.text()
    if str(newName) != self.structure.name:
      self.structure.rename(newName)
    self.accept()

