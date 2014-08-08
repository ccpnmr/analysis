from PySide import QtCore, QtGui
import sys
import random
import numpy as np
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock
import os

from ccpnmrcore.modules.Spectrum1dPane import Spectrum1dPane
from ccpnmrcore.Current import Current
from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
from ccpncore.lib.memops.Implementation.Project import loadDataSource, getSpectrumFileFormat
from ccpncore.gui.Action import Action
from ccpncore.gui.Console import PythonConsole
from ccpncore.gui.MainWindow import MainWindow as GuiMainWindow
from ccpnmrcore.modules.PeakTable import PeakListSimple
from ccpncore.gui.SideBar import SideBar

from ccpn import openProject, newProject

class MainWindow(GuiMainWindow):

  def __init__(self, **kw):
    from ccpncore.util import Translation
    Translation.setTranslationLanguage('Dutch')
    GuiMainWindow.__init__(self, **kw)
    self.project = None
    # project = None
    self.initUi()

  def initUi(self):


    # self.layout = QtGui.QHBoxLayout(self)
    self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    self.splitter3 = QtGui.QSplitter(QtCore.Qt.Vertical)
    self.current = Current()
    self.namespace = {'pg': pg, 'np': np, 'current': self.current, 'openProject':self.openProject}
    self.pythonConsole = PythonConsole(parent=self, namespace=self.namespace)
    self.pythonConsole.setGeometry(300, 300, 300, 200)
    self.spectrumPane=Spectrum1dPane(parent=self, project=self.project, title='Module 1', current=self.current)
    self.moduleCount = 1
    self.widget1=self.spectrumPane.dock
    self.leftWidget = SideBar(parent=self)
    self.leftWidget.setDragDropMode(self.leftWidget.DragDrop)
    self.splitter3.addWidget(self.leftWidget)
    self.splitter1.addWidget(self.splitter3)
    # self.spectrumPane.current = self.current
    self.splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
    self.splitter2.addWidget(self.splitter1)
    self.splitter2.addWidget(self.pythonConsole)
    # self.layout.addWidget(self.splitter2)
    self.current.spectra = []
    self.dockArea = DockArea()

    self.current.pane = self.spectrumPane
    # self.spectrumBarWidget = QtGui.QToolBar()
    # self.spectrumToolbar = QtGui.QToolBar()
    # self.dock1.addWidget(self.spectrumToolbar)
    self.dockArea.addDock(self.widget1)
    self.widget1.name = 'Module %s' % (self.moduleCount+1)

    self.splitter1.addWidget(self.dockArea)
    self.state = None
    self.setCentralWidget(self.splitter2)
    # QtGui.QApplication.setStyle(QtGui.QStyleFactory.create('Cleanlooks'))

    self.statusBar().showMessage('Ready')
    self._menuBar =  QtGui.QMenuBar()
    fileMenu = QtGui.QMenu("&Project", self)

    spectrumMenu = QtGui.QMenu("&Spectrum", self)
    windowMenu = QtGui.QMenu("&Window", self)
    ##fileMenu.addAction(QtGui.QAction("Open Project", self, shortcut="P, O"), triggered=self.openProject))
    fileMenu.addAction(Action(self, "New Project", callback=self.newProject, shortcut="PN"))
    fileMenu.addAction(Action(self, "Open Project", callback=self.openProject, shortcut="PO"))
    fileMenu.addAction(Action(self, "Save Project", callback=self.saveProject, shortcut="PS"))
    fileMenu.addAction(Action(self, "Save Project As", shortcut="PA", callback=self.saveProjectAs))
    fileMenu.addAction(Action(self, "Close Program", callback=QtCore.QCoreApplication.instance().quit, shortcut="QT"))
    spectrumMenu.addAction(Action(self, "Open Spectra", callback=self.loadSpectra, shortcut="FO"))
    spectrumMenu.addAction(Action(self, "Manual Integration", shortcut="MI", callback=self.manualIntegration))
    spectrumMenu.addAction(Action(self, "Automatic Integration", callback=self.automaticIntegration, shortcut="AI"))
    spectrumMenu.addAction(Action(self, "Find Peaks", callback=Spectrum1dItem.findPeaks, shortcut="FP"))
    spectrumMenu.addAction(Action(self, "Peak Table", callback=self.showPeakTable, shortcut="LT"))

    windowMenu.addAction(Action(self, "Hide Console", callback=self.hideConsole, shortcut="HC"))
    windowMenu.addAction(Action(self, "Show Console", callback=self.showConsole, shortcut="SC"))
    windowMenu.addAction(Action(self, "Show CrossHair", callback=self.showCrossHair, shortcut="SH"))
    windowMenu.addAction(Action(self, "Hide CrossHair", callback=self.hideCrossHair, shortcut="HH"))
    windowMenu.addAction(Action(self, "Save State", callback=self.saveState, shortcut="SS"))
    windowMenu.addAction(Action(self, "Restore State", callback=self.restoreState, shortcut="RS"))
    windowMenu.addAction(Action(self, "Add Module", callback=self.addModule, shortcut="AM"))

    # windowMenu.addAction(Action("New Window", self, shortcut="N, W"), callback=self.handleNewWindow))
    self.pythonConsole.runMacroButton.clicked.connect(self.runMacro)
    windowMenu.addAction(Action("Run Macro", self, shortcut="RM", callback=self.runMacro))
    self.windowMenu = windowMenu
    self._menuBar.addMenu(fileMenu)
    self._menuBar.addMenu(spectrumMenu)
    self._menuBar.addMenu(self.windowMenu)
    self.setMenuBar(self._menuBar)
    self._menuBar.setNativeMenuBar(False)
    self.setWindowTitle('Analysis v3')
    self.show()

  def runMacro(self):
    macroFile = QtGui.QFileDialog.getOpenFileName(self, "Run Macro")
    f = open(macroFile[0])
    lines = f.readlines()

    for line in lines:
        print(line)# print(line.strip())
        self.pythonConsole.execSingle(line)
        self.pythonConsole.write(line)

    f.close()

  def addModule(self):
    newModule = Spectrum1dPane(parent=self, title='Module %s' % str(self.moduleCount+1), current=self.current)
    newModule.project = self.project
    print(newModule.project)
    newModule.current = self.current
    self.moduleCount+=1
    self.dockArea.addDock(newModule.dock)

  def saveState(self):
    self.state = self.dockArea.saveState()
    print(self.state)
  def loadState(self):
    self.state = self.dockArea.restoreState(self.state)

  def newProject(self):
    self.project=newProject('defaultProject')
    msg  = (self.project.name)+' created'
    self.statusBar().showMessage(msg)
    self.pythonConsole.write("project = newProject('"+self.project.name+"')\n")
    self.namespace['project'] = self.project

  def openProject(self, projectDir=None):

    if projectDir is None:
      currentProjectDir = QtGui.QFileDialog.getExistingDirectory(self, 'Open Project')

    else:
      currentProjectDir = projectDir
    self.project = openProject(currentProjectDir)
    msg  = (currentProjectDir)+' opened'
    self.leftWidget.fillSideBar(self.project)
    self.spectrumPane.project = self.project
    self.statusBar().showMessage(msg)
    self.pythonConsole.write("project = openProject('"+currentProjectDir+"')\n")
    self.namespace['project'] = self.project

  def showPeakTable(self):

    peakList = PeakListSimple(dimensions=self.current.spectrum.dimensionCount)
    if self.current.spectrum.peaks:
      peakList.updateContents(self.current.spectrum.peakLists)
    peakDock = Dock(name=self.current.spectrum.peakLists[0].pid, size=(1000,1000))
    peakDock.addWidget(peakList)
    self.dockArea.addDock(peakDock)

  def automaticIntegration(spectrum):
    spectrum.automaticIntegration()

  def manualIntegration(self):
    pass

  def loadSpectra(self):
    directory = QtGui.QFileDialog.getOpenFileName(self, 'Open Spectra')
    print(directory)
    dataSource = loadDataSource(self.project._wrappedData.parent,directory[0])
    # spectrum = current._data2Obj[dataSource]
    # print(spectrum)

    if dataSource.numDim == 1:
      data = Spectrum1dItem(self.spectrumPane,dataSource).spectralData
      self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
    # elif dataSource.numDim > 1:
    #   data = SpectrumNdItem(self.spectrumPane,dataSource).spectralData
    #   print(data)
    #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
    msg = dataSource.name+' loaded'
    print(dataSource)
    self.statusBar().showMessage(msg)
    self.pythonConsole.write("project.loadSpectrum('"+directory+"')\n")
    self.pythonConsole.execSingle('c')


      # dirLength=len(os.listdir(directory))
      #
      # print(dirLength)

  def saveProject(self):

    print("project saved")

  def saveProjectAs(self):
    print("project saved as...")


  def showCrossHair(self):
    self.spectrumPane.vLine.show()
    self.spectrumPane.hLine.show()

  def hideCrossHair(self):
    self.spectrumPane.vLine.hide()
    self.spectrumPane.hLine.hide()

  def hideConsole(self):
    self.pythonConsole.hide()

  def showConsole(self):
    self.pythonConsole.show()

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
          global project
          currentProjectDir = filePaths[0]

          self.openProject(projectDir=filePaths[0])
                # peakListItem.setData(0, QtCore.Qt.UserRole + 1, peakList)
                # peakListItem.setData(1, QtCore.Qt.DisplayRole, str(peakList))
          # self.statusBar().showMessage(msg)
          # self.pythonConsole.write("openProject('"+currentProjectDir.name+"')\n")
          # list1 = self.spectrumItem.takeChildren()
          # for item in list1:
          #   print((item.data()))

        else:
          spectrumFormat = getSpectrumFileFormat(filePaths[0])
          print(filePaths)
          print(spectrumFormat)

          if spectrumFormat:
            event.acceptProposedAction()
            dataSource = loadDataSource(self.project,filePaths[0])


          if dataSource.numDim == 1:
            data = Spectrum1dItem(self.spectrumPane,dataSource).spectralData
            self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
          # elif dataSource.numDim > 1:
          #   data = SpectrumNdItem(self.spectrumPane,dataSource).spectralData
          #   print(data)
          #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
            msg = dataSource.name+' loaded'
            self.statusBar().showMessage(msg)
            self.pythonConsole.write("project.loadSpectrum('"+filePaths[0]+"')\n")

          # peakListFormat = getPeakListFileFormat(filePaths[0])
          # if peakListFormat:
          #   event.acceptProposedAction()
          #   self.mainApp.openPeakList(filePaths[0])
          #   return

          else:
            event.ignore()

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