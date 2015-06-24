"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author$"
__date__ = "$Date$"
__version__ = "$Revision$"

#=========================================================================================
# Start of code
#=========================================================================================
import os
import json
import shutil
from functools import partial

from PyQt4 import QtGui, QtCore

from ccpncore.gui.Action import Action
from ccpncore.gui.Console import Console
from ccpncore.gui.Menu import Menu, MenuBar
from ccpncore.gui import MessageDialog
from ccpncore.gui.SideBar import SideBar
from ccpncore.gui.TextEditor import TextEditor

from ccpnmrcore.gui.Assigner import Assigner
from ccpnmrcore.modules.GuiBlankDisplay import GuiBlankDisplay
from ccpnmrcore.modules.BackboneAssignmentModule import BackboneAssignmentModule
from ccpnmrcore.modules.GuiWindow import GuiWindow
from ccpnmrcore.modules.DataPlottingModule import DataPlottingModule
#from ccpnmrcore.modules.ParassignPeakTable import ParassignModule
from ccpnmrcore.modules.PeakTable import PeakListSimple
from ccpnmrcore.modules.PickAndAssignModule import PickAndAssignModule
from ccpnmrcore.popups.PreferencesPopup import PreferencesPopup
from ccpnmrcore.popups.SpectrumPropertiesPopup import SpectrumPropertiesPopup

from ccpncore.util import Io as ioUtil
from ccpncore.util import Pid

class GuiMainWindow(QtGui.QMainWindow, GuiWindow):

  def __init__(self):
    QtGui.QMainWindow.__init__(self)
    #if not apiWindow.modules:
      #apiGuiTask = apiWindow.windowStore.memopsRoot.findFirstGuiTask(name='Ccpn') # constant should be stored somewhere
      ##apiModule = apiGuiTask.newStripDisplay1d(name='Module1_1D', axisCodes=('H','intensity'), stripDirection='Y')
      ##apiWindow.addModule(apiModule)
      ##codes = ('H','N')
      ##apiModule = apiGuiTask.newStripDisplayNd(name='Module2_ND', axisCodes=codes, axisOrder=codes, stripDirection='Y')
      ##apiWindow.addModule(apiModule)
      #apiModule = apiGuiTask.newTaskModule(name=self.INITIAL_MODULE_NAME)
      #apiWindow.addModule(apiModule)
    GuiWindow.__init__(self)
    self.setupWindow()
    self.setupMenus()
    self.initProject()
    # self.setFixedWidth(QtGui.QApplication.desktop().screenGeometry().width())


  def initProject(self):

    # No need, project already set and initialised in AppBase init
    # if project:
    #   self._appBase.initProject(project)
    # else:
    #   project = self._appBase.project

    # project = self._appBase.project

    isNew = self.apiWindow.root.isModified  # a bit of a hack this, but should be correct

    project = self._project
    path = project.path
    self.leftWidget.fillSideBar(project)
    self.namespace['project'] = project
    msg  = path + (' created' if isNew else ' opened')
    self.statusBar().showMessage(msg)

    # msg2 = 'project = ' + ('new' if isNew else 'open') + 'Project("+path+")\n'
    msg2 = 'project = %sProject("%s")\n' % (('new' if isNew else 'open'), path)
    self.pythonConsole.write(msg2)
    self.pythonConsole.ui.historyList.addItem(msg2)

    if not isNew:
      recentFiles = self._appBase.preferences.recentFiles
      if len(recentFiles) >= 10:
        recentFiles.pop()
      recentFiles.insert(0, path)

    self.setWindowTitle('%s %s (%s): %s' % (self._appBase.applicationName, self._appBase.applicationVersion, __version__[1:-1].strip(), project.name))

  def setupWindow(self):

    self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    self.splitter3 = QtGui.QSplitter(QtCore.Qt.Vertical)

    self.namespace = {'current': self._project._appBase.current, 'openProject':self._appBase.openProject,
                      'newProject':self._appBase.newProject, 'loadSpectrum':self.loadSpectra, 'window':self,
                      'preferences':self._appBase.preferences, 'project':self._project}
    self.pythonConsole = Console(parent=self, namespace=self.namespace)
    self.pythonConsole.setGeometry(1200, 700, 10, 1)
    self.pythonConsole.heightMax = 200

    self.leftWidget = SideBar(parent=self)
    self.leftWidget.setDragDropMode(self.leftWidget.DragDrop)
    self.leftWidget.setGeometry(0, 0, 10, 600)
    self.leftWidget.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Fixed)

    self.splitter3.addWidget(self.leftWidget)
    self.splitter1.addWidget(self.splitter3)
    self.splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
    self.splitter2.addWidget(self.splitter1)
    self.splitter2.heightMax = 200
    assignerShorcut = QtGui.QShortcut(QtGui.QKeySequence('s, a'), self, self.showAssigner)
    csShortcut = QtGui.QShortcut(QtGui.QKeySequence('c, s'), self, self.showChemicalShiftTable)
    # peakTableShorcut = QtGui.QShortcut(QtGui.QKeySequence('p, t'), self, self.showPeakTable)
    self.leftWidget.itemDoubleClicked.connect(self.raiseProperties)
    self.splitter2.addWidget(self.pythonConsole)
    # self.sequenceWidget = QtGui.QLabel(self)
    # self.sequenceWidget.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
    # font = self.sequenceWidget.font()
    # font.setPointSize(21)
    # self.sequenceWidget.setFont(font)
    self.pythonConsole.hide()
    self.splitter2.setGeometry(QtCore.QRect(1200, 1300, 100, 100))
    self.splitter1.addWidget(self.dockArea)
    self.seqScrollArea = QtGui.QScrollArea()
    self.seqScrollArea.setFixedHeight(30)
    # if len(self._project.chains) > 0:
    # # self.seqScrollArea.setWidget(self.sequenceWidget)
    #   self.dockArea.layout.addWidget(self.sequenceWidget)
    #   self.sequence = ''.join([residue.shortName for residue in self._project.chains[0].residues])
    #   self.sequenceWidget.setText(self.sequence)
    self.setCentralWidget(self.splitter2)
    self.statusBar().showMessage('Ready')
    self.setShortcuts()

  def setupMenus(self):

    self._menuBar =  MenuBar(self)

    fileMenu = Menu("&Project", self)
    spectrumMenu = Menu("&Spectra", self)
    viewMenu = Menu("&View", self)
    moleculeMenu = Menu("&Molecules", self)
    restraintsMenu = Menu("&Restraints", self)
    structuresMenu = Menu("&Structures", self)
    macroMenu = Menu("Macro", self)
    helpMenu = Menu("&Help", self)

    fileMenu.addAction(Action(self, "New", callback=self._appBase.newProject, shortcut='pn'))
    fileMenu.addAction(Action(self, "Open...", callback=self.openAProject, shortcut="po"))
    self.recentProjectsMenu = fileMenu.addMenu("Open Recent")
    self.fillRecentProjectsMenu()
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Save", callback=self._appBase.saveProject, shortcut="ps"))
    fileMenu.addAction(Action(self, "Save As...", shortcut="pa", callback=self.saveProjectAs))
    backupOption = fileMenu.addMenu("Backup")
    backupOption.addAction(Action(self, "Save", callback=self.saveBackup))
    backupOption.addAction(Action(self, "Restore", callback=self.restoreBackup))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Undo", callback=self.undo, shortcut=QtGui.QKeySequence("Ctrl+z")))
    fileMenu.addAction(Action(self, "Redo", callback=self.redo, shortcut=QtGui.QKeySequence("Ctrl+y")))
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
    macroMenu.addAction(Action(self, "New from Logfile...", callback=self.newMacroFromLog))
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
    viewNewMenu.addAction(Action(self, "New Blank Display", callback=self.addBlankDisplay, shortcut="nd"))
    # viewNewMenu.addAction(Action(self, "nD Spectral Pane", callback=self.addSpectrumNdDisplay))
    viewNewMenu.addAction(Action(self, "Peak Table", callback=self.showPeakTable, shortcut="lt"))

    viewLayoutMenu = viewMenu.addMenu("Layout")
    viewLayoutMenu.addAction(Action(self, "Default", callback=self.setLayoutToDefault))
    viewLayoutMenu.addAction(Action(self, "Save", callback=self.saveLayout))
    viewLayoutMenu.addAction(Action(self, "Save As...", callback=self.saveLayoutAs))
    viewLayoutMenu.addAction(Action(self, "Restore", callback=self.restoreLayout))
    viewMenu.addSeparator()
    self.consoleAction = Action(self, "Console", callback=self.toggleConsole, shortcut="py",
                                         checkable=True)
    self.consoleAction.setChecked(self.pythonConsole.isVisible())
    viewMenu.addAction(self.consoleAction)

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


  def addBlankDisplay(self):
    if not self.blankDisplay:
      self.blankDisplay = GuiBlankDisplay(self.dockArea)

  def openAProject(self, projectDir=None):

    if projectDir is None:
      currentProjectDir = QtGui.QFileDialog.getExistingDirectory(self, 'Open Project')
    else:
      currentProjectDir = projectDir

    if currentProjectDir:
      self._appBase.openProject(currentProjectDir)


  def showAssigner(self, position='bottom', nextTo=None):
    self.assigner = Assigner(project=self._project)
    if nextTo is not None:
      self.dockArea.addDock(self.assigner, position=position, relativeTo=nextTo)
    else:
      self.dockArea.addDock(self.assigner, position=position)
    return self.assigner
    # self.dockArea.addDock(assigner)

  def raiseProperties(self, item):
    """get object from Pid and dispatch call depending on type

    NBNB TBD How about refactoring so that we have a shortClassName:Popup dictionary?"""
    dataPid =  item.data(0, QtCore.Qt.DisplayRole)
    project = self._appBase.project
    obj = project.getById(dataPid)
    if obj is None:
      project._logger.error("No data object matching Pid %s" % dataPid)
    elif obj.shortClassName == 'SP':
      popup = SpectrumPropertiesPopup(obj)
      popup.exec_()
      popup.raise_()
    else:
      project._logger.error("Double-click activation not implemented for object %s" % obj)
    # dataItem = item.data(0, QtCore.Qt.DisplayRole)
    # spectrum = self._appBase.project.getById(dataItem)
    # popup = SpectrumPropertiesPopup(spectrum)
    # popup.exec_()
    # popup.raise_()

  def fillRecentProjectsMenu(self):
    for recentFile in self._appBase.preferences.recentFiles:
      self.action = Action(self, text=recentFile, callback=partial(self._appBase.openProject,projectDir=recentFile))
      self.recentProjectsMenu.addAction(self.action)

  def saveBackup(self):
    pass

  def restoreBackup(self):
    pass

  def undo(self):
    self._project._undo.undo()

  def redo(self):
    self._project._undo.redo()

  def saveLogFile(self):
    pass

  def clearLogFile(self):
    pass

  def displayProjectSummary(self):
    pass

  def archiveProject(self):
    pass

  def showApplicationPreferences(self):
    PreferencesPopup(preferences=self._appBase.preferences).exec_()

  def quitAction(self):
    # pass
    prefPath = os.path.expanduser("~/.ccpn/v3settings.json")
    if os.path.exists(prefPath):
      prefFile = open(prefPath)
      pref = json.load(prefFile)
      prefFile.close()
      if pref == self._appBase.preferences:
        savePref = False
      else:
        msgBox = QtGui.QMessageBox()
        msgBox.setText("Application Preferences have been changed")
        msgBox.setInformativeText("Do you want to save your changes?")
        msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        savePref = (msgBox.exec_() == QtGui.QMessageBox.Yes)
    else:
      savePref = True
      
    if savePref:
      directory = os.path.dirname(prefPath)
      if not os.path.exists(directory):
        try:
          os.makedirs(directory)
        except Exception as e:
          project = self._appBase.project
          project._logger.warning('Preferences not saved: %s' % (directory, e))
          return
          
      prefFile = open(prefPath, 'w+')
      json.dump(self._appBase.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
      prefFile.close()

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

    if self.pythonConsole.isVisible():
      self.hideConsole()
    else:
      self.showConsole()

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

  def runMacro(self, macroFile=None):

    macroFile = QtGui.QFileDialog.getOpenFileName(self, "Run Macro", self._appBase.preferences.general.macroPath)
    f = open(macroFile)
    lines = f.readlines()

    for line in lines:
        self.pythonConsole.runCmd(line)

    f.close()

  def showPeakTable(self, position='left', relativeTo=None):
    peakList = PeakListSimple(name="Peak Table", peakLists=self.project.peakLists)
    if relativeTo is not None:
      self.dockArea.addDock(peakList, position=position, relativeTo=relativeTo)
    else:
      self.dockArea.addDock(peakList, position='bottom')


  def showChemicalShiftTable(self, position='bottom'):
    from ccpnmrcore.modules.ChemicalShiftTable import ChemicalShiftTable
    chemicalShiftTable = ChemicalShiftTable(chemicalShiftLists=self.project.chemicalShiftLists)
    self.dockArea.addDock(chemicalShiftTable, position=position)

  def showParassignPeakTable(self, position='left', relativeTo=None):
    peakList = ParassignModule(name="Peak Table", peakLists=self.project.peakLists)
    if relativeTo is not None:
      self.dockArea.addDock(peakList, position=position, relativeTo=relativeTo)
    else:
      self.dockArea.addDock(peakList, position='bottom')

  def showBackboneAssignmentModule(self, position=None, relativeTo=None, assigner=None, hsqcDisplay=None):
    self.bbModule = BackboneAssignmentModule(self._project, position, relativeTo, assigner, hsqcDisplay)
    self.dockArea.addDock(self.bbModule)
    return self.bbModule

  def showPickAndAssignModule(self, position=None, relativeTo=None, assigner=None, hsqcDisplay=None):
    self.paaModule = PickAndAssignModule(self._project, position, relativeTo, assigner, hsqcDisplay)
    self.dockArea.addDock(self.paaModule)
    return self.paaModule

  def showDataPlottingModule(self):
    dpModule = DataPlottingModule(self.dockArea)

  def saveProjectAs(self):
    if not self.project:
      return
    dialog = QtGui.QFileDialog(self, caption='Save Project As...')
    dialog.setFileMode(QtGui.QFileDialog.AnyFile)
    if not dialog.exec_():
      return
    fileNames = dialog.selectedFiles()
    if not fileNames:
      return
    newPath = fileNames[0]
    if newPath:
      if os.path.exists(newPath) and (os.path.isfile(newPath) or os.listdir(newPath)):
        # should not really need to check the second and third condition above, only
        # the Qt dialog stupidly insists a directory exists before you can select it
        # so if it exists but is empty then don't bother asking the question
        title = 'Overwrite path'
        msg ='Path "%s" already exists, overwrite?' % newPath
        if MessageDialog.showYesNo(title, msg, self):
          if os.path.isfile(newPath):
            os.remove(newPath)
          else:
            shutil.rmtree(newPath, ignore_errors=True)
        else:
          return
      self._appBase.saveProject(newPath=newPath)

  def toggleCrossHair(self):
    self._appBase.current.strip.toggleCrossHair()

  def toggleGrid(self):
    self._appBase.current.strip.toggleGrid()

  def hideConsole(self):
    self.pythonConsole.hide()

  def showConsole(self):
    self.pythonConsole.show()

