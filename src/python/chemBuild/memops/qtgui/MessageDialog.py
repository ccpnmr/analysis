from PyQt5 import QtCore, QtGui, QtWidgets

Ok          = QtWidgets.QMessageBox.Ok
Cancel      = QtWidgets.QMessageBox.Cancel
Yes         = QtWidgets.QMessageBox.Yes
No          = QtWidgets.QMessageBox.No
Retry       = QtWidgets.QMessageBox.Retry
Ignore      = QtWidgets.QMessageBox.Ignore
Abort       = QtWidgets.QMessageBox.Abort
Close       = QtWidgets.QMessageBox.Close
Information = QtWidgets.QMessageBox.Information
Question    = QtWidgets.QMessageBox.Question
Warning     = QtWidgets.QMessageBox.Warning
Critical    = QtWidgets.QMessageBox.Critical
Save        = QtWidgets.QMessageBox.Save
Discard     = QtWidgets.QMessageBox.Discard

def showInfo(title, message, parent=None):

  dialog = MessageDialog('Information', title, message,
                         Information, parent)

  dialog.setStandardButtons(Ok)
  dialog.exec_()
  
  return 

def showOkCancel(title, message, parent=None):

  dialog = MessageDialog('Query', title, message,
                         Question, parent)

  dialog.setStandardButtons(Ok | Cancel)
  dialog.setDefaultButton(Ok)
  
  return dialog.exec_() == Ok

def showYesNo(title, message, parent=None):


  dialog = MessageDialog('Query', title, message,
                         Question, parent)
                         
  dialog.setStandardButtons(Yes | No)
  dialog.setDefaultButton(Yes)

  return dialog.exec_() == Yes

def showRetryIgnoreCancel(title, message, parent=None):

  dialog = MessageDialog('Retry', title, message,
                         Question, parent)
                         
  dialog.setStandardButtons( Retry | Ignore | Cancel)
  dialog.setDefaultButton(Retry)
  
  result = dialog.exec_()
  
  if result == Retry:
    return True
  
  elif result == Cancel:
    return False
  
  else:
    return None    

def showSaveDiscardCancel(title, message, parent=None):

  dialog = MessageDialog('Query', title, message,
                         Question, parent)
                         
  dialog.setStandardButtons( Save | Discard | Cancel)
  dialog.setDefaultButton(Save)
  
  result = dialog.exec_()
  
  if result == Save:
    return True
  
  elif result == Discard:
    return False
  
  else:
    return None    

def showWarning(title, message, parent=None):

  dialog = MessageDialog('Warning', title, message,
                         Warning, parent)

  dialog.setStandardButtons(Close)
  dialog.exec_()
 
  return

def showMulti(title, message, texts, objects=None, parent=None):

  if objects:
    assert len(objects) == len(texts)

  dialog = MessageDialog('Query', title, message,
                         Question, parent)
  
  for text in texts:
    dialog.addButton(text, QtWidgets.QMessageBox.AcceptRole)
  
  index = dialog.exec_()

  if objects:
    return objects[index]
  
  else:
    return texts[index]  

def showError(title, message, parent=None):
  
  dialog = MessageDialog('Error', title, message,
                         Critical, parent)

  dialog.setStandardButtons(Close)
  dialog.exec_()
  
  return

def showMessage(title, message, icon, parent=None):
  
  dialog = MessageDialog('Message', title, message,
                         icon, parent)

  dialog.setStandardButtons(Close)
  dialog.exec_()
  
  return
  
class MessageDialog(QtWidgets.QMessageBox):

  def __init__(self, title, basicText, message, icon=Information, parent=None):
     
    QtWidgets.QMessageBox.__init__(self, parent)
    
    self.setWindowTitle(title)
    self.setText(basicText)
    self.setInformativeText(message)
    self.setIcon(icon)


if __name__ == '__main__':

  import sys
  from .Application import Application
  from .BasePopup import BasePopup
  from .Button import Button

  def callback():
    print(showMulti('Test', 'Multi Choice', ['Apples', 'Bananas', 'Pears']))
    print(showError('Test', 'This is a test error message'))
    print(showYesNo('Test', 'Yes or No message'))
    print(showOkCancel('Test', 'Ok or Cancel message'))
    print(showRetryIgnoreCancel('Test', 'Some message'))
    print(showWarning('Test', 'Warning message'))
 
  argv = sys.argv
  app = Application(argv)
  popup = BasePopup(title='Test MessageReporter')
  popup.setSize(200,30)
  button = Button(popup, text='hit me', callback=callback)
  app.start()
