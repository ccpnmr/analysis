import pyqtgraph.console as console
from PySide import QtGui

class PythonConsole:
  def __init__(self, parent=None):
    self.parent = parent
    self.console = console.ConsoleWidget()
    # self.console.addAction()
    self.runMacroButton = QtGui.QPushButton()
    # self.console.ui.runMacroButton.setCheckable(True)
    self.runMacroButton.setText('Run Macro')
    self.console.ui.horizontalLayout.addWidget(self.runMacroButton)
  #
  #
  def runMacro(self):
    print('runMacro')
    # macroFile = QtGui.QFileDialog.getOpenFileName(self, "Run Macro")
    # print(macroFile)

