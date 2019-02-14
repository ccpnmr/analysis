"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = ""
__credits__ = ""
__licence__ = ("")
__reference__ = ("")
#=========================================================================================
# Last code modification:
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified$"
__version__ = "$Revision$"
#=========================================================================================
# Created:
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date$"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from functools import partial
from PyQt5 import QtWidgets
from ccpn.core.lib import Util as ccpnUtil
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.widgets.CompoundWidgets import CheckBoxCompoundWidget
from ccpn.ui.gui.popups.SpectrumPropertiesPopup import FilePathValidator
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpnmodel.ccpncore.api.memops import Implementation


LINEEDITSMINIMUMWIDTH = 195


class ValidateSpectraPopup(CcpnDialog):
    """
    Class to validate the paths of the selected spectra.
    """

    def __init__(self, parent=None, mainWindow=None, spectra=None,
                 title='Validate Spectra', **kwds):

        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.preferences = self.application.preferences
        self.spectra = spectra

        row = 0
        # show current insideData, alongsideData, remoteData values
        self.insidePathLabel = Label(self, "$INSIDE", grid=(row, 0), )
        self.insidePathText = LineEdit(self, textAlignment='left', grid=(row, 1), vAlign='t')
        self.insidePathText.setEnabled(False)
        self.insidePathText.setText(self._findDataPath('insideData'))
        row += 1

        self.alonsidePathLabel = Label(self, "$ALONGSIDE", grid=(row, 0), )
        self.alongsidePathText = LineEdit(self, textAlignment='left', grid=(row, 1), vAlign='t')
        self.alongsidePathText.setEnabled(False)
        self.alongsidePathText.setText(self._findDataPath('alongsideData'))
        row += 1

        self.dataPathLabel = Label(self, "User Data Path ($DATA)", grid=(row, 0), )
        self.dataPathText = LineEdit(self, textAlignment='left', grid=(row, 1), vAlign='t')
        self.dataPathText.setMinimumWidth(LINEEDITSMINIMUMWIDTH)
        self.dataPathText.setEnabled(False)
        self.dataPathText.setText(self._findDataPath('remoteData'))

        # self.dataPathText.editingFinished.connect(self._setDataPath)
        # self.dataPathText.setText(self.preferences.general.dataPath)
        # self.dataPathButton = Button(parent, grid=(row, 2), callback=self._getDataPath, icon='icons/directory', hPolicy='fixed')
        row += 1

        # buttons for show/hide valid/invalid paths
        self.showValid = CheckBoxCompoundWidget(parent=self, orientation='left', hAlign='left',
                                                minimumWidths=(150, 100),
                                                labelText='Show valid spectra',
                                                callback=self._toggleValid, grid=(row, 0), gridSpan=(1, 3),
                                                checked=True)
        row += 1
        self.showInvalid = CheckBoxCompoundWidget(parent=self, orientation='left', hAlign='left',
                                                  minimumWidths=(150, 100),
                                                  labelText='Show invalid spectra',
                                                  callback=self._toggleInvalid, grid=(row, 0), gridSpan=(1, 3),
                                                  checked=True)
        row += 1
        HLine(self, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)

        row += 1
        # set up a scroll area
        self.scrollArea = ScrollArea(self, setLayout=True, grid=(row, 0), gridSpan=(1, 3))
        self.scrollArea.setWidgetResizable(True)

        self.scrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.scrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.scrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.scrollArea.setStyleSheet("""ScrollArea { border: 0px; }""")

        if not self.spectra:
            self.spectra = self.project.spectra

        # populate the widget with a list of spectrum buttons and filepath buttons
        scrollRow = 0
        self.spectrumData = {}

        # I think there is a QT bug here - need to set a dummy button first otherwise a click is emitted, will investigate
        rogueButton = Button(self, grid=(0,0))
        rogueButton.hide()

        # standardStore = self.project._wrappedData.memopsRoot.findFirstDataLocationStore(name='standard')
        # stores = [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls() for url in store.sortedDataStores()]
        # urls = [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]
        # [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores() for dataUrl in store.sortedDataUrls()]

        for spectrum in self.spectra:
            # if not spectrum.isValidPath:

            pathLabel = Label(self.scrollAreaWidgetContents, text=spectrum.pid, grid=(scrollRow, 0))
            pathData = LineEdit(self.scrollAreaWidgetContents, textAlignment='left', grid=(scrollRow, 1))
            pathData.setValidator(FilePathValidator(parent=pathData, spectrum=spectrum))
            pathButton = Button(self.scrollAreaWidgetContents, grid=(scrollRow, 2), callback=partial(self._getSpectrumFile, spectrum),
                                icon='icons/applications-system')

            self.spectrumData[spectrum] = (pathData, pathButton, pathLabel)
            self._setPathData(spectrum)
            pathData.editingFinished.connect(partial(self._setSpectrumPath, spectrum))
            scrollRow += 1

        # finalise the scrollArea
        Spacer(self.scrollAreaWidgetContents, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(len(self.spectra), 1), gridSpan=(1, 1))

        row += 1
        # add exit buttons
        self.applyButtons = ButtonList(self, texts=['Close'],
                                       callbacks=[self._closeButton],
                                       tipTexts=[''], direction='h',
                                       hAlign='r', grid=(row, 0), gridSpan=(1, 3))

        self.setMinimumHeight(500)
        self.setMinimumWidth(600)
        # self.setFixedWidth(self.sizeHint().width()+24)

    def _closeButton(self):
        self.accept()

    # def expandDollarFilePath(self, project: 'Project', spectrum, filePath: str) -> str:
    #     """Expand paths that start with $REPOSITORY to full path
    #
    #     NBNB Should be moved to ccpnmodel.ccpncore.lib.ccp.general.DataLocation.DataLocationstore"""
    #
    #     # Convert from custom repository names to full names
    #
    #     stdRepositoryNames = {
    #         '$INSIDE/'   : 'insideData',
    #         '$ALONGSIDE/': 'alongsideData',
    #         '$DATA/'     : 'remoteData',
    #         }
    #
    #     if not filePath.startswith('$'):
    #         # Nothing to expand
    #         return filePath
    #
    #     dataLocationStore = project._wrappedData.root.findFirstDataLocationStore(name='standard')
    #
    #     if dataLocationStore is None:
    #         raise TypeError("Coding error - standard DataLocationStore has not been set")
    #
    #     for prefix, dataUrlName in stdRepositoryNames.items():
    #         if filePath.startswith(prefix):
    #             # dataUrl = dataLocationStore.findFirstDataUrl(name=dataUrlName)
    #
    #             apiDataStore = spectrum._apiDataSource.dataStore
    #             if apiDataStore and apiDataStore.dataUrl:
    #
    #                 if apiDataStore.dataUrl is not None:
    #                     return os.path.join(apiDataStore.dataUrl.url.dataLocation, filePath[len(prefix):])
    #     #
    #     return filePath

    def _getSpectrumFile(self, spectrum):
        """Get the path from the widget and call the open dialog.
        """
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]

            # if os.path.exists('/'.join(pathData.text().split('/')[:-1])):
            #     currentSpectrumDirectory = '/'.join(pathData.text().split('/')[:-1])
            # else:
            #     currentSpectrumDirectory = os.path.expanduser('~')

            filePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())

            dialog = FileDialog(self, text='Select Spectrum File', directory=filePath,
                                fileMode=1, acceptMode=0,
                                preferences=self.application.preferences.general)
            directory = dialog.selectedFiles()
            if len(directory) > 0:
                newFilePath = directory[0]

                if spectrum.filePath != newFilePath:

                    from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                    dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
                    if dataType == 'Spectrum':
                        spectrum.filePath = newFilePath

                    else:
                        getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

                    # set the widget text
                    self._setPathData(spectrum)

    def _setPathData(self, spectrum):
        """Set the pathData widgets from the spectrum.
        """
        from memops.api.Implementation import Url
        from memops.universal import Io as uniIo

        standardStore = self.project._wrappedData.memopsRoot.findFirstDataLocationStore(name='standard')

        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]

            apiDataStore = spectrum._apiDataSource.dataStore
            if not apiDataStore:
                pathData.setText('<None>')
            elif apiDataStore.dataLocationStore.name == 'standard':

                # this fails on the first loading of V2 projects - ordering issue?
                dataUrlName = apiDataStore.dataUrl.name
                if dataUrlName == 'insideData':
                    pathData.setText('$INSIDE/%s' % apiDataStore.path)
                elif dataUrlName == 'alongsideData':
                    pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
                elif dataUrlName == 'remoteData':
                    pathData.setText('$DATA/%s' % apiDataStore.path)
            else:
                pathData.setText(apiDataStore.fullPath)

            pathData.validator().resetCheck()

    def _setSpectrumPath(self, spectrum):
        """Set the path from the widget by pressing enter
        """
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]

            # if os.path.exists('/'.join(pathData.text().split('/')[:-1])):
            #     currentSpectrumDirectory = '/'.join(pathData.text().split('/')[:-1])
            # else:
            #     currentSpectrumDirectory = os.path.expanduser('~')

            newFilePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())

            if spectrum.filePath != newFilePath:

                from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
                if dataType == 'Spectrum':
                    spectrum.filePath = newFilePath
                else:
                    getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

                # set the widget text
                self._setPathData(spectrum)

    def _toggleValid(self):
        visible = self.showValid.isChecked()
        for spectrum in self.spectra:

            if spectrum in self.spectrumData and spectrum.isValidPath:
                widgets = self.spectrumData[spectrum]
                for widg in widgets:
                    widg.setVisible(visible)

    def _toggleInvalid(self):
        visible = self.showInvalid.isChecked()
        for spectrum in self.spectra:

            if spectrum in self.spectrumData and not spectrum.isValidPath:
                widgets = self.spectrumData[spectrum]
                for widg in widgets:
                    widg.setVisible(visible)

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

    def _findDataPath(self, storeType):
        dataUrl = self.project._apiNmrProject.root.findFirstDataLocationStore(
                name='standard').findFirstDataUrl(name=storeType)
        return dataUrl.url.dataLocation
