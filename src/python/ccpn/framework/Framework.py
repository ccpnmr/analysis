#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2017"
__credits__ = ("Wayne Boucher, Ed Brooksbank, Rasmus H Fogh, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpnLicense for licence text")
__reference__ = ("For publications, please use reference from http://www.ccpn.ac.uk/v3-software/downloads/license",
               "or ccpnmodel.ccpncore.memops.Credits.CcpNmrReference")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Wayne Boucher $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:36 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import json
import logging
import os
import platform
import sys
import tarfile
import tempfile

from PyQt4 import QtGui

from ccpn.core.IntegralList import IntegralList
from ccpn.core.PeakList import PeakList
from ccpn.core.Project import Project
from ccpn.core._implementation import Io as coreIo
from ccpn.core.lib import CcpnNefIo
from ccpn.framework import Version
from ccpn.framework.Current import Current
from ccpn.framework.Translation import languages, defaultLanguage
from ccpn.framework.Translation import translator
from ccpn.ui import interfaces, defaultInterface
from ccpn.ui.gui.lib.Window import MODULE_DICT
from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.modules.MacroEditor import MacroEditor
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.util import Logging
from ccpn.util import Path
from ccpn.util import Register
from ccpn.util.AttrDict import AttrDict
from ccpn.util.Common import uniquify
from ccpn.util.Logging import getLogger
from ccpn.util.Scripting import createScriptsDirectory, addScriptSubDirectory
from ccpnmodel.ccpncore.api.memops import Implementation
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil

# from functools import partial

_DEBUG = False

componentNames = ('Assignment', 'Screening', 'Structure')

interfaceNames = ('NoUi', 'Gui')


def printCreditsText(fp, programName, version):
  """Initial text to terminal """
  from ccpn.framework.PathsAndUrls import ccpnLicenceUrl

  lines = []                                                    # ejb
  lines.append("%s, version: %s" % (programName, version))
  lines.append("")
  # lines.append("%s" % __copyright__[0:__copyright__.index('-')] + '- 2016')
  lines.append("%s" % __copyright__)
  lines.append("")
  lines.append("CCPN licence. See %s. Not to be distributed without prior consent!" % ccpnLicenceUrl)
  lines.append("")

  try:
    if isinstance(__credits__, str):
      lines.append("Written by:   %s" % __credits__)
    else:
      if isinstance(__credits__, tuple):
        lines.append("Written by:   %s" % __credits__[0])
        for crLine in __credits__[1:]:
          lines.append("              %s" % crLine)
  except:
    pass

  lines.append("")
  try:
    if isinstance(__reference__, str):
      lines.append("Please cite:  %s" % __reference__)
    else:
      if isinstance(__reference__, tuple):
        lines.append("Please cite:  %s" % __reference__[0])
        for refLine in __reference__[1:]:
          lines.append("              %s" % refLine)
  except:
    pass

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
                            ('|'.join(languages), defaultLanguage)))
  parser.add_argument('--interface',
                      help=('User interface, to use; one of  = (%s); default=%s' %
                            ('|'.join(interfaces), defaultInterface)),
                      default=defaultInterface)
  parser.add_argument('--skip-user-preferences', dest='skipUserPreferences', action='store_true',
                                                 help='Skip loading user preferences')
  parser.add_argument('--dark', dest='darkColourScheme', action='store_true',
                                                 help='Use dark colour scheme')
  parser.add_argument('--light', dest='lightColourScheme', action='store_true',
                                                 help='Use dark colour scheme')
  parser.add_argument('--nologging', dest='nologging', action='store_true', help='Do not log information to a file')
  parser.add_argument('--debug', dest='debug', action='store_true', help='Set logging level to debug')
  parser.add_argument('--debug1', dest='debug', action='store_true', help='Set logging level to debug1 (=debug)')
  parser.add_argument('--debug2', dest='debug2', action='store_true', help='Set logging level to debug2')
  parser.add_argument('--debug3', dest='debug3', action='store_true', help='Set logging level to debug3')
  parser.add_argument('projectPath', nargs='?', help='Project path')

  return parser


class Arguments:
  """Class for setting FrameWork input arguments directly"""
  language = defaultLanguage
  interface = 'NoUi'
  nologging = True
  debug = False
  debug2 = False
  debug3 = False
  skipUserPreferences = True
  projectPath = None

  def __init__(self, projectPath=None, **kw):

    # Dummy values
    for component in componentNames:
      setattr(self, 'include' + component, None)

    self.projectPath = projectPath
    for tag, val in kw.items():
      setattr(self, tag, val)

def createFramework(projectPath=None, **kw):

  args = Arguments(projectPath=projectPath, **kw)
  result = Framework('CcpNmr', Version.applicationVersion, args)
  result.start()
  #
  return result



from threading import Thread
from time import time, sleep
class AutoBackup(Thread):

  def __init__(self, q, backupFunction, sleepTime=1):
    super().__init__()
    self.sleepTime = sleepTime
    self.q = q
    self.backupProject = backupFunction
    self.startTime = None


  def run(self):
    self.startTime = time()
    while True:
      if not self.q.empty():
        waitTime = self.q.get()
      if waitTime is None:
        sleep(self.sleepTime)
      elif waitTime == 'kill':
        return
      elif (time()-self.startTime) < waitTime:
        sleep(self.sleepTime)
      else:
        self.startTime = time()
        try:
          self.backupProject()
        except:
          pass



class Framework:
  """
  The Framework class is the base class for all applications.
  """

  def __init__(self, applicationName, applicationVersion, args=Arguments()):

    self.args = args
    self.applicationName = applicationName
    self.applicationVersion = applicationVersion
    self.revision = Version.revision
    self.plugins = []  # Hack for now, how should we store these?

    printCreditsText(sys.stderr, applicationName, applicationVersion)

    # self.setupComponents(args)

    self.useFileLogger = not self.args.nologging
    if self.args.debug3:
      self.level = Logging.DEBUG3
    elif self.args.debug2:
      self.level = Logging.DEBUG2
    elif self.args.debug:
      self.level = logging.DEBUG
    else:
      self.level = logging.INFO

    self.current      = None

    self.preferences  = None  # intialised by self._getUserPrefs
    self.styleSheet   = None  # intialised by self.getStyleSheet
    self.colourScheme = None  # intialised by self.getStyleSheet

    # Necessary as attribute is queried during initialisation:
    self._mainWindow  = None

    # This is needed to make project available in NoUi (if nothing else)
    self.project      = None

    # Blocking level for command echo and logging
    self._echoBlocking = 0

    # NEF reader
    self.nefReader = CcpnNefIo.CcpnNefReader(self)

    self._backupTimerQ    = None
    self.autoBackupThread = None

    # NBNB TODO The following block should maybe be moved into _getUi
    self._getUserPrefs()
    self._registrationDict = {}
    self._setLanguage()
    self.styleSheet = None
    self.ui = self._getUI()
    self.setupMenus()
    self.feedbackPopup = None
    self.submitMacroPopup = None
    self.updatePopup = None


  def _testShortcuts0(self):
    print('>>> Testing shortcuts0')

  def _testShortcuts1(self):
    print('>>> Testing shortcuts1')

  def start(self):
    """Start the program execution"""

    # Load / create project
    projectPath = self.args.projectPath
    if projectPath:
      project = self.loadProject(projectPath)

    else:
      project = self.newProject()

    self._updateCheckableMenuItems()

    if not self._checkRegistration():
      return

    # Needed in case project load failed
    if not project:
      sys.stderr.write('==> No project, aborting ...\n')
      return

    self.updateAutoBackup()

    sys.stderr.write('==> Done, %s is starting\n' % self.applicationName)

    # self.project = project
    self.ui.start()
    self._cleanup()

  def updateAutoBackup(self):

    if self.preferences.general.autoBackupEnabled:
      self.setAutoBackupTime(self.preferences.general.autoBackupFrequency)
    else:
      self.setAutoBackupTime(None)

  def setAutoBackupTime(self, time):
    # TODO: Need to add logging...
    if self._backupTimerQ is None:
      from queue import Queue
      self._backupTimerQ = Queue(maxsize=1)
    if self._backupTimerQ.full():
      self._backupTimerQ.get()
    if isinstance(time, (float, int)):
      self._backupTimerQ.put(time * 60)
    else:
      self._backupTimerQ.put(time)
    if self.autoBackupThread is None:
      self.autoBackupThread = AutoBackup(q=self._backupTimerQ,
                                         backupFunction=self.backupProject)
      self.autoBackupThread.start()


  def _cleanup(self):
    self.setAutoBackupTime('kill')
    # project._resetUndo(debug=_DEBUG)
    pass


  def backupProject(self):
    apiIo.backupProject(self.project._wrappedData.parent)


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

    # Add Scripts Folder
    createScriptsDirectory(project)
    addScriptSubDirectory(project, 'pymol')

    self.project = project
    if hasattr(self, '_mainWindow'):
      Logging.getLogger().debug('>>>framework._initialiseProject')
      self.ui.initialize(self._mainWindow)

      # Get the mainWindow out of the application top level once it's been transferred to ui
      del self._mainWindow
    else:
      # The NoUi version has no mainWindow
      self.ui.initialize(None)

  def _refreshAfterSave(self):
    """Refresh user interface after project save (which may have caused project rename)"""

    mainWindow = self.ui.mainWindow
    if mainWindow is not None:
      mainWindow.sideBar.setProjectName(self.project)

  def _getUI(self):
    if self.args.interface == 'Gui':
      self.styleSheet = self.getStyleSheet()
      from ccpn.ui.gui.Gui import Gui
      ui = Gui(self)
      ui.qtApp._ccpnApplication = self
      # ui.mainWindow is None upon initialization: gets filled later
      getLogger().debug('%s %s %s' % (self, ui, ui.mainWindow))
    else:
      from ccpn.ui.Ui import NoUi
      ui = NoUi(self)

    # Connect UI classes for chosen ui
    ui.setUp()

    return ui


  def getStyleSheet(self):
    """return Stylesheet as determined by arguments --dark, --light or preferences
    """
    colourScheme = None
    if self.args.darkColourScheme:
      colourScheme ='dark'
    elif self.args.lightColourScheme:
      colourScheme = 'light'
    else:
      colourScheme = self.preferences.general.colourScheme

    if colourScheme is None:
      raise RuntimeError('invalid colourScheme')

    self.colourScheme = colourScheme

    styleSheet = open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                                   '%sStyleSheet.qss' % metaUtil.upperFirst(colourScheme))).read()
    if platform.system() == 'Linux':
      additions = open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                                    '%sAdditionsLinux.qss' % metaUtil.upperFirst(colourScheme))).read()
      styleSheet += additions
    return styleSheet

  def _getUserPrefs(self):
    # user preferences
    if not self.args.skipUserPreferences:
      sys.stderr.write('==> Getting user preferences\n')
    self.preferences = getPreferences(self.args.skipUserPreferences)


  def _setLanguage(self):
    # Language, check for command line override, or use preferences
    if self.args.language:
      language = self.args.language
    elif self.preferences.general.language:
      language = self.preferences.general.language
    else:
      language = defaultLanguage
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
    from ccpn.ui.gui.modules import GuiStrip

    project = self.project

    # Initialise displays
    for spectrumDisplay in project.windows[0].spectrumDisplays: # there is exactly one window
      pass  # GWV: poor solution; removed the routine spectrumDisplay._resetRemoveStripAction()

    # Initialise strips
    for strip in project.strips:
      GuiStrip._setupGuiStrip(project, strip._wrappedData)

      # if isinstance(strip, GuiStripNd) and not strip.haveSetupZWidgets:
      #   strip.setZWidgets()

    # Initialise SpectrumViews
    for spectrumDisplay in project.spectrumDisplays:
      for strip in spectrumDisplay.strips:

        # TODO:ED use orderedSpectra
        # for spectrumView in strip.spectrumViews:

        for iSV, spectrumView in enumerate(spectrumDisplay.orderedSpectrumViews(includeDeleted=False)):
          spectrumView._createdSpectrumView(iSV)
          for peakList in spectrumView.spectrum.peakLists:
            strip.showPeaks(peakList)

    # add blank Display
    if len(self.ui.mainWindow.moduleArea.currentModulesNames) == 0:
      # self.ui.mainWindow.newBlankDisplay()

      self.addBlankDisplay()

    # FIXME: LM. Restore Layout
    # Restore Layout currently unstable. Unexpected bugs from pyqtgraph conteiners. Needs a better refactoring
    # self._initLayout()

  def _initLayout(self):
    """
    Restore layout of modules from previous save after graphics have been set up.
    """
    import yaml, os

    containers, modules = self.ui.mainWindow.moduleArea.findAll()
    keysSeen = set()

    # At this point, the spectrum windows (modules) have been created but not the other ones
    # These other ones have keys in MODULE_DICT
    # If the key is not in that dict then it is not needed, so remove
    # This means, for example, that Assign-specific modules are removed from Screen
    # If the key has already been seen then also remove
    # This is because PyQtGraph does not like duplicate keys when it restores the state
    # The code below assumes some knowledge of how PyQtGraph stores the state in terms of layout

    # Remaining problem: windows might be off screen

    def _analyseContents(contents):
      """function internal to _initLayout"""
      contentToRemove = []
      for content in contents:
        if isinstance(content, (tuple, list)):
          if content:
            if content[0] == 'dock':
              key = content[1]
              if key in keysSeen or not modules.get(key):  # if modules.get(key) then module exists already
                if key in keysSeen or key not in MODULE_DICT or not hasattr(self, MODULE_DICT[key]):
                  contentToRemove.append(content)
                else:
                  keysSeen.add(key)
                  func = getattr(self, MODULE_DICT[key])
                  print('FrameWork._initLayout>', func)
                  func()
            else:
              _analyseContents(content)

      contentToRemove.reverse()  # not needed, but delete from end
      for content in contentToRemove:
        contents.remove(content)
    # ===
    # start of the actual method code
    # ===
    yamlPath = os.path.join(self.project.path, 'layouts', 'layout.yaml')
    if os.path.exists(yamlPath):
      #print('FrameWork._initLayout>', yamlPath)
      try:
        with open(yamlPath) as f:
          layout = yaml.load(f)

        typ, contents, state = layout['main']  # main window
        _analyseContents(contents)

        floatLayoutsToRemove = []
        for floatLayout in layout['float']:  # floating windows
          typ, contents, state = floatLayout[0]['main']
          _analyseContents(contents)
          if not contents:
            floatLayoutsToRemove.append(floatLayout)

        floatLayoutsToRemove.reverse()  # not needed, but delete from end
        for floatLayout in floatLayoutsToRemove:
          layout['float'].remove(floatLayout)

        self.ui.mainWindow.moduleArea.restoreState(layout)
      except Exception as e:
        # for now just ignore restore failures
        getLogger().warning("Layout restore failed: %s" % e)

    if len(self.ui.mainWindow.moduleArea.currentModulesNames) == 0:
      self.ui.mainWindow.newBlankDisplay()

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
    if undo is not None:                # ejb - changed from if undo:
      # set undo step
      undo.newWaypoint()                # DO NOT CHANGE
      undo.increaseWaypointBlocking()
    if not self._echoBlocking:

      self.project.suspendNotification()

      # Get list of command strings
      commands = []
      for parameter, value in sorted(objectParameters.items()):
        if value is not None:
          if not isinstance(value, str):
            value = value.pid
          commands.append("%s = project.getByPid(%s)" % (parameter, repr(value)))
      commands.append(command)

      # echo command strings
      self.ui.echoCommands(commands)

    self._echoBlocking += 1
    getLogger().debug('command=%s, echoBlocking=%s, undo.blocking=%s'
                               % (command, self._echoBlocking, undo.blocking))


  #TODO:TJ: Why is this a private method; it is and should be used all over the code?
  def _endCommandBlock(self):
    """End block for command echoing,

    MUST be paired with _startCommandBlock call - use try ... finally to ensure both are called"""

    getLogger().debug('echoBlocking=%s' % self._echoBlocking)
    undo = self.project._undo
    if undo is not None:                # ejb - changed from if undo:
      undo.decreaseWaypointBlocking()

    if self._echoBlocking > 0:
      # If statement should always be True, but to avoid weird behaviour in error situations we check
      self._echoBlocking -= 1
    self.project.resumeNotification()

  def addApplicationMenuSpec(self, spec, position=3):
    """Add an entirely new menu at specified position"""
    self._menuSpec.insert(position, spec)

  def addApplicationMenuItem(self, menuName, menuItem, position):
    """Add a new item to an existing menu at specified position"""
    for spec in self._menuSpec:
      if spec[0] == menuName:
        spec[1].insert(position, menuItem)
        return

    raise Exception('No menu with name %s' % menuName)

  def addApplicationMenuItems(self, menuName, menuItems, position):
    """Add a new items to an existing menu starting at specified position"""
    for n, menuItem in enumerate(menuItems):
      self.addApplicationMenuItem(menuName, menuItem, position+n)

  #########################################    Start setup Menus      ############################

  def _updateCheckableMenuItems(self):
    # This has to be kept in sync with menu items below which are checkable,
    # and also with MODULE_DICT keys
    # The code is terrible because Qt has no easy way to get hold of menus / actions

    mainWindow = self.ui.mainWindow
    if mainWindow is None:
      # We have a UI with no mainWindow - nothing to do.
      return

    topMenu = mainWindow.menuBar().findChildren(QtGui.QMenu)[0]
    topActionDict = {}
    for topAction in topMenu.actions():
      mainActionDict = {}
      for mainAction in topAction.menu().actions():
        mainActionDict[mainAction.text()] = mainAction
      topActionDict[topAction.text()] = mainActionDict

    openModuleKeys = set(mainWindow.moduleArea.modules.keys())
    for key, topActionText, mainActionText in (('SEQUENCE', 'Molecules', 'Show Sequence'),
                                               ('PYTHON CONSOLE', 'View', 'Python Console')):
      if key in openModuleKeys:
        mainActionDict = topActionDict.get(topActionText) # should always exist but play safe
        if mainActionDict:
          mainAction = mainActionDict.get(mainActionText)
          if mainAction:
            mainAction.setChecked(True)

  def setupMenus(self):
    """Setup the menu specification.

    The menus are specified by a list of lists (actually, an iterable of iterables, but the term
    ‘list’ will be used here to mean any iterable).  Framework provides 7 menus: Project, Spectrum,
    Molecules, View, Macro, Plugins, Help.  If you want to create your own menu in a subclass of
    Framework, you need to create a list in the style described below, then call
    self.addApplicationMenuSpec and pass in your menu specification list.

    Menu specification lists are composed of two items, the first being a string which is the menu’s
    title, the second is a list of sub-menu items.  Each item can be zero, two or three items long.
    A zero-length list indicates a separator.  If the list is length two and the second item is a
    list, then it specifies a sub-menu in a recursive manner.  If the list is length two and the
    second item is callable, it specifies a menu action with the first item specifying the label
    and the second the callable that is triggered when the menu item is selected.  If the list is
    length three, it is treated as a menu item specification, with the third item a list of keyword,
    value pairs.

    The examples below may make this more clear…

    Create a menu called ‘Test’ with two items and a separator:

    | - Test
    |   | - Item One
    |   | - ------
    |   | - Item Two

    Where clicking on ‘Item One’ calls method self.itemOneMethod and clicking on ‘Item Two’
    calls self.itemTwoMethod

    |    def setupMenus(self):
    |      menuSpec = (‘Test’, [(‘Item One’, self.itemOneMethod),
    |                           (),
    |                           (‘Item Two’, self.itemTwoMethod),
    |                          ]
    |      self.addApplicationMenuSpec(menuSpec)



    More complicated menus are possible.  For example, to create the following menu

    | - Test
    |   | - Item A     ia
    |   | - ------
    |   | - Submenu B
    |      | - Item B1
    |      | - Item B2
    |   | - Item C     id

    where Item A can be activated using the two-key shortcut ‘ia’,
    Submenu B contains two static menu items, B1 and B2
    Submenu item B2 is checkable, but not checked by default
    Item C is disabled by default and has a shortcut of ‘ic’

    |   def setupMenus(self):
    |     subMenuSpecB = [(‘Item B1’, self.itemB1),
    |                     (‘Item B2’, self.itemB2, [(‘checkable’, True),
    |                                               (‘checked’, False)])
    |                    ]
    |
    |     menuSpec = (‘Test’, [(‘Item A’, self.itemA, [(‘shortcut’, ‘ia’)]),
    |                          (),
    |                          (‘Submenu B’, subMenuB),
    |                          (‘Item C’, self.itemA, [(‘shortcut’, ‘ic’),
    |                                                  (‘enabled’, False)]),
    |                         ]
    |     self.addApplicationMenuSpec(menuSpec)


    If we’re using the PyQt GUI, we can get the Qt action representing Item B2 somewhere in our code
    (for example, to change the checked status,) via:

    |   action = application.ui.mainWindow.getMenuAction(‘Test->Submenu B->Item B2’)
    |   action.setChecked(True)

    To see how to add items dynamically, see clearRecentProjects in this class and
    _fillRecentProjectsMenu in GuiMainWindow

    """
    self._menuSpec = ms = []

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
      ("NEF", (("Import Nef File", self._importNef, [('shortcut', 'in'), ('enabled', True)]),
                ("Export Nef File", self._exportNEF, [('shortcut', 'ex')])
              )),
      (),
      ("Undo", self.undo, [('shortcut', '⌃z')]),  # Unicode U+2303, NOT the carrot on your keyboard.
      ("Redo", self.redo, [('shortcut', '⌃y')]),  # Unicode U+2303, NOT the carrot on your keyboard.
      (),
      ("Summary", self.displayProjectSummary),
      ("Archive", self.archiveProject, [('enabled', False)]),
      ("Restore From Archive...", self.restoreFromArchive, [('enabled', False)]),
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
      ("Pick Peaks", (("Pick 1D Peaks...", self.showPeakPick1DPopup, [('shortcut', 'p1')]),
                        ("Pick ND Peaks...", self.showPeakPickNDPopup, [('shortcut', 'pp')])
                         )),
      ("Copy PeakList...", self.showCopyPeakListPopup, [('shortcut', 'cl')]),
      ("Copy Peaks...",    self.showCopyPeaks, [('shortcut', 'cp')]),

      (),
      ("Make Projection...", self.showProjectionPopup, [('shortcut', 'pj')]),
      (),
      ("Print to File...", self.showPrintSpectrumDisplayPopup, [('shortcut', 'pr')]),
    ]
               ))

    ms.append(('Molecules', [
      ("Chain from FASTA...", lambda:self.loadData(text='Load FASTA')),
      (),
      ("Generate Chain...", self.showCreateChainPopup),
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
      # ("Structure Table", self.showStructureTable, [('shortcut', 'st')]),
      ("Peak Table", self.showPeakTable, [('shortcut', 'lt')]),
      ("Integral Table", self.showIntegralTable, [('shortcut', 'it')]),
      ("Restraint Table", self.showRestraintTable, [('shortcut', 'rt')]),
      ("Structure Table", self.showStructureTable, [('shortcut', 'st')]),
      (),
      ("Chemical Shift Mapping", self.showChemicalShiftMapping, [('shortcut', 'cm')]),
      (),
      # (),
      ###("Sequence Graph", self.showSequenceGraph, [('shortcut', 'sg')]),
      ###("Atom Selector", self.showAtomSelector, [('shortcut', 'as')]),
      ###(),
      ("Show Sequence", self.toggleSequenceModule, [('shortcut', 'sq'),
                                                    ('checkable', True),
                                                    ('checked', False)
                                                    ]),
      (),
      ("Current", (("Show/Hide Toolbar", self.toggleToolbar, [('shortcut', 'tb')]),
                   ("Show/Hide Phasing Console", self.togglePhaseConsole, [('shortcut', 'pc')]),
                   ("Reset Zoom", self.resetZoom, [('shortcut', 'rz')]),
                   (),
                   ("Flip X-Y Axis", self.flipXYAxis, [('shortcut', 'xy')]),
                   ("Flip X-Z Axis", self.flipXZAxis, [('shortcut', 'xz')]),
                   ("Flip Y-Z Axis", self.flipYZAxis, [('shortcut', 'yz')])
                   )),
      (),
      ("Notes Table", self.showNotesEditor, [('shortcut', 'no')]),
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
      ("Run...", self.runMacro),
      ("Run Recent", ()),
      (),
      ("Define User Shortcuts...", self.defineUserShortcuts, [('shortcut', 'du')])
    ]
               ))

    ms.append(('Plugins', ()))

    ms.append(('Help',      [
      ("Tutorials",([
        # Submenu
        ("Beginners Tutorial", self.showBeginnersTutorial),
        ("Backbone Tutorial", self.showBackboneTutorial),
        ("Screen Tutorial", self.showScreenTutorial)
      ])),
      ("Show Shortcuts", self.showShortcuts),
      ("Show CcpNmr V3 Documentation", self.showVersion3Documentation),
      (),
      ("About CcpNmr V3...", self.showAboutPopup),
      ("About CCPN...", self.showAboutCcpn),
      ("Show License...", self.showCcpnLicense),
      (),
      ("Inspect Code...", self.showCodeInspectionPopup,[('shortcut', 'gv'),
                                                        ('enabled', False)]),
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
    project = coreIo.newProject(name=name, useFileLogger=self.useFileLogger, level=self.level)

    self._initialiseProject(project)

    project._resetUndo(debug=self.level <= Logging.DEBUG2)

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
    if dataType == 'Project' and subType in (ioFormats.CCPN, ioFormats.NEF, ioFormats.NMRSTAR):

      if subType != ioFormats.NEF:    # ejb - only reset project for CCPN files
        if self.project is not None:
          self._closeProject()

      if subType == ioFormats.CCPN:
        sys.stderr.write('==> Loading %s project "%s"\n' % (subType, path))
        project = coreIo.loadProject(path, useFileLogger=self.useFileLogger, level=self.level)
        project._resetUndo(debug=self.level <= Logging.DEBUG2)
        self._initialiseProject(project)
      elif subType == ioFormats.NEF:
        sys.stderr.write('==> Loading %s NEF project "%s"\n' % (subType, path))
        project = self._loadNefFile(path, makeNewProject=True)   # RHF - new by default
        project._resetUndo(debug=self.level <= Logging.DEBUG2)

      elif subType == ioFormats.NMRSTAR:
        sys.stderr.write('==> Loading %s NMRStar project "%s"\n' % (subType, path))
        project = self._loadNMRStarFile(path, makeNewProject=True)   # RHF - new by default
        project._resetUndo(debug=self.level <= Logging.DEBUG2)


      return project

    # elif dataType == 'NefFile' and subType in (ioFormats.NEF):
    # # ejb - testing - 24/6/17 hopefully this will insert into project
    # #                 is caught by the test above
    # #                 need to deciode whether it is a 'project' or 'NefFile' load
    #
    #   sys.stderr.write('==> Loading %s NefFile "%s"\n' % (subType, path))
    #   project = self._loadNefFile(path, makeNewProject=False)
    #   project._resetUndo(debug=_DEBUG)
    #
    #   return project

    else:
      sys.stderr.write('==> Could not recognise "%s" as a project\n' % path)

  def _loadNefFile(self, path:str, makeNewProject=True) -> Project:
    """Load Project from NEF file at path, and do necessary setup"""

    dataBlock = self.nefReader.getNefData(path)

    if makeNewProject:
      if self.project is not None:
        self._closeProject()
      self.project = self.newProject(dataBlock.name)

    self._echoBlocking += 1
    self.project._undo.increaseBlocking()
    self.project._wrappedData.shiftAveraging = False

    try:
      self.nefReader.importNewProject(self.project, dataBlock)
    finally:
      self.project._wrappedData.shiftAveraging = True
      self._echoBlocking -= 1
      self.project._undo.decreaseBlocking()

    return self.project

  def _loadNMRStarFile(self, path:str, makeNewProject=True) -> Project:
    """Load Project from NEF file at path, and do necessary setup"""

    dataBlock = self.nefReader.getNMRStarData(path)

    if makeNewProject:
      if self.project is not None:
        self._closeProject()
      self.project = self.newProject(dataBlock.name)

    self._echoBlocking += 1
    self.project._undo.increaseBlocking()
    self.project._wrappedData.shiftAveraging = False

    try:
      self.nefReader.importNewNMRStarProject(self.project, dataBlock)
    finally:
      self.project._wrappedData.shiftAveraging = True
      self._echoBlocking -= 1
      self.project._undo.decreaseBlocking()

    return self.project

  def clearRecentProjects(self):
    self.preferences.recentFiles = []
    self.ui.mainWindow._fillRecentProjectsMenu()


  def clearRecentMacros(self):
    self.preferences.recentMacros = []
    self.ui.mainWindow._fillRecentMacrosMenu()


  def loadData(self, paths=None, text=None, filter=None):
    """
    Opens a file dialog box and loads data from selected file.
    """
    if text is None:
      text = 'Load Data'

    if paths is None:
      #TODO:LIST-AS-ISSUE: This fails for native file dialogs on OSX when trying to select a project (i.e. a directory)
      # NBNB TBD I assume here that path is either a string or a list lf string paths.
      # NBNB #FIXME if incorrect
      dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.AnyFile, text=text,
                          acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general
                          , filter=filter)
      path = dialog.selectedFile()
      if not path:
        return
      paths = [path]

    elif isinstance(paths, str):
      paths = [paths]

    for path in paths:
      self.project.loadData(path)

  def _saveLayout(self):
    moduleArea = self.ui.mainWindow.moduleArea
    layout = moduleArea.saveState()
    ###currentModulesDict = moduleArea.currentModulesDict
    layoutPath = os.path.join(self.project.path, 'layouts')
    if not os.path.exists(layoutPath):
      os.makedirs(layoutPath)
    import yaml
    with open(os.path.join(layoutPath, "layout.yaml"), 'w') as stream:
      yaml.dump(layout, stream)
      stream.close()

  # GWV while refactoring: This routine seems not to be called
  #TODO:TJ: Confirm and delete
  # def _restoreLayout(self):
  #   import yaml, os
  #   if os.path.exists(os.path.join(self.project.path, 'layouts', 'layout.yaml')):
  #     try:
  #       with open(os.path.join(self.project.path, 'layouts', 'layout.yaml')) as f:
  #         modulesDict, layoutState =  yaml.load(f)
  #
  #       import ccpn.ui.gui.modules as gm
  #       ccpnModules = gm.importCcpnModules(modulesDict)
  #       for ccpnModule in ccpnModules:
  #         #FIXME: is this correct?
  #         newModule = ccpnModule(self.ui.gui.mainWindow)
  #         self.ui.mainWindow.moduleArea.addModule(newModule)
  #
  #       self.ui.mainWindow.moduleArea.restoreState(layoutState)
  #
  #     except Exception as e:
  #       # for now just ignore restore failures
  #       getLogger().warning("Layout restore failed: %s" % e)

  #
  # def _openCcpnModule(self, ccpnModules, **kwargs):
  #
  #   for ccpnModule in ccpnModules:
  #     if ccpnModule.moduleName == kwargs['moduleName']:
  #       newModule = ccpnModule(self.project)
  #       self.ui.mainWindow.moduleArea.addModule(newModule)

  def _saveProject(self, newPath=None, createFallback=True, overwriteExisting=True) -> bool:
    """Save project to newPath and return True if successful"""
    successful = self.project.save(newPath=newPath, createFallback=createFallback,
                                   overwriteExisting=overwriteExisting)
    if not successful:
      sys.stderr.write('==> Project save failed\n')
      # NBNB TODO Gui should pre-check newPath and/or pop up something in case of failure

    else:
      self.ui.mainWindow._updateWindowTitle()
      self.ui.mainWindow.getMenuAction('Project->Archive').setEnabled(True)
      self.ui.mainWindow._fillRecentProjectsMenu()
      # self._saveLayout()

      # saveIconPath = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'), 'icons', 'save.png')

      sys.stderr.write('==> Project successfully saved\n')
      # MessageDialog.showMessage('Project saved', 'Project successfully saved!',
      #                           colourScheme=self.preferences.general.colourScheme, iconPath=saveIconPath)

    return successful

  def _importNef(self):
    #TODO:ED add import routine here, dangerous so add warnings

    ok = MessageDialog.showOkCancelWarning('WARNING'
                                           , 'Importing Nef file will merge the Nef file with'
                                          ' the current project. This can cause conflicts with'
                                          ' existing objects. USE WITH CAUTION')

    if ok:
      text='Import Nef File into Project'
      filter = '*.nef'
      dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.AnyFile, text=text,
                          acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general
                          , filter=filter)
      path = dialog.selectedFile()
      if not path:
        return
      paths = [path]

      try:
        for path in paths:
          self._loadNefFile(path=path, makeNewProject=False)
      except Exception as es:
        getLogger().warning('Error Importing Nef File: %s' % str(es))

  def _exportNEF(self):
    #TODO:ED fix this temporary routine
    """
    Export the current project as a Nef file
    Temporary routine because I don't know how else to do it yet
    """
    from ccpn.ui.gui.popups.ExportNefPopup import ExportNefPopup

    dialog = ExportNefPopup(self.ui.mainWindow
                            , mainWindow=self.ui.mainWindow
                            , fileMode=FileDialog.AnyFile
                            , text="Export to Nef File"
                            , acceptMode=FileDialog.AcceptSave
                            , preferences=self.preferences.general
                            , selectFile=self.project.name+'.nef'     # new flag to populate dialog
                            , filter='*.nef')

    # an exclusion list comes out of the dialog as it

    nefPath, flags, pidList = dialog.show()

    if not nefPath:
      return

    # flags are skipPrefixes, expandSelection
    skipPrefixes = flags['skipPrefixes']
    expandSelection = flags['expandSelection']

    self.project.exportNef(nefPath
                   , overwriteExisting=True
                   , skipPrefixes=skipPrefixes
                   , expandSelection=expandSelection
                   , pidList=pidList)

  def saveProject(self, newPath=None, createFallback=True, overwriteExisting=True) -> bool:
    """Save project to newPath and return True if successful"""
    # TODO: convert this to a save and call self.project.save()
    if hasattr(self.project._wrappedData.root, '_temporaryDirectory'):
      return self.saveProjectAs()
    else:
      return self._saveProject(newPath=newPath, createFallback=createFallback,
                               overwriteExisting=overwriteExisting)

  # GWV: This routine should not be used as it calls the graphics mainWindow routine
  # Instead: The graphics part now calls _getRecentFiles
  #
  # def _updateRecentFiles(self, oldPath=None):
  #   project = self.project
  #   path = project.path
  #   recentFiles = self.preferences.recentFiles
  #   mainWindow = self.ui.mainWindow or self._mainWindow
  #
  #   if not hasattr(project._wrappedData.root, '_temporaryDirectory'):
  #     if path in recentFiles:
  #       recentFiles.remove(path)
  #     elif oldPath in recentFiles:
  #       recentFiles.remove(oldPath)
  #     elif len(recentFiles) >= 10:
  #       recentFiles.pop()
  #     recentFiles.insert(0, path)
  #   recentFiles = uniquify(recentFiles)
  #   mainWindow._fillRecentProjectsMenu()
  #   self.preferences.recentFiles = recentFiles

  def _getRecentFiles(self, oldPath=None) -> list:
    """Get and return a list of recent files, setting reference to
       self as first element, unless it is a temp project
       update the preferences with the new list
       
       CCPN INTERNAL: called by MainWindow
    """
    project = self.project
    path = project.path
    recentFiles = self.preferences.recentFiles

    #TODO:RASMUS: replace by new function on project: isTemporary()
    if not hasattr(project._wrappedData.root, '_temporaryDirectory'):
      if path in recentFiles:
        recentFiles.remove(path)
      elif oldPath in recentFiles:
        recentFiles.remove(oldPath)
      elif len(recentFiles) >= 10:
        recentFiles.pop()
      recentFiles.insert(0, path)
    recentFiles = uniquify(recentFiles)
    self.preferences.recentFiles = recentFiles
    return recentFiles

  def saveProjectAs(self):
    """Opens save Project as dialog box and saves project to path specified in the file dialog."""
    oldPath = self.project.path
    newPath = getSaveDirectory(self.preferences.general)
    if newPath:
      # Next line unnecessary, but does not hurt
      newProjectPath = apiIo.addCcpnDirectorySuffix(newPath)
      successful = self._saveProject(newPath=newProjectPath, createFallback=False)

      if not successful:
        getLogger().warning("Saving project to %s aborted" % newProjectPath)
    else:
      successful = False
      getLogger().info("Project not saved - no valid destination selected")

    self._getRecentFiles(oldPath=oldPath) # this will also update the list
    self.ui.mainWindow._fillRecentProjectsMenu()  # Update the menu

    return successful

    # NBNB TODO Consider appropriate failure handling. Is this OK?


  def undo(self):
    if self.project._undo.canUndo():
      with MessageDialog.progressManager(self.ui.mainWindow, 'performing Undo'):

        self.ui.echoCommands(['application.undo()'])
        self._echoBlocking += 1
        self.project._undo.undo()

        # TODO:ED this is a hack until guiNotifiers are working
        try:
          self.ui.mainWindow.moduleArea.repopulateModules()
        except:
          getLogger().info('application has no Gui')

        self._echoBlocking -= 1
    else:
      getLogger().warning('nothing to undo')

  def redo(self):
    if self.project._undo.canRedo():
      with MessageDialog.progressManager(self.ui.mainWindow, 'performing Redo'):
        self.ui.echoCommands(['application.redo()'])
        self._echoBlocking += 1
        self.project._undo.redo()

        # TODO:ED this is a hack until guiNotifiers are working
        try:
          self.ui.mainWindow.moduleArea.repopulateModules()
        except:
          getLogger().info('application has no Gui')

        self._echoBlocking -= 1
    else:
      getLogger().warning('nothing to redo.')

  def saveLogFile(self):
    pass

  def clearLogFile(self):
    pass

  def displayProjectSummary(self, position:str='left', relativeTo:CcpnModule=None):
    """
    Displays Project summary module on left of main window.
    """
    from ccpn.ui.gui.popups.ProjectSummaryPopup import ProjectSummaryPopup

    if self.ui:
      popup = ProjectSummaryPopup(self.project, self.ui.mainWindow, modal=True)
      popup.show()
      popup.raise_()
      popup.exec_()

  def archiveProject(self):

    project = self.project
    apiProject = project._wrappedData.parent
    fileName = apiIo.packageProject(apiProject, includeBackups=True, includeLogs=True,
                                    includeArchives=False, includeSummaries=True)

    MessageDialog.showInfo('Project Archived',
                           'Project archived to %s' % fileName, colourScheme=self.ui.mainWindow.colourScheme)

    self.ui.mainWindow._updateRestoreArchiveMenu()

  def _archivePaths(self):

    archivesDirectory = os.path.join(self.project.path, Path.CCPN_ARCHIVES_DIRECTORY)
    if os.path.exists(archivesDirectory):
      fileNames = os.listdir(archivesDirectory)
      paths = [os.path.join(archivesDirectory, fileName) for fileName in fileNames if fileName.endswith('.tgz')]
    else:
      paths = []

    return paths

  def restoreFromArchive(self, archivePath=None):

    if not archivePath:
      archivesDirectory = os.path.join(self.project.path, Path.CCPN_ARCHIVES_DIRECTORY)
      dialog = FileDialog(self.ui.mainWindow, fileMode=FileDialog.ExistingFile, text="Select Archive",
                          acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general,
                          directory=archivesDirectory, filter='*.tgz')
      archivePath = dialog.selectedFile()

    if archivePath:
      directoryPrefix = archivePath[:-4] # -4 removes the .tgz
      outputPath, temporaryDirectory = self._unpackCcpnTarfile(archivePath, outputPath=directoryPrefix)
      pythonExe = os.path.join(Path.getTopDirectory(), Path.CCPN_PYTHON)
      command = [pythonExe, sys.argv[0], outputPath]
      from subprocess import Popen
      Popen(command)

  def _unpackCcpnTarfile(self, tarfilePath, outputPath=None, directoryPrefix='CcpnProject_'):
    """
    # CCPN INTERNAL - called in loadData method of Project
    """

    if outputPath:
      if not os.path.exists(outputPath):
        os.makedirs(outputPath)
      temporaryDirectory = None
    else:
      temporaryDirectory = tempfile.TemporaryDirectory(prefix=directoryPrefix)
      outputPath = temporaryDirectory.name

    cwd = os.getcwd()
    try:
      os.chdir(outputPath)
      tp = tarfile.open(tarfilePath)
      tp.extractall()

       # look for a directory inside and assume the first found is the project directory (there should be exactly one)
      relfiles = os.listdir('.')
      for relfile in relfiles:
        fullfile = os.path.join(outputPath, relfile)
        if os.path.isdir(fullfile):
          outputPath = fullfile
          break
      else:
        raise IOError('Could not find project directory in tarfile')

    finally:
      os.chdir(cwd)

    return outputPath, temporaryDirectory

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
        getLogger().warning('Preferences not saved: %s' % (directory, e))
        return

    prefFile = open(prefPath, 'w+')
    json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
    prefFile.close()

    # reply = MessageDialog.showMulti("Quit Program", "Do you want to save changes before quitting?",
    #                                 ['Save and Quit', 'Quit without Saving', 'Cancel'],
    #                                 colourScheme=self.ui.mainWindow.colourScheme)
    reply = MessageDialog.showMulti("Quit Program", "Do you want to save changes before quitting?",
                                    ['Save and Quit', 'Quit without Saving', 'Cancel'])   # ejb
    if reply == 'Save and Quit':
      if event:
        event.accept()
      prefFile = open(prefPath, 'w+')
      json.dump(self.preferences, prefFile, sort_keys=True, indent=4, separators=(',', ': '))
      prefFile.close()

      success = self.saveProject()
      if success is True:
        # Close and clean up project
        self._closeProject()
        QtGui.QApplication.quit()
      else:
        if event:                             # ejb - don't close the project
          event.ignore()

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

  def _closeExtraWindows(self):
    tempAreas = self.ui.mainWindow.moduleArea.tempAreas
    if len(tempAreas) > 0:
      for tempArea in tempAreas:
        tempArea.window().close()

  def _closeProject(self):
    """Close project and clean up - when opening another or quitting application"""

    # NB: this function must clan up both wrapper and ui/gui

    if self.project is not None:
      # Cleans up wrapper project, including graphics data objects (Window, Strip, etc.)
      self.project._close()
      self.project = None
    if self.ui.mainWindow:
      # ui/gui cleanup
      self._closeExtraWindows()
      self.ui.mainWindow.deleteLater()
    self.ui.mainWindow = None
    self.current = None
    self.project = None

  ###################################################################################################################
  ## MENU callbacks:  Spectrum
  ###################################################################################################################

  def showSpectrumGroupsPopup(self):
    if not self.project.spectra:
      getLogger().warning('Project has no Specta. Spectrum groups cannot be displayed')
      MessageDialog.showWarning('Project contains no spectra.', 'Spectrum groups cannot be displayed')
    else:
      from ccpn.ui.gui.popups.SpectrumGroupEditor import SpectrumGroupEditor
      SpectrumGroupEditor(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, editorMode=True).exec_()


  def showProjectionPopup(self):
    if not self.project.spectra:
      getLogger().warning('Project has no Specta. Make Projection Popup cannot be displayed')
      MessageDialog.showWarning('Project contains no spectra.', 'Make Projection Popup cannot be displayed')
    else:
      from ccpn.ui.gui.popups.SpectrumProjectionPopup import SpectrumProjectionPopup
      popup = SpectrumProjectionPopup(self.ui.mainWindow, self.project)
      popup.exec_()


  def showExperimentTypePopup(self):
    """
    Displays experiment type popup.
    """
    if not self.project.spectra:
      getLogger().warning('Experiment Type Selection: Project has no Specta.')
      MessageDialog.showWarning('Experiment Type Selection', 'Project has no Spectra.')
    else:
      from ccpn.ui.gui.popups.ExperimentTypePopup import ExperimentTypePopup
      popup = ExperimentTypePopup(self.ui.mainWindow, self.project)
      popup.exec_()


  def showPeakPick1DPopup(self):
    """
    Displays Peak Picking 1D Popup.
    """
    if not self.project.peakLists:
      getLogger().warning('Peak Picking: Project has no Specta.')
      MessageDialog.showWarning('Peak Picking', 'Project has no Spectra.')
    else:
      from ccpn.ui.gui.popups.PickPeaks1DPopup import PickPeak1DPopup
      popup = PickPeak1DPopup(mainWindow=self.ui.mainWindow)
      popup.exec_()
      popup.raise_()

  def showPeakPickNDPopup(self):
    """
    Displays Peak Picking ND Popup.
    """
    if not self.project.peakLists:
      getLogger().warning('Peak Picking: Project has no Specta.')
      MessageDialog.showWarning('Peak Picking', 'Project has no Spectra.')
    else:
      from ccpn.ui.gui.popups.PeakFind import PeakFindPopup
      if self.current.strip:
        popup = PeakFindPopup(mainWindow=self.ui.mainWindow)
        popup.exec_()
        popup.raise_()
      else:
        getLogger().warning('Pick Nd Peaks, no strip selected')
        MessageDialog.showWarning('Pick Nd Peaks', 'No strip selected')

  def showCopyPeakListPopup(self):
    if not self.project.peakLists:
      getLogger().warning('Project has no Peak Lists. Peak Lists cannot be copied')
      MessageDialog.showWarning('Project has no Peak Lists.', 'Peak Lists cannot be copied')
      return
    else:
      from ccpn.ui.gui.popups.CopyPeakListPopup import CopyPeakListPopup
      CopyPeakListPopup(application=self).exec_()

  def showCopyPeaks(self):
    if not self.project.peakLists:
      getLogger().warning('Project has no Peak Lists. Peak Lists cannot be copied')
      MessageDialog.showWarning('Project has no Peak Lists.', 'Peak Lists cannot be copied')
      return
    else:
      from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks
      popup = CopyPeaks(mainWindow=self.ui.mainWindow)
      peaks = self.current.peaks
      popup._selectPeaks(peaks)
      popup.exec()
      popup.raise_()


  ################################################################################################
  ## MENU callbacks:  Molecule
  ################################################################################################

  def showCreateChainPopup(self):
    """
    Displays sequence creation popup.
    """
    from ccpn.ui.gui.popups.CreateChainPopup import CreateChainPopup
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.showCreateChainPopup()")
    getLogger().info("application.showCreateChainPopup()")
    popup = CreateChainPopup(mainWindow=self.ui.mainWindow).exec_()


  def toggleSequenceModule(self):
    """Toggles whether Sequence Module is displayed or not"""
    from ccpn.ui.gui.modules.SequenceModule import SequenceModule

    if SequenceModule._alreadyOpened is True:
      if SequenceModule._currentModule is not None:
        SequenceModule._currentModule.close()
        SequenceModule._alreadyOpened = False
    else:
      self.showSequenceModule()

    # if hasattr(self, 'sequenceModule'):
    #   if self.sequenceModule.isVisible():
    #     self.hideSequenceModule()
    # else:
    #   self.showSequenceModule()
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.toggleSequenceModule()")
    getLogger().info("application.toggleSequenceModule()")


  def showSequenceModule(self, position='top', relativeTo=None):
    """
    Displays Sequence Module at the top of the screen.
    """
    from ccpn.ui.gui.modules.SequenceModule import SequenceModule

    # if not hasattr(self, 'sequenceModule'):

    if SequenceModule._alreadyOpened is False:
      mainWindow = self.ui.mainWindow
      self.sequenceModule = SequenceModule(mainWindow=mainWindow)
      mainWindow.moduleArea.addModule(self.sequenceModule,
                                      position=position, relativeTo=relativeTo)
      action = self._findMenuAction('View', 'Show Sequence')
      if action: # should be True
        action.setChecked(True)

    return self.sequenceModule


  def hideSequenceModule(self):
    """Hides sequence module"""

    if hasattr(self, 'sequenceModule'):
      self.sequenceModule.close()
      delattr(self, 'sequenceModule')

  def inspectMolecule(self):
    pass


  def showRefChemicalShifts(self):
    """Displays Reference Chemical Shifts module."""
    from ccpn.ui.gui.modules.ReferenceChemicalShifts import ReferenceChemicalShifts
    self.refChemShifts = ReferenceChemicalShifts(mainWindow=self.ui.mainWindow)
    self.ui.mainWindow.moduleArea.addModule(self.refChemShifts)

  ###################################################################################################################
  ## MENU callbacks:  VIEW
  ###################################################################################################################

  def addBlankDisplay(self, position='right', relativeTo=None):
    # self.blankDisplay = self.ui.addBlankDisplay(position=position, relativeTo=relativeTo)

    mainWindow = self.ui.mainWindow
    blankList = mainWindow.moduleArea.findAll()
    if 'Blank Display' not in blankList[1]:

      if not relativeTo:
        relativeTo = mainWindow.moduleArea      # ejb - use same technique as below

      from ccpn.ui.gui.modules.BlankDisplay import BlankDisplay
      blankDisplay = BlankDisplay(mainWindow=mainWindow)
      mainWindow.moduleArea.addModule(blankDisplay, position=position, relativeTo=relativeTo)

    # if not BlankDisplay.isInstance():
    #   blankDisplay = BlankDisplay.instance(mainWindow=mainWindow)
    #   mainWindow.moduleArea.addModule(blankDisplay, position=position, relativeTo=relativeTo)
    # else:
    #   BlankDisplay.showInstance()

  # Property to issue deprecation warning, remove when value removed

  # ejb - temp removed 12/6/17

  # @property
  # def blankDisplay(self):
  #   from warnings import warn
  #   warn('{}.{} is deprecated.'.format(__class__, __name__), category=DeprecationWarning)
  #   return self.__blankDisplay
  # @blankDisplay.setter
  # def blankDisplay(self, value):
  #   self.__blankDisplay = value
  #

  def showChemicalShiftTable(self
                             , position:str='bottom'
                             , relativeTo:CcpnModule=None
                             , chemicalShiftList=None):
    """
    Displays Chemical Shift table.
    """
    from ccpn.ui.gui.modules.ChemicalShiftTable import ChemicalShiftTableModule

    mainWindow = self.ui.mainWindow
    #FIXME:ED - sometimes crashes
    if not relativeTo:
      relativeTo = mainWindow.moduleArea      # ejb
    self.chemicalShiftTableModule = ChemicalShiftTableModule(mainWindow=mainWindow, chemicalShiftList=chemicalShiftList)
    mainWindow.moduleArea.addModule(self.chemicalShiftTableModule, position=position, relativeTo=relativeTo)
    mainWindow.pythonConsole.writeConsoleCommand("application.showChemicalShiftTable()\n")
    getLogger().info("application.showChemicalShiftTable()")
    return self.chemicalShiftTableModule

  def showNmrResidueTable(self, position='bottom', relativeTo=None, nmrChain=None):
    """Displays Nmr Residue Table"""
    from ccpn.ui.gui.modules.NmrResidueTable import NmrResidueTableModule

    mainWindow = self.ui.mainWindow
    #FIXME:ED - sometimes crashes
    if not relativeTo:
      relativeTo = mainWindow.moduleArea      # ejb
    self.nmrResidueTableModule = NmrResidueTableModule(mainWindow=mainWindow, nmrChain=nmrChain)
    mainWindow.moduleArea.addModule(self.nmrResidueTableModule, position=position, relativeTo=relativeTo)
    mainWindow.pythonConsole.writeConsoleCommand("application.showNmrResidueTable()\n")
    getLogger().info("application.showNmrResidueTable()")
    return self.nmrResidueTableModule

  # def showStructureTable(self, position='bottom', relativeTo=None, structureEnsemble=None):
  #   """Displays Structure Table"""
  #   from ccpn.ui.gui.modules.StructureTable import StructureTableModule
  #
  #   mainWindow = self.ui.mainWindow
  #   #FIXME:ED - sometimes crashes
  #   if not relativeTo:
  #     relativeTo = mainWindow.moduleArea      # ejb
  #   self.structureTableModule = StructureTableModule(mainWindow=mainWindow
  #                                               , structureEnsemble=structureEnsemble)
  #   mainWindow.moduleArea.addModule(self.structureTableModule, position=position, relativeTo=relativeTo)
  #
  #   mainWindow.pythonConsole.writeConsoleCommand("application.showStructureTable()\n")
  #   logger.info("application.showStructureTable()")
  #   return self.structureTableModule
  #
  def showPeakTable(self, position:str='left', relativeTo:CcpnModule=None, peakList:PeakList=None):
    """
    Displays Peak table on left of main window with specified list selected.
    """
    from ccpn.ui.gui.modules.PeakTable import PeakTableModule

    mainWindow = self.ui.mainWindow
    #FIXME:ED - sometimes crashes
    if not relativeTo:
      relativeTo = mainWindow.moduleArea      # ejb
    self.peakTableModule = PeakTableModule(mainWindow, peakList=peakList)
    mainWindow.moduleArea.addModule(self.peakTableModule, position=position, relativeTo=relativeTo)
    mainWindow.pythonConsole.writeConsoleCommand("application.showPeakTable()\n")
    getLogger().info("application.showPeakTable()")
    return  self.peakTableModule

  def showIntegralTable(self, position:str='left', relativeTo:CcpnModule=None, integralList:IntegralList=None):
    """
    Displays integral table on left of main window with specified list selected.
    """
    from ccpn.ui.gui.modules.IntegralTable import IntegralTableModule

    mainWindow = self.ui.mainWindow
    #FIXME:ED - sometimes crashes
    if not relativeTo:
      relativeTo = mainWindow.moduleArea      # ejb
    self.integralTableModule = IntegralTableModule(mainWindow=mainWindow, integralList=integralList)
    mainWindow.moduleArea.addModule(self.integralTableModule, position=position, relativeTo=relativeTo)
    mainWindow.pythonConsole.writeConsoleCommand("application.showIntegralTable()\n")
    getLogger().info("application.showIntegralTable()")
    return  self.integralTableModule


  def showRestraintTable(self, position:str='bottom', relativeTo:CcpnModule=None, restraintList:PeakList=None):
    """
    Displays Peak table on left of main window with specified list selected.
    """
    from ccpn.ui.gui.modules.RestraintTable import RestraintTableModule
    mainWindow = self.ui.mainWindow
    #FIXME:ED - sometimes crashes
    if not relativeTo:
      relativeTo = mainWindow.moduleArea      # ejb
    self.restraintTableModule = RestraintTableModule(mainWindow=mainWindow, restraintList=restraintList)
    mainWindow.moduleArea.addModule(self.restraintTableModule, position=position, relativeTo=relativeTo)
    mainWindow.pythonConsole.writeConsoleCommand("application.showRestraintTable()\n")
    getLogger().info("application.showRestraintTable()")
    return self.restraintTableModule

  def showStructureTable(self, position='bottom', relativeTo=None, structureEnsemble=None):
    """Displays Structure Table"""
    from ccpn.ui.gui.modules.StructureTable import StructureTableModule

    mainWindow = self.ui.mainWindow

    #FIXME:ED - sometimes crashes
    if not relativeTo:
      relativeTo = mainWindow.moduleArea      # ejb
    self.structureTableModule = StructureTableModule(mainWindow=mainWindow
                                                , structureEnsemble=structureEnsemble)

    # self.project.newModule(moduleType=self.structureTableModule.className
    #                        , title=None
    #                        , window=mainWindow
    #                        , comment='')

    mainWindow.moduleArea.addModule(self.structureTableModule, position=position, relativeTo=relativeTo)

    mainWindow.pythonConsole.writeConsoleCommand("application.showStructureTable()\n")
    getLogger().info("application.showStructureTable()")
    return self.structureTableModule

  def showNotesEditor(self, position:str='bottom', relativeTo:CcpnModule=None, note=None):
    """
    Displays Notes Editing Table
    """
    from ccpn.ui.gui.modules.NotesEditor import NotesEditorModule
    mainWindow = self.ui.mainWindow

    #FIXME:ED - sometimes crashes
    if not relativeTo:
      relativeTo = mainWindow.moduleArea      # ejb
    self.notesEditorModule = NotesEditorModule(mainWindow=mainWindow, note=note)
    mainWindow.moduleArea.addModule(self.notesEditorModule, position=position, relativeTo=relativeTo)
    mainWindow.pythonConsole.writeConsoleCommand("application.showNotesEditorTable()\n")
    getLogger().info("application.showNotesEditorTable()")
    return self.notesEditorModule

  def showPrintSpectrumDisplayPopup(self):
    from ccpn.ui.gui.popups.PrintSpectrumPopup import SelectSpectrumDisplayPopup #,PrintSpectrumDisplayPopup
    if len(self.project.spectrumDisplays) == 0:
      MessageDialog.showWarning('', 'No Spectrum Display found')
    else:
      SelectSpectrumDisplayPopup(project=self.project).exec_()
      # PrintSpectrumDisplayPopup(project=self.project).exec_()

  def toggleToolbar(self):
    if self.current.strip is not None:
      self.current.strip.spectrumDisplay.toggleToolbar()
    else:
      getLogger().warning('No strip selected')

  def togglePhaseConsole(self):
    if self.current.strip is not None:
      self.current.strip.spectrumDisplay.togglePhaseConsole()
    else:
      getLogger().warning('No strip selected')

  def resetZoom(self):
    if self.current.strip is not None:
      self.current.strip.resetZoom()
    else:
      getLogger().warning('No strip selected')

  def flipXYAxis(self):
    if self.current.strip is not None:
      self.current.strip.flipXYAxis()
    else:
      getLogger().warning('No strip selected')

  def flipXZAxis(self):
    if self.current.strip is not None:
      self.current.strip.flipXZAxis()
    else:
      getLogger().warning('No strip selected')

  def flipYZAxis(self):
    if self.current.strip is not None:
      self.current.strip.flipYZAxis()
    else:
      getLogger().warning('No strip selected')

  def _findMenuAction(self, menubarText, menuText):
    # not sure if this function will be needed more widely or just in console context
    # CCPN internal: now also used in SequenceModule._closeModule

    for menuBarAction in self.ui.mainWindow._menuBar.actions():
      if menuBarAction.text() == menubarText:
        break
    else:
      return None

    for menuAction in menuBarAction.menu().actions():
      if menuAction.text() == menuText:
        return menuAction

    return None

  def toggleConsole(self):
    """
    Toggles whether python console is displayed at bottom of the main window.
    """

    mainWindow = self.ui.mainWindow

    if 'Python Console' in mainWindow.moduleArea.findAll()[1]:
      if mainWindow.pythonConsoleModule.isVisible():
        mainWindow.pythonConsoleModule.hide()
      else:
        mainWindow.moduleArea.moveModule(mainWindow.pythonConsoleModule, 'bottom', None)
    else:
      #TODO:LUCA: put in a proper PythonConsoleModule file; have a method showPythonConsole(True/False);
      # initialise in GuiMainWindow on __init__; set appropriate Menu callbacks
      from ccpn.ui.gui.modules.PythonConsoleModule import PythonConsoleModule
      action = self._findMenuAction('View', 'Python Console')
      closeFunc = action.trigger if action else None
      mainWindow.pythonConsoleModule = PythonConsoleModule(mainWindow, closeFunc=closeFunc)
      mainWindow.moduleArea.addModule(mainWindow.pythonConsoleModule, 'bottom')

  def showChemicalShiftMapping(self):
    from ccpn.ui.gui.modules.ChemicalShiftsMappingModule import ChemicalShiftsMapping
    cs = ChemicalShiftsMapping(mainWindow=self.ui.mainWindow)
    self.ui.mainWindow.moduleArea.addModule(cs)

  #################################################################################################
  ## MENU callbacks:  Macro
  #################################################################################################

  def showMacroEditor(self):
    """
    Displays macro editor.
    """
    mainWindow = self.ui.mainWindow
    self.editor = MacroEditor(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)
    # mainWindow.pythonConsole.writeConsoleCommand("application.showMacroEditor()")
    # getLogger().info("application.showMacroEditor()")

  def newMacroFromConsole(self):
    """
    Displays macro editor with contents of python console inside.
    """
    # editor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor")
    #FIXME:ED - haven't checked this properly
    mainWindow = self.ui.mainWindow
    self.editor = MacroEditor(mainWindow=mainWindow)
    self.editor.textBox.setText(mainWindow.pythonConsole.textEditor.toPlainText())
    mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)

  def newMacroFromLog(self):
    """
    Displays macro editor with contents of the log.
    """
    # editor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor")
    #FIXME:ED - haven't checked this properly
    mainWindow = self.ui.mainWindow
    self.editor = MacroEditor(mainWindow=mainWindow)

    l = open(getLogger().logPath, 'r').readlines()
    text = ''.join([line.strip().split(':', 6)[-1] + '\n' for line in l])
    self.editor.textBox.setText(text)
    mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)

  def startMacroRecord(self):
    """
    Displays macro editor with additional buttons for recording a macro.
    """
    mainWindow = self.ui.mainWindow
    self.editor = MacroEditor(mainWindow=mainWindow, showRecordButtons=True)
    mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)
    self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.startMacroRecord()")
    getLogger().info("application.startMacroRecord()")


  def defineUserShortcuts(self):

    from ccpn.ui.gui.modules.ShortcutModule import ShortcutModule
    # self.shortcutModule = ShortcutModule(self.ui.mainWindow)
    ShortcutModule(mainWindow=self.ui.mainWindow).exec_()   # ejb

  def runMacro(self, macroFile:str=None):
    """
    Runs a macro if a macro is specified, or opens a dialog box for selection of a macro file and then
    runs the selected macro.
    """
    if macroFile is None:
      dialog = FileDialog(self.ui.mainWindow, fileMode=FileDialog.ExistingFile, text="Run Macro",
                          acceptMode=FileDialog.AcceptOpen, preferences=self.preferences.general,
                          directory=self.preferences.general.userMacroPath, filter='*.py')
      macroFile = dialog.selectedFile()
      if not macroFile:
        return

    if not macroFile in self.preferences.recentMacros:
      self.preferences.recentMacros.append(macroFile)
    # self._fillRecentMacrosMenu()
    self.ui.mainWindow.pythonConsole._runMacro(macroFile)


  ###################################################################################################################
  ## MENU callbacks:  Help
  ###################################################################################################################



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
      newModule = CcpnModule(mainWindow=self.ui.mainWindow, name=title)
      view = CcpnWebView(path)
      newModule.addWidget(view)
      self.ui.mainWindow.moduleArea.addModule(newModule)

  def showBeginnersTutorial(self):
    from ccpn.framework.PathsAndUrls import beginnersTutorialPath
    self._systemOpen(beginnersTutorialPath)

  def showBackboneTutorial(self):
    from ccpn.framework.PathsAndUrls import backboneAssignmentTutorialPath
    self._systemOpen(backboneAssignmentTutorialPath)

  def showScreenTutorial(self):
    from ccpn.framework.PathsAndUrls import screenTutorialPath
    self._systemOpen(screenTutorialPath)

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
    # TODO: open a file browser to top of source directory
    pass

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

  # def printToFile(self, spectrumDisplay=None):
  #
  #   current = self.current
  #   # if not spectrumDisplay:
  #   #   spectrumDisplay = current.spectrumDisplay
  #   if not spectrumDisplay and current.strip:
  #     spectrumDisplay = current.strip.spectrumDisplay
  #   if not spectrumDisplay and self.spectrumDisplays:
  #     spectrumDisplay = self.spectrumDisplays[0]
  #   if spectrumDisplay:
  #     dialog = FileDialog(parent=self.ui.mainWindow, fileMode=FileDialog.AnyFile, text='Print to File',
  #                         acceptMode=FileDialog.AcceptSave, preferences=self.preferences.general, filter='SVG (*.svg)')
  #     path = dialog.selectedFile()
  #     if not path:
  #       return
  #     spectrumDisplay.printToFile(path)

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
  with open(preferencesPath) as fp:
    preferences = json.load(fp, object_hook=AttrDict)

  # read user settings and update if not skipped
  if not skipUserPreferences:
    from ccpn.framework.PathsAndUrls import userPreferencesPath
    preferencesPath = (userPath if userPath else os.path.expanduser(userPreferencesPath))
    if os.path.isfile(preferencesPath):
      with open(preferencesPath) as fp:
        userPreferences = json.load(fp, object_hook=AttrDict)
      preferences = _updateDict(preferences, userPreferences)

  return preferences
