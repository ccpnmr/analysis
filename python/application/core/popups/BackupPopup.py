from PyQt4 import QtCore, QtGui

import os

from ccpncore.memops.metamodel import Util as metaUtil

from application.core.widgets.CheckBox import CheckBox
from application.core.widgets.Frame import Frame
from application.core.widgets.Label import Label
from application.core.widgets import MessageDialog
from application.core.widgets.Entry import Entry

class BackupPopup(QtGui.QDialog):

  # parent mandatory and that needs to have attributes _appBase
  def __init__(self, parent, title='Auto Backup'):
     
    QtGui.QDialog.__init__(self, parent=parent)
    self.setWindowTitle(title)

    preferences = self.parent()._appBase.preferences

    frame = Frame(self)

    row = 0
    label = Label(frame, text='Auto backup on: ', grid=(row,0))
    checkbox = CheckBox(frame, checked=preferences.general.autoBackupEnabled, callback=self.toggleBackup, grid=(row,1))

    row += 1
    label = Label(frame, text='Auto backup frequency: ', grid=(row,0))
    entry = Entry(frame, text=str(preferences.general.autoBackupFrequency), callback=self.setBackupFrequency, grid=(row,1))

  def toggleBackup(self):

    appBase = self.parent()._appBase
    preferences = appBase.preferences
    preferences.general.autoBackupEnabled = not preferences.general.autoBackupEnabled
    if preferences.general.autoBackupEnabled:
      appBase.mainWindow.startBackupTimer()
    else:
      appBase.mainWindow.stopBackupTimer()

  def setBackupFrequency(self, value):
    try:
      value = int(value)
    except:
      return

    appBase = self.parent()._appBase
    preferences = appBase.preferences
    preferences.general.autoBackupFrequency = value
    if preferences.general.autoBackupEnabled:
      appBase.mainWindow.startBackupTimer()

