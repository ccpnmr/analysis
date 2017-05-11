#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan"
               "Simon P Skinner & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license"
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:40:40 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: simon1 $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.PulldownListsForObjects import NotesPulldown
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.core.lib.Notifiers import Notifier
from ccpn.core.Note import Note

class NotesEditorModule(CcpnModule):
  """
  This class implements the module by wrapping a StructureTable instance
  """
  includeSettingsWidget = True
  maxSettingsState = 2  # states are defined as: 0: invisible, 1: both visible, 2: only settings visible
  settingsOnTop = True

  className = 'NotesEditorModule'
  attributeName = 'notes'

  def __init__(self, mainWindow=None, name='Notes Editor', note=None):
    CcpnModule.__init__(self, mainWindow=mainWindow, name=name)

    # Derive application, project, and current from mainWindow
    self.mainWindow = mainWindow
    self.application = mainWindow.application
    self.project = mainWindow.application.project
    self.current = mainWindow.application.current
    self.note = note

    self.spacer = Spacer(self.mainWidget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(0,0), gridSpan=(1,1))
    self.noWidget = NotesPulldown(parent=self.mainWidget
                                   , project=self.project, default=0  # first Structure in project (if present)
                                   , grid=(1,0), gridSpan=(1,1), minimumWidths=(0,100)
                                   , showSelectName=True
                                   , callback=self._selectionPulldownCallback)
    self.spacer = Spacer(self.mainWidget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(2,0), gridSpan=(1,1))

    self._noteNotifier = Notifier(self.project                                          # need an object not a list
                                  , [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME]
                                  , Note.__name__
                                  , self._updateCallback)

    self.noteWidget = Widget(self.mainWidget, grid=(3,0), gridSpan=(1,5), setLayout=True)
    self.noteWidget.hide()

    self.label1 = Label(self.noteWidget, text='Note name', grid=(1,0), vAlign='centre', hAlign='right')
    self.lineEdit1 = LineEdit(self.noteWidget, grid=(1,1), gridSpan=(1,2), vAlign='top')
    self.spacer = Spacer(self.noteWidget, 5, 5
                         , QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
                         , grid=(2,0), gridSpan=(1,1))
    self.textBox = TextEditor(self.noteWidget, grid=(3,0), gridSpan=(1,7))

    if note:
      self.textBox.setText(note.text)
      self.lineEdit1.setText(self.note.name)

    self.buttonBox = ButtonList(self.noteWidget, texts=['Apply', 'Delete']
                                , callbacks=[self._applyNote, self._deleteNote]
                                , grid=(6,5), gridSpan=(1,2))
    self.spacer = Spacer(self.mainWidget, 5, 5
                         , QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding
                         , grid=(5,4), gridSpan=(1,1))

    self.mainWidget.setContentsMargins(5, 5, 5, 5)
    self.processText = self._processText

  def _setNoteName(self):
    """
    Sets the name of the note based on the text in the Note name text box.
    """
    #FIXME:ED check that the new name is valid
    self.note.rename(self.lineEdit1.text())

  def _applyNote(self):
    """
    Saves the text in the textbox to the note object.
    """
    newText = self.textBox.toPlainText()
    self.note.text = newText
    self._setNoteName()

  def _reject(self):
    """
    Closes the note editor ignoring all changes.
    """
    self.close()

  def _processText(self, text, event):
    if not self.note:
      self.note = self.project.newNote()
    self.textBox.setText(text)
    self.overlay.hide()

  def _selectionPulldownCallback(self, item):
    "Callback for selecting Structure"
    self.thisObj = self.project.getByPid(item)
    if self.thisObj is not None:
      self.displayTableForNote(self.thisObj)
    else:
      self.noteWidget.hide()

  def displayTableForNote(self, note):
    "Display the table for all Notes"

    # if self._noteNotifier is not None:
    #   # we have a new note and hence need to unregister the previous notifier
    #   self._noteNotifier.unRegister()
    # # register a notifier for this note
    # self._noteNotifier = Notifier(note,
    #                                [Notifier.CREATE, Notifier.DELETE, Notifier.RENAME], 'Note',
    #                                 self._updateCallback
    #                               )

    self.noWidget.select(note.pid)
    self._update(note)

  def _updateCallback(self, data):
    "callback for updating the note"
    thisNoteList = getattr(data[Notifier.THEOBJECT], self.attributeName)   # get the notesList
    if self.note in thisNoteList:
      self.displayTableForNote(self.note)
    else:
      self.noteWidget.hide()

  def _update(self, note):
    "Update the note"
    self.note = note
    self.textBox.setText(note.text)
    self.lineEdit1.setText(note.name)
    self.noteWidget.show()
    self.show()

  def _deleteNote(self):
    if self.note:
      self.note.delete()

  def destroy(self):
    "Cleanup of self"
    if self._noteNotifier is not None:
      self._noteNotifier.unRegister()

