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
__modifiedBy__ = "$modifiedBy: CCPN $"
__dateModified__ = "$dateModified: 2017-07-07 16:32:47 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b4 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from functools import reduce, partial

from PyQt5 import QtGui, QtWidgets

from ccpn.ui.gui.modules.CcpnModule import CcpnModule
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb
from ccpn.util.Logging import getLogger


class ShortcutsPopup(CcpnDialog):
  def __init__(self, parent=None, mainWindow=None, title='Define User Shortcuts', **kwds):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

    self.mainWindow = mainWindow
    self.application = self.mainWindow.application
    self.preferences = self.application.preferences

    # self.mainWindow.moduleArea.addModule(self)
    self.rowCount = 0
    # self.scrollArea = ScrollArea(self.mainWidget, grid=(0, 0), gridSpan=(1, 2))
    self.scrollArea = ScrollArea(self, grid=(0, 0), gridSpan=(1, 2), setLayout=True)   # ejb

    # self.shortcutWidget = ShortcutWidget(self, mainWindow)
    self.shortcutWidget = ShortcutWidget(mainWindow=mainWindow, setLayout=True)      # ejb
    self.scrollArea.setWidgetResizable(True)
    self.scrollArea.setWidget(self.shortcutWidget)
    self.buttonList = ButtonList(self, grid=(1, 1),
                                 texts=['Cancel', 'Save', 'Save and Close'],
                                 callbacks=[self.close, self.save, self.saveAndQuit])

    self.setStyleSheet('ScrollArea {background-color: #00092d}')
    self.setStyleSheet('ScrollArea > QWidget {background-color: #00092d}')

    self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
    self.setMinimumSize(400, 400)

    # self._sequenceGraphScrollArea.layout().addWidget(self.shortcutWidget)

  def save(self):
    newShortcuts = self.shortcutWidget.getShortcuts()
    self.preferences.shortcuts = newShortcuts
    if hasattr(self.application, '_userShortcuts') and self.application._userShortcuts:
      for shortcut in newShortcuts:
        self.application._userShortcuts.addUserShortcut(shortcut, newShortcuts[shortcut])

  def saveAndQuit(self):
    self.save()
    self.close()


class ShortcutWidget(ScrollableFrame):

  # def __init__(self, parent, mainWindow, **kwds):
  def __init__(self, mainWindow=None, setLayout=True):           # ejb
    ScrollableFrame.__init__(self, setLayout=setLayout)
    from functools import partial
    self.mainWindow = mainWindow
    self.application = self.mainWindow.application
    self.preferences = self.application.preferences

    i=0
    self.widgets = []
    for shortcut in sorted(self.preferences.shortcuts):
      shortcutLabel = Label(self, grid=(i, 0), text=shortcut)
      self.shortcutLineEdit = LineEdit(self, grid=(i, 1))
      self.shortcutLineEdit.setText(self.preferences.shortcuts[shortcut])
      self.shortcutLineEdit.editingFinished.connect(partial(self.validateFunction, i))
      pathButton = Button(self, grid=(i, 2), icon='icons/applications-system', callback=partial(self._getMacroFile, i))
      self.widgets.append([shortcutLabel, self.shortcutLineEdit, pathButton])
      i+=1


  def getShortcuts(self):
    shortcutDict = {}
    layout = self.layout()
    for i in range(layout.rowCount()):
      shortcut = layout.itemAtPosition(i, 0).widget().text()
      function = layout.itemAtPosition(i, 1).widget().text()
      shortcutDict[shortcut] = function
    return shortcutDict


  def _getMacroFile(self, index):
    shortcutLineEdit = self.widgets[index][1]
    if os.path.exists('/'.join(shortcutLineEdit.text().split('/')[:-1])):
      currentDirectory = '/'.join(shortcutLineEdit.text().split('/')[:-1])
    else:
      currentDirectory = os.path.expanduser(self.preferences.general.userMacroPath)
    dialog = FileDialog(self, text='Select Macro File', directory=currentDirectory,
                        fileMode=1, acceptMode=0,
                        preferences=self.preferences.general)
    directory = dialog.selectedFiles()
    if len(directory) > 0:
      shortcutLineEdit.setText('runMacro("%s")' % directory[0])


  def validateFunction(self, i):
    # check if function for shortcut is a .py file or exists in the CcpNmr V3 namespace
    path = self.widgets[i][1].text()
    namespace = self.mainWindow.namespace

    if path == '':
      return

    if path.startswith('/'):

      if os.path.exists(path) and path.split('/')[-1].endswith('.py'):
        print('pathValid')
        return True

      elif not os.path.exists(path) or not path.split('/')[-1].endswith('.py'):
        if not os.path.exists(path):
          showWarning('Invalid macro path', 'Macro path: %s is not a valid path' % path)
          return False

        if not path.split('/')[-1].endswith('.py'):
          showWarning('Invalid macro file', 'Macro files must be valid python files and end in .py' % path)
          return False

    else:
      stub = namespace.get(path.split('.')[0])
      if not stub:
        showWarning('Invalid function', 'Function: %s is not a valid CcpNmr function' % path)
        return False
      else:
        try:
          reduce(getattr, path.split('.')[1:], stub)
          return True
        except:
          showWarning('Invalid function', 'Function: %s is not a valid CcpNmr function' % path)
          return False


class UserShortcuts():
  def __init__(self, mainWindow=None):
    self.mainWindow = mainWindow
    self.namespace = self.mainWindow.namespace
    self._userShortcutFunctions={}
    self._numUserShortcutFunctions=0

  def addUserShortcut(self, funcName, funcStr):
    self._userShortcutFunctions[funcName] = funcStr

  def runUserShortcut(self, funcStr):
    if funcStr in self._userShortcutFunctions:
      function = self._userShortcutFunctions[funcStr]

      if funcStr and function:
        if function.split('(')[0] == 'runMacro':
          func = partial(self.namespace['runMacro'], function.split('(')[1].split(')')[0])
          if func:
            getLogger().info(function)
            try:
              func()
            except:
              getLogger().warning('Error executing macro: %s ' % function)

          # QtWidgets.QShortcut(QtGui.QKeySequence("%s, %s" % (shortcut[0], shortcut[1])),
          #                 self, partial(self.namespace['runMacro'], function.split('(')[1].split(')')[0]),
          #                 context=context)

        else:
          stub = self.namespace.get(function.split('.')[0])
          func = reduce(getattr, function.split('.')[1:], stub)
          if func:
            getLogger().info(function)
            try:
              func()
            except:
              getLogger().warning('Error executing user shortcut: %s ' % function)

          # QtWidgets.QShortcut(QtGui.QKeySequence("%s, %s" % (shortcut[0], shortcut[1])), self,
          #                 reduce(getattr, function.split('.')[1:], stub), context=context)
