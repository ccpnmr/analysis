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
import datetime
import os
import json
import sys
from functools import partial

from PyQt4 import QtGui, QtCore

from ccpn import PeakList

from ccpncore.gui import MessageDialog

from ccpncore.gui.Action import Action
from ccpncore.gui.CcpnWebView import CcpnWebView
from ccpncore.gui.Dock import CcpnDock
from application.core.gui.IpythonConsole import IpythonConsole
from ccpncore.gui.Menu import Menu, MenuBar
from application.core.gui.SideBar import SideBar

from ccpncore.util import Io
from ccpncore.util import Path

from ccpncore.util.Common import uniquify

from application.core.gui.Assigner import Assigner

from application.core.modules.AssignmentModule import AssignmentModule
from application.core.modules.AtomSelector import AtomSelector
from application.core.modules.BackboneAssignmentModule import BackboneAssignmentModule
from application.core.modules.DataPlottingModule import DataPlottingModule

from application.core.modules.GuiBlankDisplay import GuiBlankDisplay
from application.core.modules.GuiWindow import GuiWindow
from application.core.modules.MacroEditor import MacroEditor
from application.core.modules.NotesEditor import NotesEditor
from application.core.modules.PeakTable import PeakTable
from application.core.modules.PickAndAssignModule import PickAndAssignModule
from application.core.modules.SequenceModule import SequenceModule
from application.core.modules.SampleAnalysis import SampleAnalysis
from application.core.modules.ScreeningSetup import ScreeningSetup
from application.metabolomics.Metabolomics import MetabolomicsModule

from application.core.popups.BackupPopup import BackupPopup
from application.core.popups.FeedbackPopup import FeedbackPopup
from application.core.popups.PreferencesPopup import PreferencesPopup
from application.core.popups.SampleSetupPopup import SamplePopup

from application.core.Version import revision

from application.core.update.UpdatePopup import UpdatePopup

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
    #
    self.setGeometry(540, 40, 900, 900)

    GuiWindow.__init__(self)
    self.recordingMacro = False
    self.setupWindow()
    self.setupMenus()
    self.initProject()
    self.connect(self, QtCore.SIGNAL('triggered()'), self.closeEvent)

    # self.setFixedWidth(QtGui.QApplication.desktop().screenGeometry().width())

    self.feedbackPopup = None
    self.updatePopup = None
    self.backupPopup = None

    self.backupTimer = QtCore.QTimer()
    self.connect(self.backupTimer, QtCore.SIGNAL('timeout()'), self.backupProject)
    if self._appBase.preferences.general.autoBackupEnabled:
      self.startBackupTimer()

  def initProject(self):
    """
    Puts relevant information from the project into the appropriate places in the main window.

    """
    # No need, project already set and initialised in AppBase init
    # if project:
    #   self._appBase.initProject(project)
    # else:
    #   project = self._appBase.project

    # project = self._appBase.project

    isNew = self._apiWindow.root.isModified  # a bit of a hack this, but should be correct

    project = self._project
    path = project.path
    self.sideBar.setProject(project)
    self.sideBar.fillSideBar(project)
    self.namespace['project'] = project
    msg = path + (' created' if isNew else ' opened')
    self.statusBar().showMessage(msg)

    # msg2 = 'project = ' + ('new' if isNew else 'open') + 'Project("+path+")\n'
    msg2 = 'project = %sProject("%s")' % (('new' if isNew else 'open'), path)
    self.pythonConsole.writeConsoleCommand(msg2)
    # self.pythonConsole.ui.historyList.addItem(msg2)

    # if not isNew:
    recentFiles = self._appBase.preferences.recentFiles
    if len(recentFiles) >= 10:
      recentFiles.pop()
    recentFiles.insert(0, path)
    self.colourScheme = self._appBase.preferences.general.colourScheme
    recentFiles = uniquify(recentFiles)
    # print(recentFiles)
    self._appBase.preferences.recentFiles = recentFiles
    self.pythonConsole.setProject(project)

    self.setWindowTitle('%s %s (Revision: %s): %s' % (self._appBase.applicationName,
                                            self._appBase.applicationVersion, revision,
                                            project.name))

  def startBackupTimer(self):

    self.backupTimer.start(60000 * self._appBase.preferences.general.autoBackupFrequency)

  def stopBackupTimer(self):

    if self.backupTimer.isActive():
      self.backupTimer.stop()

  def backupProject(self):
    
    Io.backupProject(self._appBase.project._wrappedData.parent)

  def setupWindow(self):
    """
    Sets up SideBar, python console and splitters to divide up main window properly.

    """
    self.splitter1 = QtGui.QSplitter(QtCore.Qt.Horizontal)
    self.splitter3 = QtGui.QSplitter(QtCore.Qt.Vertical)

    self.setStyleSheet("""QSplitter{
                                    background-color: #bec4f3;
                                    }
                          QSplitter::handle:horizontal {
                                                        width: 3px;
                                                        }

                          QSplitter::handle:vertical {
                                                        height: 3px;
                                                      }

                                    """)

    self.namespace = {'loadProject':self._appBase.loadProject,
                      'newProject':self._appBase.newProject, 'loadData':self.loadData, 'application':self,
                      'preferences':self._appBase.preferences, 'project':self._project, 'current':self._appBase.current}

    self.pythonConsole = IpythonConsole(self, self.namespace, mainWindow=self)

    # self.pythonConsoleDock.layout.addWidget(self.pythonConsole)
    # self.pythonConsoleDock.label.hide()
    # self.dockArea.addDock(self.pythonConsoleDock, 'bottom')
    # self.pythonConsoleDock.hide()
    self.sideBar = SideBar(parent=self)
    self.sideBar.setDragDropMode(self.sideBar.DragDrop)
    self.sideBar.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
    self.splitter3.addWidget(self.sideBar)
    self.splitter1.addWidget(self.splitter3)
    # self.splitter2 = QtGui.QSplitter(QtCore.Qt.Vertical)
    # self.splitter1.setStretchFactor(0, 2)
    # self.splitter2.addWidget(self.splitter1)
    self.sideBar.itemDoubleClicked.connect(self.raiseProperties)
    # self.splitter2.addWidget(self.pythonConsole)
    # self.splitter2.setSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Minimum)
    # self.splitter2.setStretchFactor(0, 10)
    # self.splitter2.setStretchFactor(1, 1)

    self.splitter1.addWidget(self.dockArea)
    self.setCentralWidget(self.splitter1)
    self.statusBar().showMessage('Ready')
    self.setShortcuts()


  def setupMenus(self):
    """
    Creates menu bar for main window and creates the appropriate menus according to the arguments
    passed at startup.
    """
    self._menuBar =  MenuBar(self)
    # print(self._menuBar.font())
    fileMenu = Menu("&Project", self)
    self.screenMenu = QtGui.QMenu("&Screen", self)
    self.metabolomicsMenu = QtGui.QMenu("&Metabolomics", self)
    peaksMenu = Menu("Peaks", self)
    viewMenu = Menu("&View", self)
    moleculeMenu = Menu("&Molecules", self)
    restraintsMenu = Menu("&Restraints", self)
    structuresMenu = Menu("&Structures", self)
    macroMenu = Menu("Macro", self)
    helpMenu = Menu("&Help", self)


    fileMenu.addAction(Action(self, "New", callback=self.newProject, shortcut='pn'))

    fileMenu.addAction(Action(self, "Open...", callback=self.loadAProject, shortcut="po"))
    self.recentProjectsMenu = fileMenu.addMenu("Open Recent")
    self._fillRecentProjectsMenu()
    fileMenu.addAction(Action(self, "Load Spectrum", callback=lambda: self.loadData(text='Load Spectrum'), shortcut='ls'))
    fileMenu.addAction(Action(self, "Load Data", callback=self.loadData, shortcut='ld'))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Save", callback=self.saveProject, shortcut="ps"))
    fileMenu.addAction(Action(self, "Save As...", shortcut="sa", callback=self.saveProjectAs))
    ###fileMenu.addAction(Action(self, "Print...", shortcut="pr", callback=self.printToFile))

    #NBNB How are we going to implement this?
    # backupOption = fileMenu.addMenu("Backup")
    # backupOption.addAction(Action(self, "Save", callback=self.saveBackup))
    # backupOption.addAction(Action(self, "Restore", callback=self.restoreBackup))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Undo", callback=self.undo, shortcut=QtGui.QKeySequence("Ctrl+z")))
    fileMenu.addAction(Action(self, "Redo", callback=self.redo, shortcut=QtGui.QKeySequence("Ctrl+y")))

    #NBNB do we want this facility or are logs and console output separate?
    # logOption = fileMenu.addMenu("Log File")
    # logOption.addAction(Action(self, "Save As...", callback=self.saveLogFile))
    # logOption.addAction(Action(self, "Clear", callback=self.clearLogFile))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Summary...", self.displayProjectSummary))
    fileMenu.addAction(Action(self, "Archive", self.archiveProject))
    fileMenu.addAction(Action(self, "Backup...", self.showBackupPopup))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Preferences...", callback=self.showApplicationPreferences))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Close Program", callback=self.closeEvent, shortcut="qt"))


    self.screenMenu.addSeparator()
    self.screenMenu.addAction(Action(self, 'Generate Mixtures', callback=self.createSample, shortcut="cs"))
    self.screenMenu.addAction(Action(self, 'Mixtures Analysis', callback=self.showSampleAnalysis, shortcut="st"))
    self.screenMenu.addSeparator()
    self.screenMenu.addAction(Action(self, 'Screening', callback=self.showScreeningSetup, shortcut="sc"))

    self.metabolomicsMenu.addSeparator()
    self.metabolomicsMenu.addAction(Action(self, 'Analyse Metabolite', callback=self.showMetabolomicsModule, shortcut="mm"))

    # spectrumMenu.addAction(Action(self, "Add...", callback=self.loadSpectra, shortcut="fo"))
    # spectrumMenu.addAction(Action(self, "Remove...", callback=self.removeSpectra))
    # spectrumMenu.addAction(Action(self, "Rename...", callback=self.renameSpectra))
    # spectrumMenu.addAction(Action(self, "Reload", callback=self.reloadSpectra))
    # spectrumMenu.addSeparator()
    # spectrumMenu.addAction(Action(self, "Print...", callback=self.printSpectrum))
    # spectrumMenu.addSeparator()
    # spectrumMenu.addAction(Action(self, "Show in Finder", callback=self.showSpectrumInFinder))
    # spectrumMenu.addAction(Action(self, "Copy into Project", callback=self.copySpectrumIntoProject))
    # spectrumMenu.addAction(Action(self, "Move out of Project", callback=self.moveSpectrumOutOfProject))
    # spectrumMenu.addSeparator()
    # spectrumPeaksMenu = spectrumMenu.addMenu("Peaks")
    # spectrumPeaksMenu.addAction(Action(self, "Import...", callback=self.importPeaksPopup))
    # spectrumPeaksMenu.addAction(Action(self, "Delete...", callback=self.deletePeaksPopup))
    # spectrumPeaksMenu.addSeparator()
    # spectrumPeaksMenu.addAction(Action(self, "Print to File", callback=self.printPeaksToFile))

    peaksMenu.addAction(Action(self, "Peak Table", callback=self.showPeakTable, shortcut="lt"))
    peaksMenu.addAction(Action(self, "Pick Peaks", callback=self.pickPeaks, shortcut='pp'))

    # newMoleculeMenu = moleculeMenu.addMenu("New")
    moleculeMenu.addAction(Action(self, "Create Molecule...", callback=self.showMoleculePopup, shortcut='ls'))
    self.sequenceAction = Action(self, 'Show Sequence', callback=self.toggleSequence, shortcut='sq', checkable=True)
    if hasattr(self, 'sequenceWidget'):
      self.sequenceAction.setChecked(self.sequenceWidget.isVisible())
    else:
      self.sequenceAction.setChecked(False)
    moleculeMenu.addAction(self.sequenceAction)
    moleculeMenu.addAction(Action(self, "Inspect...", callback=self.inspectMolecule))
    moleculeMenu.addSeparator()
    moleculeMenu.addAction(Action(self, "Reference Chemical Shifts", callback=self.showRefChemicalShifts, shortcut='rc'))
    # moleculeMenu.addAction(Action(self, "Run ChemBuild", callback=self.runChembuild))
    # moleculeMenu.addAction(Action(self, "Show Molecule Display", callback=self.showMoleculeDisplay, shortcut='md'))

    macroMenu.addAction(Action(self, "Edit...", callback=self.editMacro))
    macroMenu.addAction(Action(self, "New from Console...", callback=self.newMacroFromConsole))
    macroMenu.addAction(Action(self, "Record Macro...", callback=self.startMacroRecord))
    # macroRecordMenu.addAction(Action(self, "Stop", callback=self.stopMacroRecord))
    # macroRecordMenu.addAction(Action(self, "Save As...", callback=self.saveRecordedMacro))
    macroMenu.addSeparator()
    macroMenu.addAction(Action(self, "Run...", shortcut="rm", callback=self.runMacro))

    self.recentMacrosMenu = macroMenu.addMenu("Run Recent")
    self._fillRecentMacrosMenu()
    # macroMenu.addAction(Action(self, "Run Recent", callback=self.showRecentMacros))
    macroMenu.addSeparator()
    macroMenu.addAction(Action(self, "Define User Shortcuts...", callback=self.defineUserShortcuts))

    # viewNewMenu = viewMenu.addMenu("New")
    viewMenu.addAction(Action(self, "New Blank Display", callback=self.addBlankDisplay, shortcut="nd"))


    #NBNB Need to decide how we are to handle layouts if at all
    # viewLayoutMenu = viewMenu.addMenu("Layout")
    # viewLayoutMenu.addAction(Action(self, "Default", callback=self.setLayoutToDefault))
    # viewLayoutMenu.addAction(Action(self, "Save", callback=self.saveLayout))
    # viewLayoutMenu.addAction(Action(self, "Save As...", callback=self.saveLayoutAs))
    # viewLayoutMenu.addAction(Action(self, "Restore", callback=self.restoreLayout))
    viewMenu.addSeparator()
    self.consoleAction = Action(self, "Console", callback=self.toggleConsole, shortcut="py",
                                         checkable=True)
    self.consoleAction.setChecked(self.pythonConsole.isVisible())
    viewMenu.addAction(self.consoleAction)



    helpMenu.addAction(Action(self, "Command...", callback=self.showCommandHelp))
    tutorialsMenu = helpMenu.addMenu("Tutorials")
    tutorialsMenu.addAction(Action(self, "Beginners Tutorial", callback=self.showBeginnersTutorial))
    tutorialsMenu.addAction(Action(self, "Backbone Tutorial", callback=self.showBackboneTutorial))
    helpMenu.addAction(Action(self, "Show Shortcuts", callback=self.showShortcuts))
    helpMenu.addAction(Action(self, "Show API Documentation", callback=self.showApiDocumentation))
    helpMenu.addAction(Action(self, "Show CCPN Documentation", callback=self.showWrapperDocumentation))
    helpMenu.addSeparator()
    helpMenu.addAction(Action(self, "About CcpNmr V3...", callback=self.showAboutPopup))
    helpMenu.addAction(Action(self, "About CCPN...", callback=self.showAboutCcpnPopup))
    helpMenu.addSeparator()
    helpMenu.addAction(Action(self, "Inspect Code...", callback=self.showCodeInspectionPopup))
    helpMenu.addAction(Action(self, "Check for Updates...", callback=self.showUpdatePopup))
    helpMenu.addAction(Action(self, "Submit Feedback...", callback=self.showFeedbackPopup))

    assignMenu = Menu("&Assign", self)
    assignMenu.addAction(Action(self, "Assignment Module", callback=self.showAssignmentModule, shortcut='aa'))
    assignMenu.addAction(Action(self, "Pick and Assign", callback=self.showPickAndAssignModule, shortcut='pa'))
    assignMenu.addAction(Action(self, 'Backbone Assignment', callback=self.showBackboneAssignmentModule, shortcut='bb'))
    assignMenu.addAction(Action(self, 'Show Assigner', callback=self.showAssigner))
    assignMenu.addAction(Action(self, 'Show Atom Selector', callback=self.showAtomSelector, shortcut='as'))
    assignMenu.addAction(Action(self, 'Residue Information', callback=self.showResidueInformation, shortcut='ri'))
    assignMenu.addAction(Action(self, "NMR Residue Table", callback=self.showNmrResidueTable, shortcut='nr'))
    assignMenu.addAction(Action(self, "PARAssign Setup", callback=self.showParassignSetup, shortcut='q1'))



    self._menuBar.addMenu(fileMenu)
    self._menuBar.addMenu(peaksMenu)

    if self._appBase.applicationName == 'Screen' :
      self._menuBar.addMenu(self.screenMenu)
    self._menuBar.addMenu(moleculeMenu)

    if self._appBase.applicationName == 'Metabolomics':
      self._menuBar.addMenu(self.metabolomicsMenu)

    if 'Assignment' in self._appBase.components:
      self._menuBar.addMenu(assignMenu)

    if 'Structure' in self._appBase.components:
      self._menuBar.addMenu(restraintsMenu)
      self._menuBar.addMenu(structuresMenu)
    self._menuBar.addMenu(viewMenu)
    self._menuBar.addMenu(macroMenu)
    self._menuBar.addMenu(helpMenu)
    self.setMenuBar(self._menuBar)
    self._menuBar.setNativeMenuBar(False)
    self.show()

  def _queryCloseProject(self, title, phrase):
    
    project = self._appBase.project
    apiProject = project._wrappedData.root
    if hasattr(apiProject, '_temporaryDirectory'):
      return True
    
    if apiProject.isProjectModified():
      ss = ' and any changes will be lost'
    else:
      ss = ''
    result = MessageDialog.showYesNo(title,
          'Do you really want to %s project (current project will be closed%s)?' % (phrase, ss),
          colourScheme=self.colourScheme)
          
    return result
    
  def newProject(self):
    
    result = self._queryCloseProject(title='New Project', phrase='create a new')
    
    if result:
      self._appBase.newProject()
    
  def _showDocumentation(self, title, *args):
    
    newDock = CcpnDock("API Documentation")
    path = os.path.join(Path.getTopDirectory(), 'doc', *args)
    view = CcpnWebView(path)
    newDock.addWidget(view)
    self.dockArea.addDock(newDock)
    
  def showApiDocumentation(self):
    """Displays API documentation in a module."""
    self._showDocumentation("API Documentation", 'apidoc', 'api.html')


  def showWrapperDocumentation(self):
    """Displays CCPN wrapper documentation in a module."""
    self._showDocumentation("CCPN Documentation", 'build', 'html', 'index.html')

  def showShortcuts(self):
    path = os.path.join(Path.getTopDirectory(), 'doc', 'static', 'AnalysisShortcuts.pdf')
    if sys.platform == 'linux2':
      os.system(["xdg-open %s" % path])
    else:
      os.system('open %s' % path)


  def showAssignmentModule(self):
    """Displays assignment module."""
    self.assignmentModule = AssignmentModule(self, self._project, self._project._appBase.current.peaks)
    self.dockArea.addDock(self.assignmentModule)
    # self.pythonConsole.writeModuleDisplayCommand('showAssignmentModule')
    self.pythonConsole.writeConsoleCommand("application.showAssignmentModule()")

  def showNmrResidueModule(self):
    """Shows Nmr Residue Module."""
    from application.core.popups.NmrResiduePopup import NmrResiduePopup
    newDock = CcpnDock("Nmr Residue")
    nmrResidueModule = NmrResiduePopup(newDock, self._project)
    newDock.layout.addWidget(nmrResidueModule)
    self.dockArea.addDock(newDock)


  def addBlankDisplay(self):
    """Adds a Blank Display to the main window if one does not already exist."""
    if not hasattr(self, 'blankDisplay') or self.blankDisplay is None:
      self.blankDisplay = GuiBlankDisplay(self.dockArea)
    else:
      self.dockArea.addDock(self.blankDisplay, 'right')

  def showSequence(self):
    """
    Displays Sequence Module at the top of the screen.
    """
    self.sequenceWidget = SequenceModule(self._project)
    self.dockArea.addDock(self.sequenceWidget, position='top')

  def hideSequence(self):
    """Hides sequence module"""
    self.sequenceWidget.close()
    delattr(self, 'sequenceWidget')


  def showNmrResidueTable(self):
    """Displays Nmr Residue Table"""
    from application.core.modules.NmrResidueTable import NmrResidueTable
    nmrResidueTable = NmrResidueTable(self, self._project)
    nmrResidueTableDock = CcpnDock(self, name='Nmr Residue Table')
    nmrResidueTableDock.layout.addWidget(nmrResidueTable)
    self.dockArea.addDock(nmrResidueTable, 'bottom')
    # self.pythonConsole.writeModuleDisplayCommand('showNmrResidueTable')
    self.pythonConsole.writeConsoleCommand("application.showNmrResidueTable()")

  def toggleSequence(self):
    """Toggles whether Sequence Module is displayed or not"""
    if hasattr(self, 'sequenceWidget'):
      if self.sequenceWidget.isVisible():
        self.hideSequence()

    else:
      self.showSequence()
    # self.pythonConsole.writeModuleDisplayCommand('toggleSequence')
    self.pythonConsole.writeConsoleCommand("application.toggleSequence()")

  def loadAProject(self, projectDir=None):
    """
    Opens a loadProject dialog box if project directory is not specified.
    Loads the selected project.
    """
    result = self._queryCloseProject(title='Open Project', phrase='open another')
    
    if result:
      if projectDir is None:
        projectDir = QtGui.QFileDialog.getExistingDirectory(self, 'Open Project')

      if projectDir:
        self._appBase.loadProject(projectDir)

  def pickPeaks(self):
    """
    Displays Peak Picking Popup.
    """
    from application.core.popups.PeakFind import PeakFindPopup
    popup = PeakFindPopup(parent=self, project=self.project)
    popup.exec_()

  def showAssigner(self, position:str='bottom', nextTo:CcpnDock=None):
    """
    Displays assigner at the bottom of the screen, relative to another module if nextTo is specified.
    """
    self.assigner = Assigner(project=self._project)
    if hasattr(self, 'bbModule'):
      self.bbModule.connectAssigner(self.assigner)
    if nextTo is not None:
      self.dockArea.addDock(self.assigner, position=position, relativeTo=nextTo)
    else:
      self.dockArea.addDock(self.assigner, position=position)
    # self.pythonConsole.writeModuleDisplayCommand('showAssigner')
    self.pythonConsole.writeConsoleCommand("application.showAssigner()")
    return self.assigner
    # self.dockArea.addDock(assigner)

  def raiseProperties(self, item):
    """get object from Pid and dispatch call depending on type

    NBNB TBD How about refactoring so that we have a shortClassName:Popup dictionary?"""
    dataPid = item.data(0, QtCore.Qt.DisplayRole)
    project = self._appBase.project
    obj = project.getByPid(dataPid)
    print(obj)
    if obj is not None:
      self.sideBar.raisePopup(obj, item)
    elif item.data(0, QtCore.Qt.DisplayRole) == '<New>':
      self.sideBar.createNewObject(item)

    else:
      project._logger.error("Double-click activation not implemented for object %s" % obj)

  def _fillRecentProjectsMenu(self):
    """
    Populates recent projects menu with 10 most recently loaded projects specified in the preferences file.
    """
    for recentFile in self._appBase.preferences.recentFiles:
      self.action = Action(self, text=recentFile, callback=partial(self.loadAProject, projectDir=recentFile))
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
    info = MessageDialog.showInfo('Not implemented yet',
          'This function has not been implemented in the current version', colourScheme=self.colourScheme)

  def archiveProject(self):

    project = self._project
    apiProject = project._wrappedData.parent
    projectPath = project.path
    now = datetime.datetime.now().strftime('%y%m%d%H%M%S')
    filePrefix = '%s_%s' % (os.path.basename(projectPath), now)
    filePrefix = os.path.join(os.path.dirname(projectPath), filePrefix)
    fileName = Io.packageProject(apiProject, filePrefix, includeBackups=True, includeLogs=True)
    
    MessageDialog.showInfo('Project Archived',
          'Project archived to %s' % fileName, colourScheme=self.colourScheme)
    
  def showBackupPopup(self):
    
    if not self.backupPopup:
      self.backupPopup = BackupPopup(self)
    self.backupPopup.show()
    self.backupPopup.raise_()
  
  def showApplicationPreferences(self):
    """
    Displays Application Preferences Popup.
    """
    PreferencesPopup(preferences=self._appBase.preferences, project=self._project).exec_()

  def closeEvent(self, event=None):
    """
    Saves application preferences. Displays message box asking user to save project or not.
    Closes Application.
    """
    prefPath = os.path.expanduser("~/.ccpn/v3settings.json")
    # if os.path.exists(prefPath):
    #   prefFile = open(prefPath)
    #   pref = json.load(prefFile)
    #   prefFile.close()
    #   if pref == self._appBase.preferences:
    #     savePref = False
    #   else:
    #     msgBox = QtGui.QMessageBox()
    #     msgBox.setText("Application Preferences have been changed")
    #     msgBox.setInformativeText("Do you want to save your changes?")
    #     msgBox.setStandardButtons(QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
    #     savePref = (msgBox.exec_() == QtGui.QMessageBox.Yes)
    # else:
    #   savePref = True
    #
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

    # NBNB TBD FIXME put code here to ask if you want to save etc.

    reply = MessageDialog.showMulti("Quit Program", "Do you want to save changes before quitting?",
                                         ['Save and Quit', 'Quit without Saving', 'Cancel'],
                                          colourScheme=self.colourScheme)
    if reply == 'Save and Quit':
      if event:
        event.accept()
      prefFile = open(prefPath, 'w+')
      json.dump(self._appBase.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
      prefFile.close()
      self.saveProject()
      # Close and clean up project
      self._appBase._closeProject()
      QtGui.QApplication.quit()
    elif reply == 'Quit without Saving':
      if event:
        event.accept()
      self._appBase._closeProject()
      QtGui.QApplication.quit()
    else:
      if event:
        event.ignore()

    # CLose and clean up project
    # if reply == QtGui.QMessageBox.Yes:
    #   if event:
    #     event.accept()
    #   saveMessage = QtGui.QMessageBox.question(self, "Save Project", "Do you want to save changes?",
    #                                     ['Save and Quit', 'Quit without Saving', 'Cancel'])
    #   print(saveMessage, 'saveMessage')
    #   if saveMessage == QtGui.QMessageBox.Yes:
    #     self.saveProject()
    #   self._appBase._closeProject()
    #   QtGui.QApplication.quit()
    # elif reply == QtGui.QMessageBox.No:
    #   if event:
    #     event.ignore()

  def createSample(self):
    """
    Displays Sample creation module.
    """
    popup = SamplePopup(parent=None, project=self.project)
    popup.exec_()
    popup.raise_()
    # self.pythonConsole.writeModuleDisplayCommand('createSample')
    self.pythonConsole.writeConsoleCommand("application.createSample()")

  def showSampleAnalysis(self):
    """
    Displays Sample Analysis Module
    """
    showSa = SampleAnalysis(self._project)
    self.dockArea.addDock(showSa, position='bottom')
    # self.pythonConsole.writeModuleDisplayCommand('showSampleAnalysis')
    self.pythonConsole.writeConsoleCommand("application.showSampleAnalysis()")

  def showScreeningSetup(self):
    showSc = ScreeningSetup(self.project)
    self.dockArea.addDock(showSc, position='bottom')
    self.pythonConsole.writeConsoleCommand("application.showScreeningSetup()")

  def showMetabolomicsModule(self):
    self.showMm = MetabolomicsModule(self.project)
    self.dockArea.addDock(self.showMm, position='bottom')



  def showPCAModule(self):
    from application.metabolomics.Pca import PcaModule
    self.pcaModule = PcaModule(self.project)
    self.dockArea.addDock(self.pcaModule, position='bottom')
    spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
    self.dockArea.moveDock(spectrumDisplay.dock, position='bottom', neighbor=self.pcaModule)

  def showPickandFitModule(self):
    spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
    from application.metabolomics.PickandFit import PickandFit
    PickandFit(spectrumDisplay.dock, grid=(2, 0), gridSpan=(1, 4))

  def showParassignSetup(self):
    try:
      from application.plugins.PARAssign.PARAssignSetup import ParassignSetup
      self.ps = ParassignSetup(project=self.project)
      newDock = CcpnDock(name='PARAssign Setup')
      newDock.addWidget(self.ps)
      self.dockArea.addDock(newDock)
    except ImportError:
      print('PARAssign cannot be found')

  # NBNB sholuld be renamed
  # def removeSpectra(self):
  #   pass

  # def renameSpectra(self):
  #   pass
  #
  # def reloadSpectra(self):
  #   pass
  #
  # def printSpectrum(self):
  #   pass
  #
  # def showSpectrumInFinder(self):
  #   pass
  #
  # def copySpectrumIntoProject(self):
  #   pass
  #
  # def moveSpectrumOutOfProject(self):
  #   pass
  #
  # def importPeaksPopup(self):
  #   pass
  #
  # def deletePeaksPopup(self):
  #   pass
  #
  # def printPeaksToFile(self):
  #   pass

  # def setLayoutToDefault(self):
  #   pass
  #
  # def saveLayout(self):
  #   pass
  #
  # def saveLayoutAs(self):
  #   pass
  #
  # def restoreLayout(self):
  #   pass

  def toggleConsole(self):
    """
    Toggles whether python console is displayed at bottom of the main window.
    """

    if hasattr(self, 'pythonConsoleDock'):
      if self.pythonConsoleDock.isVisible():
        self.hideConsole()
      else:
        self.showConsole()
    else:
      self.pythonConsoleDock = CcpnDock(name='Python Console')
      self.pythonConsoleDock.layout.addWidget(self.pythonConsole)
      self.pythonConsoleDock.label.hide()
      self.dockArea.addDock(self.pythonConsoleDock, 'bottom')


  def editMacro(self):
    """
    Displays macro editor.
    """
    editor = MacroEditor(self.dockArea, self, "Macro Editor")

  def newMacroFromConsole(self):
    """
    Displays macro editor with contents of python console inside.
    """
    editor = MacroEditor(self.dockArea, self, "Macro Editor")
    editor.textBox.setText(self.pythonConsole.textEditor.toPlainText())


  def startMacroRecord(self):
    """
    Displays macro editor with additional buttons for recording a macro.
    """
    self.macroEditor = MacroEditor(self.dockArea, self, "Macro Editor", showRecordButtons=True)
    # self.pythonConsole.writeModuleDisplayCommand('startMacroRecord')
    self.pythonConsole.writeConsoleCommand("application.startMacroRecord()")


  def _fillRecentMacrosMenu(self):
    """
    Populates recent macros menu with last ten macros ran.
    """

    recentMacros = uniquify(self._appBase.preferences.recentMacros)

    for recentMacro in recentMacros:
      self.action = Action(self, text=recentMacro, callback=partial(self.runMacro, macroFile=recentMacro))
      self.recentMacrosMenu.addAction(self.action)

  def defineUserShortcuts(self):
    info = MessageDialog.showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)


  def showNotesEditor(self):
    self.notesEditor = NotesEditor(self._appBase.mainWindow.dockArea, self._project, name='Notes Editor')

  def showMoleculePopup(self):
    """
    Displays sequence creation popup.
    """
    from application.core.modules.CreateSequence import CreateSequence
    popup = CreateSequence(self, project=self._project).exec_()
    # self.pythonConsole.writeModuleDisplayCommand('showMoleculePopup')
    self.pythonConsole.writeConsoleCommand("application.showMoleculePopup()")

  def inspectMolecule(self):
    info = MessageDialog.showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)



  def showCommandHelp(self):
    info = MessageDialog.showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)


  def showBeginnersTutorial(self):
    path = os.path.join(Path.getTopDirectory(), 'data', 'testProjects', 'CcpnSec5BBTutorial', 'BeginnersTutorial.doc')
    if sys.platform == 'linux2':
      os.system(["xdg-open %s" % path])
    else:
      os.system('open %s' % path)

  def showBackboneTutorial(self):
    path = os.path.join(Path.getTopDirectory(), 'data', 'testProjects', 'CcpnSec5BBTutorial', 'BackboneAssignmentTutorial.doc')
    if sys.platform == 'linux2':
      os.system(["xdg-open %s" % path])
    else:
      os.system('open %s' % path)

  def showAboutPopup(self):
    from application.core.popups.AboutPopup import AboutPopup
    popup = AboutPopup()
    popup.exec_()
    popup.raise_()


  def showAboutCcpnPopup(self):
    import webbrowser
    webbrowser.open('http://www.ccpn.ac.uk')


  def showCodeInspectionPopup(self):
    info = MessageDialog.showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)


  def showUpdatePopup(self):
    
    if not self.updatePopup:
      self.updatePopup = UpdatePopup(self)
    self.updatePopup.show()
    self.updatePopup.raise_()

  def showFeedbackPopup(self):
    
    if not self.feedbackPopup:
      self.feedbackPopup = FeedbackPopup(self)
    self.feedbackPopup.show()
    self.feedbackPopup.raise_()

  def runMacro(self, macroFile:str=None):
    """
    Runs a macro if a macro is specified, or opens a dialog box for selection of a macro file and then
    runs the selected macro.
    """
    if macroFile is None:
      macroFile = QtGui.QFileDialog.getOpenFileName(self, "Run Macro", self._appBase.preferences.general.macroPath)
    self._appBase.preferences.recentMacros.append(macroFile)
    self._fillRecentMacrosMenu()
    # self.fillRecentMacrosMenu()
    self.pythonConsole.runMacro(macroFile)

  # def showMoleculeDisplay(self):
  #   from ccpn.lib.moleculebox import MoleculeDisplay
  #   self.moleculeDisplay = MoleculeDisplay(self.dockArea)

  def showPeakTable(self, position:str='left', relativeTo:CcpnDock=None, selectedList:PeakList=None):
    """
    Displays Peak table on left of main window with specified list selected.
    """
    peakList = PeakTable(self._project, selectedList=selectedList)
    if relativeTo is not None:
      self.dockArea.addDock(peakList, position=position, relativeTo=relativeTo)
    else:
      self.dockArea.addDock(peakList, position='bottom')

    # self.pythonConsole.writeModuleDisplayCommand('showPeakTable')
    self.pythonConsole.writeConsoleCommand("application.showPeakTable()")

  def showChemicalShiftTable(self, position='bottom'):
    """
    Displays Chemical Shift table.
    """
    from application.core.modules.ChemicalShiftTable import ChemicalShiftTable
    chemicalShiftTable = ChemicalShiftTable(chemicalShiftLists=self._project.chemicalShiftLists)
    self.dockArea.addDock(chemicalShiftTable, position=position)
    # self.pythonConsole.writeModuleDisplayCommand('showChemicalShiftTable')
    self.pythonConsole.writeConsoleCommand("application.showChemicalShiftTable()")

  # def showParassignPeakTable(self, position='left', relativeTo=None):
  #   peakList = ParassignModule(name="Peak Table", peakLists=self._project.peakLists)
  #   if relativeTo is not None:
  #     self.dockArea.addDock(peakList, position=position, relativeTo=relativeTo)
  #   else:
  #     self.dockArea.addDock(peakList, position='bottom')

  def showBackboneAssignmentModule(self, position=None, relativeTo=None):
    """
    Displays Backbone Assignment module.
    """
    self.bbModule = BackboneAssignmentModule(self._project)
    if position is not None and relativeTo is not None:
      self.dockArea.addDock(self.bbModule, position=position, relativeTo=relativeTo)
    else:
      self.dockArea.addDock(self.bbModule, position='bottom')
    # assigner = self.showAssigner('bottom')
    # self.bbModule.setAssigner(assigner)
    # self.pythonConsole.writeModuleDisplayCommand('showBackboneAssignmentModule')
    self.pythonConsole.writeConsoleCommand("application.showBackboneAssignmentModule()")
    return self.bbModule

  def showPickAndAssignModule(self):
    """Displays Pick and Assign module."""
    self.paaModule = PickAndAssignModule(self.dockArea, self._project)
    self.dockArea.addDock(self.paaModule)
    # self.pythonConsole.writeModuleDisplayCommand('showPickAndAssignModule')
    self.pythonConsole.writeConsoleCommand("application.showPickAndAssignModule()")
    return self.paaModule

  def showAtomSelector(self):
    """Displays Atom Selector."""
    self.atomSelector = AtomSelector(self, project=self._project)
    self.dockArea.addDock(self.atomSelector)
    # self.pythonConsole.writeModuleDisplayCommand('showAtomSelector')
    self.pythonConsole.writeConsoleCommand("application.showAtomSelector()")
    return self.atomSelector

  def showResidueInformation(self):
    """Displays Residue Information module."""
    from application.core.modules.ResidueInformation import ResidueInformation
    self.dockArea.addDock(ResidueInformation(self, self._project))
    # self.pythonConsole.writeModuleDisplayCommand('showResidueInformation')
    self.pythonConsole.writeConsoleCommand("application.showResidueInformation()")

  def showDataPlottingModule(self):
    dpModule = DataPlottingModule(self.dockArea)

  def showRefChemicalShifts(self):
    """Displays Reference Chemical Shifts module."""
    from application.core.modules.ReferenceChemicalShifts import ReferenceChemicalShifts
    self.refChemShifts = ReferenceChemicalShifts(self.project, self.dockArea)

  def saveProject(self):
    """Opens save Project as dialog box if project has not been saved before, otherwise saves
    project with existing project name."""
    apiProject = self._project._wrappedData.root
    if hasattr(apiProject, '_temporaryDirectory'):
      self.saveProjectAs()
    else:
      self._appBase.saveProject()
    
  def saveProjectAs(self):
    """Opens save Project as dialog box and saves project with name specified in the file dialog."""
    dialog = QtGui.QFileDialog(self, caption='Save Project As...')
    dialog.setFileMode(QtGui.QFileDialog.AnyFile)
    dialog.setAcceptMode(1)
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
        msg ='Path "%s" already exists, continue?' % newPath
        if not MessageDialog.showYesNo(title, msg, self, colourScheme=self.colourScheme):
          return
      self._appBase.saveProject(newPath=newPath)#, newProjectName=os.path.basename(newPath))

  def printToFile(self, spectrumDisplay=None):
    
    current = self._appBase.current
    if not spectrumDisplay:
      spectrumDisplay = current.spectrumDisplay
    if not spectrumDisplay and current.strip:
      spectrumDisplay = current.strip.spectrumDisplay
    if not spectrumDisplay and self.spectrumDisplays:
      spectrumDisplay = self.spectrumDisplays[0]
    if spectrumDisplay:
      path = QtGui.QFileDialog.getSaveFileName(self, caption='Print to File', filter='SVG (*.svg)')
      if not path:
        return
      spectrumDisplay.printToFile(path)
    
  def hideConsole(self):
    """Hides python console"""
    self.pythonConsoleDock.hide()

  def showConsole(self):
    """Displays python console"""
    self.pythonConsoleDock.show()

  # def showPopupGenerator(self):
  #   from application.core.modules.GuiPopupGenerator import PopupGenerator
  #   popup = PopupGenerator(self)
  #   popup.exec_()
  #   popup.raise_()

