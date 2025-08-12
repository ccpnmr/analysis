"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2022"
__credits__ = ("Ed Brooksbank, Joanna Fox, Victoria A Higman, Luca Mureddu, Eliza Płoskoń",
               "Timothy J Ragan, Brian O Smith, Gary S Thompson & Geerten W Vuister")
__licence__ = ("CCPN licence. See https://ccpn.ac.uk/software/licensing/")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-03-29 13:40:33 +0100 (Tue, March 29, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: CCPN $"
__date__ = "$Date: 2017-11-28 10:28:42 +0000 (Tue, Nov 28, 2017) $"
#=========================================================================================
# Start of code
#=========================================================================================

import os, copy, json, pprint, math

from PyQt5 import QtCore, QtGui, QtWidgets
from ccpn.framework.lib.Plugin import Plugin
from ccpn.ui.gui.modules.PluginModule import PluginModule
from ccpn.ui.gui.widgets.FileDialog import LineEditButtonDialog
from ccpn.ui.gui.widgets.Label import Label
from ccpn.ui.gui.widgets.LineEdit import LineEdit
from ccpn.ui.gui.widgets.TextEditor import TextEditor
from ccpn.ui.gui.widgets.DoubleSpinbox import DoubleSpinbox
from ccpn.ui.gui.widgets.Spinbox import Spinbox
from ccpn.ui.gui.widgets.RadioButtons import RadioButtons
from ccpn.ui.gui.widgets.Button import Button
from ccpn.ui.gui.widgets.ButtonList import ButtonList
from ccpn.ui.gui.widgets.MessageDialog import showYesNoWarning, showWarning, showMessage
from ccpn.ui.gui.widgets.ProjectTreeCheckBoxes import ProjectTreeCheckBoxes
from ccpn.ui.gui.widgets.CheckBox import CheckBox
from ccpn.ui.gui.widgets.PulldownList import PulldownList
from ccpn.ui.gui.widgets.Spacer import Spacer
from ccpn.ui.gui.widgets.ScrollArea import ScrollArea
from ccpn.ui.gui.widgets.Frame import Frame


def _addColumn(grid):
    return (grid[0], grid[1] + 1)


def _addRow(grid):
    return (grid[0] + 1, 0)


def _addVerticalSpacer(layout, grid):
    grid = _addRow(grid)
    Spacer(layout, 0, 20, QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed, grid=grid, gridSpan=(1, 1))
    grid = _addRow(grid)
    return grid


def _setWidth(columnWidths, grid):
    # Take column width from predefined global columnWidths. If width is defined it overrides this, which can be used in combination with gridspan
    if grid[1] > len(columnWidths) - 1:
        width = columnWidths[-1]
    else:
        width = columnWidths[grid[1]]
    return width


def _setWidgetProperties(widget=None, width=100, height=25, widthType='Fixed', heightType='Fixed', hAlign='l', textAlignment='r'):
    # Set widget width and height
    if not isinstance(widget, ButtonList):
        if widthType.upper() == 'FIXED':
            if isinstance(widget, LineEditButtonDialog):
                widget.lineEdit.setFixedWidth(width)
            else:
                widget.setFixedWidth(width)
        else:
            if isinstance(widget, LineEditButtonDialog):
                widget.lineEdit.setMinimumWidth(width)
            else:
                widget.setMinimumWidth(width)
    else:
        widget.setMinimumWidth(width)

    if heightType.upper() == 'FIXED':
        if hasattr(widget, 'setFixedHeight'):
            widget.setFixedHeight(height)
    else:
        if hasattr(widget, 'setMinimumHeight'):
            widget.setMinimumHeight(height)

    # Set widget alignment, not all widgets have this attribute
    try:
        if hAlign == 'l':
            widget.setAlignment(QtCore.Qt.AlignLeft)
        if hAlign == 'c':
            widget.setAlignment(QtCore.Qt.AlignCenter)
        if hAlign == 'r':
            widget.setAlignment(QtCore.Qt.AlignRight)
    except AttributeError:
        pass

    try:
        if hasattr(widget, 'textAlignment'):
            widget.setAlignment(textAlignment)
    except AttributeError:
        pass
