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
__dateModified__ = "$dateModified: 2022-09-09 21:15:58 +0100 (Fri, September 09, 2022) $"
__version__ = "$Revision: 3.1.0 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-09-08 17:12:59 +0100 (Thu, September 08, 2022) $"
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
from ccpn.ui.gui.widgets.table.TableABC import TableABC
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
# TableABC
#=========================================================================================

class Table(TableABC, Base):
    """
    New table class to integrate into ccpn-widgets
    """

    _enableSelectionCallback = True
    _enableActionCallback = True

    def __init__(self, parent=None, df=None,
                 multiSelect=True, selectRows=True,
                 showHorizontalHeader=True, showVerticalHeader=True,
                 borderWidth=2, cellPadding=2,
                 _resize=False, setWidthToColumns=False, setHeightToRows=False,
                 **kwds):
        """Initialise the table
        """
        super().__init__(parent, df,
                         multiSelect=multiSelect, selectRows=selectRows,
                         showHorizontalHeader=showHorizontalHeader, showVerticalHeader=showVerticalHeader,
                         borderWidth=borderWidth, cellPadding=cellPadding,
                         _resize=_resize, setWidthToColumns=setWidthToColumns, setHeightToRows=setHeightToRows)
        Base._init(self, **kwds)

    #=========================================================================================
    # Methods
    #=========================================================================================

    def selectionCallback(self, selected, deselected):
        print(f'  Selection changed  {selected}  {deselected}')

    def actionCallback(self, index):
        print(f'  Action {index}')

    def deleteSelectionFromTable(self):
        pass


#=========================================================================================
# Table testing
#=========================================================================================

def main():
    """Show the test-table
    """
    MAX_ROWS = 5

    from ccpn.ui.gui.widgets.Application import TestApplication
    import pandas as pd
    import random

    data = [[1, 150, 300, 900, float('nan'), 80.1, 'delta'],
            [2, 200, 500, 300, float('nan'), 34.2, ['help', 'more', 'chips']],
            [3, 100, np.nan, 1000, None, -float('Inf'), 'charlie'],
            [4, 999, np.inf, 500, None, float('Inf'), 'echo'],
            [5, 300, -np.inf, 450, 700, 150.3, 'bravo']
            ]

    # multiIndex columnHeaders
    cols = ("No", "Toyota", "Ford", "Tesla", "Nio", "Other", "NO")
    rowIndex = ["AAA", "BBB", "CCC", "DDD", "EEE"]

    for ii in range(MAX_ROWS):
        chrs = ''.join(chr(random.randint(65, 68)) for _ in range(5))
        rowIndex.append(chrs[:3])
        data.append([6 + ii,
                     300 + random.randint(1, MAX_ROWS),
                     random.random() * 1e6,
                     450 + random.randint(-100, 400),
                     700 + random.randint(-MAX_ROWS, MAX_ROWS),
                     150.3 + random.random() * 1e2,
                     'bravo' + chrs[3:]])

    df = pd.DataFrame(data, columns=cols, index=rowIndex)

    # show the example table
    app = TestApplication()
    win = QtWidgets.QMainWindow()
    frame = QtWidgets.QFrame()
    layout = QtWidgets.QGridLayout()
    frame.setLayout(layout)

    table = Table(df=df)
    win.setCentralWidget(frame)
    frame.layout().addWidget(table, 0, 0)

    win.setWindowTitle(f'Testing {table.__class__.__name__}')
    win.show()

    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
