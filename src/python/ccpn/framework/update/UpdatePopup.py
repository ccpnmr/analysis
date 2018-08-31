"""
Module Documentation Here
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:20 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:40 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets

from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
#from ccpn.ui.gui.widgets.Table import ObjectTable, Column

from ccpn.framework.update.UpdateAgent import UpdateAgent


# class UpdatePopup(QtWidgets.QDialog, UpdateAgent):
class UpdatePopup(CcpnDialog, UpdateAgent):
  def __init__(self, parent=None, mainWindow=None, title='Update CCPN code', **kw):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    version = QtCore.QCoreApplication.applicationVersion()
    # QtWidgets.QDialog.__init__(self, parent=parent)
    UpdateAgent.__init__(self, version)

    #self.appName = QtCore.QCoreApplication.applicationName()

    self.setWindowTitle(title)

    # frame = Frame(self, setLayout=True)   # ejb
    row = 0

    #label = Label(self, 'Server location:', grid=(row, 0))
    #label = Label(self, self.server, grid=(row, 1))
    #row += 1

    label = Label(self, 'Installation location:', grid=(row, 0))
    label = Label(self, text=self.installLocation, grid=(row, 1))
    row += 1

    label = Label(self, 'Version:', grid=(row, 0))
    label = Label(self, text=version, grid=(row, 1))
    row += 1

    label = Label(self, 'Number of updates:', grid=(row, 0))
    self.updatesLabel = Label(self, text='TBD', grid=(row, 1))
    row += 1


    texts = ('Refresh Updates Information', 'Download and Install Updates', 'Close')
    callbacks = (self.resetFromServer, self.installUpdates, self.hide)
    tipTexts = ('Refresh the updates information by querying server and comparing with what is installed locally',
                'Install the updates from the server',
                'Close update dialog')
    icons = ('icons/null.png', 'icons/dialog-apply.png', 'icons/window-close.png')
    buttonList = ButtonList(self, texts=texts, tipTexts=tipTexts, callbacks=callbacks, icons=icons, grid=(row,0), gridSpan=(1,2))
    row += 1

    # self.resize(600,150)
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

  qtApp = QtWidgets.QApplication(['Update'])

  QtCore.QCoreApplication.setApplicationName('Update')
  QtCore.QCoreApplication.setApplicationVersion('3.0')

  popup = UpdatePopup()
  popup.raise_()
  popup.show()

  sys.exit(qtApp.exec_())
