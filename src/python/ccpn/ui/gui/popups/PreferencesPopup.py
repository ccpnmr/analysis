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
__author__ = 'simon'

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
from ccpn.util.Translation import languages

COLOUR_SCHEMES = ['light', 'dark']


class PreferencesPopup(QtGui.QDialog):
  def __init__(self, parent=None, preferences=None, project=None, **kw):
    super(PreferencesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.project = project
    self.preferences = preferences
    self.oldPreferences = preferences

    row=0

    self.dataPathLabel = Label(self, "Data Path", grid=(row, 0))
    self.dataPathText = LineEdit(self, grid=(row, 1))
    self.dataPathText.editingFinished.connect(self.setDataPath)
    self.dataPathText.setText(self.preferences.general.dataPath)
    self.dataPathButton = Button(self, grid=(row, 2), callback=self.getDataPath, icon='iconsNew/directory', hPolicy='fixed')
    row += 1

    self.auxiliaryFilesLabel = Label(self, text="Auxiliary Files Path ", grid=(row, 0))
    self.auxiliaryFilesData = LineEdit(self, grid=(row, 1))
    self.auxiliaryFilesDataButton = Button(self, grid=(row, 2), callback=self.getAuxiliaryFilesPath, icon='iconsNew/directory', hPolicy='fixed')
    self.auxiliaryFilesData.setText(self.preferences.general.auxiliaryFilesPath)
    self.auxiliaryFilesData.editingFinished.connect(self.setAuxiliaryFilesPath)
    row += 1

    self.macroPathLabel = Label(self, text="Macro Path", grid=(row, 0))
    self.macroPathData = LineEdit(self, grid=(row, 1))
    self.macroPathData.setText(self.preferences.general.macroPath)
    self.macroPathDataButton = Button(self, grid=(row, 2), callback=self.getMacroFilesPath, icon='iconsNew/directory', hPolicy='fixed')
    self.macroPathData.editingFinished.connect(self.setMacroFilesPath)
    row += 1

    self.languageLabel = Label(self, text="Language", grid=(row, 0))
    self.languageBox = PulldownList(self, grid=(row, 1), gridSpan=(1, 1))
    self.languageBox.addItems(languages)
    self.languageBox.setMinimumWidth(self.dataPathText.width())
    self.languageBox.setCurrentIndex(self.languageBox.findText(self.preferences.general.language))
    self.languageBox.currentIndexChanged.connect(self.changeLanguage)
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
    self.colourSchemeBox.currentIndexChanged.connect(self.changeColourScheme)
    row += 1

    self.autoSaveLayoutLabel = Label(self, text="Hide ToolBar(s): ", grid=(row, 0))
    self.autoSaveLayoutBox = CheckBox(self, grid=(row, 1), checked=self.preferences.general.toolbarHidden)
    self.autoSaveLayoutBox.toggled.connect(partial(self.toggleGeneralOptions, 'toolbarHidden'))
    row += 1

    self.useNativeLabel = Label(self, text="Use Native File Dialogs: ", grid=(row, 0))
    self.useNativeBox = CheckBox(self, grid=(row, 1), checked=self.preferences.general.useNative)
    self.useNativeBox.toggled.connect(partial(self.toggleGeneralOptions, 'useNative'))
    row += 1

    self.licenceLabel = Label(self, text='Licence', grid=(row, 0))
    self.licenceButton = Button(self, text='Show', grid=(row, 1), gridSpan=(1, 1), callback=self.showLicenceInfo)
    row += 1

    buttonBox = Button(self, grid=(row, 1), text='Save', callback=self.accept)
    row += 1

  def getDataPath(self):
    if os.path.exists('/'.join(self.dataPathText.text().split('/')[:-1])):
      currentDataPath = '/'.join(self.dataPathText.text().split('/')[:-1])
    else:
      currentDataPath = os.path.expanduser('~')
    dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                           preferences=self.preferences.general)
    directory = dialog.selectedFiles()[0]
    if len(directory) > 0:
      self.dataPathText.setText(directory)
      self.preferences.general.dataPath = directory

  def setDataPath(self):
    if self.dataPathText.isModified():
      newPath = self.dataPathText.text()
      self.preferences.general.dataPath = newPath
      dataUrl = self.project._apiNmrProject.root.findFirstDataLocationStore(
        name='standard').findFirstDataUrl(name='remoteData')
      dataUrl.url = Implementation.Url(path=newPath)

  def getAuxiliaryFilesPath(self):
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

  def setAuxiliaryFilesPath(self):
      newPath = self.auxiliaryFilesData.text()
      self.preferences.general.auxiliaryFilesPath = newPath


  def getMacroFilesPath(self):
    if os.path.exists(os.path.expanduser(self.macroPathData.text())):
      currentDataPath = os.path.expanduser(self.macroPathData.text())
    else:
      currentDataPath = os.path.expanduser('~')
    dialog = FileDialog(self, text='Select Data File', directory=currentDataPath, fileMode=2, acceptMode=0,
                           preferences=self.preferences.general)
    directory = dialog.selectedFiles()
    if len(directory) > 0:
      self.macroPathData.setText(directory[0])
      self.preferences.general.macroPath = directory[0]

  def setMacroFilesPath(self):
      newPath = self.macroPathData.text()
      self.preferences.general.macroPath = newPath

  def changeLanguage(self, value):
    self.preferences.general.language = (LANGUAGES[value])

  def changeColourScheme(self, value):
    self.preferences.general.colourScheme = (COLOUR_SCHEMES[value])

  def toggleGeneralOptions(self, preference, checked):
    self.preferences.general[preference] = checked
    if preference == 'toolbarHidden':
      if checked is True:
        for strip in self.project.strips:
          strip.guiSpectrumDisplay.spectrumUtilToolBar.hide()
      else:
        for strip in self.project.strips:
          strip.guiSpectrumDisplay.spectrumUtilToolBar.show()

  def toggleSpectralOptions(self, preference, checked):
    self.preferences.spectra[preference] = str(checked)

  def showLicenceInfo(self):
    import webbrowser
    webbrowser.open('http://www.ccpn.ac.uk/industry/licencefees')




