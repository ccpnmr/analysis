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
__dateModified__ = "$dateModified: 2017-04-10 15:35:09 +0100 (Mon, April 10, 2017) $"
__version__ = "$Revision: 3.0.b1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-03-30 11:28:58 +0100 (Thu, March 30, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt4 import QtGui, QtCore
import json, os
from functools import partial
from ccpnmodel.ccpncore.api.memops import Implementation
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES
from ccpn.framework.Translation import languages
from ccpn.ui.gui.popups.Dialog import CcpnDialog      # ejb
from ccpn.ui.gui.widgets.MessageDialog import MessageDialog


class PreferencesPopup(CcpnDialog):
  def __init__(self, parent=None, preferences=None, project=None, title='Preferences', **kw):
    CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kw)

    if not project:                                         # ejb - should always be loaded
      MessageDialog.showWarning(title, 'No project loaded')
      self.close()
      return

    self.project = project
    self.preferences = preferences
    self.oldPreferences = preferences

    row=0

    self.dataPathLabel = Label(self, "Data Path", grid=(row, 0))
    self.dataPathText = LineEdit(self, grid=(row, 1))
    self.dataPathText.editingFinished.connect(self._setDataPath)
    self.dataPathText.setText(self.preferences.general.dataPath)
    self.dataPathButton = Button(self, grid=(row, 2), callback=self._getDataPath, icon='icons/directory', hPolicy='fixed')
    row += 1

    self.auxiliaryFilesLabel = Label(self, text="Auxiliary Files Path ", grid=(row, 0))
    self.auxiliaryFilesData = LineEdit(self, grid=(row, 1))
    self.auxiliaryFilesDataButton = Button(self, grid=(row, 2), callback=self._getAuxiliaryFilesPath, icon='icons/directory', hPolicy='fixed')
    self.auxiliaryFilesData.setText(self.preferences.general.auxiliaryFilesPath)
    self.auxiliaryFilesData.editingFinished.connect(self._setAuxiliaryFilesPath)
    row += 1

    self.macroPathLabel = Label(self, text="Macro Path", grid=(row, 0))
    self.macroPathData = LineEdit(self, grid=(row, 1))
    self.macroPathData.setText(self.preferences.general.userMacroPath)
    self.macroPathDataButton = Button(self, grid=(row, 2), callback=self._getMacroFilesPath, icon='icons/directory', hPolicy='fixed')
    self.macroPathData.editingFinished.connect(self._setMacroFilesPath)
    row += 1

    self.pluginPathLabel = Label(self, text="Plugin Path", grid=(row, 0))
    self.pluginPathData = LineEdit(self, grid=(row, 1))
    self.pluginPathData.setText(self.preferences.general.userPluginPath)
    self.pluginPathDataButton = Button(self, grid=(row, 2), callback=self._getPluginFilesPath, icon='icons/directory', hPolicy='fixed')
    self.pluginPathData.editingFinished.connect(self._setPluginFilesPath)
    row += 1

    self.extensionPathLabel = Label(self, text="Extension Path", grid=(row, 0))
    self.extensionPathData = LineEdit(self, grid=(row, 1))
    self.extensionPathData.setText(self.preferences.general.userExtensionPath)
    self.extensionPathDataButton = Button(self, grid=(row, 2), callback=self._getExtensionFilesPath, icon='icons/directory', hPolicy='fixed')
    self.extensionPathData.editingFinished.connect(self._setExtensionFilesPath)
    row += 1

    self.languageLabel = Label(self, text="Language", grid=(row, 0))
    self.languageBox = PulldownList(self, grid=(row, 1), gridSpan=(1, 1))
    self.languageBox.addItems(languages)
    self.languageBox.setMinimumWidth(self.dataPathText.width())
    self.languageBox.setCurrentIndex(self.languageBox.findText(self.preferences.general.language))
    self.languageBox.currentIndexChanged.connect(self._changeLanguage)
    row += 1

    # self.editorLabel = Label(self, text="Editor ", grid=(5, 0))
    # self.edi
    # torData = LineEdit(self, text=self.preferences.general.editor, grid=(5, 1), gridSpan=(1, 1))
    self.colourSchemeLabel = Label(self, text="Colour Scheme ", grid=(row, 0))
    self.colourSchemeBox = PulldownList(self, grid=(row, 1), gridSpan=(1, 1))
    self.colourSchemeBox.setMinimumWidth(self.dataPathText.width())
    self.colourSchemeBox.addItems(COLOUR_SCHEMES)
    self.colourSchemeBox.setCurrentIndex(self.colourSchemeBox.findText(
                                         self.preferences.general.colourScheme))
    self.colourSchemeBox.currentIndexChanged.connect(self._changeColourScheme)
    row += 1

    self.useNativeLabel = Label(self, text="Use Native File Dialogs: ", grid=(row, 0))
    self.useNativeBox = CheckBox(self, grid=(row, 1), checked=self.preferences.general.useNative)
    self.useNativeBox.toggled.connect(partial(self._toggleGeneralOptions, 'useNative'))
    row += 1

    self.useNativeLabel = Label(self, text="Use Native Web Browser: ", grid=(row, 0))
    self.useNativeBox = CheckBox(self, grid=(row, 1), checked=self.preferences.general.useNativeWebbrowser)
    self.useNativeBox.toggled.connect(partial(self._toggleGeneralOptions, 'useNativeWebbrowser'))
    row += 1

    self.autoSaveLayoutLabel = Label(self, text="Show ToolBar(s): ", grid=(row, 0))
    self.autoSaveLayoutBox = CheckBox(self, grid=(row, 1), checked=self.preferences.general.showToolbar)
    self.autoSaveLayoutBox.toggled.connect(partial(self._toggleGeneralOptions, 'showToolbar'))
    row += 1

    self.spectrumBorderLabel = Label(self, text="Show Spectrum Border: ", grid=(row, 0))
    self.spectrumBorderBox = CheckBox(self, grid=(row, 1), checked=self.preferences.general.showSpectrumBorder)
    self.spectrumBorderBox.toggled.connect(partial(self._toggleGeneralOptions, 'showSpectrumBorder'))
    row += 1

    self.autoBackupEnabledLabel = Label(self, text="Auto Backup On: ", grid=(row, 0))
    self.autoBackupEnabledBox = CheckBox(self, grid=(row, 1), checked=self.preferences.general.autoBackupEnabled)
    self.autoBackupEnabledBox.toggled.connect(partial(self._toggleGeneralOptions, 'autoBackupEnabled'))
    row += 1

    self.autoBackupFrequencyLabel = Label(self, text="Auto Backup Freq (mins)", grid=(row, 0))
    self.autoBackupFrequencyData = LineEdit(self, grid=(row, 1))
    self.autoBackupFrequencyData.setText('%.0f' % self.preferences.general.autoBackupFrequency)
    self.autoBackupFrequencyData.editingFinished.connect(self._setAutoBackupFrequency)
    row += 1

    self.regionPaddingLabel = Label(self, text="Spectral Padding (%)", grid=(row, 0))
    self.regionPaddingData = LineEdit(self, grid=(row, 1))
    self.regionPaddingData.setText('%.0f' % (100*self.preferences.general.stripRegionPadding))
    self.regionPaddingData.editingFinished.connect(self._setRegionPadding)
    row += 1

    self.dropFactorLabel = Label(self, text="Peak Picking Drop (%)", grid=(row, 0))
    self.dropFactorData = LineEdit(self, grid=(row, 1))
    self.dropFactorData.setText('%.0f' % (100*self.preferences.general.peakDropFactor))
    self.dropFactorData.editingFinished.connect(self._setDropFactor)
    row += 1

    buttonBox = Button(self, grid=(row, 1), text='Close', callback=self.accept)
    row += 1

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
    self.preferences.general.language = (LANGUAGES[value])

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





