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
                 "J.Biomol.Nmr (2016), 66, 111-124, https://doi.org/10.1007/s10858-016-0060-y")
#=========================================================================================
# Last code modification
#=========================================================================================
__modifiedBy__ = "$modifiedBy: Ed Brooksbank $"
__dateModified__ = "$dateModified: 2022-10-12 15:27:14 +0100 (Wed, October 12, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-09-08 17:50:58 +0100 (Thu, September 08, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtCore, QtGui
from collections import defaultdict, OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from functools import partial
from time import time_ns
from types import SimpleNamespace
import typing

from ccpn.core.lib.CallBack import CallBack
from ccpn.core.lib.CcpnSorting import universalSortKey
from ccpn.core.lib.ContextManagers import undoBlockWithoutSideBar, catchExceptions
from ccpn.core.lib.Notifiers import Notifier
from ccpn.ui.gui.guiSettings import getColours, GUITABLE_ITEM_FOREGROUND
from ccpn.ui.gui.widgets.Font import setWidgetFont, TABLEFONT, getFontHeight
from ccpn.ui.gui.widgets.Frame import ScrollableFrame
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.Menu import Menu
from ccpn.ui.gui.widgets.ColumnViewSettings import ColumnViewSettingsPopup
from ccpn.ui.gui.widgets import MessageDialog
from ccpn.ui.gui.widgets.SearchWidget import attachDFSearchWidget
from ccpn.ui.gui.widgets.Icon import Icon
from ccpn.ui.gui.widgets.FileDialog import TablesFileDialog
from ccpn.util.Path import aPath
from ccpn.util.Logging import getLogger
from ccpn.util.Common import copyToClipboard
from ccpn.util.OrderedSet import OrderedSet


ORIENTATIONS = {'h'                 : QtCore.Qt.Horizontal,
                'horizontal'        : QtCore.Qt.Horizontal,
                'v'                 : QtCore.Qt.Vertical,
                'vertical'          : QtCore.Qt.Vertical,
                QtCore.Qt.Horizontal: QtCore.Qt.Horizontal,
                QtCore.Qt.Vertical  : QtCore.Qt.Vertical,
                }

# define a role to return a cell-value
DTYPE_ROLE = QtCore.Qt.UserRole + 1000
VALUE_ROLE = QtCore.Qt.UserRole + 1001
INDEX_ROLE = QtCore.Qt.UserRole + 1002

EDIT_ROLE = QtCore.Qt.EditRole
_EDITOR_SETTER = ('setColor', 'selectValue', 'setData', 'set', 'setValue', 'setText', 'setFile')
_EDITOR_GETTER = ('get', 'value', 'text', 'getFile')


#=========================================================================================
# _SimplePandasTableHeaderModel
#=========================================================================================

class _SimplePandasTableHeaderModel(QtCore.QAbstractTableModel):
    """A simple table model to view pandas DataFrames
    """
    _defaultForegroundColour = QtGui.QColor(getColours()[GUITABLE_ITEM_FOREGROUND])

    def __init__(self, row, column):
        """Initialise the pandas model
        Allocates space for foreground/background colours
        """
        QtCore.QAbstractTableModel.__init__(self)
        # create numpy arrays to match the data that will hold background colour
        self._colour = np.zeros((row, column), dtype=np.object)
        self._df = np.zeros((row, column), dtype=np.object)

    def rowCount(self, parent=None):
        """Return the row count for the dataFrame
        """
        return self._df.shape[0]

    def columnCount(self, parent=None):
        """Return the column count for the dataFrame
        """
        return self._df.shape[1]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Process the data callback for the model
        """
        if index.isValid():
            # get the source cell
            row, col = index.row(), index.column()

            if role == QtCore.Qt.DisplayRole:
                return str(self._df[row, col])

            elif role == QtCore.Qt.BackgroundRole:
                if (colourDict := self._colour[row, col]):
                    # get the colour from the dict
                    return colourDict.get(role)

            elif role == QtCore.Qt.ForegroundRole:
                if (colourDict := self._colour[row, col]):
                    # get the colour from the dict
                    return colourDict.get(role)

                # return the default foreground colour
                return self._defaultForegroundColour

            elif role == QtCore.Qt.ToolTipRole:
                data = self._df[row, col]

                return str(data)

        return None
