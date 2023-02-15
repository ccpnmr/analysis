"""
Module Documentation here
"""
#=========================================================================================
# Licence, Reference and Credits
#=========================================================================================
__copyright__ = "Copyright (C) CCPN project (https://www.ccpn.ac.uk) 2014 - 2023"
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
__dateModified__ = "$dateModified: 2023-02-15 19:22:57 +0000 (Wed, February 15, 2023) $"
__version__ = "$Revision: 3.1.1 $"
#=========================================================================================
# Created
#=========================================================================================
__author__ = "$Author: Ed Brooksbank $"
__date__ = "$Date: 2022-09-08 17:12:59 +0100 (Thu, September 08, 2022) $"
#=========================================================================================
# Start of code
#=========================================================================================

from PyQt5 import QtCore

import ccpn.core  # MUST be imported here for correct import-order
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
               'borderWidth', 'cellPadding', 'focusBorderWidth', 'gridColour',
               '_resize', 'setWidthToColumns', 'setHeightToRows',
               'setOnHeaderOnly', 'showGrid', 'wordWrap',
               'selectionCallback', 'selectionCallbackEnabled',
               'actionCallback', 'actionCallbackEnabled',
               'enableExport', 'enableDelete', 'enableSearch', 'enableCopyCell',
               'tableMenuEnabled',
               'ignoreStyleSheet',
               )


#=========================================================================================
# Table
#=========================================================================================

class Table(TableABC, Base):
    """
    New table class to integrate into ccpn-widgets
    """

    _enableSelectionCallback = True
    _enableActionCallback = True

    def __init__(self, parent, *, df=None,
                 multiSelect=True, selectRows=True,
                 showHorizontalHeader=True, showVerticalHeader=True,
                 borderWidth=2, cellPadding=2, focusBorderWidth=1, gridColour=None,
                 _resize=False, setWidthToColumns=False, setHeightToRows=False,
                 setOnHeaderOnly=False, showGrid=False, wordWrap=False,
                 selectionCallback=NOTHING, selectionCallbackEnabled=NOTHING,
                 actionCallback=NOTHING, actionCallbackEnabled=NOTHING,
                 enableExport=NOTHING, enableDelete=NOTHING, enableSearch=NOTHING, enableCopyCell=NOTHING,
                 tableMenuEnabled=NOTHING,
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
        :param gridColour:
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
        :param enableCopyCell:
        :param tableMenuEnabled:
        :param kwds:
        """
        super().__init__(parent, df=df,
                         multiSelect=multiSelect, selectRows=selectRows,
                         showHorizontalHeader=showHorizontalHeader, showVerticalHeader=showVerticalHeader,
                         borderWidth=borderWidth, cellPadding=cellPadding, focusBorderWidth=focusBorderWidth, gridColour=gridColour,
                         _resize=_resize, setWidthToColumns=setWidthToColumns, setHeightToRows=setHeightToRows,
                         setOnHeaderOnly=setOnHeaderOnly, showGrid=showGrid, wordWrap=wordWrap,
                         selectionCallback=selectionCallback, selectionCallbackEnabled=selectionCallbackEnabled,
                         actionCallback=actionCallback, actionCallbackEnabled=actionCallbackEnabled,
                         enableExport=enableExport, enableDelete=enableDelete, enableSearch=enableSearch, enableCopyCell=enableCopyCell,
                         tableMenuEnabled=tableMenuEnabled,
                         )
        baseKwds = {k: v for k, v in kwds.items() if k not in _TABLE_KWDS}
        Base._init(self, ignoreStyleSheet=ignoreStyleSheet, **baseKwds)


#=========================================================================================
# Table testing
#=========================================================================================

def main():
    """Show the test-table
    """
    MAX_ROWS = 7

    import pandas as pd
    import numpy as np
    import random
    from PyQt5 import QtGui, QtWidgets

    from ccpn.ui.gui.widgets.Application import TestApplication

    data = [[1, 150, 300, 900, float('nan'), 80.1, 'delta'],
            [2, 200, 500, 300, float('nan'), 34.2, ['help', 'more', 'chips']],
            [3, 100, np.nan, 1000, None, -float('Inf'), 'charlie'],
            [4, 999, np.inf, 500, None, float('Inf'), 'echo'],
            [5, 300, -np.inf, 450, 700, 150.3, 'bravo']
            ]

    # multiIndex columnHeaders
    cols = ("No", "Toyota", "Ford", "Tesla", "Nio", "Other", "NO")
    rowIndex = ["AAA", "BBB", "CCC", "DDD", "EEE"]  # duplicate index

    for ii in range(MAX_ROWS):
        chrs = ''.join(chr(random.randint(65, 68)) for _ in range(5))
        rowIndex.append(chrs[:3])
        data.append([6 + ii,
                     300 + random.randint(1, MAX_ROWS),
                     random.random() * 1e6,
                     450 + random.randint(-100, 400),
                     700 + random.randint(-MAX_ROWS, MAX_ROWS),
                     150.3 + random.random() * 1e2,
                     f'bravo{chrs[3:]}' if ii % 2 else f'delta{chrs[3:]}'])

    df = pd.DataFrame(data, columns=cols, index=rowIndex)

    # show the example table
    app = TestApplication()
    win = QtWidgets.QMainWindow()
    frame = QtWidgets.QFrame()
    layout = QtWidgets.QGridLayout()
    frame.setLayout(layout)

    table = TableABC(None, df=df, focusBorderWidth=1, cellPadding=11,
                     showGrid=True, gridColour='white',
                     setWidthToColumns=False, setHeightToRows=False, _resize=True)

    for row in range(table.rowCount()):
        for col in range(table.columnCount()):
            table.setBackground(row, col, QtGui.QColor(random.randint(0, 256**3) & 0x3f3f3f | 0x404040))

    # set some background colours
    cells = ((0, 0, '#80C0FF'),
             (1, 1, '#fe83cc'), (1, 2, '#fe83cc'),
             (2, 3, '#83fbcc'),
             (3, 2, '#e0ff87'), (3, 3, '#e0ff87'), (3, 4, '#e0ff87'), (3, 5, '#e0ff87'),
             (4, 2, '#e0f08a'), (4, 3, '#e0f08a'), (4, 4, '#e0f08a'), (4, 5, '#e0f08a'),
             (6, 2, '#70a04f'), (6, 6, '#70a04f'),
             (7, 1, '#eebb43'), (7, 2, '#eebb43'),
             (8, 4, '#7090ef'), (8, 5, '#7090ef'),
             (9, 0, '#30f06f'), (9, 1, '#30f06f'),
             (10, 2, '#e0d0e6'), (10, 3, '#e0d0e6'), (10, 4, '#e0d0e6'),
             (11, 2, '#e0d0e6'), (11, 3, '#e0d0e6'), (11, 4, '#e0d0e6'),
             )

    for row, col, colour in cells:
        if 0 <= row < table.rowCount() and 0 <= col < table.columnCount():
            table.setBackground(row, col, colour)

    # set the horizontalHeader information
    header = table.horizontalHeader()
    # test a single stretching column
    header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
    header.setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
    header.setStretchLastSection(False)

    win.setCentralWidget(frame)
    frame.layout().addWidget(table, 0, 0)

    win.setWindowTitle(f'Testing {table.__class__.__name__}')
    win.show()

    app.start()


if __name__ == '__main__':
    """Call the test function
    """
    main()
