from PyQt4 import QtCore, QtGui
Qt = QtCore.Qt

from ccpncore.memops.metamodel import Util as metaUtil

from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Entry import Entry
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.MessageDialog import showError
###from ccpn.ui.gui.widgets.WebView import WebViewPanel

from ccpn.util import Register

licenseUrl = 'http://www.ccpn.ac.uk/license'

class RegisterPopup(QtGui.QDialog):

  def __init__(self, parent=None, version='3', title='Register with CCPN', modal=False):
 
    self.version = version
    
    QtGui.QDialog.__init__(self, parent=parent)
    if modal: # Set before visible
      modality = QtCore.Qt.ApplicationModal
      self.setWindowModality(modality)
    self.setWindowTitle(title)

    frame = Frame(self)

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

    buttonFrame = Frame(frame, grid=(row,0), gridSpan=(1,2))
    ##self.licenseButton = Button(buttonFrame, 'Show License', callback=self.toggleLicense, grid=(0,0))
    button = Button(buttonFrame, 'Register', callback=self.register, grid=(0,1))
    row += 1

    ##self.licensePanel = WebViewPanel(frame, url=licenseUrl, grid=(row,0), gridSpan=(1,2))
    ##self.licensePanel.hide()
    #self.resize(300,200)
 
  def toggleLicense(self):

    if self.licensePanel.isVisible():
      self.licensePanel.hide()
      self.resize(300,200)
      self.licenseButton.setText('Show License')
    else:
      self.licensePanel.show()
      self.resize(700,700)
      self.licenseButton.setText('Hide License')

  def register(self):

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

  qtApp = QtGui.QApplication(['Test Register'])

  #QtCore.QCoreApplication.setApplicationName('TestRegister')
  #QtCore.QCoreApplication.setApplicationVersion('0.1')

  popup = RegisterPopup()
  popup.show()
  popup.raise_()

  sys.exit(qtApp.exec_())
