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
from ccpn.ui.gui.widgets.Spacer import Spacer
from PyQt4 import QtGui
from os.path import expanduser
from ccpn.util.Logging import getLogger

class ExportNefPopup(CcpnDialog):
  def __init__(self, parent=None, title='Export to Nef File', **kw):

    B = {'fileMode':None, 'text':None, 'acceptMode':None, 'preferences':None, 'selectFile':None, 'filter':None}
    self.saveDict = {k:v for k, v in kw.items() if k in B}
    filterKw = {k:v for k, v in kw.items() if k not in B}

    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **filterKw)

    self.options = Frame(self, setLayout=True, grid=(0,0))

    # put save options in this section

    self.buttons = ButtonList(self.options, ['Cancel', 'OK'], [self._rejectDialog, self._acceptDialog], grid=(0, 0))

    self.openPathIcon = Icon('icons/directory')

    self.saveFrame = Frame(self, setLayout=True, grid=(1,0))
    self.openPathIcon = Icon('icons/directory')
    self.saveLabel = Label(self.saveFrame, grid=(0,0), hAlign = 'c')
    self.pathButton = Button(self.saveFrame, text=''
                             , icon=self.openPathIcon
                             , callback=self._openFileDialog
                             , grid=(0, 1), hAlign='c')
    self.spacer = Spacer(self.saveFrame, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding
                         , grid=(1,1), gridSpan=(1,1))

    # this show/hide button doesn't quite work yet
    # self.showHide = Frame(self, setLayout=True, grid=(2,0))
    # self.showHideIcon = Icon('icons/directory')               # need to change this
    #
    # self.spacer = Spacer(self.showHide, 5, 5
    #                      , QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed
    #                      , grid=(0,0), gridSpan=(1,1))
    # self.saveLabel2 = Label(self.showHide, text='Show/Hide saveDialog', grid=(0,1), hAlign = 'c')
    # self.pathButton = Button(self.showHide, text=''
    #                          , icon=self.showHideIcon
    #                          , callback=self._toggleSaveDialog
    #                          , grid=(0, 2), hAlign='t')


    if 'selectFile' in kw:
      self.saveLabel.setText(kw['selectFile'])
    else:
      self.saveLabel.setText('None')

    self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)

    # from here down is the save dialog
    # can we add a hide/show button?

    self.fileWidget = Frame(self, setLayout=True)
    self.fileWidget.hide()
    self.fileSaveDialog = NefFileDialog(self.fileWidget, **self.saveDict)
    self.layout().addWidget(self.fileSaveDialog, 3,0)
    self.fileSaveDialog._setParent(self, self._acceptDialog, self._rejectDialog)
    self._saveState = True

  def _toggleSaveDialog(self):
    if self._saveState is True:
      self.fileSaveDialog.hide()
    else:
      self.fileSaveDialog.show()

  def _acceptDialog(self, exitSaveFileName=None):
    self.exitFileName = exitSaveFileName
    self.accept()
    # return exitSaveFileName

  def _rejectDialog(self):
    self.exitFileName = None
    self.reject()
    # return None

  def closeEvent(self, QCloseEvent):
    self._rejectDialog()

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


