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
from ccpn.ui.gui.widgets.FileDialog import NefFileDialog
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame

class ExportNefPopup(CcpnDialog):
  def __init__(self, parent=None, title='Export to Nef File', **kw):

    B = {'fileMode':None, 'text':None, 'acceptMode':None, 'preferences':None, 'selectFile':None, 'filter':None}
    C = {k:v for k, v in kw.items() if k in B}
    filterKw = {k:v for k, v in kw.items() if k not in B}

    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **filterKw)

    self.options = Frame(self, setLayout=True)
    self.buttons = ButtonList(self.options, ['Cancel', 'OK'], [self.reject, self._save], grid=(0, 0))

    self.fileWidget = Frame(self, setLayout=True)
    self.fileDialog = NefFileDialog(self.fileWidget, **C)

    self.layout().addWidget(self.options, 0,0)
    self.layout().addWidget(self.fileDialog, 1,0)

  def _save(self):
    self.accept()

  def selectedFiles(self):
    return self.fileDialog.selectedFiles()
    self.close()

  def selectedFile(self):
    return self.fileDialog.selectedFile()
    self.close()
  def reject(self):
    dialog = self.fileDialog.selectedFile()
    self.fileDialog.close()

  def _save(self):
    dialog = self.fileDialog.selectedFile()
    self.fileDialog.close()
    self.close()

if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog
  app = TestApplication()
  # popup = CcpnDialog(windowTitle='Test LineEditButtonDialog')
  dialog = ExportNefPopup()
  pass
  # print (popup.layout())
  dialog.show()
  dialog.raise_()
  # dialog.exec_()
  # app.start()
