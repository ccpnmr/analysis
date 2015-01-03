__author__ = 'simon'


from pyqtgraph.dockarea import DockArea

from ccpn.lib.Project import loadSpectrum

from ccpncore.gui.Action import Action
from ccpncore.gui.Console import PythonConsole
from ccpncore.gui.SideBar import SideBar
from ccpncore.gui.TextEditor import TextEditor

from ccpncore.lib.spectrum import Util as specUtil

from ccpnmrcore import Base as GuiBase

from ccpnmrcore.popups.PreferencesPopup import PreferencesPopup
from ccpnmrcore.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup

from PySide import QtGui, QtCore

import os, json, sys
from functools import partial
# from ccpncore.api.ccpnmr.gui.*** import SpectrumDisplay

class GuiWindow(GuiBase):

  def __init__(self, appBase, window=None):
    self.appBase = appBase
    self.window = window
    self.guiModules = []

    if window is not None:
      for module in window.modules:
        if isinstance(module, SpectrumDisplay):
          className = module.className
          classModule = __import__('ccpnmrcore.modules.' + className)
          clazz = getattr(classModule, className)
          guiModule = clazz(self, module)
        else:
          raise Exception("Don't know how to deal with this yet")

  def loadSpectra(self, directory=None):
    if directory == None:
      directory = QtGui.QFileDialog.getOpenFileName(self, 'Open Spectra')
      spectrum = loadSpectrum(self.project,directory[0])

    else:
      spectrum = loadSpectrum(self.project,directory)
      print(spectrum)
      # self.leftWidget.addItem(self.leftWidget.spectrumItem,spectrum)

    msg = spectrum.name+' loaded'
    self.leftWidget.addItem(self.leftWidget.spectrumItem,spectrum)
    self.statusBar().showMessage(msg)
    if len(directory) == 1:
      self.pythonConsole.write("project.loadSpectrum('"+directory+"')\n")
    else:
      self.pythonConsole.write("project.loadSpectrum('"+directory[0]+"')\n")

    def addSpectrum1dDisplay(self):
      pass
    # #newModule = Spectrum1dPane(parent=self, title='Module %s' % str(self.moduleCount+1),
    # newModule = Spectrum1dDisplay(title='Module %s_1D' % str(self.moduleCount+1),
    #                            current=self.current, pid='QP:%s' % str(self.moduleCount+1),
    #                            preferences=self.preferences, mainWindow=self)
    # self.panes[newModule.pid] = newModule
    # newModule.project = self.project
    # newModule.current = self.current
    # self.moduleCount+=1
    #
    # self.dockArea.addDock(newModule.dock)
    # return newModule

  def addSpectrumNdDisplay(self):
    pass
    # #newModule = SpectrumNdPane(parent=self, title='Module %s' % str(self.moduleCount+1),
    # newModule = SpectrumNdDisplay(title='Module %s_Nd' % str(self.moduleCount+1),
    #                            current=self.current, pid='QP:%s' % str(self.moduleCount+1),
    #                            preferences=self.preferences, mainWindow=self)
    # self.panes[newModule.pid] = newModule
    # newModule.project = self.project
    # newModule.current = self.current
    # self.moduleCount+=1
    #
    # self.dockArea.addDock(newModule.dock)
    # return newModule

  def setShortcuts(self):
    toggleConsoleShortcut = QtGui.QShortcut(QtGui.QKeySequence("p, y"), self, self.toggleConsole)
    toggleCrossHairShortcut = QtGui.QShortcut(QtGui.QKeySequence("c, h"), self, self.toggleCrossHair)
    toggleGridShortcut = QtGui.QShortcut(QtGui.QKeySequence("g, s"), self, self.toggleGrid)

  def setupWindow(self):
    self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    self.splitter3 = QtGui.QSplitter(QtCore.Qt.Vertical)
    self.setupPreferences()
    self.namespace = {'current': self.current, 'openProject':self.appBase.openProject,
                      'newProject':self.newProject, 'loadSpectrum':self.loadSpectra, 'self':self,
                      'preferences':self.preferences}
    self.pythonConsole = PythonConsole(parent=self, namespace=self.namespace)
    self.pythonConsole.setGeometry(1200, 700, 10, 1)
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
    self.splitter2.setGeometry(QtCore.QRect(1200, 1300, 100, 100))
    self.dockArea = DockArea()
    self.dockArea.setGeometry(0, 0, 1100, 1300)
    self.splitter1.addWidget(self.dockArea)
    self.setCentralWidget(self.splitter2)
    self.statusBar().showMessage('Ready')
    self.setShortcuts()

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
          spectrumFormat = specUtil.getSpectrumFileFormat(filePaths[0])

          if spectrumFormat:
            event.acceptProposedAction()
            dataSource = loadSpectrum(self.project,filePaths[0])


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


class MainWindow(QtGui.QMainWindow, GuiWindow):

  def __init__(self, appBase, window=None):
    QtGui.QMainWindow.__init__(self)
    GuiWindow.__init__(self, appBase, window)
    self.setupMainWindow()
    self.setProject()

  def setProject(self, isNew=False):

    project = self.appBase.project
    if project is not None:
      path = project.path
      self.leftWidget.fillSideBar(project)
      self.namespace['project'] = project
      msg  = (path)+(' created' if isNew else ' opened')
      self.statusBar().showMessage(msg)
      msg2 = "project = " + ('new' if isNew else 'open') + "Project("+path+")\n"
      self.pythonConsole.write(msg2)
      self.pythonConsole.ui.historyList.addItem(msg2)

      preferences = self.appBase.preferences
      if len(preferences.recentFiles) < 10:
        preferences.recentFiles.insert(0, path)
      else:
        preferences.recentFiles.pop()
        preferences.recentFiles.append(path)

  def setupMainWindow(self):

    self.setupWindow()
    self._menuBar =  QtGui.QMenuBar()

    fileMenu = QtGui.QMenu("&Project", self)
    spectrumMenu = QtGui.QMenu("&Spectra", self)
    viewMenu = QtGui.QMenu("&View", self)
    moleculeMenu = QtGui.QMenu("&Molecules", self)
    restraintsMenu = QtGui.QMenu("&Restraints", self)
    structuresMenu = QtGui.QMenu("&Structures", self)
    macroMenu = QtGui.QMenu("Macro", self)
    helpMenu = QtGui.QMenu("&Help", self)

    fileMenuAction = fileMenu.addAction(QtGui.QAction("New", self, triggered=self.newProject))
    fileMenu.addAction(Action(self, "Open...", callback=self.openProject, shortcut="po"))
    self.recentProjectsMenu = fileMenu.addMenu("Open Recent")
    self.fillRecentProjectsMenu()
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Save", callback=self.saveProject, shortcut="ps"))
    fileMenu.addAction(Action(self, "Save As...", shortcut="pa", callback=self.saveProjectAs))
    backupOption = fileMenu.addMenu("Backup")
    backupOption.addAction(Action(self, "Save", callback=self.saveBackup))
    backupOption.addAction(Action(self, "Restore", callback=self.restoreBackup))
    fileMenu.addSeparator()
    fileMenu.addAction(QtGui.QAction("Undo", self, triggered=self.undo, shortcut=QtGui.QKeySequence("Ctrl+z")))
    fileMenu.addAction(QtGui.QAction("Redo", self, triggered=self.redo, shortcut=QtGui.QKeySequence("Ctrl+y")))
    logOption = fileMenu.addMenu("Log File")
    logOption.addAction(Action(self, "Save As...", callback=self.saveLogFile))
    logOption.addAction(Action(self, "Clear", callback=self.clearLogFile))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Summary...", self.displayProjectSummary))
    fileMenu.addAction(Action(self, "Archive...", self.archiveProject))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Preferences...", callback=self.showApplicationPreferences))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Close Program", callback=self.quitAction, shortcut="qt"))

    spectrumMenu.addAction(Action(self, "Add...", callback=self.loadSpectra, shortcut="fo"))
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
    macroMenu.addAction(Action(self, "Run...", shortcut="rm", callback=self.runMacro))
    macroMenu.addAction(Action(self, "Run Recent", callback=self.showRecentMacros))
    macroMenu.addSeparator()
    macroMenu.addAction(Action(self, "Define User Shortcuts...", callback=self.defineUserShortcuts))

    viewNewMenu = viewMenu.addMenu("New")
    viewNewMenu.addAction(Action(self, "1D Spectral Pane", callback=self.addSpectrum1dDisplay))
    viewNewMenu.addAction(Action(self, "nD Spectral Pane", callback=self.addSpectrumNdDisplay))
    viewNewMenu.addAction(Action(self, "Peak Table", callback=self.showPeakTable, shortcut="lt"))

    viewLayoutMenu = viewMenu.addMenu("Layout")
    viewLayoutMenu.addAction(Action(self, "Default", callback=self.setLayoutToDefault))
    viewLayoutMenu.addAction(Action(self, "Save", callback=self.saveLayout))
    viewLayoutMenu.addAction(Action(self, "Save As...", callback=self.saveLayoutAs))
    viewLayoutMenu.addAction(Action(self, "Restore", callback=self.restoreLayout))
    viewMenu.addSeparator()
    self.consoleAction = Action("Console", self, callback=self.toggleConsole,
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
    self.show()

  def raiseSpectrumProperties(self, item):
    dataItem = item.data(0, QtCore.Qt.DisplayRole)
    spectrum = self.project.getById(dataItem)
    popup = SpectrumPropertiesPopup(spectrum)
    popup.show()

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
    PreferencesPopup(preferences=self.appBase.preferences).exec_()

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
        json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
        prefFile.close()
      else:
        pass

    QtGui.QApplication.quit()

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

    f.close()

  def showPeakTable(self):
    pass

  def saveProject(self):
    print("project saved")

  def saveProjectAs(self):
    print("project saved as...")

  def toggleCrossHair(self):
    self.current.pane.toggleCrossHair()

  def toggleGrid(self):
    self.current.pane.toggleGrid()

  def hideConsole(self):
    self.pythonConsole.hide()

  def showConsole(self):
    self.pythonConsole.show()


def main():

  app = QtGui.QApplication(sys.argv)
  window = MainWindow()
  window.showMaximized()
  window.raise_()
  sys.exit(app.exec_())

if __name__ ==  "__main__":
  main()
