import pyqtgraph.console as console
from PySide import QtGui

class PythonConsole(console.ConsoleWidget):
  def __init__(self, parent=None, namespace=None, historyFile=None):
    console.ConsoleWidget.__init__(self, parent, namespace)
    # self.console.addAction()
    self.runMacroButton = QtGui.QPushButton()
    # self.console.ui.runMacroButton.setCheckable(True)
    self.runMacroButton.setText('Run Macro')
    self.ui.horizontalLayout.addWidget(self.runMacroButton)
  #
  #
  def runMacro(self):
    print('runMacro')
    # macroFile = QtGui.QFileDialog.getOpenFileName(self, "Run Macro")
    # print(macroFile)

