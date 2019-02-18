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
from PyQt5 import QtWidgets, QtGui
from ccpn.core.lib import Util as ccpnUtil
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.util.Logging import getLogger
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons


LINEEDITSMINIMUMWIDTH = 195


class SpectrumValidator(QtGui.QValidator):

    def __init__(self, spectrum, parent=None, validationType='exists'):
        QtGui.QValidator.__init__(self, parent=parent)
        self.spectrum = spectrum
        self.validationType = validationType
        self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)

    def validate(self, p_str, p_int):
        if self.validationType != 'exists':
            raise NotImplemented('%s only checks that the path exists', self.__class__.__name__)
        filePath = ccpnUtil.expandDollarFilePath(self.spectrum._project, self.spectrum, p_str.strip())

        palette = self.parent().palette()

        if os.path.exists(filePath):
            if filePath == self.spectrum.filePath:
                palette.setColor(QtGui.QPalette.Base, self.baseColour)
            else:
                from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                dataType, subType, usePath = ioFormats.analyseUrl(filePath)
                if dataType == 'Spectrum':
                    palette.setColor(QtGui.QPalette.Base, QtGui.QColor('palegreen'))
                else:
                    palette.setColor(QtGui.QPalette.Base, QtGui.QColor('orange'))

            state = QtGui.QValidator.Acceptable
        else:
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor('lightpink'))
            state = QtGui.QValidator.Intermediate
        self.parent().setPalette(palette)

        return state, p_str, p_int

    def clearValidCheck(self):
        palette = self.parent().palette()
        palette.setColor(QtGui.QPalette.Base, self.baseColour)
        self.parent().setPalette(palette)

    def resetCheck(self):
        self.validate(self.parent().text(), 0)


class DataUrlValidator(QtGui.QValidator):

    def __init__(self, dataUrl, parent=None, validationType='exists'):
        QtGui.QValidator.__init__(self, parent=parent)
        self.dataUrl = dataUrl
        self.validationType = validationType
        self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)

    def validate(self, p_str, p_int):
        if self.validationType != 'exists':
            raise NotImplemented('%s only checks that the path exists', self.__class__.__name__)
        # filePath = ccpnUtil.expandDollarFilePath(self.spectrum._project, self.spectrum, p_str.strip())
        filePath = p_str.strip()

        palette = self.parent().palette()

        if os.path.isdir(filePath):
            if filePath == self.dataUrl.url.dataLocation:
                palette.setColor(QtGui.QPalette.Base, self.baseColour)
            else:

                # validate dataStores
                localStores = [store for store in self.dataUrl.sortedDataStores()]
                for store in self.dataUrl.sortedDataStores():
                    if not os.path.exists(os.path.join(filePath, store.path)):
                        palette.setColor(QtGui.QPalette.Base, QtGui.QColor('orange'))
                        break

                else:
                    palette.setColor(QtGui.QPalette.Base, QtGui.QColor('palegreen'))
            state = QtGui.QValidator.Acceptable
        else:
            palette.setColor(QtGui.QPalette.Base, QtGui.QColor('lightpink'))
            state = QtGui.QValidator.Intermediate
        self.parent().setPalette(palette)

        return state, p_str, p_int

    def clearValidCheck(self):
        palette = self.parent().palette()
        palette.setColor(QtGui.QPalette.Base, self.baseColour)
        self.parent().setPalette(palette)

    def resetCheck(self):
        self.validate(self.parent().text(), 0)


VALIDSPECTRA = 'valid'
INVALIDSPECTRA = 'invalid'
ALLSPECTRA = 'all'
DEFAULTSELECTED = (VALIDSPECTRA, INVALIDSPECTRA, ALLSPECTRA)


class ValidateSpectraPopup(CcpnDialog):
    """
    Class to validate the paths of the selected spectra.
    """

    def __init__(self, parent=None, mainWindow=None, spectra=None,
                 title='Validate Spectra', defaultSelected='all', **kwds):

        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current
        self.preferences = self.application.preferences
        self.spectra = spectra
        self.defaultSelected = DEFAULTSELECTED.index(defaultSelected) if defaultSelected in DEFAULTSELECTED else DEFAULTSELECTED.index(ALLSPECTRA)

        # I think there is a QT bug here - need to set a dummy button first otherwise a click is emitted, will investigate
        rogueButton = Button(self, grid=(0, 0))
        rogueButton.hide()

        row = 0

        # put widget intro here

        # set up a scroll area
        self.dataUrlScrollArea = ScrollArea(self, setLayout=True, grid=(row, 0), gridSpan=(1, 3))
        self.dataUrlScrollArea.setWidgetResizable(True)
        self.dataUrlScrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False)
        self.dataUrlScrollArea.setWidget(self.dataUrlScrollAreaWidgetContents)
        self.dataUrlScrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.dataUrlScrollArea.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.dataUrlScrollArea.setStyleSheet("""ScrollArea { border: 0px; }""")
        self.dataUrlScrollArea.setFixedHeight(120)

        # populate the widget with a list of spectrum buttons and filepath buttons
        scrollRow = 0
        self.dataUrlData = {}

        standardStore = self.project._wrappedData.memopsRoot.findFirstDataLocationStore(name='standard')
        stores = [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls() for url in store.sortedDataStores()]
        urls = [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]

        self.allUrls = [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores()
                        for dataUrl in store.sortedDataUrls() if dataUrl.name not in ('insideData', 'alongsideData')]

        urls = self._findDataUrl('insideData')
        for url in urls:
            label = self._addUrl(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=False)
            label.setText('$INSIDE')
            scrollRow += 1

        urls = self._findDataUrl('alongsideData')
        for url in urls:
            label = self._addUrl(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=False)
            label.setText('$ALONGSIDE')
            scrollRow += 1

        urls = self._findDataUrl('remoteData')
        for url in urls:
            label = self._addUrl(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=True)
            label.setText('$DATA (user datapath)')
            scrollRow += 1

        otherUrls = [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores()
                     for dataUrl in store.sortedDataUrls() if dataUrl.name not in ('insideData', 'alongsideData', 'remoteData')]

        for url in otherUrls:
            self._addUrl(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=True)
            scrollRow += 1

        # finalise the spectrumScrollArea
        Spacer(self.dataUrlScrollAreaWidgetContents, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(scrollRow, 1), gridSpan=(1, 1))
        row += 1

        HLine(self, grid=(row, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)
        row += 1

        self.buttonFrame = Frame(self, setLayout=True, showBorder=False, fShape='noFrame',
                                 grid=(row, 0), gridSpan=(1, 3),
                                 vAlign='top', hAlign='left')
        self.showValidLabel = Label(self.buttonFrame, text="Show spectra: ", vAlign='t', grid=(0, 0), bold=True)
        self.showValid = RadioButtons(self.buttonFrame, texts=['valid', 'invalid', 'all'],
                                      selectedInd=self.defaultSelected,
                                      callback=self._toggleValid,
                                      direction='h',
                                      grid=(0, 1), hAlign='l',
                                      tipTexts=None,
                                      )
        row += 1

        self.addSpacer(0,10, grid=(row,0))
        row += 1

        # set up a scroll area
        self.spectrumScrollArea = ScrollArea(self, setLayout=True, grid=(row, 0), gridSpan=(1, 3))
        self.spectrumScrollArea.setWidgetResizable(True)
        self.spectrumScrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False)
        self.spectrumScrollArea.setWidget(self.spectrumScrollAreaWidgetContents)
        self.spectrumScrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.spectrumScrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.spectrumScrollArea.setStyleSheet("""ScrollArea { border: 0px; }""")

        if not self.spectra:
            self.spectra = self.project.spectra

        # populate the widget with a list of spectrum buttons and filepath buttons
        scrollRow = 0
        self.spectrumData = {}

        # standardStore = self.project._wrappedData.memopsRoot.findFirstDataLocationStore(name='standard')
        # stores = [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls() for url in store.sortedDataStores()]
        # urls = [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]
        # [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores() for dataUrl in store.sortedDataUrls()]

        for spectrum in self.spectra:
            # if not spectrum.isValidPath:

            pathLabel = Label(self.spectrumScrollAreaWidgetContents, text=spectrum.pid, grid=(scrollRow, 0))
            pathData = LineEdit(self.spectrumScrollAreaWidgetContents, textAlignment='left', grid=(scrollRow, 1))
            pathData.setValidator(SpectrumValidator(parent=pathData, spectrum=spectrum))
            pathButton = Button(self.spectrumScrollAreaWidgetContents, grid=(scrollRow, 2), callback=partial(self._getSpectrumFile, spectrum),
                                icon='icons/applications-system')

            self.spectrumData[spectrum] = (pathData, pathButton, pathLabel)
            self._setPathData(spectrum)
            pathData.editingFinished.connect(partial(self._setSpectrumPath, spectrum))
            scrollRow += 1

        # finalise the spectrumScrollArea
        Spacer(self.spectrumScrollAreaWidgetContents, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(scrollRow, 1), gridSpan=(1, 1))
        row += 1

        # add exit buttons
        self.applyButtons = ButtonList(self, texts=['Close', 'Apply'],
                                       callbacks=[self._closeButton, self._apply],
                                       tipTexts=[''], direction='h',
                                       hAlign='r', grid=(row, 0), gridSpan=(1, 3))

        self.setMinimumHeight(500)
        self.setMinimumWidth(600)
        # self.setFixedWidth(self.sizeHint().width()+24)

    def _addUrl(self, widget, dataUrl, urlList, scrollRow, enabled=True):
        urlLabel = Label(widget, text=dataUrl.name, grid=(scrollRow, 0))
        urlData = LineEdit(widget, textAlignment='left', grid=(scrollRow, 1))
        urlData.setValidator(DataUrlValidator(parent=urlData, dataUrl=dataUrl))
        urlButton = Button(widget, grid=(scrollRow, 2), callback=partial(self._getDataUrlDialog, dataUrl),
                           icon='icons/applications-system')

        urlList[dataUrl] = (urlData, None, urlLabel)
        self._setUrlData(dataUrl)
        urlData.setEnabled(enabled)
        urlButton.setEnabled(enabled)
        urlButton.setVisible(enabled)
        urlData.editingFinished.connect(partial(self._setDataUrlPath, dataUrl))
        return urlLabel

    def _getDataUrlDialog(self, dataUrl):
        """Get the path from the widget and call the open dialog.
        """
        if dataUrl and dataUrl in self.dataUrlData:
            urlData, urlButton, urlLabel = self.dataUrlData[dataUrl]

            newUrl = urlData.text().strip()

            dialog = FileDialog(self, text='Select DataUrl File', directory=newUrl,
                                fileMode=FileDialog.Directory, acceptMode=0,
                                preferences=self.application.preferences.general)
            directory = dialog.selectedFiles()
            if len(directory) > 0:
                newUrl = directory[0]

                if dataUrl.url.dataLocation != newUrl:
                    dataUrl.url = dataUrl.url.clone(path=newUrl)

                    # set the widget text
                    # self._setUrlData(dataUrl)
                    self._validateAll()

    def _setDataUrlPath(self, dataUrl):
        """Set the path from the widget by pressing enter
        """
        if dataUrl and dataUrl in self.dataUrlData:
            urlData, urlButton, urlLabel = self.dataUrlData[dataUrl]

            newUrl = urlData.text().strip()
            if dataUrl.url.dataLocation != newUrl:
                dataUrl.url = dataUrl.url.clone(path=newUrl)

                # set the widget text
                # self._setUrlData(dataUrl)
                self._validateAll()

    def _setUrlData(self, dataUrl):
        """Set the urlData widgets from the dataUrl.
        """
        urlData, urlButton, urlLabel = self.dataUrlData[dataUrl]
        urlData.setText(dataUrl.url.dataLocation)
        urlData.validator().resetCheck()

    def _getSpectrumFile(self, spectrum):
        """Get the path from the widget and call the open dialog.
        """
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]
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
                    # self._setPathData(spectrum)
                    self._validateAll()

    def _setPathData(self, spectrum):
        """Set the pathData widgets from the spectrum.
        """
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
            newFilePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())

            if spectrum.filePath != newFilePath:

                from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
                if dataType == 'Spectrum':
                    spectrum.filePath = newFilePath
                else:
                    getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

                # set the widget text
                # self._setPathData(spectrum)

    def _toggleValid(self):
        ind = self.showValid.getIndex()
        if ind == 0:
            valid = True
            allVisible = False
        elif ind == 1:
            valid = False
            allVisible = False
        else:
            valid = True
            allVisible = True

        for spectrum in self.spectra:
            visible = True if allVisible else (spectrum.isValidPath is valid)
            if spectrum in self.spectrumData:
                widgets = self.spectrumData[spectrum]
                for widg in widgets:
                    widg.setVisible(visible)

    def _findDataPath(self, storeType):
        dataUrl = self.project._apiNmrProject.root.findFirstDataLocationStore(
                name='standard').findFirstDataUrl(name=storeType)
        return dataUrl.url.dataLocation

    def _findDataUrl(self, storeType):
        dataUrl = self.project._apiNmrProject.root.findFirstDataLocationStore(
                name='standard').findFirstDataUrl(name=storeType)
        if dataUrl:
            return (dataUrl,)
        else:
            return ()

    def _validateAll(self):
        """Validate all the objects as the dataUrls may have changed.
        """
        for url in self.allUrls:
            self._setUrlData(url)
        for spectrum in self.spectra:
            self._setPathData(spectrum)

    def _closeButton(self):
        self.accept()

    def _apply(self):
        # apply all the buttons
        for spectrum in self.spectra:
            self._setSpectrumPath(spectrum)
        for url in self.allUrls:
            self._setDataUrlPath(url)

        self.accept()

