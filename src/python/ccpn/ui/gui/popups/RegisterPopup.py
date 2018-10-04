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
__dateModified__ = "$dateModified: 2017-07-07 16:32:49 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore, QtGui, QtWidgets
Qt = QtCore.Qt

from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.Entry import Entry
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.MessageDialog import showError
from ccpn.framework.PathsAndUrls import ccpnUrl
###from ccpn.ui.gui.widgets.WebView import WebViewPanel
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb

from ccpn.util import Register


licenseUrl = ccpnUrl + '/license'

# class RegisterPopup(QtWidgets.QDialog):
class RegisterPopup(CcpnDialog):
  def __init__(self, parent=None, version='3', title='Register with CCPN', modal=False, **kw):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    self.version = version
    
    if modal: # Set before visible
      modality = QtCore.Qt.ApplicationModal
      self.setWindowModality(modality)
    self.setWindowTitle(title)
    self.setMinimumSize(700,350)

    frame = Frame(self, setLayout=True, grid=(0,0))

    message = '''To keep track of our users, which is important for grant applications,
we would like you to register your contact details with us.
This needs to be done once on every computer you use the programme on.
'''
    label = Label(frame, message, grid=(0,0), gridSpan=(1,2))

    row = 1
    self.entries = []
    registrationDict = Register.loadDict()
    for attr in Register.userAttributes:
      label = Label(frame, metaUtil.upperFirst(attr), grid=(row,0))
      text = registrationDict.get(attr, '')
      entry = Entry(frame, text=text, grid=(row,1), maxLength=60)
      self.entries.append(entry)
      row += 1

    licenseFrame = Frame(frame,setLayout=True, grid=(row, 0), gridSpan=(1,2))
    row += 1

    self.licenseCheckBox = CheckBox(licenseFrame,
                                    text='I have read and agree to the terms and conditions of the license',
                                    callback=self._toggledCheckBox, grid=(0,0))
    self.licenseCheckBox.setChecked(False)
    button = Button(licenseFrame, text='Show License', callback=self._showLicense, grid=(0,1))

    buttonFrame = Frame(frame,setLayout=True, grid=(row,0), gridSpan=(1,2))
    ##self.licenseButton = Button(buttonFrame, 'Show License', callback=self.toggleLicense, grid=(0,0))
    self.registerButton = Button(buttonFrame, 'Register', callback=self._register, grid=(0, 1))
    self.registerButton.setEnabled(False)
    row += 1

    ##self.licensePanel = WebViewPanel(frame, url=licenseUrl, grid=(row,0), gridSpan=(1,2))
    ##self.licensePanel.hide()
    #self.resize(300,200)

  def _toggledCheckBox(self, *args, **kw):
    self.registerButton.setEnabled(self.licenseCheckBox.isChecked())

  def _showLicense(self):
    self.parent().application.showLicense()

  # def _toggleLicense(self):
  #
  #   if self.licensePanel.isVisible():
  #     self.licensePanel.hide()
  #     self.resize(300,200)
  #     self.licenseButton.setText('Show License')
  #   else:
  #     self.licensePanel.show()
  #     self.resize(700,700)
  #     self.licenseButton.setText('Hide License')

  def _register(self):

    registrationDict = {}
    for n, attr in enumerate(Register.userAttributes):
      entry = self.entries[n]
      registrationDict[attr] = entry.get() or ''
      
    Register.setHashCode(registrationDict)
    Register.saveDict(registrationDict)
    Register.updateServer(registrationDict, self.version)
    
    if self.isModal():
      self.close()


if __name__ == '__main__':

  import sys

  qtApp = QtWidgets.QApplication(['Test Register'])

  #QtCore.QCoreApplication.setApplicationName('TestRegister')
  #QtCore.QCoreApplication.setApplicationVersion('0.1')

  popup = RegisterPopup()
  popup.show()
  popup.raise_()

  sys.exit(qtApp.exec_())
