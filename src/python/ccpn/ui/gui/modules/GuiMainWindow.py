"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date$"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

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
import json
import os
import sys
from functools import partial

from PyQt4 import QtGui, QtCore

from ccpn.Assign.modules.AtomSelector import AtomSelector
# from ccpn.Assign.modules.BackboneAssignmentModule import BackboneAssignmentModule
# from ccpn.Assign.modules.PickAndAssignModule import PickAndAssignModule
from ccpn.Assign.modules.SequenceGraph import SequenceGraph

from ccpn.core.PeakList import PeakList
# from ccpn.Screen.modules.MixtureAnalysis import MixtureAnalysis
# from ccpn.Screen.modules.ScreeningSettings import ScreeningSettings
# from ccpn.Screen.modules.ShowScreeningHits import ShowScreeningHits
# from ccpn.Screen.popups.SampleSetupPopup import SamplePopup
from ccpn.core.lib.Version import revision
from ccpn.framework.update.UpdatePopup import UpdatePopup
from ccpn.ui.gui.modules.DataPlottingModule import DataPlottingModule
from ccpn.ui.gui.modules.GuiBlankDisplay import GuiBlankDisplay
from ccpn.ui.gui.modules.GuiWindow import GuiWindow
from ccpn.ui.gui.modules.MacroEditor import MacroEditor
from ccpn.ui.gui.modules.NotesEditor import NotesEditor
# from ccpn.ui.gui.modules.PeakAssigner import PeakAssigner
from ccpn.ui.gui.modules.PeakTable import PeakTable
from ccpn.ui.gui.modules.SequenceModule import SequenceModule
from ccpn.ui.gui.popups.BackupPopup import BackupPopup
from ccpn.ui.gui.popups.ExperimentTypePopup import ExperimentTypePopup
from ccpn.ui.gui.popups.FeedbackPopup import FeedbackPopup
from ccpn.ui.gui.popups.PreferencesPopup import PreferencesPopup
# from ccpn.ui.gui.popups.SetupNmrResiduesPopup import SetupNmrResiduesPopup
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Action import Action
from ccpn.ui.gui.widgets.CcpnWebView import CcpnWebView
from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.IpythonConsole import IpythonConsole
from ccpn.ui.gui.widgets.Menu import Menu, MenuBar
from ccpn.ui.gui.widgets.SideBar import SideBar
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpn.util import Path
from ccpn.util.Common import uniquify
try:
  from ccpn.util.Translation import translator
except ImportError:
  from ccpn.framework.Translation import translator


class GuiMainWindow(QtGui.QMainWindow, GuiWindow):

  def __init__(self):
    QtGui.QMainWindow.__init__(self)

    self.setGeometry(540, 40, 900, 900)

    GuiWindow.__init__(self)
    # self._appBase._mainWindow = self
    self.framework._mainWindow = self
    self.recordingMacro = False
    self._setupWindow()
    self._setupMenus()
    self._initProject()
    self.closeEvent = self._closeEvent
    self.connect(self, QtCore.SIGNAL('triggered()'), self._closeEvent)

    self.feedbackPopup = None
    self.updatePopup = None
    self.backupPopup = None

    self.backupTimer = QtCore.QTimer()
    self.connect(self.backupTimer, QtCore.SIGNAL('timeout()'), self.backupProject)
    if self._appBase.preferences.general.autoBackupEnabled:
      self._startBackupTimer()

  def _initProject(self):
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

  def _startBackupTimer(self):
    """
    #CCPN INTERNAL - called in setBackupFrequency and toggleBackup methods of BackupPopup
    and __init__ of this class.
    """
    self.backupTimer.start(60000 * self._appBase.preferences.general.autoBackupFrequency)

  def _stopBackupTimer(self):
    """
    #CCPN INTERNAL - called in toggleBackup method of BackupPopup
    """
    if self.backupTimer.isActive():
      self.backupTimer.stop()

  def backupProject(self):
    
    apiIo.backupProject(self._project._wrappedData.parent)

  def _setupWindow(self):
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
                      'preferences': self._appBase.preferences, 'project': self._project, 'current': self._appBase.current,
                      'undo': self.undo, 'redo': self.redo}

    self.pythonConsole = IpythonConsole(self, self.namespace, mainWindow=self)


    self.sideBar = SideBar(parent=self)
    self.sideBar.setDragDropMode(self.sideBar.DragDrop)
    self.splitter3.addWidget(self.sideBar)
    self.splitter1.addWidget(self.splitter3)
    self.sideBar.itemDoubleClicked.connect(self._raiseObjectProperties)
    self.splitter1.addWidget(self.moduleArea)
    self.setCentralWidget(self.splitter1)
    self.statusBar().showMessage('Ready')
    self._setShortcuts()


  def _setupMenus(self):
    """
    Creates menu bar for main window and creates the appropriate menus according to the arguments
    passed at startup.

    This currently pulls info on what menus to create from Framework.  Once GUI and Project are
    separated, Framework should be able to call a method to set the menus.

    """

    self._menuBar = MenuBar(self)
    for m in self.framework._menuSpec:
      self._createMenu(m)
    self.setMenuBar(self._menuBar)
    self._menuBar.setNativeMenuBar(False)
    self.show()

    #
    # fileMenu = Menu("Project", self)
    # self.screenMenu = Menu("Screen", self)
    # self.metabolomicsMenu = Menu("Metabolomics", self)
    # spectrumMenu = Menu("Spectrum", self)
    # viewMenu = Menu("View", self)
    # moleculeMenu = Menu("Molecules", self)
    # restraintsMenu = Menu("Restraints", self)
    # structuresMenu = Menu("Structures", self)
    # macroMenu = Menu("Macro", self)
    # pluginsMenu = Menu("Plugins", self)
    # helpMenu = Menu("Help", self)


    # fileMenu.addAction(Action(self, "New", callback=self.newProject, shortcut='pn'))
    #
    # fileMenu.addAction(Action(self, "Open ...", callback=self.loadAProject, shortcut="po"))
    # self.recentProjectsMenu = fileMenu.addMenu("Open Recent")
    # self._fillRecentProjectsMenu()
    # fileMenu.addAction(Action(self, "Load Spectrum", callback=lambda: self.loadData(text='Load Spectrum'), shortcut='ls'))
    # fileMenu.addAction(Action(self, "Load Data", callback=self.loadData, shortcut='ld'))
    # fileMenu.addSeparator()
    # fileMenu.addAction(Action(self, "Save", callback=self.saveProject, shortcut="ps"))
    # fileMenu.addAction(Action(self, "Save As ...", shortcut="sa", callback=self.saveProjectAs))
    # fileMenu.addSeparator()
    # fileMenu.addAction(Action(self, "Undo", callback=self.undo, shortcut=QtGui.QKeySequence("Ctrl+z")))
    # fileMenu.addAction(Action(self, "Redo", callback=self.redo, shortcut=QtGui.QKeySequence("Ctrl+y")))
    #
    # fileMenu.addSeparator()
    # fileMenu.addAction(Action(self, "Summary ...", self.displayProjectSummary))
    # fileMenu.addAction(Action(self, "Archive", self.archiveProject))
    # fileMenu.addAction(Action(self, "Backup ...", self.showBackupPopup))
    # fileMenu.addSeparator()
    # fileMenu.addAction(Action(self, "Preferences ...", callback=self.showApplicationPreferences))
    # fileMenu.addSeparator()
    # fileMenu.addAction(Action(self, "Close Program", callback=self._closeEvent, shortcut="qt"))


    # self.screenMenu.addSeparator()
    # self.screenMenu.addAction(Action(self, 'Generate Mixtures', callback=self.showSamplePopup, shortcut="cs"))
    # self.screenMenu.addAction(Action(self, 'Mixtures Analysis', callback=self.showSampleAnalysis, shortcut="st"))
    # self.screenMenu.addSeparator()
    # self.screenMenu.addAction(Action(self, 'Screening Settings', callback=self.showScreeningSetup, shortcut="sc"))
    # self.screenMenu.addAction(Action(self, 'Hit Analysis', callback=self.showHitAnalysisModule, shortcut="ha"))

    # self.metabolomicsMenu.addSeparator()
    # self.metabolomicsMenu.addAction(Action(self, 'Analyse Metabolite', callback=self.showMetabolomicsModule, shortcut="mm"))
    # self.metabolomicsMenu.addAction(Action(self, 'Integral Assignment', callback=self.showIntegralAssigmentModule, shortcut="ia"))
    # self.decompMenu = self.metabolomicsMenu.addMenu('Decomposition')

    # self.decompMenu.addAction(Action(self, 'Run PCA', callback=self.showPCAModule))

    # self.metabolomicsMenu.addAction(Action(self, 'Peak Assignment', callback=self.showPeakAssigmentModule))
    # self.metabolomicsMenu.addAction(Action(self, 'Pick and Fit', callback=self.showPickandFitModule))
    #
    # self.metabolomicsMenu.addAction(Action(self, 'Spectrum Groups ...', callback=None))

    # spectrumMenu.addAction(Action(self, "Spectrum Groups ...", callback=self.showProjectionPopup, shortcut='ss'))
    # spectrumMenu.addAction(Action(self, "Set Experiment Types ...", callback=self.showExperimentTypePopup, shortcut='et'))
    # spectrumMenu.addSeparator()
    # spectrumMenu.addAction(Action(self, "Pick Peaks ...", callback=self.showPeakPickPopup, shortcut='pp'))
    # spectrumMenu.addAction(Action(self, 'Integration', callback=self.showIntegrationModule, shortcut='it'))
    # spectrumMenu.addSeparator()
    # spectrumMenu.addAction(Action(self, "Make Projection ...", callback=self.showProjectionPopup, shortcut='pj'))
    # spectrumMenu.addAction(Action(self, "Phasing Console", partial(self.togglePhaseConsole, self), shortcut='pc'))

    # moleculeMenu.addAction(Action(self, "Create Molecule ...", callback=self.showMoleculePopup, shortcut='cm'))
    # self.sequenceAction = Action(self, 'Show Sequence', callback=self.toggleSequenceModule, shortcut='sq', checkable=True)
    # self.sequenceAction.setChecked(False)
    # if hasattr(self, 'sequenceModule'):
    #   self.sequenceAction.setChecked(self.sequenceModule.isVisible())
    # else:
    #   self.sequenceAction.setChecked(False)
    # moleculeMenu.addAction(self.sequenceAction)
    # moleculeMenu.addAction(Action(self, "Inspect ...", callback=self.inspectMolecule))
    # moleculeMenu.addSeparator()
    # moleculeMenu.addAction(Action(self, "Reference Chemical Shifts", callback=self.showRefChemicalShifts, shortcut='rc'))

    # macroMenu.addAction(Action(self, "Edit ...", callback=self.showMacroEditor))
    # macroMenu.addAction(Action(self, "New from Console ...", callback=self.newMacroFromConsole))
    # macroMenu.addAction(Action(self, "New from Log ...", callback=self.newMacroFromLog))
    # macroMenu.addAction(Action(self, "Record Macro ...", callback=self.startMacroRecord))
    # macroMenu.addSeparator()
    # macroMenu.addAction(Action(self, "Run ...", shortcut="rm", callback=self.runMacro))
    #
    # self.recentMacrosMenu = macroMenu.addMenu("Run Recent")
    # # self._fillRecentMacrosMenu()
    # macroMenu.addSeparator()
    # macroMenu.addAction(Action(self, "Define User Shortcuts ...", callback=self.defineUserShortcuts))
    # #
    # viewNewMenu = viewMenu.addMenu("New")
    # viewMenu.addAction(Action(self, "New Blank Display", callback=self.addBlankDisplay, shortcut="nd"))
    # viewMenu.addSeparator()
    # viewMenu.addAction(Action(self, "Chemical Shift Table", callback=self.showChemicalShiftTable, shortcut="ct"))
    # viewMenu.addAction(Action(self, "NmrResidue Table", callback=self.showNmrResidueTable, shortcut="nt"))
    # viewMenu.addAction(Action(self, "Peak Table", callback=self.showPeakTable, shortcut="lt"))
    # viewMenu.addSeparator()
    # viewMenu.addAction(Action(self, 'Sequence Graph', callback=self.showSequenceGraph, shortcut='sg'))
    # viewMenu.addAction(Action(self, 'Atom Selector', callback=self.showAtomSelector, shortcut='as'))


    #NBNB Need to decide how we are to handle layouts if at all
    # viewLayoutMenu = viewMenu.addMenu("Layout")
    # viewLayoutMenu.addAction(Action(self, "Default", callback=self.setLayoutToDefault))
    # viewLayoutMenu.addAction(Action(self, "Save", callback=self.saveLayout))
    # viewLayoutMenu.addAction(Action(self, "Save As...", callback=self.saveLayoutAs))
    # viewLayoutMenu.addAction(Action(self, "Restore", callback=self.restoreLayout))
    # viewMenu.addSeparator()
    # self.consoleAction = Action(self, "Console", callback=self.toggleConsole, shortcut="py",
    #                                      checkable=True)
    # self.consoleAction.setChecked(self.pythonConsole.isVisible())
    # viewMenu.addAction(self.consoleAction)
    #
    #

    # helpMenu.addAction(Action(self, "Command ...", callback=self.showCommandHelp))
    # tutorialsMenu = helpMenu.addMenu("Tutorials")
    # tutorialsMenu.addAction(Action(self, "Beginners Tutorial", callback=self.showBeginnersTutorial))
    # tutorialsMenu.addAction(Action(self, "Backbone Tutorial", callback=self.showBackboneTutorial))
    # helpMenu.addAction(Action(self, "Show Shortcuts", callback=self.showShortcuts))
    # helpMenu.addAction(Action(self, "Show CcpNmr V3 Documentation", callback=self.showWrapperDocumentation))
    # helpMenu.addAction(Action(self, "Show API Documentation", callback=self._showApiDocumentation))
    # helpMenu.addSeparator()
    # helpMenu.addAction(Action(self, "About CcpNmr V3 ...", callback=self.showAboutPopup))
    # helpMenu.addAction(Action(self, "About CCPN ...", callback=self.showAboutCcpnPopup))
    # helpMenu.addSeparator()
    # helpMenu.addAction(Action(self, "Inspect Code ...", callback=self.showCodeInspectionPopup))
    # helpMenu.addAction(Action(self, "Check for Updates ...", callback=self.showUpdatePopup))
    # helpMenu.addAction(Action(self, "Submit Feedback ...", callback=self.showFeedbackPopup))


    # pluginsMenu.addAction(Action(self, "PARAssign Setup", callback=self.showParassignSetup, shortcut='q1'))

    #
    # self._menuBar.addMenu(fileMenu)
    # self._menuBar.addMenu(spectrumMenu)
    #
    # if self._appBase.applicationName == 'Screen':
    #   self._menuBar.addMenu(self.screenMenu)
    # self._menuBar.addMenu(moleculeMenu)
    #
    # if self._appBase.applicationName == 'Metabolomics':
    #   self._menuBar.addMenu(self.metabolomicsMenu)
    #

    # if 'Structure' in self._appBase.components:
    #   self._menuBar.addMenu(restraintsMenu)
    #   self._menuBar.addMenu(structuresMenu)
    # self._menuBar.addMenu(viewMenu)
    # self._menuBar.addMenu(pluginsMenu)
    # self._menuBar.addMenu(macroMenu)
    # self._menuBar.addMenu(helpMenu)



  def _createMenu(self, spec, targetMenu=None):
    menu = self._addMenu(spec[0], targetMenu)
    self._addMenuActions(menu, spec[1])

  def _addMenu(self, menuTitle, targetMenu=None):
    if targetMenu is None:
      targetMenu = self._menuBar
    if isinstance(targetMenu, MenuBar):
      menu = Menu(menuTitle, self)
      targetMenu.addMenu(menu)
    else:
      menu = targetMenu.addMenu(menuTitle)
    return menu

  def _addMenuActions(self, menu, actions):
    for action in actions:
      if len(action) == 0:
        menu.addSeparator()
      elif len(action) == 2:
        if callable(action[1]):
          menu.addAction(Action(self, action[0], callback=action[1]))
        else:
          self._createMenu(action, menu)
      elif len(action) == 3:
        kwDict = dict(action[2])
        menu.addAction(Action(self, action[0], callback=action[1], **kwDict))


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
    
    newModule = CcpnModule("API Documentation")
    path = os.path.join(Path.getTopDirectory(), 'doc', *args)
    view = CcpnWebView(path)
    newModule.addWidget(view)
    self.moduleArea.addModule(newModule)
    



  # def showPeakAssigner(self, position='bottom', relativeTo=None):
  #   """Displays assignment module."""
  #   self.assignmentModule = PeakAssigner(self, self._project, self._project._appBase.current.peaks)
  #   self.moduleArea.addModule(self.assignmentModule, position=position, relativeTo=relativeTo)
  #   self.pythonConsole.writeConsoleCommand("application.showAssignmentModule()")
  #   self.project._logger.info("application.showAssignmentModule()")

  def showNmrResidueModule(self, position='bottom', relativeTo=None):
    """Shows Nmr Residue Module."""
    from ccpn.ui.gui.popups.NmrResiduePopup import NmrResiduePopup
    newModule = CcpnModule("Nmr Residue")
    nmrResidueModule = NmrResiduePopup(newModule, self._project)
    newModule.layout.addWidget(nmrResidueModule)
    self.moduleArea.addModule(newModule, position=position, relativeTo=relativeTo)


  # def showProjectionPopup(self):
  #   pass

  def addBlankDisplay(self, position='right', relativeTo=None):
    """Adds a Blank Display to the main window if one does not already exist."""
    # if not hasattr(self, 'blankDisplay') or self.blankDisplay is None:
    #   self.blankDisplay = GuiBlankDisplay(self.moduleArea)
    # else:
    #   self.moduleArea.addModule(self.blankDisplay, position=position, relativeTo=relativeTo)

    if 'BLANK DISPLAY' in self.moduleArea.findAll()[1]:
      blankDisplay = self.moduleArea.findAll()[1]['BLANK DISPLAY']
      if blankDisplay.isVisible():
        return
      else:
        self.moduleArea.moveModule(blankDisplay, position, None)
    else:
      self.blankDisplay = GuiBlankDisplay(self.moduleArea)
      self.moduleArea.addModule(self.blankDisplay, position, None)

    self.pythonConsole.writeConsoleCommand(("application.addBlankDisplay()"))
    self._project._logger.info("application.addBlankDisplay()")

  def showSequenceModule(self, position='top', relativeTo=None):
    """
    Displays Sequence Module at the top of the screen.
    """
    self.sequenceModule = SequenceModule(self._project)
    self.moduleArea.addModule(self.sequenceModule, position=position, relativeTo=relativeTo)
    return self.sequenceModule

  def hideSequenceModule(self):
    """Hides sequence module"""
    self.sequenceModule.close()
    delattr(self, 'sequenceModule')


  def showNmrResidueTable(self, position='bottom', relativeTo=None):
    """Displays Nmr Residue Table"""
    from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTable
    nmrResidueTable = NmrResidueTable(self, self._project)
    nmrResidueTableModule = CcpnModule(name='Nmr Residue Table')
    nmrResidueTableModule.layout.addWidget(nmrResidueTable)
    self.moduleArea.addModule(nmrResidueTableModule, position=position, relativeTo=relativeTo)
    self.pythonConsole.writeConsoleCommand("application.showNmrResidueTable()")
    self.project._logger.info("application.showNmrResidueTable()")

  def toggleSequenceModule(self):
    """Toggles whether Sequence Module is displayed or not"""
    if hasattr(self, 'sequenceModule'):
      if self.sequenceModule.isVisible():
        self.hideSequenceModule()

    else:
      self.showSequenceModule()
    self.pythonConsole.writeConsoleCommand("application.toggleSequenceModule()")
    self.project._logger.info("application.toggleSequenceModule()")

  def loadAProject(self, projectDir=None):
    """
    Opens a loadProject dialog box if project directory is not specified.
    Loads the selected project.
    """
    result = self._queryCloseProject(title='Open Project', phrase='open another')
    if result:
      if projectDir is None:
        dialog = FileDialog(self, fileMode=2, text="Open Project", acceptMode=0, preferences=self._appBase.preferences.general)
        projectDir = dialog.selectedFiles()[0]

      if projectDir:
        self._appBase.loadProject(projectDir)

  def showPeakPickPopup(self):
    """
    Displays Peak Picking Popup.
    """
    from ccpn.ui.gui.popups.PeakFind import PeakFindPopup
    popup = PeakFindPopup(parent=self, project=self.project)
    popup.exec_()

  def showSequenceGraph(self, position:str='bottom', nextTo:CcpnModule=None):
    """
    Displays assigner at the bottom of the screen, relative to another module if nextTo is specified.
    """
    self.assigner = SequenceGraph(project=self.framework.project)
    if hasattr(self.framework, 'bbModule'):
      self.framework.bbModule._connectSequenceGraph(self.assigner)

    if nextTo is not None:
      self.moduleArea.addModule(self.assigner, position=position, relativeTo=nextTo)
    else:
      self.moduleArea.addModule(self.assigner, position=position)
    self.pythonConsole.writeConsoleCommand("application.showSequenceGraph()")
    self.project._logger.info("application.showSequenceGraph()")
    return self.assigner

  def _raiseObjectProperties(self, item):
    """get object from Pid and dispatch call depending on type

    NBNB TBD How about refactoring so that we have a shortClassName:Popup dictionary?"""
    dataPid = item.data(0, QtCore.Qt.DisplayRole)
    project = self._project
    obj = project.getByPid(dataPid)
    if obj is not None:
      self.sideBar.raisePopup(obj, item)
    elif item.data(0, QtCore.Qt.DisplayRole) == '<New>':
      self.sideBar._createNewObject(item)

    else:
      project._logger.error("Double-click activation not implemented for Pid %s, object %s"
                            % (dataPid, obj))

  def _fillRecentProjectsMenu(self):
    """
    Populates recent projects menu with 10 most recently loaded projects
    specified in the preferences file.
    """
    # translator.setSilent()
    for recentFile in self._appBase.preferences.recentFiles:
      self.action = Action(self, text=recentFile, translate=False,
                           callback=partial(self.loadAProject, projectDir=recentFile))
      self.recentProjectsMenu.addAction(self.action)
    # translator.setLoud()
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
    fileName = apiIo.packageProject(apiProject, filePrefix, includeBackups=True, includeLogs=True)
    
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

  # def showSamplePopup(self):
  #   """
  #   Displays Sample creation popup.
  #   """
  #   popup = SamplePopup(parent=None, project=self.project)
  #   popup.exec_()
  #   popup.raise_()
  #   self.pythonConsole.writeConsoleCommand("application.showSamplePopup()")
  #   self.project._logger.info("application.showSamplePopup()")
  #
  # def showSampleAnalysis(self, position='bottom', relativeTo=None):
  #   """
  #   Displays Sample Analysis Module
  #   """
  #   showSa = MixtureAnalysis(self._project)
  #   self.moduleArea.addModule(showSa, position=position, relativeTo=relativeTo)
  #   self.pythonConsole.writeConsoleCommand("application.showSampleAnalysis()")
  #   self.project._logger.info("application.showSampleAnalysis()")
  #
  # def showScreeningSetup(self, position='bottom', relativeTo=None):
  #   showSc = ScreeningSettings(self.project)
  #   self.moduleArea.addModule(showSc, position=position)
  #   self.pythonConsole.writeConsoleCommand("application.showScreeningSetup()")
  #   self.project._logger.info("application.showScreeningSetup()")
  #
  # def showHitAnalysisModule(self, position='top', relativeTo:CcpnModule=None):
  #
  #   self.showScreeningHits = ShowScreeningHits(self.project)
  #   self.moduleArea.addModule(self.showScreeningHits, position, None)
  #   spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
  #   # spectrum only to create a display
  #   self.project.strips[0].viewBox.autoRange()
  #   self.showScreeningHits._clearDisplayView()
  #   self.moduleArea.moveModule(spectrumDisplay.module, position='top', neighbor=self.showScreeningHits)
  #     # returns a clean display
  #
  #   self.pythonConsole.writeConsoleCommand("application.showScreeningHits()")
  #   self.project._logger.info("application.showScreeningHits()")

  def showMetabolomicsModule(self, position:str='bottom', relativeTo:CcpnModule=None):
    self.showMm = MetabolomicsModule(self.project)
    self.moduleArea.addModule(self.showMm, position=position)



  # def showPCAModule(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   from ccpn.Metabolomics.Pca import PcaModule
  #   self.pcaModule = PcaModule(self.project)
  #   self.moduleArea.addModule(self.pcaModule, position=position)

  def showPickandFitModule(self, position:str='bottom', relativeTo:CcpnModule=None):
    spectrumDisplay = self.createSpectrumDisplay()
    from ccpn.AnalysisMetabolomics.PickandFit import PickandFit, PickandFitTable
    fitModule = PickandFit(spectrumDisplay.module, strip=spectrumDisplay.strips[0], grid=(2, 0), gridSpan=(1, 4))
    PickandFitTable(spectrumDisplay.module, project=self._project, fitModule=fitModule, grid=(0, 4), gridSpan=(3, 1))
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None


  # def showIntegrationModule(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
  #   from ccpn.Metabolomics.Integration import IntegrationTable, IntegrationWidget
  #   spectrumDisplay.integrationWidget = IntegrationWidget(spectrumDisplay.module, project=self._project, grid=(2, 0), gridSpan=(1, 4))
  #   spectrumDisplay.integrationTable = IntegrationTable(spectrumDisplay.module, project=self._project, grid=(0, 4), gridSpan=(3, 1))
  #   self._appBase.current.strip = spectrumDisplay.strips[0]
  #   if self.blankDisplay:
  #     self.blankDisplay.setParent(None)
  #     self.blankDisplay = None

  def showIntegralAssigmentModule(self, position:str='bottom', relativeTo:CcpnModule=None):
    spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
    from ccpn.AnalysisMetabolomics.IntegralAssignment import IntegralAssignment
    self.iaModule = IntegralAssignment(self)
    spectrumDisplay.module.layout.addWidget(self.iaModule, 2, 0, 1, 4)
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None

  def showPeakAssigmentModule(self, position:str='bottom', relativeTo:CcpnModule=None):
    spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
    from ccpn.AnalysisMetabolomics.PeakAssignment import PeakAssignment
    PeakAssignment(spectrumDisplay.module, self._project, grid=(2, 0), gridSpan=(1, 4))
    if self.blankDisplay:
      self.blankDisplay.setParent(None)
      self.blankDisplay = None

  # def showSpectrumGroupModule(self, position:str='bottom', relativeTo:CcpnModule=None):
    # spectra = [spectrum for group in self.project.spectrumGroups for spectrum in group.spectra]
    # spectrumDisplay = self.createSpectrumDisplay(spectra[0])
    # for spectrum in spectra[1:]:
    #   spectrumDisplay.displaySpectrum(spectrum)
    # from ccpn.Metabolomics.SpectrumGroupsWidget import SpectrumGroupsWidget
    # SpectrumGroupsWidget(spectrumDisplay.module, self._project, spectrumDisplay.strips[0], grid=(2, 0), gridSpan=(1, 4))
    # spectrumDisplay.spectrumToolBar.hide()
    # if self.blankDisplay:
    #   self.blankDisplay.setParent(None)
    #   self.blankDisplay = None


  def showParassignSetup(self):
    try:
      from ccpn.plugins.PARAssign.PARAssignSetup import ParassignSetup
      self.ps = ParassignSetup(project=self.project)
      newModule = CcpnModule(name='PARAssign Setup')
      newModule.addWidget(self.ps)
      self.moduleArea.addModule(newModule)
    except ImportError:
      print('PARAssign cannot be found')


  def toggleConsole(self):
    """
    Toggles whether python console is displayed at bottom of the main window.
    """

    # if hasattr(self, 'pythonConsoleModule'):
    #   if self.pythonConsoleModule.isVisible():
    #     self.hideConsole()
    #   else:
    #     self.showConsole()
    # else:
    #   self.pythonConsoleModule = CcpnModule(name='Python Console')
    #   self.pythonConsoleModule.layout.addWidget(self.pythonConsole)
    #   self.moduleArea.addModule(self.pythonConsoleModule, 'bottom')

    if 'PYTHON CONSOLE' in self.moduleArea.findAll()[1]:
      if self.pythonConsoleModule.isVisible():
        self.pythonConsoleModule.hide()
      else:
        self.moduleArea.moveModule(self.pythonConsoleModule, 'bottom', None)
    else:
      self.pythonConsoleModule = CcpnModule(name='Python Console')
      self.pythonConsoleModule.layout.addWidget(self.pythonConsole)
      self.moduleArea.addModule(self.pythonConsoleModule, 'bottom')

  # def movePythonConsole(self):
  #   """
  #     move PythonConsole below all the modules.
  #     """
  #   if 'PYTHON CONSOLE' in self.moduleArea.findAll()[1]:
  #     pythonConsole = self.moduleArea.findAll()[1]['PYTHON CONSOLE']
  #     for container in self.moduleArea.findAll()[0]:
  #       if container and pythonConsole is not None:
  #         self.moduleArea.moveModule(pythonConsole, 'bottom', container)

  def showMacroEditor(self):
    """
    Displays macro editor.
    """
    editor = MacroEditor(self.moduleArea, self, "Macro Editor")

  def newMacroFromConsole(self):
    """
    Displays macro editor with contents of python console inside.
    """
    editor = MacroEditor(self.moduleArea, self, "Macro Editor")
    editor.textBox.setText(self.pythonConsole.textEditor.toPlainText())

  def newMacroFromLog(self):
    """
    Displays macro editor with contents of the log.
    """
    editor = MacroEditor(self.moduleArea, self, "Macro Editor")
    l = open(self.project._logger.logPath, 'r').readlines()
    text = ''.join([line.strip().split(':', 6)[-1]+'\n' for line in l])
    editor.textBox.setText(text)

  def startMacroRecord(self):
    """
    Displays macro editor with additional buttons for recording a macro.
    """
    self.macroEditor = MacroEditor(self.moduleArea, self, "Macro Editor", showRecordButtons=True)
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
    if self._appBase.ui.mainWindow is not None:
      mainWindow = self._appBase.ui.mainWindow
    else:
      mainWindow = self._appBase._mainWindow
    self.notesEditor = NotesEditor(mainWindow.moduleArea, self._project, name='Notes Editor')

  # def showMoleculePopup(self):
  #   """
  #   Displays sequence creation popup.
  #   """
  #   from ccpn.ui.gui.modules.CreateSequence import CreateSequence
  #   popup = CreateSequence(self, project=self._project).exec_()
  #   self.pythonConsole.writeConsoleCommand("application.showMoleculePopup()")
  #   self.project._logger.info("application.showMoleculePopup()")

  # def inspectMolecule(self):
  #   info = MessageDialog.showInfo('Not implemented yet!',
  #         'This function has not been implemented in the current version',
  #         colourScheme=self.colourScheme)



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
    from ccpn.ui.gui.popups.AboutPopup import AboutPopup
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
    self.pythonConsole._runMacro(macroFile)


  def showPeakTable(self, position:str='left', relativeTo:CcpnModule=None, selectedList:PeakList=None):
    """
    Displays Peak table on left of main window with specified list selected.
    """
    peakList = PeakTable(self._project, selectedList=selectedList)
    self.moduleArea.addModule(peakList, position=position, relativeTo=relativeTo)
    self.pythonConsole.writeConsoleCommand("application.showPeakTable()")
    self.project._logger.info("application.showPeakTable()")

  def showChemicalShiftTable(self, position:str='bottom', relativeTo:CcpnModule=None):
    """
    Displays Chemical Shift table.
    """
    from ccpn.ui.gui.modules.ChemicalShiftTable import NmrAtomShiftTable as Table
    chemicalShiftTable = Table(chemicalShiftLists=self._project.chemicalShiftLists)
    self.moduleArea.addModule(chemicalShiftTable, position=position, relativeTo=relativeTo)
    self.pythonConsole.writeConsoleCommand("application.showChemicalShiftTable()")
    self.project._logger.info("application.showChemicalShiftTable()")


  # def showBackboneAssignmentModule(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   """
  #   Displays Backbone Assignment module.
  #   """
  #   self.bbModule = BackboneAssignmentModule(self._project)
  #   self.moduleArea.addModule(self.bbModule, position=position, relativeTo=relativeTo)
  #   self.pythonConsole.writeConsoleCommand("application.showBackboneAssignmentModule()")
  #   self.project._logger.info("application.showBackboneAssignmentModule()")
  #
  #   return self.bbModule

  # def showPickAndAssignModule(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   """Displays Pick and Assign module."""
  #   self.paaModule = PickAndAssignModule(self.moduleArea, self._project)
  #   self.moduleArea.addModule(self.paaModule, position=position, relativeTo=relativeTo)
  #   self.pythonConsole.writeConsoleCommand("application.showPickAndAssignModule()")
  #   self.project._logger.info("application.showPickAndAssignModule()")
  #   return self.paaModule

  def showAtomSelector(self, position:str='bottom', relativeTo:CcpnModule=None):
    """Displays Atom Selector."""
    self.atomSelector = AtomSelector(self, project=self._project)
    self.moduleArea.addModule(self.atomSelector, position=position, relativeTo=relativeTo)
    self.pythonConsole.writeConsoleCommand("application.showAtomSelector()")
    self.project._logger.info("application.showAtomSelector()")
    return self.atomSelector

  # def showResidueInformation(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   """Displays Residue Information module."""
  #   from ccpn.ui.gui.modules.ResidueInformation import ResidueInformation
  #   self.moduleArea.addModule(ResidueInformation(self, self._project), position=position, relativeTo=relativeTo)
  #   self.pythonConsole.writeConsoleCommand("application.showResidueInformation()")
  #   self.project._logger.info("application.showResidueInformation()")

  def showDataPlottingModule(self, position:str='bottom', relativeTo:CcpnModule=None):
    dpModule = DataPlottingModule(self.moduleArea, position=position, relativeTo=relativeTo)

  # def showRefChemicalShifts(self):
  #   """Displays Reference Chemical Shifts module."""
  #   from ccpn.ui.gui.modules.ReferenceChemicalShifts import ReferenceChemicalShifts
  #   self.refChemShifts = ReferenceChemicalShifts(self.project, self.moduleArea)

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
    from ccpn.ui.gui import AppBase  # has to be here because of circular import
    apiProject = self._project._wrappedData.root
    newPath = AppBase.getSaveDirectory(apiProject, self._appBase.preferences)
    if newPath:
      newProjectPath = apiIo.ccpnProjectPath(newPath)
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
    
  # def hideConsole(self):
  #   """Hides python console"""
  #   self.pythonConsoleModule.hide()
  #
  # def showConsole(self):
  #   """Displays python console"""
  #   self.pythonConsoleModule.show()
