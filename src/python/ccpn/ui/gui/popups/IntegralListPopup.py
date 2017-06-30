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
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.popups.Dialog import CcpnDialog


class IntegralListPopup(CcpnDialog):
  def __init__(self, parent=None, mainWindow=None, integralList=None, title='IntegralList', **kw):
    """
    Initialise the widget
    """
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    self.integralList = integralList
    self.integralListLabel = Label(self, "integralList Name ", grid=(0, 0))
    self.integralListText = LineEdit(self, integralList.title, grid=(0, 1))
    ButtonList(self, ['Cancel', 'OK'], [self.reject, self._integralListName], grid=(1, 1))

  def _integralListName(self):
    newName = self.integralListText.text()
    self.integralList.title = newName
    self.accept()
