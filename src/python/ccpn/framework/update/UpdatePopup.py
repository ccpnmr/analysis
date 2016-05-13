from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
#from ccpn.ui.gui.widgets.Table import ObjectTable, Column

from ccpn.framework.update.UpdateAgent import UpdateAgent

class UpdatePopup(QtGui.QDialog, UpdateAgent):

  def __init__(self, parent=None, title='Update CCPN code'):
 
    version = QtCore.QCoreApplication.applicationVersion()

    QtGui.QDialog.__init__(self, parent=parent)
    UpdateAgent.__init__(self, version)

    #self.appName = QtCore.QCoreApplication.applicationName()

    self.setWindowTitle(title)

    frame = Frame(self)
    row = 0

    #label = Label(frame, 'Server location:', grid=(row, 0))
    #label = Label(frame, self.server, grid=(row, 1))
    #row += 1

    label = Label(frame, 'Installation location:', grid=(row, 0))
    label = Label(frame, text=self.installLocation, grid=(row, 1))
    row += 1

    label = Label(frame, 'Version:', grid=(row, 0))
    label = Label(frame, text=version, grid=(row, 1))
    row += 1

    label = Label(frame, 'Number of updates:', grid=(row, 0))
    self.updatesLabel = Label(frame, text='TBD', grid=(row, 1))
    row += 1


    texts = ('Refresh Updates Information', 'Download and Install Updates')
    callbacks = (self.resetFromServer, self.installUpdates)
    tipTexts = ('Refresh the updates information by querying server and comparing with what is installed locally',
                'Install the updates from the server')
    icons = ('icons/null.png', 'icons/dialog-ok-apply.png')
    buttonList = ButtonList(frame, texts=texts, tipTexts=tipTexts, callbacks=callbacks, icons=icons, grid=(row,0), gridSpan=(1,2))
    row += 1

    self.resize(600,200)
    self.resetFromServer()
 
  def resetFromServer(self):

    UpdateAgent.resetFromServer(self)
    """
    if self.updateFiles:
      n = len(self.updateFiles)
      msg = '%d update%s available' % (n, n > 1 and 's' or '')
    else:
      msg = 'No new updates available'
    #self.messageLabel.set(msg)
    print(msg)
    """
    
    #self.updateTable.setObjects(self.updateFiles)
    self.updatesLabel.set('%d' % len(self.updateFiles))

  #def update(self):

  #  self.updateTable.update()

if __name__ == '__main__':

  import sys

  qtApp = QtGui.QApplication(['Update'])

  QtCore.QCoreApplication.setApplicationName('Update')
  QtCore.QCoreApplication.setApplicationVersion('3.0')

  popup = UpdatePopup()
  popup.raise_()
  popup.show()

  sys.exit(qtApp.exec_())
