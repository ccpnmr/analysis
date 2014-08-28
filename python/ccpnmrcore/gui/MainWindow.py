from PySide import QtCore, QtGui
import os
import sys
import random
import numpy as np
import json
from functools import partial
import pyqtgraph as pg
from pyqtgraph.dockarea import DockArea, Dock

from ccpnmrcore.modules.Spectrum1dPane import Spectrum1dPane
from ccpnmrcore.modules.SpectrumNdPane import SpectrumNdPane
from ccpnmrcore.Current import Current
from ccpnmrcore.modules.spectrumPane.Spectrum1dItem import Spectrum1dItem
from ccpncore.lib.memops.Implementation.Project import loadDataSource, getSpectrumFileFormat
from ccpncore.gui.Action import Action
from ccpncore.gui.Console import PythonConsole
from ccpncore.gui.MainWindow import MainWindow as GuiMainWindow
from ccpnmrcore.modules.PeakTable import PeakListSimple
from ccpncore.gui.SideBar import SideBar
from ccpncore.gui.TextEditor import TextEditor
from ccpnmrcore.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup
from ccpnmrcore.popups.PreferencesPopup import PreferencesPopup
from ccpncore.util.AttrDict import AttrDict
from difflib import Differ

from ccpn import openProject, newProject


class MainWindow(GuiMainWindow):

  def __init__(self, project=None, **kw):
    GuiMainWindow.__init__(self, **kw)
    self.initUi(project)
    screen = QtGui.QDesktopWidget().screenGeometry()
    self.setGeometry(0, 0, screen.width(), screen.height())
    self.setProject(project)

  def initUi(self, project):

    self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    self.splitter3 = QtGui.QSplitter(QtCore.Qt.Vertical)
    self.current = Current()
    self.panes = {}
    self.setupPreferences()
    self.namespace = {'pg': pg, 'np': np, 'current': self.current, 'openProject':self.openProject,
                      'newProject':self.newProject, 'loadSpectrum':self.loadSpectra, 'self':self,
                      'panes':self.panes, 'preferences':self.preferences}
    self.pythonConsole = PythonConsole(parent=self, namespace=self.namespace)
    self.pythonConsole.setGeometry(1200, 700, 10, 1)
    
    ###self.spectrumPane=Spectrum1dPane(parent=self, project=self.project, title='Module 1', current=self.current, pid='QP:1', preferences=self.preferences)
    self.spectrumPane1=Spectrum1dPane(project=project, title='Module 1_1D', current=self.current,
                                     pid='QP:1', preferences=self.preferences, mainWindow=self)
    self.spectrumPane2=SpectrumNdPane(project=project, title='Module 2_ND', current=self.current,
                                     pid='QP:2', preferences=self.preferences, mainWindow=self)
    self.panes[self.spectrumPane1.pid] = self.spectrumPane1
    self.panes[self.spectrumPane2.pid] = self.spectrumPane2
    self.moduleCount = 2
    self.widget1=self.spectrumPane1.dock
    self.widget2=self.spectrumPane2.dock
    self.leftWidget = SideBar(parent=self)
    self.leftWidget.setDragDropMode(self.leftWidget.DragDrop)
    self.leftWidget.setGeometry(0, 0, 10, 600)
    self.leftWidget.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)
    self.splitter3.addWidget(self.leftWidget)
    self.splitter1.addWidget(self.splitter3)
    self.splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
    self.splitter2.addWidget(self.splitter1)
    self.splitter2.heightMax = 200
    self.leftWidget.itemDoubleClicked.connect(self.raiseSpectrumProperties)
    self.pythonConsole.heightMax = 200
    self.splitter2.addWidget(self.pythonConsole)
    self.pythonConsole.hide()
    self.pythonConsoleShown = False
    self.splitter2.setGeometry(QtCore.QRect(1200, 1300, 100, 100))
    self.current.spectra = []
    self.dockArea = DockArea()
    self.dockArea.setGeometry(0, 0, 1100, 1300)
    self.current.pane = self.spectrumPane1
    self.dockArea.addDock(self.widget1)
    self.dockArea.addDock(self.widget2)
    self.splitter1.addWidget(self.dockArea)
    self.state = None
    self.setCentralWidget(self.splitter2)
    self.statusBar().showMessage('Ready')
    self._menuBar =  QtGui.QMenuBar()


    fileMenu = QtGui.QMenu("&Project", self)
    spectrumMenu = QtGui.QMenu("&Spectra", self)
    viewMenu = QtGui.QMenu("&View", self)
    moleculeMenu = QtGui.QMenu("&Molecules", self)
    restraintsMenu = QtGui.QMenu("&Restraints", self)
    structuresMenu = QtGui.QMenu("&Structures", self)
    macroMenu = QtGui.QMenu("Macro", self)
    helpMenu = QtGui.QMenu("&Help", self)

    fileMenu.addAction(Action(self, "New", callback=self.newProject, shortcut="PN"))
    fileMenu.addAction(Action(self, "Open...", callback=self.openProject, shortcut="PO"))
    self.recentProjectsMenu = fileMenu.addMenu("Open Recent")
    self.fillRecentProjectsMenu()
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Save", callback=self.saveProject, shortcut="PS"))
    fileMenu.addAction(Action(self, "Save As...", shortcut="PA", callback=self.saveProjectAs))
    backupOption = fileMenu.addMenu("Backup")
    backupOption.addAction(Action(self, "Save", callback=self.saveBackup))
    backupOption.addAction(Action(self, "Restore", callback=self.restoreBackup))
    fileMenu.addSeparator()
    fileMenu.addAction(QtGui.QAction("Undo", self, triggered=self.undo, shortcut=QtGui.QKeySequence("Ctrl+Z")))
    fileMenu.addAction(QtGui.QAction("Redo", self, triggered=self.redo, shortcut=QtGui.QKeySequence("Ctrl+Y")))
    logOption = fileMenu.addMenu("Log File")
    logOption.addAction(Action(self, "Save As...", callback=self.saveLogFile))
    logOption.addAction(Action(self, "Clear", callback=self.clearLogFile))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Summary...", self.displayProjectSummary))
    fileMenu.addAction(Action(self, "Archive...", self.archiveProject))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Preferences...", callback=self.showApplicationPreferences))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Close Program", callback=self.quitAction, shortcut="QT"))

    spectrumMenu.addAction(Action(self, "Add...", callback=self.loadSpectra, shortcut="FO"))
    spectrumMenu.addAction(Action(self, "Remove...", callback=self.removeSpectra))
    spectrumMenu.addAction(Action(self, "Rename...", callback=self.renameSpectra))
    spectrumMenu.addAction(Action(self, "Reload", callback=self.reloadSpectra))
    spectrumMenu.addSeparator()
    spectrumMenu.addAction(Action(self, "Print...", callback=self.printSpectrum))
    spectrumMenu.addSeparator()
    spectrumMenu.addAction(Action(self, "Show in Finder", callback=self.showSpectrumInFinder))
    spectrumMenu.addAction(Action(self, "Copy into Project", callback=self.copySpectrumIntoProject))
    spectrumMenu.addAction(Action(self, "Move out of Project", callback=self.moveSpectrumOutOfProject))
    spectrumMenu.addSeparator()
    spectrumPeaksMenu = spectrumMenu.addMenu("Peaks")
    spectrumPeaksMenu.addAction(Action(self, "Import...", callback=self.importPeaksPopup))
    spectrumPeaksMenu.addAction(Action(self, "Delete...", callback=self.deletePeaksPopup))
    spectrumPeaksMenu.addSeparator()
    spectrumPeaksMenu.addAction(Action(self, "Print to File", callback=self.printPeaksToFile))

    newMoleculeMenu = moleculeMenu.addMenu("New")
    newMoleculeMenu.addAction(Action(self, "From Fasta...", callback=self.createMoleculeFromFasta))
    newMoleculeMenu.addAction(Action(self, "From PDB...", callback=self.createMoleculeFromPDB))
    newMoleculeMenu.addAction(Action(self, "From NEF...", callback=self.createMoleculeFromNEF))
    newMoleculeMenu.addAction(Action(self, "Interactive...", callback=self.showMoleculePopup))
    moleculeMenu.addAction(Action(self, "Inspect...", callback=self.inspectMolecule))
    moleculeMenu.addSeparator()
    moleculeMenu.addAction(Action(self, "Run ChemBuild", callback=self.runChembuild))

    macroMenu.addAction(Action(self, "Edit...", callback=self.editMacro))
    macroMenu.addAction(Action(self, "New From Logfile...", callback=self.newMacroFromLog))
    macroRecordMenu = macroMenu.addMenu("Record")
    macroRecordMenu.addAction(Action(self, "Start", callback=self.startMacroRecord))
    macroRecordMenu.addAction(Action(self, "Stop", callback=self.stopMacroRecord))
    macroRecordMenu.addAction(Action(self, "Save As...", callback=self.saveRecordedMacro))
    macroMenu.addSeparator()
    macroMenu.addAction(Action(self, "Run...", shortcut="RM", callback=self.runMacro))
    macroMenu.addAction(Action(self, "Run Recent", callback=self.showRecentMacros))
    macroMenu.addSeparator()
    macroMenu.addAction(Action(self, "Define User Shortcuts...", callback=self.defineUserShortcuts))

    viewNewMenu = viewMenu.addMenu("New")
    viewNewMenu.addAction(Action(self, "1D Spectral Pane", callback=self.addSpectrum1dPane))
    viewNewMenu.addAction(Action(self, "nD Spectral Pane", callback=self.addSpectrumNdPane))
    viewNewMenu.addAction(Action(self, "Peak Table", callback=self.showPeakTable, shortcut="LT"))

    viewLayoutMenu = viewMenu.addMenu("Layout")
    viewLayoutMenu.addAction(Action(self, "Default", callback=self.setLayoutToDefault))
    viewLayoutMenu.addAction(Action(self, "Save", callback=self.saveLayout))
    viewLayoutMenu.addAction(Action(self, "Save As...", callback=self.saveLayoutAs))
    viewLayoutMenu.addAction(Action(self, "Restore", callback=self.restoreLayout))
    viewMenu.addSeparator()
    self.consoleAction = QtGui.QAction("Console", self, triggered=self.toggleConsole,
                                         checkable=True)
    if self.pythonConsoleShown == True:
      self.consoleAction.setChecked(True)
    else:
      self.consoleAction.setChecked(False)

    viewMenu.addAction(self.consoleAction, isFloatWidget=True)

    helpMenu.addAction(Action(self, "Command...", callback=self.showCommandHelp))
    helpMenu.addAction(Action(self, "Tutorials...", callback=self.showTutorials))
    helpMenu.addSeparator()
    helpMenu.addAction(Action(self, "About Analysis V3...", callback=self.showAboutPopup))
    helpMenu.addAction(Action(self, "About CCPN...", callback=self.showAboutCcpnPopup))
    helpMenu.addSeparator()
    helpMenu.addAction(Action(self, "Inspect Code...", callback=self.showCodeInspectionPopup))
    helpMenu.addAction(Action(self, "Check for Upgrades...", callback=self.showUpgradePopup))
    helpMenu.addAction(Action(self, "Report Bug...", callback=self.showBugReportingPopup))

    self.pythonConsole.runMacroButton.clicked.connect(self.runMacro)
    self._menuBar.addMenu(fileMenu)
    self._menuBar.addMenu(spectrumMenu)
    self._menuBar.addMenu(moleculeMenu)
    self._menuBar.addMenu(restraintsMenu)
    self._menuBar.addMenu(structuresMenu)
    self._menuBar.addMenu(viewMenu)
    self._menuBar.addMenu(macroMenu)
    self._menuBar.addMenu(helpMenu)
    self.setMenuBar(self._menuBar)
    self._menuBar.setNativeMenuBar(False)
    self.setWindowTitle('Analysis v3')
    self.show()

  def raiseSpectrumProperties(self, item):
    dataItem = item.data(0, QtCore.Qt.DisplayRole)
    spectrum = self.project.getById(dataItem)
    SpectrumPropertiesPopup(spectrum).exec_()

  def newProject(self, name=None):
    if name is None:
      self.project=newProject('defaultProject')
    else:
      self.project=newProject(name)
    msg  = (self.project.name)+' created'
    self.statusBar().showMessage(msg)
    self.pythonConsole.write("project = newProject('"+self.project.name+"')\n")
    self.namespace['project'] = self.project
    self.pythonConsole.input.history.append("project = newProject('"+self.project.name+"')\n")

  def openProject(self, projectDir=None):
    if projectDir is None:
      currentProjectDir = QtGui.QFileDialog.getExistingDirectory(self, 'Open Project')
    else:
      currentProjectDir = projectDir
    project = openProject(currentProjectDir)
    self.setProject(project)
    msg  = (currentProjectDir)+' opened'
    self.statusBar().showMessage(msg)
    self.pythonConsole.write("project = openProject('"+currentProjectDir+"')\n")
    self.pythonConsole.ui.historyList.addItem("project = openProject('"+currentProjectDir+"')\n")
    if len(self.preferences.recentFiles) != 10:
      self.preferences.recentFiles.insert(0, currentProjectDir)
    else:
      self.preferences.recentFiles.pop()
      self.preferences.recentFiles.append(currentProjectDir)

  def setProject(self, project):
    
    if project is not None:
      self.leftWidget.fillSideBar(project)
      self.spectrumPane1.project = project
      self.spectrumPane2.project = project
      self.namespace['project'] = project
    
    self.project = project

  def setupPreferences(self):
      
    preferencesPath = os.path.expanduser('~/.ccpn/v3settings.json') # TBD: where should it go?
    try:
      fp = open(preferencesPath)
      self.preferences = json.load(fp, object_hook=AttrDict)
      print(self.preferences)
      fp.close()
    except:
      self.preferences = None # TBD: should give some sensible default
  
  def fillRecentProjectsMenu(self):
    for recentFile in self.preferences.recentFiles:
      self.action = Action(self, text=recentFile, callback=partial(self.openProject,projectDir=recentFile))
      self.recentProjectsMenu.addAction(self.action)



  def saveBackup(self):
    pass

  def restoreBackup(self):
    pass

  def undo(self):
    pass

  def redo(self):
    pass

  def saveLogFile(self):
    pass

  def clearLogFile(self):
    pass

  def displayProjectSummary(self):
    pass

  def archiveProject(self):
    pass

  def showApplicationPreferences(self):
    PreferencesPopup(preferences=self.preferences).exec_()

  def quitAction(self):
    # pass
    prefFile = open(os.path.expanduser("~/.ccpn/v3settings.json"))
    pref = json.load(prefFile)
    prefFile.close()
    if not pref == self.preferences:
      msgBox = QtGui.QMessageBox()
      msgBox.setText("Application Preferences have been changed")
      msgBox.setInformativeText("Do you want to save your changes?")
      msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
      ret = msgBox.exec_()
      if ret == QtGui.QMessageBox.Yes:
        preferencesPath = os.path.expanduser("~/.ccpn/v3settings.json")
        prefFile = open(preferencesPath, 'w+')
        json.dump(self.preferences, prefFile)
        prefFile.close()
      else:
        pass

    QtGui.QApplication.quit()

    # json.dumps(self.preferences, pref)


  def removeSpectra(self):
    pass

  def renameSpectra(self):
    pass

  def reloadSpectra(self):
    pass

  def printSpectrum(self):
    pass

  def showSpectrumInFinder(self):
    pass

  def copySpectrumIntoProject(self):
    pass

  def moveSpectrumOutOfProject(self):
    pass

  def importPeaksPopup(self):
    pass

  def deletePeaksPopup(self):
    pass

  def printPeaksToFile(self):
    pass

  def addSpectrum1dPane(self):

    #newModule = Spectrum1dPane(parent=self, title='Module %s' % str(self.moduleCount+1),
    newModule = Spectrum1dPane(title='Module %s_1D' % str(self.moduleCount+1),
                               current=self.current, pid='QP:%s' % str(self.moduleCount+1),
                               preferences=self.preferences, mainWindow=self)
    self.panes[newModule.pid] = newModule
    newModule.project = self.project
    newModule.current = self.current
    self.moduleCount+=1
    
    self.dockArea.addDock(newModule.dock)

  def addSpectrumNdPane(self):

    #newModule = SpectrumNdPane(parent=self, title='Module %s' % str(self.moduleCount+1),
    newModule = SpectrumNdPane(title='Module %s_Nd' % str(self.moduleCount+1),
                               current=self.current, pid='QP:%s' % str(self.moduleCount+1),
                               preferences=self.preferences, mainWindow=self)
    self.panes[newModule.pid] = newModule
    newModule.project = self.project
    newModule.current = self.current
    self.moduleCount+=1

    self.dockArea.addDock(newModule.dock)

  def setLayoutToDefault(self):
    pass

  def saveLayout(self):
    pass

  def saveLayoutAs(self):
    pass

  def restoreLayout(self):
    pass

  def toggleConsole(self):
    if self.pythonConsoleShown == True:
      self.hideConsole()
      self.pythonConsoleShown = False
    else:
      self.showConsole()
      self.pythonConsoleShown = True

  def editMacro(self):
    pass

  def newMacroFromLog(self):

    editor = TextEditor(filename=self.logFile)
    editor.exec_()

  def startMacroRecord(self):
    pass

  def stopMacroRecord(self):
    pass

  def saveRecordedMacro(self):
    pass

  def showRecentMacros(self):
    pass

  def defineUserShortcuts(self):
    pass

  def createMoleculeFromFasta(self):
    pass

  def createMoleculeFromPDB(self):
    pass

  def createMoleculeFromNEF(self):
    pass

  def showMoleculePopup(self):
    pass

  def inspectMolecule(self):
    pass

  def runChembuild(self):
    pass

  def showCommandHelp(self):
    pass

  def showTutorials(self):
    pass

  def showAboutPopup(self):
    pass

  def showAboutCcpnPopup(self):
    pass

  def showCodeInspectionPopup(self):
    pass

  def showUpgradePopup(self):
    pass

  def showBugReportingPopup(self):
    pass

  def runMacro(self):
    macroFile = QtGui.QFileDialog.getOpenFileName(self, "Run Macro")
    f = open(macroFile[0])
    lines = f.readlines()

    for line in lines:
        self.pythonConsole.runCmd(line)
        # self.pythonConsole.write(line)

    f.close()

  def showPeakTable(self):

    peakList = PeakListSimple(dimensions=self.current.spectrum.dimensionCount)
    if self.current.spectrum.peaks:
      peakList.updateContents(self.current.spectrum)
    peakDock = Dock(name=self.current.spectrum.peakLists[0].pid, size=(1000,1000))
    peakDock.addWidget(peakList)
    self.dockArea.addDock(peakDock)

  def automaticIntegration(spectrum):
    spectrum.automaticIntegration()

  def manualIntegration(self):
    pass

  def loadSpectra(self, directory=None):
    if directory == None:
      directory = QtGui.QFileDialog.getOpenFileName(self, 'Open Spectra')
      spectrum = loadDataSource(self.project,directory[0])

    else:
      spectrum = loadDataSource(self.project,directory)

      self.current.pane.addSpectrum(spectrum)
      self.leftWidget.addItem(self.leftWidget.spectrumItem,spectrum)

    msg = spectrum.name+' loaded'
    self.statusBar().showMessage(msg)
    if len(directory) == 1:
      self.pythonConsole.write("project.loadSpectrum('"+directory+"')\n")
    else:
      self.pythonConsole.write("project.loadSpectrum('"+directory[0]+"')\n")
    # self.logFile.write("project.loadSpectrum('"+directory+"')\n")
    # self.pythonConsole.execSingle('c')

  def saveProject(self):

    print("project saved")

  def saveProjectAs(self):
    print("project saved as...")


  def showCrossHair(self):
    self.current.pane.showCrossHair()

  def hideCrossHair(self):
    self.current.pane.hideCrossHair()

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

          if spectrumFormat:
            event.acceptProposedAction()
            dataSource = loadDataSource(self.project,filePaths[0])


          # if dataSource.numDim == 1:
          #   data = Spectrum1dItem(self.current.pane,dataSource).spectralData
          #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
          # elif dataSource.numDim > 1:
          #   data = SpectrumNdItem(self.spectrumPane,dataSource).spectralData
          #   print(data)
          #   self.widget1.plot(data, pen={'color':(random.randint(0,255),random.randint(0,255),random.randint(0,255))})
            msg = dataSource.name+' loaded'
            self.statusBar().showMessage(msg)
            self.pythonConsole.write("loadSpectrum('"+filePaths[0]+"')\n")

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
  window.showMaximized()
  window.raise_()
  sys.exit(app.exec_())

if __name__ ==  "__main__":
  main()