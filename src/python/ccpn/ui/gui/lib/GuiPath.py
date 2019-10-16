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
from PyQt5 import QtGui, QtWidgets
from ccpn.ui.gui.widgets.LineEdit import LineEdit


VALIDROWCOLOUR = QtGui.QColor('palegreen')
ACCEPTROWCOLOUR = QtGui.QColor('darkseagreen')
REJECTROWCOLOUR = QtGui.QColor('orange')
INVALIDROWCOLOUR = QtGui.QColor('lightpink')
VALIDFILE ='File'
VALIDPATH = 'Path'
VALIDMODES = (VALIDFILE, VALIDPATH)
VALIDFUNCS = (os.path.isfile, os.path.isdir)


class PathValidator(QtGui.QValidator):

    def __init__(self, parent=None, fileMode=VALIDPATH):
        super().__init__(parent=parent)

        if fileMode not in VALIDMODES:
            raise NotImplemented("Error, fileMode %s not supported, use %s" % (str(fileMode), str(VALIDMODES)))
        self.fileMode = fileMode
        self.baseColour = self.parent().palette().color(QtGui.QPalette.Base)
        self._func = VALIDFUNCS[VALIDMODES.index(fileMode)]

    def validate(self, p_str, p_int):
        filePath = p_str.strip()
        filePath = os.path.expanduser(filePath)

        palette = self.parent().palette()

        if self._func(filePath):
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


class PathEdit(LineEdit):
    """LineEdit widget that contains validator for checking filePaths exists
    """
    def __init__(self, parent, fileMode=VALIDPATH, **kwds):
        super().__init__(parent=parent, **kwds)

        if fileMode not in VALIDMODES:
            raise ValueError("Error, fileMode %s not supported, use %s" % (str(fileMode), str(VALIDMODES)))

        self.setValidator(PathValidator(parent=self, fileMode=fileMode))
        self.validator().resetCheck()