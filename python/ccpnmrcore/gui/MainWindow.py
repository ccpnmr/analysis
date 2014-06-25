from PySide import QtCore, QtGui
import sys, os
from ccpnmrcore.modules.SpectrumPane import SpectrumPane
from ccpnmrcore.modules.Spectrum1dPane import Spectrum1dPane
from ccpncore.util import Io as Io
import pyqtgraph.console as console

class MainWindow(QtGui.QMainWindow):

  # pressed = QtCore.Signal(spectrumWidget.viewBox.processmultikeys([int, int]))
  def __init__(self):
    super(MainWindow, self).__init__()

    self.initUi()

  def initUi(self):

    self.layout = QtGui.QHBoxLayout(self)
    self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    self.splitter3 = QtGui.QSplitter(QtCore.Qt.Vertical)
    self.spectrumWidget=Spectrum1dPane()
    self.widget=self.spectrumWidget.widget
    self.currentProject = None
    self.leftWidget = QtGui.QListWidget()
    self.leftWidget.addItem('Drag me!')
    self.leftWidget.setDragDropMode(self.leftWidget.DragOnly)
    self.leftWidget2 = QtGui.QListWidget()
    self.splitter3.addWidget(self.leftWidget)
    self.splitter3.addWidget(self.leftWidget2)
    self.splitter1.addWidget(self.splitter3)
    self.splitter1.addWidget(self.widget)
    self.pythonConsole = console.ConsoleWidget()
    self.pythonConsole.setGeometry(300, 300, 300, 200)
    self.splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
    self.splitter2.addWidget(self.splitter1)
    self.splitter2.addWidget(self.pythonConsole)
    self.layout.addWidget(self.splitter2)
    self.setCentralWidget(self.splitter2)
    QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

    self.addToolBar(QtGui.QToolBar())
    self.statusBar().showMessage('Ready')
    fileMenu = QtGui.QMenu("&Project", self)

    spectrumMenu = QtGui.QMenu("&Spectrum", self)
    windowMenu = QtGui.QMenu("&Window", self)
    # fileMenu.addAction(QtGui.QAction(("Close"), self, shortcut=QtGui.QKeySequence('q','p'),
    #             triggered=self.close))
    fileMenu.addAction(QtGui.QAction("Open Project", self, shortcut=QtGui.QKeySequence("P, O"), triggered=self.openProject))
    fileMenu.addAction(QtGui.QAction("Save Project", self, shortcut=QtGui.QKeySequence("P, S"), triggered=self.saveProject()))
    fileMenu.addAction(QtGui.QAction("Save Project As", self, shortcut=QtGui.QKeySequence("P, A"), triggered=self.saveProjectAs()))
    fileMenu.addAction(QtGui.QAction("Close Program", self, shortcut=QtGui.QKeySequence("Q, T"), triggered=(QtCore.QCoreApplication.instance().quit)))

    windowMenu.addAction(QtGui.QAction("Hide Console", self, shortcut=QtGui.QKeySequence("H, C"),triggered=self.hideConsole))
    windowMenu.addAction(QtGui.QAction("Show Console", self, shortcut=QtGui.QKeySequence("S, C"),triggered=self.showConsole))
    windowMenu.addAction(QtGui.QAction("Show CrossHair", self, shortcut=QtGui.QKeySequence("S, H"), triggered=self.showCrossHair))
    windowMenu.addAction(QtGui.QAction("Hide CrossHair", self, shortcut=QtGui.QKeySequence("H, H"), triggered=self.hideCrossHair))


    self.menuBar().addMenu(fileMenu)
    self.menuBar().addMenu(spectrumMenu)
    self.menuBar().addMenu(windowMenu)

    self.setMenuBar(self.menuBar())

    self.setWindowTitle('Analysis v3')
    self.show()


  def openProject(self):
    self.currentProject = QtGui.QFileDialog.getExistingDirectory(self, 'Open Project')
    Io.loadProject(self.currentProject)
    msg  = (self.currentProject)+' opened'
    self.statusBar().showMessage(msg)
    self.pythonConsole.write("openProject("+self.currentProject+")\n")
    self.pythonConsole.write("for spectrum in spectra:\n  openSpectrum(spectrum)")



  def showCrossHair(self):
    self.spectrumWidget.vLine.show()
    self.spectrumWidget.hLine.show()

  def hideCrossHair(self):
    self.spectrumWidget.vLine.hide()
    self.spectrumWidget.hLine.hide()

  def hideConsole(self):
    self.pythonConsole.hide()

  def showConsole(self):
    self.pythonConsole.show()






def main():

  app = QtGui.QApplication(sys.argv)
  window = MainWindow()
  window.raise_()
  sys.exit(app.exec_())

if __name__ ==  "__main__":
  main()