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
ACCEPTROWCOLOUR =  QtGui.QColor('darkseagreen')
REJECTROWCOLOUR = QtGui.QColor('orange')

class ValidatorABC(QtGui.QValidator):

    VALIDROWCOLOUR = QtGui.QColor('palegreen')
    INVALIDROWCOLOUR = QtGui.QColor('lightpink')

    def __init__(self, obj, parent=None, validationType='exists'):
        QtGui.QValidator.__init__(self, parent=parent)
        self.obj = obj
        self.validationType = validationType
        self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)
        self._isValid = True  # The result of the validator

    def validate(self, p_str, p_int):

        if self.validationType != 'exists':
            raise NotImplemented('%s only checks that the path exists', self.__class__.__name__)

        self._isValid = self.isValid(p_str.strip())

        palette = self.parent().palette()
        if self._isValid:
            palette.setColor(QtGui.QPalette.Base, self.VALIDROWCOLOUR)
            state = QtGui.QValidator.Acceptable
        else:
            palette.setColor(QtGui.QPalette.Base, self.INVALIDROWCOLOUR)
            state = QtGui.QValidator.Intermediate
        self.parent().setPalette(palette)

        return state, p_str, p_int

    def clearValidCheck(self):
        palette = self.parent().palette()
        palette.setColor(QtGui.QPalette.Base, self.baseColour)
        self.parent().setPalette(palette)

    def resetCheck(self):
        self.validate(self.parent().text(), 0)

    def isValid(self, value):
        "return True is value is valid; should be subclassed"
        raise NotImplementedError('Implement %s.isValid' % self.__class__.__name__)


class SpectrumValidator(ValidatorABC):

    def isValid(self, value):
        "return True is value is valid"
        ds = DataStore.newFromPath(value, expandData=False, autoRedirect=False)
        return ds.exists()


class DataUrlValidator(ValidatorABC):

    def isValid(self, value):
        "return True is value is valid"
        filePath = aPath(value)
        return filePath.exists() and filePath.is_dir()


class PathRowABC(object):
    """Implements all functionality for a row with label, text and button to select a file path
    """

    validatorClass = None  # Requires subclassing
    dialogFileMode = 1

    def __init__(self, topWidget, labelText, obj, enabled=True, callback=None):
        """
        :param parent:
        :param labelText:
        :param row:
        :param obj: object being displayed
        :param callback: func(pathRow) is called when changing value of the dataWidget
        """
        self.topWidget = topWidget
        self.labelText = labelText
        self.obj = obj
        self.enabled = enabled
        self.callback = callback

        self.row= None  # Undefined
        self.isValid = True
        self.validator = None

    def addRow(self, widget, row):
        """Add the row to widget
        returns self
        """
        self.row = row
        self.labelWidget = Label(widget, text=self.labelText, grid=(row, 0))
        self.dataWidget = LineEdit(widget, textAlignment='left', grid=(row, 1))

        if self.enabled:
            self.validator = self.validatorClass(self.obj, parent=self.dataWidget)
            self.dataWidget.setValidator(self.validator)
            self.dataWidget.textEdited.connect(self._updateAfterEditCallback)
        else:
            # set to italic/grey
            oldFont = self.dataWidget.font()
            oldFont.setItalic(True)
            self.dataWidget.setFont(oldFont)

        self.buttonWidget = Button(widget, grid=(self.row, 2), callback=self._getDialog,
                                   icon='icons/directory')
        self._setDataInWidget(self.getPath())

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
            self._setDataInWidget(newPath)

    def _updateAfterEditCallback(self):
        "Callback after editing "
        path = self.dataWidget.text()
        self.setPath(path)
        self._setDataInWidget(path)

    def _setDataInWidget(self, path):
        self.dataWidget.setText(path)
        self.validate()
        if self.callback:
            self.callback(self)

    def setPath(self, path):
        "Set the path name of the object; requires subclassing"
        pass

    def getPath(self) -> str:
        "Get the path name from the object to edit; requires subclassing"
        pass

    def getDialogPath(self) -> str:
        "Get the directry path to start the selection dialog; optionally can be subclassed"
        return str(aPath(self.getPath()))

    def validate(self):
        "Validate the row, return True if valid"
        if self.validator is not None:
            self.dataWidget.validator()
            if hasattr(self.validator, 'resetCheck'):
                self.validator.resetCheck()
            self.isValid = self.validator._isValid
        return self.isValid

    def setVisible(self, visible):
        "set visibilty of row"
        self.labelWidget.setVisible(visible)
        self.dataWidget.setVisible(visible)
        self.buttonWidget.setVisible(visible)


class SpectrumPathRow(PathRowABC):

    validatorClass = SpectrumValidator
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

    validatorClass = DataUrlValidator
    dialogFileMode = 2

    def getPath(self):
        return self.obj.url.path

    def setPath(self, path):
        # self.obj.url.path = path not allowed?
        oldPath = self.getPath()
        if oldPath != path:
            dataUrl = self.obj
            dataUrl.url = dataUrl.url.clone(path=path)


# Radiobuttons
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

        if spectra is None:
            self.spectra = self.project.spectra
        else:
            self.spectra = spectra

        self.defaultSelected = DEFAULTSELECTED.index(defaultSelected) if defaultSelected in DEFAULTSELECTED else DEFAULTSELECTED.index(ALLSPECTRA)


        self.dataUrlData = {}  # dict with (url, UrlPathRow) tuples
        self.spectrumData = {}  # dict with (spectrum, SpectrumPathRow) tuples
        self._badUrls = False

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
        for urlName, label, enabled, callback in [
                ('remoteData',    '$DATA (user dataPath)', True,  self._validateAll),
                ('insideData',    '$INSIDE              ', False, None),
                ('alongsideData', '$ALONGSIDE           ', False, None),
            ]:

            urls = self._findDataUrl(urlName)
            if len(urls) > 0:
                url = urls[0]
                _row = UrlPathRow(topWidget=self, obj=url, labelText=label, enabled=enabled, callback=callback).addRow(
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

        # radiobuttons
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
        self.setMinimumWidth(800)
        # self.setFixedWidth(self.sizeHint().width()+24)

    def _showRow(self, valid):
        "Return True/False depending on valid and settings of radio buttons"

        doShow = True
        if hasattr(self, 'showValid') and self.showValid is not None:
            ind = self.showValid.getIndex()
            if ind == 0 and not valid:  # show only valid
                doShow = False
            elif ind == 1 and valid: # show only invalid
                doShow = False
            else:  # show all
                doShow = True

        return doShow

    def _toggleValid(self):
        "Toggle rows on or off depending on their state and the settings of the radio buttons"
        for spectrum, row in self.spectrumData.items():
            visible = self._showRow(row.isValid)
            row.setVisible(visible)

    def _findDataUrl(self, storeType):
        dataUrl = self.project._apiNmrProject.root.findFirstDataLocationStore(
                name='standard').findFirstDataUrl(name=storeType)
        if dataUrl:
            return (dataUrl,)
        else:
            return ()

    def _validateAll(self, pathRow):
        """Callback from $DATA url to validate all the spectrum rows as the data Urls may have changed.
        """
        self._badUrls = False
        for spectrum, row in self.spectrumData.items():
            if row == pathRow:
                raise RuntimeError('row == pathRow: this should never happen!')

            valid = row.validate()
            if not valid:
                self._badUrls = True
            visible = self._showRow(valid)
            row.setVisible(visible)

        #self._toggleValid()
        #self.applyButtons.getButton('Close').setEnabled(not self._badUrls)

    def _closeButton(self):
        self.accept()

    def _apply(self):
        # apply all the buttons
        pass
        self.accept()

    def closeEvent(self, event):
        # don't close if there any empty urls, which cause an api crash
        if not self._badUrls:
            super().closeEvent(event)
        else:
            event.ignore()
            showWarning(str(self.windowTitle()), 'Project contains empty dataUrls')