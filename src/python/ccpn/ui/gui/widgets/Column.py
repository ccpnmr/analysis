"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (http://www.ccpn.ac.uk) 2014 - 2019"
__credits__ = ("Ed Brooksbank, Luca Mureddu, Timothy J Ragan & Geerten W Vuister")
__licence__ = ("CCPN licence. See http://www.ccpn.ac.uk/v3-software/downloads/license")
__reference__ = ("Skinner, S.P., Fogh, R.H., Boucher, W., Ragan, T.J., Mureddu, L.G., & Vuister, G.W.",
                 "CcpNmr AnalysisAssign: a flexible platform for integrated NMR analysis",
                 "J.Biomol.Nmr (2016), 66, 111-124, http://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2018-12-20 15:53:22 +0000 (Thu, December 20, 2018) $"
__version__ = "$Revision: 3.0.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2018-12-20 15:44:35 +0000 (Thu, December 20, 2018) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtGui, QtCore, QtWidgets
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.util.Logging import getLogger


BG_COLOR = QtGui.QColor('#E0E0E0')


# TODO:ED add some documentation here
class ColumnClass:
    def __init__(self, columnList=[None] * 4):
        self._columns = [Column(colName, func, tipText=tipText, setEditValue=editValue) for
                         colName, func, tipText, editValue in columnList]  # FIXME . this mechanism is very fragile

    def addColumn(self, newColumn):
        columnToAdd = [Column(colName, func, tipText=tipText, setEditValue=editValue) for
                       colName, func, tipText, editValue in newColumn]

        if self._columns:
            self._columns.append(columnToAdd)
        else:
            self._columns = columnToAdd

    @property
    def numColumns(self):
        if self._columns:
            return len(self._columns)
        else:
            return None

    @property
    def columns(self):
        return self._columns

    @property
    def headings(self):
        return [heading.headerText for heading in self._columns]

    @property
    def functions(self):
        return [heading.getValue for heading in self._columns]

    @property
    def tipTexts(self):
        return [heading.tipText for heading in self._columns]

    @property
    def getEditValues(self):
        return [heading.getValue for heading in self._columns]

    @property
    def setEditValues(self):
        return [heading.setEditValue for heading in self._columns]


# TODO:ED add some documentation here

class Column:

    def __init__(self, headerText, getValue, getEditValue=None, setEditValue=None,
                 editClass=None, editArgs=None, editKw=None, tipText=None,
                 getColor=None, getIcon=None, stretch=False, format=None,
                 editDecimals=None, editStep=None, alignment=QtCore.Qt.AlignLeft):
        # editDecimals=None, editStep=None, alignment=QtCore.Qt.AlignLeft,
        # orderFunc=None):

        self.headerText = headerText
        self.getValue = getValue or self._defaultText
        self.getEditValue = getEditValue or getValue
        self.setEditValue = setEditValue
        self.editClass = editClass
        self.editArgs = editArgs or []
        self.editKw = editKw or {}
        self.stretch = stretch
        self.format = format
        self.editDecimals = editDecimals
        self.editStep = editStep
        self.defaultIcon = None
        #self.alignment = ALIGN_OPTS.get(alignment, alignment) | Qt.AlignVCenter
        # Alignment combinations broken in PyQt4 v1.1.1
        # Use better default than top left
        self.alignment = QtCore.Qt.AlignCenter
        # self.orderFunc = orderFunc

        self.getIcon = getIcon or self._defaultIcon
        self.getColor = getColor or self._defaultColor
        self.tipText = tipText

        self._checkTextAttrs()

    def orderFunc(self, objA, objB):
        return (universalSortKey(self.getValue(objA)) < universalSortKey(self.getValue(objB)))

    def getFormatValue(self, obj):

        value = self.getValue(obj)
        format = self.format
        if format and (value is not None):
            return format % value
        else:
            return value

    def _checkTextAttrs(self):

        if isinstance(self.getValue, str):
            attr = self.getValue
            self.getValue = lambda obj: getattr(obj, attr)

        if isinstance(self.getEditValue, str):
            attr = self.getEditValue
            self.getEditValue = lambda obj: getattr(obj, attr)

        if isinstance(self.setEditValue, str):
            attr = self.setEditValue
            self.setEditValue = lambda obj, value: setattr(obj, attr, value)

        if isinstance(self.getIcon, QtGui.QIcon):
            self.defaultIcon = self.getIcon
            self.getIcon = self._defaultIcon

    def _defaultText(self, obj):

        return ' '

    def _defaultColor(self, obj):

        return BG_COLOR

    def _defaultIcon(self, obj):

        return self.defaultIcon
