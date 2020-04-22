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
__dateModified__ = "$dateModified: 2020-04-22 17:06:31 +0100 (Wed, April 22, 2020) $"
__version__ = "$Revision: 3.0.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2017-07-06 15:51:11 +0000 (Thu, July 06, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.popups.Dialog import CcpnDialog
from ccpn.ui.gui.widgets.FileDialog import FileDialog, NefFileDialog, USEREXPORTPATH
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.MessageDialog import progressManager
from PyQt5 import QtWidgets
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning
from ccpn.ui.gui.guiSettings import COLOUR_SCHEMES, getColours, DIVIDER
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.util.AttrDict import AttrDict


class ExportDialog(CcpnDialog):

    _pathHistory = {}

    def __init__(self, parent=None, mainWindow=None, title='Export to File',
                 fileMode=FileDialog.AnyFile,
                 text='Export File',
                 acceptMode=FileDialog.AcceptSave,
                 preferences=None,
                 selectFile=None,
                 pathID=None,
                 filter='*',
                 **kwds):
        """
        Initialise the widget
        """
        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        selectFile = os.path.basename(selectFile) if selectFile else None

        self._dialogFileMode = fileMode
        self._dialogText = text
        self._dialogAcceptMode = acceptMode
        self._dialogPreferences = preferences
        self._dialogSelectFile = selectFile
        self._dialogFilter = filter
        self._dialogPathID = pathID
        self.params = {}
        self.preferences = preferences
        self.title = title

        if preferences is not None:
            if isinstance(preferences, AttrDict) and hasattr(preferences, 'general'):
                self._dialogPreferences = preferences
            else:
                raise TypeError("Error: preferences incorrectly defined")

        CcpnDialog.__init__(self, parent, setLayout=True, windowTitle=title, **kwds)

        self.mainWindow = mainWindow
        self.application = mainWindow.application
        self.project = mainWindow.application.project
        self.current = mainWindow.application.current

        # the top frame to contain user defined widgets
        self.options = Frame(self, setLayout=True, grid=(0, 0))
        self.options.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        # # initialise the frame
        # self.initialise(self.options)

        # add a spacer to separate from the common save widgets
        HLine(self, grid=(2, 0), gridSpan=(1, 1), colour=getColours()[DIVIDER], height=20)

        # file directory options here
        self.openPathIcon = Icon('icons/directory')

        self.saveFrame = Frame(self, setLayout=True, grid=(3, 0))

        self.openPathIcon = Icon('icons/directory')
        self.saveLabel = Label(self.saveFrame, text=' Path: ', grid=(0, 0), hAlign='c')
        self.saveText = LineEdit(self.saveFrame, grid=(0, 1), textAlignment='l')
        self.saveText.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)

        self.saveText.setDisabled(False)  # ejb - enable but need to check path on okay

        self.pathEdited = True
        self.saveText.textEdited.connect(self._editPath)

        self.spacer = Spacer(self.saveFrame, 13, 3,
                             QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed,
                             grid=(0, 2), gridSpan=(1, 1))
        self.pathButton = Button(self.saveFrame, text='',
                                 icon=self.openPathIcon,
                                 callback=self._openFileDialog,
                                 grid=(0, 3), hAlign='c')

        self.buttonFrame = Frame(self, setLayout=True, grid=(9, 0))
        self.spacer = Spacer(self.buttonFrame, 3, 3,
                             QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed,
                             grid=(0, 0), gridSpan=(1, 1))

        self.actionButtons()

        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.MinimumExpanding)
        # self.resize(300, 500)

        self.updateDialog()
        self.setSave(self._dialogSelectFile)

        if self._dialogSelectFile is not None:  # and self.application.preferences.general.useNative is False:
            self.saveText.setText(self._dialogSelectFile)  #.fileSaveDialog.selectedFile())
        else:
            self.saveText.setText('')

        # initialise the frame
        self.initialise(self.options)

        self._saveState = True

    def actionButtons(self):
        self.buttons = ButtonList(self.buttonFrame, ['Cancel', 'Save'], [self._rejectDialog, self._acceptDialog],
                                  grid=(0, 1))

    def setSave(self, fileName):
        if fileName:
            # must assume that _dialogSelectFile is a file and not a path
            _currentPath = self.fileSaveDialog.getCurrentWorkingPath()
            if _currentPath:
                self._dialogSelectFile = os.path.join(_currentPath, os.path.basename(fileName))

                self._dialogSelectFile = self.setPathHistory(self._dialogSelectFile)
                self._dialogPath = os.path.dirname(self._dialogSelectFile)
            else:
                _currentPath = self._dialogPreferences.general.userWorkingPath if self._dialogPreferences else '~'
                self._dialogSelectFile = os.path.join(_currentPath, os.path.basename(fileName))

                self._dialogSelectFile = self.setPathHistory(self._dialogSelectFile)
                self._dialogPath = os.path.dirname(self._dialogSelectFile)
                self.fileSaveDialog.setInitialFile(self._dialogSelectFile)

            if hasattr(self, 'saveText'):
                self.saveText.setText(str(self._dialogSelectFile))

    def updateDialog(self):
        self.fileSaveDialog = NefFileDialog(self,
                                            fileMode=self._dialogFileMode,
                                            text=self._dialogText,
                                            acceptMode=self._dialogAcceptMode,
                                            preferences=self._dialogPreferences,
                                            selectFile=self._dialogSelectFile,
                                            filter=self._dialogFilter,
                                            # initialPath=self._dialogPath,       # self._dialogPreferences.general.userWorkingPath,
                                            pathID=self._dialogPathID)            # USEREXPORTPATH)

    def initialise(self, userFrame):
        """Initialise the frame containing the user widgets
        To be overridden when sub-classed by user

        :param userFrame: frame widget to insert user widgets into
        """
        pass

    def buildParameters(self):
        """build parameters dict from the user widgets, to be passed to the export method.
        To be overridden when sub-classed by user

        :return: dict - user parameters
        """
        params = {'filename': self.exitFilename}
        return params

    def exportToFile(self, filename=None, params=None):
        """Export to file
        To be overridden when sub-classed by user

        :param filename: filename to export
        :param params: dict - user defined paramters for export
        """
        pass

    def _acceptDialog(self, exitSaveFileName=None):
        """save button has been clicked
        """
        self.exitFilename = self.saveText.text().strip()  # strip the trailing whitespace

        if self.pathEdited is False:
            # user has not changed the path so we can accept()
            self.accept()
        else:
            # have edited the path so check the new file
            if os.path.isfile(self.exitFilename):
                yes = showYesNoWarning('%s already exists.' % os.path.basename(self.exitFilename),
                                       'Do you want to replace it?')
                if yes:
                    self.accept()
            else:
                if not self.exitFilename:
                    showWarning('FileName Error:', 'Filename is empty.')
                else:
                    self.accept()

    def _rejectDialog(self):
        self.exitFilename = None
        self.reject()

    def closeEvent(self, QCloseEvent):
        self._rejectDialog()

    def _exportToFile(self):
        # build the export dict
        with progressManager(self, 'Saving to file:\n%s' % self.exitFilename):
            params = self.buildParameters()

            # do the export
            if params:
                self.exportToFile(params=params)

            # return the filename
            return params

    def exec_(self):
        """popup the dialog
        """
        value = super(ExportDialog, self).exec_()

        if value:
            return self._exportToFile()

    def _openFileDialog(self):
        """open the save dialog
        """
        # self.fileSaveDialog = NefFileDialog(self,
        #                                 fileMode=self._dialogFileMode,
        #                                 text=self._dialogText,
        #                                 acceptMode=self._dialogAcceptMode,
        #                                 preferences=self._dialogPreferences,
        #                                 selectFile=self.saveText.text(),
        #                                 filter=self._dialogFilter)

        # set the path, it may have been edited
        self.fileSaveDialog._selectFile = self._dialogSelectFile

        self.fileSaveDialog._show()
        selectedFile = self.fileSaveDialog.selectedFile()
        selectedFile = self.setPathHistory(selectedFile)

        if selectedFile:
            self.saveText.setText(str(selectedFile))
            self._dialogSelectFile = str(selectedFile)
            self.pathEdited = False  # path has been reset

    def _save(self):
        self.accept()

    def _editPath(self):
        self.pathEdited = True
        self._dialogSelectFile = self.saveText.text()
        self._dialogSelectFile = self.setPathHistory(self._dialogSelectFile)

    def updateFilename(self, filename):
        self._dialogSelectFile = self.setPathHistory(filename)
        if hasattr(self, 'saveText'):
            self.saveText.setText(str(self._dialogSelectFile))

    def getPathHistory(self):
        if self.title in ExportDialog._pathHistory:
            return ExportDialog._pathHistory[self.title]

        return ''

    def setPathHistory(self, filename):
        if filename:
            if os.path.dirname(filename):
                ExportDialog._pathHistory[self.title] = os.path.dirname(filename)
            else:
                if self.title in ExportDialog._pathHistory:
                    filename = os.path.join(ExportDialog._pathHistory[self.title], filename)
                else:
                    ExportDialog._pathHistory[self.title] = ''
        else:
            if self.title not in ExportDialog._pathHistory:
                ExportDialog._pathHistory[self.title] = ''

        return filename


if __name__ == '__main__':
    from sandbox.Geerten.Refactored.framework import Framework
    from sandbox.Geerten.Refactored.programArguments import Arguments


    _makeMainWindowVisible = False


    class MyProgramme(Framework):
        "My first app"
        pass


    myArgs = Arguments()
    myArgs.noGui = False
    myArgs.debug = True

    application = MyProgramme('MyProgramme', '3.0.0-beta3', args=myArgs)
    ui = application.ui
    ui.initialize()

    if _makeMainWindowVisible:
        ui.mainWindow._updateMainWindow(newProject=True)
        ui.mainWindow.show()
        QtWidgets.QApplication.setActiveWindow(ui.mainWindow)

    dialog = ExportDialog(parent=application.mainWindow, mainWindow=application.mainWindow)
    filename = dialog.exec_()
