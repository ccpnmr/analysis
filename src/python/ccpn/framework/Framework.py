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
__version__ = "$Revision: 3.0.b3 $"
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
import re
from PyQt5 import QtWidgets
from distutils.dir_util import copy_tree

from ccpn.core.IntegralList import IntegralList
from ccpn.core.PeakList import PeakList
from ccpn.core.MultipletList import MultipletList
from ccpn.core.Project import Project
from ccpn.core._implementation import Io as coreIo
from ccpn.core.lib import CcpnNefIo, CcpnSparkyIo
from ccpn.framework import Version
from ccpn.framework.Current import Current
from ccpn.framework.lib.Pipeline import Pipeline
from ccpn.framework.Translation import languages, defaultLanguage
from ccpn.framework.Translation import translator
from ccpn.ui import interfaces, defaultInterface
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
from ccpn.util import Layout
from ccpn.ui.gui.lib.guiDecorators import suspendSideBarNotifications
from ccpnmodel.ccpncore.api.memops import Implementation
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats
from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil
from ccpn.ui.gui.guiSettings import getColourScheme
from ccpn.framework.PathsAndUrls import userPreferencesDirectory
# from functools import partial

_DEBUG = False

# componentNames = ('Assignment', 'Screening', 'Structure')

AnalysisAssign = 'AnalysisAssign'
AnalysisScreen = 'AnalysisScreen'
AnalysisMetabolomics = 'AnalysisMetabolomics'
AnalysisStructure = 'AnalysisStructure'
ApplicationNames = [AnalysisAssign, AnalysisScreen, AnalysisMetabolomics, AnalysisStructure]
interfaceNames = ('NoUi', 'Gui')
DataDirName = 'data'
SpectraDirName = 'spectra'
PluginDataDirName = 'pluginData'
ScriptsDirName = 'scripts'
MacrosDirName = 'macros'

def _ccpnExceptionhook(type, value, tback):
  '''This because PyQT raises and catches exceptions,
  but doesn't pass them along instead makes the program crashing miserably.'''
  sys.__excepthook__(type, value, tback)

sys.excepthook = _ccpnExceptionhook


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
      lines.append("Developed by: %s" % __credits__)
    else:
      if isinstance(__credits__, tuple):
        lines.append("Developed by: %s" % __credits__[0])
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
    for component in ApplicationNames:
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
    self.ccpnModules = []

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
    self.layout  = None  # intialised by self._getUserLayout
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

    # SPARKY reader - ejb
    self.sparkyReader = CcpnSparkyIo.CcpnSparkyReader(self)

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
    backupPath = self.project.backupPath

    backupStatePath = Path.fetchDir(backupPath, Layout.StateDirName)

    copy_tree(self.statePath, backupStatePath)
    layoutFile = os.path.join(backupStatePath, Layout.DefaultLayoutFileName)
    Layout.saveLayoutToJson(self.ui.mainWindow, layoutFile)
    self.current._dumpStateToFile(backupStatePath)

    #Spectra should not be copied over. Dangerous for disk space
    # backupDataPath = Path.fetchDir(backupPath, DataDirName)

    #   TODO add other files inside this dirs
    backupScriptsPath = Path.fetchDir(backupPath, ScriptsDirName)
    backupLogsPath = Path.fetchDir(backupPath, ScriptsDirName)

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



    # init application directory
    self.scriptsPath = self.scriptsPath
    self.pymolScriptsPath = Path.fetchDir(self.scriptsPath, 'pymol')
    self.statePath = self.statePath
    self.dataPath = self.dataPath
    self.pipelinePath = self.pipelinePath
    self.spectraPath = self.spectraPath
    self.pluginDataPath = self.pluginDataPath

    # restore current
    self.current._restoreStateFromFile(self.statePath)

    self.project = project
    if hasattr(self, '_mainWindow'):
      Logging.getLogger().debug('>>>framework._initialiseProject')

      project._blockSideBar = True
      self.ui.initialize(self._mainWindow)
      project._blockSideBar = False

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

  def _getUserLayout(self, userPath=None):
    """defines the application.layout dictionary.
    For a saved project: uses the auto-generated during the saving process, if a user specified json file is given then
    is used that one instead.
    For a new project, it is used the default.
    """
    # try:
    if userPath:
      with open(userPath) as fp:
        layout = json.load(fp, object_hook=AttrDict)
        self.layout = layout
    else:
      # opens the autogenerated if an existing project
      savedLayoutPath = self._getAutogeneratedLayoutFile()
      if savedLayoutPath:
        with open(savedLayoutPath) as fp:
          layout = json.load(fp, object_hook=AttrDict)
          self.layout = layout
      else: # opens the default
        Layout._createLayoutFile(self)
        self._getUserLayout()
    # except Exception as e:
    #   getLogger().warning('No layout found. %s' %e)


    return self.layout

  def saveLayout(self):
    Layout.updateSavedLayout(self.ui.mainWindow)

  def saveLayoutAs(self):
    fp = self.getSaveLayoutPath()
    try:
      Layout.saveLayoutToJson(self.ui.mainWindow, jsonFilePath=fp)
    except Exception as e:
      getLogger().warning('Impossible to save layout. %s' %e)

  def restoreLastSavedLayout(self):
    self.ui.mainWindow.moduleArea._closeAll()
    Layout.restoreLayout(self.ui.mainWindow, self.layout)

  def restoreLayoutFromFile(self, jsonFilePath=None):
    if jsonFilePath is None:
      #asks with a dialog
      jsonFilePath = self.getSavedLayoutPath()
      if not os.path.exists(jsonFilePath):
        again = MessageDialog.showOkCancelWarning(title='File Does not exist', message='Try again?')
        if again:
          self.restoreLayoutFromFile()
        else:
          return
    try:
      self.ui.mainWindow.moduleArea._closeAll()
      self._getUserLayout(jsonFilePath)
      Layout.restoreLayout(self.ui.mainWindow, self.layout)
    except Exception as e:
      getLogger().warning('Impossible to restore layout. %s' %e)

  def _getAutogeneratedLayoutFile(self):
    if self.project:
      layoutFile = Layout.getLayoutFile(self)
      return layoutFile

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
        self.ui.mainWindow.show()
        QtWidgets.QApplication.processEvents()
        popup = RegisterPopup(self.ui.mainWindow, version=self.applicationVersion, modal=True)
        QtWidgets.QApplication.processEvents()
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
    from ccpn.ui.gui.lib import GuiStrip

    project = self.project
    try:
      if self.preferences.general.restoreLayoutOnOpening:
        layout = self._getUserLayout()
        if layout:
          Layout.restoreLayout(self._mainWindow, layout)
    except Exception as e:
      getLogger().warning('Impossible to restore Layout %s' % e)

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

      strips = spectrumDisplay.strips
      for strip in strips:

        # move to the correct place in the widget
        stripIndex = strips.index(strip)
        spectrumDisplay.stripFrame.layout().addWidget(strip, 0, stripIndex)

        specViews = strip.spectrumViews
        # for iSV, spectrumView in enumerate(strip.orderedSpectrumViews(includeDeleted=False)):

        for iSV, spectrumView in enumerate(spectrumDisplay.orderedSpectrumViews(specViews)):
          spectrumView._createdSpectrumView(iSV)
          for peakList in spectrumView.spectrum.peakLists:
            strip.showPeaks(peakList)

      # some of the strips may not be instantiated at this point
      spectrumDisplay.showAxes()
      spectrumDisplay.setColumnStretches(True)

#~~~~~~~~~~~~~~~~
    #
    # # Initialise SpectrumDisplays, SpectrumViews
    # for spectrumDisplay in project.spectrumDisplays:
    #
    #   # self.moduleArea.addModule(spectrumDisplay, position='right')
    #   strips = spectrumDisplay.strips
    #   for strip in strips:
    #
    #     # move to the correct place in the widget
    #     stripIndex = strips.index(strip)
    #     spectrumDisplay.stripFrame.layout().addWidget(strip, 0, stripIndex)
    #
    #     specViews = strip.spectrumViews
    #     # for iSV, spectrumView in enumerate(spectrumDisplay.orderedSpectrumViews(specViews)):
    #     for iSV, spectrumView in enumerate(specViews):
    #
    #       # set up the Z widgets and add new toolbar button
    #       spectrumDisplay._createdSpectrumView({Notifier.OBJECT: spectrumView})  #iSV)
    #
    #       for peakList in spectrumView.spectrum.peakLists:
    #         strip.showPeaks(peakList)
    #
    #   # some of the strips may no be instantiated at this point
    #   spectrumDisplay.showAxes()
    #   spectrumDisplay.setColumnStretches(True)
    #
#~~~~~~~~~~~~~~~~






    if self.current.strip is None:
      if len(self.project.strips)>0:
        self.current.strip = self.project.strips[0]

  def getByPid(self, pid):
    return self.project.getByPid(pid)

  def getByGid(self, gid):
    return self.ui.getByGid(gid)

  def _startCommandBlock(self, command:str, quiet:bool=False, **objectParameters):
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

      if not self.project._blockSideBar and not undo._blocked:
        if undo._waypointBlockingLevel < 1 and self.ui and self.ui.mainWindow:
          self._storedState = self.ui.mainWindow.sideBar._saveExpandedState()

      undo.increaseWaypointBlocking()
    if not self._echoBlocking:

      self.project.suspendNotification()

      # Get list of command strings
      commands = []
      for parameter, value in sorted(objectParameters.items()):
        if value is not None:
          if not isinstance(value, str):
            value = value.pid
          commands.append("%s = project.getByPid(%s)\n" % (parameter, repr(value)))
      commands.append(command)    # ED: newLine NOT needed here

      # echo command strings
      # added 'quiet' mode to keep full functionality to 'startCommandEchoBLock'
      # but without the screen output
      if not quiet:
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

    self.project.resumeNotification()

    if undo is not None:                # ejb - changed from if undo:
      undo.decreaseWaypointBlocking()

      if not self.project._blockSideBar and not undo._blocked:
        if undo._waypointBlockingLevel < 1 and self.ui and self.ui.mainWindow:
          self.ui.mainWindow.sideBar._restoreExpandedState(self._storedState)

    if self._echoBlocking > 0:
      # If statement should always be True, but to avoid weird behaviour in error situations we check
      self._echoBlocking -= 1
    # self.project.resumeNotification()

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


  #########################################    Create sub dirs   ########################################################

  ## dirs are created with decorators because the project path can change dynamically.
  ##  When a project is saved in a new location, all the dirs get refreshed automatically'

  @property
  def statePath(self):
    return self._statePath

  @statePath.getter
  def statePath(self):
    return Path.fetchDir(self.project.path, Layout.StateDirName)

  @statePath.setter
  def statePath(self, path):
    self._statePath = path

  @property
  def pipelinePath(self):
    return self._pipelinePath

  @pipelinePath.getter
  def pipelinePath(self):
    return Path.fetchDir(self.statePath, Pipeline.className)

  @pipelinePath.setter
  def pipelinePath(self, path):
    self._pipelinePath = path

  @property
  def dataPath(self):
    return self._dataPath

  @dataPath.getter
  def dataPath(self):
    return Path.fetchDir(self.project.path, DataDirName)

  @dataPath.setter
  def dataPath(self, path):
    self._dataPath = path

  @property
  def spectraPath(self):
    return self._spectraPath

  @spectraPath.getter
  def spectraPath(self):
    return Path.fetchDir(self.dataPath, SpectraDirName)

  @spectraPath.setter
  def spectraPath(self, path):
    self._spectraPath = path

  @property
  def pluginDataPath(self):
    return self._pluginDataPath

  @pluginDataPath.getter
  def pluginDataPath(self):
    return Path.fetchDir(self.dataPath, PluginDataDirName)

  @pluginDataPath.setter
  def pluginDataPath(self, path):
    self._pluginDataPath = path

  @property
  def tempMacrosPath(self):
    return self._tempMacrosPath

  @tempMacrosPath.getter
  def tempMacrosPath(self):
    return Path.fetchDir(userPreferencesDirectory, MacrosDirName)

  @tempMacrosPath.setter
  def tempMacrosPath(self, path):
    self._tempMacrosPath = path


  @property
  def scriptsPath(self):
    return self._scriptsPath

  @scriptsPath.getter
  def scriptsPath(self):
    return Path.fetchDir(self.project.path, ScriptsDirName)

  @scriptsPath.setter
  def scriptsPath(self, path):
    self._scriptsPath = path

  #########################################    Start setup Menus      ############################

  def _updateCheckableMenuItems(self):
    # This has to be kept in sync with menu items below which are checkable,
    # and also with MODULE_DICT keys
    # The code is terrible because Qt has no easy way to get hold of menus / actions

    mainWindow = self.ui.mainWindow
    if mainWindow is None:
      # We have a UI with no mainWindow - nothing to do.
      return

    topMenu = mainWindow.menuBar().findChildren(QtWidgets.QMenu)[0]
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
      ("New", self.createNewProject, [('shortcut', '⌃n')]),  # Unicode U+2303, NOT the carrot on your keyboard.
      ("Open...", self.openProject, [('shortcut', '⌃o')]),  # Unicode U+2303, NOT the carrot on your keyboard.
      ("Open Recent", ()),

#      ("Load Spectrum...", lambda: self.loadData(text='Load Spectrum'), [('shortcut', 'ls')]),
      ("Load Data...", self.loadData, [('shortcut', 'ld')]),
      (),
      ("Save", self.saveProject, [('shortcut', '⌃s')]),  # Unicode U+2303, NOT the carrot on your keyboard.
      ("Save As...", self.saveProjectAs, [('shortcut', 'sa')]),
      (),
      ("NEF", (("Import Nef File", self._importNef, [('shortcut', 'in'), ('enabled', True)]),
                ("Export Nef File", self._exportNEF, [('shortcut', 'ex')])
              )),
      (),
      (),
      ("Layout", (("Save", self.saveLayout, [('enabled', False)]),
                 ("Save as...", self.saveLayoutAs, [('enabled', False)]),
                 ("Restore last", self.restoreLastSavedLayout, [('enabled', False)]),
                 ("Restore from file...", self.restoreLayoutFromFile, [('enabled', False)]),
                 (),
                 ("Open pre-defined...", None, [('enabled', False)]),


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
      ("Quit", self._closeEvent, [('shortcut', '⌃q')]),  # Unicode U+2303, NOT the carrot on your keyboard.
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
      ("Residue Information", self.showResidueInformation, [('shortcut', 'ri')]),
      (),
      ("Reference Chemical Shifts", self.showRefChemicalShifts,[('shortcut', 'rc')]),
    ]
               ))

    ms.append(('View',      [
      ("Chemical Shift Table", self.showChemicalShiftTable, [('shortcut', 'ct')]),
      ("NmrResidue Table", self.showNmrResidueTable, [('shortcut', 'nt')]),
      # ("Structure Table", self.showStructureTable, [('shortcut', 'st')]),
      ("Peak Table", self.showPeakTable, [('shortcut', 'lt')]),
      ("Integral Table", self.showIntegralTable, [('shortcut', 'it')]),
      ("Multiplet Table", self.showMultipletTable, [('shortcut', 'mt')]),
      ("Restraint Table", self.showRestraintTable, [('shortcut', 'rt')]),
      ("Structure Table", self.showStructureTable, [('shortcut', 'st')]),
      (),
      ("Chemical Shift Mapping", self.showChemicalShiftMapping, [('shortcut', 'cm')]),
      ("Notes Editor", self.showNotesEditor, [('shortcut', 'no')]),
      (),
      # (),
      ###("Sequence Graph", self.showSequenceGraph, [('shortcut', 'sg')]),
      ###("Atom Selector", self.showAtomSelector, [('shortcut', 'as')]),
      ###(),

      # sequenceModule has been incorporated into sequence graph
      # ("Show Sequence", self.toggleSequenceModule, [('shortcut', 'sq'),
      #                                               ('checkable', True),
      #                                               ('checked', False)
      #                                               ]),
      (),
      ("Current", (("Show/Hide Toolbar", self.toggleToolbar, [('shortcut', 'tb')]),
                   ("Show/Hide Phasing Console", self.togglePhaseConsole, [('shortcut', 'pc')]),
                   (),
                   ("Set Zoom...", self._setZoomPopup, [('shortcut', 'sz')]),
                   ("Reset Zoom", self.resetZoom, [('shortcut', 'rz')]),
                   (),
                   ("New SpectrumDisplay with strip",    self.copyStrip,  []),
                   ("Flip X-Y Axis", self.flipXYAxis, [('shortcut', 'xy')]),
                   ("Flip X-Z Axis", self.flipXZAxis, [('shortcut', 'xz')]),
                   ("Flip Y-Z Axis", self.flipYZAxis, [('shortcut', 'yz')])
                   )),
      (),
      ("Show/hide Modules", ([
                              ("None", None, [('checkable', True),
                                               ('checked', False)])
                            ])),
      ("Python Console", self._toggleConsole, [('shortcut', '  '),
                                              ('checkable', True),
                                              ('checked', False)])
    ]
               ))

    ms.append(('Macro',     [
      ("New", self.showMacroEditor),
      ("New from Console", self.newMacroFromConsole),
      # ("New from Log", self.newMacroFromLog), #Broken
      (),
      ("Open...", self.openMacroOnEditor),
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
      project = self.newProject()
      try:
        project._mainWindow.show()
        QtWidgets.QApplication.setActiveWindow(project._mainWindow)
      except Exception as es:
        getLogger().warning('Error creating new project:', str(es))

  def newProject(self, name='default'):
    # """Create new, empty project"""

    # NB _closeProject includes a gui cleanup call

    if self.project is not None:
      self._closeProject()

    sys.stderr.write('==> Creating new, empty project\n')
    newName = re.sub('[^0-9a-zA-Z]+', '', name)
    if newName != name:
      getLogger().info('Removing whitespace from name: %s' % name)

    project = coreIo.newProject(name=newName, useFileLogger=self.useFileLogger, level=self.level)
    project._isNew = True
    # Needs to know this for restoring the GuiSpectrum Module. Could be removed after decoupling Gui and Data!

    self._initialiseProject(project)

    project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)

    return project


  def openProject(self, path=None):
    project = self.ui.mainWindow.loadProject(projectDir=path)
    if project:
      try:
        project._mainWindow.show()
        QtWidgets.QApplication.setActiveWindow(project._mainWindow)

      except Exception as es:
        getLogger().warning('Error opening project:', str(es))
      finally:
        return project
    else:
      return None

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
    if dataType == 'Project' and subType in (ioFormats.CCPN,
                                             ioFormats.NEF,
                                             ioFormats.NMRSTAR,
                                             ioFormats.SPARKY):

      # if subType != ioFormats.NEF:    # ejb - only reset project for CCPN files
      #   if self.project is not None:
      #     self._closeProject()

      if subType == ioFormats.CCPN:
        sys.stderr.write('==> Loading %s project "%s"\n' % (subType, path))

        if self.project is not None:    # always close for Ccpn
          self._closeProject()
        project = coreIo.loadProject(path, useFileLogger=self.useFileLogger, level=self.level)
        project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)
        self._initialiseProject(project)
        project._undo.clear()
      elif subType == ioFormats.NEF:
        sys.stderr.write('==> Loading %s NEF project "%s"\n' % (subType, path))
        project = self._loadNefFile(path, makeNewProject=True)   # RHF - new by default
        project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)

      elif subType == ioFormats.NMRSTAR:
        sys.stderr.write('==> Loading %s NMRStar project "%s"\n' % (subType, path))
        project = self._loadNMRStarFile(path, makeNewProject=True)   # RHF - new by default
        project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)

      elif subType == ioFormats.SPARKY:
        sys.stderr.write('==> Loading %s Sparky project "%s"\n' % (subType, path))
        project = self._loadSparkyProject(path, makeNewProject=True)   # RHF - new by default
        project._resetUndo(debug=self.level <= Logging.DEBUG2, application=self)

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

    from ccpn.core.lib.ContextManagers import undoBlock

    dataBlock = self.nefReader.getNefData(path)

    if makeNewProject:
      if self.project is not None:
        self._closeProject()
      self.project = self.newProject(dataBlock.name)

    # self._echoBlocking += 1
    # self.project._undo.increaseBlocking()
    self.project._wrappedData.shiftAveraging = False

    with undoBlock(self):
      try:
        self.nefReader.importNewProject(self.project, dataBlock)
      except Exception as es:
        getLogger().warning('Error loading Nef file: %s' % str(es))
      # finally:

    self.project._wrappedData.shiftAveraging = True
    # self._echoBlocking -= 1
    # self.project._undo.decreaseBlocking()

    return self.project

  def _loadNMRStarFile(self, path:str, makeNewProject=True) -> Project:
    """Load Project from NEF file at path, and do necessary setup"""

    from ccpn.core.lib.ContextManagers import undoBlock

    dataBlock = self.nefReader.getNMRStarData(path)

    if makeNewProject:
      if self.project is not None:
        self._closeProject()
      self.project = self.newProject(dataBlock.name)

    # self._echoBlocking += 1
    # self.project._undo.increaseBlocking()
    self.project._wrappedData.shiftAveraging = False

    with undoBlock(self):
      try:
        self.nefReader.importNewNMRStarProject(self.project, dataBlock)
      except Exception as es:
        getLogger().warning('Error loading NMRStar file: %s' % str(es))

    self.project._wrappedData.shiftAveraging = True
    # self._echoBlocking -= 1
    # self.project._undo.decreaseBlocking()

    return self.project

  def _loadSparkyProject(self, path:str, makeNewProject=True) -> Project:
    """Load Project from Sparky file at path, and do necessary setup"""

    from ccpn.core.lib.ContextManagers import undoBlock

    # read data files
    from ccpn.core.lib.CcpnSparkyIo import SPARKY_NAME

    dataBlock = self.sparkyReader.parseSparkyFile(path)
    sparkyName = dataBlock.getDataValues(SPARKY_NAME, firstOnly=True)

    if makeNewProject and (dataBlock.getDataValues('sparky', firstOnly=True) == 'project file'):
      if self.project is not None:
        self._closeProject()
      self.project = self.newProject(sparkyName)

    # self._echoBlocking += 1
    # self.project._undo.increaseBlocking()

    with undoBlock(self):
      try:
        # insert file into project

        self.sparkyReader.importSparkyProject(self.project, dataBlock)
        sys.stderr.write('==> Loaded Sparky project files: "%s", building project\n' % (path,))
      except Exception as es:
        getLogger().warning('Error loading Sparky file: %s' % str(es))

    self.project._wrappedData.shiftAveraging = True
    # self._echoBlocking -= 1
    # self.project._undo.decreaseBlocking()

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

  def _cloneSpectraToProjectDir(self):
    ''' Keep a copy of spectra inside the project directory "myproject.ccpn/data/spectra".
    This is useful when saving the project in an external driver and want to keep the spectra together with the project.
    '''
    from shutil import copyfile
    try:
      for spectrum in self.project.spectra:
        oldPath = spectrum.filePath
        # For Bruker need to keep all the tree structure.
        # Uses the fact that there is a folder called "pdata" and start to copy from the dir before.
        ss = oldPath.split('/')
        if 'pdata' in ss:
          brukerDir = os.path.join(os.sep, *ss[:ss.index('pdata')])
          brukerName = brukerDir.split('/')[-1]
          os.mkdir(os.path.join(self.spectraPath, brukerName))
          destinationPath = os.path.join(self.spectraPath, brukerName)
          copy_tree(brukerDir, destinationPath)
          clonedPath = os.path.join(destinationPath, *ss[ss.index('pdata'):])
          # needs to repoint the path but doesn't seem to work!! troubles with $INSIDE!!
          # spectrum.filePath = clonedPath
        else:
          # copy the file and or other files containing params
          from ntpath import basename
          pathWithoutFileName = os.path.join(os.sep, *ss[:ss.index(basename(oldPath))])
          fullpath = os.path.join(pathWithoutFileName, basename(oldPath))
          import glob
          otherFilesWithSameName = glob.glob(fullpath+".*")
          clonedPath = os.path.join(self.spectraPath, basename(oldPath))
          for otherFileTocopy in otherFilesWithSameName:
            otherFilePath = os.path.join(self.spectraPath, basename(otherFileTocopy))
            copyfile(otherFileTocopy, otherFilePath)
          if oldPath != clonedPath:
            copyfile(oldPath,clonedPath)
            # needs to repoint the path but doesn't seem to work!! troubles with $INSIDE!!
            # spectrum.filePath = clonedPath

    except Exception as e:
      getLogger().debug(str(e))

  def _saveProject(self, newPath=None, createFallback=True, overwriteExisting=True) -> bool:
    """Save project to newPath and return True if successful"""
    if self.preferences.general.keepSpectraInsideProject:
      self._cloneSpectraToProjectDir()

    successful = self.project.save(newPath=newPath, createFallback=createFallback,
                                   overwriteExisting=overwriteExisting)
    if not successful:
      sys.stderr.write('==> Project save failed\n')
      # NBNB TODO Gui should pre-check newPath and/or pop up something in case of failure

    else:
      self.ui.mainWindow._updateWindowTitle()
      self.ui.mainWindow.getMenuAction('Project->Archive').setEnabled(True)
      self.ui.mainWindow._fillRecentProjectsMenu()
      # self._createApplicationPaths()
      self.current._dumpStateToFile(self.statePath)
      try:
        if self.preferences.general.autoSaveLayoutOnQuit:
          Layout.saveLayoutToJson(self.ui.mainWindow)
      except Exception as e:
        getLogger().warning('Impossible to save Layout %s' % e)

      # saveIconPath = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'), 'icons', 'save.png')
      sys.stderr.write('==> Project successfully saved\n')
      # MessageDialog.showMessage('Project saved', 'Project successfully saved!',
      #                            iconPath=saveIconPath)


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
    """
    Export the current project as a Nef file
    Temporary routine because I don't know how else to do it yet
    """
    from ccpn.ui.gui.popups.ExportNefPopup import ExportNefPopup

    dialog = ExportNefPopup(self.ui.mainWindow,
                             mainWindow=self.ui.mainWindow,
                             fileMode=FileDialog.AnyFile,
                             text="Export to Nef File",
                             acceptMode=FileDialog.AcceptSave,
                             preferences=self.preferences.general,
                             selectFile=self.project.name+'.nef',     # new flag to populate dialog,
                             filter='*.nef')

    # an exclusion list comes out of the dialog as it
    result = dialog.exec_()

    if not result:
      return

    nefPath = result['filename']
    flags = result['flags']
    pidList = result['pidList']

    # flags are skipPrefixes, expandSelection
    skipPrefixes = flags['skipPrefixes']
    expandSelection = flags['expandSelection']

    self.project.exportNef(nefPath,
                    overwriteExisting=True,
                    skipPrefixes=skipPrefixes,
                    expandSelection=expandSelection,
                    pidList=pidList)

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
    newPath = getSaveDirectory(self.ui.mainWindow, self.preferences.general)
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

        expandedState = self.ui.mainWindow.sideBar._saveExpandedState()
        self.project._undo.undo()
        self.ui.mainWindow.sideBar._restoreExpandedState(expandedState)

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

        expandedState = self.ui.mainWindow.sideBar._saveExpandedState()
        self.project._undo.redo()
        self.ui.mainWindow.sideBar._restoreExpandedState(expandedState)

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
      popup = ProjectSummaryPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, modal=True)
      popup.show()
      popup.raise_()
      popup.exec_()

  def archiveProject(self):

    project = self.project
    apiProject = project._wrappedData.parent
    fileName = apiIo.packageProject(apiProject, includeBackups=True, includeLogs=True,
                                    includeArchives=False, includeSummaries=True)

    MessageDialog.showInfo('Project Archived',
                           'Project archived to %s' % fileName,)

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

    PreferencesPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, preferences=self.preferences).exec_()

  def getSavedLayoutPath(self):
    """Opens a saved Layout as dialog box and gets directory specified in the file dialog."""

    fType = 'JSON (*.json)'
    dialog = FileDialog(fileMode=FileDialog.AnyFile, text='Open Saved Layout',
                        acceptMode=FileDialog.AcceptOpen,filter=fType )
    path = dialog.selectedFile()
    if not path:
      return
    if path:
      return path

  def getSaveLayoutPath(self):
    """Opens save Layout as dialog box and gets directory specified in the file dialog."""
    jsonType = '.json'
    fType = 'JSON (*.json)'
    dialog = FileDialog(fileMode=FileDialog.AnyFile, text='Save Layout As',
                        acceptMode=FileDialog.AcceptSave,filter=fType )
    newPath = dialog.selectedFile()
    if not newPath:
      return
    if newPath:

      if os.path.exists(newPath):
        # should not really need to check the second and third condition above, only
        # the Qt dialog stupidly insists a directory exists before you can select it
        # so if it exists but is empty then don't bother asking the question
        title = 'Overwrite path'
        msg = 'Path "%s" already exists, continue?' % newPath
        if not MessageDialog.showYesNo(title, msg):
          newPath = ''
      if not newPath.endswith(jsonType):
        newPath += jsonType
      return newPath

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
        QtWidgets.QApplication.quit()
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
      QtWidgets.QApplication.quit()
    else:
      if event:
        event.ignore()

  def _closeMainWindows(self):
    tempModules = self.ui.mainWindow.application.ccpnModules
    if len(tempModules) > 0:
      for tempModule in tempModules:
        getLogger().debug('closing module: %s' % tempModule)
        try:
          tempModule.close()
        except:
          # wrapped C/C++ object of type StripDisplay1d has been deleted
          pass

  def _closeExtraWindows(self):
    tempAreas = self.ui.mainWindow.moduleArea.tempAreas
    if len(tempAreas) > 0:
      for tempArea in tempAreas:
        getLogger().debug('closing external module: %s' % tempArea.window())
        try:
          tempArea.window().close()
        except:
          # wrapped C/C++ object of type StripDisplay1d has been deleted
          pass

  def _closeProject(self):
    """Close project and clean up - when opening another or quitting application"""

    # NB: this function must clan up both wrapper and ui/gui

    if self.ui.mainWindow:
      # ui/gui cleanup
      self._closeMainWindows()
      self._closeExtraWindows()
      self.ui.mainWindow.deleteLater()

    if self.project is not None:
      # Cleans up wrapper project, including graphics data objects (Window, Strip, etc.)
      self.project._close()
      self.project = None

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
      popup = SpectrumProjectionPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
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
      popup = ExperimentTypePopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
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
      popup = PickPeak1DPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
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
        popup = PeakFindPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
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
      popup = CopyPeakListPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
      popup.exec_()

  def showCopyPeaks(self):
    if not self.project.peakLists:
      getLogger().warning('Project has no Peak Lists. Peak Lists cannot be copied')
      MessageDialog.showWarning('Project has no Peak Lists.', 'Peak Lists cannot be copied')
      return
    else:
      from ccpn.ui.gui.popups.CopyPeaksPopup import CopyPeaks
      popup = CopyPeaks(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow)
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
    popup = CreateChainPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow).exec_()


  def toggleSequenceModule(self):
    """Toggles whether Sequence Module is displayed or not"""
    from ccpn.ui.gui.modules.SequenceModule import SequenceModule

    # openList = [m for m in SequenceModule.getInstances()]
    # if openList:
    #   openList[0].close()
    #   # SequenceModule._alreadyOpened = False
    # # if SequenceModule._alreadyOpened is True:
    # #   if SequenceModule._currentModule is not None:
    # #     SequenceModule._currentModule.close()
    # #     SequenceModule._alreadyOpened = False
    # else:
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

      # set the colours of the currently highlighted chain in open sequenceGraph
      # should really be in the class, but doesn't fire correctly during __init__
      self.sequenceModule.populateFromSequenceGraphs()

    return self.sequenceModule


  def hideSequenceModule(self):
    """Hides sequence module"""

    if hasattr(self, 'sequenceModule'):
      self.sequenceModule.close()
      delattr(self, 'sequenceModule')

  def inspectMolecule(self):
    pass

  def showResidueInformation(self, position: str='bottom', relativeTo:CcpnModule=None):
    """Displays Residue Information module.
    """
    from ccpn.ui.gui.modules.ResidueInformation import ResidueInformation
    if not self.project.residues:
      getLogger().warning('No Residues in project. Residue Information Module requires Residues in the project to launch.')
      MessageDialog.showWarning('No Residues in project.',
                                'Residue Information Module requires Residues in the project to launch.')
      return

    mainWindow = self.ui.mainWindow
    if not relativeTo:
      relativeTo = mainWindow.moduleArea    # ejb
    self.residueModule = ResidueInformation(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(self.residueModule, position=position, relativeTo=relativeTo)
    mainWindow.pythonConsole.writeConsoleCommand("application.showResidueInformation()")
    getLogger().info("application.showResidueInformation()")

  def showRefChemicalShifts(self):
    """Displays Reference Chemical Shifts module."""
    from ccpn.ui.gui.modules.ReferenceChemicalShifts import ReferenceChemicalShifts
    self.refChemShifts = ReferenceChemicalShifts(mainWindow=self.ui.mainWindow)
    self.ui.mainWindow.moduleArea.addModule(self.refChemShifts)

  ###################################################################################################################
  ## MENU callbacks:  VIEW
  ###################################################################################################################

  def showChemicalShiftTable(self,
                              position:str='bottom',
                              relativeTo:CcpnModule=None,
                              chemicalShiftList=None):
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
    mainWindow.pythonConsole.writeConsoleCommand("application.showChemicalShiftTable()")
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
    mainWindow.pythonConsole.writeConsoleCommand("application.showNmrResidueTable()")
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
  #   mainWindow.pythonConsole.writeConsoleCommand("application.showStructureTable()")
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
    mainWindow.pythonConsole.writeConsoleCommand("application.showPeakTable()")
    getLogger().info("application.showPeakTable()")
    return  self.peakTableModule

  def showMultipletTable(self, position:str='left', relativeTo:CcpnModule=None, multipletList:MultipletList=None):
    """
    Displays multipletList table on left of main window with specified list selected.
    """
    from ccpn.ui.gui.modules.MultipletListTable import MultipletTableModule

    mainWindow = self.ui.mainWindow
    if not relativeTo:
      relativeTo = mainWindow.moduleArea      # ejb
    self.multipletTableModule = MultipletTableModule(mainWindow, multipletList=multipletList)
    mainWindow.moduleArea.addModule(self.multipletTableModule, position=position, relativeTo=relativeTo)
    mainWindow.pythonConsole.writeConsoleCommand("application.showMultipletTable()")
    getLogger().info("application.showMultipletTable()")
    return  self.multipletTableModule

  def showIntegralTable(self, position:str='left', relativeTo:CcpnModule=None, integralList:IntegralList=None):
    """
    Displays integral table on left of main window with specified list selected.
    """
    from ccpn.ui.gui.modules.IntegralTable import IntegralTableModule

    mainWindow = self.ui.mainWindow
    if not relativeTo:
      relativeTo = mainWindow.moduleArea      # ejb
    self.integralTableModule = IntegralTableModule(mainWindow=mainWindow, integralList=integralList)
    mainWindow.moduleArea.addModule(self.integralTableModule, position=position, relativeTo=relativeTo)
    mainWindow.pythonConsole.writeConsoleCommand("application.showIntegralTable()")
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
    mainWindow.pythonConsole.writeConsoleCommand("application.showRestraintTable()")
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

    mainWindow.pythonConsole.writeConsoleCommand("application.showStructureTable()")
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
    mainWindow.pythonConsole.writeConsoleCommand("application.showNotesEditorTable()")
    getLogger().info("application.showNotesEditorTable()")
    return self.notesEditorModule

  def showPrintSpectrumDisplayPopup(self):
    # from ccpn.ui.gui.popups.PrintSpectrumPopup import SelectSpectrumDisplayPopup #,PrintSpectrumDisplayPopup

    from ccpn.ui.gui.popups.ExportStripToFile import ExportStripToFilePopup
    if len(self.project.spectrumDisplays) == 0:
      MessageDialog.showWarning('', 'No Spectrum Display found')
    else:
      exportDialog = ExportStripToFilePopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow, strips=self.project.strips)
      exportDialog.exec_()

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

  def _setZoomPopup(self):
    if self.current.strip is not None:
      self.current.strip._setZoomPopup()
    else:
      getLogger().warning('No strip selected')

  def resetZoom(self):
    if self.current.strip is not None:
      self.current.strip.resetZoom()
    else:
      getLogger().warning('No strip selected')

  def copyStrip(self):
    if self.current.strip is not None:
      with suspendSideBarNotifications(self.project, "getByPid('%s').copyStrip" % self.current.strip.pid, quiet=False):
        self.current.strip.copyStrip()
    else:
      getLogger().warning('No strip selected')

  def flipXYAxis(self):
    if self.current.strip is not None:
      with suspendSideBarNotifications(self.project, "getByPid('%s').flipXYAxis" % self.current.strip.pid, quiet=False):
        self.current.strip.flipXYAxis()
    else:
      getLogger().warning('No strip selected')

  def flipXZAxis(self):
    if self.current.strip is not None:
      with suspendSideBarNotifications(self.project, "getByPid('%s').flipXZAxis" % self.current.strip.pid, quiet=False):
        self.current.strip.flipXZAxis()
    else:
      getLogger().warning('No strip selected')

  def flipYZAxis(self):
    if self.current.strip is not None:
      with suspendSideBarNotifications(self.project, "getByPid('%s').flipYZAxis" % self.current.strip.pid, quiet=False):
        self.current.strip.flipYZAxis()
    else:
      getLogger().warning('No strip selected')

  def _findMenuAction(self, menubarText, menuText):
    # not sure if this function will be needed more widely or just in console context
    # CCPN internal: now also used in SequenceModule._closeModule

    #GWV should not be here; moved to GuiMainWindow
    self.ui.mainWindow._findMenuAction(menubarText, menuText)

    #
    # for menuBarAction in self.ui.mainWindow._menuBar.actions():
    #   if menuBarAction.text() == menubarText:
    #     break
    # else:
    #   return None
    #
    # for menuAction in menuBarAction.menu().actions():
    #   if menuAction.text() == menuText:
    #     return menuAction
    #
    # return None

  def _toggleConsole(self):
    """
    Toggles whether python console is displayed at bottom of the main window.
    """

    self.ui.mainWindow.toggleConsole()


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

  def openMacroOnEditor(self):
    """
    Displays macro editor.
    """
    mainWindow = self.ui.mainWindow
    self.editor = MacroEditor(mainWindow=mainWindow)
    mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)
    self.editor._openMacroFile()
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

  # FIXME:ED - haven't checked this properly. Broken
  # def newMacroFromLog(self):
  #   """
  #   Displays macro editor with contents of the log.
  #   """
  #   # editor = MacroEditor(self.ui.mainWindow.moduleArea, self, "Macro Editor")
  #   #FIXME:ED - haven't checked this properly
  #   mainWindow = self.ui.mainWindow
  #   self.editor = MacroEditor(mainWindow=mainWindow)
  #
  #   l = open(getLogger().logPath, 'r').readlines()
  #   text = ''.join([line.strip().split(':', 6)[-1] + '\n' for line in l])
  #   self.editor.textBox.setText(text)
  #   mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)

  # This has never worked. Removed from menus
  # def startMacroRecord(self):
  #   """
  #   Displays macro editor with additional buttons for recording a macro.
  #   """
  #   mainWindow = self.ui.mainWindow
  #   self.editor = MacroEditor(mainWindow=mainWindow, showRecordButtons=True)
  #   mainWindow.moduleArea.addModule(self.editor, position='top', relativeTo=mainWindow.moduleArea)
  #   self.ui.mainWindow.pythonConsole.writeConsoleCommand("application.startMacroRecord()")
  #   getLogger().info("application.startMacroRecord()")


  def defineUserShortcuts(self):

    from ccpn.ui.gui.popups.ShortcutsPopup import ShortcutsPopup
    ShortcutsPopup(parent=self.ui.mainWindow, mainWindow=self.ui.mainWindow).exec_()

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

    mainWindow = self.ui.mainWindow

    if self.preferences.general.useNativeWebbrowser:
      self._systemOpen(path)
    else:
      from ccpn.ui.gui.widgets.CcpnWebView import CcpnWebView

      self.newModule = CcpnWebView(mainWindow=mainWindow, name=title, urlPath=path)

      # self.newModule = CcpnModule(mainWindow=mainWindow, name=title)
      # view = CcpnWebView(path)
      # self.newModule.addWidget(view, 0, 0, 1, 1)      # make it the first item
      # self.newModule.mainWidget = view      # ejb

      self.ui.mainWindow.moduleArea.addModule(self.newModule, position='top', relativeTo=mainWindow.moduleArea)

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
    popup = AboutPopup(parent=self.ui.mainWindow)
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

def getSaveDirectory(parent, preferences=None):
  """Opens save Project as dialog box and gets directory specified in the file dialog."""

  dialog = FileDialog(parent=parent, fileMode=FileDialog.AnyFile, text='Save Project As',
                      acceptMode=FileDialog.AcceptSave, preferences=preferences,
                      restrictDirToFilter=False)
  newPath = dialog.selectedFile()
  if not newPath:
    return
  if newPath:

    # native dialog returns a tuple: (path, ''); ccpn returns a string
    if isinstance(newPath, tuple):
      newPath = newPath[0]
      if not newPath:
        return None

    newPath = apiIo.addCcpnDirectorySuffix(newPath)
    if os.path.exists(newPath) and (os.path.isfile(newPath) or os.listdir(newPath)):
      # should not really need to check the second and third condition above, only
      # the Qt dialog stupidly insists a directory exists before you can select it
      # so if it exists but is empty then don't bother asking the question
      title = 'Overwrite path'
      msg = 'Path "%s" already exists, continue?' % newPath
      if not MessageDialog.showYesNo(title, msg):
        newPath = ''

    return newPath

########

def getPreferences(skipUserPreferences=False, defaultPath=None, userPath=None):
  from ccpn.framework.PathsAndUrls import defaultPreferencesPath
  try:
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
  except: #should we have the preferences hard coded as py dict for extra safety? if json goes wrong the whole project crashes!
    with open(defaultPreferencesPath) as fp:
      preferences = json.load(fp, object_hook=AttrDict)

  return preferences
