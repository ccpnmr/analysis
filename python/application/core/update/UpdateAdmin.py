import os

from PyQt4 import QtCore, QtGui
from ccpncore.gui.ButtonList import ButtonList
from ccpncore.gui.Frame import Frame
from ccpncore.gui.Label import Label
from ccpncore.gui.Table import ObjectTable, Column
from application.core.update.UpdateAgent import UpdateAgent

SERVER_USER = 'ccpn'

class UpdateAdmin(QtGui.QDialog, UpdateAgent):

  def __init__(self, parent=None, title='Update Administrator', serverUser=SERVER_USER):
 
    version = QtCore.QCoreApplication.applicationVersion()

    QtGui.QDialog.__init__(self, parent=parent)
    UpdateAgent.__init__(self, version, serverUser=serverUser)

    self.defaultDirectory = self.installLocation

    self.setWindowTitle(title)

    frame = Frame(self)
    row = 0

    label = Label(frame, 'Installation location:', grid=(row, 0))
    label = Label(frame, text=self.installLocation, grid=(row, 1))
    row += 1

    label = Label(frame, 'Version:', grid=(row, 0))
    label = Label(frame, text=self.version, grid=(row, 1))
    row += 1

    columns = [ \
      Column('Commit', 'shouldCommit', tipText='Whether this file should be committed', setEditValue=self.toggleShouldCommit, getColor=self.getColor),
      Column('File', 'fileName', tipText='File name', getColor=self.getColor),
      Column('Local Date', 'fileLocalDateTime', tipText='Date/time the file was last updated locally', getColor=self.getColor),
      Column('Server Date', 'fileServerDateTime', tipText='Date/time the file was last updated on the server', getColor=self.getColor),
      Column('Path', 'fileDir', tipText='Path for file from installation location', getColor=self.getColor),
    ]

    self.updateTable = ObjectTable(frame, columns, grid=(row,0), gridSpan=(1,2))
    row += 1

    texts = ('Refresh Data', 'Add Files', 'Diff Highlighted', 'Commit Selected')
    callbacks = (self.resetFromServer, self.addLocalFiles, self.diffSelected, self.commitChosen)
    tipTexts = ('Refresh the table (updating for changes on server or locally)',
                'Add local files to the list, which can then be committed',
                'Diff the highlighted files local versus server to the console',
                'Commit the files selected with the check box to the server')
    nullIcon = 'icons/null.png'
    icons = (nullIcon, nullIcon, nullIcon, nullIcon)
    buttonList = ButtonList(frame, texts=texts, callbacks=callbacks, icons=icons, grid=(row,0), gridSpan=(1,2))
    row += 1

    self.resize(600,200)
    self.resetFromServer()
 
  def getColor(self, updateFile):

    if updateFile in self.colorCache:
      return self.colorCache[updateFile]

    if updateFile.isNew:
      color = QtGui.QColor('#B0FFB0')
    elif self.isUpdateDifferent(updateFile.filePath, updateFile.fileHashCode):
      color = QtGui.QColor('#FFB0B0')
    else:
      color = None

    self.colorCache[updateFile] = color

    return color

  def resetFromServer(self):

    UpdateAgent.resetFromServer(self)

    self.colorCache = {}
    self.updateTable.setObjects(self.updateFiles)

  def addLocalFiles(self):

    dialog = QtGui.QFileDialog(self, caption='Select files to add')
    dialog.setFileMode(QtGui.QFileDialog.AnyFile)
    dialog.setDirectory(self.defaultDirectory)
    if not dialog.exec_():
      return
    filePaths = dialog.selectedFiles()
    if not filePaths:
      return

    if filePaths:
      directory = os.path.dirname(filePaths[0])
      if os.path.exists(directory):
        self.defaultDirectory = directory
      self.addFiles(filePaths)
      self.updateTable.setObjects(self.updateFiles)

  def diffSelected(self):

    updateFiles = self.updateTable.getSelectedObjects()
    if updateFiles:
      self.diffUpdates(updateFiles)

  def toggleShouldCommit(self, updateFile, value):

    updateFile.shouldCommit = value

  def update(self):

    self.updateTable.update()

if __name__ == '__main__':

  import sys
  from ccpn.lib.Version import applicationVersion

  qtApp = QtGui.QApplication(['UpdateAdmin',])

  QtCore.QCoreApplication.setApplicationName('UpdateAdmin')
  QtCore.QCoreApplication.setApplicationVersion(applicationVersion)

  popup = UpdateAdmin()
  popup.raise_()
  popup.show()

  sys.exit(qtApp.exec_())
