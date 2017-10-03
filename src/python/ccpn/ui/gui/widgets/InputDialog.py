from PyQt5 import QtCore, QtGui, QtWidgets


def askPassword(title, prompt, parent=None):
    
  dialog = QtGui.QInputDialog(parent)
  dialog.setInputMode(QtGui.QInputDialog.TextInput)
  dialog.setTextEchoMode( QtWidgets.QLineEdit.Password )
  dialog.setLabelText(prompt)
  dialog.connect(dialog, QtCore.SIGNAL('rejected()'), lambda:dialog.setTextValue(''))  
  dialog.exec_()
  
  return dialog.textValue() or None
 

def askString(title, prompt, initialValue='', parent=None):

  value, isOk =  QtGui.QInputDialog.getText(parent, title, prompt,
                                            text=initialValue)
  
  if isOk:
    return value

def askInteger(title, prompt, initialValue=0, minValue=-2147483647,
               maxValue=2147483647, parent=None):

  value, isOk = QtGui.QInputDialog.getInt(parent, title, prompt, initialValue,
                                          minValue, maxValue)
  if isOk:
    return value

def askFloat(title, prompt, initialValue=0.0, minValue=-2147483647,
             maxValue=2147483647, decimals=6, parent=None):

  value, isOk = QtGui.QInputDialog.getDouble(parent, title, prompt, initialValue,
                                             minValue, maxValue, decimals)
                                             
  if isOk:
    return value

if __name__ == '__main__':
  
  from ccpn.ui.gui.widgets.Application import Application
  
  app = Application()

  print(askString('ask string title', 'ask string prompt', 'Hello'))
  print(askInteger('ask integer title', 'ask integer prompt', 7))
  print(askFloat('ask float title', 'ask float prompt', 3.141593))
  print(askPassword('ask password', 'ask password prompt'))
