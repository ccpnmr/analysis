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
__dateModified__ = "$dateModified: 2025-10-08 19:44:50 +0100 (Wed, October 08, 2025) $"
__version__ = "$Revision: 3.3.3 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2020-04-16 12:14:50 +0000 (Thu, April 16, 2020) $"
#=========================================================================================
# Start of code
#=========================================================================================

__all__ = ["PathEdit", "PathValidator"]

import os
from typing import Callable
from PyQt5 import QtGui, QtWidgets

from ccpn.util.Path import aPath
from ccpn.ui.gui.widgets.LineEdit import LineEdit

from ccpn.ui.gui.guiSettings import (COLOUR_BLIND_LIGHTGREEN, COLOUR_BLIND_MEDIUM, COLOUR_BLIND_DARKGREEN,
                                     COLOUR_BLIND_RED, COLOUR_BLIND_ORANGE)


VALIDROWCOLOUR = COLOUR_BLIND_LIGHTGREEN
ACCEPTROWCOLOUR = COLOUR_BLIND_DARKGREEN
REJECTROWCOLOUR = COLOUR_BLIND_ORANGE
INVALIDROWCOLOUR = COLOUR_BLIND_RED


def _validPath(path, suffix) -> bool:
    "Return True if path is valid and (optionally) has suffix"
    # catch any anomalies in expanding or testing _path
    try:
        _path = aPath(path)
        result = _path.exists()
        if result and suffix is not None:
            result = _path.suffix == suffix
    except RuntimeError:
        result = False
    return result


def _validFile(path, suffix) -> bool:
    "Return True if path is valid and a file and (optionally) has suffix"
    # catch any anomalies in expanding or testing _path
    try:
        _path = aPath(path)
        result = _path.exists() and _path.is_file()
        if result and suffix is not None:
            result = _path.suffix == suffix
    except RuntimeError:
        result = False
    return result


VALIDFILE = 'File'
VALIDPATH = 'Path'
VALIDMODES = (VALIDFILE, VALIDPATH)
VALIDFUNCS = (_validFile, _validPath)

PATH = 'path'
IS_VALID = 'isValid'


class PathValidator(QtGui.QValidator):

    def __init__(self, parent=None, fileMode=VALIDPATH, withSuffix=None, callback=None):
        """
        Path validator object
        :param parent: parent PathEdit widget
        :param fileMode: mode to validate, either VALIDFILE or VALIDPATH
        :param withSuffix: suffix of path (ignore if None)
        :param callback: optional callback function called when validating input;
                         signature: callback(callbackDict: dict) with keys PATH, IS_VALID
        """
        super().__init__(parent=parent)

        if fileMode not in VALIDMODES:
            raise NotImplemented("Error, fileMode %s not supported, use %s" % (str(fileMode), str(VALIDMODES)))
        self.fileMode = fileMode
        self.withSuffix = withSuffix
        self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)
        self._func = VALIDFUNCS[VALIDMODES.index(fileMode)]
        self._state = None  # last checked state
        self._callback = callback
        self._blankCallback: int = 0  # callback blanking; done during initialisation

    def validate(self, p_str, p_int):
        """Validate the current imput of parent widget; sets self._state
        """
        # filePath = p_str.strip()
        # filePath = os.path.expanduser(filePath)

        palette = self.parent().palette()

        if not p_str or self._func(p_str, self.withSuffix):
            palette.setColor(QtGui.QPalette.Base, QtGui.QPalette().base().color())
            self._state = QtGui.QValidator.Acceptable  # entry is valid
        else:
            palette.setColor(QtGui.QPalette.Base, INVALIDROWCOLOUR)
            self._state = QtGui.QValidator.Intermediate  # entry is NOT valid, but can continue editing
        self.parent().setPalette(palette)

        if self._blankCallback == 0 and self._callback is not None:
            _callBackDict = {PATH: p_str, IS_VALID: self.isValid}
            self._callback(_callBackDict)

        return self._state, p_str, p_int

    def clearValidCheck(self):
        palette = self.parent().palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QPalette().base().color())
        self.parent().setPalette(palette)

    def resetCheck(self, blankCallback: bool = False):
        if blankCallback:
            self._blankCallback += 1
        self.validate(self.parent().text(), 0)
        if blankCallback:
            self._blankCallback -= 1

    # GWV: 16/8/2024: removed as no longer used!?
    # should be a function, not a property
    # @property
    # def checkState(self):
    #     self.validate(self.parent().text(), 0)
    #     return self._state

    @property
    def isValid(self) -> bool:
        """:return True is state is acceptable
        """
        return self._state == QtGui.QValidator.Acceptable


class PathEdit(LineEdit):
    """LineEdit widget that contains validator for checking filePaths exists
    """

    def __init__(self, parent, fileMode=VALIDPATH, withSuffix=None, callback=None, **kwds):
        """
        A widget to enter/edit path's; check for validity and optional callback
        when validating data.
        :param parent: parent of the widget
        :param fileMode: mode to validate, either VALIDFILE or VALIDPATH
        :param withSuffix: (optionally) check for suffix
        :param callback: optional callback function called when validating input;
                         signature: callback(callbackDict: dict) with keys PATH, IS_VALID
        :param **kwds: optional keyword arguments passed to Base
        """
        kwds.setdefault('textAlignment', 'l')
        kwds.setdefault('acceptDrops', True)

        super().__init__(parent=parent, **kwds)

        if fileMode not in VALIDMODES:
            raise ValueError("Error, fileMode %s not supported, use %s" % (str(fileMode), str(VALIDMODES)))

        self.setValidator(PathValidator(parent=self, fileMode=fileMode, withSuffix=withSuffix, callback=callback))
        self.validator().resetCheck(blankCallback=True)

    @property
    def isValid(self) -> bool:
        """:return True is widget contains a valid path
        """
        return len(self.get()) > 0 and self.validator().isValid

    def dropEvent(self, event):
        """
        Subclass the dropEvent to catch any urls (i.e. file-paths) dropped
        """
        if self.acceptDrops():
            dataDict = self.parseEvent(event)
            urls = dataDict.get(self.URLS)
            if len(urls) > 0:
                self.set(urls[0])
