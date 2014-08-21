from PySide import QtGui, QtCore
import json
from functools import partial
from ccpncore.gui.Label import Label
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PullDownList import PulldownList
from ccpncore.gui.CheckBox import CheckBox

LANGUAGES = ['English-UK', 'English-US', 'Nederlands', 'Deutsch', 'Español', 'Français', 'Dansk']


class PreferencesPopup(QtGui.QDialog):
  def __init__(self, parent=None, preferences=None, **kw):
    super(PreferencesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.preferences = preferences
    self.generalTitle = Label(self, text="General", grid=(0, 0))
    self.generalTitle.setStyleSheet("font: bold;")
    self.autoBackupLabel =  Label(self, text="Auto Backup On Open: ", grid=(2, 0))
    self.autoBackupBox = CheckBox(self, grid=(2, 1), checked=str(self.preferences.general.autoBackupOnOpen))
    # self.autoBackupBox.stateChanged.connect(partial(self.autoBackupBox.changeState, self.preferences.general.autoBackupOnOpen))
    self.autoBackupBox.toggled.connect(partial(self.toggleGeneralOptions, 'autoBackupOnOpen'))
    self.autoSaveLabel = Label(self, text='Auto Save On Quit: ', grid=(4, 0))
    self.autoSaveBox = CheckBox(self, grid=(4, 1), checked=str(self.preferences.general.autoSaveOnQuit))
    self.autoSaveBox.toggled.connect(partial(self.toggleGeneralOptions, 'autoSaveOnQuit'))
    self.autoSaveLayoutLabel = Label(self, text="Auto Save Layout On Quit: ", grid=(6, 0))
    self.autoSaveLayoutBox = CheckBox(self, grid=(6, 1), checked=str(self.preferences.general.autoSaveLayoutOnQuit))
    self.autoSaveLayoutBox.toggled.connect(partial(self.toggleGeneralOptions, 'autoSaveLayoutOnQuit'))
    self.auxiliaryFilesLabel = Label(self, text="Auxiliary Files Path: ", grid=(8, 0))
    self.auxiliaryFilesData = LineEdit(self, grid=(8, 1))
    self.auxiliaryFilesData.setText(self.preferences.general.auxiliaryFilesPath)
    self.macroPathLabel = Label(self, text="Macro Path", grid=(10, 0))
    self.macroPathData = LineEdit(self, grid=(10, 1))
    self.macroPathData.setText(self.preferences.general.macroPath)
    self.languageLabel = Label(self, text="Language", grid=(12, 0))
    self.languageBox = PulldownList(self, grid=(12, 1))
    self.languageBox.addItems(LANGUAGES)
    self.languageBox.setCurrentIndex(self.languageBox.findText(self.preferences.general.language))
    self.languageBox.currentIndexChanged.connect(self.changeLanguage)
    self.editorLabel = Label(self, text="Editor: ", grid=(14, 0))
    self.editorData = LineEdit(self, text=self.preferences.general.editor, grid=(14, 1))
    self.colourSchemeLabel = Label(self, text="Colour Scheme: ", grid=(16, 0))
    self.colourSchemeBox = PulldownList(self, grid=(16, 1))
    self.colourSchemeBox.addItems(['light', 'dark'])
    self.colourSchemeBox.setCurrentIndex(self.colourSchemeBox.findText(
      self.preferences.general.colourScheme))

    self.licenceLabel = Label(self, text='Licence', grid=(18, 0))
    self.licenceButton = Button(self,text='Show Licence', grid=(18, 1))
    self.spectraTitle = Label(self, text='Spectra', grid=(22, 0))
    self.spectraTitle.setStyleSheet("font: bold;")
    self.keepExternalLabel = Label(self, text='Keep External:', grid=(24, 0))
    self.keepExternalBox = CheckBox(self, grid=(24, 1), checked=self.preferences.spectra.keepExternal)
    self.keepExternalBox.toggled.connect(partial(self.toggleSpectralOptions, 'keepExternal'))

    buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
    buttonBox.accepted.connect(self.accept)

    self.layout().addWidget(buttonBox, 28, 0, 1, 2)

  def changeLanguage(self, value):
    self.preferences.general.language = (LANGUAGES[value])

  def toggleGeneralOptions(self, property, checked):
    self.preferences.general[property] = str(checked)

  def toggleSpectralOptions(self, property, checked):
    self.preferences.spectra[property] = str(checked)



