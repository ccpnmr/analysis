from PyQt4 import QtGui
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.guiSettings import fixedWidthFont

from ccpn.ui.gui.widgets.Widget import Widget
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager



class IpythonConsole(Widget, Base):

    def __init__(self, parent=None, namespace=None, mainWindow=None, historyFile=None, **kw):

        Widget.__init__(self, parent=parent)
        Base.__init__(self, **kw)

        km = QtInProcessKernelManager()
        km.start_kernel()
        km.kernel.gui = 'qt4'
        kc = km.client()

        self.mainWindow = mainWindow
        self.ipythonWidget = RichJupyterWidget(self, gui_completion='plain')
        #TODO:GEERTEN: Sort Stylesheet issues
        self.setStyleSheet(self.mainWindow.styleSheet())
        self.ipythonWidget._set_font(fixedWidthFont)
        self.ipythonWidget.kernel_manager = km
        self.ipythonWidget.kernel_client = kc
        #TODO:LUCA:The Widget class already has a layout: can juts do grid=(row,col)
        #use getLayout() of the widget class to get hold of the widget layout in case you need to do something special
        consoleLayout = QtGui.QGridLayout()
        buttonLayout = QtGui.QGridLayout()
        self.setMinimumHeight(100)

        self.textEditor = TextEditor(self)
        self.textEditor.setReadOnly(True)
        kc.start_channels()

        self.layout().setSpacing(1)
        self.layout().addWidget(self.textEditor, 0, 0)
        self.layout().addLayout(consoleLayout, 1, 0)
        self.layout().addLayout(buttonLayout, 2, 0)

        consoleLayout.addWidget(self.ipythonWidget)

        namespace['runMacro'] = self._runMacro


        runMacroButton = QtGui.QPushButton()
        runMacroButton.clicked.connect(self._runMacro)
        runMacroButton.setText('Run Macro')
        buttonLayout.addWidget(runMacroButton)

        historyButton = QtGui.QPushButton()
        historyButton.clicked.connect(self._showHistory)
        historyButton.setText('Show History')
        buttonLayout.addWidget(historyButton, 0, 1)
        km.kernel.shell.push(namespace)


    def setProject(self, project):
      self.project = project

    def _runMacro(self, macroFile:str):
      """
      # CCPN INTERNAL - called in runMacro method of GuiMainWindow.
      Executes the specified macro file in the python console.
      """
      if macroFile:
        self.ipythonWidget.execute('%run -i {}'.format(macroFile))


    def _showHistory(self):
      """
      Shows the history of commands executed inside the python console.
      """
      self.ipythonWidget.execute('%history')


    def _write(self, msg:str=None, html=False):
      """
      writes the specified string to the python console text box.
      """
      self.textEditor.moveCursor(QtGui.QTextCursor.End)
      if html:
          self.textEditor.textCursor().insertHtml(msg)
      else:
        # self.textEditor.textCursor().insertHtml("</div><br><div style='font-weight: normal; background-color: #FFF;'>")
        self.textEditor.insertPlainText(msg)
        # self.textEditor.insertPlainText('\n')
        self.mainWindow.statusBar().showMessage(msg)
      if self.mainWindow.recordingMacro is True:
        self.mainWindow.macroEditor.textBox.insertPlainText(msg)


    def _setUndoWaypoint(self):
      """Set Undo waypoint, if undo is present"""
      if hasattr(self, 'project'):
        undo = self.project._undo
        if undo is not None:
          undo.newWaypoint()



    def writeConsoleCommand(self, command:str, **objectParameters):
      """Set keyword:value objectParameters to point to the relevant objects,
      echo command in console, and set Undo

      Example calls:

      writeConsoleCommand("application.createSpectrumDisplay(spectrum)", spectrum=spectrumOrPid)

      writeConsoleCommand(
         "newAssignment = peak.assignDimension(axisCode=%s, value=[newNmrAtom]" % axisCode,
         peak=peakOrPid)
      """

      # write lines getting objects by their Pids

      for parameter in sorted(objectParameters):
        value = objectParameters[parameter]
        if not isinstance(value, str):
          value = value.pid
        self._write("%s = project.getByPid('%s')\n" % (parameter, value))

      # execute command
      self._write(msg=command)

      # set undo step
      self._setUndoWaypoint()








