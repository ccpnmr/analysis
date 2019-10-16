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
from collections import OrderedDict
from PyQt5 import QtWidgets, QtGui, QtCore
from ccpn.core.lib import Util as ccpnUtil
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.FileDialog import FileDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.guiSettings import getColours, DIVIDER
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Splitter import Splitter
from ccpn.ui.gui.widgets.MessageDialog import showWarning
from ccpn.ui.gui.lib.GuiPath import VALIDROWCOLOUR, ACCEPTROWCOLOUR, REJECTROWCOLOUR, INVALIDROWCOLOUR
from ccpn.core.lib.ContextManagers import undoStackBlocking


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
                palette.setColor(QtGui.QPalette.Base, VALIDROWCOLOUR)
            else:
                from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                dataType, subType, usePath = ioFormats.analyseUrl(filePath)
                if dataType == 'Spectrum':
                    palette.setColor(QtGui.QPalette.Base, VALIDROWCOLOUR)
                else:
                    palette.setColor(QtGui.QPalette.Base, INVALIDROWCOLOUR)

            state = QtGui.QValidator.Acceptable
        else:
            palette.setColor(QtGui.QPalette.Base, INVALIDROWCOLOUR)
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

            # validate dataStores
            localStores = tuple(store for store in self.dataUrl.sortedDataStores())
            for store in localStores:
                if not os.path.exists(os.path.join(filePath, store.path)):
                    palette.setColor(QtGui.QPalette.Base, INVALIDROWCOLOUR)
                    break
            else:
                palette.setColor(QtGui.QPalette.Base, self.baseColour)

            state = QtGui.QValidator.Acceptable  # entry is valid
        else:
            palette.setColor(QtGui.QPalette.Base, INVALIDROWCOLOUR)
            state = QtGui.QValidator.Intermediate  # entry is NOT valid, but can continue editing
        self.parent().setPalette(palette)

        return state, p_str, p_int

    def clearValidCheck(self):
        palette = self.parent().palette()
        palette.setColor(QtGui.QPalette.Base, self.baseColour)
        self.parent().setPalette(palette)

    def resetCheck(self):
        self.validate(self.parent().text(), 0)


# def _findDataPath(obj, storeType):
#     dataUrl = obj.project._apiNmrProject.root.findFirstDataLocationStore(
#             name='standard').findFirstDataUrl(name=storeType)
#     return dataUrl.url.dataLocation
#
#
# def _findDataUrl(obj, storeType):
#     dataUrl = obj.project._apiNmrProject.root.findFirstDataLocationStore(
#             name='standard').findFirstDataUrl(name=storeType)
#     if dataUrl:
#         return (dataUrl,)
#     else:
#         return ()
#
#
# def _setUrlData(self, dataUrl, urlWidgets):
#     """Set the urlData widgets from the dataUrl.
#     """
#     if isinstance(urlWidgets, (tuple, list)):
#         urlData, _, _ = urlWidgets  #self.dataUrlData[dataUrl]
#     else:
#         urlData = urlWidgets
#
#     urlData.setText(dataUrl.url.dataLocation)
#     # if urlData.validator:
#     valid = urlData.validator()
#     if valid and hasattr(valid, 'resetCheck'):
#         urlData.validator().resetCheck()


VALIDSPECTRA = 'valid'
INVALIDSPECTRA = 'invalid'
ALLSPECTRA = 'all'
DEFAULTSELECTED = (VALIDSPECTRA, INVALIDSPECTRA, ALLSPECTRA)


class ValidateSpectraPopup(CcpnDialog):
    """
    Class to validate the paths of the selected spectra.
    """

    defaultSelected = ALLSPECTRA

    def __init__(self, parent=None, mainWindow=None, spectra=None,
                 title='Validate Spectra', defaultSelected=None, **kwds):

        super().__init__(parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            self.preferences = self.application.preferences
        else:
            self.application = None
            self.project = None
            self.current = None
            self.preferences = None
        self.spectra = spectra
        defaultSelected = defaultSelected if defaultSelected else self.defaultSelected
        self._defaultSelected = DEFAULTSELECTED.index(defaultSelected) if defaultSelected in DEFAULTSELECTED else DEFAULTSELECTED.index(ALLSPECTRA)

        # I think there is a QT bug here - need to set a dummy button first otherwise a click is emitted, will investigate
        rogueButton = Button(self, grid=(0, 0))
        rogueButton.hide()
        self.lastRow = 0

        # add validate frame
        self.validateFrame = ValidateSpectraForPopup(self, mainWindow=mainWindow, spectra=spectra, defaultSelected=self._defaultSelected,
                                                     setLayout=True, showBorder=False, grid=(0, 0), gridSpan=(1, 3))

        # add exit buttons
        self.dialogButtons = ButtonList(self, texts=[self.CLOSEBUTTONTEXT],
                                        callbacks=[self._closeButton],
                                        tipTexts=[''], direction='h',
                                        hAlign='r', grid=(self.lastRow, 0), gridSpan=(1, 3))

        self.setMinimumHeight(500)
        self.setMinimumWidth(600)
        # self.setFixedWidth(self.sizeHint().width()+24)

    def _closeButton(self):
        self.accept()


class ValidateSpectraFrameABC(Frame):
    """
    Class to handle a frame containing the dataPaths
    """

    VIEWDATAURLS = False
    VIEWSPECTRA = False
    ENABLECLOSEBUTTON = False
    AUTOUPDATE = False
    USESCROLLFRAME = False
    SHOWSPECTRUMBUTTONS = False
    USESPLITTER = True
    VERTICALSIZEPOLICY = QtWidgets.QSizePolicy.MinimumExpanding

    _filePathCallback = None
    _dataUrlCallback = None
    _matchDataUrlWidths = None
    _matchFilePathWidths = None
    
    def __init__(self, parent, mainWindow=None, spectra=None, defaultSelected=None, **kwds):
        super().__init__(parent, **kwds)

        row = 0

        # put widget intro here
        self.mainWindow = mainWindow
        if mainWindow:
            self.application = mainWindow.application
            self.project = mainWindow.application.project
            self.current = mainWindow.application.current
            self.preferences = self.application.preferences
        else:
            self.application = None
            self.project = None
            self.current = None
            self.preferences = None
        self.spectra = spectra if spectra else self.project.spectra
        self._defaultSelected = defaultSelected
        self._parent = parent

        # set up a scroll area
        self.dataUrlScrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False, grid=(row, 0), gridSpan=(1, 3))
        self.dataUrlScrollAreaWidgetContents.setAutoFillBackground(False)

        if self.USESCROLLFRAME:
            self.dataUrlScrollArea = ScrollArea(self, setLayout=True, grid=(row, 0), gridSpan=(1, 3))
            self.dataUrlScrollArea.setWidgetResizable(True)
            # self.dataUrlScrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False)
            self.dataUrlScrollArea.setWidget(self.dataUrlScrollAreaWidgetContents)
            self.dataUrlScrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
            self.dataUrlScrollArea.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
            self.dataUrlScrollArea.setStyleSheet("""ScrollArea { border: 0px; }""")
            # self.dataUrlScrollArea.setFixedHeight(120)
        row += 1

        self.allUrls = []
        self.dataUrlData = OrderedDict()

        if self.VIEWDATAURLS:
            # populate the widget with a list of spectrum buttons and filepath buttons
            scrollRow = 0

            standardStore = self.project._wrappedData.memopsRoot.findFirstDataLocationStore(name='standard')
            stores = [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls() for url in store.sortedDataStores()]
            urls = [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]

            self.allUrls = [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores()
                            for dataUrl in store.sortedDataUrls() if dataUrl.name not in ('insideData', 'alongsideData')]

            urls = self._findDataUrl('remoteData')
            # urls = _findDataUrl(self, 'remoteData')
            for url in urls:
                label = self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=True)
                label.setText('$DATA (user datapath)')
                scrollRow += 1

            urls = self._findDataUrl('insideData')
            # urls = _findDataUrl(self, 'insideData')
            for url in urls:
                label = self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=False)
                label.setText('$INSIDE')
                scrollRow += 1

            urls = self._findDataUrl('alongsideData')
            # urls = _findDataUrl(self, 'alongsideData')
            for url in urls:
                label = self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=False)
                label.setText('$ALONGSIDE')
                scrollRow += 1

            if self.application._isInDebugMode:
                otherUrls = [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores()
                             for dataUrl in store.sortedDataUrls() if dataUrl.name not in ('insideData', 'alongsideData', 'remoteData')]

                for url in otherUrls:
                    # only show the urls that contain spectra
                    if url.sortedDataStores():
                        self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=True)
                    else:
                        self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=False)
                    scrollRow += 1

            # finalise the dataUrl ScrollArea
            Spacer(self.dataUrlScrollAreaWidgetContents, 0, 0,
                   QtWidgets.QSizePolicy.MinimumExpanding, self.VERTICALSIZEPOLICY,
                   grid=(scrollRow, 1), gridSpan=(1, 1))
            row += 1

        self._spectrumFrame = Frame(self, setLayout=True, grid=(row, 0), gridSpan=(1, 3), showBorder=False)
        self._spectrumFrame.setAutoFillBackground(False)
        self.spectrumData = OrderedDict()

        if self.VIEWSPECTRA:
            specRow = 0

            if self.VIEWDATAURLS:
                HLine(self._spectrumFrame, grid=(specRow, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)
                specRow += 1

            if self.SHOWSPECTRUMBUTTONS:
                self.buttonFrame = Frame(self._spectrumFrame, setLayout=True, showBorder=False, fShape='noFrame',
                                         grid=(specRow, 0), gridSpan=(1, 3),
                                         vAlign='top', hAlign='left')
                self.showValidLabel = Label(self.buttonFrame, text="Show spectra: ", vAlign='t', grid=(0, 0), bold=True)
                self.showValid = RadioButtons(self.buttonFrame, texts=['valid', 'invalid', 'all'],
                                              selectedInd=self._defaultSelected,
                                              callback=self._toggleValid,
                                              direction='h',
                                              grid=(0, 1), hAlign='l',
                                              tipTexts=None,
                                              )
                specRow += 1

                self._spectrumFrame.addSpacer(5, 10, grid=(specRow, 0))
                specRow += 1

            # set up a scroll area
            self.spectrumScrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False, grid=(specRow, 0), gridSpan=(1, 3))
            self.spectrumScrollAreaWidgetContents.setAutoFillBackground(False)

            if self.USESCROLLFRAME:
                self.spectrumScrollArea = ScrollArea(self._spectrumFrame, setLayout=True, grid=(specRow, 0), gridSpan=(1, 3))
                self.spectrumScrollArea.setWidgetResizable(True)
                # self.spectrumScrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False)
                self.spectrumScrollArea.setWidget(self.spectrumScrollAreaWidgetContents)
                self.spectrumScrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
                self.spectrumScrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
                self.spectrumScrollArea.setStyleSheet("""ScrollArea { border: 0px; }""")
            specRow += 1

            # if not self.spectra:
            #     self.spectra = self.project.spectra

            # populate the widget with a list of spectrum buttons and filepath buttons
            scrollRow = 0
            # self.spectrumData = {}

            # standardStore = self.project._wrappedData.memopsRoot.findFirstDataLocationStore(name='standard')
            # stores = [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls() for url in store.sortedDataStores()]
            # urls = [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]
            # [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores() for dataUrl in store.sortedDataUrls()]

            if self.spectra:
                for spectrum in self.spectra:
                    # if not spectrum.isValidPath:

                    pathLabel = Label(self.spectrumScrollAreaWidgetContents, text=spectrum.pid, grid=(scrollRow, 0))
                    pathData = LineEdit(self.spectrumScrollAreaWidgetContents, textAlignment='left', grid=(scrollRow, 1))
                    pathData.setValidator(SpectrumValidator(parent=pathData, spectrum=spectrum))
                    pathButton = Button(self.spectrumScrollAreaWidgetContents, grid=(scrollRow, 2), callback=partial(self._getSpectrumFile, spectrum),
                                        icon='icons/directory')

                    self.spectrumData[spectrum] = (pathData, pathButton, pathLabel)
                    self._setPathData(spectrum)

                    # pathData.editingFinished.connect(partial(self._setSpectrumPath, spectrum))
                    pathData.textEdited.connect(partial(self._setSpectrumPath, spectrum))

                    scrollRow += 1

            # finalise the spectrumScrollArea
            Spacer(self.spectrumScrollAreaWidgetContents, 0, 0,
                   QtWidgets.QSizePolicy.MinimumExpanding, self.VERTICALSIZEPOLICY,
                   grid=(scrollRow, 1), gridSpan=(1, 1))

            # self._spectrumFrame.addSpacer(5, 10, grid=(specRow, 0))
            # specRow += 1

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        row = 1
        if self.VIEWDATAURLS and self.VIEWSPECTRA and self.USESPLITTER:
            # put a splitter of both are visible
            self.splitter = Splitter(self, grid=(row, 0), setLayout=True, horizontal=False, gridSpan=(1, 3))
            if self.USESCROLLFRAME:
                self.splitter.addWidget(self.dataUrlScrollArea)
            else:
                self.splitter.addWidget(self.dataUrlScrollAreaWidgetContents)
            self.splitter.addWidget(self._spectrumFrame)
            self.getLayout().addWidget(self.splitter, row, 0, 1, 3)
            # self.splitter.setStretchFactor(0, 5)
            # self.splitter.setStretchFactor(1, 1)
            self.splitter.setChildrenCollapsible(False)
            self.splitter.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
            row += 1

        self._parent.lastRow = row

        # check for any bad urls
        self._badUrls = False
        self._validateAll()

    def _populate(self):
        """Populate the frames with the values from dataUrls and project
        """
        for dataUrl in self.dataUrlData:
            self._setUrlData(dataUrl)

        for spectrum in self.spectra:
            self._setPathData(spectrum)

    def _addUrlWidget(self, widget, dataUrl, urlList, scrollRow, enabled=True):
        """add a url row to the frame
        """
        urlLabel = Label(widget, text=dataUrl.name, grid=(scrollRow, 0))
        urlData = LineEdit(widget, textAlignment='left', grid=(scrollRow, 1))

        if enabled:
            urlData.setValidator(DataUrlValidator(parent=urlData, dataUrl=dataUrl))
        else:
            # set to italic/grey
            oldFont = urlData.font()
            oldFont.setItalic(True)
            urlData.setFont(oldFont)

        urlButton = Button(widget, grid=(scrollRow, 2), callback=partial(self._getDataUrlDialog, dataUrl),
                           icon='icons/directory')

        urlList[dataUrl] = (urlData, None, urlLabel)
        self._setUrlData(dataUrl)
        # _setUrlData(self, dataUrl, self.dataUrlData[dataUrl])
        urlData.setEnabled(enabled)
        urlButton.setEnabled(enabled)
        urlButton.setVisible(enabled)

        # urlData.editingFinished.connect(partial(self._setDataUrlPath, dataUrl))
        urlData.textEdited.connect(partial(self._setDataUrlPath, dataUrl))

        return urlLabel

    def dataUrlFunc(self, dataUrl, newUrl):
        """Set the new url in the dataUrl
        """
        dataUrl.url = dataUrl.url.clone(path=newUrl)
        self._validateAll()

    def _getDataUrlDialog(self, dataUrl):
        """Get the path from the widget and call the open dialog.
        """
        if dataUrl and dataUrl in self.dataUrlData:
            urlData, urlButton, urlLabel = self.dataUrlData[dataUrl]
            urlNum = list(self.dataUrlData.keys()).index(dataUrl)

            newUrl = urlData.text().strip()

            dialog = FileDialog(self, text='Select DataUrl File', directory=newUrl,
                                fileMode=FileDialog.Directory, acceptMode=0,
                                preferences=self.application.preferences.general)
            directory = dialog.selectedFiles()
            if len(directory) > 0:
                newUrl = directory[0]

                # newUrl cannot be '' otherwise the api cannot re-load the project
                if newUrl:

                    # NOTE:ED AUTOUPDATE
                    if not self.AUTOUPDATE and self._dataUrlCallback:
                        self._dataUrlCallback(dataUrl, newUrl, urlNum)

                    elif dataUrl.url.dataLocation != newUrl:
                        # define a function to clone the datUrl
                        self.dataUrlFunc(dataUrl, newUrl, urlNum)

                    # dataUrl.url = dataUrl.url.clone(path=newUrl)
                    # set the widget text
                    # self._setUrlData(dataUrl)
                    # self._validateAll()

    def _setDataUrlPath(self, dataUrl):
        """Set the path from the widget by pressing enter
        """
        if dataUrl and dataUrl in self.dataUrlData:
            urlData, urlButton, urlLabel = self.dataUrlData[dataUrl]
            urlNum = list(self.dataUrlData.keys()).index(dataUrl)

            newUrl = urlData.text().strip()

            # newUrl cannot be '' otherwise the api cannot re-load the project
            if newUrl:

                # NOTE:ED AUTOUPDATE
                if not self.AUTOUPDATE and self._dataUrlCallback:
                    self._dataUrlCallback(dataUrl, newUrl, urlNum)

                elif dataUrl.url.dataLocation != newUrl:
                    # define a function to clone the datUrl
                    self.dataUrlFunc(dataUrl, newUrl, urlNum)

                # dataUrl.url = dataUrl.url.clone(path=newUrl)
                # set the widget text
                # self._setUrlData(dataUrl)
                # self._validateAll()

    def _setUrlData(self, dataUrl):
        """Set the urlData widgets from the dataUrl.
        """
        if dataUrl not in self.dataUrlData:
            return

        urlData, urlButton, urlLabel = self.dataUrlData[dataUrl]
        urlData.setText(dataUrl.url.dataLocation)
        # if urlData.validator:
        valid = urlData.validator()
        if valid and hasattr(valid, 'resetCheck'):
            urlData.validator().resetCheck()

    def filePathFunc(self, spectrum, filePath):
        """Set the new filePath for the spectrum
        """
        spectrum.filePath = filePath
        self._validateAll()

    def _getSpectrumFile(self, spectrum):
        """Get the path from the widget and call the open dialog.
        """
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel = self.spectrumData[spectrum]
            specNum = list(self.spectrumData.keys()).index(spectrum)

            filePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())

            dialog = FileDialog(self, text='Select Spectrum File', directory=filePath,
                                fileMode=1, acceptMode=0,
                                preferences=self.application.preferences.general)
            directory = dialog.selectedFiles()
            if directory:
                newFilePath = directory[0]

                # if spectrum.filePath != newFilePath:

                from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
                if dataType == 'Spectrum':

                    # populate the widget
                    self._setPathDataFromUrl(spectrum, newFilePath)

                    # NOTE:ED AUTOUPDATE
                    if not self.AUTOUPDATE and self._filePathCallback:
                        self._filePathCallback(spectrum, newFilePath, specNum)
                    else:
                        # define a function to update the filePath
                        self.filePathFunc(spectrum, newFilePath)

                    # spectrum.filePath = newFilePath

                # else:
                #     getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

                # set the widget text
                # self._setPathData(spectrum)
                # self._validateAll()

    def _setPathDataFromUrl(self, spectrum, newFilePath):
        """Set the pathData widgets from the filePath
        Creates a temporary dataUrl to get the required data location
        to populate the widget
        """
        if spectrum and spectrum in self.spectrumData:
            with undoStackBlocking():
                pathData, pathButton, pathLabel = self.spectrumData[spectrum]

                dataUrl = spectrum.project._wrappedData.root.fetchDataUrl(newFilePath)

                # get the list of dataUrls
                apiDataStores = [store for store in dataUrl.sortedDataStores() if store.fullPath == newFilePath]
                if not apiDataStores:
                    return

                apiDataStore = apiDataStores[0]

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
            specNum = list(self.spectrumData.keys()).index(spectrum)

            newFilePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())

            # if spectrum.filePath != newFilePath:

            from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

            dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
            if dataType == 'Spectrum':

                # populate the widget
                self._setPathDataFromUrl(spectrum, newFilePath)

                # NOTE:ED AUTOUPDATE
                if not self.AUTOUPDATE and self._filePathCallback:
                    self._filePathCallback(spectrum, newFilePath, specNum)
                else:
                    # define a function to update the filePath
                    self.filePathFunc(spectrum, newFilePath)

            # else:
            #     getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

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
        self._badUrls = False
        for url in self.allUrls:
            self._setUrlData(url)
            # _setUrlData(self, url, self.dataUrlData[url])
            if not url.url.path:
                self._badUrls = True

        if self.spectra:
            for spectrum in self.spectra:
                self._setPathData(spectrum)

        if self.ENABLECLOSEBUTTON:
            applyButtons = getattr(self._parent, 'applyButtons', None)
            if applyButtons:
                applyButtons.getButton('Close').setEnabled(not self._badUrls)

    def _apply(self):
        # apply all the buttons
        if self.spectra:
            for spectrum in self.spectra:
                self._setSpectrumPath(spectrum)
        for url in self.allUrls:
            self._setDataUrlPath(url)

        self.accept()

    def closeEvent(self, event):
        # don't close if there any empty urls, which cause an api crash
        if not self._badUrls:
            super().closeEvent(event)
        else:
            event.ignore()
            showWarning(str(self.windowTitle()), 'Project contains empty dataUrls')

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        super().resizeEvent(a0)

        if self._matchDataUrlWidths and self.VIEWDATAURLS:
            parentLayout = self._matchDataUrlWidths.getLayout()
            dataUrlLayout = self.dataUrlScrollAreaWidgetContents.getLayout()
            dataUrlLayout.setSpacing(parentLayout.spacing())

            for urlData, urlButton, urlLabel in self.dataUrlData.values():

                col0 = col1 = col2 = 0

                for index in range(parentLayout.count()):

                    row, column, cols, rows = parentLayout.getItemPosition(index)
                    wid = parentLayout.itemAt(index).widget()

                    if column == 0:
                        if wid and not isinstance(wid, (ValidateSpectraForSpectrumPopup,
                                                        ValidateSpectraForPreferences,
                                                        ValidateSpectraForPopup,
                                                        ValidateSpectraPopup,
                                                        HLine)):

                            # print('>>>wid', wid, row, column, cols, rows, wid.width())
                            col0 = max(wid.width(), col0)

                    elif column == 1:
                        if wid:
                            # print('>>>wid', wid, row, column, cols, rows, wid.width())
                            col1 = max(wid.width(), col1)

                    elif column == 2:
                        if wid and wid.isVisible():
                            # print('>>>wid', wid, row, column, cols, rows, wid.width())
                            col2 = max(wid.width(), col2)

                if urlLabel:
                    urlLabel.setFixedWidth(col0)
                if urlData:
                    urlData.setFixedWidth(col1)
                if urlButton:
                    urlButton.setFixedWidth(col2)

        if self._matchFilePathWidths and self.spectra and self.VIEWSPECTRA:
            parentLayout = self._matchFilePathWidths.getLayout()
            spectrumLayout = self.spectrumScrollAreaWidgetContents.getLayout()
            spectrumLayout.setSpacing(parentLayout.spacing())

            for spectrum in self.spectra[:1]:
                if spectrum and spectrum in self.spectrumData:
                    pathData, pathButton, pathLabel = self.spectrumData[spectrum]

                    col0 = col1 = col2 = 0

                    for index in range(parentLayout.count()):

                        row, column, cols, rows = parentLayout.getItemPosition(index)
                        wid = parentLayout.itemAt(index).widget()

                        if column == 0:
                            if wid and not isinstance(wid, ValidateSpectraForSpectrumPopup):
                                # print('>>>wid', wid, row, column, cols, rows, wid.width())
                                col0 = max(wid.width(), col0)

                        elif column == 1:
                            if wid:
                                # print('>>>wid', wid, row, column, cols, rows, wid.width())
                                col1 = max(wid.width(), col1)

                        elif column == 2:
                            if wid and wid.isVisible():
                                # print('>>>wid', wid, row, column, cols, rows, wid.width())
                                col2 = max(wid.width(), col2)

                    if pathLabel:
                        pathLabel.setFixedWidth(col0)
                    if pathData:
                        pathData.setFixedWidth(col1)
                    if pathButton:
                        pathButton.setFixedWidth(col2)


class ValidateSpectraForPopup(ValidateSpectraFrameABC):
    """
    Class to handle a frame containing the dataUrls/filePaths
    """

    VIEWDATAURLS = True
    VIEWSPECTRA = True
    ENABLECLOSEBUTTON = True
    AUTOUPDATE = True
    USESCROLLFRAME = True
    SHOWSPECTRUMBUTTONS = True
    USESPLITTER = True
    VERTICALSIZEPOLICY = QtWidgets.QSizePolicy.MinimumExpanding


class ValidateSpectraForPreferences(ValidateSpectraFrameABC):
    """
    Class to handle a frame containing the dataUrls/filePaths
    """

    VIEWDATAURLS = True
    VIEWSPECTRA = True
    ENABLECLOSEBUTTON = False
    AUTOUPDATE = False
    USESCROLLFRAME = False
    SHOWSPECTRUMBUTTONS = False
    USESPLITTER = False
    VERTICALSIZEPOLICY = QtWidgets.QSizePolicy.Minimum


class ValidateSpectraForSpectrumPopup(ValidateSpectraFrameABC):
    """
    Class to handle a frame containing the dataUrls/filePaths
    """

    VIEWDATAURLS = False
    VIEWSPECTRA = True
    ENABLECLOSEBUTTON = False
    AUTOUPDATE = False
    USESCROLLFRAME = False
    SHOWSPECTRUMBUTTONS = False
    USESPLITTER = True
    VERTICALSIZEPOLICY = QtWidgets.QSizePolicy.Minimum
