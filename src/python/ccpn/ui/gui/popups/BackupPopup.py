# from PyQt4 import QtCore, QtGui
#
# import os
#
# from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil
#
# from ccpn.ui.gui.widgets.CheckBox import CheckBox
# from ccpn.ui.gui.widgets.Frame import Frame
# from ccpn.ui.gui.widgets.Label import Label
# from ccpn.ui.gui.widgets import MessageDialog
# from ccpn.ui.gui.widgets.Entry import Entry
#
# class BackupPopup(QtGui.QDialog):
#
#   # parent mandatory and that needs to have attributes _appBase
#   def __init__(self, parent, title='Auto Backup'):
#
#     QtGui.QDialog.__init__(self, parent=parent)
#     self.setWindowTitle(title)
#
#     preferences = self.parent()._appBase.preferences
#
#     frame = Frame(self)
#
#     row = 0
#     label = Label(frame, text='Auto backup on: ', grid=(row,0))
#     checkbox = CheckBox(frame, checked=preferences.general.autoBackupEnabled, callback=self._toggleBackup, grid=(row, 1))
#
#     row += 1
#     label = Label(frame, text='Auto backup frequency: ', grid=(row,0))
#     entry = Entry(frame, text=str(preferences.general.autoBackupFrequency), callback=self._setBackupFrequency, grid=(row, 1))
#
#   def _toggleBackup(self):
#
#     appBase = self.parent()._appBase
#     preferences = appBase.preferences
#     preferences.general.autoBackupEnabled = not preferences.general.autoBackupEnabled
#     if preferences.general.autoBackupEnabled:
#       appBase.mainWindow._startBackupTimer()
#     else:
#       appBase.mainWindow._stopBackupTimer()
#
#   def _setBackupFrequency(self, value):
#     try:
#       value = int(value)
#     except:
#       return
#
#     appBase = self.parent()._appBase
#     preferences = appBase.preferences
#     preferences.general.autoBackupFrequency = value
#     if preferences.general.autoBackupEnabled:
#       appBase.mainWindow._startBackupTimer()
#
