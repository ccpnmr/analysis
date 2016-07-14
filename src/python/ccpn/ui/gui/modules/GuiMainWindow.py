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

from ccpn.AnalysisAssign.modules.AtomSelector import AtomSelector

from ccpn.core.PeakList import PeakList

from ccpn.framework.update.UpdatePopup import UpdatePopup
from ccpn.ui.gui.modules.DataPlottingModule import DataPlottingModule
from ccpn.ui.gui.modules.GuiBlankDisplay import GuiBlankDisplay
from ccpn.ui.gui.modules.GuiWindow import GuiWindow
from ccpn.ui.gui.modules.MacroEditor import MacroEditor
from ccpn.ui.gui.modules.NotesEditor import NotesEditor
from ccpn.ui.gui.modules.PeakTable import PeakTable
from ccpn.ui.gui.modules.SequenceModule import SequenceModule
from ccpn.ui.gui.popups.BackupPopup import BackupPopup
from ccpn.ui.gui.popups.FeedbackPopup import FeedbackPopup
from ccpn.ui.gui.popups.PreferencesPopup import PreferencesPopup
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
from ccpn.framework.Translation import translator


class GuiMainWindow(QtGui.QMainWindow, GuiWindow):

  def __init__(self):
    QtGui.QMainWindow.__init__(self)

    self.setGeometry(540, 40, 900, 900)

    GuiWindow.__init__(self)
    # self._appBase._mainWindow = self
    self.application._mainWindow = self
    self.recordingMacro = False
    self._setupWindow()
    self._setupMenus()
    self._initProject()
    self.closeEvent = self._closeEvent
    self.connect(self, QtCore.SIGNAL('triggered()'), self._closeEvent)

    # do not need an unRegisterNotify because those removed when mainWindow / project destroyed
    self.application.current.registerNotify(self._resetRemoveStripAction, 'strips')

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

    self.colourScheme = self._appBase.preferences.general.colourScheme
    self._appBase._updateRecentFiles()
    self.pythonConsole.setProject(project)
    self._updateWindowTitle()


  # def _updateRecentFiles(self, oldPath=None):
  #   project = self._project
  #   path = project.path
  #   recentFiles = self._appBase.preferences.recentFiles
  #   if not hasattr(project._wrappedData.root, '_temporaryDirectory'):
  #     if path in recentFiles:
  #       recentFiles.remove(path)
  #     elif oldPath in recentFiles:
  #       recentFiles.remove(oldPath)
  #     elif len(recentFiles) >= 10:
  #       recentFiles.pop()
  #     recentFiles.insert(0, path)
  #   recentFiles = uniquify(recentFiles)
  #   self._fillRecentProjectsMenu()
  #   self._appBase.preferences.recentFiles = recentFiles


  def _updateWindowTitle(self):
    """
    #CCPN INTERNAL - called in saveProject method of Framework
    """    
    self.setWindowTitle('%s %s (Revision: %s): %s' % (self._appBase.applicationName,
                                            self._appBase.applicationVersion, self._appBase.revision,
                                            self._project.name))

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


  def getMenuAction(self, menuString, topMenuAction=None):
    if topMenuAction is None:
      topMenuAction = self._menuBar
    splitMenuString = menuString.split('->')
    if len(splitMenuString) > 1:
      topMenuAction = self.getMenuAction('->'.join(splitMenuString[:-1]), topMenuAction)
    for a in topMenuAction.actions():
      if a.text() == splitMenuString[-1]:
        return a.menu() or a
    raise ValueError('Menu item not found.')


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

    self.namespace = {'application': self.application,
                      'current': self.application.current,
                      'preferences': self.application.preferences,
                      'redo': self.application.redo,
                      'undo': self.application.undo,

                      'ui': self.application.ui,
                      'mainWindow': self,

                      'project': self.application.project,
                      'loadProject': self.application.loadProject,
                      'newProject': self.application.newProject,
                     }
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
    for m in self.application._menuSpec:
      self._createMenu(m)
    self.setMenuBar(self._menuBar)
    self._menuBar.setNativeMenuBar(False)
    self.show()

    self._fillRecentProjectsMenu()
    self._fillRecentMacrosMenu()


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
    

  # def _showDocumentation(self, title, *args):
  #
  #   newModule = CcpnModule("API Documentation")
  #   path = os.path.join(Path.getTopDirectory(), 'doc', *args)
  #   view = CcpnWebView(path)
  #   newModule.addWidget(view)
  #   self.moduleArea.addModule(newModule)
    

  # def showNmrResidueModule(self, position='bottom', relativeTo=None):
  #   """Shows Nmr Residue Module."""
  #   from ccpn.ui.gui.popups.NmrResiduePopup import NmrResiduePopup
  #   newModule = CcpnModule("Nmr Residue")
  #   nmrResidueModule = NmrResiduePopup(newModule, self._project)
  #   newModule.layout.addWidget(nmrResidueModule)
  #   self.moduleArea.addModule(newModule, position=position, relativeTo=relativeTo)


  def addBlankDisplay(self, position='right', relativeTo=None):
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

  # def showSequenceModule(self, position='top', relativeTo=None):
  #   """
  #   Displays Sequence Module at the top of the screen.
  #   """
  #   self.sequenceModule = SequenceModule(self._project)
  #   self.moduleArea.addModule(self.sequenceModule, position=position, relativeTo=relativeTo)
  #   return self.sequenceModule

  # def hideSequenceModule(self):
  #   """Hides sequence module"""
  #   self.sequenceModule.close()
  #   delattr(self, 'sequenceModule')


  # def showNmrResidueTable(self, position='bottom', relativeTo=None):
  #   """Displays Nmr Residue Table"""
  #   from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTable
  #   nmrResidueTable = NmrResidueTable(self, self._project)
  #   nmrResidueTableModule = CcpnModule(name='Nmr Residue Table')
  #   nmrResidueTableModule.layout.addWidget(nmrResidueTable)
  #   self.moduleArea.addModule(nmrResidueTableModule, position=position, relativeTo=relativeTo)
  #   self.pythonConsole.writeConsoleCommand("application.showNmrResidueTable()")
  #   self.project._logger.info("application.showNmrResidueTable()")

  # def toggleSequenceModule(self):
  #   """Toggles whether Sequence Module is displayed or not"""
  #   if hasattr(self, 'sequenceModule'):
  #     if self.sequenceModule.isVisible():
  #       self.hideSequenceModule()
  #
  #   else:
  #     self.showSequenceModule()
  #   self.pythonConsole.writeConsoleCommand("application.toggleSequenceModule()")
  #   self.project._logger.info("application.toggleSequenceModule()")


  def loadProject(self, projectDir=None):
    """
    Opens a loadProject dialog box if project directory is not specified.
    Loads the selected project.
    """
    result = self._queryCloseProject(title='Open Project', phrase='open another')
    if result:
      if projectDir is None:
        dialog = FileDialog(self, fileMode=2, text="Open Project", acceptMode=0, preferences=self._appBase.preferences.general)
        projectDir = dialog.selectedFile()


      if projectDir:
        self.application.loadProject(projectDir)


  # def showPeakPickPopup(self):
  #   """
  #   Displays Peak Picking Popup.
  #   """
  #   from ccpn.ui.gui.popups.PeakFind import PeakFindPopup
  #   popup = PeakFindPopup(parent=self, project=self.project)
  #   popup.exec_()


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
    recentFileLocations = uniquify(self.application.preferences.recentFiles)
    recentFileMenu = self.getMenuAction('Project->Open Recent')
    recentFileMenu.clear()
    for recentFile in recentFileLocations:
     action = Action(self, text=recentFile, translate=False,
                     callback=partial(self.application.loadProject, path=recentFile))
     recentFileMenu.addAction(action)
    recentFileMenu.addSeparator()
    recentFileMenu.addAction(Action(recentFileMenu, text='Clear',
                                    callback=self.application.clearRecentProjects))


  def _fillRecentMacrosMenu(self):
    """
    Populates recent macros menu with last ten macros ran.
    TODO: make sure that running a macro adds it to the prefs and calls this function
    """

    recentMacros = uniquify(self.application.preferences.recentMacros)
    recentMacrosMenu = self.getMenuAction('Macro->Run Recent')
    recentMacrosMenu.clear()
    for recentMacro in recentMacros:
      action = Action(self, text=recentMacro, translate=False,
                      callback=partial(self.runMacro, macroFile=recentMacro))
      recentMacrosMenu.addAction(action)
    recentMacrosMenu.addSeparator()
    recentMacrosMenu.addAction(Action(recentMacrosMenu, text='Clear',
                                      callback=self.application.clearRecentMacros))


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

  # def archiveProject(self):
  #
  #   project = self._project
  #   apiProject = project._wrappedData.parent
  #   projectPath = project.path
  #   now = datetime.datetime.now().strftime('%y%m%d%H%M%S')
  #   filePrefix = '%s_%s' % (os.path.basename(projectPath), now)
  #   filePrefix = os.path.join(os.path.dirname(projectPath), filePrefix)
  #   fileName = apiIo.packageProject(apiProject, filePrefix, includeBackups=True, includeLogs=True)
  #
  #   MessageDialog.showInfo('Project Archived',
  #         'Project archived to %s' % fileName, colourScheme=self.colourScheme)
    
  # def showBackupPopup(self):
  #
  #   if not self.backupPopup:
  #     self.backupPopup = BackupPopup(self)
  #   self.backupPopup.show()
  #   self.backupPopup.raise_()
  
  # def showApplicationPreferences(self):
  #   """
  #   Displays Application Preferences Popup.
  #   """
  #   PreferencesPopup(preferences=self._appBase.preferences, project=self._project).exec_()

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


  # def showMetabolomicsModule(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   self.showMm = MetabolomicsModule(self.project)
  #   self.moduleArea.addModule(self.showMm, position=position)



  # def showPickandFitModule(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   spectrumDisplay = self.createSpectrumDisplay()
  #   from ccpn.AnalysisMetabolomics.PickandFit import PickandFit, PickandFitTable
  #   fitModule = PickandFit(spectrumDisplay.module, strip=spectrumDisplay.strips[0], grid=(2, 0), gridSpan=(1, 4))
  #   PickandFitTable(spectrumDisplay.module, project=self._project, fitModule=fitModule, grid=(0, 4), gridSpan=(3, 1))
  #   if self.blankDisplay:
  #     self.blankDisplay.setParent(None)
  #     self.blankDisplay = None


  # def showIntegralAssigmentModule(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
  #   from ccpn.AnalysisMetabolomics.IntegralAssignment import IntegralAssignment
  #   self.iaModule = IntegralAssignment(self)
  #   spectrumDisplay.module.layout.addWidget(self.iaModule, 2, 0, 1, 4)
  #   if self.blankDisplay:
  #     self.blankDisplay.setParent(None)
  #     self.blankDisplay = None


  # def showPeakAssigmentModule(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   spectrumDisplay = self.createSpectrumDisplay(self._project.spectra[0])
  #   from ccpn.AnalysisMetabolomics.PeakAssignment import PeakAssignment
  #   PeakAssignment(spectrumDisplay.module, self._project, grid=(2, 0), gridSpan=(1, 4))
  #   if self.blankDisplay:
  #     self.blankDisplay.setParent(None)
  #     self.blankDisplay = None


  # def showParassignSetup(self):
  #   try:
  #     from ccpn.plugins.PARAssign.PARAssignSetup import ParassignSetup
  #     self.ps = ParassignSetup(project=self.project)
  #     newModule = CcpnModule(name='PARAssign Setup')
  #     newModule.addWidget(self.ps)
  #     self.moduleArea.addModule(newModule)
  #   except ImportError:
  #     print('PARAssign cannot be found')


  # def toggleConsole(self):
  #   """
  #   Toggles whether python console is displayed at bottom of the main window.
  #   """
  #
  #   if 'PYTHON CONSOLE' in self.moduleArea.findAll()[1]:
  #     if self.pythonConsoleModule.isVisible():
  #       self.pythonConsoleModule.hide()
  #     else:
  #       self.moduleArea.moveModule(self.pythonConsoleModule, 'bottom', None)
  #   else:
  #     self.pythonConsoleModule = CcpnModule(name='Python Console')
  #     self.pythonConsoleModule.layout.addWidget(self.pythonConsole)
  #     self.moduleArea.addModule(self.pythonConsoleModule, 'bottom')


  # def showMacroEditor(self):
  #   """
  #   Displays macro editor.
  #   """
  #   editor = MacroEditor(self.moduleArea, self, "Macro Editor")

  # def newMacroFromConsole(self):
  #   """
  #   Displays macro editor with contents of python console inside.
  #   """
  #   editor = MacroEditor(self.moduleArea, self, "Macro Editor")
  #   editor.textBox.setText(self.pythonConsole.textEditor.toPlainText())

  def newMacroFromLog(self):
    """
    Displays macro editor with contents of the log.
    """
    editor = MacroEditor(self.moduleArea, self, "Macro Editor")
    l = open(self.project._logger.logPath, 'r').readlines()
    text = ''.join([line.strip().split(':', 6)[-1]+'\n' for line in l])
    editor.textBox.setText(text)

  # def startMacroRecord(self):
  #   """
  #   Displays macro editor with additional buttons for recording a macro.
  #   """
  #   self.macroEditor = MacroEditor(self.moduleArea, self, "Macro Editor", showRecordButtons=True)
  #   self.pythonConsole.writeConsoleCommand("application.startMacroRecord()")
  #   self.project._logger.info("application.startMacroRecord()")


  # def defineUserShortcuts(self):
  #   info = MessageDialog.showInfo('Not implemented yet!',
  #         'This function has not been implemented in the current version',
  #         colourScheme=self.colourScheme)


  # def showNotesEditor(self):
  #   if self._appBase.ui.mainWindow is not None:
  #     mainWindow = self._appBase.ui.mainWindow
  #   else:
  #     mainWindow = self._appBase._mainWindow
  #   self.notesEditor = NotesEditor(mainWindow.moduleArea, self._project, name='Notes Editor')


  # def showCommandHelp(self):
  #   info = MessageDialog.showInfo('Not implemented yet!',
  #         'This function has not been implemented in the current version',
  #         colourScheme=self.colourScheme)


  # def showBeginnersTutorial(self):
  #   path = os.path.join(Path.getTopDirectory(), 'data', 'testProjects', 'CcpnSec5BBTutorial', 'BeginnersTutorial.pdf')
  #   if 'linux' in sys.platform.lower():
  #     os.system("xdg-open %s" % path)
  #   else:
  #     os.system('open %s' % path)

  # def showBackboneTutorial(self):
  #   path = os.path.join(Path.getTopDirectory(), 'data', 'testProjects', 'CcpnSec5BBTutorial', 'BackboneAssignmentTutorial.pdf')
  #   if 'linux' in sys.platform.lower():
  #     os.system("xdg-open %s" % path)
  #   else:
  #     os.system('open %s' % path)

  # def showAboutPopup(self):
  #   from ccpn.ui.gui.popups.AboutPopup import AboutPopup
  #   popup = AboutPopup()
  #   popup.exec_()
  #   popup.raise_()


  # def showAboutCcpnPopup(self):
  #   import webbrowser
  #   webbrowser.open('http://www.ccpn.ac.uk')


  # def showCodeInspectionPopup(self):
  #   info = MessageDialog.showInfo('Not implemented yet!',
  #         'This function has not been implemented in the current version',
  #         colourScheme=self.colourScheme)


  # def showUpdatePopup(self):
  #   if not self.updatePopup:
  #     self.updatePopup = UpdatePopup(self)
  #   self.updatePopup.show()
  #   self.updatePopup.raise_()


  # def showFeedbackPopup(self):
  #   if not self.feedbackPopup:
  #     self.feedbackPopup = FeedbackPopup(self)
  #   self.feedbackPopup.show()
  #   self.feedbackPopup.raise_()


  def runMacro(self, macroFile:str=None):
    """
    Runs a macro if a macro is specified, or opens a dialog box for selection of a macro file and then
    runs the selected macro.
    """
    if macroFile is None:
      macroFile = QtGui.QFileDialog.getOpenFileName(self, "Run Macro", self._appBase.preferences.general.macroPath)
    self.application.preferences.recentMacros.append(macroFile)
    self._fillRecentMacrosMenu()
    self.pythonConsole._runMacro(macroFile)


  # def showPeakTable(self, position:str='left', relativeTo:CcpnModule=None, selectedList:PeakList=None):
  #   """
  #   Displays Peak table on left of main window with specified list selected.
  #   """
  #   peakList = PeakTable(self._project, selectedList=selectedList)
  #   self.moduleArea.addModule(peakList, position=position, relativeTo=relativeTo)
  #   self.pythonConsole.writeConsoleCommand("application.showPeakTable()")
  #   self.project._logger.info("application.showPeakTable()")


  # def showChemicalShiftTable(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   """
  #   Displays Chemical Shift table.
  #   """
  #   from ccpn.ui.gui.modules.ChemicalShiftTable import NmrAtomShiftTable as Table
  #   chemicalShiftTable = Table(chemicalShiftLists=self._project.chemicalShiftLists)
  #   self.moduleArea.addModule(chemicalShiftTable, position=position, relativeTo=relativeTo)
  #   self.pythonConsole.writeConsoleCommand("application.showChemicalShiftTable()")
  #   self.project._logger.info("application.showChemicalShiftTable()")


  # def showAtomSelector(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   """Displays Atom Selector."""
  #   self.atomSelector = AtomSelector(self, project=self._project)
  #   self.moduleArea.addModule(self.atomSelector, position=position, relativeTo=relativeTo)
  #   self.pythonConsole.writeConsoleCommand("application.showAtomSelector()")
  #   self.project._logger.info("application.showAtomSelector()")
  #   return self.atomSelector


  # def showDataPlottingModule(self, position:str='bottom', relativeTo:CcpnModule=None):
  #   dpModule = DataPlottingModule(self.moduleArea, position=position, relativeTo=relativeTo)


  # def saveProject(self):
  #   """Opens save Project as dialog box if project has not been saved before, otherwise saves
  #   project with existing project name."""
  #   apiProject = self._project._wrappedData.root
  #   if hasattr(apiProject, '_temporaryDirectory'):
  #     # self.saveProjectAs()
  #     # Replaced by equivalent application function
  #     self._appBase.saveProjectAs()
  #   else:
  #     self._appBase.saveProject()
    

  # def saveProjectAs(self):
  #   """Opens save Project as dialog box and saves project with name specified in the file dialog."""
  #   # Imported here to avoid risk of circular imports.
  #   from ccpn.application import Framework
  #   # TODO try to refactor this
  #   newPath = Framework.getSaveDirectory()
  #   if newPath:
  #     # Next line unnecessary, but does no harm
  #     newProjectPath = apiIo.addCcpnDirectorySuffix(newPath)
  #     #self._appBase.saveProject(newPath=newProjectPath, newProjectName=os.path.basename(newPath),
  #     # createFallback=False)
  #     self._appBase.saveProject(newPath=newProjectPath, createFallback=False)


  # def printToFile(self, spectrumDisplay=None):
  #   current = self._appBase.current
  #   if not spectrumDisplay:
  #     spectrumDisplay = current.spectrumDisplay
  #   if not spectrumDisplay and current.strip:
  #     spectrumDisplay = current.strip.spectrumDisplay
  #   if not spectrumDisplay and self.spectrumDisplays:
  #     spectrumDisplay = self.spectrumDisplays[0]
  #   if spectrumDisplay:
  #     path = QtGui.QFileDialog.getSaveFileName(self, caption='Print to File', filter='SVG (*.svg)')
  #     if not path:
  #       return
  #     spectrumDisplay.printToFile(path)

  def _resetRemoveStripAction(self, strips):
    for spectrumDisplay in self.spectrumDisplays:
      spectrumDisplay._resetRemoveStripAction()
