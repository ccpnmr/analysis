"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2025"
__credits__ = ("Ed Brooksbank, Morgan Hayward, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Daniel Thompson",
               "Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2025-10-08 19:44:49 +0100 (Wed, October 08, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2023-06-28 15:41:23 +0100 (Wed, June 28, 2023) $"
#=========================================================================================
# Start of code
#=========================================================================================

__all__ = ["generateWidget", "selectedRadioButton"]

from collections.abc import Mapping, Iterable
from functools import partial

from PyQt5 import QtGui, QtWidgets
from PyQt5 import QtCore

from ccpn.framework.Application import getApplication
# from ccpn.ui.gui.popups.ImportNefPopup import CHEMICALSHIFTLIST
# from ccpn.ui.gui.widgets.Widget import Widget
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.Frame import Frame
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.PulldownListsForObjects import (
    _PulldownABC,
    SpectrumPulldown, PeakListPulldown, ChemicalShiftListPulldown,
    )
from ccpn.ui.gui.widgets.HLine import HLine
from ccpn.ui.gui.widgets.CompoundWidgets import EntryPathCompoundWidget
from ccpn.ui.gui.widgets.FileDialog import DataFileDialog
from ccpn.ui.gui.lib.GuiPath import PathEdit
from ccpn.ui.gui.guiSettings import getColours, DIVIDER

from ccpn.util.DataEnum import DataEnum


LABEL = 'Label'
LINE_EDIT = 'LineEdit'
CHECKBOX = 'CheckBox'
PULLDOWNLIST = 'PulldownList'
MAPPED_PULLDOWNLIST = 'MappedPulldownList'
RADIOBUTTONS = 'RadioButtons'
SPINBOX = 'Spinbox'
DOUBLESPINBOX = 'DoubleSpinbox'
SPECTRUM_PULLDOWN = 'SpectrumPulldown'
PEAKLIST_PULLDOWN = 'PeakListPulldown'
CHEMICALSHIFTLIST_PULLDOWN = 'ChemicalShiftListPulldown'
HLINE = 'Hline'
PATH_EDIT = 'PathEdit'

widgetTypes = {
    LABEL                     : Label,
    LINE_EDIT                 : LineEdit,
    CHECKBOX                  : CheckBox,
    PULLDOWNLIST              : PulldownList,
    RADIOBUTTONS              : RadioButtons,
    MAPPED_PULLDOWNLIST       : PulldownList,
    SPINBOX                   : Spinbox,
    DOUBLESPINBOX             : DoubleSpinbox,
    SPECTRUM_PULLDOWN         : SpectrumPulldown,
    PEAKLIST_PULLDOWN         : PeakListPulldown,
    CHEMICALSHIFTLIST_PULLDOWN: ChemicalShiftListPulldown,
    HLINE                     : HLine,
    PATH_EDIT                 : PathEdit,
    }


class _AutoWidget():
    """A class to wrap the get, set for a widget
    """

    def __init__(self, widget, getMethod, setMethod):
        self.widget = widget
        self.getMethod = getMethod
        self.setMethod = setMethod

    def get(self):
        """Return the value from the widget or None if no getMethod is defined.
        """
        if self.getMethod is None:
            return None
        _get = getattr(self.widget, self.getMethod)
        return _get()

    def set(self, value):
        """Set the value of the widget, or do nothing if setMethod is not defined.
        """
        if self.setMethod is None:
            return
        _set = getattr(self.widget, self.setMethod)
        _set(value)


# def _updateRunArgs(argsDict, arg, value):
#   argsDict[arg] = value
AUTOGEN_TAG = 'Auto-generated input:'


#TODO: document
#TODO: removed hard-coded strings

def _valueToWidgetType(value) -> str | None:
    """Convert the old value based definitions to the new widgetType definitions.
      :param value: The value to convert
      :return: The new widgetType definition or None if failed

      From Plugin:

      The 'value' entry:
        The type of widget generated is controlled by the value of this entry,
        if the value is an iterable, the type of widget is controlled by the first item in the iterable
        strings are not considered iterables here.
          value type                       : type of widget
          string                           : LineEdit
          boolean                          : Checkbox
          Iterable(strings)                : PulldownList
          Iterable(int, int)               : Spinbox
          Iterable(float, float)           : DoubleSpinbox
          Iterable(Iterables(str, object)) : PulldownList where the object is passed instead of the string

         GWV: RadioButton and mapped-list undefined above!
         Code derived from generateWidgets below
    """
    _widgetType = None

    if isinstance(value, str):
        _widgetType = LINE_EDIT
    elif isinstance(value, bool):
        _widgetType = CHECKBOX
    elif isinstance(value, Iterable):
        if isinstance(value[0], str):
            _widgetType = PULLDOWNLIST
        elif isinstance(value[0], tuple):
            if isinstance(value[0][1], bool):
                _widgetType = RADIOBUTTONS
            else:
                assert all([len(v) == 2 for v in value])
                assert all([isinstance(v[0], str) for v in value])
                _widgetType = MAPPED_PULLDOWNLIST
        elif isinstance(value[0], int) and len(value) == 2:
            _widgetType = SPINBOX
        elif isinstance(value[0], float) and len(value) == 2:
            _widgetType = DOUBLESPINBOX

    return _widgetType


def generateWidget(params: list, parentWidget, argsDict=None,
                   columns=1, leftAlignLabel=True, showBorder=False):
    """Generate the input widget from the params definitions
    """
    if argsDict is None:
        argsDict = {}

    # make a frame for each column requested
    _frames = [Frame(parentWidget, setLayout=True, grid=(0, _col), showBorder=showBorder)
               for _col in range(columns)
               ]

    for i, _param in enumerate(params):

        assert isinstance(_param, Mapping)

        # skip any empty entries
        if len(_param) == 0:
            continue

        # we are popping the parameters, so need to preserve the original
        # for next usage
        param = _param.copy()

        row = int(i / columns)
        column = i % columns

        if (_widgetType := param.pop('widgetType', None)) is None:
            # revert to old defs
            _widgetType = _valueToWidgetType(param['value'])

        if (_widgetClass := widgetTypes.get(_widgetType, None)) is None:
            raise RuntimeError(f'generateWidget: invalid widgetType {_widgetType}')

        if (_variable := param.pop('variable', None)) is None:
            raise RuntimeError(f'generateWidget: unable to find variable in {param}')

        _value = param.pop('value', None)
        _defaultValue = param.pop('default', None)
        _label = param.get('label', _variable)

        # frame = Frame(parentWidget, setLayout=True, grid=(row, column), margins=(10, 2, 10, 2))  # ejb, gwv
        frame = _frames[column]

        # start generating widgets
        # Generate a label for the parameter, except in case of
        # the Label, Hline widgets
        if _widgetType not in (LABEL, HLINE):
            # put parameter label for all but LABEL type
            _hAlign = 'left' if leftAlignLabel else 'right'
            Label(frame, _label, grid=(row, 0), hAlign=_hAlign, minimumHeight=28)

        # Generate the input widget
        if _widgetType == LABEL:
            _col = param.pop('column', 1)
            _widget = Label(frame, _value, grid=(row, _col), **param)

        if _widgetType == HLINE:
            param.setdefault('colour', getColours()[DIVIDER])
            _widget = HLine(frame, grid=(row, 0), gridSpan=(1, 2), **param)

        elif issubclass(_widgetClass, _PulldownABC):
            _app = getApplication()
            param.setdefault('showSelectName', True)
            callback = partial(argsDict.__setitem__, _variable)
            _widget = _widgetClass(parent=frame, grid=(row, 1),
                                   mainWindow=_app.mainWindow,
                                   labelText='',
                                   callback=callback,
                                   **param
                                   )
            _aWidget = _AutoWidget(_widget,
                                   'getSelectedObject',
                                   None)
            setattr(parentWidget, _variable, _aWidget)
            callback(_aWidget.get())

        elif _widgetType == LINE_EDIT:
            param.setdefault('textAlignment', 'left')
            _widget = LineEdit(frame, grid=(row, 1), **param)
            if _defaultValue:
                _widget.setText(_defaultValue)
            setattr(parentWidget, _variable, _widget)
            callback = partial(argsDict.__setitem__, _variable)
            _widget.textChanged.connect(callback)
            callback(_widget.get())

        elif _widgetType == CHECKBOX:
            _widget = CheckBox(frame, checked=False, grid=(row, 1))
            setattr(parentWidget, _variable, _widget)
            _widget.stateChanged.connect(partial(argsDict.__setitem__, _variable))
            _widget.set(bool(_defaultValue) or bool(_value))
            argsDict[_variable] = _defaultValue

        elif _widgetType == PULLDOWNLIST:
            assert isinstance(_value, Iterable) and len(_value) > 0
            _widget = PulldownList(frame, texts=_value, grid=(row, 1))
            _widget.set(param.get('default', _value[0]))
            setattr(parentWidget, _variable, _widget)
            callback = partial(argsDict.__setitem__, _variable)
            _widget.setCallback(callback)
            callback(_widget.get())

        elif _widgetType == RADIOBUTTONS:
            assert all([len(v) == 2 for v in _value])
            assert all([isinstance(v[0], str) for v in _value])
            assert all([isinstance(v[1], bool) for v in _value])
            t, b = zip(*_value)
            _widget = RadioButtons(frame, texts=t, grid=(row, 1))
            setattr(parentWidget, _variable, _widget)
            _widget.set(_defaultValue)
            _widget.buttonGroup.buttonClicked[QtWidgets.QAbstractButton].connect(
                    partial(selectedRadioButton, param=param, argsDict=argsDict))
            argsDict[_variable] = _defaultValue

        elif _widgetType == MAPPED_PULLDOWNLIST:
            assert all([len(v) == 2 for v in _value])
            assert all([isinstance(v[0], str) for v in _value])
            t, o = zip(*_value)
            _widget = PulldownList(frame, texts=t, objects=o, grid=(row, 1))
            _widget.set(param.get('default', _value[0]))
            setattr(parentWidget, _variable, _widget)
            callback = partial(argsDict.__setitem__, _variable)
            _widget.setCallback(callback)
            callback(_widget.get())

        elif _widgetType == SPINBOX:
            assert len(_value) == 2
            _widget = Spinbox(frame, min=_value[0], max=_value[1], grid=(row, 1))
            _widget.setSingleStep(param.get('stepsize', 1))
            _widget.setValue(param.get('default', _value[0]))
            callback = partial(argsDict.__setitem__, _variable)
            _widget.valueChanged.connect(callback)
            setattr(parentWidget, _variable, _widget)
            callback(_widget.value())

        elif _widgetType == DOUBLESPINBOX:
            assert len(_value) == 2
            _widget = DoubleSpinbox(frame, min=_value[0], max=_value[1], grid=(row, 1))
            defaultStepSize = (_value[1] - _value[0]) / 100
            _widget.setSingleStep(param.get('stepsize', defaultStepSize))
            _widget.setValue(param.get('default', _value[0]))
            callback = partial(argsDict.__setitem__, _variable)
            _widget.valueChanged.connect(callback)
            setattr(parentWidget, _variable, _widget)
            callback(_widget.value())

        elif _widgetType == PATH_EDIT:
            # _fr = Frame(frame, setLayout=True, grid=(row, 1), gridspan=(1,2))
            # _widget = LineEditButtonDialog(_fr)

            param.setdefault('textAlignment', 'left')
            callback = partial(argsDict.__setitem__, _variable)
            _widget = PathEdit(frame, grid=(row, 1), callback=callback, **param)
            if _defaultValue:
                _widget.set(_defaultValue)

            button = Button(parent=frame, text='', icon=Icon('icons/directory'),
                            callback=partial(_openFileDialog, _widget),
                            grid=(row, 2),
                            )
            button.setStyleSheet("border: 0px solid transparent")

        if _widget is not None:
            _widget.setObjectName(AUTOGEN_TAG + _variable)

    return parentWidget


def _openFileDialog(widget):
    """Get a file using file dialog
    """
    _app = getApplication()
    _fileDialog = DataFileDialog(parent=_app.mainWindow, acceptMode='load')
    _fileDialog._show()
    selectedFile = _fileDialog.selectedFile()
    if selectedFile:
        widget.setText(str(selectedFile))


def selectedRadioButton(self, argsDict, param):
    clicked = [b.text() for b in self.sender().buttons() if b.isChecked()]
    partial(argsDict.__setitem__, param['variable'])


def _getNonDefaultArgCount(self, f: callable) -> int:  # TODO: Move this to util
    import inspect

    count = 0
    sig = inspect.signature(f)
    for _, p in sig.parameters.items():
        if p.default == inspect._empty:
            count += 1
    return count


def _anyArgsVarPositional(self, f: callable) -> int:
    import inspect

    sig = inspect.signature(f)
    for _, p in sig.parameters.items():
        if p.kind == inspect._ParameterKind.VAR_POSITIONAL:
            return True
    return False

# dialog = FileDialog(parent=self.mainWindow, fileMode=FileDialog.AnyFile, text=text,
#                     acceptMode=FileDialog.AcceptOpen, preferences=self.application.preferences,
#                     restrictDirToFilter=False, selectFile=self.application.project.path)
# class FileDialog(QtWidgets.QFileDialog):
#
#     # def __init__(self, parent=None, fileMode=QtWidgets.QFileDialog.AnyFile, text=None,
#     #              acceptMode=QtWidgets.QFileDialog.AcceptOpen, preferences=None, **kwds):
#
#     def __init__(self, parent=None, fileMode=QtWidgets.QFileDialog.AnyFile, text=None,
#                  acceptMode=QtWidgets.QFileDialog.AcceptOpen, preferences=None,
#                  selectFile=None, filter=None,
#                  restrictDirToFilter=False, dirFilter=None,
#                  multiSelection=False, **kwds):
#
#         # ejb - added selectFile to suggest a filename in the file box
#         #       this is not passed to the super class
#
#         QtWidgets.QFileDialog.__init__(self, parent, caption=text, **kwds)
#
#         staticFunctionDict = {
#             (0, 0)                               : 'getOpenFileName',
#             (0, 1)                               : 'getOpenFileName',
#             (0, 2)                               : 'getExistingDirectory',
#             (0, 3)                               : 'getOpenFileNames',
#             (0, 4)                               : 'getExistingDirectory',
#             (1, 0)                               : 'getSaveFileName',
#             (1, 1)                               : 'getSaveFileName',
#             (1, 2)                               : 'getSaveFileName',
#             (1, 3)                               : 'getSaveFileName',
#             (self.AcceptOpen, self.AnyFile)      : 'getOpenFileName',
#             (self.AcceptOpen, self.ExistingFile) : 'getOpenFileName',
#             (self.AcceptOpen, self.Directory)    : 'getExistingDirectory',
#             (self.AcceptOpen, self.ExistingFiles): 'getOpenFileNames',
#             (self.AcceptOpen, self.DirectoryOnly): 'getExistingDirectory',
#             (self.AcceptSave, self.AnyFile)      : 'getSaveFileName',
#             (self.AcceptSave, self.ExistingFile) : 'getSaveFileName',
#             (self.AcceptSave, self.Directory)    : 'getSaveFileName',
#             (self.AcceptSave, self.ExistingFiles): 'getSaveFileName',
#             }
#
#         self.setFileMode(fileMode)
#         self.setAcceptMode(acceptMode)
#         if filter is not None:
#             self.setNameFilter(filter)
#         self._currentNameFilter = filter
#         self.dirFilter = dirFilter if dirFilter else []
#
#         # self.setNameFilters(["Text files (*.txt)", "Images (*.png *.jpg)"])
#         # self.selectNameFilter("Images (*.png *.jpg)")
#
#         self._lastDirectory = None
#         if selectFile is not None:  # ejb - populates fileDialog with a suggested filename
#             self.selectFile(selectFile)
#             self._lastDirectory = selectFile
#
#         if preferences is not None and preferences.general.useNative:
#             self.useNative = True
#         else:
#             self.useNative = False
#
#         # need to do this before setting DontUseNativeDialog
#         self._restrictDirToFilter = restrictDirToFilter
#
#         if restrictDirToFilter == True:
#             self.directoryEntered.connect(self._dir)
#             # self.setOption(QtWidgets.QFileDialog.ShowDirsOnly)  # don't think this works - need to select DirectoryOnly
#             self._restrictedType = filter
#         # else:
#         # add new handler to allow selection of file or folder
#         self.currentChanged.connect(self._changed)
#
#         # self.result is '' (first case) or 0 (second case) if Cancel button selected
#         if self.useNative and not sys.platform.lower() == 'linux':
#             funcName = staticFunctionDict[(acceptMode, fileMode)]
#             self.result = getattr(self, funcName)(caption=text, **kwds)
#             if isinstance(self.result, tuple):
#                 self.result = self.result[0]
#         else:
#             self.setOption(QtWidgets.QFileDialog.DontUseNativeDialog)
#
#             # add a multiselection option - only for non-native dialogs
#             if multiSelection:
#                 for view in self.findChildren((QtWidgets.QListView, QtWidgets.QTreeView)):
#                     if isinstance(view.model(), QtWidgets.QFileSystemModel):
#                         view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
#
#             self.result = self.exec_()
#
#     # def setFileMode(self, mode: 'QFileDialog.FileMode'):
#     #   super(FileDialog, self).setFileMode(mode)
#
#     def _changed(self, file: str):
#         """
#         new event handler to allow selection of files or folders by
#         switching fileMode depending on what is clicked
#         """
#         if aPath(file).is_file():
#             self.setFileMode(self.AnyFile)
#             # self.setNameFilter(self._currentNameFilter)
#         elif aPath(file).is_dir() and self._restrictDirToFilter:
#             self.setFileMode(self.Directory)
#             self._lastDirectory = file
#
#     def _dir(self, directory: str):
#         for dirEnd in self.dirFilter:
#             if directory.endswith(dirEnd):
#                 self._lastDirectory = directory
#                 self.selectFile(directory)
#
#                 # accept and terminate the file dialog
#                 self.accept()
#
#         return True
#
#     def accept(self):
#         super(FileDialog, self).accept()
#
#     # overrides Qt function, which does not pay any attention to whether Cancel button selected
#     def selectedFiles(self):
#         # files = QtWidgets.QFileDialog.selectedFiles(self)
#         # print('>>>', self.result, files)
#
#         if self.useNative:
#             file = self.result[0]
#             if len(file) > 0:
#                 return [file]
#             else:
#                 return []
#
#         elif not self.useNative and self.result:
#             return QtWidgets.QFileDialog.selectedFiles(self)
#
#         else:
#             return []
#
#     # Qt does not have this but useful if you know you only want one file
#     def selectedFile(self):
#
#         files = self.selectedFiles()
#         if files and len(files) > 0:
#             if aPath(files[0]).is_dir() and self._restrictDirToFilter:
#                 return self._lastDirectory if self._lastDirectory else files[0]
#             else:
#                 return files[0]
#         else:
#             return None
