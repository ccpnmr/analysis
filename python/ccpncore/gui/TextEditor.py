import sys
import os
from PySide import QtGui

class TextEditor(QtGui.QTextEdit):

   def __init__(self, filename=None):
      super(TextEditor, self).__init__()
      #font = QFont("Courier", 11)
      #self.setFont(font)
      self.filename = filename
      if self.filename is not None:

        fileData = self.filename.read()
        print(fileData)
        self.setText(fileData)

      self.show()

