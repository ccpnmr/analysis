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
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2016-05-16 17:45:50 +0100 (Mon, 16 May 2016) $"
__version__ = "$Revision: 9320 $"

#=========================================================================================
# Start of code
#=========================================================================================

import os
import sys
import json
import platform

from PyQt4 import QtGui, QtCore

from ccpn.core.Project import Project
from ccpn.ui.gui import _implementation # NB Neccessary to force load of graphics classes
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpn.ui.gui.widgets.Application import Application
from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil
from ccpnmodel.ccpncore.api.memops import Implementation
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.util import Path
from ccpn.util.AttrDict import AttrDict
from ccpn.util import Register

try:
  from ccpn.util.Translation import translator
  from ccpn.util.Translation import languages, defaultLanguage
except ImportError:
  from ccpn.framework.Translation import translator
  from ccpn.framework.Translation import languages, defaultLanguage


from ccpn.ui.gui.Base import Base as GuiBase
from ccpn.ui.gui.Current import Current
from ccpn.ui.gui.popups.RegisterPopup import RegisterPopup

# The following must be there even though the import is not used in this file.
# from ccpn.ui.gui.widgets import resources_rc

componentNames = ('Assignment', 'Screening', 'Structure')

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
                      help='Language for menus, etc.; valid options = (' + '|'.join(languages) + '); default='+defaultLanguage,
                      default=defaultLanguage)
  parser.add_argument('--skip-user-preferences', dest='skipUserPreferences', action='store_true',
                                                 help='Skip loading user preferences')
  parser.add_argument('--nologging', dest='nologging', action='store_true', help='Do not log information to a file')
  parser.add_argument('projectPath', nargs='?', help='Project path')

  return parser


class Framework:#
  """
  The Framework class is the base class for all applications
  It's currently broken, so don't use this if you want your application to actually work!
  """

  def __init__(self, applicationName, applicationVersion, args):

    GuiBase.__init__(self, self) # yuk, two selfs, but it is that

    self.args = args
    self.applicationName = applicationName
    self.applicationVersion = applicationVersion

    printCreditsText(sys.stderr, applicationName, applicationVersion)

    self.setupComponents(args)

    self.useFileLogger = not self.args.nologging

    self.current = None

    self.gui = None  # No gui app so far
    # Necessary as attribute is queried during initialisation:
    self.mainWindow = None

    self._getUserPrefs()

    self._setLanguage()

    # Currently, we have to have a GUI running for the wrapper to create GuiMainWindow.
    self.ui = self.gui = self._setupUI()



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


  def isRegistered(self):
    """return True if registered"""
    return True
    self.registrationDict = Register.loadDict()
    return not Register.isNewRegistration(self.registrationDict)


  def register(self):
    """
    Display registration popup if there is a gui
    return True on error
    """
    if self.gui is None:
        return True

    popup = RegisterPopup(version=self.applicationVersion, modal=True)
    popup.show()
    popup.raise_()
    popup.exec_()
    self.gui.processEvents()

    if not self.isRegistered():
      return True

    Register.updateServer(self.registrationDict, self.applicationVersion)
    return False


  def _setupUI(self):
    gui = Application(self.applicationName, self.applicationVersion, organizationName='CCPN', organizationDomain='ccpn.ac.uk')
    gui.setStyleSheet(getStyleSheet(self.preferences))
    return gui


  def start(self):
    """Start the program execution"""

    project = self.initProject()

    sys.stderr.write('==> Done, %s is starting\n' % self.applicationName )

    # Need to add back in registration

    self.gui.start()


  def initProject(self):
    # load user-specified project or default if not specified
    if self.args.projectPath:
      sys.stderr.write('==> Loading "%s" project\n' % self.args.projectPath)
      projectPath = os.path.normpath(self.args.projectPath)
      apiProject = apiIo.loadProject(projectPath, useFileLogger=self.useFileLogger)
      if not projectPath.endswith(apiIo.CCPN_DIRECTORY_SUFFIX):
        projectPath = saveV2ToV3(apiProject, projectPath, self.preferences)
        if not projectPath:
          return
        apiProject = apiIo.loadProject(projectPath, useFileLogger=self.useFileLogger)
    else:
      sys.stderr.write('==> Loading default project\n')
      apiProject = apiIo.newProject('default', useFileLogger=self.useFileLogger)

    # Reset remoteData DataStores to match preferences setting
    dataPath = self.preferences.general.dataPath
    if not dataPath or not os.path.isdir(dataPath):
      dataPath = os.path.expanduser('~')
    dataUrl = apiProject.root.findFirstDataLocationStore(name='standard').findFirstDataUrl(
      name='remoteData')
    dataUrl.url = Implementation.Url(path=dataPath)

    # ApiProject to appBase - Done this way to sneak the appBase in before creating the wrapper
    apiProject._appBase = self
    self.current = Current(project=None)

    # Make sure we have a WindowStore attached to the NmrProject - that guarantees a mainWindow
    apiNmrProject = apiProject.fetchNmrProject()
    apiWindowStore = apiNmrProject.windowStore
    if apiWindowStore is None:
      apiWindowStore = apiProject.findFirstWindowStore()
      if apiWindowStore is None:
        apiWindowStore = apiProject.newWindowStore(nmrProject=apiNmrProject)
      else:
        apiNmrProject.windowStore = apiWindowStore

    # Wrap ApiNmrProject
    project = Project(apiNmrProject)

    self.current._project = project

    mainWindow = self._setupMainWindow(project)

    # TODO: Don't know what this does, or if it's necessary.  Ask Rasmus,...
    # if not apiProject.findAllGuiTasks(nmrProject=project._wrappedData):
    #   apiGuiTask = apiProject.newGuiTask(name='View', nmrProject=project._wrappedData,
    #                                      windows=(mainWindow._wrappedData,))


    self.initGraphics()
    # Set up undo stack
    # The default values are as below. They can be changed if desired
    #project._resetUndo(maxWaypoints=20, maxOperations=10000)
    project._resetUndo(debug=True)
    #
    return project


  def _setupMainWindow(self, project):
    # Set up mainWindow (link is set from mainWindow init
    mainWindow = self.mainWindow
    mainWindow.sideBar.setProject(project)
    mainWindow.sideBar.fillSideBar(project)
    mainWindow.raise_()
    mainWindow.namespace['current'] = self.current
    return mainWindow


  def initGraphics(self):
    """Set up graphics system after loading - to be overridden in subclasses"""
    # for window in self.project.windows:
    #   window.initGraphics()
    pass


  def _closeProject(self):
    """Close project and clean up - should only be called when opening another"""

    # NBNB TBD add code to save first, ask, etc. Somewhere

    if self.project is not None:
      self.project._close()
      self.project = None
    if self.mainWindow:
      self.mainWindow.deleteLater()
    self.mainWindow = None
    self.current = None


  def loadProject(self, path):
    """Open new project from path"""
    self._closeProject()
    apiProject = apiIo.loadProject(path)
    return self.initProject(apiProject)


  def newProject(self, name='default'):
    """Create new, empty project"""
    self._closeProject()
    apiProject = apiIo.newProject(name)
    return self.initProject(apiProject)


  def saveProject(self, newPath=None, newProjectName=None, createFallback=True):
    apiIo.saveProject(self.project._wrappedData.root, newPath=newPath, newProjectName=newProjectName, createFallback=createFallback)
    layout = self.mainWindow.moduleArea.saveState()
    layoutPath = os.path.join(self.project.path, 'layouts')
    if not os.path.exists(layoutPath):
      os.makedirs(layoutPath)
    import yaml
    with open(os.path.join(layoutPath, "layout.yaml"), 'w') as stream:
      yaml.dump(layout, stream)
      stream.close()
    saveIconPath = os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'), 'icons', 'save.png')
    MessageDialog.showMessage('Project saved', 'Project successfully saved!',
                              colourScheme=self.preferences.general.colourScheme, iconPath=saveIconPath)



def getPreferences(skipUserPreferences=False, defaultPreferencesPath=None, userPreferencesPath=None):

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



def getStyleSheet(preferences):

  colourScheme = preferences.general.colourScheme
  colourScheme = metaUtil.upperFirst(colourScheme)

  styleSheet = open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                                 '%sStyleSheet.qss' % colourScheme)).read()
  if platform.system() == 'Linux':
    additions = open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
                                  '%sAdditionsLinux.qss' % colourScheme)).read()
    styleSheet += additions
  return styleSheet




def getSaveDirectory(apiProject, preferences):
  """Opens save Project as dialog box and gets directory specified in the file dialog."""
  preferences = getPreferences()
  dialog = QtGui.QFileDialog(caption='Save Project As...')
  dialog.setFileMode(QtGui.QFileDialog.AnyFile)
  dialog.setAcceptMode(1)
  if preferences.general.colourScheme == 'dark':
    dialog.setStyleSheet("""
                        QFileDialog QWidget {
                                            background-color: #2a3358;
                                            color: #f7ffff;
                                            }
                        """)
  elif preferences.general.colourScheme == 'light':
    dialog.setStyleSheet("QFileDialog QWidget {color: #464e76; }")

  if not dialog.exec_():
    return ''
  fileNames = dialog.selectedFiles()
  if not fileNames:
    return ''
  newPath = fileNames[0]
  if newPath:
    newPath = apiIo.ccpnProjectPath(newPath)
    if os.path.exists(newPath) and (os.path.isfile(newPath) or os.listdir(newPath)):
      # should not really need to check the second and third condition above, only
      # the Qt dialog stupidly insists a directory exists before you can select it
      # so if it exists but is empty then don't bother asking the question
      title = 'Overwrite path'
      msg ='Path "%s" already exists, continue?' % newPath
      if not MessageDialog.showYesNo(title, msg, colourScheme=preferences.general.colourScheme):
        newPath = ''

  return newPath









def saveV2ToV3(apiProject, projectPath, preferences):

  projectPath = apiIo.ccpnProjectPath(projectPath)

  needNewDirectory = False
  if os.path.exists(projectPath) and (os.path.isfile(projectPath) or os.listdir(projectPath)):
    # should not really need to check the second and third condition above, only
    # the Qt dialog stupidly insists a directory exists before you can select it
    # so if it exists but is empty then don't bother asking the question
    title = 'Overwrite path'
    msg ='Converting to V3 format, path "%s" already exists, overwrite?' % projectPath
    if not MessageDialog.showYesNo(title, msg, colourScheme=preferences.general.colourScheme):
      needNewDirectory = True

  if not needNewDirectory:
    try:
      apiIo.saveProject(apiProject, newPath=projectPath)
      MessageDialog.showMessage('Project save', 'Project saved in v3 format at %s' % projectPath,
                                colourScheme=preferences.general.colourScheme)
    except IOError as e:
      needNewDirectory = True
      MessageDialog.showMessage('Project save', 'Project could not be saved in V3 format at %s' % projectPath,
                                colourScheme=preferences.general.colourScheme)

  if needNewDirectory:
    projectPath = getSaveDirectory(apiProject, preferences)
    if projectPath:
      try:
        apiIo.saveProject(apiProject, newPath=projectPath, overwriteExisting=True)
      except IOError as e:
        MessageDialog.showMessage('Project save', 'Project could not be saved in V3 format at %s, quitting' % projectPath,
                                  colourScheme=preferences.general.colourScheme)
        projectPath = ''

  return projectPath


class TestApplication(Framework):

  def __init__(self,commandLineArguments):

    AppBase.__init__(self, 'testApplication', '1.0',commandLineArguments)

if __name__ == '__main__':

  parser = defineProgramArguments()
  commandLineArguments = parser.parse_args()
  program = TestApplication(commandLineArguments)
  program.start()

  # splash = SplashScreen()
  #
  # app.processEvents()
  # w = QtGui.QWidget()
  # w.resize(250, 150)
  # w.move(300, 300)
  # w.setWindowTitle('testApplication')
  # w.show()
  # #splash = showSplashScreen()
  # print(splash)
  # splash.info('test')
  # app.processEvents()























# import sys
# from ccpn.framework.Translation import Translation
#
# from ccpn.framework.Preferences import getDotfilePreferences, commandLineArguementParser
# from ccpn.framework.Settings import setupSettings
# from ccpn.util.Namespace import Namespace
# from ccpn.framework import Register
#
#
# class Framework:
#   '''
#   The parent class that all CCPN based applications should subclass.
#   '''
#
#   commandLineArguementParser = commandLineArguementParser()
#
#
#   def __init__(self, programName, programVersion, commandLineOptions):
#     self._options = commandLineOptions
#     self.settings = self._options
#
#     self.ui = self.getUI()  # We need to pass the UI on to the project for now
#     self.project = self.setupProject()
#     self.logger = self.getLogger()
#
#     self._preferences = self.loadPreferences()
#     self.settings = setupSettings(options=self._options, preferences=self._preferences)
#
#     self.current = None
#     self.translator = self.getTranslator()
#
#
#   @property
#   def registered(self):
#     self.registrationDict = Register.loadDict()
#     return not Register.isNewRegistration(self.registrationDict)
#   # TODO: How do we do a registration (AppBase line 192)?
#
#
#   def setupProject(self):
#     if 'projectPath' in self.options:
#       project = None
#     else:
#       project = None
#     return project
#
#
#   def loadPreferences(self):
#     if hasattr(self._options, 'skipUserPreferences'):
#       return Namespace()
#     preferences = Namespace.fromNestedDict(getDotfilePreferences())
#     preferences.flatten()
#     return preferences
#
#
#   def getTranslator(self):
#     language = self.settings.language
#     translator = Translation()
#     if not translator.setLanguage(language):
#       raise NotImplementedError('No translations available for {}.'.format(language))
#     sys.stderr.write('==> Language set to "%s"\n' % translator._language)
#     return translator
#
#
#   def getLogger(self):
#     if hasattr('noLogging', self.settings) and (not self.settings.noLogging):
#       return None
#     return self.project.logger
#
#
#   def getUI(self):
#     return None
#
#
#   def start(self):
#     pass
#
#
#   def save(self):
#     pass
#
#
#   def load(self):
#     pass
