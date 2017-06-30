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
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Spacer import Spacer
from PyQt4 import QtGui, QtCore
from os.path import expanduser
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.ListWidget import ListWidgetPair

CHAINS = 'chains'
NMRCHAINS = 'nmrChains'
RESTRAINTLISTS = 'restraintLists'
CCPNTAG = 'ccpn'
SKIPPREFIXES = 'skipPrefixes'
EXPANDSELECTION = 'expandSelection'

class ExportNefPopup(CcpnDialog):

  def __init__(self, parent=None, mainWindow=None, title='Export to Nef File'
               , fileMode=FileDialog.AnyFile
               , text='Export File'
               , acceptMode=FileDialog.AcceptSave
               , preferences=None
               , selectFile=None
               , filter='*'
               , **kw):
    """
    Initialise the widget
    """
    # pre __init__ to process extra keywords

    # B = {'fileMode':None
    #       , 'text':None
    #       , 'acceptMode':None
    #       , 'preferences':None
    #       , 'selectFile':None
    #       , 'filter':None}
    # self.saveDict = {k:v for k, v in kw.items() if k in B}
    # filterKw = {k:v for k, v in kw.items() if k not in B}

    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current

    self.options = Frame(self, setLayout=True, grid=(0,0))
    self.buttonCCPN = CheckBox(self.options, checked=True
                               , text='include CCPN tags'
                               , grid=(0,0), hAlign ='l')
    self.buttonExpand = CheckBox(self.options, checked=False
                               , text='expand selection'
                               , grid=(1,0), hAlign ='l')
    # self.spacer = Spacer(self.options, 5, 5
    #                      , QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding
    #                      , grid=(1,1), gridSpan=(1,1))
    # self._includeCCPN = True
    # self._includeExpand = False

    # put save options in this section

    self.spacer = Spacer(self, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(1,0), gridSpan=(1,1))

    self.labelFrame = Frame(self, setLayout=True, grid=(2,0))
    self.labelLeft = Label(self.labelFrame, text='Items in Project', grid=(1,0), hAlign='c')
    self.labelRight = Label(self.labelFrame, text='Items to Export to Nef File', grid=(1,1), hAlign='c')

    self.chainCopy = ListWidgetPair(self, setLayout=True, grid=(3,0), title=CHAINS)
    if hasattr(self.project, CHAINS):
      self.chainCopy.setListObjects(self.project.chains)

    self.nmrChainCopy = ListWidgetPair(self, setLayout=True, grid=(4,0), title=NMRCHAINS)
    if hasattr(self.project, NMRCHAINS):
      self.nmrChainCopy.setListObjects(self.project.nmrChains)

    self.restraintCopy = ListWidgetPair(self, setLayout=True, grid=(5,0), title=RESTRAINTLISTS)
    if hasattr(self.project, RESTRAINTLISTS):
      self.restraintCopy.setListObjects(self.project.restraintLists)

    self.spacer = Spacer(self, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(6,0), gridSpan=(1,1))

    self.spacer = Spacer(self, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding
                         , grid=(7,0), gridSpan=(1,1))

    # file directory options here
    self.openPathIcon = Icon('icons/directory')

    self.saveFrame = Frame(self, setLayout=True, grid=(8,0))

    self.openPathIcon = Icon('icons/directory')
    self.saveLabel = Label(self.saveFrame, text = '   Path:   ', grid=(0,0), hAlign = 'c')
    self.saveText = LineEdit(self.saveFrame, grid=(0,1), textAligment='l')
    self.saveText.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
    self.saveText.setDisabled(True)
    if 'selectFile' in kw:
      self.saveText.setText(kw['selectFile'])
    else:
      self.saveText.setText('None')
    self.spacer = Spacer(self.saveFrame, 15, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(0,2), gridSpan=(1,1))
    self.pathButton = Button(self.saveFrame, text=''
                             , icon=self.openPathIcon
                             , callback=self._openFileDialog
                             , grid=(0, 3), hAlign='c')

    self.buttonFrame = Frame(self, setLayout=True, grid=(9,0))
    self.spacer = Spacer(self.buttonFrame, 5, 5
                         , QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed
                         , grid=(0,0), gridSpan=(1,1))
    self.buttons = ButtonList(self.buttonFrame, ['Cancel', 'Save'], [self._rejectDialog, self._acceptDialog], grid=(0,1))

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
    # if 'selectFile' in kw:
    #   self.saveLabel.setText(kw['selectFile'])
    # else:
    #   self.saveLabel.setText('None')

    self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.MinimumExpanding)

    # from here down is the save dialog
    # can we add a hide/show button?

    # self.fileWidget = Frame(self, setLayout=True, grid=(3,0))   # ejb -
    # self.fileWidget.hide()
    # self.fileSaveDialog = NefFileDialog(self.fileWidget, **self.saveDict)
    # self.layout().addWidget(self.fileSaveDialog, 3,0)
    # self.fileSaveDialog._setParent(self, self._acceptDialog, self._rejectDialog)  # why does this work?

    # self.fileSaveDialog = NefFileDialog(self, **self.saveDict)
    self.fileSaveDialog = NefFileDialog(self
                                        , fileMode = fileMode
                                        , text = text
                                        , acceptMode = acceptMode
                                        , preferences = preferences
                                        , selectFile = selectFile
                                        , filter = filter)

    if 'selectFile':
      self.saveText.setText(self.fileSaveDialog.selectedFile())
    else:
      self.saveText.setText('None')

    self._saveState = True

  def _toggleSaveDialog(self):
    if self._saveState is True:
      self.fileSaveDialog.hide()
    else:
      self.fileSaveDialog.show()

  def _acceptDialog(self, exitSaveFileName=None):
    # self.exitFileName = exitSaveFileName
    self.exitFileName = self.saveText.text()    # self.fileSaveDialog.selectedFile()
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

    # build the export dict and flags

    self.flags = {}
    self.flags[SKIPPREFIXES] = []
    if self.buttonCCPN.isChecked() is False:        # these are negated as they are skipped flags
      self.flags[SKIPPREFIXES].append(CCPNTAG)
    self.flags[EXPANDSELECTION] = self.buttonExpand.isChecked()

    #TODO:ED need to work on this, but currently trying to match the items
    #       in CcpnNefIo/exportProject
    #       export a dict for clarity

    self.exclusionDict = {CHAINS: self.chainCopy.getLeftList()
                         , NMRCHAINS: self.nmrChainCopy.getLeftList()
                         , RESTRAINTLISTS: self.restraintCopy.getLeftList()}

    self.accept()
    return self.exitFileName, self.flags, self.exclusionDict

  def _openFileDialog(self):
    self.fileDialog = FileDialog(self, **self.saveDict)
    selectedFile = self.fileDialog.selectedFile()
    if selectedFile:
      self.saveText.setText(str(selectedFile))

  def _save(self):
    self.accept()


if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog
  app = TestApplication()
  dialog = ExportNefPopup(fileMode=FileDialog.AnyFile
                          , text="Export to Nef File"
                          , acceptMode=FileDialog.AcceptSave
                          , filter='*.nef')
  dialog.show()


