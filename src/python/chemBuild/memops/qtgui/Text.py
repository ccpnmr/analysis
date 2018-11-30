from PyQt5 import QtCore, QtGui, QtWidgets

from .Base import Base

class Text(QtWidgets.QPlainTextEdit, Base):

  def __init__(self, parent, text='', callback=None, wrap=False, readOnly=False, **kw):
    
    QtWidgets.QPlainTextEdit.__init__(self, text, parent)
    Base.__init__(self, parent, **kw)
    
    if wrap:
      self.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
    else:
      self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
    
    self.setReadOnly(readOnly)
    self.callback = callback
    self._isUserModified = False
   
    self.connect(self, QtCore.SIGNAL('textChanged()'), self._textChanged)
  
  def _textChanged(self):
  
    self._isUserModified = True
  
  def leaveEvent(self, event):
  
    QtWidgets.QPlainTextEdit.leaveEvent(self, event)
    
    if self._isUserModified and self.callback:
      self.callback()
      self._isUserModified = False
    
  def clearText(self):
    
    self.clear()
    self._isUserModified = False

  def getText(self):

    return self.toPlainText()

  def setText(self, text):
    
    self.setPlainText(text)
    self._isUserModified = False
    
  def addText(self, text):
  
    self.appendPlainText(text)
    self._isUserModified = False

import sys
from code import InteractiveConsole
from io import StringIO
  
class Console(QtWidgets.QPlainTextEdit, Base):
  
  def __init__(self, parent, message='', context=None, prompt='>>> ', **kw):
    
    major, minor, micro, rel, serial = sys.version_info
    startup = 'Python %d.%d.%d on %s' % (major, minor, micro, sys.platform)
    
    QtWidgets.QPlainTextEdit.__init__(self, startup, parent)
    Base.__init__(self, parent, **kw)

    if message:
      self.write(message)
    
    self.setLineWrapMode(self.NoWrap)
    self.setReadOnly(False)
    self.setUndoRedoEnabled(False)
    self.document().setDefaultFont(QtGui.QFont("monospace", 10, QtGui.QFont.Normal))
    
    self.prompt = prompt
    if context:
      if isinstance(context, dict):
        context = dict(context)
      else:
        context = context.__dict__
      self.shell = InteractiveConsole(locals=context)
    else:
      self.shell = InteractiveConsole(locals=locals())
    
    self.history = []
    self.historyPos = 0
    self._pos = 0
    self.promptLen = len(prompt)
    self.inBlock = False
    
    self._prompt()

  
  def _prompt(self):
  
    if self.inBlock:
      prompt = '.' * (self.promptLen-1)
      prompt+= ' '
    else:
      prompt = self.prompt
    
    self.appendPlainText(prompt)
    self.moveCursor(QtGui.QTextCursor.End)
    self._pos = self.textCursor().position()
  
  def write(self, text):
    
    text = text.rstrip()
    if text:
      self.appendPlainText(text)
                
  def _issueLine(self):
  
    text = self.getLastLine()
    
    if text:
      self.appendHistory(text)
    
    stdout = sys.stdout
    stderr = sys.stderr
    
    sys.stdout = self
    sys.stderr = self

    self.inBlock = self.shell.push(text)
      
    sys.stdout = stdout
    sys.stderr = stderr
    
    QtCore.QCoreApplication.processEvents()
      
    self._prompt()
    
    
  def keyPressEvent(self, event):
    
    key = event.key()
    
    pos = self.textCursor().position()
    
    if pos < self._pos:
      self.moveCursor(QtGui.QTextCursor.End)
      
    if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
      self._issueLine()
      return
    
    elif key == QtCore.Qt.Key_Home:
      self.setLinePos(0)
      return
      
    elif key == QtCore.Qt.Key_PageUp:
      return
        
    elif key in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace):
      if self.getLinePos() == 0:
        return
          
    elif key == QtCore.Qt.Key_Up:
      self.prevHistory()
      return
        
    elif key == QtCore.Qt.Key_Down:
      self.nextHistory()
      return
        
    elif key == QtCore.Qt.Key_D and event.modifiers() == QtCore.Qt.ControlModifier:
      self.close()
      
    QtWidgets.QPlainTextEdit.keyPressEvent(self, event)
    
  def getLastLine(self):
  
    document = self.document()
    last = document.lineCount() - 1
    text = document.findBlockByLineNumber(last).text()
    text = text.rstrip()
    
    return str(text[self.promptLen:])
    
  def setLastLine(self, text):

    self.moveCursor(QtGui.QTextCursor.End)
    self.moveCursor(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.KeepAnchor)
    for i in range(self.promptLen):
      self.moveCursor(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
      
    self.textCursor().removeSelectedText()
    self.textCursor().insertText(text)
    self.moveCursor(QtGui.QTextCursor.End)
    
  def appendHistory(self, text):
  
     if text:
       if self.history:
         if self.history[-1] != text:
           self.history.append(text)
       
       else:
         self.history.append(text)
       
     self.historyPos = len(self.history)

  def prevHistory(self):
  
    if self.history:
      self.historyPos -= 1
      self.historyPos = max(0, self.historyPos)
      
      self.setLastLine( self.history[self.historyPos] )

  def nextHistory(self):
  
    if self.history:
      n = len(self.history)
      self.historyPos += 1
      self.historyPos = min(n-1, self.historyPos)
      
      if self.historyPos < n:
        self.setLastLine( self.history[self.historyPos] )

  def getLinePos(self):
    
    return self.textCursor().columnNumber() - self.promptLen
    
  def setLinePos(self, p):
    
    self.moveCursor(QtGui.QTextCursor.StartOfLine)
    
    for i in range(self.promptLen + p):
      self.moveCursor(QtGui.QTextCursor.Right)
 
  def clearConsole(self):
    
    self.clear()
    self.shell.resetbuffer()
    self._prompt()

if __name__ == '__main__':

  from .Application import Application
  from .Menu import Menu
  
  import string
  
  def callback():
    print("Editing done")
  
  app = Application()

  window = QtWidgets.QWidget()
  
  text = Text(window, 'Initial text', callback)
  
  text.addText('Pugh,\nPugh,\nBarney McGrew,\nCuthbert,\nDibble,\nGrubb.\n')

  text.addText('\n\n%s\n' % (string.letters))
  

  text2 = Text(window, 'Initial text', callback, wrap=True)
  text2.setText('With wrapping\n%s\n' % (string.letters))
  
  console = Console(window, '[Python Console Widget]', app)
  
  window.show()
  
  app.start()

