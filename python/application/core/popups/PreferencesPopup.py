"""Module Documentation here

"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (www.ccpn.ac.uk) 2014 - $Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__credits__ = "Wayne Boucher, Rasmus H Fogh, Simon P Skinner, Geerten W Vuister"
__license__ = ("CCPN license. See www.ccpn.ac.uk/license"
              "or ccpncore.memops.Credits.CcpnLicense for license text")
__reference__ = ("For publications, please use reference from www.ccpn.ac.uk/license"
                " or ccpncore.memops.Credits.CcpNmrReference")

#=========================================================================================
# Last code modification:
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2014-06-04 18:13:10 +0100 (Wed, 04 Jun 2014) $"
__version__ = "$Revision: 7686 $"

#=========================================================================================
# Start of code
#=========================================================================================
__author__ = 'simon'

from PyQt4 import QtGui, QtCore
import json, os
from functools import partial
from ccpncore.api.memops import Implementation
from ccpncore.gui.Label import Label
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.CheckBox import CheckBox

LANGUAGES = ['English-UK', 'Italiano']
COLOUR_SCHEMES = ['light', 'dark']


class PreferencesPopup(QtGui.QDialog):
  def __init__(self, parent=None, preferences=None, project=None, **kw):
    super(PreferencesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.project = project
    self.preferences = preferences
    self.oldPreferences = preferences
    self.dataPathLabel = Label(self, "Data Path", grid=(0, 0))
    self.dataPathText = LineEdit(self, grid=(0, 1))
    self.dataPathText.editingFinished.connect(self.setDataPath)
    self.dataPathText.setText(self.preferences.general.dataPath)
    self.dataPathButton = Button(self, grid=(0, 2), callback=self.getDataPath, icon='iconsNew/directory', hPolicy='fixed')
    self.autoSaveLayoutLabel = Label(self, text="ToolBar Hidden: ", grid=(1, 0))
    self.autoSaveLayoutBox = CheckBox(self, grid=(1, 1), checked=self.preferences.general.toolbarHidden)
    self.autoSaveLayoutBox.toggled.connect(partial(self.toggleGeneralOptions, 'toolbarHidden'))
    self.auxiliaryFilesLabel = Label(self, text="Auxiliary Files Path ", grid=(2, 0))
    self.auxiliaryFilesData = LineEdit(self, grid=(2, 1))
    self.auxiliaryFilesDataButton = Button(self, grid=(2, 2), callback=self.setDataPath, icon='iconsNew/directory', hPolicy='fixed')
    self.auxiliaryFilesData.setText(self.preferences.general.auxiliaryFilesPath)
    self.macroPathLabel = Label(self, text="Macro Path", grid=(3, 0))
    self.macroPathData = LineEdit(self, grid=(3, 1))
    self.macroPathData.setText(self.preferences.general.macroPath)
    self.macroPathDataButton = Button(self, grid=(3, 2), callback=self.setDataPath, icon='iconsNew/directory', hPolicy='fixed')
    self.languageLabel = Label(self, text="Language", grid=(4, 0))
    self.languageBox = PulldownList(self, grid=(4, 1), gridSpan=(1, 1))
    self.languageBox.addItems(LANGUAGES)
    self.languageBox.setMinimumWidth(self.dataPathText.width())
    self.languageBox.setCurrentIndex(self.languageBox.findText(self.preferences.general.language))
    self.languageBox.currentIndexChanged.connect(self.changeLanguage)
    # self.editorLabel = Label(self, text="Editor ", grid=(5, 0))
    # self.editorData = LineEdit(self, text=self.preferences.general.editor, grid=(5, 1), gridSpan=(1, 1))
    self.colourSchemeLabel = Label(self, text="Colour Scheme ", grid=(5, 0))
    self.colourSchemeBox = PulldownList(self, grid=(5, 1), gridSpan=(1, 1))
    self.colourSchemeBox.setMinimumWidth(self.dataPathText.width())
    self.colourSchemeBox.addItems(COLOUR_SCHEMES)
    self.colourSchemeBox.setCurrentIndex(self.colourSchemeBox.findText(
      self.preferences.general.colourScheme))
    self.colourSchemeBox.currentIndexChanged.connect(self.changeColourScheme)
    self.licenceLabel = Label(self, text='Licence', grid=(6, 0))
    self.licenceButton = Button(self, text='Show Licence', grid=(6, 1), gridSpan=(1, 1), callback=self.showLicenceInfo)
    # self.spectraTitle = Label(self, text='Spectra', grid=(8, 0))
    # self.spectraTitle.setStyleSheet("font: bold;")
    # self.keepExternalLabel = Label(self, text='Keep External:', grid=(8, 0))
    # self.keepExternalBox = CheckBox(self, grid=(24, 1), hAlign='l',checked=self.preferences.spectra.keepExternal)
    # self.keepExternalBox.toggled.connect(partial(self.toggleSpectralOptions, 'keepExternal'))

    buttonBox = Button(self, grid=(7, 1), text='Close', callback=self.accept)

  def getDataPath(self):
    if os.path.exists('/'.join(self.dataPathText.text().split('/')[:-1])):
      currentDataPath = '/'.join(self.dataPathText.text().split('/')[:-1])
    else:
      currentDataPath = os.path.expanduser('~')
    directory = QtGui.QFileDialog.getExistingDirectory(self, 'Select Data File', currentDataPath)
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




