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
from ccpncore.gui.FileDialog import FileDialog
from ccpncore.gui.Menu import Menu, MenuBar
from application.core.gui.SideBar import SideBar
from ccpncore.util import Io as ioUtil
from ccpncore.util import Path
from ccpncore.util.Common import uniquify
from ccpncore.util.Translation import translator
from application.core.gui.Assigner import Assigner
from application.core.gui.IpythonConsole import IpythonConsole
from application.metabolomics.Metabolomics import MetabolomicsModule
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

from application.core.popups.BackupPopup import BackupPopup
from application.core.popups.ExperimentTypePopup import ExperimentTypePopup
from application.core.popups.FeedbackPopup import FeedbackPopup
from application.core.popups.PreferencesPopup import PreferencesPopup
from application.core.popups.SetupNmrResiduesPopup import SetupNmrResiduesPopup
from ccpn.lib.Version import revision
from application.core.update.UpdatePopup import UpdatePopup

from application.screen.modules.ShowScreeningHits import ShowScreeningHits
from application.screen.modules.ScreeningSettings import ScreeningSettings
from application.screen.modules.MixtureAnalysis import MixtureAnalysis
from application.screen.popups.SampleSetupPopup import SamplePopup


class GuiMainWindow(QtGui.QMainWindow, GuiWindow):

  def __init__(self):
    QtGui.QMainWindow.__init__(self)

    self.setGeometry(540, 40, 900, 900)

    GuiWindow.__init__(self)
    self.recordingMacro = False
    self.setupWindow()
    self.setupMenus()
    self.initProject()
    self.closeEvent = self._closeEvent
    self.connect(self, QtCore.SIGNAL('triggered()'), self._closeEvent)

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
    isNew = self._apiWindow.root.isModified  # a bit of a hack this, but should be correct

    project = self._project
    path = project.path
    self.namespace['project'] = project
    msg = path + (' created' if isNew else ' opened')
    self.statusBar().showMessage(msg)

    msg2 = 'project = %sProject("%s")' % (('new' if isNew else 'open'), path)
    self.pythonConsole.writeConsoleCommand(msg2)

    # if not isNew:
    recentFiles = self._appBase.preferences.recentFiles
    if len(recentFiles) >= 10:
      recentFiles.pop()
    recentFiles.insert(0, path)
    self.colourScheme = self._appBase.preferences.general.colourScheme
    recentFiles = uniquify(recentFiles)
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
    
    ioUtil.backupProject(self._project._wrappedData.parent)

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

    self.namespace = {'loadProject': self._appBase.loadProject,
                      'newProject': self._appBase.newProject, 'loadData': self.loadData, 'application': self,
                      'preferences': self._appBase.preferences, 'project': self._project, 'current': self._appBase.current}

    self.pythonConsole = IpythonConsole(self, self.namespace, mainWindow=self)


    self.sideBar = SideBar(parent=self)
    self.sideBar.setDragDropMode(self.sideBar.DragDrop)
    self.splitter3.addWidget(self.sideBar)
    self.splitter1.addWidget(self.splitter3)
    self.sideBar.itemDoubleClicked.connect(self.raiseProperties)
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
    fileMenu = Menu("Project", self)
    self.screenMenu = Menu("Screen", self)
    self.metabolomicsMenu = Menu("Metabolomics", self)
    spectrumMenu = Menu("Spectrum", self)
    viewMenu = Menu("View", self)
    moleculeMenu = Menu("Molecules", self)
    restraintsMenu = Menu("Restraints", self)
    structuresMenu = Menu("Structures", self)
    macroMenu = Menu("Macro", self)
    pluginsMenu = Menu("Plugins", self)
    helpMenu = Menu("Help", self)


    fileMenu.addAction(Action(self, "New", callback=self.newProject, shortcut='pn'))

    fileMenu.addAction(Action(self, "Open ...", callback=self.loadAProject, shortcut="po"))
    self.recentProjectsMenu = fileMenu.addMenu("Open Recent")
    self._fillRecentProjectsMenu()
    fileMenu.addAction(Action(self, "Load Spectrum", callback=lambda: self.loadData(text='Load Spectrum'), shortcut='ls'))
    fileMenu.addAction(Action(self, "Load Data", callback=self.loadData, shortcut='ld'))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Save", callback=self.saveProject, shortcut="ps"))
    fileMenu.addAction(Action(self, "Save As ...", shortcut="sa", callback=self.saveProjectAs))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Undo", callback=self.undo, shortcut=QtGui.QKeySequence("Ctrl+z")))
    fileMenu.addAction(Action(self, "Redo", callback=self.redo, shortcut=QtGui.QKeySequence("Ctrl+y")))

    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Summary ...", self.displayProjectSummary))
    fileMenu.addAction(Action(self, "Archive", self.archiveProject))
    fileMenu.addAction(Action(self, "Backup ...", self.showBackupPopup))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Preferences ...", callback=self.showApplicationPreferences))
    fileMenu.addSeparator()
    fileMenu.addAction(Action(self, "Close Program", callback=self.closeEvent, shortcut="qt"))


    self.screenMenu.addSeparator()
    self.screenMenu.addAction(Action(self, 'Generate Mixtures', callback=self.createSample, shortcut="cs"))
    self.screenMenu.addAction(Action(self, 'Mixtures Analysis', callback=self.showSampleAnalysis, shortcut="st"))
    self.screenMenu.addSeparator()
    self.screenMenu.addAction(Action(self, 'Screening Settings', callback=self.showScreeningSetup, shortcut="sc"))
    self.screenMenu.addAction(Action(self, 'Hit Analysis', callback=self.showHitAnalysisModule, shortcut="ha"))

    self.metabolomicsMenu.addSeparator()
    self.metabolomicsMenu.addAction(Action(self, 'Analyse Metabolite', callback=self.showMetabolomicsModule, shortcut="mm"))
    self.metabolomicsMenu.addAction(Action(self, 'Integral Assignment', callback=self.showIntegralAssigmentModule, shortcut="ia"))
    self.decompMenu = self.metabolomicsMenu.addMenu('Decomposition')
    self.decompMenu.addAction(Action(self, 'Run PCA', callback=self.showPCAModule))
    self.metabolomicsMenu.addAction(Action(self, 'Peak Assignment', callback=self.showPeakAssigmentModule))
    self.metabolomicsMenu.addAction(Action(self, 'Pick and Fit', callback=self.showPickandFitModule))
    self.metabolomicsMenu.addAction(Action(self, 'Spectrum Groups ...', callback=self.showSpectrumGroupModule))

    spectrumMenu.addAction(Action(self, "Spectrum Groups ...", callback=self.showProjectionPopup, shortcut='ss'))
    spectrumMenu.addAction(Action(self, "Set Experiment Types ...", callback=self.showExptTypePopup, shortcut='et'))
    spectrumMenu.addSeparator()
    spectrumMenu.addAction(Action(self, "Pick Peaks ...", callback=self.pickPeaks, shortcut='pp'))
    spectrumMenu.addAction(Action(self, 'Integration', callback=self.showIntegrationModule, shortcut='it'))
    spectrumMenu.addSeparator()
    spectrumMenu.addAction(Action(self, "Make Projection ...", callback=self.showProjectionPopup, shortcut='pj'))
    spectrumMenu.addAction(Action(self, "Phasing Console", partial(self.togglePhaseConsole, self), shortcut='pc'))

    moleculeMenu.addAction(Action(self, "Create Molecule ...", callback=self.showMoleculePopup, shortcut='cm'))
    self.sequenceAction = Action(self, 'Show Sequence', callback=self.toggleSequence, shortcut='sq', checkable=True)
    if hasattr(self, 'sequenceWidget'):
      self.sequenceAction.setChecked(self.sequenceWidget.isVisible())
    else:
      self.sequenceAction.setChecked(False)
    moleculeMenu.addAction(self.sequenceAction)
    moleculeMenu.addAction(Action(self, "Inspect ...", callback=self.inspectMolecule))
    moleculeMenu.addSeparator()
    moleculeMenu.addAction(Action(self, "Reference Chemical Shifts", callback=self.showRefChemicalShifts, shortcut='rc'))

    macroMenu.addAction(Action(self, "Edit ...", callback=self.editMacro))
    macroMenu.addAction(Action(self, "New from Console ...", callback=self.newMacroFromConsole))
    macroMenu.addAction(Action(self, "New from Log ...", callback=self.newMacroFromLog))
    macroMenu.addAction(Action(self, "Record Macro ...", callback=self.startMacroRecord))
    macroMenu.addSeparator()
    macroMenu.addAction(Action(self, "Run ...", shortcut="rm", callback=self.runMacro))

    self.recentMacrosMenu = macroMenu.addMenu("Run Recent")
    self._fillRecentMacrosMenu()
    macroMenu.addSeparator()
    macroMenu.addAction(Action(self, "Define User Shortcuts ...", callback=self.defineUserShortcuts))

    # viewNewMenu = viewMenu.addMenu("New")
    viewMenu.addAction(Action(self, "New Blank Display", callback=self.addBlankDisplay, shortcut="nd"))
    viewMenu.addSeparator()
    viewMenu.addAction(Action(self, "Chemical Shift Table", callback=self.showChemicalShiftTable, shortcut="ct"))
    viewMenu.addAction(Action(self, "NmrResidue Table", callback=self.showNmrResidueTable, shortcut="nt"))
    viewMenu.addAction(Action(self, "Peak Table", callback=self.showPeakTable, shortcut="lt"))
    viewMenu.addSeparator()
    viewMenu.addAction(Action(self, 'Sequence Graph', callback=self.showSequenceGraph, shortcut='sg'))
    viewMenu.addAction(Action(self, 'Atom Selector', callback=self.showAtomSelector, shortcut='as'))


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



    helpMenu.addAction(Action(self, "Command ...", callback=self.showCommandHelp))
    tutorialsMenu = helpMenu.addMenu("Tutorials")
    tutorialsMenu.addAction(Action(self, "Beginners Tutorial", callback=self.showBeginnersTutorial))
    tutorialsMenu.addAction(Action(self, "Backbone Tutorial", callback=self.showBackboneTutorial))
    helpMenu.addAction(Action(self, "Show Shortcuts", callback=self.showShortcuts))
    helpMenu.addAction(Action(self, "Show CcpNmr V3 Documentation", callback=self.showWrapperDocumentation))
    helpMenu.addAction(Action(self, "Show API Documentation", callback=self.showApiDocumentation))
    helpMenu.addSeparator()
    helpMenu.addAction(Action(self, "About CcpNmr V3 ...", callback=self.showAboutPopup))
    helpMenu.addAction(Action(self, "About CCPN ...", callback=self.showAboutCcpnPopup))
    helpMenu.addSeparator()
    helpMenu.addAction(Action(self, "Inspect Code ...", callback=self.showCodeInspectionPopup))
    helpMenu.addAction(Action(self, "Check for Updates ...", callback=self.showUpdatePopup))
    helpMenu.addAction(Action(self, "Submit Feedback ...", callback=self.showFeedbackPopup))

    assignMenu = Menu("Assign", self)
    assignMenu.addAction(Action(self, "Setup NmrResidues", callback=self.showSetupNmrResiduesPopup, shortcut='sn'))
    assignMenu.addAction(Action(self, "Pick and Assign", callback=self.showPickAndAssignModule, shortcut='pa'))
    assignMenu.addSeparator()
    assignMenu.addAction(Action(self, "Backbone Assignment", callback=self.showBackboneAssignmentModule, shortcut='bb'))
    # assignMenu.addAction(Action(self, "Sidechain Assignment", callback=self.showPickAndAssignModule, shortcut='sc'))
    assignMenu.addSeparator()
    assignMenu.addAction(Action(self, "Peak Assigner", callback=self.showAssignmentModule, shortcut='aa'))
    assignMenu.addAction(Action(self, "Residue Information", callback=self.showResidueInformation, shortcut='ri'))

    pluginsMenu.addAction(Action(self, "PARAssign Setup", callback=self.showParassignSetup, shortcut='q1'))



    self._menuBar.addMenu(fileMenu)
    self._menuBar.addMenu(spectrumMenu)

    if self._appBase.applicationName == 'Screen':
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
    self._menuBar.addMenu(pluginsMenu)
    self._menuBar.addMenu(macroMenu)
    self._menuBar.addMenu(helpMenu)
    self.setMenuBar(self._menuBar)
    self._menuBar.setNativeMenuBar(False)
    self.show()

  def _queryCloseProject(self, title, phrase):

    apiProject = self._project._wrappedData.root
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

  def showExptTypePopup(self):
    """
    Displays experiment type popup.
    """
    popup = ExperimentTypePopup(self, self._project)
    popup.exec_()

  def showSetupNmrResiduesPopup(self):
    popup = SetupNmrResiduesPopup(self, self._project)
    popup.exec_()


  def showWrapperDocumentation(self):
    """Displays CCPN wrapper documentation in a module."""
    self._showDocumentation("CCPN Documentation", 'build', 'html', 'index.html')

  def showShortcuts(self):
    path = os.path.join(Path.getTopDirectory(), 'doc', 'static', 'AnalysisShortcuts.pdf')
    if 'linux' in sys.platform.lower():
      os.system("xdg-open %s" % path)
    else:
      os.system('open %s' % path)


  def showAssignmentModule(self):
    """Displays assignment module."""
    self.assignmentModule = AssignmentModule(self, self._project, self._project._appBase.current.peaks)
    self.dockArea.addDock(self.assignmentModule)
    self.pythonConsole.writeConsoleCommand("application.showAssignmentModule()")
    self.project._logger.info("application.showAssignmentModule()")

  def showNmrResidueModule(self):
    """Shows Nmr Residue Module."""
    from application.core.popups.NmrResiduePopup import NmrResiduePopup
    newDock = CcpnDock("Nmr Residue")
    nmrResidueModule = NmrResiduePopup(newDock, self._project)
    newDock.layout.addWidget(nmrResidueModule)
    self.dockArea.addDock(newDock)


  def showProjectionPopup(self):
    pass

  def addBlankDisplay(self):
    """Adds a Blank Display to the main window if one does not already exist."""
    if not hasattr(self, 'blankDisplay') or self.blankDisplay is None:
      self.blankDisplay = GuiBlankDisplay(self.dockArea)
    else:
      self.dockArea.addDock(self.blankDisplay, 'right')
    self.pythonConsole.writeConsoleCommand(("application.addBlankDisplay()"))
    self._project._logger.info("application.addBlankDisplay()")

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
    nmrResidueTableDock = CcpnDock(name='Nmr Residue Table')
    nmrResidueTableDock.layout.addWidget(nmrResidueTable)
    self.dockArea.addDock(nmrResidueTableDock, 'bottom')
    self.pythonConsole.writeConsoleCommand("application.showNmrResidueTable()")
    self.project._logger.info("application.showNmrResidueTable()")

  def toggleSequence(self):
    """Toggles whether Sequence Module is displayed or not"""
    if hasattr(self, 'sequenceWidget'):
      if self.sequenceWidget.isVisible():
        self.hideSequence()

    else:
      self.showSequence()
    self.pythonConsole.writeConsoleCommand("application.toggleSequence()")
    self.project._logger.info("application.toggleSequence()")

  def loadAProject(self, projectDir=None):
    """
    Opens a loadProject dialog box if project directory is not specified.
    Loads the selected project.
    """
    result = self._queryCloseProject(title='Open Project', phrase='open another')
    
    if result:
      if projectDir is None:
        dialog = FileDialog(self, fileMode=2, text="Open Project", acceptMode=0, preferences=self._appBase.preferences.general)
        # dialog.exec_()
        projectDir = dialog.selectedFiles()[0]

      if projectDir:
        self._appBase.loadProject(projectDir)

  def pickPeaks(self):
    """
    Displays Peak Picking Popup.
    """
    from application.core.popups.PeakFind import PeakFindPopup
    popup = PeakFindPopup(parent=self, project=self.project)
    popup.exec_()

  def showSequenceGraph(self, position:str='bottom', nextTo:CcpnDock=None):
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
    self.pythonConsole.writeConsoleCommand("application.showSequenceGraph()")
    self.project._logger.info("application.showSequenceGraph()")
    return self.assigner

  def raiseProperties(self, item):
    """get object from Pid and dispatch call depending on type

    NBNB TBD How about refactoring so that we have a shortClassName:Popup dictionary?"""
    dataPid = item.data(0, QtCore.Qt.DisplayRole)
    project = self._project
    obj = project.getByPid(dataPid)
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
    translator.setSilent()
    for recentFile in self._appBase.preferences.recentFiles:
      self.action = Action(self, text=recentFile, callback=partial(self.loadAProject, projectDir=recentFile))
      self.recentProjectsMenu.addAction(self.action)
    translator.setLoud()
    self.recentProjectsMenu.addAction(Action(self, text='Clear', callback=self.clearRecentProjectsMenu))

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
    fileName = ioUtil.packageProject(apiProject, filePrefix, includeBackups=True, includeLogs=True)
    
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

  def _closeEvent(self, event=None):
    """
    Saves application preferences. Displays message box asking user to save project or not.
    Closes Application.
    """
    prefPath = os.path.expanduser("~/.ccpn/v3settings.json")
    directory = os.path.dirname(prefPath)
    if not os.path.exists(directory):
      try:
        os.makedirs(directory)
      except Exception as e:
        self._project._logger.warning('Preferences not saved: %s' % (directory, e))
        return
          
    prefFile = open(prefPath, 'w+')
    json.dump(self._appBase.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
    prefFile.close()

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
      prefFile = open(prefPath, 'w+')
      json.dump(self._appBase.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
      prefFile.close()
      self._appBase._closeProject()
      QtGui.QApplication.quit()
    else:
      if event:
        event.ignore()

  def createSample(self):
    """
    Displays Sample creation module.
    """
    popup = SamplePopup(parent=None, project=self.project)
    popup.exec_()
    popup.raise_()
    self.pythonConsole.writeConsoleCommand("application.createSample()")
    self.project._logger.info("application.createSample()")

  def showSampleAnalysis(self):
    """
    Displays Sample Analysis Module
    """
    showSa = MixtureAnalysis(self._project)
    self.dockArea.addDock(showSa, position='bottom')
    self.pythonConsole.writeConsoleCommand("application.showSampleAnalysis()")
    self.project._logger.info("application.showSampleAnalysis()")

  def showScreeningSetup(self):
    showSc = ScreeningSettings(self.project)
    self.dockArea.addDock(showSc, position='bottom')
    self.pythonConsole.writeConsoleCommand("application.showScreeningSetup()")
    self.project._logger.info("application.showScreeningSetup()")

  def showHitAnalysisModule(self):

    self.showScreeningHits = ShowScreeningHits(self.project)
    self.dockArea.addDock(self.showScreeningHits, position='bottom')
    print(self.createSpectrumDisplay)
    spectrumDisplay = self.createSpectrumDisplay(
      self._project.spectrumHits[0]._parent)  # spectrum only to create a display
    # self._project.spectrumHits[0]._parent.peakLists[0].pickPeaks1dFiltered(ignoredRegions=None, noiseThreshold=0)
    self.dockArea.moveDock(spectrumDisplay.dock, position='top', neighbor=self.showScreeningHits)
    self.dockArea.guiWindow.deleteBlankDisplay()
    self.project.strips[0].viewBox.autoRange()

    self.showScreeningHits.clearDisplayView()  # returns a clean display

    self.pythonConsole.writeConsoleCommand("application.showScreeningHits()")
    self.project._logger.info("application.showScreeningHits()")

  def showMetabolomicsModule(self):
    self.showMm = MetabolomicsModule(self.project)
    self.dockArea.addDock(self.showMm, position='bottom')



  def showPCAModule(self):
    from application.metabolomics.Pca import PcaModule
    self.pcaModule = PcaModule(self.project)
    self.dockArea.addDock(self.pcaModule, position='bottom')

  def showPickandFitModule(self):
    spectrumDisplay = self.createSpectrumDisplay()
    from application.metabolomics.PickandFit import PickandFit, PickandFitTable
    fitModule = PickandFit(spectrumDisplay.dock, strip=spectrumDisplay.strips[0], grid=(2, 0), gridSpan=(1, 4))
    PickandFitTable(spectrumDisplay.dock, project=self._project, fitModule=fitModule, grid=(0, 4), gridSpan=(3, 1))
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None


  def showIntegrationModule(self):
    spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
    from application.metabolomics.Integration import IntegrationTable, IntegrationWidget
    spectrumDisplay.integrationWidget = IntegrationWidget(spectrumDisplay.dock, project=self._project, grid=(2, 0), gridSpan=(1, 4))
    spectrumDisplay.integrationTable = IntegrationTable(spectrumDisplay.dock, project=self._project, grid=(0, 4), gridSpan=(3, 1))
    self._appBase.current.strip = spectrumDisplay.strips[0]
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None

  def showIntegralAssigmentModule(self):
    spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
    from application.metabolomics.IntegralAssignment import IntegralAssignment
    self.iaModule = IntegralAssignment(self)
    spectrumDisplay.dock.layout.addWidget(self.iaModule, 2, 0, 1, 4)
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None

  def showPeakAssigmentModule(self):
    spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
    from application.metabolomics.PeakAssignment import PeakAssignment
    PeakAssignment(spectrumDisplay.dock, self._project, grid=(2, 0), gridSpan=(1, 4))
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None

  def showSpectrumGroupModule(self):
    spectra = [spectrum for group in self.project.spectrumGroups for spectrum in group.spectra]
    spectrumDisplay = self.createSpectrumDisplay(spectra[0])
    for spectrum in spectra[1:]:
      spectrumDisplay.displaySpectrum(spectrum)
    from application.metabolomics.SpectrumGroupsWidget import SpectrumGroupsWidget
    SpectrumGroupsWidget(spectrumDisplay.dock, self._project, spectrumDisplay.strips[0], grid=(2, 0), gridSpan=(1, 4))
    spectrumDisplay.spectrumToolBar.hide()
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None


  def showParassignSetup(self):
    try:
      from application.plugins.PARAssign.PARAssignSetup import ParassignSetup
      self.ps = ParassignSetup(project=self.project)
      newDock = CcpnDock(name='PARAssign Setup')
      newDock.addWidget(self.ps)
      self.dockArea.addDock(newDock)
    except ImportError:
      print('PARAssign cannot be found')


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

  def newMacroFromLog(self):
    """
    Displays macro editor with contents of log.
    """
    editor = MacroEditor(self.dockArea, self, "Macro Editor")
    l = open(self.project._logger.logPath, 'r').readlines()
    text = ''.join([line.strip().split(':', 6)[-1]+'\n' for line in l])
    editor.textBox.setText(text)

  def startMacroRecord(self):
    """
    Displays macro editor with additional buttons for recording a macro.
    """
    self.macroEditor = MacroEditor(self.dockArea, self, "Macro Editor", showRecordButtons=True)
    self.pythonConsole.writeConsoleCommand("application.startMacroRecord()")
    self.project._logger.info("application.startMacroRecord()")


  def _fillRecentMacrosMenu(self):
    """
    Populates recent macros menu with last ten macros ran.
    """

    recentMacros = uniquify(self._appBase.preferences.recentMacros)

    translator.setSilent()
    for recentMacro in recentMacros:
      self.action = Action(self, text=recentMacro, callback=partial(self.runMacro, macroFile=recentMacro))
      self.recentMacrosMenu.addAction(self.action)
    translator.setLoud()
    self.recentMacrosMenu.addAction(Action(self, text='Clear', callback=self.clearRecentMacros))


  def clearRecentMacros(self):
    self.recentMacrosMenu.clear()
    self._appBase.preferences.recentMacros = []

  def clearRecentProjectsMenu(self):
    self.recentProjectsMenu.clear()
    self._appBase.preferences.recentFiles = []


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
    self.pythonConsole.writeConsoleCommand("application.showMoleculePopup()")
    self.project._logger.info("application.showMoleculePopup()")

  def inspectMolecule(self):
    info = MessageDialog.showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)



  def showCommandHelp(self):
    info = MessageDialog.showInfo('Not implemented yet!',
          'This function has not been implemented in the current version',
          colourScheme=self.colourScheme)


  def showBeginnersTutorial(self):
    path = os.path.join(Path.getTopDirectory(), 'data', 'testProjects', 'CcpnSec5BBTutorial', 'BeginnersTutorial.pdf')
    if 'linux' in sys.platform.lower():
      os.system("xdg-open %s" % path)
    else:
      os.system('open %s' % path)

  def showBackboneTutorial(self):
    path = os.path.join(Path.getTopDirectory(), 'data', 'testProjects', 'CcpnSec5BBTutorial', 'BackboneAssignmentTutorial.pdf')
    if 'linux' in sys.platform.lower():
      os.system("xdg-open %s" % path)
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
    self.pythonConsole.runMacro(macroFile)


  def showPeakTable(self, position:str='left', relativeTo:CcpnDock=None, selectedList:PeakList=None):
    """
    Displays Peak table on left of main window with specified list selected.
    """
    peakList = PeakTable(self._project, selectedList=selectedList)
    if relativeTo is not None:
      self.dockArea.addDock(peakList, position=position, relativeTo=relativeTo)
    else:
      self.dockArea.addDock(peakList, position='bottom')

    self.pythonConsole.writeConsoleCommand("application.showPeakTable()")
    self.project._logger.info("application.showPeakTable()")

  def showChemicalShiftTable(self, position='bottom'):
    """
    Displays Chemical Shift table.
    """
    from application.core.modules.ChemicalShiftTable import NmrAtomShiftTable as Table
    # from application.core.modules.ChemicalShiftTable import ChemicalShiftTable as Table
    chemicalShiftTable = Table(chemicalShiftLists=self._project.chemicalShiftLists)
    self.dockArea.addDock(chemicalShiftTable, position=position)
    self.pythonConsole.writeConsoleCommand("application.showChemicalShiftTable()")
    self.project._logger.info("application.showChemicalShiftTable()")


  def showBackboneAssignmentModule(self, position=None, relativeTo=None):
    """
    Displays Backbone Assignment module.
    """
    self.bbModule = BackboneAssignmentModule(self._project)
    if position is not None and relativeTo is not None:
      self.dockArea.addDock(self.bbModule, position=position, relativeTo=relativeTo)
    else:
      self.dockArea.addDock(self.bbModule, position='bottom')
    self.pythonConsole.writeConsoleCommand("application.showBackboneAssignmentModule()")
    self.project._logger.info("application.showBackboneAssignmentModule()")

    return self.bbModule

  def showPickAndAssignModule(self):
    """Displays Pick and Assign module."""
    self.paaModule = PickAndAssignModule(self.dockArea, self._project)
    self.dockArea.addDock(self.paaModule)
    self.pythonConsole.writeConsoleCommand("application.showPickAndAssignModule()")
    self.project._logger.info("application.showPickAndAssignModule()")
    return self.paaModule

  def showAtomSelector(self):
    """Displays Atom Selector."""
    self.atomSelector = AtomSelector(self, project=self._project)
    self.dockArea.addDock(self.atomSelector)
    self.pythonConsole.writeConsoleCommand("application.showAtomSelector()")
    self.project._logger.info("application.showAtomSelector()")
    return self.atomSelector

  def showResidueInformation(self):
    """Displays Residue Information module."""
    from application.core.modules.ResidueInformation import ResidueInformation
    self.dockArea.addDock(ResidueInformation(self, self._project))
    self.pythonConsole.writeConsoleCommand("application.showResidueInformation()")
    self.project._logger.info("application.showResidueInformation()")

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
    from application.core import AppBase  # has to be here because of circular import
    apiProject = self._project._wrappedData.root
    newPath = AppBase.getSaveDirectory(apiProject, self._appBase.preferences)
    if newPath:
      newProjectPath = ioUtil.ccpnProjectPath(newPath)
      self._appBase.saveProject(newPath=newProjectPath, newProjectName=os.path.basename(newPath), createFallback=False)

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
