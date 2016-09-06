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
    self.namespace['runMacro'] = self.pythonConsole._runMacro

    msg = path + (' created' if isNew else ' opened')
    self.statusBar().showMessage(msg)
    msg2 = 'project = %sProject("%s")' % (('new' if isNew else 'open'), path)
    self.pythonConsole.writeConsoleCommand(msg2)

    self.colourScheme = self._appBase.preferences.general.colourScheme
    self._appBase._updateRecentFiles()
    self.pythonConsole.setProject(project)
    self._updateWindowTitle()


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
    

  def loadProject(self, projectDir=None):
    """
    Opens a loadProject dialog box if project directory is not specified.
    Loads the selected project.
    """
    result = self._queryCloseProject(title='Open Project', phrase='open another')
    if result:
      if projectDir is None:
        dialog = FileDialog(self, fileMode=FileDialog.Directory, text="Open Project",
                            acceptMode=FileDialog.AcceptOpen, preferences=self._appBase.preferences.general)
        projectDir = dialog.selectedFile()

      if projectDir:
        self.application.loadProject(projectDir)



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


  def _fillMacrosMenu(self):
    """
    Populates recent macros menu with last ten macros ran.
    TODO: make sure that running a macro adds it to the prefs and calls this function
    """

    runMacrosMenu = self.getMenuAction('Macro->Run')
    runMacrosMenu.clear()

    from ccpn.framework.PathsAndUrls import macroPath as ccpnMacroPath

    try:
      ccpnMacros = os.listdir(ccpnMacroPath)
      ccpnMacros = [f for f in ccpnMacros if
                    os.path.isfile(os.path.join(ccpnMacroPath, f))]
      ccpnMacros = [f for f in ccpnMacros if f.split('.')[-1] == 'py']
      ccpnMacros = [f for f in ccpnMacros if not f.startswith('.')]
      ccpnMacros = [f for f in ccpnMacros if not f.startswith('_')]
      ccpnMacros = sorted(ccpnMacros)

      for macro in ccpnMacros:
        action = Action(self, text=macro, translate=False,
                        callback=partial(self.runMacro,
                                         macroFile=os.path.join(ccpnMacroPath, macro)))
        runMacrosMenu.addAction(action)
      if len(ccpnMacros) > 0:
        runMacrosMenu.addSeparator()
    except FileNotFoundError:
      pass

    try:
      userMacroPath = os.path.expanduser(self.application.preferences.general.userMacroPath)
      userMacros = os.listdir(userMacroPath)
      userMacros = [f for f in userMacros if
                    os.path.isfile(os.path.join(userMacroPath, f))]
      userMacros = [f for f in userMacros if f.split('.')[-1] == 'py']
      userMacros = [f for f in userMacros if not f.startswith('.')]
      userMacros = [f for f in userMacros if not f.startswith('_')]
      userMacros = sorted(userMacros)

      for macro in userMacros:
          action = Action(self, text=macro, translate=False,
                          callback=partial(self.runMacro,
                                           macroFile=os.path.join(userMacroPath, macro)))
          runMacrosMenu.addAction(action)
      if len(userMacros) > 0:
        runMacrosMenu.addSeparator()
    except FileNotFoundError:
      pass

    runMacrosMenu.addAction(Action(runMacrosMenu, text='Refresh',
                                    callback=self._fillMacrosMenu))
    runMacrosMenu.addAction(Action(runMacrosMenu, text='Browse...',
                                    callback=self.runMacro))


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
      self._appBase.saveProject()
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


  def newMacroFromLog(self):
    """
    Displays macro editor with contents of the log.
    """
    editor = MacroEditor(self.moduleArea, self, "Macro Editor")
    l = open(self.project._logger.logPath, 'r').readlines()
    text = ''.join([line.strip().split(':', 6)[-1]+'\n' for line in l])
    editor.textBox.setText(text)


  # the below is in Framework (slightly different implementation) so presumably does not belong here???
  def runMacro(self, macroFile:str=None):
    """
    Runs a macro if a macro is specified, or opens a dialog box for selection of a macro file and then
    runs the selected macro.
    """
    if macroFile is None:
      dialog = FileDialog(self, fileMode=FileDialog.ExistingFile, text="Run Macro",
                          acceptMode=FileDialog.AcceptOpen, preferences=self._appBase.preferences.general)
      if os.path.exists(self._appBase.preferences.general.userMacroPath):
        dialog.setDirectory(self._appBase.preferences.general.userMacroPath)
      macroFile = dialog.selectedFile()
      if not macroFile:
        return

    if os.path.isfile(macroFile):
      self.application.preferences.recentMacros.append(macroFile)
      self._fillRecentMacrosMenu()
      self.pythonConsole._runMacro(macroFile)


  def _resetRemoveStripAction(self, strips):
    for spectrumDisplay in self.spectrumDisplays:
      spectrumDisplay._resetRemoveStripAction()
