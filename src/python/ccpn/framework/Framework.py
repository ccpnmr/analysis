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

from ccpn.core.Project import Project
from ccpnmodel.ccpncore.lib.Io import Api as apiIo
from ccpnmodel.ccpncore.memops.metamodel import Util as metaUtil
from ccpnmodel.ccpncore.api.memops import Implementation

from ccpn.ui.gui.Current import Current

from ccpn.util import Path
from ccpn.util.AttrDict import AttrDict
from ccpn.util import Register

from ccpn.core.lib.Version import applicationVersion
from ccpn.core.lib import Io as coreIo

from ccpn.framework.Translation import translator
from ccpn.framework.Translation import languages, defaultLanguage

from ccpn.ui import interfaces, defaultInterface

_DEBUG = True

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

    # GuiBase.__init__(self, self) # yuk, two selfs, but it is that

    self.args = args
    self.applicationName = applicationName
    self.applicationVersion = applicationVersion

    printCreditsText(sys.stderr, applicationName, applicationVersion)

    self.setupComponents(args)

    self.useFileLogger = not self.args.nologging

    self.current = None

    self.preferences = None
    self.styleSheet = None

    self.ui = None  # No gui app so far

    # Necessary as attribute is queried during initialisation:
    self.mainWindow = None

    # This is needed to make project available in NoUi (if nothing else)
    self.project = None


    # NBNB TODO The following block should maybe be moved into _setupUI
    self._getUserPrefs()
    self.registrationDict = Register.loadDict()
    self._setLanguage()
    self.styleSheet = self.getStyleSheet(self.preferences)

    # Currently, we have to have a GUI running for the wrapper to create GuiMainWindow.
    self.ui = self._setupUI()


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
    if self.ui is None:
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
    if self.args.interface == 'Gui':
      from ccpn.ui.gui.Gui import Gui
      ui = Gui(self)
    else:
      from ccpn.ui.NoUi import NoUi
      ui = NoUi(self)
    return ui


  def start(self):
    """Start the program execution"""

    # L:oad / create uninitialised project
    projectPath =  self.args.projectPath
    if projectPath:
      sys.stderr.write('==> Loading "%s" initial project\n' % projectPath)
      projectPath = os.path.normpath(projectPath)
      project = coreIo._loadProject(projectPath)

    else:
      sys.stderr.write('==> Creating new, empty project\n')
      project = coreIo._newProject(name='default')

    # Connect UI classes for chosen ui
    self.ui.setUp()

    self.project = project

    # Initialise project, wrapping to underlying data using selected ui
    self._initialiseProject(project)

    sys.stderr.write('==> Done, %s is starting\n' % self.applicationName )

    # TODO: Add back in registration ???

    self.ui.start()

    project._resetUndo(debug=_DEBUG)


  def _initialiseProject(self, project:Project):
    """Initialise project and set up links and objects that involve it"""

    # Set up current
    self.current = Current(project=project)

    # Adapt API level project
    project._wrappedData.initialiseGraphicsData()
    self.applyPreferences(project)

    # NBNB TODO THIS IS A BAD HACK - refactor!!!
    project._appBase = self

    # This wraps the underlying data, including the wrapped graphics data
    #  - the project is now ready to use
    project._initialiseProject()
    #
    # # Set up mainWindow
    # self._setupMainWindow(project)
    #
    # self.initGraphics()

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


  def _closeProject(self):
    """Close project and clean up - when opening another or quitting application"""

    # NB: this function must clan up both wrapper and ui/gui

    if self.current and self.current._project is not None:
      # Cleans up wrapper project, including graphics data objects (Window, Strip, etc.)
      self.current._project._close()
    if self.mainWindow:
      # ui/gui cleanup
      self.mainWindow.deleteLater()
    self.mainWindow = None
    self.current = None


  def loadProject(self, path):
    """Open new project from path"""
    # TODO: convert this to  self.project.load() RHF: Reconsider?

    # NB _closeProject includes a gui cleanup call

    self._closeProject()

    sys.stderr.write('==> Loading "%s" project\n' % path)
    path = os.path.normpath(path)
    project = coreIo._loadProject(path)

    self._initialiseProject(project)

    project._resetUndo(debug=_DEBUG)

    return project


  def newProject(self, name='default'):
    # """Create new, empty project"""

    # NB _closeProject includes a gui cleanup call

    self._closeProject()
    sys.stderr.write('==> Creating new, empty project\n')
    project = coreIo._newProject(name=name)

    self._initialiseProject(project)

    project._resetUndo(debug=_DEBUG)

    return project


  def saveProject(self, newPath=None, newProjectName=None, createFallback=True):
    # TODO: convert this to a save and call self.project.save()
    pass
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

    sys.stderr.write('==> Project successfully saved\n')
    # MessageDialog.showMessage('Project saved', 'Project successfully saved!',
    #                           colourScheme=self.preferences.general.colourScheme, iconPath=saveIconPath)
###################################


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



# def getStyleSheet(preferences):
#
#   colourScheme = preferences.general.colourScheme
#   colourScheme = metaUtil.upperFirst(colourScheme)
#
#   styleSheet = open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
#                                  '%sStyleSheet.qss' % colourScheme)).read()
#   if platform.system() == 'Linux':
#     additions = open(os.path.join(Path.getPathToImport('ccpn.ui.gui.widgets'),
#                                   '%sAdditionsLinux.qss' % colourScheme)).read()
#     styleSheet += additions
#   return styleSheet
#
#
#
#
# def getSaveDirectory(apiProject, preferences):
#   """Opens save Project as dialog box and gets directory specified in the file dialog."""
#   preferences = getPreferences()
#   dialog = QtGui.QFileDialog(caption='Save Project As...')
#   dialog.setFileMode(QtGui.QFileDialog.AnyFile)
#   dialog.setAcceptMode(1)
#   if preferences.general.colourScheme == 'dark':
#     dialog.setStyleSheet("""
#                         QFileDialog QWidget {
#                                             background-color: #2a3358;
#                                             color: #f7ffff;
#                                             }
#                         """)
#   elif preferences.general.colourScheme == 'light':
#     dialog.setStyleSheet("QFileDialog QWidget {color: #464e76; }")
#
#   if not dialog.exec_():
#     return ''
#   fileNames = dialog.selectedFiles()
#   if not fileNames:
#     return ''
#   newPath = fileNames[0]
#   if newPath:
#     newPath = apiIo.ccpnProjectPath(newPath)
#     if os.path.exists(newPath) and (os.path.isfile(newPath) or os.listdir(newPath)):
#       # should not really need to check the second and third condition above, only
#       # the Qt dialog stupidly insists a directory exists before you can select it
#       # so if it exists but is empty then don't bother asking the question
#       title = 'Overwrite path'
#       msg ='Path "%s" already exists, continue?' % newPath
#       if not MessageDialog.showYesNo(title, msg, colourScheme=preferences.general.colourScheme):
#         newPath = ''
#
#   return newPath
#
#
# def saveV2ToV3(apiProject, projectPath, preferences):
#
#   projectPath = apiIo.ccpnProjectPath(projectPath)
#
#   needNewDirectory = False
#   if os.path.exists(projectPath) and (os.path.isfile(projectPath) or os.listdir(projectPath)):
#     # should not really need to check the second and third condition above, only
#     # the Qt dialog stupidly insists a directory exists before you can select it
#     # so if it exists but is empty then don't bother asking the question
#     title = 'Overwrite path'
#     msg ='Converting to V3 format, path "%s" already exists, overwrite?' % projectPath
#     if not MessageDialog.showYesNo(title, msg, colourScheme=preferences.general.colourScheme):
#       needNewDirectory = True
#
#   if not needNewDirectory:
#     try:
#       apiIo.saveProject(apiProject, newPath=projectPath)
#       MessageDialog.showMessage('Project save', 'Project saved in v3 format at %s' % projectPath,
#                                 colourScheme=preferences.general.colourScheme)
#     except IOError as e:
#       needNewDirectory = True
#       MessageDialog.showMessage('Project save', 'Project could not be saved in V3 format at %s' % projectPath,
#                                 colourScheme=preferences.general.colourScheme)
#
#   if needNewDirectory:
#     projectPath = getSaveDirectory(apiProject, preferences)
#     if projectPath:
#       try:
#         apiIo.saveProject(apiProject, newPath=projectPath, overwriteExisting=True)
#       except IOError as e:
#         MessageDialog.showMessage('Project save', 'Project could not be saved in V3 format at %s, quitting' % projectPath,
#                                   colourScheme=preferences.general.colourScheme)
#         projectPath = ''
#
#   return projectPath
#
#
# class TestApplication(Framework):
#
#   def __init__(self,commandLineArguments):
#
#     AppBase.__init__(self, 'testApplication', '1.0',commandLineArguments)
#
# if __name__ == '__main__':
#
#   parser = defineProgramArguments()
#   commandLineArguments = parser.parse_args()
#   program = TestApplication(commandLineArguments)
#   program.start()
#
#   # splash = SplashScreen()
#   #
#   # app.processEvents()
#   # w = QtGui.QWidget()
#   # w.resize(250, 150)
#   # w.move(300, 300)
#   # w.setWindowTitle('testApplication')
#   # w.show()
#   # #splash = showSplashScreen()
#   # print(splash)
#   # splash.info('test')
#   # app.processEvents()























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
