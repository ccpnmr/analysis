"""
Module Documentation here
"""
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
__dateModified__ = "$dateModified: 2017-07-07 16:32:49 +0100 (Fri, July 07, 2017) $"
__version__ = "$Revision: 3.0.b2 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui
import os
from functools import partial
from ccpnmodel.ccpncore.api.memops import Implementation
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES
from ccpn.framework.Translation import languages
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets import MessageDialog

PulldownListsMinimumWidth = 200
LineEditsMinimumWidth = 195

class PreferencesPopup(CcpnDialog):
  def __init__(self, parent=None, preferences=None, project=None, title='Preferences', **kw):
    CcpnDialog.__init__(self, parent=parent, setLayout=True, windowTitle=title, size=(300, 300), **kw)

    if not project:                                         # ejb - should always be loaded
      MessageDialog.showWarning(title, 'No project loaded')
      self.close()
      return

    self.project = project
    self.preferences = preferences
    self.oldPreferences = preferences

    self.mainLayout = self.getLayout()
    self._setTabs()
    self._setWidgets()


  def _setTabs(self):

    ''' Creates the tabs as Frame Widget. All the children widgets will go in the Frame.
     Each frame will be the widgets parent. 
     Tabs are displayed by the order how appear here. '''

    self.tabWidget = QtGui.QTabWidget()

    ## 1 Tab
    self.appearanceTabFrame = Frame(self, setLayout=True, )
    self.tabWidget.addTab(self.appearanceTabFrame, 'Appearance')

    ## 2 Tab
    self.pathsTabFrame = Frame(self, setLayout=True)
    self.tabWidget.addTab(self.pathsTabFrame, 'Paths')

    ## 3 Tab
    self.miscellaneousTabFrame = Frame(self, setLayout=True)
    self.tabWidget.addTab(self.miscellaneousTabFrame, 'Miscellaneous')


  def _setWidgets(self):

    ''' sets all widgets:
        Tabs and Close button are in the mainLayout.
        All  other widgets are children contained in tabs (Frame)
    '''
    self._setPathsTabWidgets(parent=self.pathsTabFrame)
    self._setAppearanceTabWidgets(parent=self.appearanceTabFrame)
    self._setMiscellaneousTabWidgets(parent=self.miscellaneousTabFrame)

    buttonBox = Button(self.miscellaneousTabFrame, text='Close', callback=self.accept)
    self.mainLayout.addWidget(self.tabWidget, 0, 0, 1, 3)
    self.mainLayout.addWidget(buttonBox, 1, 2)


  def _setPathsTabWidgets(self, parent):
    ''' Insert a widget in here to appear in the Paths Tab  '''

    row = 0
    self.dataPathLabel = Label(parent, "Data Path", grid=(row, 0),)
    self.dataPathText = LineEdit(parent, grid=(row, 1), hAlign='l')
    self.dataPathText.setMinimumWidth(LineEditsMinimumWidth)
    self.dataPathText.editingFinished.connect(self._setDataPath)
    self.dataPathText.setText(self.preferences.general.dataPath)
    self.dataPathButton = Button(self.pathsTabFrame, grid=(row, 2), callback=self._getDataPath, icon='icons/directory', hPolicy='fixed')

    row += 1
    self.auxiliaryFilesLabel = Label(parent, text="Auxiliary Files Path ", grid=(row, 0))
    self.auxiliaryFilesData = LineEdit(parent, grid=(row, 1), hAlign='l')
    self.auxiliaryFilesData.setMinimumWidth(LineEditsMinimumWidth)
    self.auxiliaryFilesDataButton = Button(parent, grid=(row, 2), callback=self._getAuxiliaryFilesPath, icon='icons/directory', hPolicy='fixed')
    self.auxiliaryFilesData.setText(self.preferences.general.auxiliaryFilesPath)
    self.auxiliaryFilesData.editingFinished.connect(self._setAuxiliaryFilesPath)

    row += 1
    self.macroPathLabel = Label(parent, text="Macro Path", grid=(row, 0))
    self.macroPathData = LineEdit(parent, grid=(row, 1), hAlign='l')
    self.macroPathData.setMinimumWidth(LineEditsMinimumWidth)
    self.macroPathData.setText(self.preferences.general.userMacroPath)
    self.macroPathDataButton = Button(parent, grid=(row, 2), callback=self._getMacroFilesPath, icon='icons/directory', hPolicy='fixed')
    self.macroPathData.editingFinished.connect(self._setMacroFilesPath)

    row += 1
    self.pluginPathLabel = Label(parent, text="Plugin Path", grid=(row, 0))
    self.pluginPathData = LineEdit(parent, grid=(row, 1),hAlign='l')
    self.pluginPathData.setMinimumWidth(LineEditsMinimumWidth)
    self.pluginPathData.setText(self.preferences.general.userPluginPath)
    self.pluginPathDataButton = Button(parent, grid=(row, 2), callback=self._getPluginFilesPath, icon='icons/directory', hPolicy='fixed')
    self.pluginPathData.editingFinished.connect(self._setPluginFilesPath)

    row += 1
    self.extensionPathLabel = Label(parent, text="Extension Path", grid=(row, 0))
    self.extensionPathData = LineEdit(parent, grid=(row, 1), hAlign='l')
    self.extensionPathData.setMinimumWidth(LineEditsMinimumWidth)
    self.extensionPathData.setText(self.preferences.general.userExtensionPath)
    self.extensionPathDataButton = Button(parent, grid=(row, 2), callback=self._getExtensionFilesPath, icon='icons/directory', hPolicy='fixed')
    self.extensionPathData.editingFinished.connect(self._setExtensionFilesPath)


  def _setAppearanceTabWidgets(self, parent):
    ''' Insert a widget in here to appear in the Appearance Tab. Parent is the Frame obj where the widget should live'''

    row = 0
    self.languageLabel = Label(parent, text="Language", grid=(row, 0))
    self.languageBox = PulldownList(parent, grid=(row, 1), hAlign='l')
    self.languageBox.addItems(languages)
    self.languageBox.setMinimumWidth(PulldownListsMinimumWidth)
    self.languageBox.setCurrentIndex(self.languageBox.findText(self.preferences.general.language))
    self.languageBox.currentIndexChanged.connect(self._changeLanguage)

    row += 1
    self.colourSchemeLabel = Label(parent, text="Colour Scheme ", grid=(row, 0))
    self.colourSchemeBox = PulldownList(parent, grid=(row, 1), hAlign='l')
    self.colourSchemeBox.setMinimumWidth(PulldownListsMinimumWidth)
    self.colourSchemeBox.addItems(COLOUR_SCHEMES)
    self.colourSchemeBox.setCurrentIndex(self.colourSchemeBox.findText(
      self.preferences.general.colourScheme))
    self.colourSchemeBox.currentIndexChanged.connect(self._changeColourScheme)

    row += 1
    self.regionPaddingLabel = Label(parent, text="Spectral Padding (%)", grid=(row, 0))
    self.regionPaddingData = LineEdit(parent, grid=(row, 1), hAlign='l')
    self.regionPaddingData.setMinimumWidth(LineEditsMinimumWidth)
    self.regionPaddingData.setText('%.0f' % (100 * self.preferences.general.stripRegionPadding))
    self.regionPaddingData.editingFinished.connect(self._setRegionPadding)

    row += 1
    self.useNativeLabel = Label(parent, text="Use Native File Dialogs: ", grid=(row, 0))
    self.useNativeBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.useNative)
    self.useNativeBox.toggled.connect(partial(self._toggleGeneralOptions, 'useNative'))

    row += 1
    self.useNativeLabel = Label(parent, text="Use Native Web Browser: ", grid=(row, 0))
    self.useNativeBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.useNativeWebbrowser)
    self.useNativeBox.toggled.connect(partial(self._toggleGeneralOptions, 'useNativeWebbrowser'))
    row += 1
    self.showToolbarLabel = Label(parent, text="Show ToolBar(s): ", grid=(row, 0))
    self.showToolbarBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.showToolbar)
    self.showToolbarBox.toggled.connect(partial(self._toggleGeneralOptions, 'showToolbar'))

    row += 1
    self.spectrumBorderLabel = Label(parent, text="Show Spectrum Border: ", grid=(row, 0))
    self.spectrumBorderBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.showSpectrumBorder)
    self.spectrumBorderBox.toggled.connect(partial(self._toggleGeneralOptions, 'showSpectrumBorder'))


  def _setMiscellaneousTabWidgets(self, parent):
    ''' Insert a widget in here to appear in the Miscellaneous Tab  '''

    row = 0
    self.autoBackupEnabledLabel = Label(parent, text="Auto Backup On: ", grid=(row, 0))
    self.autoBackupEnabledBox = CheckBox(parent, grid=(row, 1), checked=self.preferences.general.autoBackupEnabled)
    self.autoBackupEnabledBox.toggled.connect(partial(self._toggleGeneralOptions, 'autoBackupEnabled'))
    row += 1

    self.autoBackupFrequencyLabel = Label(parent, text="Auto Backup Freq (mins)", grid=(row, 0))
    self.autoBackupFrequencyData = LineEdit(parent, grid=(row, 1), hAlign='l')
    self.autoBackupFrequencyData.setMinimumWidth(LineEditsMinimumWidth)
    self.autoBackupFrequencyData.setText('%.0f' % self.preferences.general.autoBackupFrequency)
    self.autoBackupFrequencyData.editingFinished.connect(self._setAutoBackupFrequency)

    row += 1
    self.dropFactorLabel = Label(parent, text="Peak Picking Drop (%)", grid=(row, 0))
    self.dropFactorData = LineEdit(parent, grid=(row, 1), hAlign='l')
    self.dropFactorData.setMinimumWidth(LineEditsMinimumWidth)
    self.dropFactorData.setText('%.0f' % (100*self.preferences.general.peakDropFactor))
    self.dropFactorData.editingFinished.connect(self._setDropFactor)


  def _getDataPath(self):
    if os.path.exists('/'.join(self.dataPathText.text().split('/')[:-1])):
      currentDataPath = '/'.join(self.dataPathText.text().split('/')[:-1])
    else:
      currentDataPath = os.path.expanduser('~')
    dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                        preferences=self.preferences.general)
    directory = dialog.selectedFiles()
    if directory:
      self.dataPathText.setText(directory[0])
      self.preferences.general.dataPath = directory[0]

  def _setDataPath(self):
    if self.dataPathText.isModified():
      newPath = self.dataPathText.text()
      self.preferences.general.dataPath = newPath
      dataUrl = self.project._apiNmrProject.root.findFirstDataLocationStore(
        name='standard').findFirstDataUrl(name='remoteData')
      dataUrl.url = Implementation.Url(path=newPath)

  def _getAuxiliaryFilesPath(self):
    if os.path.exists(os.path.expanduser(self.auxiliaryFilesData.text())):
      currentDataPath = os.path.expanduser(self.auxiliaryFilesData.text())
    else:
      currentDataPath = os.path.expanduser('~')
    dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                        preferences=self.preferences.general)
    directory = dialog.selectedFiles()
    if len(directory) > 0:
      self.auxiliaryFilesData.setText(directory[0])
      self.preferences.general.auxiliaryFilesPath = directory[0]

  def _setAuxiliaryFilesPath(self):
    newPath = self.auxiliaryFilesData.text()
    self.preferences.general.auxiliaryFilesPath = newPath

  def _getMacroFilesPath(self):
    if os.path.exists(os.path.expanduser(self.macroPathData.text())):
      currentDataPath = os.path.expanduser(self.macroPathData.text())
    else:
      currentDataPath = os.path.expanduser('~')
    dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                        preferences=self.preferences.general)
    directory = dialog.selectedFiles()
    if len(directory) > 0:
      self.macroPathData.setText(directory[0])
      self.preferences.general.userMacroPath = directory[0]

  def _getPluginFilesPath(self):
    if os.path.exists(os.path.expanduser(self.pluginPathData.text())):
      currentDataPath = os.path.expanduser(self.pluginPathData.text())
    else:
      currentDataPath = os.path.expanduser('~')
    dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                        preferences=self.preferences.general)
    directory = dialog.selectedFiles()
    if len(directory) > 0:
      self.pluginPathData.setText(directory[0])
      self.preferences.general.pluginMacroPath = directory[0]

  def _getExtensionFilesPath(self):
    if os.path.exists(os.path.expanduser(self.extensionPathData.text())):
      currentDataPath = os.path.expanduser(self.extensionPathData.text())
    else:
      currentDataPath = os.path.expanduser('~')
    dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                        preferences=self.preferences.general)
    directory = dialog.selectedFiles()
    if len(directory) > 0:
      self.extensionPathData.setText(directory[0])
      self.preferences.general.userExtensionPath = directory[0]

  def _setMacroFilesPath(self):
    newPath = self.macroPathData.text()
    self.preferences.general.userMacroPath = newPath

  def _setPluginFilesPath(self):
    newPath = self.pluginPathData.text()
    self.preferences.general.userPluginPath = newPath

  def _setExtensionFilesPath(self):
    newPath = self.extensionPathData.text()
    self.preferences.general.userExtensionPath = newPath

  def _changeLanguage(self, value):
    self.preferences.general.language = (languages[value])

  def _changeColourScheme(self, value):
    self.preferences.general.colourScheme = (COLOUR_SCHEMES[value])

  def _toggleGeneralOptions(self, preference, checked):
    self.preferences.general[preference] = checked
    if preference == 'showToolbar':
      for spectrumDisplay in self.project.spectrumDisplays:
        spectrumDisplay.spectrumUtilToolBar.setVisible(checked)
    elif preference == 'showSpectrumBorder':
      for strip in self.project.strips:
        for spectrumView in strip.spectrumViews:
          spectrumView._setBorderItemHidden(checked)
    elif preference == 'autoBackupEnabled':
      application = self.project._appBase
      application.updateAutoBackup()

  def _setAutoBackupFrequency(self):
    try:
      frequency = int(self.autoBackupFrequencyData.text())
    except:
      return
    self.preferences.general.autoBackupFrequency = frequency
    application = self.project._appBase
    application.updateAutoBackup()

  def _setRegionPadding(self):
    try:
      padding = 0.01*float(self.regionPaddingData.text())
    except:
      return
    self.preferences.general.stripRegionPadding = padding

  def _setDropFactor(self):
    try:
      dropFactor = 0.01*float(self.dropFactorData.text())
    except:
      return
    self.preferences.general.peakDropFactor = dropFactor

  def _toggleSpectralOptions(self, preference, checked):
    self.preferences.spectra[preference] = str(checked)
