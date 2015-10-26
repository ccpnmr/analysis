from PyQt4 import QtGui, QtCore
from ccpncore.gui.Base import Base
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.TextEditor import TextEditor

from ccpncore.util import Types
from IPython.qt.console.completion_widget import CompletionWidget
from ccpncore.gui.Widget import Widget
from IPython.qt.console.rich_ipython_widget import RichIPythonWidget
from IPython.qt.inprocess import QtInProcessKernelManager



class IpythonConsole(QtGui.QWidget, Base):

    def __init__(self, parent=None, namespace=None, historyFile=None, **kw):

        Widget.__init__(self)
        Base.__init__(self, **kw)

        km = QtInProcessKernelManager()
        km.start_kernel()
        km.kernel.gui = 'qt4'
        kc = km.client()

        self.ipythonWidget = RichIPythonWidget(self, gui_completion='plain')
        self.ipythonWidget._set_font(QtGui.QFont('Lucida Grande', 12))
        self.ipythonWidget.kernel_manager = km
        self.ipythonWidget.kernel_client = kc
        consoleLayout = QtGui.QGridLayout()
        buttonLayout = QtGui.QGridLayout()

        self.textEditor = TextEditor(self)
        self.textEditor.setReadOnly(True)
        self.textEditor.setFont(QtGui.QFont('Lucida Grande', 12))
        self.textEditor.setTextColor(QtGui.QColor('black'))
        # self.textEditor.setFontPointSize(int(10))
        self.a = {'text': ''}
        km.kernel.shell.push(self.a)
        kc.start_channels()
        self.layout().setSpacing(1)
        # self.layout().setContentsMargins(3, 3, 3, 3)
        self.layout().addWidget(self.textEditor, 0, 0)
        self.layout().addLayout(consoleLayout, 1, 0)
        self.layout().addLayout(buttonLayout, 2, 0)

        consoleLayout.addWidget(self.ipythonWidget)

        runMacroButton = QtGui.QPushButton()
        runMacroButton.clicked.connect(self.runMacro)
        runMacroButton.setText('Run Macro')
        buttonLayout.addWidget(runMacroButton)

        historyButton = QtGui.QPushButton()
        historyButton.clicked.connect(self.showHistory)
        historyButton.setText('Show History')
        buttonLayout.addWidget(historyButton, 0, 1)
        km.kernel.shell.push(namespace)


    def runMacro(self, macroFile:str):
      """
      Executes the specified macro file in the python console.
      """
      self.ipythonWidget.execute('%run -i {}'.format(macroFile))


    def showHistory(self):
      """
      Shows the history of commands executed inside the python console.
      """
      self.ipythonWidget.execute('%history')


    def write(self, msg:str, html=False):
        """
        Writes the specified string to the python console text box.
        """
        # print(self.self.ipythonWidget.text())
        self.textEditor.moveCursor(QtGui.QTextCursor.End)
        if html:
            self.textEditor.textCursor().insertHtml(msg)
        else:
          # self.textEditor.textCursor().insertHtml("</div><br><div style='font-weight: normal; background-color: #FFF;'>")
          self.textEditor.insertPlainText(msg)
          self.parent().parent().statusBar().showMessage(msg)
        if self.parent().parent().recordingMacro is True:
          self.parent().parent().macroEditor.textBox.insertPlainText(msg)


    def writeCommand(self, objectName:str, functionCall:str, arguments:Types.List[str], pid:str=None,
                     obj:object=None):
      """
      Writes a command specified by the arguments to the console text box.
      """
      if pid is None:
        pid = obj.pid
      msg1 = "%s = project.getByPid('%s')\n" % (objectName, pid)
      msg2 = '%s(%s)\n' % (functionCall, arguments)

      self.write(msg1)
      self.write(msg2)

    def writeCompoundCommand(self, objectNames:Types.List[str], functionCall:str,
               arguments:Types.List=[str], pids:Types.List[str]=None, objs:Types.List[object]=None):
      """
      Writes a command consisting of a single function call and two pids or objects specified by
      the arguments to the console text box.
      """
      if pids is None:
        pids = [obj.pid for obj in objs]
      msg1 = "%s = project.getByPid('%s')\n" % (objectNames[0], pids[0])
      msg2 = "%s = project.getByPid('%s')\n" % (objectNames[1], pids[1])
      msg3 = '%s(%s)\n' % (functionCall, arguments)
      self.write(msg1)
      self.write(msg2)
      self.write(msg3)

    def writeModuleDisplayCommand(self, moduleCommand:str):
      """
      Writes a module display command to the console text box.
      """
      msg1 = 'application.%s()\n' % moduleCommand
      self.write(msg1)

    def writeWrapperCommand(self, objectNames:Types.List[str], wrapperCommand:str, pid:str,
                            args:Types.List[str]):
      """
      Writes a command dealing with ccpn objects to the console text box.
      """
      msg1 = "%s = project.getByPid('%s')\n" % (objectNames[0], pid)
      msg2 = "%s = %s.%s(%s)\n" % (objectNames[1], objectNames[0], wrapperCommand, args)
      self.write(msg1)
      self.write(msg2)








