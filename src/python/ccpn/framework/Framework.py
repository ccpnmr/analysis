#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2016-05-16 17:45:50 +0100 (Mon, 16 May 2016) $"
__credits__   = "Wayne Boucher, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan, Simon P Skinner & Geerten W Vuister"
__license__   = "CCPN license. See www.ccpn.ac.uk/license"
__reference__ = "Skinner et al, J. Biomol. NMR, 2016, submitted"

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
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil

from ccpn.core.Project import Project
from ccpn.core._implementation import Io as coreIo
from ccpn.core.lib import CcpnNefIo
from ccpn.core.lib.Version import applicationVersion
from ccpn.core.PeakList import PeakList

from ccpn.util import Path
from ccpn.util import Register
from ccpn.util.AttrDict import AttrDict

from ccpn.core.lib import Version

from ccpn.framework.Translation import languages, defaultLanguage
from ccpn.framework.Translation import translator
from ccpn.framework.lib.misc import _checked

from ccpn.ui import interfaces, defaultInterface
from ccpn.framework.Current import Current
from ccpn.ui.gui.modules.MacroEditor import MacroEditor
from ccpn.ui.gui.widgets.Module import CcpnModule
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.lib.Window import MODULE_DICT
from ccpn.util.Common import uniquify

from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QKeySequence

_DEBUG = False

componentNames = ('Assignment', 'Screening', 'Structure')

interfaceNames = ('NoUi', 'Gui')


def printCreditsText(fp, programName, version):
  """Initial text to terminal """

  lines = []
  lines.append("%s, version: %s" % (programName, version))
  lines.append("")
  lines.append("%s" % __copyright__[0:__copyright__.index('-')] + '- 2016')
  lines.append("%s. Not to be distributed without prior consent!" % __license__)
  lines.append("")
  lines.append("Written by:   %s" % __credits__)
  lines.append("")
  lines.append("Please cite:  %s" % __reference__)
  lines.append("")
  lines.append("DISCLAIMER:   This program is offered 'as-is'. Under no circumstances will the authors, CCPN,")
  lines.append("              the Department of Molecular and Cell Biology, or the University of Leicester be")
  lines.append("              liable of any damage, loss of data, loss of revenue or any other undesired")
  lines.append("              consequences originating from the usage of this software.")

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
  # for component in componentNames:
  #   parser.add_argument('--'+component.lower(), dest='include'+component, action='store_true',
  #                                               help='Show %s component' % component.lower())
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
  The Framework class is the base class for all applications.
  """

  def __init__(self, applicationName, applicationVersion, args):

    self.args = args
    self.applicationName = applicationName
    self.applicationVersion = applicationVersion
    self.revision = Version.revision

    printCreditsText(sys.stderr, applicationName, applicationVersion)

    # self.setupComponents(args)

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

    # NEF reader
    self.nefReader = CcpnNefIo.CcpnNefReader(self)

    # NBNB TODO The following block should maybe be moved into _getUi
    self._getUserPrefs()
    self._registrationDict = {}
    self._setLanguage()
    self.styleSheet = self.getStyleSheet(self.preferences)
    self.ui = self._getUI()
    self.setupMenus()
    self.feedbackPopup = None
    self.submitMacroPopup = None
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

    if not self._checkRegistration():
      return

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
    if hasattr(self, '_mainWindow'):
      self.ui.initialize(self._mainWindow)

      # Get the mainWindow out of the application top level once it's been transferred to ui
      del self._mainWindow
    else:
      # The NoUi version has no mainWindow
      self.ui.initialize(None)


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


  # def setupComponents(self, args):
  #   # components (for menus)
  #   self.components = set()
  #   for component in componentNames:
  #     if getattr(args, 'include' + component):
  #       self.components.add(component)
  #
  #
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


  def _checkRegistration(self):
    """
    Display registration popup if there is a gui
    return True if ok
    return False on error
    """
    from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup

    if self.ui:
      if not self._isRegistered():
        popup = RegisterPopup(self.ui.mainWindow, version=self.applicationVersion, modal=True)
        popup.show()
        popup.raise_()
        popup.exec_()

    if not self._isRegistered():
      return False

    Register.updateServer(self._registrationDict, self.applicationVersion)
    return True

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
    """Set up graphics system after loading"""
    from ccpn.ui.gui.lib.Window import MODULE_DICT
    from ccpn.ui.gui.modules import GuiStrip

    project = self.project

    # Initialise displays
    for spectrumDisplay in project.windows[0].spectrumDisplays: # there is exactly one window
      spectrumDisplay._resetRemoveStripAction()

    # Initialise strips
    for strip in project.strips:
      GuiStrip._setupGuiStrip(project, strip._wrappedData)

      # if isinstance(strip, GuiStripNd) and not strip.haveSetupZWidgets:
      #   strip.setZWidgets()

    # Initialise Rulers
    for task in project.tasks:
      for apiMark in task._wrappedData.sortedMarks():
        for apiRuler in apiMark.sortedRulers():
          GuiStrip._rulerCreated(project, apiRuler)

    # Initialise SpectrumViews
    for spectrumDisplay in project.spectrumDisplays:
      for strip in spectrumDisplay.strips:
        for spectrumView in strip.spectrumViews:
          spectrumView._createdSpectrumView()
          for peakList in spectrumView.spectrum.peakLists:
            strip.showPeaks(peakList)

    self._initLayout()

  def _initLayout(self):
    """
    Restore layout of modules from previous save after graphics have been set up.
    """
    import yaml, os
    if os.path.exists(os.path.join(self.project.path, 'layouts', 'layout.yaml')):
      with open(os.path.join(self.project.path, 'layouts', 'layout.yaml')) as f:
        layout = yaml.load(f)
        typ, contents, state = layout['main']

        # TODO: When UI has a main window, change the call below (then move the whole function!)
        containers, modules = self.ui.mainWindow.moduleArea.findAll()
        flatten = lambda *n: (e for a in n
        for e in (flatten(*a) if isinstance(a, (tuple, list)) else (a,)))
        flatContents = list(flatten(contents))
        for item in flatContents:
          if item in list(MODULE_DICT.keys()):
            obj = modules.get(item)
            if not obj:
             func = getattr(self, MODULE_DICT[item])
             func()
        for s in layout['float']:
          typ, contents, state = s[0]['main']
          containers, modules = self.ui.mainWindow.moduleArea.findAll()
          for item in contents:
            if item[0] == 'dock':
              obj = modules.get(item[1])
              if not obj:
                func = getattr(self, MODULE_DICT[item[1]])
                func()
        self.ui.mainWindow.moduleArea.restoreState(layout)


  def getByPid(self, pid):
    return self.project.getByPid(pid)


  def getByGid(self, gid):
    return self.ui.getByGid(gid)


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
      self.project.suspendNotification()

      # Get list of command strings
      commands = []
      for parameter, value in sorted(objectParameters.items()):
        if not isinstance(value, str):
          value = value.pid
        commands.append("%s = project.getByPid(%s)\n" % (parameter, repr(value)))
      commands.append(command)

      # echo command strings
      self.ui.echoCommands(commands)

    self._echoBlocking += 1
    self.project._logger.debug('startCommandBlock. command=%s, echoBlocking=%s, undo.blocking=%s'
                               % (command, self._echoBlocking, undo.blocking))


  def _endCommandBlock(self):
    """End block for command echoing,

    MUST be paired with _startCommandBlock call - use try ... finally to ensure both are called"""

    self.project._logger.debug('endCommandBlock. echoBlocking=%s' % self._echoBlocking)

    if self._echoBlocking > 0:
      # If statement should always be True, but to avoid weird behaviour in error situations we check
      self._echoBlocking -= 1
    self.project.resumeNotification()

  def addApplicationMenuSpec(self, spec, position=3):
    self._menuSpec.insert(position, spec)


  #########################################    Start setup Menus      ############################

  def setupMenus(self):
    '''
    Setup the menu specification.

    The menus are specified by a list of lists (actually, an iterable of iterables, but the term
    ‘list’ will be used here to mean any iterable).  Framework provides 7 menus: Project, Spectrum,
    Molecules, View, Macro, Plugins, Help.  If you want to create your own menu in a subclass of
    Framework, you need to create a list in the style described below, then call
    self.addApplicationMenuSpec and pass in your menu specification list.

    Menu specification lists are composed of two items, the first being a string which is the menu’s
    title, the second is a list of sub-menu items.  Each item can be zero, two or three items long.
    A zero-length list indicates a separator.  If the list is length two and the second item is a
    list, then it specifies a sub-menu in a recursive manner.  If the list is length two and the second
    item is callable, it specifies a menu action with the first item specifying the label and the second
    the callable that is triggered when the menu item is selected.  If the list is length three, it is
    treated as a menu item specification, with the third item a list of keyword, value pairs.

    The examples below may make this more clear…

    Create a menu called ‘Test’ with two items and a separator:

    | - Test
        |- Item One
        |- ------
        |- Item Two

    Where clicking on ‘Item One’ calls method self.itemOneMethod and clicking on ‘Item Two’
    calls self.itemTwoMethod

        def setupMenus(self):
          menuSpec = (‘Test’, [(‘Item One’, self.itemOneMethod),
                               (),
                               (‘Item Two’, self.itemTwoMethod),
                              ]
          self.addApplicationMenuSpec(menuSpec)

    
    More complicated menus are possible.  For example, to create the following menu

    | - Test
        |- Item A     ia
        |- ------
        |- Submenu B
           |- Item B1
           |- Item B2
        |- Item C     id

    where Item A can be activated using the two-key shortcut ‘ia’,
    Submenu B contains two static menu items, B1 and B2
    Submenu item B2 is checkable, but not checked by default
    Item C is disabled by default and has a shortcut of ‘ic’

        def setupMenus(self):
          subMenuSpecB = [(‘Item B1’, self.itemB1),
                          (‘Item B2’, self.itemB2, [(‘checkable’, True),
                                                    (‘checked’, False)])
                         ]

          menuSpec = (‘Test’, [(‘Item A’, self.itemA, [(‘shortcut’, ‘ia’)]),
                               (),
                               (‘Submenu B’, subMenuB),
                               (‘Item C’, self.itemA, [(‘shortcut’, ‘ic’),
                                                       (‘enabled’, False)]),
                              ]
          self.addApplicationMenuSpec(menuSpec)


    If we’re using the PyQt GUI, we can get the Qt action representing Item B2 somewhere in our code
    (for example, to change the checked status,) via:

        action = application.ui.mainWindow.getMenuAction(‘Test->Submenu B->Item B2’)
        action.setChecked(True)

    To see how to add items dynamically, see clearRecentProjects in this class and
    _fillRecentProjectsMenu in GuiMainWindow

    '''
    self._menuSpec = ms = []
    # TODO: remove QKeySequence

    ms.append(('Project',   [
      ("New", self.createNewProject, [('shortcut', 'pn')]),
      ("Open...", self.openProject, [('shortcut', 'po')]),
      ("Open Recent", ()),

#      ("Load Spectrum...", lambda: self.loadData(text='Load Spectrum'), [('shortcut', 'ls')]),
      ("Load Data...", self.loadData, [('shortcut', 'ld')]),
      (),
      ("Save", self.saveProject, [('shortcut', 'ps')]),
      ("Save As...", self.saveProjectAs, [('shortcut', 'sa')]),
      (),
      ("Undo", self.undo, [('shortcut', QKeySequence("Ctrl+z"))]),
      ("Redo", self.redo, [('shortcut', QKeySequence("Ctrl+y"))]),
      (),
      ("Summary", self.displayProjectSummary, [('enabled', False)]),
      ("Archive", self.archiveProject, [('enabled', True)]),
      ("Backup...", self.showBackupPopup, [('enabled', False)]),
      (),
      ("Preferences...", self.showApplicationPreferences),
      (),
      ("Close Program", self._closeEvent, [('shortcut', 'qt')]),
    ]
               ))

    ms.append(('Spectrum',  [
      ("Load Spectrum...", lambda: self.loadData(text='Load Spectrum'), [('shortcut', 'ls')]),
      (),
      ("Spectrum Groups...", self.showSpectrumGroupsPopup, [('shortcut', 'ss')]),
      ("Set Experiment Types...", self.showExperimentTypePopup, [('shortcut', 'et')]),
      (),
      ("Pick Peaks...", self.showPeakPickPopup, [('shortcut', 'pp')]),
      ("Integration", self.showIntegrationModule, [('shortcut', 'it'),
                                                   ('enabled', False)]),
      (),
      ("Make Projection...", self.showProjectionPopup, [('shortcut', 'pj'),
                                                        ('enabled', False)]),
    ]
               ))

    ms.append(('Molecules', [
      ("Create Molecule...", self.showMoleculePopup),
      ("Show Sequence", self.toggleSequenceModule, [('shortcut', 'sq'),
                                                    ('checkable', True),
                                                    ('checked', False)
                                                    ]),
      ("Inspect...", self.inspectMolecule, [('enabled', False)]),
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
      ("Current", (("Show/Hide Toolbar", self.toggleToolbar, [('shortcut', 'tb')]),
                   ("Show/Hide Phasing Console", self.togglePhaseConsole, [('shortcut', 'pc')])
                  )),
      (),
      ("Python Console", self.toggleConsole, [('shortcut', 'py'),
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
      ("Run Recent", ()),
      (),
      ("Define Shortcut...", self.defineShortcut, [('enabled', False)])
    ]
               ))

    # ms.append(('Plugins',   [
    #   ("PARAssign Setup", self.showParassignSetup, [('shortcut', 'q1')]),
    # ]
    #            ))
    ms.append(('Plugins',   self.getPluginMenuItems()))

    ms.append(('Help',      [
      ("Command...", self.showCommandHelp, [('enabled', False)]),
      ("Tutorials",([
        # Submenu
        ("Beginners Tutorial", self.showBeginnersTutorial),
        ("Backbone Tutorial", self.showBackboneTutorial)
      ])),
      ("Show Shortcuts", self.showShortcuts),
      ("Show CcpNmr V3 Documentation", self.showVersion3Documentation),
      (),
      ("About CcpNmr V3...", self.showAboutPopup),
      ("About CCPN...", self.showAboutCcpn),
      ("Show License...", self.showCcpnLicense),
      (),
      ("Inspect Code...", self.showCodeInspectionPopup,[('enabled', False)]),
      ("Show Issues...", self.showIssuesList),
      ("Check for Updates...", self.showUpdatePopup),
      (),
      ("Submit Feedback...", self.showFeedbackPopup),
      ("Submit Macro...", self.showSubmitMacroPopup)
    ]
               ))


  ###################################################################################################################
  ## These will eventually move to gui (probably via a set of lambda functions.
  ###################################################################################################################
  ###################################################################################################################
  ## MENU callbacks:  Project
  ###################################################################################################################


  def createNewProject(self):
    okToContinue = self.ui.mainWindow._queryCloseProject(title='New Project',
                                                         phrase='create a new')
    if okToContinue:
      self.newProject()


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


  def openProject(self, path=None):
    return self.ui.mainWindow.loadProject(projectDir=path)


  def loadProject(self, path=None):
    """
       Load project from path
       If not path then opens a file dialog box and loads project from selected file.
    """

    if not path:
      dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.Directory, text='Load Project',
                          acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general)
      path = dialog.selectedFile()
      if not path:
        return

    dataType, subType, usePath = ioFormats.analyseUrl(path)
    if dataType == 'Project' and subType in (ioFormats.CCPN, ioFormats.NEF):

      if self.project is not None:
        self._closeProject()

      if subType == ioFormats.CCPN:
        sys.stderr.write('==> Loading %s project "%s"\n' % (subType, path))
        project = coreIo.loadProject(path)
        project._resetUndo(debug=_DEBUG)
        self._initialiseProject(project)
      elif subType == ioFormats.NEF:
        sys.stderr.write('==> Loading %s project (Experimental Only!) "%s"\n' % (subType, path))
        project = self._loafNefFile(path)
        project._resetUndo(debug=_DEBUG)
      #
      return project

    else:
      sys.stderr.write('==> Could not recognise "%s" as a project\n' % path)

  def _loafNefFile(self, path:str) -> Project:
    """Load Project from NEF file at path, and do necessary setup"""

    mainWindow = None
    if hasattr(self.ui, 'mainWindow'):
      mainWindow = self.ui.mainWindow

    if mainWindow is not None:
      sys.stderr.write("==> NEF file loading not yet implemented for Gui interface. Aborting...")
      return

    dataBlock = self.nefReader.getNefData(path)
    project = self.newProject(dataBlock.name)
    self._echoBlocking += 1
    self.project._undo.increaseBlocking()
    try:
      self.nefReader.importNewProject(project, dataBlock)
    finally:
      self._echoBlocking -= 1
      self.project._undo.decreaseBlocking()

    if mainWindow is not None:
      # TODO initialisation does not work properly. Needs fixing.
      mainWindow.sideBar.fillSideBar(project)
    #
    return project

  def clearRecentProjects(self):
    self.preferences.recentFiles = []
    self.ui.mainWindow._fillRecentProjectsMenu()


  def clearRecentMacros(self):
    self.preferences.recentMacros = []
    self.ui.mainWindow._fillRecentMacrosMenu()


  def loadData(self, paths=None, text=None):
    """
    Opens a file dialog box and loads data from selected file.
    """
    if text is None:
      text = 'Load Data'

    if paths is None:
      dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.AnyFile, text=text,
                          acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general)
      path = dialog.selectedFile()
      if not path:
        return
      paths = [path]

    elif isinstance(paths, str):
      paths = [paths]

    self.ui.mainWindow.processDropData(paths, dataType='urls')

  def saveProject(self, newPath=None, createFallback=True, overwriteExisting=True) -> bool:
    """Save project to newPath and return True if successful"""
    # TODO: convert this to a save and call self.project.save()
    successful = self.project.save(newPath=newPath, createFallback=createFallback, overwriteExisting=overwriteExisting)
    if not successful:
      sys.stderr.write('==> Project save failed\n')

      # NBNB TODO Gui should pre-check newPath and/or pop up something in case of failure

    self.ui.mainWindow._updateWindowTitle()
    self._updateRecentFiles()

    layout = self.ui.mainWindow.moduleArea.saveState()
    layoutPath = os.path.join(self.project.path, 'layouts')
    if not os.path.exists(layoutPath):
      os.makedirs(layoutPath)
    import yaml
    with open(os.path.join(layoutPath, "layout.yaml"), 'w') as stream:
      yaml.dump(layout, stream)
      stream.close()
    # saveIconPath = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'), 'icons', 'save.png')

    sys.stderr.write('==> Project successfully saved\n')
    # MessageDialog.showMessage('Project saved', 'Project successfully saved!',
    #                           colourScheme=self.preferences.general.colourScheme, iconPath=saveIconPath)

    return successful


  def _updateRecentFiles(self, oldPath=None):
    project = self.project
    path = project.path
    recentFiles = self.preferences.recentFiles
    mainWindow = self.ui.mainWindow or self._mainWindow

    if not hasattr(project._wrappedData.root, '_temporaryDirectory'):
      if path in recentFiles:
        recentFiles.remove(path)
      elif oldPath in recentFiles:
        recentFiles.remove(oldPath)
      elif len(recentFiles) >= 10:
        recentFiles.pop()
      recentFiles.insert(0, path)
    recentFiles = uniquify(recentFiles)
    mainWindow._fillRecentProjectsMenu()
    self.preferences.recentFiles = recentFiles


  def saveProjectAs(self):
    """Opens save Project as dialog box and saves project to path specified in the file dialog."""
    oldPath = self.project.path
    newPath = getSaveDirectory(self.preferences.general)
    if newPath:
      # Next line unnecessary, but does not hurt
      newProjectPath = apiIo.addCcpnDirectorySuffix(newPath)
      successful = self.saveProject(newPath=newProjectPath, createFallback=False)

      if not successful:
        self.project._logger.warning("Saving project to %s aborted" % newProjectPath)
    else:
      successful = False
      self.project._logger.info("Project not saved - no valid destination selected")

    self._updateRecentFiles(oldPath=oldPath)

    return successful

    # NBNB TODO Consider appropriate failure handling. Is this OK?

  def saveBackup(self):
    pass

  def restoreBackup(self):
    pass

  def undo(self):
    self.ui.echoCommands(['application.undo()'])
    self._echoBlocking += 1
    self.project._undo.undo()
    self._echoBlocking -= 1

  def redo(self):
    self.ui.echoCommands(['application.redo()'])
    self._echoBlocking += 1
    self.project._undo.redo()
    self._echoBlocking -= 1

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
    SpectrumGroupEditor(parent=self.ui.mainWindow, project=self.project, editorMode=True).exec_()

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
    popup = PeakFindPopup(parent=self.ui.mainWindow, project=self.project, current=self.current)
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

    self.ui.mainWindow.pythonConsole.writeConsoleCommand(("application.addBlankDisplay()"))
    self.project._logger.info("application.addBlankDisplay()")

  def showChemicalShiftTable(self, position:str='bottom', relativeTo:CcpnModule=None):
    """
    Displays Chemical Shift table.
    """
    if not self.project.chemicalShiftLists:
      self.project._logger.warn('Project has no Chemical Shift Lists. Chemical Shift Table cannot be displayed')
      MessageDialog.showWarning('Project has no Chemical Shift Lists.', 'Chemical Shift Table cannot be displayed', colourScheme=self.preferences.general.colourScheme)
      return
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
    if not self.project.peakLists:
      self.project._logger.warn('Project has no Peak Lists. Peak table cannot be displayed')
      MessageDialog.showWarning('Project has no Peak Lists.', 'Peak table cannot be displayed', colourScheme=self.preferences.general.colourScheme)
      return
    peakList = PeakTable(self.project, selectedList=selectedList)
    self.ui.mainWindow.moduleArea.addModule(peakList, position=position, relativeTo=relativeTo)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showPeakTable()")
    self.project._logger.info("application.showPeakTable()")

  def showSequenceGraph(self, position:str='bottom', relativeTo:CcpnModule=None):
    """
    Displays assigner at the bottom of the screen, relative to another module if nextTo is specified.
    """
    from ccpn.AnalysisAssign.modules.SequenceGraph import SequenceGraph

    if hasattr(self, 'assigner'):
      return

    self.assigner = SequenceGraph(self, project=self.project)
    if hasattr(self, 'backboneModule'):
      self.backboneModule._connectSequenceGraph(self.assigner)

    if relativeTo is not None:
      self.ui.mainWindow.moduleArea.addModule(self.assigner, position=position, relativeTo=relativeTo)
    else:
      self.ui.mainWindow.moduleArea.addModule(self.assigner, position=position)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showSequenceGraph()")
    self.project._logger.info("application.showSequenceGraph()")
    return self.assigner

  def showAtomSelector(self, position:str='bottom', relativeTo:CcpnModule=None):
    """Displays Atom Selector."""
    from ccpn.AnalysisAssign.modules.AtomSelector import AtomSelector
    self.atomSelector = AtomSelector(parent=self.ui.mainWindow, project=self.project)
    self.ui.mainWindow.moduleArea.addModule(self.atomSelector, position=position, relativeTo=relativeTo)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showAtomSelector()")
    self.project._logger.info("application.showAtomSelector()")
    return self.atomSelector

  def toggleToolbar(self):
    if self.current.strip is not None:
      self.current.strip.spectrumDisplay.toggleToolbar()

  def togglePhaseConsole(self):
    if self.current.strip is not None:
      self.current.strip.spectrumDisplay.togglePhaseConsole()

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

  def getPluginMenuItems(self):
    # TODO: move instantiation to plugin.  This is a HACK for now!!!
    menuItems = []

    try:
      from ccpn.plugins.PARAssign.PARAssignSetup import ParassignSetup
      menuItems = [("PARAssign Setup", self.showParassignSetup, [('shortcut', 'q1')])]
    except ImportError:
      menuItems = [("PARAssign Setup", self.showParassignSetup, [('shortcut', 'q1'),
                                                                 ('enabled', False)])]

    return menuItems

  def showParassignSetup(self):
    # try:
      from ccpn.plugins.PARAssign.PARAssignSetup import ParassignSetup
      self.ps = ParassignSetup(project=self.project)
      newModule = CcpnModule(name='PARAssign Setup')
      newModule.addWidget(self.ps)
      self.ui.mainWindow.moduleArea.addModule(newModule)
    # except ImportError:
    #   print('PARAssign cannot be found')



  ###################################################################################################################
  ## MENU callbacks:  Macro
  ###################################################################################################################

  def showMacroEditor(self):
    """
    Displays macro editor.
    """
    editor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor")

  def newMacroFromConsole(self):
    """
    Displays macro editor with contents of python console inside.
    """
    editor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor")
    editor.textBox.setText(self.ui.mainWindow.pythonConsole.textEditor.toPlainText())

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
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.startMacroRecord()")
    self.project._logger.info("application.startMacroRecord()")


  def defineUserShortcuts(self):
    info = MessageDialog.showInfo('Not implemented yet!',
                                  'This function has not been implemented in the current version',
                                  colourScheme=self.ui.mainWindow.colourScheme)

  def runMacro(self, macroFile:str=None):
    """
    Runs a macro if a macro is specified, or opens a dialog box for selection of a macro file and then
    runs the selected macro.
    """
    if macroFile is None:
      dialog = FileDialog(self.ui.mainWindow, fileMode=FileDialog.ExistingFile, text="Run Macro",
                          acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general,
                          directory=self.preferences.general.macroPath, filter='*.py')
      macroFile = dialog.selectedFile()
      if not macroFile:
        return

    if not macroFile in self.preferences.recentMacros:
      self.preferences.recentMacros.append(macroFile)
    # self._fillRecentMacrosMenu()
    self.ui.mainWindow.pythonConsole._runMacro(macroFile)

  def defineShortcut(self):
    info = MessageDialog.showInfo('Not implemented yet',
                                  'This function has not been implemented in the current version',
                                  colourScheme=self.ui.mainWindow.colourScheme)


  ###################################################################################################################
  ## MENU callbacks:  Help
  ###################################################################################################################



  def showCommandHelp(self):
    info = MessageDialog.showInfo('Not implemented yet!',
                                  'This function has not been implemented in the current version',
                                  colourScheme=self.ui.mainWindow.colourScheme)

  def _systemOpen(self, path):
    "Open path on system"
    if 'linux' in sys.platform.lower():
      os.system("xdg-open %s" % path)
    else:
      os.system('open %s' % path)

  def _showHtmlFile(self, title, path):
    "Displays html files in program QT viewer or using native webbrowser depending on useNativeWebbrowser option"

    if self.preferences.general.useNativeWebbrowser:
      self._systemOpen(path)
    else:
      from ccpn.ui.gui.widgets.CcpnWebView import CcpnWebView
      newModule = CcpnModule(title)
      view = CcpnWebView(path)
      newModule.addWidget(view)
      self.ui.mainWindow.moduleArea.addModule(newModule)

  def showBeginnersTutorial(self):
    from ccpn.framework.PathsAndUrls import beginnersTutorialPath
    self._systemOpen(beginnersTutorialPath)

  def showBackboneTutorial(self):
    from ccpn.framework.PathsAndUrls import backboneAssignmentTutorialPath
    self._systemOpen(backboneAssignmentTutorialPath)

  def showVersion3Documentation(self):
    """Displays CCPN wrapper documentation in a module."""
    from ccpn.framework.PathsAndUrls import documentationPath
    self._showHtmlFile("Analysis Version-3 Documentation", documentationPath)

  def showShortcuts(self):
    from ccpn.framework.PathsAndUrls import shortcutsPath
    self._systemOpen(shortcutsPath)

  def showAboutPopup(self):
    from ccpn.ui.gui.popups.AboutPopup import AboutPopup
    popup = AboutPopup()
    popup.exec_()
    popup.raise_()

  def showAboutCcpn(self):
    from ccpn.framework.PathsAndUrls import ccpnUrl
    import webbrowser
    webbrowser.open(ccpnUrl)

  def showCcpnLicense(self):
    from ccpn.framework.PathsAndUrls import ccpnLicenceUrl
    import webbrowser
    webbrowser.open(ccpnLicenceUrl)

  def showCodeInspectionPopup(self):
    info = MessageDialog.showInfo('Not implemented yet!',
                                  'This function has not been implemented in the current version',
                                  colourScheme=self.ui.mainWindow.colourScheme)

  def showIssuesList(self):
    from ccpn.framework.PathsAndUrls import ccpnIssuesUrl
    import webbrowser
    webbrowser.open(ccpnIssuesUrl)


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

  def showSubmitMacroPopup(self):
    from ccpn.ui.gui.popups.SubmitMacroPopup import SubmitMacroPopup

    if not self.submitMacroPopup:
      self.submitMacroPopup = SubmitMacroPopup(parent=self.ui.mainWindow)
    self.submitMacroPopup.show()
    self.submitMacroPopup.raise_()

  def showLicense(self):
    from ccpn.framework.PathsAndUrls import licensePath
    self._systemOpen(licensePath)


  #########################################    End Menu callbacks   ##################################################

  def printToFile(self, spectrumDisplay=None):

    current = self.current
    # if not spectrumDisplay:
    #   spectrumDisplay = current.spectrumDisplay
    if not spectrumDisplay and current.strip:
      spectrumDisplay = current.strip.spectrumDisplay
    if not spectrumDisplay and self.spectrumDisplays:
      spectrumDisplay = self.spectrumDisplays[0]
    if spectrumDisplay:
      dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.AnyFile, text='Print to File',
                          acceptMode=FileDialog.AcceptSave, preferences=self.preferences.general, filter='SVG (*.svg)')
      path = dialog.selectedFile()
      if not path:
        return
      spectrumDisplay.printToFile(path)

def getSaveDirectory(preferences=None):
  """Opens save Project as dialog box and gets directory specified in the file dialog."""

  dialog = FileDialog(fileMode=FileDialog.AnyFile, text='Save Project As',
                      acceptMode=FileDialog.AcceptSave, preferences=preferences)
  newPath = dialog.selectedFile()
  if not newPath:
    return
  if newPath:
    newPath = apiIo.addCcpnDirectorySuffix(newPath)
    if os.path.exists(newPath) and (os.path.isfile(newPath) or os.listdir(newPath)):
      # should not really need to check the second and third condition above, only
      # the Qt dialog stupidly insists a directory exists before you can select it
      # so if it exists but is empty then don't bother asking the question
      title = 'Overwrite path'
      msg = 'Path "%s" already exists, continue?' % newPath
      if not MessageDialog.showYesNo(title, msg, colourScheme=preferences.colourScheme):
        newPath = ''

    return newPath

########

def getPreferences(skipUserPreferences=False, defaultPath=None, userPath=None):

  def _readPreferencesFile(preferencesPath):
    fp = open(preferencesPath)
    preferences = json.load(fp, object_hook=AttrDict) #TODO find a better way ?!?
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

  # read the default settings
  from ccpn.framework.PathsAndUrls import defaultPreferencesPath
  preferencesPath = (defaultPath if defaultPath else defaultPreferencesPath)
  preferences = _readPreferencesFile(preferencesPath)

  # read user settings and update if not skipped
  if not skipUserPreferences:
    from ccpn.framework.PathsAndUrls import userPreferencesPath
    preferencesPath = (userPath if userPath else os.path.expanduser(userPreferencesPath))
    if os.path.exists(preferencesPath):
      _updateDict(preferences, _readPreferencesFile(preferencesPath))

  return preferences
