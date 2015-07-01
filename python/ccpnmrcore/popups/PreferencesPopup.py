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
import json
from functools import partial
from ccpncore.gui.Label import Label
from ccpncore.gui.Base import Base
from ccpncore.gui.Button import Button
from ccpncore.gui.LineEdit import LineEdit
from ccpncore.gui.PulldownList import PulldownList
from ccpncore.gui.CheckBox import CheckBox

LANGUAGES = ['English-UK', 'English-US', 'Nederlands', 'Deutsch', 'Español', 'Français', 'Dansk']
COLOUR_SCHEMES = ['light', 'dark']


class PreferencesPopup(QtGui.QDialog):
  def __init__(self, parent=None, preferences=None, **kw):
    super(PreferencesPopup, self).__init__(parent)
    Base.__init__(self, **kw)
    self.preferences = preferences
    self.oldPreferences = preferences
    self.autoBackupLabel =  Label(self, text="Auto Backup On Open: ", grid=(2, 0))
    self.autoBackupBox = CheckBox(self, grid=(2, 1), checked=bool(self.preferences.general.autoBackupOnOpen))
    self.autoBackupBox.toggled.connect(partial(self.toggleGeneralOptions, 'autoBackupOnOpen'))
    self.autoSaveLabel = Label(self, text='Auto Save On Quit: ', grid=(4, 0))
    self.autoSaveBox = CheckBox(self, grid=(4, 1), checked=bool(self.preferences.general.autoSaveOnQuit))
    self.autoSaveBox.toggled.connect(partial(self.toggleGeneralOptions, 'autoSaveOnQuit'))
    self.autoSaveLayoutLabel = Label(self, text="Auto Save Layout On Quit: ", grid=(6, 0))
    self.autoSaveLayoutBox = CheckBox(self, grid=(6, 1), checked=bool(self.preferences.general.autoSaveLayoutOnQuit))
    self.autoSaveLayoutBox.toggled.connect(partial(self.toggleGeneralOptions, 'autoSaveLayoutOnQuit'))
    self.auxiliaryFilesLabel = Label(self, text="Auxiliary Files Path: ", grid=(8, 0))
    self.auxiliaryFilesData = LineEdit(self, grid=(8, 1), hAlign='l')
    self.auxiliaryFilesData.setText(self.preferences.general.auxiliaryFilesPath)
    self.macroPathLabel = Label(self, text="Macro Path", grid=(10, 0))
    self.macroPathData = LineEdit(self, grid=(10, 1), hAlign='l')
    self.macroPathData.setText(self.preferences.general.macroPath)
    self.languageLabel = Label(self, text="Language", grid=(12, 0))
    self.languageBox = PulldownList(self, grid=(12, 1), hAlign='l')
    self.languageBox.addItems(LANGUAGES)
    self.languageBox.setCurrentIndex(self.languageBox.findText(self.preferences.general.language))
    self.languageBox.currentIndexChanged.connect(self.changeLanguage)
    self.editorLabel = Label(self, text="Editor: ", grid=(14, 0))
    self.editorData = LineEdit(self, text=self.preferences.general.editor, grid=(14, 1), hAlign='l')
    self.colourSchemeLabel = Label(self, text="Colour Scheme: ", grid=(16, 0))
    self.colourSchemeBox = PulldownList(self, grid=(16, 1), hAlign='l')
    self.colourSchemeBox.addItems(COLOUR_SCHEMES)
    self.colourSchemeBox.setCurrentIndex(self.colourSchemeBox.findText(
      self.preferences.general.colourScheme))
    self.colourSchemeBox.currentIndexChanged.connect(self.changeColourScheme)

    self.licenceLabel = Label(self, text='Licence', grid=(18, 0))
    self.licenceButton = Button(self,text='Show Licence', grid=(18, 1), hAlign='l')
    self.spectraTitle = Label(self, text='Spectra', grid=(22, 0))
    self.spectraTitle.setStyleSheet("font: bold;")
    self.keepExternalLabel = Label(self, text='Keep External:', grid=(24, 0))
    self.keepExternalBox = CheckBox(self, grid=(24, 1), hAlign='l',checked=bool(self.preferences.spectra.keepExternal))
    self.keepExternalBox.toggled.connect(partial(self.toggleSpectralOptions, 'keepExternal'))

    buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
    buttonBox.accepted.connect(self.accept)


    self.layout().addWidget(buttonBox, 28, 0, 1, 2)

  def changeLanguage(self, value):
    self.preferences.general.language = (LANGUAGES[value])

  def changeColourScheme(self, value):
    self.preferences.general.colourScheme = (COLOUR_SCHEMES[value])

  def toggleGeneralOptions(self, preference, checked):
    self.preferences.general[preference] = str(checked)

  def toggleSpectralOptions(self, preference, checked):
    self.preferences.spectra[preference] = str(checked)




