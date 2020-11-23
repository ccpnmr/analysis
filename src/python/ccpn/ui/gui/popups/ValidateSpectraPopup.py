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
__modifiedBy__ = "$modifiedBy: geertenv $"
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

from PyQt5 import QtWidgets, QtGui

from ccpn.core.lib import Util as ccpnUtil
from ccpn.core.lib.DataStore import DATA_INDENTIFIER, INSIDE_INDENTIFIER, ALONGSIDE_INDENTIFIER, DataStore
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


VALID_ROWCOLOUR = QtGui.QColor('palegreen')
VALID_CHANGED_ROWCOLOUR =  QtGui.QColor('darkseagreen')
WARNING_ROWCOLOUR = QtGui.QColor('orange')
INVALID_ROWCOLOUR = QtGui.QColor('lightpink')
INVALID_CHANGED_ROWCOLOUR = QtGui.QColor('red')


class ValidatorABC(QtGui.QValidator):

    def __init__(self, obj, parent=None, callback=None):
        QtGui.QValidator.__init__(self, parent=parent)
        self.obj = obj
        self.callback = callback

        self._isValid = True  # The result of the validator

    def validate(self, p_str, p_int):

        self._isValid = self.isValid(p_str.strip())
        if self._isValid:
            state = QtGui.QValidator.Acceptable
        else:
            state = QtGui.QValidator.Intermediate

        if self.callback:
            self.callback(self)

        return state, p_str, p_int

    def isValid(self, value):
        "return True is value is valid; should be subclassed"
        raise NotImplementedError('Implement %s.isValid' % self.__class__.__name__)


class SpectrumValidator(ValidatorABC):

    def isValid(self, value):
        "return True is value is valid"
        ds = DataStore.newFromPath(value, expandData=False, autoRedirect=False)
        return ds.exists()
# end class


class DataUrlValidator(ValidatorABC):

    def isValid(self, value):
        "return True is value is valid"
        filePath = aPath(value)
        return filePath.exists() and filePath.is_dir()
# end class


class PathRowABC(object):
    """Implements all functionality for a row with label, text and button to select a file path
    """

    validatorClass = None  # Requires subclassing
    dialogFileMode = 1

    LABELWIDGET_MIN_WIDTH = 200

    def __init__(self, topWidget, labelText, obj, enabled=True, callback=None):
        """
        :param parent:
        :param labelText:
        :param row:
        :param obj: object being displayed
        :param callback: func(self) is called when changing value of the dataWidget
        """
        if self.validatorClass is None:
            raise NotImplementedError('Define %s.validatorClass' % self.__class__.__name__)

        self.topWidget = topWidget
        self.labelText = labelText
        self.obj = obj
        self.enabled = enabled
        self.callback = callback    # callback for this row upon change of value /validate()
                                    # if defined called as: callback(self)

        self.row= None  # Undefined
        self.isValid = True
        self.validator = None  # validator instance of type self.validatorClass
        self.initialValue = None

    @property
    def text(self):
        "Return the text content of the dataWidget"
        return self.dataWidget.text()

    @text.setter
    def text(self, value):
        self.dataWidget.setText(value)

    @property
    def hasChanged(self):
        """Return True if the text value has changed"""
        return (self.initialValue != self.text) #and not self._firstTime

    @property
    def isNotValid(self):
        return not self.isValid

    def addRow(self, widget, row):
        """Add the row to widget
        returns self
        """
        self.row = row
        self.labelWidget = Label(widget, text=self.labelText, grid=(row, 0))
        self.labelWidget.setMinimumWidth(self.LABELWIDGET_MIN_WIDTH)
        self.dataWidget = LineEdit(widget, textAlignment='left', grid=(row, 1))

        if self.enabled:
            self.validator = self.validatorClass(obj=self, parent=self.dataWidget, callback= self._validatorCallback)
            self.dataWidget.setValidator(self.validator)
            # self.dataWidget.textEdited.connect(self._updateAfterEditCallback)
        else:
            # set to italic/grey
            oldFont = self.dataWidget.font()
            oldFont.setItalic(True)
            self.dataWidget.setFont(oldFont)

        self.buttonWidget = Button(widget, grid=(self.row, 2), callback=self._getDialog,
                                   icon='icons/directory')
        # initialise
        self.initialValue = self.getPath()
        self._setDataInWidget(self.initialValue)

        self.labelWidget.setEnabled(self.enabled)
        self.dataWidget.setEnabled(self.enabled)
        self.buttonWidget.setVisible(self.enabled)

        return self

    def _getDialog(self):

        dialogPath = self.getDialogPath()
        dialog = FileDialog(parent=self.topWidget, text='Select path', directory=str(dialogPath),
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
        "Populate the dataWidget, validate and callback"
        self.dataWidget.setText(path)
        self.validate()

    def setPath(self, path):
        "Set the path name of the object; requires subclassing"
        pass

    def getPath(self) -> str:
        "Get the path name from the object to edit; requires subclassing"
        pass

    def getDialogPath(self) -> str:
        "Get the directory path to start the selection dialog; optionally can be subclassed"
        dirPath = Path.home()
        return str(dirPath)

    def _validatorCallback(self, validator):
        """Callback for the validator instance; set path if valid
        Also call self.callback (if defined)
        """
        self.isValid = validator._isValid
        if self.callback:
            self.callback(self)

    def validate(self):
        "Validate the row, return True if valid"
        if self.validator is not None:
            self.validator.validate(self.text, 0)
            self.isValid = self.validator._isValid
        return self.isValid

    def setColour(self, colour):
        "Set the (base) colour of the dataWidget"
        if isinstance(colour,str):
            colour = QtGui.QColor(colour)
        if not isinstance(colour, QtGui.QColor):
            raise ValueError('Invalid colour ("%s"' % colour)
        palette = self.dataWidget.palette()
        palette.setColor(QtGui.QPalette.Base, colour)
        self.dataWidget.setPalette(palette)

    def setVisible(self, visible):
        "set visibilty of row"
        self.labelWidget.setVisible(visible)
        self.dataWidget.setVisible(visible)
        self.buttonWidget.setVisible(visible)
# end class


class SpectrumPathRow(PathRowABC):
    """
    A class to implement a row for spectrum paths
    """
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
# end class


class UrlPathRow(PathRowABC):
    """
    A class to implement a row for url paths
    """
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
# end class


# Radiobuttons
VALID_SPECTRA = 'valid'
INVALID_SPECTRA = 'invalid'
CHANGED_SPECTRA = 'changed'
ALL_SPECTRA = 'all'
buttons = (ALL_SPECTRA, VALID_SPECTRA, INVALID_SPECTRA, CHANGED_SPECTRA)


class ValidateSpectraPopup(CcpnDialog):
    """
    Class to generate a popup to validate the paths of the (selected) spectra.
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

        self.defaultSelected = buttons.index(defaultSelected) \
            if defaultSelected in buttons else buttons.index(ALL_SPECTRA)


        self.dataUrlData = OrderedDict()  # dict with (url, UrlPathRow) tuples
        self.spectrumData = OrderedDict()  # dict with (spectrum, SpectrumPathRow) tuples
        self.dataRow = None # remember the $DATA row

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
        for idx, urlName, label, enabled, callback in [
                (0, 'remoteData',    '$DATA (user dataPath)', True,  self._dataRowCallback),
                (1, 'insideData',    '$INSIDE              ', False, None),
                (2, 'alongsideData', '$ALONGSIDE           ', False, None),
            ]:

            urls = self._findDataUrl(urlName)
            if len(urls) > 0:
                url = urls[0]
                _row = UrlPathRow(topWidget=self, obj=url, labelText=label, enabled=enabled, callback=callback).addRow(
                                  widget=self.dataUrlScrollAreaWidgetContents, row=scrollRow)
                scrollRow += 1
                self.dataUrlData[url] = _row
                if idx == 0:
                    self.dataRow = _row  # remember the row for $DATA

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
        self.showValid = RadioButtons(self.buttonFrame,
                                      texts=['%s  '%b for b in buttons], # hack to add some space!
                                      selectedInd=self.defaultSelected,
                                      callback=self._radiobuttonsCallback,
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
            _row = SpectrumPathRow(topWidget=self, labelText=sp.pid, obj=sp, enabled=True, callback=self._spectrumRowCallback).addRow(
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

    def _findDataUrl(self, storeType):
        dataUrl = self.project._apiNmrProject.root.findFirstDataLocationStore(
                name='standard').findFirstDataUrl(name=storeType)
        if dataUrl:
            return (dataUrl,)
        else:
            return ()

    def _radiobuttonsCallback(self):
        """Toggle rows on or off depending on their state and the settings of the radio buttons
        Callback for the radio buttons
        """
        for spectrum, row in self.spectrumData.items():
            self._showRow(row)

    def _showRow(self, row):
        """show row depending on isValid, hasChanged of row and settings of radio buttons
        """
        doShow = True
        if hasattr(self, 'showValid') and self.showValid is not None:  # just checking that the widget exist
                                                                       # (not the case on initialisation!)
            ind = self.showValid.getIndex()
            if ind == buttons.index(VALID_SPECTRA) and not row.isValid:  # show only valid
                doShow = False
            elif ind == buttons.index(INVALID_SPECTRA) and row.isValid: # show only invalid
                doShow = False
            elif ind == buttons.index(CHANGED_SPECTRA) and not row.hasChanged: # show only changed
                doShow = False
            else:  # show all
                doShow = True
        row.setVisible(doShow)

    def _colourRow(self, row):
        """
        Set colours of row depending on its state
        """
        # row is valid
        if row.isValid:
            if row.hasChanged:
                row.setColour(VALID_CHANGED_ROWCOLOUR)
            else:
                row.setColour(VALID_ROWCOLOUR)

        # row is not valid
        else:
            if row.hasChanged:
                row.setColour(INVALID_CHANGED_ROWCOLOUR)
            else:
                row.setColour(INVALID_ROWCOLOUR)

    def _spectrumRowCallback(self, row):
        """
        Callback used for spectrum rows
        Decide if to update the path
        Set colours and Toggle row on or off depending on its state and the settings of the radio buttons
        """

        if row.isValid and row.hasChanged:
            row.setPath(row.text)

        self._colourRow(row)
        # Special case: set WARNING colour of the rows starting with $DATA if not correct
        if row.text.startswith(DATA_INDENTIFIER) \
            and self.dataRow is not None and self.dataRow.isNotValid \
            and row.isNotValid:
                row.setColour(WARNING_ROWCOLOUR)

        self._showRow(row)

    def _dataRowCallback(self, dataRow):
        """Callback from $DATA url to validate all the spectrum rows as $DATA may have changed.
        """
        self._colourRow(dataRow)
        dataRow.setPath(dataRow.text)

        for spectrum, row in self.spectrumData.items():
            if row == dataRow:
                raise RuntimeError('row == dataRow: this should never happen!')
            row.validate()

    def _closeButton(self):
        self.accept()

    def _apply(self):
        # apply all the buttons
        pass
        self.accept()

    # def closeEvent(self, event):
    #     # don't close if there any empty urls, which cause an api crash
    #     if not self._badUrls:
    #         super().closeEvent(event)
    #     else:
    #         event.ignore()
    #         showWarning(str(self.windowTitle()), 'Project contains empty dataUrls')