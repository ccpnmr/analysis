#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-05-16 17:45:50 +0100 (Mon, 16 May 2016) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Luca Mureddu, Simon P Skinner & Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license "
              "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: TJ Ragan $"
__date__ = "$Date: 2016-05-16 17:45:50 +0100 (Mon, 16 May 2016) $"
__version__ = "$Revision: 9320 $"

#=========================================================================================
# Start of code
#=========================================================================================

import json
import os
import platform
import sys
from functools import partial

from ccpnmodel.ccpncore.api.memops import Implementation
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil

from ccpn.core.Project import Project
from ccpn.core._implementation import Io as coreIo
from ccpn.core.lib.Version import applicationVersion
from ccpn.core.PeakList import PeakList

from ccpn.util import Path
from ccpn.util import Register
from ccpn.util.AttrDict import AttrDict
from ccpn.util.Common import uniquify

from ccpn.framework.lib import SvnRevision

from ccpn.framework.Translation import languages, defaultLanguage
from ccpn.framework.Translation import translator

from ccpn.ui import interfaces, defaultInterface
from ccpn.ui.gui.Current import Current
from ccpn.ui.gui.modules.MacroEditor import MacroEditor
from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.Action import Action

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QKeySequence

_DEBUG = True

componentNames = ('Assignment', 'Screening', 'Structure')

interfaceNames = ('NoUi', 'Gui')

def printCreditsText(fp, programName, version):
  """Initial text to terminal """

  lines = []
  lines.append("%s, version: %s" % (programName, version))
  lines.append("")
  lines.append(__copyright__[0:__copyright__.index('-')] + '- 2016')
  lines.append(__license__)
  lines.append("Not to be distributed without prior consent!")
  lines.append("")
  lines.append("Written by: %s" % __credits__)

  # print with aligning '|'s
  maxlen = max(map(len,lines))
  fp.write('%s\n' % ('=' * (maxlen+8)))
  for line in lines:
    fp.write('|   %s ' % line + ' ' * (maxlen-len(line)) + '  |\n')
  fp.write('%s\n' % ('=' * (maxlen+8)))


def defineProgramArguments():
  """Define the arguments of the program
  return argparse instance
  """
  import argparse
  parser = argparse.ArgumentParser(description='Process startup arguments')
  for component in componentNames:
    parser.add_argument('--'+component.lower(), dest='include'+component, action='store_true',
                                                help='Show %s component' % component.lower())
  parser.add_argument('--language',
                      help=('Language for menus, etc.; valid options = (%s); default=%s' %
                            ('|'.join(languages) ,defaultLanguage)),
                      default=defaultLanguage)
  parser.add_argument('--interface',
                      help=('User interface, to use; one of  = (%s); default=%s' %
                            ('|'.join(interfaces) ,defaultInterface)),
                      default=defaultInterface)
  parser.add_argument('--skip-user-preferences', dest='skipUserPreferences', action='store_true',
                                                 help='Skip loading user preferences')
  parser.add_argument('--nologging', dest='nologging', action='store_true', help='Do not log information to a file')
  parser.add_argument('projectPath', nargs='?', help='Project path')

  return parser

class Arguments:
  """Class for setting FrameWork input arguments directly"""
  language = defaultLanguage
  interface = 'NoUi'
  nologging = True
  skipUserPreferences = True
  projectPath = None

  def __init__(self, projectPath=None, **kw):

    # Dummy values
    for component in componentNames:
      setattr(self, 'include' + component, None)

    self.projectPath = projectPath
    for tag, val in kw.items():
      setattr(self, tag, val)

def getFramework(projectPath=None, **kw):

  args = Arguments(projectPath=projectPath, **kw)
  result = Framework('CcpNmr', applicationVersion, args)
  result.start()
  #
  return result



class Framework:
  """
  The Framework class is the base class for all applications
  It's currently broken, so don't use this if you want your application to actually work!
  """


  def __init__(self, applicationName, applicationVersion, args):

    self.args = args
    self.applicationName = applicationName
    self.applicationVersion = applicationVersion
    self.revision = SvnRevision.revision()

    printCreditsText(sys.stderr, applicationName, applicationVersion)

    self.setupComponents(args)

    self.useFileLogger = not self.args.nologging

    self.current = None

    self.preferences = None
    self.styleSheet = None

    # Necessary as attribute is queried during initialisation:
    self._mainWindow = None

    # This is needed to make project available in NoUi (if nothing else)
    self.project = None

    # Blocking level for command echo and logging
    self._echoBlocking = 0

    # NBNB TODO The following block should maybe be moved into _getUi
    self._getUserPrefs()
    self._registrationDict = {}   # Default - overridden elsewhere
    self._setLanguage()
    self.styleSheet = self.getStyleSheet(self.preferences)
    self.ui = self._getUI()
    self._setupMenus()
    self.feedbackPopup = None
    self.updatePopup = None
    self.backupPopup = None


  def start(self):
    """Start the program execution"""

    # Load / create project
    projectPath = self.args.projectPath
    if projectPath:
      project = self.loadProject(projectPath)

    else:
      project = self.newProject()

    sys.stderr.write('==> Done, %s is starting\n' % self.applicationName)

    # TODO: Add back in registration ???

    # self.project = project
    self.ui.start()

    project._resetUndo(debug=_DEBUG)


  def _initialiseProject(self, project: Project):
    """Initialise project and set up links and objects that involve it"""

    self.project = project

    # Pass an instance of framework to project so the UI instantiation can happen
    project._appBase = self

    # Set up current
    self.current = Current(project=project)

    # This wraps the underlying data, including the wrapped graphics data
    #  - the project is now ready to use
    project._initialiseProject()

    # Adapt project to preferences
    self.applyPreferences(project)

    self.project = project
    self.ui.initialize(self._mainWindow)

    # Get the mainWindow out of the framework once it's been transferred to ui
    del self._mainWindow


  def _getUI(self):
    if self.args.interface == 'Gui':
      from ccpn.ui.gui.Gui import Gui
      ui = Gui(self)
    else:
      from ccpn.ui.Ui import NoUi
      ui = NoUi(self)

    # Connect UI classes for chosen ui
    ui.setUp()

    return ui


  def getStyleSheet(self, preferences=None):
    if preferences is None:
      preferences = self.preferences

    colourScheme = preferences.general.colourScheme
    colourScheme = metaUtil.upperFirst(colourScheme)

    styleSheet = open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                                   '%sStyleSheet.qss' % colourScheme)).read()
    if platform.system() == 'Linux':
      additions = open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                                    '%sAdditionsLinux.qss' % colourScheme)).read()
      styleSheet += additions
    return styleSheet


  def setupComponents(self, args):
    # components (for menus)
    self.components = set()
    for component in componentNames:
      if getattr(args, 'include' + component):
        self.components.add(component)


  def _getUserPrefs(self):
    # user preferences
    if not self.args.skipUserPreferences:
      sys.stderr.write('==> Getting user preferences\n')
    self.preferences = getPreferences(self.args.skipUserPreferences)


  def _setLanguage(self):
    # Language, check for command line override, or use preferences
    if self.args.language:
      language = self.args.language
    else:
      language = self.preferences.general.language
    if not translator.setLanguage(language):
      self.preferences.general.language = language
    # translator.setDebug(True)
    sys.stderr.write('==> Language set to "%s"\n' % translator._language)


  def _isRegistered(self):
    """return True if registered"""
    self._registrationDict = Register.loadDict()
    return not Register.isNewRegistration(self._registrationDict)


  def register(self):
    """
    Display registration popup if there is a gui
    return True on error
    """
    if self.ui is None:
        return True

    popup = RegisterPopup(version=self.applicationVersion, modal=True)
    popup.show()
    popup.raise_()
    popup.exec_()
    self.gui.processEvents()

    if not self._isRegistered():
      return True

    Register.updateServer(self._registrationDict, self.applicationVersion)
    return False


  def applyPreferences(self, project):
    """Apply user preferences

    NBNB project should be impliclt rather than a parameter (once reorganisation is finished)
    """
    # Reset remoteData DataStores to match preferences setting
    dataPath = self.preferences.general.dataPath
    if not dataPath or not os.path.isdir(dataPath):
      dataPath = os.path.expanduser('~')
    memopsRoot = project._wrappedData.root
    dataUrl = memopsRoot.findFirstDataLocationStore(name='standard').findFirstDataUrl(
      name='remoteData'
    )
    dataUrl.url = Implementation.Url(path=dataPath)


  def initGraphics(self):
    """Set up graphics system after loading - to be overridden in subclasses"""
    # for window in self.project.windows:
    #   window.initGraphics()
    pass


  def getByPid(self, pid):
    return self.project.getByPid(pid)

  def _startCommandBlock(self, command:str, **objectParameters):
    """Start block for command echoing, set undo waypoint, and echo command to ui and logger

    MUST be paired with _endCommandBlock call - use try ... finally to ensure both are called

    Set keyword:value objectParameters to point to the relevant objects in setup commands,
    and pass setup commands and command proper to ui for echoing

    Example calls:

    _startCommandBlock("application.createSpectrumDisplay(spectrum)", spectrum=spectrumOrPid)

    _startCommandBlock(
       "newAssignment = peak.assignDimension(axisCode=%s, value=[newNmrAtom]" % axisCode,
       peak=peakOrPid)"""

    undo = self.project._undo
    if not self._echoBlocking and not undo.blocking:

      # set undo step
      undo.newWaypoint()

      # Get list of command strings
      commands = []
      for parameter, value in sorted(objectParameters.items()):
        if not isinstance(value, str):
          value = value.longPid
        commands.append("%s = project.getByPid(%s)\n" % (parameter, repr(value)))
      commands.append(command)

      # echo command strings
      self.ui.echoCommands(commands)

    self._echoBlocking += 1


  def _endCommandBlock(self):
    """End block for command echoing,

    MUST be paired with _startCommandBlock call - use try ... finally to ensure both are called"""
    if self._echoBlocking > 0:
      self._echoBlocking -= 1

  def addApplicationMenuSpec(self, spec, position=3):
    self._menuSpec.insert(position, spec)


  #########################################    Start setup Menus      ############################

  def _setupMenus(self):
    self._menuSpec = ms = []
      # TODO: remove QKeySequence



    ms.append(('Project',   [
                            ("New", self.newProject, [('shortcut', 'pn')]),
                            ("Open...", self.loadProject, [('shortcut', 'po')]),
                            ("Open Recent",self._recentProjectsMenuItems()),

                            ("Load Spectrum", lambda: self.loadData(text='Load Spectrum'), [('shortcut', 'ls')]),
                            ("Load Data", self.loadData, [('shortcut', 'ld')]),
                            (),
                            ("Save", self.saveProject, [('shortcut', 'ps')]),
                            ("Save As...", self.saveProjectAs, [('shortcut', 'sa')]),
                            (),
                            ("Undo", self.undo, [('shortcut', QKeySequence("Ctrl+z"))]),
                            ("Redo", self.redo, [('shortcut', QKeySequence("Ctrl+y"))]),
                            (),
                            ("Summary", self.displayProjectSummary),
                            ("Archive", self.archiveProject),
                            ("Backup...", self.showBackupPopup),
                            (),
                            ("Preferences", self.showApplicationPreferences),
                            (),
                            ("Close Program", self._closeEvent, [('shortcut', 'qt')]),
                            ]
             ))

    ms.append(('Spectrum',  [
                            ("Spectrum Groups...", self.showSpectrumGroupsPopup, [('shortcut', 'ss')]),
                            ("Set Experiment Types...", self.showExperimentTypePopup, [('shortcut', 'et')]),
                            (),
                            ("Pick Peaks...", self.showPeakPickPopup, [('shortcut', 'pp')]),
                            ("Integration", self.showIntegrationModule, [('shortcut', 'it')]),
                            (),
                            ("Make Projection...", self.showProjectionPopup, [('shortcut', 'pj')]),
                            ("Phasing Console", self.togglePhaseConsole, [('shortcut', 'pc')])
                            ]
             ))

    ms.append(('Molecules', [
                            ("Create Molecule...", self.showMoleculePopup),
                            ("Show Sequence", self.toggleSequenceModule, [('shortcut', 'sq'),
                                                                          ('checkable', True),
                                                                          ('checked', False)
                                                                          ]),
                             ("Inspect...", self.inspectMolecule),
                             (),
                             ("Reference Chemical Shifts", self.showRefChemicalShifts,[('shortcut', 'rc')]),
                            ]
             ))

    ms.append(('View',      [
                            ("New Blank Display", self.addBlankDisplay, [('shortcut', 'nd')]),
                            (),
                            ("Chemical Shift Table", self.showChemicalShiftTable, [('shortcut', 'ct')]),
                            ("NmrResidue Table", self.showNmrResidueTable, [('shortcut', 'nt')]),
                            ("Peak Table", self.showPeakTable, [('shortcut', 'lt')]),
                            (),
                            ("Sequence Graph", self.showSequenceGraph, [('shortcut', 'sg')]),
                            ("Atom Selector", self.showAtomSelector, [('shortcut', 'as')]),
                            (),
                            ("Console", self.toggleConsole, [('shortcut', 'py'),
                                                            ('checkable', True),
                                                            ('checked', False)])
                            ]
             ))

    ms.append(('Macro',     [
                            ("Edit...", self.showMacroEditor),
                            ("New from Console...", self.newMacroFromConsole),
                            ("New from Log...", self.newMacroFromLog),
                            (),
                            ("Record Macro...", self.startMacroRecord),
                            ("Run...", self.runMacro, [('shortcut', 'rm')]),
                            ("Run Recent", self._fillRecentMacrosMenu())
                            ]
             ))

    ms.append(('Plugins',   [
                            ("PARAssign Setup", self.showParassignSetup, [('shortcut', 'q1')]),
                            ]
             ))

    ms.append(('Help',      [
                            ("Command...", self.showCommandHelp, [('shortcut', 'ss')]),
                            ("Tutorials",([
                                    # Submenu
                                    ("Beginners Tutorial", self.showBeginnersTutorial),
                                    ("Backbone Tutorial", self.showBackboneTutorial)
                                    ])),
                            ("Show Shortcuts", self.showShortcuts),
                            ("Show CcpNmr V3 Documentation", self.showWrapperDocumentation),
                            ("Show API Documentation", self._showApiDocumentation),
                            (),
                            ("About CcpNmr V3...", self.showAboutPopup),
                            ("About CCPN...", self.showAboutCcpnPopup),
                            (),
                            ("Inspect Code...", self.showCodeInspectionPopup),
                            ("Check for Updates...", self.showUpdatePopup),
                            ("Submit Feedback...", self.showFeedbackPopup)
                          ]
             ))


  ###################################################################################################################
  ## MENU callbacks:  Project
  ###################################################################################################################

  def newProject(self, name='default'):
    # """Create new, empty project"""

    # NB _closeProject includes a gui cleanup call

    if self.project is not None:
      self._closeProject()

    sys.stderr.write('==> Creating new, empty project\n')
    project = coreIo.newProject(name=name)

    self._initialiseProject(project)

    project._resetUndo(debug=_DEBUG)

    return project

  def loadProject(self, path=None):
    """
       Load project from path
       If not path then opens a file dialog box and loads project from selected file.
    """
    from ccpn.ui.gui.widgets.FileDialog import FileDialog

    if self.project is not None:
      self._closeProject()

    if not path:
      dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.Directory, text='Load Project', preferences=self.preferences.general)
      paths = dialog.selectedFiles()
      if paths:
        path = paths[0]

    if not path:
      return

    sys.stderr.write('==> Loading "%s" project\n' % path)
    project = coreIo.loadProject(path)

    self._initialiseProject(project)

    project._resetUndo(debug=_DEBUG)

    return project

  def _recentProjectsMenuItems(self):
    """
    Populates recent projects menu with 10 most recently loaded projects
    specified in the preferences file.
    """
    l = []
    for recentFile in self.preferences.recentFiles:
      if (recentFile.startswith('/var/') is False):
        l.append((recentFile, partial(self.loadProject, recentFile), (('translate', False),)))

    return l

  def clearRecentProjectsMenu(self):
    # self.recentProjectsMenu.clear()
    self.preferences.recentFiles = []
    self._recentProjectsMenuItems()


  def loadData(self, paths=None, text=None):
    """
    Opens a file dialog box and loads data from selected file.
    """
    from ccpn.ui.gui.widgets.FileDialog import FileDialog

    if text is None:
      text = 'Load Data'
    if paths is None:
      dialog = FileDialog(parent=self.ui.mainWindow, fileMode=0, text=text, preferences=self.preferences.general)
      paths = dialog.selectedFiles()[0]

    # NBNB TBD I assume here that path is either a string or a list lf string paths.
    # NBNB FIXME if incorrect

    if not paths:
      return
    elif isinstance(paths, str):
      paths = [paths]

    self.ui.mainWindow.processDropData(paths, dataType='urls')

  def saveProject(self, newPath=None, newProjectName=None, createFallback=True):
    # TODO: convert this to a save and call self.project.save()
    pass
    apiIo.saveProject(self.project._wrappedData.root, newPath=newPath, newProjectName=newProjectName,
                      createFallback=createFallback)
    self.ui.mainWindow._updateWindowTitle()
    
    layout = self.ui.mainWindow.moduleArea.saveState()
    layoutPath = os.path.join(self.project.path, 'layouts')
    if not os.path.exists(layoutPath):
      os.makedirs(layoutPath)
    import yaml
    with open(os.path.join(layoutPath, "layout.yaml"), 'w') as stream:
      yaml.dump(layout, stream)
      stream.close()
    saveIconPath = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'), 'icons', 'save.png')

    sys.stderr.write('==> Project successfully saved\n')
    # MessageDialog.showMessage('Project saved', 'Project successfully saved!',
    #                           colourScheme=self.preferences.general.colourScheme, iconPath=saveIconPath)

  def saveProjectAs(self):
    """Opens save Project as dialog box and saves project with name specified in the file dialog."""
    from ccpn.ui.gui import AppBase  # has to be here because of circular import
    apiProject = self.ui.mainWindow._wrappedData.root
    newPath = AppBase.getSaveDirectory(apiProject, self.preferences)
    if newPath:
      newProjectPath = apiIo.ccpnProjectPath(newPath)
      self.saveProject(newPath=newProjectPath, newProjectName=os.path.basename(newPath),
                                createFallback=False)

  def saveBackup(self):
    pass

  def restoreBackup(self):
    pass

  def undo(self):
    self.project._undo.undo()

  def redo(self):
    self.project._undo.redo()

  def saveLogFile(self):
    pass

  def clearLogFile(self):
    pass

  def displayProjectSummary(self):
    info = MessageDialog.showInfo('Not implemented yet',
                                  'This function has not been implemented in the current version',
                                  colourScheme=self.ui.mainWindow.colourScheme)

  def archiveProject(self):
    import datetime
    project = self.project
    apiProject = project._wrappedData.parent
    projectPath = project.path
    now = datetime.datetime.now().strftime('%y%m%d%H%M%S')
    filePrefix = '%s_%s' % (os.path.basename(projectPath), now)
    filePrefix = os.path.join(os.path.dirname(projectPath), filePrefix)
    fileName = apiIo.packageProject(apiProject, filePrefix, includeBackups=True, includeLogs=True)

    MessageDialog.showInfo('Project Archived',
                           'Project archived to %s' % fileName, colourScheme=self.ui.mainWindow.colourScheme)

  def showBackupPopup(self):
    from ccpn.ui.gui.popups.BackupPopup import BackupPopup

    if not self.backupPopup:
      self.backupPopup = BackupPopup(parent=self.ui.mainWindow)
    self.backupPopup.show()
    self.backupPopup.raise_()

  def showApplicationPreferences(self):
    """
    Displays Application Preferences Popup.
    """
    from ccpn.ui.gui.popups.PreferencesPopup import PreferencesPopup

    PreferencesPopup(preferences=self.preferences, project=self.project).exec_()

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
        self.project._logger.warning('Preferences not saved: %s' % (directory, e))
        return

    prefFile = open(prefPath, 'w+')
    json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
    prefFile.close()

    reply = MessageDialog.showMulti("Quit Program", "Do you want to save changes before quitting?",
                                    ['Save and Quit', 'Quit without Saving', 'Cancel'],
                                    colourScheme=self.ui.mainWindow.colourScheme)
    if reply == 'Save and Quit':
      if event:
        event.accept()
      prefFile = open(prefPath, 'w+')
      json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
      prefFile.close()
      self.saveProject()
      # Close and clean up project
      self._closeProject()
      QtGui.QApplication.quit()
    elif reply == 'Quit without Saving':
      if event:
        event.accept()
      prefFile = open(prefPath, 'w+')
      json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
      prefFile.close()
      self._closeProject()
      QtGui.QApplication.quit()
    else:
      if event:
        event.ignore()

  def _closeProject(self):
    """Close project and clean up - when opening another or quitting application"""

    # NB: this function must clan up both wrapper and ui/gui

    if self.project is not None:
      # Cleans up wrapper project, including graphics data objects (Window, Strip, etc.)
      self.project._close()
      self.project = None
    if self.ui.mainWindow:
      # ui/gui cleanup
      self.ui.mainWindow.deleteLater()
    self.ui.mainWindow = None
    self.current = None
    self.project = None

  ###################################################################################################################
  ## MENU callbacks:  Spectrum
  ###################################################################################################################

  def showSpectrumGroupsPopup(self):
    from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
    SpectrumGroupEditor(parent=self.ui.mainWindow, project=self.project).exec_()

  def showProjectionPopup(self):
    pass

  def showExperimentTypePopup(self):
    """
    Displays experiment type popup.
    """
    from ccpn.ui.gui.popups.ExperimentTypePopup import ExperimentTypePopup
    popup = ExperimentTypePopup(self.ui.mainWindow, self.project)
    popup.exec_()

  def showPeakPickPopup(self):
    """
    Displays Peak Picking Popup.
    """
    from ccpn.ui.gui.popups.PeakFind import PeakFindPopup
    popup = PeakFindPopup(parent=self.ui.mainWindow, project=self.project)
    popup.exec_()

  def showIntegrationModule(self, position:str='bottom', relativeTo:CcpnModule=None):
    spectrumDisplay = self.ui.mainWindow.createSpectrumDisplay(self.project.spectra[0])
    from ccpn.AnalysisMetabolomics.Integration import IntegrationTable, IntegrationWidget
    spectrumDisplay.integrationWidget = IntegrationWidget(spectrumDisplay.module,
                                                          project=self.project, grid=(2, 0), gridSpan=(1, 4))
    spectrumDisplay.integrationTable = IntegrationTable(spectrumDisplay.module,
                                                        project=self.project, grid=(0, 4), gridSpan=(3, 1))
    self.current.strip = spectrumDisplay.strips[0]
    if self.ui.mainWindow.blankDisplay:
      self.ui.mainWindow.blankDisplay.setParent(None)
      self.ui.mainWindow.blankDisplay = None

  def togglePhaseConsole(self):
    self.ui.mainWindow.togglePhaseConsole(self.ui.mainWindow)


  ###################################################################################################################
  ## MENU callbacks:  Molecule
  ###################################################################################################################


  def showMoleculePopup(self):
    """
    Displays sequence creation popup.
    """
    from ccpn.ui.gui.modules.CreateSequence import CreateSequence
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showMoleculePopup()")
    self.project._logger.info("application.showMoleculePopup()")
    popup = CreateSequence(self.ui.mainWindow, project=self.project).exec_()

  def toggleSequenceModule(self):
    """Toggles whether Sequence Module is displayed or not"""
    if hasattr(self, 'sequenceModule'):
      if self.sequenceModule.isVisible():
        self.hideSequenceModule()
    else:
      self.showSequenceModule()
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.toggleSequenceModule()")
    self.project._logger.info("application.toggleSequenceModule()")

  def showSequenceModule(self, position='top', relativeTo=None):
    """
    Displays Sequence Module at the top of the screen.
    """
    from ccpn.ui.gui.modules.SequenceModule import SequenceModule

    self.sequenceModule = SequenceModule(self.project)
    self.ui.mainWindow.moduleArea.addModule(self.sequenceModule,
                                            position=position, relativeTo=relativeTo)
    return self.sequenceModule

  def hideSequenceModule(self):
    """Hides sequence module"""
    self.sequenceModule.close()
    delattr(self, 'sequenceModule')

  def inspectMolecule(self):
    from ccpn.ui.gui.widgets import MessageDialog
    info = MessageDialog.showInfo('Not implemented yet!',
                                  'This function has not been implemented in the current version',
                                  colourScheme=self.ui.mainWindow.colourScheme)

  def showRefChemicalShifts(self):
    """Displays Reference Chemical Shifts module."""
    from ccpn.ui.gui.modules.ReferenceChemicalShifts import ReferenceChemicalShifts
    self.refChemShifts = ReferenceChemicalShifts(self.project, self.ui.mainWindow.moduleArea)



  ###################################################################################################################
  ## MENU callbacks:  VIEW
  ###################################################################################################################

  def addBlankDisplay(self, position='right', relativeTo=None):
    from ccpn.ui.gui.modules.GuiBlankDisplay import GuiBlankDisplay

    if 'BLANK DISPLAY' in self.ui.mainWindow.moduleArea.findAll()[1]:
      blankDisplay = self.ui.mainWindow.moduleArea.findAll()[1]['BLANK DISPLAY']
      if blankDisplay.isVisible():
        return
      else:
        self.ui.mainWindow.moduleArea.moveModule(blankDisplay, position, None)
    else:
      self.blankDisplay = GuiBlankDisplay(self.ui.mainWindow.moduleArea)
      self.ui.mainWindow.moduleArea.addModule(self.blankDisplay, position, None)

    self.pythonConsole.writeConsoleCommand(("application.addBlankDisplay()"))
    self.project._logger.info("application.addBlankDisplay()")

  def showChemicalShiftTable(self, position:str='bottom', relativeTo:CcpnModule=None):
    """
    Displays Chemical Shift table.
    """
    from ccpn.ui.gui.modules.ChemicalShiftTable import NmrAtomShiftTable as Table
    chemicalShiftTable = Table(chemicalShiftLists=self.project.chemicalShiftLists)
    self.ui.mainWindow.moduleArea.addModule(chemicalShiftTable, position=position, relativeTo=relativeTo)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showChemicalShiftTable()")
    self.project._logger.info("application.showChemicalShiftTable()")

  def showNmrResidueTable(self, position='bottom', relativeTo=None):
    """Displays Nmr Residue Table"""
    from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTable
    nmrResidueTable = NmrResidueTable(self.ui.mainWindow, self.project)
    nmrResidueTableModule = CcpnModule(name='Nmr Residue Table')
    nmrResidueTableModule.layout.addWidget(nmrResidueTable)
    self.ui.mainWindow.moduleArea.addModule(nmrResidueTableModule, position=position, relativeTo=relativeTo)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showNmrResidueTable()")
    self.project._logger.info("application.showNmrResidueTable()")

  def showPeakTable(self, position:str='left', relativeTo:CcpnModule=None, selectedList:PeakList=None):
    """
    Displays Peak table on left of main window with specified list selected.
    """
    from ccpn.ui.gui.modules.PeakTable import PeakTable

    peakList = PeakTable(self.project, selectedList=selectedList)
    self.ui.mainWindow.moduleArea.addModule(peakList, position=position, relativeTo=relativeTo)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showPeakTable()")
    self.project._logger.info("application.showPeakTable()")

  def showSequenceGraph(self, position:str='bottom', relativeTo:CcpnModule=None):
    """
    Displays assigner at the bottom of the screen, relative to another module if nextTo is specified.
    """
    from ccpn.Assign.modules.SequenceGraph import SequenceGraph
    self.assigner = SequenceGraph(self, project=self.project)
    if hasattr(self, 'bbModule'):
      self.bbModule._connectSequenceGraph(self.assigner)

    if relativeTo is not None:
      self.ui.mainWindow.moduleArea.addModule(self.assigner, position=position, relativeTo=relativeTo)
    else:
      self.ui.mainWindow.moduleArea.addModule(self.assigner, position=position)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showSequenceGraph()")
    self.project._logger.info("application.showSequenceGraph()")
    return self.assigner

  def showAtomSelector(self, position:str='bottom', relativeTo:CcpnModule=None):
    """Displays Atom Selector."""
    from ccpn.Assign.modules.AtomSelector import AtomSelector
    self.atomSelector = AtomSelector(parent=self.ui.mainWindow, project=self.project)
    self.ui.mainWindow.moduleArea.addModule(self.atomSelector, position=position, relativeTo=relativeTo)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showAtomSelector()")
    self.project._logger.info("application.showAtomSelector()")
    return self.atomSelector


  def toggleConsole(self):
    """
    Toggles whether python console is displayed at bottom of the main window.
    """

    if 'PYTHON CONSOLE' in self.ui.mainWindow.moduleArea.findAll()[1]:
      if self.ui.mainWindow.pythonConsoleModule.isVisible():
        self.ui.mainWindow.pythonConsoleModule.hide()
      else:
        self.ui.mainWindow.moduleArea.moveModule(self.ui.mainWindow.pythonConsoleModule, 'bottom', None)
    else:
      self.ui.mainWindow.pythonConsoleModule = CcpnModule(name='Python Console')
      self.ui.mainWindow.pythonConsoleModule.layout.addWidget(self.ui.mainWindow.pythonConsole)
      self.ui.mainWindow.moduleArea.addModule(self.ui.mainWindow.pythonConsoleModule, 'bottom')


  ##################################################################################################################
  ## MENU callbacks:  Plugins
  ###################################################################################################################

  def showParassignSetup(self):
    try:
      from ccpn.plugins.PARAssign.PARAssignSetup import ParassignSetup
      self.ps = ParassignSetup(project=self.project)
      newModule = CcpnModule(name='PARAssign Setup')
      newModule.addWidget(self.ps)
      self.ui.mainWindow.moduleArea.addModule(newModule)
    except ImportError:
      print('PARAssign cannot be found')



  ###################################################################################################################
  ## MENU callbacks:  Macro
  ###################################################################################################################

  def showMacroEditor(self):
    """
    Displays macro editor.
    """
    editor = MacroEditor(self.ui.mainWindow.moduleArea, self.ui.mainWindow, "Macro Editor")

  def newMacroFromConsole(self):
    """
    Displays macro editor with contents of python console inside.
    """
    editor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor")
    editor.textBox.setText(self.pythonConsole.textEditor.toPlainText())

  def newMacroFromLog(self):
    """
    Displays macro editor with contents of the log.
    """
    editor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor")
    l = open(self.project._logger.logPath, 'r').readlines()
    text = ''.join([line.strip().split(':', 6)[-1] + '\n' for line in l])
    editor.textBox.setText(text)

  def startMacroRecord(self):
    """
    Displays macro editor with additional buttons for recording a macro.
    """
    self.macroEditor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor", showRecordButtons=True)
    self.pythonConsole.writeConsoleCommand("application.startMacroRecord()")
    self.project._logger.info("application.startMacroRecord()")

  def _fillRecentMacrosMenu(self):
    """
    Populates recent macros menu with last ten macros ran.
    """

    recentMacros = uniquify(self.preferences.recentMacros)
    l = []
    for recentMacro in self.preferences.recentMacros:
      if recentMacro:
        l.append((recentMacro, partial(self.runMacro, recentMacro)))
    return l

    # translator.setSilent()
    # for recentMacro in recentMacros:
    #   self.action = Action(parent=self.ui.mainWindow, text=recentMacro, callback=partial(self.runMacro, macroFile=recentMacro))
    #   self.recentMacrosMenu.addAction(self.action)
    # translator.setLoud()
    # self.recentMacrosMenu.addAction(Action(parent=self.ui.mainWindow, text='Clear', callback=self.clearRecentMacros))

  def clearRecentMacros(self):
    # self.recentMacrosMenu.clear()
    self.preferences.recentMacros = []

  def defineUserShortcuts(self):
    info = MessageDialog.showInfo('Not implemented yet!',
                                  'This function has not been implemented in the current version',
                                  colourScheme=self.ui.mainWindow.colourScheme)

  def runMacro(self, macroFile: str = None):
    """
    Runs a macro if a macro is specified, or opens a dialog box for selection of a macro file and then
    runs the selected macro.
    """
    if macroFile is None:
      macroFile = QtGui.QFileDialog.getOpenFileName(self.ui.mainWindow, "Run Macro", self.preferences.general.macroPath)
    self.preferences.recentMacros.append(macroFile)
    # self._fillRecentMacrosMenu()
    self.pythonConsole._runMacro(macroFile)



  ###################################################################################################################
  ## MENU callbacks:  Help
  ###################################################################################################################



  def showCommandHelp(self):
    info = MessageDialog.showInfo('Not implemented yet!',
                                  'This function has not been implemented in the current version',
                                  colourScheme=self.ui.mainWindow.colourScheme)

  def showBeginnersTutorial(self):
    path = os.path.join(Path.getTopDirectory(), 'data', 'testProjects', 'CcpnSec5BBTutorial', 'BeginnersTutorial.pdf')
    if 'linux' in sys.platform.lower():
      os.system("xdg-open %s" % path)
    else:
      os.system('open %s' % path)

  def showBackboneTutorial(self):
    path = os.path.join(Path.getTopDirectory(), 'data', 'testProjects', 'CcpnSec5BBTutorial',
                        'BackboneAssignmentTutorial.pdf')
    if 'linux' in sys.platform.lower():
      os.system("xdg-open %s" % path)
    else:
      os.system('open %s' % path)

  def _showApiDocumentation(self):
    """Displays API documentation in a module."""
    self._showDocumentation("API Documentation", 'apidoc', 'api.html')

  def showWrapperDocumentation(self):
    """Displays CCPN wrapper documentation in a module."""
    self._showDocumentation("CCPN Documentation", 'build', 'html', 'index.html')

  def _showDocumentation(self, title, *args):
    from ccpn.ui.gui.widgets.CcpnWebView import CcpnWebView

    newModule = CcpnModule("API Documentation")
    path = os.path.join(Path.getTopDirectory(), 'doc', *args)
    view = CcpnWebView(path)
    newModule.addWidget(view)
    self.ui.mainWindow.moduleArea.addModule(newModule)

  def showShortcuts(self):
    path = os.path.join(Path.getTopDirectory(), 'doc', 'static', 'AnalysisShortcuts.pdf')
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
                                  colourScheme=self.ui.mainWindow.colourScheme)

  def showUpdatePopup(self):
    from ccpn.framework.update.UpdatePopup import UpdatePopup

    if not self.updatePopup:
      self.updatePopup = UpdatePopup(parent=self.ui.mainWindow)
    self.updatePopup.show()
    self.updatePopup.raise_()

  def showFeedbackPopup(self):
    from ccpn.ui.gui.popups.FeedbackPopup import FeedbackPopup

    if not self.feedbackPopup:
      self.feedbackPopup = FeedbackPopup(parent=self.ui.mainWindow)
    self.feedbackPopup.show()
    self.feedbackPopup.raise_()



  #########################################    End Menu callbacks   ##################################################

  def printToFile(self, spectrumDisplay=None):

    current = self.current
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


########

def getPreferences(skipUserPreferences=False, defaultPreferencesPath=None,
                   userPreferencesPath=None):

  def _readPreferencesFile(preferencesPath):
    fp = open(preferencesPath)
    preferences = json.load(fp, object_hook=AttrDict) ##TBD find a better way ?!?
    fp.close()
    return preferences

  def _updateDict(d, u):
    import collections
    # recursive update of dictionary
    # this deletes every key in u that is not in d
    # if we want every key regardless, then remove first if check below
    for k, v in u.items():
      if k not in d:
        continue
      if isinstance(v, collections.Mapping):
        r = _updateDict(d.get(k, {}), v)
        d[k] = r
      else:
        d[k] = u[k]
    return d

  preferencesPath = (defaultPreferencesPath if defaultPreferencesPath else
                     os.path.join(Path.getTopDirectory(), 'config', 'defaultv3settings.json'))
  preferences = _readPreferencesFile(preferencesPath)

  if not skipUserPreferences:
    preferencesPath = userPreferencesPath if userPreferencesPath else os.path.expanduser('~/.ccpn/v3settings.json')
    if os.path.exists(preferencesPath):
      _updateDict(preferences, _readPreferencesFile(preferencesPath))

  return preferences
