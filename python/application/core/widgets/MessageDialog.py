from PyQt4 import QtCore, QtGui

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

def showInfo(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Information', title, message,
                         Information, iconPath, colourScheme, parent)

  dialog.setStandardButtons(Ok)
  dialog.raise_()
  dialog.exec_()
  
  return 

def showOkCancel(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Query', title, message,
                         Question, iconPath, colourScheme, parent)

  dialog.setStandardButtons(Ok | Cancel)
  dialog.setDefaultButton(Ok)
  
  dialog.raise_()
  return dialog.exec_() == Ok

def showYesNo(title, message, parent=None, colourScheme=None, iconPath=None):


  dialog = MessageDialog('Query', title, message,
                         Question, iconPath, colourScheme, parent)
                         
  dialog.setStandardButtons(Yes | No)
  dialog.setDefaultButton(Yes)

  dialog.raise_()
  return dialog.exec_() == Yes

def showRetryIgnoreCancel(title, message, parent=None, colourScheme=None, iconPath=None):

  dialog = MessageDialog('Retry', title, message,
                         Question, iconPath, colourScheme, parent)
                         
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

  dialog = MessageDialog('Query', title, message,
                         Question, iconPath, colourScheme, parent)
                         
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

  dialog = MessageDialog('Warning', title, message,
                         Warning, iconPath, colourScheme, parent)

  dialog.setStandardButtons(Close)
  dialog.raise_()
  dialog.exec_()
 
  return

def showMulti(title, message, texts, objects=None, parent=None, colourScheme=None, iconPath=None):

  if objects:
    assert len(objects) == len(texts)

  dialog = MessageDialog('Query', title, message,
                         Question, iconPath, colourScheme, parent)
  
  for text in texts:
    dialog.addButton(text, QtGui.QMessageBox.AcceptRole)
  
  dialog.raise_()
  index = dialog.exec_()

  if objects:
    return objects[index]
  
  else:
    return texts[index]  

def showError(title, message, parent=None, colourScheme=None, iconPath=None):
  
  dialog = MessageDialog('Error', title, message,
                         Critical, iconPath, colourScheme, parent)

  dialog.setStandardButtons(Close)
  dialog.raise_()
  dialog.exec_()
  
  return

def showMessage(title, message, parent=None, colourScheme=None, iconPath=None):
  
  dialog = MessageDialog('Message', title, message,
                         Information, iconPath, colourScheme, parent)

  dialog.setStandardButtons(Close)
  dialog.raise_()
  dialog.exec_()
  
  return
  
class MessageDialog(QtGui.QMessageBox):

  def __init__(self, title, basicText, message, icon=Information, iconPath=None, colourScheme='dark', parent=None):
     
    QtGui.QMessageBox.__init__(self, parent)
    
    self.setWindowTitle(title)
    self.setText(basicText)
    self.setInformativeText(message)
    self.setIcon(icon)
    palette = QtGui.QPalette()
    if iconPath:
      image = QtGui.QPixmap(iconPath)
      scaledImage = image.scaled(64, 64, QtCore.Qt.KeepAspectRatio)
      self.setIconPixmap(scaledImage)

    if colourScheme == 'dark':
      self.setStyleSheet("""  QMessageBox QLabel {
                              color: #f7ffff;
                          }
                          QMessageBox QPushButton {
                            color:  #bec4f3;
                            background-color: #535a83;
                            padding: 2px;
                            border: 1px solid #182548;
                            }

                          """)
      palette.setColor(QtGui.QPalette.Background, QtGui.QColor('#2a3358'))
    elif colourScheme == 'light':
      self.setStyleSheet("""  QMessageBox QLabel {
                              color: #555d85;
                          }""")
      palette.setColor(QtGui.QPalette.Background, QtGui.QColor('#fbf4cc'))
    self.setPalette(palette)

if __name__ == '__main__':

  import sys
  from application.core.widgets.Application import TestApplication
  from application.core.widgets.BasePopup import BasePopup
  from application.core.widgets.Button import Button

  def callback():
    print(showMulti('Test', 'Multi Choice', ['Apples', 'Bananas', 'Pears']))
    print(showError('Test', 'This is a test error message'))
    print(showYesNo('Test', 'Yes or No message'))
    print(showOkCancel('Test', 'Ok or Cancel message'))
    print(showRetryIgnoreCancel('Test', 'Some message'))
    print(showWarning('Test', 'Warning message'))
 
  app = TestApplication()
  popup = BasePopup(title='Test MessageReporter')
  popup.setSize(200,30)
  button = Button(popup, text='hit me', callback=callback)
  app.start()
