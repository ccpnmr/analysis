"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:48 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-06 15:51:11 +0000 (Thu, July 06, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
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
from PyQt5 import QtGui, QtWidgets, QtCore
from os.path import expanduser
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.ListWidget import ListWidget
from ccpn.ui.gui.widgets.ListWidget import ListWidgetPair
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes

from ccpn.ui.gui.widgets.Base import Base

# TODO These should maybe be consolidated with the same constants in CcpnNefIo
# (and likely those in Project)
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
    self._nefFileMode = fileMode
    self._nefText = text
    self._nefAcceptMode = acceptMode
    self._nefPreferences = preferences
    self._nefSelectFile = selectFile
    self._nefFilter = filter

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
    # self.spacer = Spacer(self.options, 3, 3
    #                      , QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
    #                      , grid=(1,1), gridSpan=(1,1))
    # self._includeCCPN = True
    # self._includeExpand = False

    # put save options in this section

    self.spacer = Spacer(self, 3, 3
                         , QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                         , grid=(1,0), gridSpan=(1,1))

    # self.labelFrame = Frame(self, setLayout=True, grid=(2,0))
    # self.labelLeft = Label(self.labelFrame, text='Items in Project', grid=(1,0), hAlign='c')
    # self.labelRight = Label(self.labelFrame, text='Items to Export to Nef File', grid=(1,1), hAlign='c')
    #
    # self.chainCopy = ListWidgetPair(self, setLayout=True, grid=(3,0), title=CHAINS, showMoveArrows=True)
    # if hasattr(self.project, CHAINS):
    #   self.chainCopy.setListObjects(self.project.chains)
    #
    # self.nmrChainCopy = ListWidgetPair(self, setLayout=True, grid=(4,0), title=NMRCHAINS, showMoveArrows=True)
    # if hasattr(self.project, NMRCHAINS):
    #   self.nmrChainCopy.setListObjects(self.project.nmrChains)
    #
    # self.restraintCopy = ListWidgetPair(self, setLayout=True, grid=(5,0), title=RESTRAINTLISTS, showMoveArrows=True)
    # if hasattr(self.project, RESTRAINTLISTS):
    #   self.restraintCopy.setListObjects(self.project.restraintLists)
    #
    # self.spacer = Spacer(self, 3, 3
    #                      , QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
    #                      , grid=(6,0), gridSpan=(1,1))
    #
    # self.spacer = Spacer(self, 3, 3
    #                      , QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
    #                      , grid=(7,0), gridSpan=(1,1))

    self.treeView = ProjectTreeCheckBoxes(self, project=self.project, grid=(3,0))
    # self._addTreeWidget(grid=(3,0))

    # file directory options here
    self.openPathIcon = Icon('icons/directory')

    self.saveFrame = Frame(self, setLayout=True, grid=(8,0))

    self.openPathIcon = Icon('icons/directory')
    self.saveLabel = Label(self.saveFrame, text = ' Path: ', grid=(0,0), hAlign = 'c')
    self.saveText = LineEdit(self.saveFrame, grid=(0,1), textAligment='l')
    self.saveText.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

    self.saveText.setDisabled(False)   # ejb - enable but need to check path on okay

    self.pathEdited = True
    self.saveText.textEdited.connect(self._editPath)

    self.spacer = Spacer(self.saveFrame, 13, 3
                         , QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
                         , grid=(0,2), gridSpan=(1,1))
    self.pathButton = Button(self.saveFrame, text=''
                             , icon=self.openPathIcon
                             , callback=self._openFileDialog
                             , grid=(0, 3), hAlign='c')

    self.buttonFrame = Frame(self, setLayout=True, grid=(9,0))
    self.spacer = Spacer(self.buttonFrame, 3, 3
                         , QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
                         , grid=(0,0), gridSpan=(1,1))
    self.buttons = ButtonList(self.buttonFrame, ['Cancel', 'Save'], [self._rejectDialog, self._acceptDialog], grid=(0,1))

    # this show/hide button doesn't quite work yet
    # self.showHide = Frame(self, setLayout=True, grid=(2,0))
    # self.showHideIcon = Icon('icons/directory')               # need to change this
    #
    # self.spacer = Spacer(self.showHide, 3, 3
    #                      , QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
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

    self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)

    # from here down is the save dialog
    # can we add a hide/show button?

    # self.fileWidget = Frame(self, setLayout=True, grid=(3,0))   # ejb -
    # self.fileWidget.hide()
    # self.fileSaveDialog = NefFileDialog(self.fileWidget, **self.saveDict)
    # self.layout().addWidget(self.fileSaveDialog, 3,0)
    # self.fileSaveDialog._setParent(self, self._acceptDialog, self._rejectDialog)  # why does this work?

    # self.fileSaveDialog = NefFileDialog(self, **self.saveDict)
    self.fileSaveDialog = NefFileDialog(self
                                        , fileMode = self._nefFileMode
                                        , text = self._nefText
                                        , acceptMode = self._nefAcceptMode
                                        , preferences = self._nefPreferences
                                        , selectFile = self._nefSelectFile
                                        , filter = self._nefFilter)

    if selectFile is not None:    # and self.application.preferences.general.useNative is False:
      self.saveText.setText(self.fileSaveDialog.selectedFile())
    else:
      self.saveText.setText('')
    self.oldFilePath = self.saveText.text()       # set to the same for the minute

    self._saveState = True

  def _toggleSaveDialog(self):
    if self._saveState is True:
      self.fileSaveDialog.hide()
    else:
      self.fileSaveDialog.show()

  def _acceptDialog(self, exitSaveFileName=None):
    self.exitFileName = self.saveText.text().strip()    # strip the trailing whitespace

    if self.pathEdited is False:     # self.exitFileName == self.oldFilePath:
      # user has not changed the path so we can accept()
      self.accept()
    else:
      # have edited the path so check the new file
      if os.path.isfile(self.exitFileName):
        yes = showYesNoWarning('%s already exists.' % os.path.basename(self.exitFileName)
                            , 'Do you want to replace it?')
        if yes:
          self.accept()
      else:
        if not self.exitFileName:
          showWarning('FileName Error:', 'Filename is empty.')
        else:
          self.accept()

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

    #TODO:ED do final checking

    # new bit to read all the checked pids (contain ':') from the checkboxtreewidget
    self.newList = []
    for item in self.treeView.findItems(':', QtCore.Qt.MatchContains | QtCore.Qt.MatchRecursive):
      if item.checkState(0) == QtCore.Qt.Checked:
        self.newList.append(item.text(0))

    self.accept()
    return self.exitFileName, self.flags, self.newList

    # this is the old bit that reads from the drag boxes
    self.exclusionDict = {Chain._pluralLinkName: self.chainCopy.getLeftList()
                         , NmrChain._pluralLinkName: self.nmrChainCopy.getLeftList()
                         , RestraintList._pluralLinkName: self.restraintCopy.getLeftList()}

    # from ccpn.core.Chain import Chain
    # from ccpn.core.ChemicalShiftList import ChemicalShiftList
    # from ccpn.core.RestraintList import RestraintList
    # from ccpn.core.PeakList import PeakList
    # from ccpn.core.Sample import Sample
    # from ccpn.core.Substance import Substance
    # from ccpn.core.NmrChain import NmrChain
    # from ccpn.core.DataSet import DataSet
    # from ccpn.core.Complex import Complex
    # from ccpn.core.SpectrumGroup import SpectrumGroup
    # from ccpn.core.Note import Note
    #
    # checkList = [Chain._pluralLinkName
    #              , ChemicalShiftList._pluralLinkName
    #              , RestraintList._pluralLinkName
    #              , PeakList._pluralLinkName
    #              , Sample._pluralLinkName
    #              , Substance._pluralLinkName
    #              , NmrChain._pluralLinkName
    #              , DataSet._pluralLinkName
    #              , Complex._pluralLinkName
    #              , SpectrumGroup._pluralLinkName
    #              , Note._pluralLinkName]

      # CHAINS, CHEMICALSHIFTLISTS, RESTRAINTLISTS, PEAKLISTS
      # , SAMPLES, SUBSTANCES, NMRCHAINS
      # , DATASETS, COMPLEXES, SPECTRUMGROUPS, NOTES]

    self.pidList = []                                # start with an empty list

    # go through the checkList above and add all objects to the list
    for name in ExportNefPopup.checkList:
      if hasattr(self.project, name):                   # just to be safe
        for obj in getattr(self.project, name):
          self.pidList.append(obj.pid)                 # append the found items to the list
      else:
        raise (ValueError, 'Name not found in project: %s' % self.pid)

    # now remove those items that are not needed (some may be added later depending on flags)
    for ky in self.exclusionDict:
      for exPid in self.exclusionDict[ky]:
        # exPidObj = self.getByPid(exPid)
        if exPid in self.pidList:
          self.pidList.remove(exPid)

    self.accept()
    return self.exitFileName, self.flags, self.pidList

  def _openFileDialog(self):
    self.fileDialog = FileDialog(self                       # ejb - old, , **self.saveDict)
                                 , fileMode=self._nefFileMode
                                 , text=self._nefText
                                 , acceptMode=self._nefAcceptMode
                                 , preferences=self._nefPreferences
                                 , selectFile=self.saveText.text()
                                 , filter=self._nefFilter)
    selectedFile = self.fileDialog.selectedFile()
    if selectedFile:
      self.saveText.setText(str(selectedFile))
      self.oldFilePath = str(selectedFile)
      self.pathEdited = False                     # we have reset the path

  def _save(self):
    self.accept()

  def _editPath(self):
    self.pathEdited = True      # user has manually changed the path

  # def _addTreeWidget(self, grid=None):
  #
  #   self.treeView = QtWidgets.QTreeWidget()
  #   self.headerItem = QtWidgets.QTreeWidgetItem()
  #   self.item = QtWidgets.QTreeWidgetItem()
  #
  #   self.treeView.header().hide()
  #
  #   for name in ExportNefPopup.checkList:
  #     if hasattr(self.project, name):                   # just to be safe
  #
  #       parent = QtWidgets.QTreeWidgetItem(self.treeView)
  #       parent.setText(0, name)
  #       parent.setFlags(parent.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
  #
  #       for obj in getattr(self.project, name):
  #
  #         child = QtWidgets.QTreeWidgetItem(parent)
  #         child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
  #         child.setText(0, obj.pid)
  #         child.setCheckState(0, QtCore.Qt.Unchecked)
  #
  #       parent.setCheckState(0, QtCore.Qt.Checked)
  #       parent.setExpanded(False)
  #       parent.setDisabled(name not in ExportNefPopup.selectList)
  #
  #   #       self.pidList.append(obj.pid)                 # append the found items to the list
  #   #
  #   # for i in range(3):
  #   #     parent = QtWidgets.QTreeWidgetItem(self.treeView)
  #   #     parent.setText(0, "Parent {}".format(i))
  #   #     parent.setFlags(parent.flags() | QtCore.Qt.ItemIsTristate | QtCore.Qt.ItemIsUserCheckable)
  #   #     for x in range(5):
  #   #         child = QtWidgets.QTreeWidgetItem(parent)
  #   #         child.setFlags(child.flags() | QtCore.Qt.ItemIsUserCheckable)
  #   #         child.setText(0, "Child {}".format(x))
  #   #         child.setCheckState(0, QtCore.Qt.Unchecked)
  #
  #   self.layout().addWidget(self.treeView, grid[0], grid[1])

if __name__ == '__main__':
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.popups.Dialog import CcpnDialog
  app = TestApplication()
  dialog = CcpnDialog()

  dialog.exec()
  dialog.raise_()

