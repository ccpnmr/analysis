from PyQt4 import QtGui, QtCore
from ccpncore.gui.Base import Base
from ccpncore.gui.Dock import CcpnDock
from ccpncore.gui.TextEditor import TextEditor
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
        kc.start_channels()
        self.ipythonWidget = RichIPythonWidget(self)
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


    def runMacro(self):
        macroFile = QtGui.QFileDialog.getOpenFileName(self, "Run Macro")
        if macroFile:
            # The -i argument runs the macro within the namespace
            # of the teminal, which can be handy. In this way you
            # have access to things like current.peaks, which the
            # user most likely expects.
            self.ipythonWidget.execute('%run -i {}'.format(macroFile))

    def showHistory(self):
        self.self.ipythonWidget.execute('%history')

    def write(self, msg, html=False):
        '''Not implemented. I don't know yet how to write something
           to the input line without executing it.

        '''
        # print(self.self.ipythonWidget.text())
        print(msg, 'message here')
        self.textEditor.moveCursor(QtGui.QTextCursor.End)
        if html:
            self.textEditor.textCursor().insertHtml(msg)
        else:
          # self.textEditor.textCursor().insertHtml("</div><br><div style='font-weight: normal; background-color: #FFF;'>")
          self.textEditor.insertPlainText(msg)








