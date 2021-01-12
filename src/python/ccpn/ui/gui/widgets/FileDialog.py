"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2021"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2021-01-12 18:21:41 +0000 (Tue, January 12, 2021) $"
__version__ = "$Revision: 3.0.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: rhfogh $"
__date__ = "$Date: 2017-04-07 10:28:41 +0000 (Fri, April 07, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import sys
import os
from PyQt5 import QtWidgets
from ccpn.util.Path import aPath
from ccpn.util.Common import makeIterableList
from ccpn.util.AttrDict import AttrDict
from ccpn.util.Logging import getLogger
from ccpn.util.decorators import singleton
from ccpn.framework.Application import getApplication


USERDEFAULTPATH = 'userDefaultPath'
USERWORKINGPATH = 'userWorkingPath'
USERDATAPATH = 'userDataPath'
USERLAYOUTSPATH = 'userLayoutsPaths'
USERMACROSPATH = 'userMacrosPath'
USERNEFPATH = 'userNefPath'
USERACHIVESPATH = 'userAchivesPath'
USERPLUGINSPATH = 'userPluginsPath'
USERPREFERENCESPATH = 'userPreferencesPath'
USERSPECTRUMPATH = 'userSpectrumPath'
USERTABLESPATH = 'userTablesPath'
USERBACKUPSPATH = 'userBackupsPath'
USERAUXILIARYPATH = 'userAuxiliaryPath'
USERPIPESPATH = 'userPipesPath'
USERNMRSTARPATH = 'userNmrStarPath'
USEROTHERPATH = 'userOtherPath'
USERSAVEPROJECTPATH = 'userSaveProjectPath'
USEREXPORTPDFPATH = 'userExportPdfPath'
USEREXPORTPATH = 'userExportPath'

def getInitialPath(pathID=USERDEFAULTPATH):
    _dialog = FileDialogABC()
    if pathID in _dialog._initialPaths:
        return _dialog._initialPaths[pathID]


def setInitialPath(pathID=USERDEFAULTPATH, initialPath=None):
    _dialog = FileDialogABC()
    _dialog._initialPaths[pathID] = initialPath


ACCEPTMODEDICT = {
    'open'  : QtWidgets.QFileDialog.AcceptOpen, # 0
    'load'  : QtWidgets.QFileDialog.AcceptOpen, # 0
    'save'  : QtWidgets.QFileDialog.AcceptSave, # 1
    'import': QtWidgets.QFileDialog.AcceptOpen, # 0
    'export': QtWidgets.QFileDialog.AcceptSave, # 1
    'select': QtWidgets.QFileDialog.AcceptOpen, # 0
    'run'   : QtWidgets.QFileDialog.AcceptOpen, # 0
    }

FILEMODESDICT = {
    'anyFile'      : QtWidgets.QFileDialog.AnyFile, # 0
    'existingFile' : QtWidgets.QFileDialog.ExistingFile, # 1
    'directory'    : QtWidgets.QFileDialog.Directory, # 2
    'directoryOnly': QtWidgets.QFileDialog.Directory, # 2
    'existingFiles': QtWidgets.QFileDialog.ExistingFiles, # 3
    }

STATICFUNCTIONDICT = {
    (0, 0)                                                                 : 'getOpenFileName',
    (0, 1)                                                                 : 'getOpenFileName',
    (0, 2)                                                                 : 'getExistingDirectory',
    (0, 3)                                                                 : 'getOpenFileNames',
    (1, 0)                                                                 : 'getSaveFileName',
    (1, 1)                                                                 : 'getSaveFileName',
    (1, 2)                                                                 : 'getSaveFileName',
    (1, 3)                                                                 : 'getSaveFileName',
    (QtWidgets.QFileDialog.AcceptOpen, QtWidgets.QFileDialog.AnyFile)      : 'getOpenFileName',
    (QtWidgets.QFileDialog.AcceptOpen, QtWidgets.QFileDialog.ExistingFile) : 'getOpenFileName',
    (QtWidgets.QFileDialog.AcceptOpen, QtWidgets.QFileDialog.Directory)    : 'getExistingDirectory',
    (QtWidgets.QFileDialog.AcceptOpen, QtWidgets.QFileDialog.ExistingFiles): 'getOpenFileNames',
    (QtWidgets.QFileDialog.AcceptSave, QtWidgets.QFileDialog.AnyFile)      : 'getSaveFileName',
    (QtWidgets.QFileDialog.AcceptSave, QtWidgets.QFileDialog.ExistingFile) : 'getSaveFileName',
    (QtWidgets.QFileDialog.AcceptSave, QtWidgets.QFileDialog.Directory)    : 'getSaveFileName',
    (QtWidgets.QFileDialog.AcceptSave, QtWidgets.QFileDialog.ExistingFiles): 'getSaveFileName',
    }


class FileDialog(QtWidgets.QFileDialog):
    # Temporary to search for instances
    pass


class FileDialogABC(QtWidgets.QFileDialog):
    """
    Class to implement open/save dialogs
    """
    _initialPaths = {}
    _fileMode = 'anyFile'
    _text = None
    _updatePathOnReject = True
    _multiSelect = False
    restrictDirToFilter = False,

    # path attribute to read from preferences.general dict in __new__
    _initialPath = 'userWorkingPath'

    def __init__(self, parent=None,
                 acceptMode='open',
                 selectFile=None, filter=None, directory=None,
                 # restrictDirToFilter=False,
                 # multiSelection=False,
                 useNative=None,
                 initialPath=None,
                 _useDirectoryOnly=False,
                 **kwds):
        """
        Initialise the dialog widget

        :param parent:
        :param acceptMode: 'open' or 'save'
        :param selectFile:
        :param filter:
        :param directory:
        :param restrictDirToFilter:
        :param multiSelection:
        :param useNative:
        :param initialPath:
        :param kwds:
        """

        # NOTE:ED - hack for the minute to set the directories from preferences
        if _useDirectoryOnly:
            self._fileMode = 'directoryOnly'
            self._text = ' '.join([self._text, 'Path'])

        # check that the subclass attributes has been defined
        if self._fileMode is None and not self._text:
            raise RuntimeError(f'{self.__class__.__name__} not defined correctly')
        _fm = FILEMODESDICT.get(self._fileMode)
        if _fm is None:
            raise RuntimeError(f'{self.__class__.__name__}: _fileMode \'{self._fileMode}\' not defined')

        _am = ACCEPTMODEDICT.get(acceptMode)
        if _am is None:
            raise TypeError(f'{self.__class__.__name__}: acceptMode \'{acceptMode}\' not defined')

        try:
            application = getApplication()
            self._preferences = application.preferences
            _general = self._preferences.general
        except:
            raise RuntimeError('application is not defined')

        if directory is None:
            _path = aPath(_general.get(self._initialPath))
            if not _path:
                raise RuntimeError(f'preferences.general.{self._initialPath} not defined correctly')
            # set the current working path if this is the first time the dialog has been opened
            if self._clsID not in self._initialPaths:
                self._initialPaths[self._clsID] = _path
            directory = self._initialPaths[self._clsID]
            self._setDirectory = False
        else:
            directory = directory
            self._setDirectory = True

        # # set the current working path if this is the first time the dialog has been opened
        # if self._clsID not in self._initialPaths:
        #     self._initialPaths[self._clsID] = aPath(_path or '~')

        # if directory is None:
        #     # set the current working path if this is the first time the dialog has been opened
        #     if self._clsID not in self._initialPaths and initialPath:
        #         self._initialPaths[self._clsID] = initialPath
        #     if self._clsID in self._initialPaths:
        #         directory = str(aPath(self._initialPaths[self._clsID] or '~'))
        #     else:
        #         directory = str(aPath('~'))
        #     self._setDirectory = False
        # else:
        #     directory = str(aPath(directory))
        #     self._setDirectory = True

        # self._updatePathOnReject = updatePathOnReject

        _txt = self._text.format(acceptMode) if '{}' in self._text else self._text
        _txt = _txt[0].capitalize() + _txt[1:]
        super().__init__(parent, caption=_txt, directory=str(directory), **kwds)

        try:
            if self._fileMode == 'directoryOnly':
                # fix obsolete DirectoryOnly
                self.setOption(self.ShowDirsOnly, True)
        except  Exception as es:
            pass

        self._kwds = kwds
        # self._selectFile = os.path.basename(selectFile) if selectFile else None
        self._selectFile = aPath(selectFile).name if selectFile else None

        self.setFileMode(_fm)
        self._customMultiSelectedFiles = []  #used to multiselect directories and files at the same time. Available only on Non Native
        # self._multiSelect = multiSelection

        self._acceptMode = ACCEPTMODEDICT.get(acceptMode)
        self.setAcceptMode(self._acceptMode)

        if filter is not None:
            self.setNameFilter(filter)
        if selectFile is not None:
            # populates fileDialog with the suggested filename
            self.selectFile(selectFile)

        if useNative is not None:
            self.useNative = useNative
        else:
            self.useNative = self._preferences.general.useNative

        # need to do this before setting DontUseNativeDialog (only for non-native?)
        if self.restrictDirToFilter == True:
            self.filterSelected.connect(self._predir)
            self.directoryEntered.connect(self._dir)
            self._restrictedType = filter

        # self.result is '' (first case) or 0 (second case) if Cancel button selected
        if self.useNative and not sys.platform.lower() == 'linux':

            pass

            # # get the function name from the dict above
            # funcName = self.staticFunctionDict[(acceptMode, fileMode)]
            # self.result = getattr(self, funcName)(caption=text, **kwds)
            # if isinstance(self.result, tuple):
            #     self.result = self.result[0]
        else:
            self.setOption(QtWidgets.QFileDialog.DontUseNativeDialog, not self.useNative)

            # add a multi-selection option - only for non-native dialogs
            for view in self.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
                if isinstance(view.model(), QtWidgets.QFileSystemModel):

                    # set the selection mode for the dialog
                    if self._multiSelect:
                        view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
                    else:
                        view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

            btns = self.findChildren(QtWidgets.QPushButton)
            if btns:
                # search for the open button and connect to the clicked signal
                self.openBtn = [x for x in btns if 'open' in str(x.text()).lower()]
                if self.openBtn:
                    self.openBtn[0].clicked.disconnect()
                    self.openBtn[0].clicked.connect(self._openClicked)

            # NOTE:ED - exec separated from the _init__ to stop threading issues with Windows 10
            #           _show or exec_ must be called after creating a FileDialog object

    @property
    def _clsID(self):
        return self.__class__.__name__

    def getCurrentWorkingPath(self):
        if self._clsID in self._initialPaths:
            return self._initialPaths[self._clsID]

    @property
    def initialPath(self):
        if self._clsID in self._initialPaths:
            return self._initialPaths[self._clsID]

    @initialPath.setter
    def initialPath(self, value):
        if self._clsID in self._initialPaths:
            self._initialPaths[self._clsID] = value

    def _show(self):
        """Separated from the _init__ to stop threading issues with Windows 10
        Must be called after creating a FileDialog object
        """
        if self.useNative and not sys.platform.lower() == 'linux':
            funcName = STATICFUNCTIONDICT[(self._acceptMode, self._fileMode)]
            self.result = getattr(self, funcName)(caption=self._text, directory=self._selectFile, **self._kwds)
            if isinstance(self.result, tuple):
                self.result = self.result[0]
        else:
            self.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
            self.result = self.exec_()

        if self.selectedFiles():
            # empty assumes that the dialog has been rejected
            self._updateCurrentPath()

    def _updateCurrentPath(self):
        """Update the current path
        """
        if not self._setDirectory:
            # accept the dialog and set the current selected folder for next time if directory not originally set
            absPath = aPath(self.directory().absolutePath())
            getLogger().info(f'>>> update path {self._clsID}')
            self._initialPaths[self._clsID] = absPath

    def accept(self):
        """Update the current path and exit the dialog
        """
        self._updateCurrentPath()
        super().accept()

    def reject(self):
        """Update the current path (if required) and exit the dialog
        """
        self.selectedFiles = lambda: None  # needs to clear the selection when closing
        if self._updatePathOnReject:
            self._updateCurrentPath()
        super().reject()

    def _predir(self, file: str):
        if file.endswith(self._restrictedType):
            self.fileSelected = None

    def _dir(self, directory: str):
        if directory.endswith(self._restrictedType):
            return False

        return True

    def _openClicked(self):
        """Custom action to multiselect files and dir at the same time or just Dirs or just Files. Needed to open a top dir
        containing the spectra. Eg 10 Brukers at once
        """
        self.tree = self.findChild(QtWidgets.QTreeView)
        if self.tree:
            inds = self.tree.selectionModel().selectedIndexes()
            files = []
            for i in inds:
                if i.column() == 0:
                    files.append(os.path.join(str(self.directory().absolutePath()), str(i.data())))
            self._customMultiSelectedFiles = files

            # NOTE:ED - does this need to hide here?
            self.hide()

    # overrides Qt function, which does not pay any attention to whether Cancel button selected
    def selectedFiles(self):
        """Get the list of selected files
        """
        if self.useNative:
            # get the selected files from the native dialog
            if self.result:
                return makeIterableList(self.result)
            else:
                return []
        else:
            # use our ccpn dialog
            files = super().selectedFiles()
            return files

    def selectedFile(self):
        """Get the first selected file
        """
        # Qt does not have this but useful if you know you only want one file
        files = self.selectedFiles()
        if files and len(files) > 0:
            return files[0]
        else:
            return None


class NefFileDialog(QtWidgets.QFileDialog):
    _selectPath = os.path.expanduser('~')

    def __init__(self, parent=None, fileMode=QtWidgets.QFileDialog.AnyFile, text=None,
                 acceptMode=QtWidgets.QFileDialog.AcceptOpen, preferences=None, selectFile=None,
                 directory=None, initialPath=None,
                 # pathID=USERDEFAULTPATH,
                 updatePathOnReject=True,
                 confirmOverwrite=True,
                 **kwds):

        # ejb - added selectFile to suggest a filename in the file box
        #       this is not passed to the super class
        self._preferences = None
        if preferences is not None:
            if isinstance(preferences, AttrDict) and hasattr(preferences, 'general'):
                self._preferences = preferences
            else:
                raise TypeError("Error: preferences incorrectly defined")

        if directory is None:
            if self.pathID not in self._initialPaths and initialPath:
                self._initialPaths[self.pathID] = initialPath
            if self.pathID in self._initialPaths:
                directory = str(aPath(self._initialPaths[self.pathID] or '~'))
            else:
                directory = str(aPath('~'))
            self._setDirectory = False
        else:
            directory = str(aPath(directory))
            self._setDirectory = True

        selectFile = os.path.basename(selectFile) if selectFile else None

        # self._pathID = pathID
        self._updatePathOnReject = updatePathOnReject

        QtWidgets.QFileDialog.__init__(self, parent, caption=text, directory=directory, **kwds)
        if not confirmOverwrite:
            self.setOption(QtWidgets.QFileDialog.DontConfirmOverwrite)

        # self.staticFunctionDict = {
        #     (0, 0)                               : 'getOpenFileName',
        #     (0, 1)                               : 'getOpenFileName',
        #     (0, 2)                               : 'getExistingDirectory',
        #     (0, 3)                               : 'getOpenFileNames',
        #     (1, 0)                               : 'getSaveFileName',
        #     (1, 1)                               : 'getSaveFileName',
        #     (1, 2)                               : 'getSaveFileName',
        #     (1, 3)                               : 'getSaveFileName',
        #     (self.AcceptOpen, self.AnyFile)      : 'getOpenFileName',
        #     (self.AcceptOpen, self.ExistingFile) : 'getOpenFileName',
        #     (self.AcceptOpen, self.Directory)    : 'getExistingDirectory',
        #     (self.AcceptOpen, self.ExistingFiles): 'getOpenFileNames',
        #     (self.AcceptSave, self.AnyFile)      : 'getSaveFileName',
        #     (self.AcceptSave, self.ExistingFile) : 'getSaveFileName',
        #     (self.AcceptSave, self.Directory)    : 'getSaveFileName',
        #     (self.AcceptSave, self.ExistingFiles): 'getSaveFileName',
        #     }

        self._fileMode = fileMode
        self._acceptMode = acceptMode
        self._kwds = kwds
        self._text = text
        self._selectFile = selectFile

        self.setFileMode(fileMode)
        self.setAcceptMode(acceptMode)
        self.setLabelText(QtWidgets.QFileDialog.Accept, 'Select')

        if selectFile is not None:  # ejb - populates fileDialog with a suggested filename
            self.selectFile(selectFile)

        self.useNative = self._preferences.general.useNative if self._preferences else False

        # if self._preferences:
        #     if self._preferences.general.colourScheme == 'dark':
        #         self.setStyleSheet("""
        #                    QFileDialog QWidget {
        #                                        background-color: #2a3358;
        #                                        color: #f7ffff;
        #                                        }
        #                   """)
        #     elif self._preferences.general.colourScheme == 'light':
        #         self.setStyleSheet("QFileDialog QWidget {color: #464e76; }")

    def getCurrentWorkingPath(self):
        if self.pathID in self._initialPaths:
            return self._initialPaths[self.pathID]

    def setInitialFile(self, initialFile):
        initialPath = os.path.dirname(initialFile)
        if self.pathID not in self._initialPaths and initialPath:
            self._initialPaths[self.pathID] = initialPath
        if self.pathID in self._initialPaths:
            directory = str(aPath(self._initialPaths[self.pathID] or '~'))
        else:
            directory = str(aPath('~'))

        self.setDirectory(directory)
        self.selectFile(initialFile)
        self._setDirectory = False

    def setInitialPath(self, initialPath):
        if self.pathID not in self._initialPaths and initialPath:
            self._initialPaths[self.pathID] = initialPath
        if self.pathID in self._initialPaths:
            directory = str(aPath(self._initialPaths[self.pathID] or '~'))
        else:
            directory = str(aPath('~'))

        self.setDirectory(directory)
        self._setDirectory = False

    def selectedFiles(self):
        # if self.useNative:
        #     # return empty list if the native dialog
        #     return None
        # else:

        # the selectFile works and returns the file in the current directory
        if self.result and not self.useNative:
            return QtWidgets.QFileDialog.selectedFiles(self)
        elif self.result and self.useNative:
            return [self.result]
        else:
            return []

    def selectedFile(self):
        files = self.selectedFiles()
        if files:
            return files[0]
        else:
            return None

    def _setParent(self, parent, acceptFunc, rejectFunc):
        self._parent = parent
        self.acceptFunc = acceptFunc
        self.rejectFunc = rejectFunc

    def _updateCurrentPath(self):
        """Update the current path for the current pathID
        """
        if not self._setDirectory:
            # accept the dialog and set the current selected folder for next time if directory not originally set
            absPath = self.directory().absolutePath()
            self._initialPaths[self.pathID] = absPath

    def reject(self):
        """Update the current path (if required) and exit the dialog
        """
        if self._updatePathOnReject:
            self._updateCurrentPath()
        super().reject()
        # self.rejectFunc()

    def accept(self):
        """Update the current path and exit the dialog
        """
        self._updateCurrentPath()
        super().accept()
        # self.acceptFunc(self.selectedFile())

    def setLabels(self, save='Save', cancel='Cancel'):
        self.setLabelText(QtWidgets.QFileDialog.Accept, save)
        self.setLabelText(QtWidgets.QFileDialog.Reject, cancel)

    def _setResult(self, value):
        self.thisAccepted = value

    def _show(self):
        if self.useNative and not sys.platform.lower() == 'linux':
            funcName = STATICFUNCTIONDICT[(self._acceptMode, self._fileMode)]
            self.result = getattr(self, funcName)(caption=self._text, directory=self._selectFile, **self._kwds)
            # self.result = getattr(self, funcName)(caption=self._text, **self._kwds)
            if isinstance(self.result, tuple):
                self.result = self.result[0]
        else:
            self.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
            if self._selectFile is not None:  # ejb - populates fileDialog with a suggested filename
                self.selectFile(self._selectFile)

            self.result = self.exec_()

        if self.selectedFiles():
            # empty assumes that the dialog has been rejected
            self._updateCurrentPath()


# Define the subclasses for each dialog

class ProjectFileDialog(FileDialogABC):
    _fileMode = 'directory'
    _text = '{} Project'


class WorkingPathFileDialog(FileDialogABC):
    _fileMode = 'directoryOnly'
    _text = '{} Working Path'


class DataPathFileDialog(FileDialogABC):
    _fileMode = 'directoryOnly'
    _text = '{} Data Path'


class DataFileDialog(FileDialogABC):
    _text = '{} Data'


class LayoutsFileDialog(FileDialogABC):
    _initialPath = 'userLayoutsPath'
    _text = '{} Layout'


class MacrosFileDialog(FileDialogABC):
    _initialPath = 'userMacroPath'
    _text = '{} Macro'


# class NefFileDialog(FileDialogABC):
#     pathID = USERNEFPATH


class ArchivesFileDialog(FileDialogABC):
    _text = '{} Archive'


class PluginsFileDialog(FileDialogABC):
    _initialPath = 'userPluginPath'
    _text = '{} Plugin'


class PreferencesFileDialog(FileDialogABC):
    _text = '{} Preferences'


class SpectrumFileDialog(FileDialogABC):
    _text = '{} Spectra'
    _fileMode = 'existingFiles'
    _multiSelect = True


class TablesFileDialog(FileDialogABC):
    _text = '{} Table'


class BackupsFileDialog(FileDialogABC):
    _text = '{} Backup'


class AuxiliaryFileDialog(FileDialogABC):
    _text = '{} Auxiliary File'


class PipelineFileDialog(FileDialogABC):
    _text = '{} Pipeline'


class NMRStarFileDialog(FileDialogABC):
    _text = '{} NMRStar File'


class OtherFileDialog(FileDialogABC):
    _text = '{} File'


# class SaveProjectFileDialog(FileDialogABC):
#     _text = '{} Project'


class PDFFileDialog(FileDialogABC):
    _text = '{} PDF Document'


class ExportFileDialog(FileDialogABC):
    _text = '{} as'


class ExcelFileDialog(FileDialogABC):
    _text = '{} Excel File'


class ExecutablesFileDialog(FileDialogABC):
    _text = '{} Executable'


class AdminFileDialog(FileDialogABC):
    _text = '{} Files'
    _fileMode = 'existingFiles'
    _multiSelect = True


class LineButtonFileDialog(FileDialogABC):
    """Special class for a lineEdit button in pipelines
    """

    def __init__(self, parent=None,
                 fileMode=QtWidgets.QFileDialog.AnyFile,
                 text=None,
                 directory=None,
                 filter=None,
                 **kwds):
        self._fileMode = fileMode
        self._text = text
        super().__init__(parent, filter=filter, directory=directory, **kwds)


from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Widget import Widget
from os.path import expanduser


class LineEditButtonDialog(Widget):
    def __init__(self, parent, textDialog=None, textLineEdit=None, fileMode=None, filter=None, directory=None, **kwds):

        super().__init__(parent, setLayout=True, **kwds)
        self.openPathIcon = Icon('icons/directory')

        if textDialog is None:
            self.textDialog = ''
        else:
            self.textDialog = textDialog

        if textLineEdit is None:
            self.textLineEdit = expanduser("~")
        else:
            self.textLineEdit = textLineEdit

        if fileMode is None:
            self.fileMode = QtWidgets.QFileDialog.AnyFile
        else:
            self.fileMode = fileMode

        self.filter = filter
        self.directory = directory

        tipText = 'Click the icon to select'
        self.lineEdit = LineEdit(self, text=self.textLineEdit, textAlignment='l', hAlign='l', minimumWidth=100,
                                 tipText=tipText, grid=(0, 0))
        self.lineEdit.setEnabled(True)
        self.lineEdit.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                    QtWidgets.QSizePolicy.Minimum)
        button = Button(self, text='', icon=self.openPathIcon, callback=self._openFileDialog, grid=(0, 1), hAlign='c')
        button.setStyleSheet("border: 0px solid transparent")

    def _openFileDialog(self):
        self.fileDialog = LineButtonFileDialog(self, fileMode=self.fileMode, text=self.textDialog,
                                               directory=self.directory, filter=self.filter)
        self.fileDialog._show()
        selectedFile = self.fileDialog.selectedFile()
        if selectedFile:
            self.lineEdit.setText(str(selectedFile))
            return True
        else:
            return False

    def get(self):
        return self.lineEdit.text()

    def setText(self, text):
        self.lineEdit.setText(str(text))


if __name__ == '__main__':
    from ccpn.ui.gui.widgets.Application import TestApplication
    from ccpn.ui.gui.popups.Dialog import CcpnDialog


    app = TestApplication()
    popup = CcpnDialog(windowTitle='Test LineEditButtonDialog')
    slider = FileDialog(parent=popup)
    print(slider.selectedFile())

    popup.show()
    popup.raise_()
    app.start()
