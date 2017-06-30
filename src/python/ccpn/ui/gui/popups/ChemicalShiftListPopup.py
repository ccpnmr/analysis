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
from ccpn.ui.gui.widgets.MessageDialog import showWarning


class ChemicalShiftListPopup(CcpnDialog):
  def __init__(self, parent=None, mainWindow=None, chemicalShiftList=None, title='Chemical Shift List', **kw):
    """
    Initialise the widget
    """
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    self.chemicalShiftList = chemicalShiftList
    self.chemicalShiftListLabel = Label(self, "Chemical Shift List Name ", grid=(0, 0))
    self.chemicalShiftListText = LineEdit(self, chemicalShiftList.name, grid=(0, 1))
    ButtonList(self, ['Cancel', 'OK'], [self.reject, self._okButton], grid=(1, 1))

  def _okButton(self):
    newName = self.chemicalShiftListText.text()
    try:
      if str(newName) != self.chemicalShiftList.name:
        self.chemicalShiftList.rename(newName)
      self.accept()
    except Exception as es:
      showWarning(self.windowTitle(), str(es))

