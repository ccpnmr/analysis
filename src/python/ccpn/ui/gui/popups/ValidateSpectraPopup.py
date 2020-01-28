"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2020"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2020-01-28 00:02:07 +0000 (Tue, January 28, 2020) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-01-17 13:27:03 +0000 (Fri, January 17, 2020) $"
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
INSIDEDATA = 'insideData'
ALONGSIDEDATA = 'alongsideData'
REMOTEDATA = 'remoteData'
STANDARD = 'standard'
VALIDSTORENAMES = (('$DATA', REMOTEDATA),
                   ('$INSIDEDATA', INSIDEDATA),
                   ('ALONGSIDEDATA', ALONGSIDEDATA))
DIRSEP = '/'
SHOWDATAURLS = True


def _checkStoreName(name):
    for checkName, remoteName in VALIDSTORENAMES:
        if name.startswith(checkName):
            return DIRSEP.join([remoteName, name[len(checkName) + 1:]])
            # return os.path.join(remoteName, name[len(checkName) + 1:])
    return name


def _expandFilePath(project, spectrum, filePath: str) -> str:
    # filePath = filePath.strip()
    storeName = spectrum._wrappedData.dataStore.dataUrl.name
    # storeName = _checkStoreName(storeName)
    if filePath.startswith(storeName):
        filePath = spectrum._wrappedData.dataStore.fullPath

    return filePath


class SpectrumValidator(QtGui.QValidator):
    """Validator class to handle marking status of spectra.
    Entry is marked green if the spectrum path points to a valid spectrum file, otherwise red
    """

    def __init__(self, spectrum, parent=None, validationType='exists'):
        super().__init__(parent=parent)

        self.spectrum = spectrum
        self.validationType = validationType
        self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)

    def validate(self, p_str, p_int):
        if self.validationType != 'exists':
            raise NotImplemented('%s only checks that the path exists', self.__class__.__name__)

        # filePath = ccpnUtil.expandDollarFilePath(self.spectrum._project, self.spectrum, p_str.strip())
        filePath = _expandFilePath(self.spectrum._project, self.spectrum, p_str)

        # filePath = p_str.strip()

        palette = self.parent().palette()

        if os.path.exists(filePath):
            if filePath == self.spectrum.filePath:
                palette.setColor(QtGui.QPalette.Base, VALIDROWCOLOUR)
            else:
                from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                # NOTE:ED - only search the current filePath
                dataType, subType, usePath = ioFormats.analyseUrl(filePath, recursiveSearch=False)
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

    @property
    def checkState(self):
        state, _, _ = self.validate(self.parent().text(), 0)
        return state


class DataUrlValidator(QtGui.QValidator):
    """Validator class to handle marking status of dataUrls.
    Entry is marked red if any referenced spectra are invalid
    """

    def __init__(self, dataUrl, parent=None, validationType='exists'):
        QtGui.QValidator.__init__(self, parent=parent)
        self.dataUrl = dataUrl
        self.validationType = validationType
        self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)

    def validate(self, p_str, p_int):
        if self.validationType != 'exists':
            raise NotImplemented('%s only checks that the path exists', self.__class__.__name__)
        # filePath = ccpnUtil.expandDollarFilePath(self.spectrum._project, self.spectrum, p_str.strip())
        filePath = p_str

        palette = self.parent().palette()

        if os.path.isdir(filePath):

            # validate dataStores
            localStores = tuple(store for store in self.dataUrl.sortedDataStores()) if self.dataUrl else ()
            for store in localStores:
                # if not os.path.exists(os.path.join(filePath, store.path)):
                if not os.path.exists(DIRSEP.join([filePath, store.path])):
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

    @property
    def checkState(self):
        state, _, _ = self.validate(self.parent().text(), 0)
        return state


VALIDSPECTRA = 'valid'
INVALIDSPECTRA = 'invalid'
ALLSPECTRA = 'all'
DEFAULTSELECTED = (VALIDSPECTRA, INVALIDSPECTRA, ALLSPECTRA)
MAXIMUMSCROLLROW = 1000


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
        self._dataUrlSpacer = None

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
        self.dataIndexing = OrderedDict()

        self.project._validateCleanUrls()

        if self.VIEWDATAURLS:
            # populate the widget with a list of spectrum buttons and filepath buttons
            scrollRow = 0

            standardStore = self.project._wrappedData.memopsRoot.findFirstDataLocationStore(name=STANDARD)
            stores = [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls() for url in store.sortedDataStores()]
            urls = [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]

            # all the urls except remoteData
            self.allUrls = [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores()
                            for dataUrl in store.sortedDataUrls() if dataUrl.name not in (INSIDEDATA, ALONGSIDEDATA)]

            urls = self._findDataUrl(REMOTEDATA)
            # urls = _findDataUrl(self, REMOTEDATA)
            for url in urls:
                label = self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=True)
                label.setText('$DATA (user datapath)')
                scrollRow += 1

            urls = self._findDataUrl(INSIDEDATA)
            # urls = _findDataUrl(self, INSIDEDATA)
            for url in urls:
                label = self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=False)
                label.setText('$INSIDE')
                scrollRow += 1

            urls = self._findDataUrl(ALONGSIDEDATA)
            # urls = _findDataUrl(self, ALONGSIDEDATA)
            for url in urls:
                label = self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=scrollRow, enabled=False)
                label.setText('$ALONGSIDE')
                scrollRow += 1

            if self.application._isInDebugMode or SHOWDATAURLS:
                self.otherUrls = [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores()
                                  for dataUrl in store.sortedDataUrls() if dataUrl.name not in (INSIDEDATA, ALONGSIDEDATA, REMOTEDATA)]

                for url in self.otherUrls:
                    # only show the urls that contain spectra
                    if url.sortedDataStores():
                        self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=0, enabled=True)
                    else:
                        self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=0, enabled=False)
                    scrollRow += 1

            # finalise the dataUrl ScrollArea
            # Spacer(self.dataUrlScrollAreaWidgetContents, 0, 0,
            #        QtWidgets.QSizePolicy.MinimumExpanding, self.VERTICALSIZEPOLICY,
            #        grid=(MAXIMUMSCROLLROW, 1), gridSpan=(1, 1))
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

            # standardStore = self.project._wrappedData.memopsRoot.findFirstDataLocationStore(name=STANDARD)
            # stores = [(store.name, store.url.dataLocation, url.path,) for store in standardStore.sortedDataUrls() for url in store.sortedDataStores()]
            # urls = [(store.dataUrl.name, store.dataUrl.url.dataLocation, store.path,) for store in standardStore.sortedDataStores()]
            # [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores() for dataUrl in store.sortedDataUrls()]

            if self.spectra:
                for spectrum in self.spectra:
                    # if not spectrum.isValidPath:

                    pathLabel = Label(self.spectrumScrollAreaWidgetContents, text=spectrum.pid, grid=(scrollRow, 0))
                    pathUrlLabel = Label(self.spectrumScrollAreaWidgetContents, text='', grid=(scrollRow, 1))
                    pathUrlLabel.setVisible(self.application._isInDebugMode)

                    pathData = LineEdit(self.spectrumScrollAreaWidgetContents, textAlignment='left', grid=(scrollRow, 2))
                    pathData.setValidator(SpectrumValidator(parent=pathData, spectrum=spectrum))
                    pathButton = Button(self.spectrumScrollAreaWidgetContents, grid=(scrollRow, 3), callback=partial(self._getSpectrumFile, spectrum),
                                        icon='icons/directory')

                    self.spectrumData[spectrum] = (pathData, pathButton, pathLabel, pathUrlLabel)
                    self._populatePathData(spectrum)

                    # pathData.editingFinished.connect(partial(self._setSpectrumPath, spectrum))
                    pathData.textEdited.connect(partial(self._filePathConnect, spectrum))

                    scrollRow += 1

            # finalise the spectrumScrollArea
            Spacer(self.spectrumScrollAreaWidgetContents, 0, 0,
                   QtWidgets.QSizePolicy.MinimumExpanding, self.VERTICALSIZEPOLICY,
                   grid=(scrollRow, 2), gridSpan=(1, 1))

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
            self._populateUrlData(dataUrl)

        for spectrum in self.spectra:
            self._populatePathData(spectrum)

    def _clearOldUrlWidgets(self):
        """Clear the old dataUrl elements that are pointing to urls with no dataStores
        """
        self.otherUrls = [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores()
                          for dataUrl in store.sortedDataUrls() if dataUrl.name not in (INSIDEDATA, ALONGSIDEDATA, REMOTEDATA)]
        self.project._validateCleanUrls()

        for url in self.otherUrls:
            # only show the urls that contain spectra
            if url.sortedDataStores():
                pass
            else:
                if url in self.dataUrlData:
                    urlData, urlButton, urlLabel = self.dataUrlData[url]
                    urlData.hide()
                    urlButton.hide()
                    urlLabel.hide()
                    urlData.deleteLater()
                    urlButton.deleteLater()
                    urlLabel.deleteLater()
                    del self.dataUrlData[url]
                    # delete the dataUrl
        # self.project._validateCleanUrls()

    def _addNewUrlWidgets(self):
        if self.application._isInDebugMode or SHOWDATAURLS:
            self.otherUrls = [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores()
                              for dataUrl in store.sortedDataUrls() if dataUrl.name not in (INSIDEDATA, ALONGSIDEDATA, REMOTEDATA)]

            for url in self.otherUrls:
                # only show the urls that contain spectra
                if url.sortedDataStores():
                    self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=None, enabled=True)
                else:
                    self._addUrlWidget(self.dataUrlScrollAreaWidgetContents, url, urlList=self.dataUrlData, scrollRow=None, enabled=False)

    def _addUrlWidget(self, widget, dataUrl, urlList, scrollRow=None, enabled=True):
        """add a url row to the frame if it doesn't exist
        """
        if dataUrl in urlList:
            return

        # remove unneeded spacers
        layout = widget.getLayout()
        spacers = [layout.itemAt(itmNum) for itmNum in range(layout.count()) if isinstance(layout.itemAt(itmNum), Spacer)]
        for sp in spacers:
            layout.removeItem(sp)

        scrollRow = widget.getLayout().rowCount()
        urlLabel = Label(widget, text=dataUrl.name, grid=(scrollRow, 0))
        urlData = LineEdit(widget, textAlignment='left', grid=(scrollRow, 1))

        urlData.setValidator(DataUrlValidator(parent=urlData, dataUrl=dataUrl))
        if enabled:
            pass

            # urlData.setValidator(DataUrlValidator(parent=urlData, dataUrl=dataUrl))
        else:
            # set to italic/grey
            oldFont = urlData.font()
            oldFont.setItalic(True)
            urlData.setFont(oldFont)

        urlButton = Button(widget, grid=(scrollRow, 2), callback=partial(self._getDataUrlDialog, dataUrl),
                           icon='icons/directory')

        urlList[dataUrl] = (urlData, urlButton, urlLabel)
        self._populateUrlData(dataUrl)
        # _setUrlData(self, dataUrl, self.dataUrlData[dataUrl])
        urlData.setEnabled(enabled)
        urlButton.setEnabled(enabled)
        urlButton.setVisible(enabled)

        # urlData.editingFinished.connect(partial(self._setDataUrlPath, dataUrl))
        urlData.textEdited.connect(partial(self._dataUrlConnect, dataUrl))

        # add a new spacer at the bottom
        Spacer(widget, 0, 0,
               QtWidgets.QSizePolicy.MinimumExpanding, self.VERTICALSIZEPOLICY,
               grid=(scrollRow + 1, 1), gridSpan=(1, 1))

        return urlLabel

    def _updateUrlWidgets(self):
        pass

    # @staticmethod
    # def _fetchDataUrl(self: 'MemopsRoot', fullPath: str) -> 'DataUrl':
    #     """Get or create DataUrl that matches fullPath, prioritising insideData, alongsideDta, remoteData
    #     and existing dataUrls"""
    #     from ccpnmodel.ccpncore.api.memops.Implementation import Url
    #     from ccpn.util import Path
    #
    #     standardStore = self.findFirstDataLocationStore(name=STANDARD)
    #     fullPath = Path.normalisePath(fullPath, makeAbsolute=True)
    #     standardTags = (REMOTEDATA,)
    #     # Check standard DataUrls first
    #     checkUrls = [standardStore.findFirstDataUrl(name=tag) for tag in standardTags]
    #     # Then check other existing DataUrls
    #     checkUrls += [x for x in standardStore.sortedDataUrls() if x.name not in standardTags]
    #     for dataUrl in checkUrls:
    #         directoryPath = os.path.join(dataUrl.url.path, '')
    #         if fullPath.startswith(directoryPath):
    #             break
    #     else:
    #         # No matches found, make a new one
    #         dirName, path = os.path.split(fullPath)
    #         dataUrl = standardStore.newDataUrl(url=Url(path=fullPath))
    #     #
    #     return dataUrl

    def dataUrlFunc(self, dataUrl, newUrl):
        """Set the new url in the dataUrl
        """
        # tempDataUrl = self._fetchDataUrl(dataUrl.root, newUrl)
        # #
        # dataUrl.url = tempDataUrl.url
        # # pass

        #
        # okay, this seems to be working now
        dataUrl.url = dataUrl.url.clone(path=newUrl)
        self._validateSpectra()
        return

        # oldDataUrl = dataUrl
        # newDataUrl = None
        #
        # self.project._validateCleanUrls()
        #
        # from ccpnmodel.ccpncore.lib._ccp.general.DataLocation.AbstractDataStore import forceChangeDataStoreUrl
        #
        # for spec in self.project.spectra:
        #     apiDataStore = spec._wrappedData.dataStore
        #     if apiDataStore:  # is None:
        #         # getLogger().warning("Spectrum is not stored, cannot change file path")
        #         #
        #         # else:
        #         # dataUrl = self._project._wrappedData.root.fetchDataUrl(value)
        #
        #         # temporary skip
        #         if apiDataStore.dataUrl != oldDataUrl:
        #             continue
        #
        #         print('>>>   found', spec.pid, apiDataStore.dataUrl.name)
        #
        #         dataUrlName = apiDataStore.dataUrl.name
        #         # if dataUrlName == REMOTEDATA:
        #         if dataUrlName not in (INSIDEDATA, ALONGSIDEDATA):
        #
        #             lastDataUrl = newDataUrl
        #             newDataUrl = forceChangeDataStoreUrl(apiDataStore, newUrl)
        #             print('>>>validate cleanup urls: newDataUrl', oldDataUrl, newDataUrl)
        #
        #             if lastDataUrl and newDataUrl and lastDataUrl != newDataUrl:
        #                 print('>>>validate cleanup urls: Url conflict')
        #
        #             # apiDataStore.repointToDataUrl(dataUrl)
        #             # apiDataStore.path = apiDataStore.fullPath[len(dataUrl.url.path) + 1:]
        #
        #             if newDataUrl:
        #                 # update the links with the new dataUrl
        #                 for uu, (urlData, urlButton, urlLabel) in list(self.dataUrlData.items()):
        #
        #                     if uu == oldDataUrl:
        #                         print('>>>validate update widgets')
        #
        #                         self.dataUrlData[newDataUrl] = (urlData, urlButton, urlLabel)
        #                         urlButton.setCallback(partial(self._getDataUrlDialog, newDataUrl))
        #                         urlData.textEdited.disconnect()
        #                         urlData.textEdited.connect(partial(self._dataUrlConnect, newDataUrl))
        #
        #                         # urlData.setValidator(DataUrlValidator(parent=urlData, dataUrl=newDataUrl))
        #                         urlData.validator().dataUrl = newDataUrl
        #                         del self.dataUrlData[oldDataUrl]
        #
        #                         self.allUrls.append(newDataUrl)
        #                         self.allUrls.remove(oldDataUrl)

        # # reset the dataStores
        # localDataUrlData = {}
        # localDataUrlData[REMOTEDATA] = self._findDataUrl(REMOTEDATA)
        # localDataUrlData[INSIDEDATA] = self._findDataUrl(INSIDEDATA)
        # localDataUrlData[ALONGSIDEDATA] = self._findDataUrl(ALONGSIDEDATA)
        # localDataUrlData['otherData'] = [dataUrl for store in self.project._wrappedData.memopsRoot.sortedDataLocationStores()
        #                             for dataUrl in store.sortedDataUrls() if dataUrl.name not in (INSIDEDATA, ALONGSIDEDATA, REMOTEDATA)]
        #
        # standardStore = self.project._wrappedData.memopsRoot.findFirstDataLocationStore(name=STANDARD)
        #
        # spectraStores = [spec._wrappedData.dataStore for spec in self.spectra]
        # bad = [url for store in standardStore.sortedDataUrls() for url in store.sortedDataStores() if url not in spectraStores]
        # badStore = [store for store in standardStore.sortedDataUrls() if store.name == REMOTEDATA if not store.dataStores]
        #
        # for bb in bad:
        #     print('>>>validate cleanup urls: %s' % str(bb))
        #     bb.delete()
        #
        # for url in localDataUrlData['otherData']:
        #     if not url.dataStores:
        #         print('>>>validate cleanup stores: %s' % str(url))
        #         url.delete()
        #
        # for bb in badStore[1:]:
        #     print('>>>validate cleanup remoteStores: %s' % str(bb))
        #     bb.delete()

        # clean up the data urls links to the widgets

        self.project._validateCleanUrls()

        self._validateSpectra()

        # print('>>>dataUrlFunc - clone dataUrl', dataUrl.url.dataLocation)

    def _getDataUrlDialog(self, dataUrl):
        """Get the path from the widget and call the open dialog.
        """
        if dataUrl and dataUrl in self.dataUrlData:

            print('>>>>dataurlget', str(dataUrl))

            urlData, urlButton, urlLabel = self.dataUrlData[dataUrl]
            urlNum = list(self.dataUrlData.keys()).index(dataUrl)

            newUrl = urlData.text().strip()

            dialog = FileDialog(self, text='Select DataUrl File', directory=newUrl,
                                fileMode=FileDialog.Directory, acceptMode=0,
                                preferences=self.application.preferences.general)
            directory = dialog.selectedFiles()
            if directory and len(directory) > 0:
                newUrl = directory[0]

                # newUrl cannot be '' otherwise the api cannot re-load the project
                if newUrl:

                    # populate the widget
                    self._populateUrlData(dataUrl, newFilePath=newUrl)

                    # only accept valid paths from the urlData box
                    urlValid = urlData.validator().checkState == QtGui.QValidator.Acceptable

                    # NOTE:ED AUTOUPDATE
                    if not self.AUTOUPDATE and self._dataUrlCallback:
                        self._dataUrlCallback(dataUrl, newUrl, urlValid, urlNum)
                        self._validateSpectra()

                    elif dataUrl.url.dataLocation != newUrl:
                        # define a function to clone the dataUrl
                        self.dataUrlFunc(dataUrl, newUrl)

    def _dataUrlConnect(self, dataUrl):
        """CALLBACK FROM DATAURL WIDGET LINEEDIT by pressing enter/pressing a key
        Set the dataUrl from the widget
        """
        self._setDataUrlPath(dataUrl)

    def _setDataUrlPath(self, dataUrl):
        """Set the dataUrl from the widget
        """
        # print('>>>>_setDataUrlPath pre', str(dataUrl))

        if dataUrl and dataUrl in self.dataUrlData:

            # print('>>>>_setDataUrlPath', str(dataUrl))

            urlData, urlButton, urlLabel = self.dataUrlData[dataUrl]
            urlNum = list(self.dataUrlData.keys()).index(dataUrl)

            newUrl = urlData.text().strip()

            # newUrl cannot be '' otherwise the api cannot re-load the project
            if newUrl:

                # only accept valid paths from the urlData box
                urlValid = (urlData.validator().checkState == QtGui.QValidator.Acceptable)

                # NOTE:ED AUTOUPDATE
                if not self.AUTOUPDATE and self._dataUrlCallback:
                    print('>>>  dataUrl callback and validate')
                    self._dataUrlCallback(dataUrl, newUrl, urlValid, urlNum)
                    self._validateSpectra()

                elif dataUrl.url.dataLocation != newUrl:
                    # define a function to clone the dataUrl
                    print('>>>  dataUrl callback')
                    self.dataUrlFunc(dataUrl, newUrl)

                # print('>>>_setDataUrlPath post', dataUrl.url.dataLocation)

    def _populateUrlData(self, dataUrl, newFilePath=None):
        """Set the urlData widgets from the dataUrl.
        """
        if dataUrl not in self.dataUrlData:
            return

        urlData, urlButton, urlLabel = self.dataUrlData[dataUrl]

        if dataUrl:
            urlData.setText(newFilePath if newFilePath else dataUrl.url.path)
            # if urlData.validator:
            valid = urlData.validator()
            if valid and hasattr(valid, 'resetCheck'):
                urlData.validator().resetCheck()

    def filePathFunc(self, spectrum, filePath):
        """Set the new filePath for the spectrum
        """
        if filePath:
            try:
                # storeName = spectrum._wrappedData.dataStore.dataUrl.name
                # if filePath.startswith(storeName):
                #     print('>>>filePathFunc storeName', filePath)
                #     spectrum._wrappedData.dataStore.path = filePath[len(storeName) + 1:]
                # else:
                #     print('>>>filePathFunc - ', filePath)
                spectrum.filePath = filePath
            except:
                # ignore filePath warning for the minute
                pass

            finally:
                self._clearOldUrlWidgets()
                self._validateDataUrls()

    def _getSpectrumFile(self, spectrum):
        """Get the path from the widget and call the open dialog.
        """
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel, pathUrlLabel = self.spectrumData[spectrum]
            specNum = list(self.spectrumData.keys()).index(spectrum)

            # filePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())
            filePath = _expandFilePath(self.project, spectrum, pathData.text())

            dialog = FileDialog(self, text='Select Spectrum File', directory=filePath,
                                fileMode=1, acceptMode=0,
                                preferences=self.application.preferences.general)
            directory = dialog.selectedFiles()
            if directory and len(directory) > 0:
                newFilePath = directory[0]

                # if spectrum.filePath != newFilePath:

                from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

                dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
                if dataType == 'Spectrum':
                    pass

                # # populate the widget
                # self._populatePathDataFromUrl(spectrum, newFilePath)

                # NOTE:ED AUTOUPDATE
                if not self.AUTOUPDATE and self._filePathCallback:
                    self._filePathCallback(spectrum, newFilePath, specNum)
                    self._validateDataUrls()
                else:
                    # define a function to update the filePath
                    self.filePathFunc(spectrum, newFilePath)

                    # spectrum.filePath = newFilePath

                # else:
                #     getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

                # set the widget text
                self._populatePathData(spectrum)
                # self._validateAll()

    def _populatePathDataFromUrl(self, spectrum, newFilePath):
        """Set the pathData widgets from the filePath
        Creates a temporary dataUrl to get the required data location
        to populate the widget
        """
        if spectrum and spectrum in self.spectrumData:
            with undoStackBlocking():
                pathData, pathButton, pathLabel, pathUrlLabel = self.spectrumData[spectrum]

                # # create a new temporary dataUrl to validate the path names
                # tempDataUrl = spectrum.project._wrappedData.root.fetchDataUrl(newFilePath)
                #
                # # get the list of dataUrls
                # apiDataStores = [store for store in tempDataUrl.sortedDataStores() if store.fullPath == newFilePath]
                # if not apiDataStores:
                #     return
                #
                # apiDataStore = apiDataStores[0]

                apiDataStore = spectrum._wrappedData.dataStore

                self._populatePathNamesInWidgets(apiDataStore, pathData, pathUrlLabel)

    def _populatePathNamesInWidgets(self, apiDataStore, pathData, pathUrlLabel):
        if not apiDataStore:
            pathData.setText('<None>')

        elif apiDataStore.dataLocationStore.name == STANDARD:

            # dataUrlName = apiDataStore.dataUrl.name
            #     if dataUrlName == INSIDEDATA:
            #         pathData.setText('$INSIDE/%s' % apiDataStore.path)
            #     elif dataUrlName == ALONGSIDEDATA:
            #         pathData.setText('$ALONGSIDE/%s' % apiDataStore.path)
            #     elif dataUrlName == REMOTEDATA:
            #         pathData.setText('$DATA/%s' % apiDataStore.path)
            # pathData.setText(os.path.join(apiDataStore.dataUrl.name, apiDataStore.path))
            # pathData.setText(apiDataStore.fullPath)
            pathData.setText(DIRSEP.join([apiDataStore.dataUrl.url.path, apiDataStore.path]))
        else:
            # TODO:ED check this
            pathData.setText(apiDataStore.fullPath)

        pathUrlLabel.set(apiDataStore.dataUrl.name)
        # print('>>>   pathData', apiDataStore.dataUrl.name)
        # print('>>>   pathData', apiDataStore.dataUrl.url.path)
        # print('>>>   pathData', apiDataStore.path, apiDataStore.path == apiDataStore.fullPath)

        pathData.validator().resetCheck()

    def _populatePathData(self, spectrum):
        """Set the pathData widgets from the spectrum.
        """
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel, pathUrlLabel = self.spectrumData[spectrum]

            apiDataStore = spectrum._apiDataSource.dataStore
            self._populatePathNamesInWidgets(apiDataStore, pathData, pathUrlLabel)

    def _filePathConnect(self, spectrum):
        """CALLBACK FROM PATH WIDGET LINEEDIT by pressing enter/pressing a key
        Set the spectrum path from the widget
        """
        self._setSpectrumPath(spectrum)

    def _setSpectrumPath(self, spectrum, update=True):
        """Set the spectrum path from the widget
        """
        if spectrum and spectrum in self.spectrumData:
            pathData, pathButton, pathLabel, pathUrlLabel = self.spectrumData[spectrum]
            specNum = list(self.spectrumData.keys()).index(spectrum)

            # newFilePath = ccpnUtil.expandDollarFilePath(self.project, spectrum, pathData.text().strip())
            newFilePath = _expandFilePath(self.project, spectrum, pathData.text())

            # print('>>> _setSpectrumPath', newFilePath)
            # if spectrum.filePath != newFilePath:

            from ccpnmodel.ccpncore.lib.Io import Formats as ioFormats

            dataType, subType, usePath = ioFormats.analyseUrl(newFilePath)
            if dataType == 'Spectrum':
                pass

            # current spectrum dataUrl
            dataUrl = spectrum._wrappedData.dataStore.dataUrl
            cursorPosition = pathData.cursorPosition()

            # NOTE:ED AUTOUPDATE
            if not self.AUTOUPDATE and self._filePathCallback:
                self._filePathCallback(spectrum, newFilePath, specNum)
                self._validateDataUrls()
            else:
                # define a function to update the filePath
                # print('>>>  filePath callback')
                self.filePathFunc(spectrum, newFilePath)

            # dataUrl may have changed
            newDataUrl = spectrum._wrappedData.dataStore.dataUrl
            if (dataUrl != newDataUrl):
                # add new dataPath to widget list and cleanup(later)
                self._addNewUrlWidgets()
                self._clearOldUrlWidgets()

            # else:
            #     getLogger().warning('Not a spectrum file: %s - (%s, %s)' % (newFilePath, dataType, subType))

            # set the widget text
            if update:
                self._populatePathData(spectrum)
            # diffLen = len(dataUrl.name) - len(newDataUrl.name)
            # print('>>> cursorPos', diffLen, dataUrl.name, newDataUrl.name)

            diffLen = len(dataUrl.url.path) - len(newDataUrl.url.path)
            # print('>>> cursorPos', diffLen, dataUrl.name, newDataUrl.name)

            pathData.setCursorPosition(cursorPosition)
            # pathData.setCursorPosition(cursorPosition + (diffLen if cursorPosition > len(dataUrl.name) else 0))

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
                name=STANDARD).findFirstDataUrl(name=storeType)
        return dataUrl.url.dataLocation

    def _findDataUrl(self, storeType):
        dataUrl = self.project._apiNmrProject.root.findFirstDataLocationStore(
                name=STANDARD).findFirstDataUrl(name=storeType)
        if dataUrl:
            return (dataUrl,)
        else:
            return ()

    def _validateDataUrls(self):
        # print('>>> _validateDataUrls')
        for url in self.allUrls:
            self._populateUrlData(url)
            # _setUrlData(self, url, self.dataUrlData[url])
            if not (url and url.url and url.url.path):
                self._badUrls = True

    def _validateSpectra(self):
        # print('>>> _validateSpectra')
        if self.spectra:
            for spectrum in self.spectra:
                self._populatePathData(spectrum)

    def _validateAll(self):
        """Validate all the objects as the dataUrls may have changed.
        """
        # print('>>> validateAll')

        self._validateDataUrls()
        self._validateSpectra()

        # self._badUrls = False
        # for url in self.allUrls:
        #     self._setUrlData(url)
        #     # _setUrlData(self, url, self.dataUrlData[url])
        #     print('  >>> vvv', url.url.path)
        #     if not url.url.path:
        #         print('    >>> vvv', url.url.path)
        #         self._badUrls = True
        # print('>>> vvv')
        #
        # if self.spectra:
        #     for spectrum in self.spectra:
        #         self._setPathData(spectrum)

        # if self.ENABLECLOSEBUTTON:
        #     applyButtons = getattr(self._parent, 'applyButtons', None)
        #     if applyButtons:
        #         applyButtons.getButton('Close').setEnabled(not self._badUrls)

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

    def resizeEvent(self, ev) -> None:
        super().resizeEvent(ev)

        def _getColWidths(layout):
            """Get the colWidths from the parentWidget layout
            """
            colWidths = [None] * layout.columnCount()

            for index in range(layout.count()):
                row, column, cols, rows = layout.getItemPosition(index)
                wid = layout.itemAt(index).widget()
                if wid and not isinstance(wid, (ValidateSpectraForSpectrumPopup,
                                                ValidateSpectraForPreferences,
                                                ValidateSpectraForPopup,
                                                ValidateSpectraPopup,
                                                HLine)):
                    colWidths[column] = max(wid.width(), colWidths[column] or 0)

            return colWidths

        if self._matchDataUrlWidths and self.VIEWDATAURLS:
            parentLayout = self._matchDataUrlWidths.getLayout()
            dataUrlLayout = self.dataUrlScrollAreaWidgetContents.getLayout()
            dataUrlLayout.setSpacing(parentLayout.spacing())

            for urlData, urlButton, urlLabel in self.dataUrlData.values():
                colWidths = _getColWidths(parentLayout)
                for widget, col in zip((urlLabel, urlData, urlButton), colWidths):
                    if widget and col:
                        widget.setFixedWidth(col)

        if self._matchFilePathWidths and self.spectra and self.VIEWSPECTRA:
            parentLayout = self._matchFilePathWidths.getLayout()
            spectrumLayout = self.spectrumScrollAreaWidgetContents.getLayout()
            spectrumLayout.setSpacing(parentLayout.spacing())

            for spectrum in self.spectra:
                if spectrum and spectrum in self.spectrumData:
                    pathData, pathButton, pathLabel, pathUrlLabel = self.spectrumData[spectrum]

                    colWidths = _getColWidths(parentLayout)
                    for widget, col in zip((pathLabel, pathData, pathButton), colWidths):
                        if widget and col:
                            widget.setFixedWidth(col)


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
