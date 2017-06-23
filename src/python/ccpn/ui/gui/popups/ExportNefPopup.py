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
from ccpn.ui.gui.widgets.FileDialog import FileDialog, NefFileDialog
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Button import Button
from os.path import expanduser

class ExportNefPopup(CcpnDialog):
  def __init__(self, parent=None, title='Export to Nef File', **kw):

    B = {'fileMode':None, 'text':None, 'acceptMode':None, 'preferences':None, 'selectFile':None, 'filter':None}
    self.saveDict = {k:v for k, v in kw.items() if k in B}
    filterKw = {k:v for k, v in kw.items() if k not in B}

    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **filterKw)

    self.options = Frame(self, setLayout=True, grid=(0,0))
    self.buttons = ButtonList(self.options, ['Cancel', 'OK'], [self._rejectDialog, self._acceptDialog], grid=(0, 0))

    self.openPathIcon = Icon('icons/directory')

    self.saveFrame = Frame(self, setLayout=True, grid=(1,0))
    self.openPathIcon = Icon('icons/directory')
    self.saveLabel = Label(self.saveFrame, grid=(0,0), hAlign = 'c')
    self.pathButton = Button(self.saveFrame, text=''
                             , icon=self.openPathIcon
                             , callback=self._openFileDialog
                             , grid=(0, 1), hAlign='c')

    if 'selectFile' in kw:
      self.saveLabel.setText(kw['selectFile'])
    else:
      self.saveLabel.setText('None')

    self.fileWidget = Frame(self, setLayout=True)
    self.fileSaveDialog = NefFileDialog(self.fileWidget, **self.saveDict)
    self.layout().addWidget(self.fileSaveDialog, 2,0)
    self.fileSaveDialog._setParent(self, self._acceptDialog, self._rejectDialog)

  def _acceptDialog(self, exitSaveFileName=None):
    self.exitFileName = exitSaveFileName
    self.accept()
    # return exitSaveFileName

  def _rejectDialog(self):
    self.exitFileName = None
    self.reject()
    # return None

  def show(self):
    self.raise_()
    val = self.exec_()
    self.accept()
    return self.exitFileName    # and other save options here

  def _openFileDialog(self):
    self.fileDialog = FileDialog(self, **self.saveDict)
    selectedFile = self.fileDialog.selectedFile()
    if selectedFile:
      self.saveLabel.setText(str(selectedFile))

  def _save(self):
    self.accept()


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog
  app = TestApplication()
  dialog = ExportNefPopup()
  dialog.show()


