"""
This file contains the routines for message dialogues
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2017-04-07 11:41:04 +0100 (Fri, April 07, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtCore, QtGui

from ccpn.ui.gui.guiSettings import messageFont

Ok          = QtGui.QMessageBox.Ok
Cancel      = QtGui.QMessageBox.Cancel
Yes         = QtGui.QMessageBox.Yes
No          = QtGui.QMessageBox.No
Retry       = QtGui.QMessageBox.Retry
Ignore      = QtGui.QMessageBox.Ignore
Abort       = QtGui.QMessageBox.Abort
Close       = QtGui.QMessageBox.Close
Information = QtGui.QMessageBox.Information
Question    = QtGui.QMessageBox.Question
Warning     = QtGui.QMessageBox.Warning
Critical    = QtGui.QMessageBox.Critical
Save        = QtGui.QMessageBox.Save 
Discard     = QtGui.QMessageBox.Discard


class MessageDialog(QtGui.QMessageBox):
  """
  Base class for all dialogues
  Using the 'multiline' to emulate the windowTitle, as on Mac the windows do not get their title
  """
  def __init__(self, title, basicText, message, icon=Information, iconPath=None, parent=None):
    QtGui.QMessageBox.__init__(self, parent)
    self.setFont(messageFont)
    self.setWindowModality(QtCore.Qt.WindowModal)

    self.setWindowTitle(title)
    self.setText(basicText)
    self.setInformativeText(message)
    self.setIcon(icon)
    self.setMinimumWidth(300)

    palette = QtGui.QPalette()
    self.setPalette(palette)

    if iconPath:
      image = QtGui.QPixmap(iconPath)
      scaledImage = image.scaled(48, 48, QtCore.Qt.KeepAspectRatio)
      self.setIconPixmap(scaledImage)


def showInfo(title, message, parent=None, colourScheme=None, iconPath=None):
  """Display an info message
  """
  dialog = MessageDialog('Information', title, message, Information, iconPath, parent)
  dialog.setStandardButtons(Ok)

  #dialog = QtGui.QMessageBox.information(parent, title, message)
  dialog.raise_()
  dialog.exec_()
  return 


def showOkCancel(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Query', title, message, Question, iconPath, parent)

  dialog.setStandardButtons(Ok | Cancel)
  dialog.setDefaultButton(Ok)

  dialog.raise_()
  return dialog.exec_() == Ok


def showYesNo(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Query', title, message, Question, iconPath, parent)
                         
  dialog.setStandardButtons(Yes | No)
  dialog.setDefaultButton(Yes)

  dialog.raise_()
  return dialog.exec_() == Yes


def showRetryIgnoreCancel(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Retry', title, message, Question, iconPath, parent)
                         
  dialog.setStandardButtons( Retry | Ignore | Cancel)
  dialog.setDefaultButton(Retry)
  
  dialog.raise_()
  result = dialog.exec_()
  
  if result == Retry:
    return True

  elif result == Cancel:
    return False

  else:
    return None    


def showSaveDiscardCancel(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Query', title, message, Question, iconPath, parent)
                         
  dialog.setStandardButtons( Save | Discard | Cancel)
  dialog.setDefaultButton(Save)
  
  dialog.raise_()
  result = dialog.exec_()
  
  if result == Save:
    return True

  elif result == Discard:
    return False
  
  else:
    return None    


def showWarning(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Warning', title, message, Warning, iconPath, parent)

  dialog.setStandardButtons(Close)
  dialog.raise_()
  dialog.exec_()
  return

def showOkCancelWarning(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Warning', title, message, Warning, iconPath, parent)

  dialog.setStandardButtons(Ok | Cancel)
  dialog.setDefaultButton(Cancel)

  dialog.raise_()
  return dialog.exec_() == Ok

def showYesNoWarning(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Warning', title, message, Warning, iconPath, parent)

  dialog.setStandardButtons(Yes | No)
  dialog.setDefaultButton(No)

  dialog.raise_()
  return dialog.exec_() == Yes

def showMulti(title, message, texts, objects=None, parent=None, colourScheme=None, iconPath=None):

  if objects:
    assert len(objects) == len(texts)

  dialog = MessageDialog('Query', title, message, Question, iconPath, parent)
  
  for text in texts:
    dialog.addButton(text, QtGui.QMessageBox.AcceptRole)
  
  dialog.raise_()
  index = dialog.exec_()

  if objects:
    return objects[index]
  
  else:
    return texts[index]  

def showError(title, message, parent=None, colourScheme=None, iconPath=None):
  
  dialog = MessageDialog('Error', title, message, Critical, iconPath, parent)

  dialog.setStandardButtons(Close)
  dialog.raise_()
  dialog.exec_()
  return

def showMessage(title, message, parent=None, colourScheme=None, iconPath=None):
  
  dialog = MessageDialog('Message', title, message, Information, iconPath, parent)

  dialog.setStandardButtons(Close)
  dialog.raise_()
  dialog.exec_()
  return


if __name__ == '__main__':

  import sys
  from ccpn.ui.gui.widgets.Application import TestApplication
  from ccpn.ui.gui.widgets.BasePopup import BasePopup
  from ccpn.ui.gui.widgets.Button import Button

  def callback():
    print(showInfo('My info window', 'test info'))
    print(showMulti('Test', 'Multi Choice', ['Apples', 'Bananas', 'Pears']))
    print(showError('Test', 'This is a test error message'))
    print(showYesNo('Test', 'Yes or No message'))
    print(showOkCancel('Test', 'Ok or Cancel message'))
    print(showRetryIgnoreCancel('Test', 'Some message'))
    print(showWarning('Test', 'Warning message'))
 
  app = TestApplication()
  popup = BasePopup(title='Test MessageReporter')
  #popup.setSize(200,30)
  button = Button(popup, text='hit me', callback=callback)
  app.start()
