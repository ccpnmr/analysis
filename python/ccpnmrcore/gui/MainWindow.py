from PySide import QtCore, QtGui
import sys, os
from ccpnmrcore.modules.SpectrumPane import SpectrumPane
from ccpnmrcore.modules.Spectrum1dPane import Spectrum1dPane
from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
from ccpncore.gui import SideBar
from ccpncore.lib.memops.Implementation.Project import loadDataSource
from ccpncore.util import Io as Io
# from ccpn import openProject
from ccpn.lib import Spectrum as LibSpectrum
import random
import pyqtgraph.console as console
from pyqtgraph.dockarea import DockArea, Dock

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
    self.spectrumWidget2=Spectrum1dPane()
    self.widget1=self.spectrumWidget.widget
    self.widget2=self.spectrumWidget2.widget
    self.leftWidget = SideBar.SideBar(self)
    # self.leftWidget2 = SideBar.SideBar(self)
    # self.leftWidget.setAcceptDrops(True)
    # self.leftWidget.addItem('Spectra')
    # self.leftWidget2.addItem('Peak Lists')
    self.leftWidget.setDragDropMode(self.leftWidget.DragDrop)
    # self.leftWidget2 = QtGui.QListWidget()
    self.splitter3.addWidget(self.leftWidget)
    # self.splitter3.addWidget(self.leftWidget2)
    self.splitter1.addWidget(self.splitter3)
    # self.splitter1.addWidget(self.widget)
    self.pythonConsole = console.ConsoleWidget()
    self.pythonConsole.setGeometry(300, 300, 300, 200)
    self.splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
    self.splitter2.addWidget(self.splitter1)
    self.splitter2.addWidget(self.pythonConsole)
    self.layout.addWidget(self.splitter2)
    self.dockArea = DockArea()
    self.spectrumBarWidget = QtGui.QToolBar()
    self.dock1 = Dock("Module 1", size=(500,300))
    self.dock2 = Dock("Module 2", size=(500,300))
    self.dockArea.addDock(self.dock1, 'left')
    self.dockArea.addDock(self.dock2, 'right')
    # self.widget1.addItem(self.spectrumBarWidget)
    self.dock1.addWidget(self.widget1)
    self.dock2.addWidget(self.widget2)
    self.splitter1.addWidget(self.dockArea)
    self.state = None
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
    fileMenu.addAction(QtGui.QAction("Save Project", self, shortcut=QtGui.QKeySequence("P, S"), triggered=self.saveProject))
    fileMenu.addAction(QtGui.QAction("Save Project As", self, shortcut=QtGui.QKeySequence("P, A"), triggered=self.saveProjectAs))
    fileMenu.addAction(QtGui.QAction("Close Program", self, shortcut=QtGui.QKeySequence("Q, T"), triggered=(QtCore.QCoreApplication.instance().quit)))
    spectrumMenu.addAction(QtGui.QAction("Open Spectra", self, shortcut=QtGui.QKeySequence("F, O"), triggered=self.loadSpectra))

    windowMenu.addAction(QtGui.QAction("Hide Console", self, shortcut=QtGui.QKeySequence("H, C"),triggered=self.hideConsole))
    windowMenu.addAction(QtGui.QAction("Show Console", self, shortcut=QtGui.QKeySequence("S, C"),triggered=self.showConsole))
    windowMenu.addAction(QtGui.QAction("Show CrossHair", self, shortcut=QtGui.QKeySequence("S, H"), triggered=self.showCrossHair))
    windowMenu.addAction(QtGui.QAction("Hide CrossHair", self, shortcut=QtGui.QKeySequence("H, H"), triggered=self.hideCrossHair))
    windowMenu.addAction(QtGui.QAction("Save State", self, shortcut=QtGui.QKeySequence("S, S"), triggered=self.saveState))
    windowMenu.addAction(QtGui.QAction("Restore State", self, shortcut=QtGui.QKeySequence("R, S"), triggered=self.restoreState))
    windowMenu.addAction(QtGui.QAction("New Window", self, shortcut=QtGui.QKeySequence("N, W"), triggered=self.newWindow))

    self.windowMenu = windowMenu
    self.menuBar().addMenu(fileMenu)
    self.menuBar().addMenu(spectrumMenu)
    self.menuBar().addMenu(self.windowMenu)

    self.setMenuBar(self.menuBar())

    self.setWindowTitle('Analysis v3')
    self.show()

  def saveState(self):
    self.state = self.dockArea.saveState()

  def loadState(self):
    self.state = self.dockArea.restoreState(self.state)

  def openProject(self):
    global current
    currentProjectDir = QtGui.QFileDialog.getExistingDirectory(self, 'Open Project')

    current = Io.loadProject(currentProjectDir)
    msg  = (currentProjectDir)+' opened'
    self.statusBar().showMessage(msg)
    self.pythonConsole.write("openProject('"+currentProjectDir+"')\n")


  def loadSpectra(self):
    directory = QtGui.QFileDialog.getOpenFileName(self, 'Open Spectra')
    print(directory)
    dataSource = loadDataSource(current,directory[0])
    # spectrum = current._data2Obj[dataSource]
    # print(spectrum)

    if dataSource.numDim == 1:
      data = Spectrum1dItem(self.spectrumWidget,dataSource).spectralData
      self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
    # elif dataSource.numDim > 1:
    #   data = SpectrumNdItem(self.spectrumWidget,dataSource).spectralData
    #   print(data)
    #   self.widget1.plot(data, pen={'color':(255,0,0)})
    msg = dataSource.name+' loaded'
    self.statusBar().showMessage(msg)
    self.pythonConsole.write("project.loadSpectrum('"+directory+"')\n")


      # dirLength=len(os.listdir(directory))
      #
      # print(dirLength)

  def saveProject(self):
    print("project saved")

  def saveProjectAs(self):
    print("project saved as...")


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

  def newWindow(self):
    self.newWindow = Spectrum1dPane().widget
    self.newDock = Dock("newWindow", size=(500,500))
    self.newDock.addWidget(self.newWindow)
    self.dockArea.addDock(self.newDock)

  def showWindow(self, window):
    window.show()
    window.raise_()

  def dropEvent(self, event):
    '''if object can be dropped into this area, accept dropEvent, otherwise throw an error
        spectra, projects and peak lists can be dropped into this area but nothing else
        if project is dropped, it is loaded,
        if spectra/peak lists are dropped, these are displayed in the side bar but not displayed in
        spectrumPane
        '''

    event.accept()
    data = event.mimeData()
    print(data,"dropped")
    print("dropped")
    if isinstance(self.parent, QtGui.QGraphicsScene):
      event.ignore()
      return

    if event.mimeData().urls():


      filePaths = [url.path() for url in event.mimeData().urls()]

      if filePaths:

        print(filePaths)
        if len(filePaths) == 1:
          global current
          currentProjectDir = filePaths[0]

          current = Io.loadProject(currentProjectDir)
          msg  = (currentProjectDir)+' opened'
          self.statusBar().showMessage(msg)
          self.pythonConsole.write("openProject('"+currentProjectDir+"')\n")
          msg  = (currentProjectDir.name)+' opened'
          print(msg)
          print(current)
          for experiment in current._wrappedData.findAllExperiments():
            print(experiment)
            experimentItem = QtGui.QTreeWidgetItem(self.spectrumItem)
            experimentItem.setText(0,str(experiment.name))
            experimentItem.setData(0, QtCore.Qt.UserRole, experiment)
            # experimentItem.data(0, QtCore.Qt.UserRole).toPyObject()
            dataSource = experiment.findFirstDataSource()
            if dataSource is not None:
              if dataSource.numDim == 1:
                data = Spectrum1dItem(self.spectrumWidget,dataSource).spectralData
                print(data)
                self.widget1.plot(data, pen={'color':(255,0,0)})
              for peakList in dataSource.findAllPeakLists():
                peakListItem = QtGui.QTreeWidgetItem(self.peaksItem)
                peakListItem.setText(0, str(peakList))
                # peakListItem.setData(0, QtCore.Qt.UserRole + 1, peakList)
                # peakListItem.setData(1, QtCore.Qt.DisplayRole, str(peakList))
          # self.statusBar().showMessage(msg)
          # self.pythonConsole.write("openProject('"+currentProjectDir.name+"')\n")
          # list1 = self.spectrumItem.takeChildren()
          # for item in list1:
          #   print((item.data()))

        else:
          pass
          # spectrumFormat = getSpectrumFileFormat(filePaths[0])
          # print(filePaths)
          # print(spectrumFormat)
          #
          # if spectrumFormat:
          #   event.acceptProposedAction()
          #   self.openSpectra(filePaths, replace=replace)
          #   return
          #
          # peakListFormat = getPeakListFileFormat(filePaths[0])
          # if peakListFormat:
          #   event.acceptProposedAction()
          #   self.mainApp.openPeakList(filePaths[0])
          #   return
          #
          # else:
          #   event.ignore()

      else:
        event.ignore()

    else:
      event.ignore()




def main():

  app = QtGui.QApplication(sys.argv)
  window = MainWindow()
  window.raise_()
  sys.exit(app.exec_())

if __name__ ==  "__main__":
  main()