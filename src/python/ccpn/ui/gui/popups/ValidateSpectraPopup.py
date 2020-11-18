"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
from ccpn.core.lib.DataStore import DataStore

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
from ccpn.util.Path import aPath, Path
from ccpn.util.Logging import getLogger

from ccpn.framework.Application import getApplication


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


LINEEDITSMINIMUMWIDTH = 195
VALIDROWCOLOUR = QtGui.QColor('palegreen')
ACCEPTROWCOLOUR =  QtGui.QColor('darkseagreen')
REJECTROWCOLOUR = QtGui.QColor('orange')
INVALIDROWCOLOUR = QtGui.QColor('lightpink')


class SpectrumValidator(QtGui.QValidator):

    def __init__(self, spectrum, parent=None, validationType='exists'):
        QtGui.QValidator.__init__(self, parent=parent)
        self.spectrum = spectrum
        self.validationType = validationType
        self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)

    def validate(self, p_str, p_int):

        if self.validationType != 'exists':
            raise NotImplemented('%s only checks that the path exists', self.__class__.__name__)

        palette = self.parent().palette()

        ds = DataStore.newFromPath(p_str, expandData=False, autoRedirect=False)
        if ds.exists():
            palette.setColor(QtGui.QPalette.Base, VALIDROWCOLOUR)
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

        filePath = aPath(p_str.strip())
        palette = self.parent().palette()

        if filePath.exists() and filePath.is_dir():

            # # validate dataStores
            # localStores = [store for store in self.dataUrl.sortedDataStores()]
            # for store in self.dataUrl.sortedDataStores():
            #     if not os.path.exists(os.path.join(filePath, store.path)):
            #         palette.setColor(QtGui.QPalette.Base, INVALIDROWCOLOUR)
            #         break
            # else:
            #     palette.setColor(QtGui.QPalette.Base, self.baseColour)

            palette.setColor(QtGui.QPalette.Base, VALIDROWCOLOUR)
            state = QtGui.QValidator.Acceptable                                 # entry is valid
        else:
            palette.setColor(QtGui.QPalette.Base, INVALIDROWCOLOUR)
            state = QtGui.QValidator.Intermediate                                   # entry is NOT valid, but can continue editing
        self.parent().setPalette(palette)

        return state, p_str, p_int

    def clearValidCheck(self):
        palette = self.parent().palette()
        palette.setColor(QtGui.QPalette.Base, self.baseColour)
        self.parent().setPalette(palette)

    def resetCheck(self):
        self.validate(self.parent().text(), 0)


class PathRowABC(object):
    """Implements all functionality for a row with label, text and button to select a file path
    """

    validator = None  # Requires subclassing
    dialogFileMode = 1

    def __init__(self, topWidget, labelText, obj, enabled=True):
        """
        :param parent:
        :param labelText:
        :param row:
        :param obj: object being displayed
        :param validator:
        """
        self.topWidget = topWidget
        self.labelText = labelText
        self.obj = obj
        self.enabled = enabled
        self.row= None  # Undefined

    def addRow(self, widget, row):
        """Add the row to widget
        returns self
        """
        self.row = row
        self.labelWidget = Label(widget, text=self.labelText, grid=(row, 0))
        self.dataWidget = LineEdit(widget, textAlignment='left', grid=(row, 1))

        if self.enabled:
            self.dataWidget.setValidator(self.validator(self.obj, parent=self.dataWidget))
            self.dataWidget.textEdited.connect(self.setPath)
        else:
            # set to italic/grey
            oldFont = self.dataWidget.font()
            oldFont.setItalic(True)
            self.dataWidget.setFont(oldFont)

        self.buttonWidget = Button(widget, grid=(self.row, 2),
                                   callback=self._getDialog,
                                   icon='icons/directory')
        self._setDataInWidget()

        self.labelWidget.setEnabled(self.enabled)
        self.dataWidget.setEnabled(self.enabled)
        self.buttonWidget.setVisible(self.enabled)

        return self

    def _getDialog(self):

        dialogPath = self.getDialogPath()
        dialog = FileDialog(parent=self.topWidget, text='Select path', directory=dialogPath,
                            fileMode=self.dialogFileMode, acceptMode=0)
        choices = dialog.selectedFiles()
        if len(choices) > 0:
            newPath = choices[0]
            self.setPath(newPath)
            self._setDataInWidget()

    def setPath(self, path):
        "Set the path name of the object"
        pass

    def getPath(self) -> str:
        "Get the path name from the object to edit"
        pass

    def getDialogPath(self) -> str:
        "Get the directry path to start the selection"
        return str(aPath(self.getPath()))

    def _setDataInWidget(self):
        path = self.getPath()
        self.dataWidget.setText(path)
        valid = self.dataWidget.validator()
        if valid and hasattr(valid, 'resetCheck'):
            self.dataWidget.validator().resetCheck()

    def setVisible(self, visible):
        "set visibilty of row"
        self.labelWidget.setVisible(visible)
        self.dataWidget.setVisible(visible)
        self.buttonWidget.setVisible(visible)


class SpectrumPathRow(PathRowABC):

    validator = SpectrumValidator
    dialogFileMode = 1

    def getPath(self):
        return self.obj.filePath

    def setPath(self, path):
        oldPath = self.getPath()
        if oldPath != path:
            self.obj.filePath = path

    def getDialogPath(self) -> str:
        "Get the directory path to start the selection"
        return str(self.obj.path.parent)


class UrlPathRow(PathRowABC):

    validator = DataUrlValidator
    dialogFileMode = 2

    def getPath(self):
        return self.obj.url.path

    def setPath(self, path):
        # self.obj.url.path = path not allowed?
        oldPath = self.getPath()
        if oldPath != path:
            dataUrl = self.obj
            dataUrl.url = dataUrl.url.clone(path=path)


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

        # TODO I think there is a QT bug here - need to set a dummy button first otherwise a click is emitted, will investigate
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
        # self.dataUrlScrollArea.setFixedHeight(120)
        row += 1

        # populate the widget with a list of spectrum buttons and filepath buttons
        scrollRow = 0
        self.dataUrlData = {}

        for urlName, label, enabled in [
                ('remoteData',    '$DATA (user dataPath)', True),
                ('insideData',    '$INSIDE              ', False),
                ('alongsideData', '$ALONGSIDE           ', False),
            ]:

            urls = self._findDataUrl(urlName)
            if len(urls) > 0:
                url = urls[0]
                _row = UrlPathRow(topWidget=self, obj=url, labelText=label, enabled=enabled).addRow(
                                  widget=self.dataUrlScrollAreaWidgetContents, row=scrollRow)
                scrollRow += 1
                self.dataUrlData[url] = _row

        # finalise the dataUrlScrollArea
        Spacer(self.dataUrlScrollAreaWidgetContents, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(scrollRow, 1), gridSpan=(1, 1))
        row += 1

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        self._spectrumFrame = Frame(self, setLayout=True, grid=(row, 0), gridSpan=(1, 3), showBorder=False)

        specRow = 0
        HLine(self._spectrumFrame, grid=(specRow, 0), gridSpan=(1, 3), colour=getColours()[DIVIDER], height=15)
        specRow += 1

        self.buttonFrame = Frame(self._spectrumFrame, setLayout=True, showBorder=False, fShape='noFrame',
                                 grid=(specRow, 0), gridSpan=(1, 3),
                                 vAlign='top', hAlign='left')
        self.showValidLabel = Label(self.buttonFrame, text="Show spectra: ", vAlign='t', grid=(0, 0), bold=True)
        self.showValid = RadioButtons(self.buttonFrame, texts=['valid', 'invalid', 'all'],
                                      selectedInd=self.defaultSelected,
                                      callback=self._toggleValid,
                                      direction='h',
                                      grid=(0, 1), hAlign='l',
                                      tipTexts=None,
                                      )
        specRow += 1

        self._spectrumFrame.addSpacer(5,10, grid=(specRow,0))
        specRow += 1

        # set up a scroll area
        self.spectrumScrollArea = ScrollArea(self._spectrumFrame, setLayout=True, grid=(specRow, 0), gridSpan=(1, 3))
        self.spectrumScrollArea.setWidgetResizable(True)
        self.spectrumScrollAreaWidgetContents = Frame(self, setLayout=True, showBorder=False)
        self.spectrumScrollArea.setWidget(self.spectrumScrollAreaWidgetContents)
        self.spectrumScrollAreaWidgetContents.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        self.spectrumScrollArea.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.spectrumScrollArea.setStyleSheet("""ScrollArea { border: 0px; }""")
        specRow += 1

        # populate the widget with a list of spectrum buttons and filepath buttons
        scrollRow = 0
        self.spectrumData = {}  # dict with (spectrum, SpectrumPathRow) tuples
        for sp in self.project.spectra:
            _row = SpectrumPathRow(topWidget=self, labelText=sp.pid, obj=sp, enabled=True).addRow(
                                   widget=self.spectrumScrollAreaWidgetContents, row=scrollRow)
            scrollRow += 1
            self.spectrumData[sp] = _row

        # finalise the spectrumScrollArea
        Spacer(self.spectrumScrollAreaWidgetContents, 2, 2,
               QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding,
               grid=(scrollRow, 1), gridSpan=(1, 1))

        self._spectrumFrame.addSpacer(5,10, grid=(specRow,0))
        specRow += 1

        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        row = 1
        self.splitter = Splitter(self, grid=(row, 0), setLayout=True, horizontal=False, gridSpan=(1,3))
        self.splitter.addWidget(self.dataUrlScrollArea)
        self.splitter.addWidget(self._spectrumFrame)
        self.getLayout().addWidget(self.splitter, row, 0, 1, 3)
        # self.splitter.setStretchFactor(0, 5)
        # self.splitter.setStretchFactor(1, 1)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        row += 1

        # add exit buttons
        self.applyButtons = ButtonList(self, texts=['Close'],
                                       callbacks=[self._closeButton],
                                       tipTexts=[''], direction='h',
                                       hAlign='r', grid=(row, 0), gridSpan=(1, 3))

        self.setMinimumHeight(500)
        self.setMinimumWidth(600)
        # self.setFixedWidth(self.sizeHint().width()+24)

        # check for any bad urls
        self._badUrls = False
        self._validateAll()

    def _toggleValid(self):
        "Toggle rows on or off depending on their state and the settings of the radio buttons"
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

        for spectrum, row in self.spectrumData.items():
            visible = True if allVisible else (spectrum.isValidPath is valid)
            row.setVisible(visible)

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
        for spectrum, row in self.spectrumData.items():
            if not spectrum.isValidPath:
                self._badUrls = True

        self.applyButtons.getButton('Close').setEnabled(not self._badUrls)

    def _closeButton(self):
        self.accept()

    def _apply(self):
        # apply all the buttons
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