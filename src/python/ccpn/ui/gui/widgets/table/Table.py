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
__dateModified__ = "$dateModified: 2022-10-25 15:59:09 +0100 (Tue, October 25, 2022) $"
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
from PyQt5 import QtWidgets, QtCore
from ccpn.ui.gui.widgets.Base import Base
from ccpn.ui.gui.widgets.table.TableABC import TableABC
from ccpn.util.Common import NOTHING


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

_TABLE_KWDS = ('parent', 'df',
               'multiSelect', 'selectRows',
               'showHorizontalHeader', 'showVerticalHeader',
               'borderWidth', 'cellPadding', 'focusBorderWidth',
               '_resize', 'setWidthToColumns', 'setHeightToRows',
               'setOnHeaderOnly', 'showGrid', 'wordWrap',
               'selectionCallback', 'selectionCallbackEnabled',
               'actionCallback', 'actionCallbackEnabled',
               'enableExport', 'enableDelete', 'enableSearch', 'enableCopyCell',
               'ignoreStyleSheet',
               )


#=========================================================================================
# TableABC
#=========================================================================================

class Table(TableABC, Base):
    """
    New table class to integrate into ccpn-widgets
    """

    _enableSelectionCallback = True
    _enableActionCallback = True

    def __init__(self, parent, df=None,
                 multiSelect=True, selectRows=True,
                 showHorizontalHeader=True, showVerticalHeader=True,
                 borderWidth=2, cellPadding=2, focusBorderWidth=0,
                 _resize=False, setWidthToColumns=False, setHeightToRows=False,
                 setOnHeaderOnly=False, showGrid=False, wordWrap=False,
                 selectionCallback=NOTHING, selectionCallbackEnabled=NOTHING,
                 actionCallback=NOTHING, actionCallbackEnabled=NOTHING,
                 enableExport=NOTHING, enableDelete=NOTHING, enableSearch=NOTHING, enableCopyCell=NOTHING,
                 # local parameters
                 ignoreStyleSheet=True,
                 **kwds):
        """Initialise the table.

        :param parent:
        :param df:
        :param multiSelect:
        :param selectRows:
        :param showHorizontalHeader:
        :param showVerticalHeader:
        :param borderWidth:
        :param cellPadding:
        :param focusBorderWidth:
        :param _resize:
        :param setWidthToColumns:
        :param setHeightToRows:
        :param setOnHeaderOnly:
        :param showGrid:
        :param wordWrap:
        :param selectionCallback:
        :param selectionCallbackEnabled:
        :param actionCallback:
        :param actionCallbackEnabled:
        :param enableExport:
        :param enableDelete:
        :param enableSearch:
        :param enableCopyCell:
        :param ignoreStyleSheet:
        :param kwds:
        """
        super().__init__(parent, df=df,
                         multiSelect=multiSelect, selectRows=selectRows,
                         showHorizontalHeader=showHorizontalHeader, showVerticalHeader=showVerticalHeader,
                         borderWidth=borderWidth, cellPadding=cellPadding, focusBorderWidth=focusBorderWidth,
                         _resize=_resize, setWidthToColumns=setWidthToColumns, setHeightToRows=setHeightToRows,
                         setOnHeaderOnly=setOnHeaderOnly, showGrid=showGrid, wordWrap=wordWrap,
                         selectionCallback=selectionCallback, selectionCallbackEnabled=selectionCallbackEnabled,
                         actionCallback=actionCallback, actionCallbackEnabled=actionCallbackEnabled,
                         enableExport=enableExport, enableDelete=enableDelete, enableSearch=enableSearch, enableCopyCell=enableCopyCell,
                         )
        baseKwds = {k: v for k, v in kwds.items() if k not in _TABLE_KWDS}
        Base._init(self, ignoreStyleSheet=ignoreStyleSheet, **baseKwds)


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

    table = Table(None, df=df)
    win.setCentralWidget(frame)
    frame.layout().addWidget(table, 0, 0)

    win.setWindowTitle(f'Testing {table.__class__.__name__}')
    win.show()

    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
